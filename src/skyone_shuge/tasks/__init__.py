"""
天一阁 - 异步任务模块

提供 Celery 异步任务支持，包括：
- 文档处理任务 (document_tasks)
- 文本嵌入任务 (embedding_tasks)
- 索引管理任务 (index_tasks)
- 通知推送任务 (notification_tasks)

使用示例:
    from skyone_shuge.tasks import process_document_upload
    
    # 提交文档处理任务
    task = process_document_upload.delay(document_id, file_path)
    print(f"任务已提交: {task.id}")
"""

from skyone_shuge.tasks.document_tasks import (
    process_document_upload,
    parse_document,
    chunk_document,
    generate_embeddings,
    build_index,
    cleanup_document,
)

from skyone_shuge.tasks.embedding_tasks import (
    generate_text_embedding,
    generate_batch_embeddings,
    compute_similarity,
    cleanup_embedding_cache,
)

from skyone_shuge.tasks.index_tasks import (
    add_document_to_index,
    update_document_index,
    rebuild_collection_index,
    sync_metadata_to_index,
    cleanup_orphan_vectors,
    optimize_index,
)

from skyone_shuge.tasks.notification_tasks import (
    send_websocket_notification,
    broadcast_task_progress,
    notify_document_processed,
    send_email_notification,
    cleanup_old_tasks,
    notify_system_alert,
)

__all__ = [
    # 文档任务
    "process_document_upload",
    "parse_document",
    "chunk_document",
    "generate_embeddings",
    "build_index",
    "cleanup_document",
    # 嵌入任务
    "generate_text_embedding",
    "generate_batch_embeddings",
    "compute_similarity",
    "cleanup_embedding_cache",
    # 索引任务
    "add_document_to_index",
    "update_document_index",
    "rebuild_collection_index",
    "sync_metadata_to_index",
    "cleanup_orphan_vectors",
    "optimize_index",
    # 通知任务
    "send_websocket_notification",
    "broadcast_task_progress",
    "notify_document_processed",
    "send_email_notification",
    "cleanup_old_tasks",
    "notify_system_alert",
]
