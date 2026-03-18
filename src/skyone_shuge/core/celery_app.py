"""
天一阁 - Celery 应用配置
"""

from celery import Celery
from skyone_shuge.core.config import settings

# 创建 Celery 应用实例
celery_app = Celery(
    "skyone_shuge",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "skyone_shuge.tasks.document_tasks",
        "skyone_shuge.tasks.embedding_tasks",
        "skyone_shuge.tasks.index_tasks",
        "skyone_shuge.tasks.notification_tasks",
    ]
)

# 任务序列化配置
celery_app.conf.task_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.result_serializer = "json"
celery_app.conf.timezone = "Asia/Shanghai"
celery_app.conf.enable_utc = True

# 任务追踪与超时配置
celery_app.conf.task_track_started = True
celery_app.conf.task_time_limit = 3600  # 1小时硬超时
celery_app.conf.task_soft_time_limit = 3300  # 55分钟软超时
celery_app.conf.result_expires = 86400  # 结果24小时过期

# Worker 性能配置
celery_app.conf.worker_prefetch_multiplier = 1  # 公平调度，避免长任务阻塞
celery_app.conf.task_acks_late = True  # 任务完成后确认
celery_app.conf.worker_concurrency = 4  # 默认并发数

# 队列路由配置 - 按任务类型分发到不同队列
celery_app.conf.task_routes = {
    "skyone_shuge.tasks.document_tasks.*": {"queue": "documents"},
    "skyone_shuge.tasks.embedding_tasks.*": {"queue": "embeddings"},
    "skyone_shuge.tasks.index_tasks.*": {"queue": "index"},
    "skyone_shuge.tasks.notification_tasks.*": {"queue": "notifications"},
}

# 任务默认配置
celery_app.conf.task_default_queue = "default"
celery_app.conf.task_default_exchange = "default"
celery_app.conf.task_default_routing_key = "default"

# 定时任务配置 (可选)
celery_app.conf.beat_schedule = {
    "cleanup-old-tasks": {
        "task": "skyone_shuge.tasks.notification_tasks.cleanup_old_tasks",
        "schedule": 3600.0,  # 每小时执行一次
    },
}


def get_task_info(task_id: str) -> dict:
    """获取任务状态信息"""
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
