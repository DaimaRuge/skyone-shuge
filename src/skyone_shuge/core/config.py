"""
天一阁 - 配置管理
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    APP_NAME: str = "天一阁"
    APP_VERSION: str = "3.0.6"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./skyone_shuge.db"
    
    # 文件存储配置
    STORAGE_TYPE: str = "local"  # local, s3, oss
    UPLOAD_DIR: str = "./data/uploads"
    VECTOR_STORE_DIR: str = "./data/vector_store"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: list = [
        "pdf", "txt", "md", "doc", "docx", "xls", "xlsx",
        "ppt", "pptx", "epub", "mobi"
    ]
    
    # 向量数据库配置
    VECTOR_DB_TYPE: str = "chroma"  # chroma, milvus, qdrant
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    
    # LLM 配置
    LLM_PROVIDER: str = "ark"  # openai, ark, anthropic
    LLM_API_KEY: Optional[str] = None
    LLM_API_BASE: Optional[str] = None
    LLM_MODEL: str = "doubao-seed-2.0-code"
    LLM_EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000
    
    # OCR 配置
    OCR_ENABLED: bool = True
    OCR_PROVIDER: str = "paddle"  # paddle, tesseract
    
    # 检索配置
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_SIMILARITY_THRESHOLD: float = 0.7
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 前端配置
    FRONTEND_URL: str = "http://localhost:5173"
    
    # 异步任务队列配置
    TASK_QUEUE_ENABLED: bool = True
    TASK_QUEUE_TYPE: str = "celery"  # rq, celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery 配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_TASK_TIMEOUT: int = 3600  # 1小时
    
    # 机器学习模型配置
    ML_EMBEDDING_PROVIDER: str = "ark"  # openai, ark, sentence_transformers
    ML_EMBEDDING_MODEL: str = "doubao-text-embedding-v3"
    ML_EMBEDDING_DIM: int = 1536
    
    # RAG 配置
    RAG_ENABLED: bool = True
    RAG_CHUNK_SIZE: int = 1024
    RAG_CHUNK_OVERLAP: int = 128
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.7
    
    # 分析与统计配置
    ANALYTICS_ENABLED: bool = True
    ANALYTICS_RETENTION_DAYS: int = 90
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    """获取配置单例"""
    return Settings()


settings = get_settings()
