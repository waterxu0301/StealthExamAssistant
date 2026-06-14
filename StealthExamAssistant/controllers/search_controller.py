from PySide6.QtCore import QObject, Signal

class SearchController(QObject):
    """搜索控制器：串联三级检索逻辑"""
    
    # 信号
    answer_found = Signal(dict)  # 找到答案
    search_complete = Signal()  # 搜索完成
    error_occurred = Signal(str)  # 错误信号
    
    def __init__(self, db_service, embedding_service, llm_service, parent=None):
        super().__init__(parent)
        
        self.db_service = db_service
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        
        # 连接 LLM 信号
        self.llm_service.result_ready.connect(self._on_llm_result)
        self.llm_service.error_occurred.connect(self._on_llm_error)
        
    def search(self, ocr_text, image_base64=None, project=None):
        """执行三级检索"""
        if not ocr_text or not ocr_text.strip():
            self.error_occurred.emit("OCR 文本为空")
            return
            
        print(f"\n{'='*50}")
        print("开始三级检索")
        print(f"{'='*50}")
        print(f"OCR 文本: {ocr_text[:100]}...")
        if project:
            print(f"当前项目: {project}")
        
        # 第一级：FTS5 极速检索
        print("\n[第一级] FTS5 全文检索...")
        fts_result = self.db_service.search_exact(ocr_text, threshold=0.85, project=project)
        
        if fts_result:
            print(f"✓ FTS5 命中！相似度: {fts_result['score']:.2%}")
            fts_result["source"] = "fts"
            fts_result["source_label"] = "⚡ 本地极速秒答"
            self.answer_found.emit(fts_result)
            self.search_complete.emit()
            return
            
        print("✗ FTS5 未命中")
        
        # 第二级：向量语义检索
        print("\n[第二级] 向量语义检索...")
        
        if self.embedding_service.is_configured():
            embedding_result = self.embedding_service.search_similar_question(
                ocr_text, self.db_service, threshold=0.88, project=project
            )
            
            if embedding_result:
                print(f"✓ 语义命中！相似度: {embedding_result['score']:.2%}")
                embedding_result["source"] = "embedding"
                embedding_result["source_label"] = "🧠 语义命中"
                self.answer_found.emit(embedding_result)
                self.search_complete.emit()
                return
                
            print("✗ 语义检索未命中")
        else:
            print("⚠ 向量模型未加载，跳过语义检索")
            
        # 第三级：大模型推理
        print("\n[第三级] 大模型推理...")
        
        if self.llm_service.is_configured():
            print("正在请求大模型...")
            self.llm_service.analyze_question(ocr_text, image_base64)
            # 结果将通过信号返回
        else:
            print("⚠ LLM 未配置")
            self.error_occurred.emit("所有检索方式均未命中，且 LLM 未配置")
            self.search_complete.emit()
            
    def _on_llm_result(self, result):
        """处理 LLM 结果"""
        print(f"✓ 大模型返回结果")
        result["source_label"] = "☁️ AI 实时推理"
        self.answer_found.emit(result)
        
        # 异步保存到数据库
        self._save_to_database(result)
        
        self.search_complete.emit()
        
    def _on_llm_error(self, error):
        """处理 LLM 错误"""
        print(f"✗ 大模型错误: {error}")
        self.error_occurred.emit(f"大模型推理失败: {error}")
        self.search_complete.emit()
        
    def _save_to_database(self, result):
        """保存到数据库（静默）"""
        try:
            question = result.get("question", "")
            answer = result.get("answer", "")
            project = result.get("project", "默认项目")
            
            if question and answer:
                # 如果有 embedding service，生成向量
                vector_data = None
                if self.embedding_service.is_available():
                    vector_data = self.embedding_service.encode_text(question)
                
                success = self.db_service.insert_question(
                    question=question,
                    options="",
                    answer=answer,
                    source="ai_generated",
                    project=project,
                    vector_data=vector_data
                )
                
                if success:
                    print("✓ 题目已保存到数据库")
                else:
                    print("✗ 保存到数据库失败")
                    
        except Exception as e:
            print(f"保存到数据库时出错: {e}")