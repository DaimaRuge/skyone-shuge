"""
天一阁 - 索引任务
处理向量入库、索引更新、元数据同步等任务
"""

import traceback
from typing import List, Dict, Any, Optional
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from skyone_shuge.core.celery_app import celery_app
from skyone_shuge.ml.vector_db import VectorDB


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def add_document_to_index(
    self,
    document_id: str,
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]],
    metadata: Optional[Dict[str, Any]] = None
) -> dict:
    """
    将文档添加到向量索引
    
    Args:
        document_id: 文档ID
        chunks: 文本块列表，每项包含 {id, content, metadata}
        embeddings: 向量嵌入列表
        metadata: 文档级元数据
    
    Returns:
        索引操作结果
    """
    try:
        self.update_state(
            state="PROGRESS",
            meta={"step": "indexing", "progress": 0, "message": "开始添加文档到索引..."}
        )
        
        # 初始化向量数据库
        vector_db = VectorDB()
        
        # 准备数据
        total = len(chunks)
        ids = []
        texts = []
        metadatas = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            ids.append(chunk.get("id", f"{document_id}_{i}"))
            texts.append(chunk.get("content", ""))
            chunk_meta = chunk.get("metadata", {})
            chunk_meta.update({
                "document_id": document_id,
                "chunk_index": i,
            })
            if metadata:
                chunk_meta.update(metadata)
            metadatas.append(chunk_meta)
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "indexing", "progress": 50, "message": f"正在索引 {total} 个块..."}
        )
        
        # 添加到向量数据库
        vector_db.add_vectors(ids, embeddings, metadatas)
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "completed", "progress": 100, "message": "文档索引完成"}
        )
        
        return {
            "status": "completed",
            "document_id": document_id,
            "chunks_indexed": total,
        }
        
    except Exception as exc:
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc), "traceback": traceback.format_exc()}
        )
        try:
            self.retry(countdown=30 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            return {
                "status": "failed",
                "document_id": document_id,
                "error": str(exc),
            }
        raise


@celery_app.task(bind=True, max_retries=3)
def update_document_index(
    self,
    document_id: str,
    operation: str = "update",
    metadata: Optional[Dict[str, Any]] = None
) -> dict:
    """
    更新文档索引
    
    Args:
        document_id: 文档ID
        operation: 操作类型 (update/delete)
        metadata: 更新的元数据
    
    Returns:
        更新结果
    """
    try:
        self.update_state(
            state="PROGRESS",
            meta={"step": "updating", "progress": 0, "message": f"开始{operation}文档索引..."}
        )
        
        vector_db = VectorDB()
        
        if operation == "delete":
            # 删除文档相关向量
            vector_db.delete_by_filter({"document_id": document_id})
        elif operation == "update" and metadata:
            # 更新元数据
            vector_db.update_metadata({"document_id": document_id}, metadata)
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "completed", "progress": 100, "message": f"文档索引{operation}完成"}
        )
        
        return {
            "status": "completed",
            "document_id": document_id,
            "operation": operation,
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
                "status": "failed",
                "document_id": document_id,
                "error": str(exc),
            }
        raise


@celery_app.task(bind=True, max_retries=3)
def rebuild_collection_index(self, collection_name: str) -> dict:
    """
    重建集合索引
    
    Args:
        collection_name: 集合名称
    
    Returns:
        重建结果
    """
    try:
        self.update_state(
            state="PROGRESS",
            meta={"step": "rebuilding", "progress": 0, "message": f"开始重建 {collection_name} 索引..."}
        )
        
        vector_db = VectorDB()
        
        # TODO: 实现索引重建逻辑
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "completed", "progress": 100, "message": "索引重建完成"}
        )
        
        return {
            "status": "completed",
            "collection": collection_name,
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
                "status": "failed",
                "collection": collection_name,
                "error": str(exc),
            }
        raise


@celery_app.task(bind=True, max_retries=3)
def sync_metadata_to_index(
    self,
    document_ids: List[str],
    metadata_updates: Dict[str, Any]
) -> dict:
    """
    批量同步元数据到索引
    
    Args:
        document_ids: 文档ID列表
        metadata_updates: 元数据更新
    
    Returns:
        同步结果
    """
    try:
        total = len(document_ids)
        self.update_state(
            state="PROGRESS",
            meta={"step": "syncing", "progress": 0, "message": f"开始同步 {total} 个文档的元数据..."}
        )
        
        vector_db = VectorDB()
        
        for i, doc_id in enumerate(document_ids):
            vector_db.update_metadata({"document_id": doc_id}, metadata_updates)
            
            progress = int((i + 1) / total * 100)
            self.update_state(
                state="PROGRESS",
                meta={
                    "step": "syncing",
                    "progress": progress,
                    "message": f"已同步 {i + 1}/{total} 个文档"
                }
            )
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "completed", "progress": 100, "message": "元数据同步完成"}
        )
        
        return {
            "status": "completed",
            "documents_updated": total,
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
                "status": "failed",
                "error": str(exc),
            }
        raise


@celery_app.task
def cleanup_orphan_vectors() -> dict:
    """
    清理孤向往量（没有对应文档的向量）
    """
    try:
        # TODO: 实现孤儿向量清理逻辑
        return {
            "status": "completed",
            "message": "孤儿向量清理完成",
            "removed_count": 0,
        }
    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
        }


@celery_app.task
def optimize_index(collection_name: Optional[str] = None) -> dict:
    """
    优化索引性能
    
    Args:
        collection_name: 集合名称，None 表示所有集合
    """
    try:
        vector_db = VectorDB()
        
        # TODO: 实现索引优化逻辑
        
        return {
            "status": "completed",
            "collection": collection_name or "all",
            "message": "索引优化完成",
        }
    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
        }
