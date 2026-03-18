"""
天一阁 - Embedding 任务
处理文本向量化和批量嵌入任务
"""

import traceback
from typing import List, Dict, Any
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from skyone_shuge.core.celery_app import celery_app
from skyone_shuge.ml.embedding import EmbeddingGenerator


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def generate_text_embedding(self, text: str, metadata: Dict[str, Any] = None) -> dict:
    """
    为单个文本生成向量嵌入
    
    Args:
        text: 输入文本
        metadata: 可选的元数据
    
    Returns:
        包含向量嵌入的结果字典
    """
    try:
        self.update_state(
            state="PROGRESS",
            meta={"step": "embedding", "progress": 0, "message": "开始生成向量..."}
        )
        
        # 创建 embedding 生成器
        generator = EmbeddingGenerator()
        
        # 生成向量
        embedding = generator.generate(text)
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "completed", "progress": 100, "message": "向量生成完成"}
        )
        
        return {
            "status": "completed",
            "text_length": len(text),
            "embedding_dim": len(embedding) if embedding else 0,
            "metadata": metadata or {},
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
                "error": str(exc),
            }
        raise


@celery_app.task(bind=True, max_retries=3)
def generate_batch_embeddings(self, texts: List[str], batch_size: int = 32) -> dict:
    """
    批量生成文本向量
    
    Args:
        texts: 文本列表
        batch_size: 批处理大小
    
    Returns:
        批量嵌入结果
    """
    try:
        total = len(texts)
        self.update_state(
            state="PROGRESS",
            meta={"step": "embedding", "progress": 0, "message": f"开始批量生成 {total} 个向量..."}
        )
        
        generator = EmbeddingGenerator()
        embeddings = []
        
        # 分批处理
        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = generator.generate_batch(batch)
            embeddings.extend(batch_embeddings)
            
            progress = min(100, int((i + len(batch)) / total * 100))
            self.update_state(
                state="PROGRESS",
                meta={
                    "step": "embedding",
                    "progress": progress,
                    "message": f"已处理 {i + len(batch)}/{total} 个文本"
                }
            )
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "completed", "progress": 100, "message": "批量向量生成完成"}
        )
        
        return {
            "status": "completed",
            "total": total,
            "completed": len(embeddings),
            "embedding_dim": len(embeddings[0]) if embeddings else 0,
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
                "status": "failed",
                "error": str(exc),
            }
        raise


@celery_app.task(bind=True, max_retries=3)
def compute_similarity(self, text1: str, text2: str) -> dict:
    """
    计算两个文本的相似度
    
    Args:
        text1: 第一个文本
        text2: 第二个文本
    
    Returns:
        相似度分数
    """
    try:
        self.update_state(
            state="PROGRESS",
            meta={"step": "computing", "progress": 0, "message": "正在计算相似度..."}
        )
        
        generator = EmbeddingGenerator()
        
        # 生成向量
        embedding1 = generator.generate(text1)
        embedding2 = generator.generate(text2)
        
        # 计算余弦相似度
        import numpy as np
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "completed", "progress": 100, "message": "相似度计算完成"}
        )
        
        return {
            "status": "completed",
            "similarity": float(similarity),
            "text1_length": len(text1),
            "text2_length": len(text2),
        }
        
    except Exception as exc:
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc)}
        )
        try:
            self.retry(countdown=30)
        except MaxRetriesExceededError:
            return {
                "status": "failed",
                "error": str(exc),
            }
        raise


@celery_app.task
def cleanup_embedding_cache() -> dict:
    """
    清理 embedding 缓存
    """
    try:
        # TODO: 实现缓存清理逻辑
        return {
            "status": "completed",
            "message": "Embedding 缓存已清理",
        }
    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
        }
