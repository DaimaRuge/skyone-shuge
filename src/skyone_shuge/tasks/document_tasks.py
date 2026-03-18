"""
天一阁 - 文档处理任务
处理文档上传、解析、格式转换等任务
"""

import os
import traceback
from typing import Optional
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from skyone_shuge.core.celery_app import celery_app
from skyone_shuge.core.config import settings
from skyone_shuge.agents.document_processor import DocumentProcessorAgent
from skyone_shuge.models.document import Document
from skyone_shuge.core.database import get_db_session


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document_upload(self, document_id: str, file_path: str) -> dict:
    """
    文档上传后处理任务
    
    任务链：上传 → 解析 → 切分 → 向量化 → 索引
    """
    try:
        # 更新任务状态
        self.update_state(
            state="PROGRESS",
            meta={"step": "started", "progress": 0, "message": "开始处理文档..."}
        )
        
        # 1. 验证文件存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "parsing", "progress": 10, "message": "正在解析文档..."}
        )
        
        # 2. 调用文档解析任务
        parse_result = parse_document.delay(document_id, file_path)
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "chunking", "progress": 30, "message": "正在切分文本..."}
        )
        
        # 3. 调用文本切分任务
        chunk_result = chunk_document.delay(document_id)
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "embedding", "progress": 50, "message": "正在生成向量..."}
        )
        
        # 4. 调用向量化任务
        embedding_result = generate_embeddings.delay(document_id)
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "indexing", "progress": 80, "message": "正在构建索引..."}
        )
        
        # 5. 调用索引任务
        index_result = build_index.delay(document_id)
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "completed", "progress": 100, "message": "文档处理完成"}
        )
        
        return {
            "document_id": document_id,
            "status": "completed",
            "tasks": {
                "parse": parse_result.id,
                "chunk": chunk_result.id,
                "embedding": embedding_result.id,
                "index": index_result.id,
            }
        }
        
    except Exception as exc:
        # 更新任务状态为失败
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc), "traceback": traceback.format_exc()}
        )
        
        # 重试机制
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {
                "document_id": document_id,
                "status": "failed",
                "error": str(exc),
            }
        raise


@celery_app.task(bind=True, max_retries=3)
def parse_document(self, document_id: str, file_path: str) -> dict:
    """
    解析文档内容
    
    支持格式：PDF, TXT, MD, DOC, DOCX, EPUB, MOBI
    """
    try:
        self.update_state(
            state="PROGRESS",
            meta={"step": "parsing", "progress": 0, "message": "开始解析文档..."}
        )
        
        # 创建文档处理器
        processor = DocumentProcessorAgent()
        
        # 解析文档
        with open(file_path, "rb") as f:
            content = processor.parse_document(f, os.path.basename(file_path))
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "completed", "progress": 100, "message": "文档解析完成"}
        )
        
        return {
            "document_id": document_id,
            "status": "completed",
            "content_length": len(content) if content else 0,
        }
        
    except Exception as exc:
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc), "traceback": traceback.format_exc()}
        )
        try:
            self.retry(countdown=60)
        except MaxRetriesExceededError:
            return {
                "document_id": document_id,
                "status": "failed",
                "error": str(exc),
            }
        raise


@celery_app.task(bind=True, max_retries=3)
def chunk_document(self, document_id: str) -> dict:
    """
    将文档切分为文本块
    """
    try:
        self.update_state(
            state="PROGRESS",
            meta={"step": "chunking", "progress": 0, "message": "开始切分文本..."}
        )
        
        # TODO: 从数据库获取文档内容并切分
        # 这里需要与实际的文档存储逻辑对接
        
        chunk_count = 0  # 实际切分后获取
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "completed", "progress": 100, "message": f"文本切分完成，共 {chunk_count} 块"}
        )
        
        return {
            "document_id": document_id,
            "status": "completed",
            "chunk_count": chunk_count,
        }
        
    except Exception as exc:
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc)}
        )
        try:
            self.retry(countdown=60)
        except MaxRetriesExceededError:
            return {
                "document_id": document_id,
                "status": "failed",
                "error": str(exc),
            }
        raise


@celery_app.task(bind=True, max_retries=3)
def generate_embeddings(self, document_id: str) -> dict:
    """
    为文档块生成向量嵌入
    """
    try:
        self.update_state(
            state="PROGRESS",
            meta={"step": "embedding", "progress": 0, "message": "开始生成向量..."}
        )
        
        # TODO: 调用 embedding 服务生成向量
        
        embedding_count = 0
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "completed", "progress": 100, "message": f"向量生成完成，共 {embedding_count} 个"}
        )
        
        return {
            "document_id": document_id,
            "status": "completed",
            "embedding_count": embedding_count,
        }
        
    except Exception as exc:
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc)}
        )
        try:
            self.retry(countdown=60)
        except MaxRetriesExceededError:
            return {
                "document_id": document_id,
                "status": "failed",
                "error": str(exc),
            }
        raise


@celery_app.task(bind=True, max_retries=3)
def build_index(self, document_id: str) -> dict:
    """
    构建文档索引
    """
    try:
        self.update_state(
            state="PROGRESS",
            meta={"step": "indexing", "progress": 0, "message": "开始构建索引..."}
        )
        
        # TODO: 调用 vector_db 服务构建索引
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "completed", "progress": 100, "message": "索引构建完成"}
        )
        
        return {
            "document_id": document_id,
            "status": "completed",
        }
        
    except Exception as exc:
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc)}
        )
        try:
            self.retry(countdown=60)
        except MaxRetriesExceededError:
            return {
                "document_id": document_id,
                "status": "failed",
                "error": str(exc),
            }
        raise


@celery_app.task
def cleanup_document(file_path: str) -> dict:
    """
    清理临时文档文件
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"file_path": file_path, "status": "deleted"}
        return {"file_path": file_path, "status": "not_found"}
    except Exception as exc:
        return {"file_path": file_path, "status": "error", "error": str(exc)}
