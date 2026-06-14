import sqlite3
import os
import json
import numpy as np
from pathlib import Path
from PySide6.QtCore import QObject, Signal

class DatabaseService(QObject):
    """题库服务：SQLite FTS5 全文检索 + 向量存储"""
    
    # 信号
    db_ready = Signal()  # 数据库就绪
    error_occurred = Signal(str)  # 错误信号
    
    def __init__(self, db_path="./data/exam_data.db", parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.conn = None
        self._ensure_directory()
        self._init_database()
        
    def _ensure_directory(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            
    def _migrate_database(self, cursor):
        """迁移旧数据库结构"""
        try:
            # 检查 questions 表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
            if not cursor.fetchone():
                return  # 表不存在，不需要迁移
                
            # 获取现有列
            cursor.execute("PRAGMA table_info(questions)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # 添加 project 列（如果不存在）
            if 'project' not in columns:
                cursor.execute('ALTER TABLE questions ADD COLUMN project TEXT DEFAULT "默认项目"')
                cursor.execute('UPDATE questions SET project = "默认项目" WHERE project IS NULL')
                print("[DB] 迁移：添加 project 列")
                
            # 添加 vector_data 列（如果不存在）
            if 'vector_data' not in columns:
                cursor.execute('ALTER TABLE questions ADD COLUMN vector_data BLOB')
                print("[DB] 迁移：添加 vector_data 列")
                
            self.conn.commit()
            
        except Exception as e:
            print(f"[DB] 迁移警告: {e}")
            
    def _init_database(self):
        """初始化数据库和 FTS5 表"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # 检查是否需要迁移旧数据库
            self._migrate_database(cursor)
            
            # 创建主表（增加 vector_data 字段）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    options TEXT,
                    answer TEXT,
                    source TEXT DEFAULT 'unknown',
                    project TEXT DEFAULT '默认项目',
                    vector_data BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建 FTS5 虚拟表（全文检索）
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS questions_fts USING fts5(
                    question,
                    options,
                    answer,
                    content='questions',
                    content_rowid='id'
                )
            ''')
            
            # 创建触发器：插入时同步 FTS
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS questions_ai AFTER INSERT ON questions BEGIN
                    INSERT INTO questions_fts(rowid, question, options, answer)
                    VALUES (new.id, new.question, new.options, new.answer);
                END
            ''')
            
            # 创建触发器：删除时同步 FTS
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS questions_ad AFTER DELETE ON questions BEGIN
                    INSERT INTO questions_fts(questions_fts, rowid, question, options, answer)
                    VALUES ('delete', old.id, old.question, old.options, old.answer);
                END
            ''')
            
            # 创建触发器：更新时同步 FTS
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS questions_au AFTER UPDATE ON questions BEGIN
                    INSERT INTO questions_fts(questions_fts, rowid, question, options, answer)
                    VALUES ('delete', old.id, old.question, old.options, old.answer);
                    INSERT INTO questions_fts(rowid, question, options, answer)
                    VALUES (new.id, new.question, new.options, new.answer);
                END
            ''')
            
            # 创建项目表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 插入默认项目
            cursor.execute('''
                INSERT OR IGNORE INTO projects (name, description)
                VALUES ('默认项目', '系统默认项目')
            ''')
            
            self.conn.commit()
            self.db_ready.emit()
            print(f"数据库初始化成功: {self.db_path}")
            
        except Exception as e:
            self.error_occurred.emit(f"数据库初始化失败: {str(e)}")
            print(f"数据库初始化失败: {e}")
            
    def search_exact(self, text, threshold=0.85, project=None):
        """FTS5 全文检索"""
        if self.conn is None:
            return None
            
        try:
            cursor = self.conn.cursor()
            
            # 清理搜索文本
            clean_text = self._clean_text(text)
            
            # 使用 FTS5 搜索
            if project:
                cursor.execute('''
                    SELECT q.id, q.question, q.options, q.answer, q.source, q.project,
                           rank
                    FROM questions_fts fts
                    JOIN questions q ON fts.rowid = q.id
                    WHERE questions_fts MATCH ? AND q.project = ?
                    ORDER BY rank
                    LIMIT 5
                ''', (clean_text, project))
            else:
                cursor.execute('''
                    SELECT q.id, q.question, q.options, q.answer, q.source, q.project,
                           rank
                    FROM questions_fts fts
                    JOIN questions q ON fts.rowid = q.id
                    WHERE questions_fts MATCH ?
                    ORDER BY rank
                    LIMIT 5
                ''', (clean_text,))
            
            results = cursor.fetchall()
            
            if not results:
                return None
                
            # 计算相似度
            best_match = None
            best_score = 0
            
            for row in results:
                q_id, question, options, answer, source, proj, rank = row
                score = self._calculate_similarity(clean_text, question)
                
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = {
                        "id": q_id,
                        "question": question,
                        "options": options,
                        "answer": answer,
                        "source": source,
                        "project": proj,
                        "score": score
                    }
                    
            return best_match
            
        except Exception as e:
            self.error_occurred.emit(f"FTS 搜索失败: {str(e)}")
            return None
            
    def search_keyword(self, text, project=None):
        """关键词搜索（备用）"""
        if self.conn is None:
            return None
            
        try:
            cursor = self.conn.cursor()
            
            # 提取关键词
            keywords = self._extract_keywords(text)
            
            if not keywords:
                return None
                
            # 构建 LIKE 查询
            conditions = []
            params = []
            
            for keyword in keywords[:3]:
                conditions.append("question LIKE ?")
                params.append(f"%{keyword}%")
                
            if project:
                conditions.append("project = ?")
                params.append(project)
                
            query = f'''
                SELECT id, question, options, answer, source, project
                FROM questions
                WHERE {" AND ".join(conditions)}
                LIMIT 5
            '''
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                return None
                
            # 返回最佳匹配
            best_match = None
            best_score = 0
            
            for row in results:
                q_id, question, options, answer, source, proj = row
                score = self._calculate_similarity(text, question)
                
                if score > best_score:
                    best_score = score
                    best_match = {
                        "id": q_id,
                        "question": question,
                        "options": options,
                        "answer": answer,
                        "source": source,
                        "project": proj,
                        "score": score
                    }
                    
            return best_match
            
        except Exception as e:
            self.error_occurred.emit(f"关键词搜索失败: {str(e)}")
            return None
            
    def insert_question(self, question, options, answer, source="ai_generated", project="默认项目", vector_data=None):
        """插入新题目"""
        if self.conn is None:
            return False
            
        try:
            cursor = self.conn.cursor()
            
            # 序列化向量数据
            vector_blob = None
            if vector_data is not None:
                vector_blob = vector_data.tobytes()
            
            cursor.execute('''
                INSERT INTO questions (question, options, answer, source, project, vector_data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (question, options, answer, source, project, vector_blob))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"插入题目失败: {str(e)}")
            return False
            
    def update_vector(self, question_id, vector_data):
        """更新题目的向量数据"""
        if self.conn is None:
            return False
            
        try:
            cursor = self.conn.cursor()
            vector_blob = vector_data.tobytes() if vector_data is not None else None
            
            cursor.execute('''
                UPDATE questions SET vector_data = ? WHERE id = ?
            ''', (vector_blob, question_id))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"更新向量失败: {str(e)}")
            return False
            
    def get_all_questions_with_vectors(self, project=None):
        """获取所有题目及其向量"""
        if self.conn is None:
            return []
            
        try:
            cursor = self.conn.cursor()
            
            if project:
                cursor.execute('''
                    SELECT id, question, options, answer, source, project, vector_data
                    FROM questions
                    WHERE project = ? AND vector_data IS NOT NULL
                ''', (project,))
            else:
                cursor.execute('''
                    SELECT id, question, options, answer, source, project, vector_data
                    FROM questions
                    WHERE vector_data IS NOT NULL
                ''')
            
            results = []
            for row in cursor.fetchall():
                q_id, question, options, answer, source, proj, vector_blob = row
                
                # 反序列化向量
                vector = np.frombuffer(vector_blob, dtype=np.float32) if vector_blob else None
                
                results.append({
                    "id": q_id,
                    "question": question,
                    "options": options,
                    "answer": answer,
                    "source": source,
                    "project": proj,
                    "vector": vector
                })
                
            return results
            
        except Exception as e:
            self.error_occurred.emit(f"获取题目失败: {str(e)}")
            return []
            
    def get_all_questions(self, limit=100, project=None):
        """获取所有题目（用于调试）"""
        if self.conn is None:
            return []
            
        try:
            cursor = self.conn.cursor()
            
            if project:
                cursor.execute('''
                    SELECT id, question, options, answer, source, project, created_at
                    FROM questions
                    WHERE project = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (project, limit))
            else:
                cursor.execute('''
                    SELECT id, question, options, answer, source, project, created_at
                    FROM questions
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
            
            return cursor.fetchall()
            
        except Exception as e:
            self.error_occurred.emit(f"查询失败: {str(e)}")
            return []
            
    def get_question_count(self, project=None):
        """获取题目数量"""
        if self.conn is None:
            return 0
            
        try:
            cursor = self.conn.cursor()
            
            if project:
                cursor.execute('SELECT COUNT(*) FROM questions WHERE project = ?', (project,))
            else:
                cursor.execute('SELECT COUNT(*) FROM questions')
            
            return cursor.fetchone()[0]
            
        except Exception as e:
            return 0
            
    def _clean_text(self, text):
        """清理文本"""
        import re
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
        
    def _extract_keywords(self, text):
        """提取关键词"""
        import re
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        keywords = [w for w in words if len(w) >= 2]
        return keywords[:10]
        
    def _calculate_similarity(self, text1, text2):
        """计算文本相似度"""
        if not text1 or not text2:
            return 0.0
            
        text1 = text1.lower()
        text2 = text2.lower()
        
        set1 = set(text1)
        set2 = set(text2)
        
        intersection = set1.intersection(set2)
        similarity = len(intersection) / max(len(set1), len(set2))
        
        return similarity
        
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None