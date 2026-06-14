import sqlite3
import os
from PySide6.QtCore import QObject, Signal

class ProjectService(QObject):
    """项目管理服务：管理考试项目，实现数据隔离"""
    
    # 信号
    project_changed = Signal(str)  # 项目切换信号
    project_created = Signal(str)  # 项目创建信号
    error_occurred = Signal(str)  # 错误信号
    
    def __init__(self, db_path="./data/exam_data.db", parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.conn = None
        self.current_project = None
        self._init_database()
        
    def _init_database(self):
        """初始化项目表"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
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
            
            # 设置默认项目
            self.current_project = "默认项目"
            print(f"项目管理服务初始化成功")
            
        except Exception as e:
            self.error_occurred.emit(f"项目管理初始化失败: {str(e)}")
            print(f"项目管理初始化失败: {e}")
            
    def get_all_projects(self):
        """获取所有项目"""
        if self.conn is None:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT name, description, created_at FROM projects ORDER BY created_at DESC')
            return cursor.fetchall()
        except Exception as e:
            self.error_occurred.emit(f"获取项目列表失败: {str(e)}")
            return []
            
    def get_project_names(self):
        """获取所有项目名称"""
        projects = self.get_all_projects()
        return [p[0] for p in projects]
        
    def create_project(self, name, description=""):
        """创建新项目"""
        if self.conn is None:
            return False
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO projects (name, description)
                VALUES (?, ?)
            ''', (name, description))
            
            self.conn.commit()
            self.project_created.emit(name)
            print(f"项目创建成功: {name}")
            return True
            
        except sqlite3.IntegrityError:
            self.error_occurred.emit(f"项目 '{name}' 已存在")
            return False
        except Exception as e:
            self.error_occurred.emit(f"创建项目失败: {str(e)}")
            return False
            
    def switch_project(self, project_name):
        """切换当前项目"""
        if self.conn is None:
            return False
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM projects WHERE name = ?', (project_name,))
            result = cursor.fetchone()
            
            if result:
                self.current_project = project_name
                self.project_changed.emit(project_name)
                print(f"切换到项目: {project_name}")
                return True
            else:
                self.error_occurred.emit(f"项目 '{project_name}' 不存在")
                return False
                
        except Exception as e:
            self.error_occurred.emit(f"切换项目失败: {str(e)}")
            return False
            
    def get_current_project(self):
        """获取当前项目名称"""
        return self.current_project
        
    def delete_project(self, project_name):
        """删除项目（谨慎使用）"""
        if project_name == "默认项目":
            self.error_occurred.emit("不能删除默认项目")
            return False
            
        if self.conn is None:
            return False
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM projects WHERE name = ?', (project_name,))
            self.conn.commit()
            
            # 如果删除的是当前项目，切换到默认项目
            if self.current_project == project_name:
                self.switch_project("默认项目")
                
            print(f"项目已删除: {project_name}")
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"删除项目失败: {str(e)}")
            return False
            
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None