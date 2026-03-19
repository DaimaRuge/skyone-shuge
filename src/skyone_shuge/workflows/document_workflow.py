"""
文档处理工作流引擎
管理文档端到端处理流程
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from celery import chain, group, chord
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...core.celery_app import celery_app
from ...core.connection_manager import ConnectionManager, get_connection_manager
from ...models.document import Document

logger = logging.getLogger(__name__)


class WorkflowStep(Enum):
    """文档处理工作流步骤"""
    PENDING = "pending"
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    PARSING = "parsing"
    PARSED = "parsed"
    CHUNKING = "chunking"
    CHUNKED = "chunked"
    EMBEDDING = "embedding"
    EMBEDDED = "embedded"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# 步骤进度映射
STEP_PROGRESS = {
    WorkflowStep.PENDING: 0,
    WorkflowStep.UPLOADED: 5,
    WorkflowStep.VALIDATING: 10,
    WorkflowStep.PARSING: 20,
    WorkflowStep.PARSED: 35,
    WorkflowStep.CHUNKING: 40,
    WorkflowStep.CHUNKED: 55,
    WorkflowStep.EMBEDDING: 60,
    WorkflowStep.EMBEDDED: 80,
    WorkflowStep.INDEXING: 85,
    WorkflowStep.COMPLETED: 100,
    WorkflowStep.FAILED: 0,
    WorkflowStep.CANCELLED: 0,
}


class DocumentWorkflowEngine:
    """文档处理工作流引擎
    
    管理文档从上传到索引的完整处理流程：
    1. 上传验证
    2. 文档解析
    3. 文本切分
    4. 向量嵌入
    5. 索引入库
    
    支持实时进度推送、错误重试、状态追踪。
    """
    
    def __init__(
        self,
        db: AsyncSession,
        celery_app=celery_app,
        ws_manager: Optional[ConnectionManager] = None
    ):
        self.db = db
        self.celery_app = celery_app
        self.ws_manager = ws_manager or get_connection_manager()
        logger.info("DocumentWorkflowEngine initialized")
    
    async def start_workflow(
        self,
        document_id: str,
        user_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """启动文档处理工作流
        
        Args:
            document_id: 文档ID
            user_id: 用户ID
            options: 处理选项（如切分大小、嵌入模型等）
            
        Returns:
            工作流任务ID
        """
        from ...tasks.document_tasks import process_document_task
        
        logger.info(f"Starting workflow for document: {document_id}")
        
        # 启动 Celery 任务
        task = process_document_task.delay(
            document_id=document_id,
            user_id=user_id,
            options=options or {}
        )
        
        # 通知用户
        await self._notify_user(user_id, {
            "type": "task_created",
            "payload": {
                "task_id": task.id,
                "document_id": document_id,
                "status": TaskStatus.PENDING.value,
                "step": WorkflowStep.PENDING.value,
                "progress": 0
            }
        })
        
        return task.id
    
    async def cancel_workflow(self, task_id: str, user_id: str) -> bool:
        """取消正在执行的工作流
        
        Args:
            task_id: Celery 任务ID
            user_id: 用户ID
            
        Returns:
            是否成功取消
        """
        try:
            # 撤销 Celery 任务
            self.celery_app.control.revoke(
                task_id,
                terminate=True,
                signal='SIGTERM'
            )
            
            # 通知用户
            await self._notify_user(user_id, {
                "type": "task_cancelled",
                "payload": {
                    "task_id": task_id,
                    "status": TaskStatus.CANCELLED.value
                }
            })
            
            logger.info(f"Workflow cancelled: task_id={task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel workflow: {e}")
            return False
    
    async def retry_workflow(
        self,
        document_id: str,
        user_id: str,
        from_step: Optional[WorkflowStep] = None
    ) -> str:
        """重试失败的工作流
        
        Args:
            document_id: 文档ID
            user_id: 用户ID
            from_step: 从哪个步骤开始重试
            
        Returns:
            新的任务ID
        """
        logger.info(f"Retrying workflow for document: {document_id}")
        return await self.start_workflow(document_id, user_id)
    
    async def get_workflow_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态
        
        Args:
            task_id: Celery 任务ID
            
        Returns:
            状态信息字典
        """
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id, app=self.celery_app)
        
        # 获取任务元数据
        status_map = {
            "PENDING": TaskStatus.PENDING,
            "STARTED": TaskStatus.PROCESSING,
            "SUCCESS": TaskStatus.COMPLETED,
            "FAILURE": TaskStatus.FAILED,
            "REVOKED": TaskStatus.CANCELLED,
            "RETRY": TaskStatus.PROCESSING
        }
        
        task_status = status_map.get(result.status, TaskStatus.PENDING)
        
        return {
            "task_id": task_id,
            "status": task_status.value,
            "celery_status": result.status,
            "result": result.result if result.successful() else None,
            "traceback": result.traceback if result.failed() else None
        }
    
    async def _notify_user(self, user_id: str, message: Dict[str, Any]) -> None:
        """发送 WebSocket 通知给用户
        
        Args:
            user_id: 用户ID
            message: 消息内容
        """
        try:
            await self.ws_manager.send_to_user(user_id, message)
        except Exception as e:
            logger.warning(f"Failed to notify user {user_id}: {e}")
    
    async def update_document_status(
        self,
        document_id: str,
        status: str,
        step: Optional[str] = None,
        progress: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> None:
        """更新文档处理状态
        
        Args:
            document_id: 文档ID
            status: 状态
            step: 当前步骤
            progress: 进度百分比
            error_message: 错误信息
        """
        try:
            doc = await self.db.get(Document, document_id)
            if doc:
                doc.processing_status = status
                if step:
                    doc.current_step = step
                if progress is not None:
                    doc.processing_progress = progress
                if error_message:
                    doc.error_message = error_message
                await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update document status: {e}")
            await self.db.rollback()


def get_step_progress(step: WorkflowStep) -> int:
    """获取步骤对应的进度百分比
    
    Args:
        step: 工作流步骤
        
    Returns:
        进度百分比 (0-100)
    """
    return STEP_PROGRESS.get(step, 0)


# Celery 任务定义
@celery_app.task(bind=True, max_retries=3)
def update_task_progress(
    self,
    task_id: str,
    step: str,
    progress: int,
    user_id: str
) -> Dict[str, Any]:
    """更新任务进度（Celery 任务）
    
    此任务用于在工作流执行过程中更新进度并通知用户。
    """
    import asyncio
    
    async def _notify():
        ws_manager = get_connection_manager()
        await ws_manager.send_to_user(user_id, {
            "type": "task_progress",
            "payload": {
                "task_id": task_id,
                "step": step,
                "progress": progress
            }
        })
    
    try:
        # 运行异步通知
        asyncio.run(_notify())
        return {"success": True, "task_id": task_id, "step": step}
    except Exception as exc:
        logger.error(f"Failed to update progress: {exc}")
        # 重试
        raise self.retry(exc=exc, countdown=5)
