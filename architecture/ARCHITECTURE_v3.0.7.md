# 天一阁 架构设计文档 v3.0.7

**版本**: v3.0.7  
**日期**: 2026-03-17  
**架构状态**: 异步任务队列与工作流集成

---

## 1. 架构变更记录

| 版本 | 日期 | 核心变更 |
|------|------|----------|
| v3.0.7 | 2026-03-17 | 引入 Celery + Redis 异步任务队列，文档端到端工作流，Agent RAG 工具 |
| v3.0.6 | 2026-03-16 | 完整 API 服务层：10 个路由模块 + 扩展 Schemas |
| v3.0.5 | 2026-03-10 | 新增 `RAGEngine` 与 `SearchService` |

---

## 2. 异步任务队列架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI 应用层                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ API 路由    │  │ WebSocket   │  │ Agent 工具              │  │
│  │ 接收请求    │──│ 进度推送    │  │ 集成                    │  │
│  └──────┬──────┘  └─────────────┘  └─────────────────────────┘  │
└─────────┼───────────────────────────────────────────────────────┘
          │
          │ 提交任务
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Celery 任务队列层                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Redis Broker                         │   │
│  │              (任务队列 + 结果存储)                      │   │
│  └────────────────────┬────────────────────────────────────┘   │
│                       │                                         │
│  ┌────────────────────▼────────────────────────────────────┐   │
│  │                  Celery Workers                         │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │   │
│  │  │ Worker-1     │ │ Worker-2     │ │ Worker-N     │    │   │
│  │  │ (文档处理)   │ │ (Embedding)  │ │ (索引)       │    │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │
          │ 执行任务
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        业务逻辑层                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Parser      │  │ RAGEngine   │  │ VectorDB    │             │
│  │ 文档解析    │  │ 检索生成    │  │ 向量操作    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Celery 配置详解

**位置**: `src/skyone_shuge/core/celery_app.py`

```python
from celery import Celery
from skyone_shuge.core.config import settings

celery_app = Celery(
    "skyone_shuge",
    broker=settings.CELERY_BROKER_URL,      # Redis 作为 Broker
    backend=settings.CELERY_RESULT_BACKEND,  # Redis 存储结果
    include=[
        "skyone_shuge.tasks.document_tasks",
        "skyone_shuge.tasks.embedding_tasks", 
        "skyone_shuge.tasks.index_tasks",
        "skyone_shuge.tasks.notification_tasks",
    ]
)

# 任务序列化配置
celery_app.conf.task_serializer = 'json'
celery_app.conf.accept_content = ['json']
celery_app.conf.result_serializer = 'json'
celery_app.conf.result_expires = 86400  # 结果24小时过期

# Worker 性能配置
celery_app.conf.worker_prefetch_multiplier = 1  # 公平调度，避免长任务阻塞
celery_app.conf.task_acks_late = True           # 任务完成后确认
celery_app.conf.task_time_limit = 3600          # 单任务1小时超时
celery_app.conf.task_soft_time_limit = 3300     # 软超时55分钟

# 队列路由配置
celery_app.conf.task_routes = {
    'skyone_shuge.tasks.document_tasks.*': {'queue': 'documents'},
    'skyone_shuge.tasks.embedding_tasks.*': {'queue': 'embeddings'},
    'skyone_shuge.tasks.index_tasks.*': {'queue': 'index'},
}

# 定时任务配置 (可选)
celery_app.conf.beat_schedule = {
    'cleanup-old-tasks': {
        'task': 'skyone_shuge.tasks.maintenance.cleanup_old_tasks',
        'schedule': 86400.0,  # 每天执行
    },
}
```

### 2.3 任务模块设计

#### 文档处理任务 (`tasks/document_tasks.py`)

```python
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, document_id: str, file_path: str):
    """
    文档处理主任务
    
    Args:
        document_id: 文档ID
        file_path: 文件临时路径
    
    Returns:
        Dict: 处理结果
    """
    try:
        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'parsing', 'progress': 10}
        )
        
        # 1. 解析文档
        parsed_content = parse_document_file(file_path)
        
        self.update_state(
            state='PROGRESS', 
            meta={'stage': 'chunking', 'progress': 30}
        )
        
        # 2. 文本切分
        chunks = chunk_text(parsed_content)
        
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'embedding', 'progress': 50}
        )
        
        # 3. 生成 Embedding (调用 embedding_tasks)
        embedding_task = generate_embeddings.delay(document_id, chunks)
        
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'indexing', 'progress': 80}
        )
        
        # 4. 索引文档
        index_document.delay(document_id, embedding_task.get())
        
        return {
            'document_id': document_id,
            'status': 'completed',
            'chunks_count': len(chunks)
        }
        
    except SoftTimeLimitExceeded:
        # 软超时处理
        logger.warning(f"Document {document_id} processing soft timeout")
        raise self.retry(countdown=300)
        
    except Exception as exc:
        logger.error(f"Document processing failed: {exc}")
        # 重试3次后仍失败
        if self.request.retries >= 3:
            update_document_status(document_id, 'failed', str(exc))
        raise self.retry(exc=exc)
```

#### Embedding 任务 (`tasks/embedding_tasks.py`)

```python
@shared_task(bind=True)
def generate_embeddings(self, document_id: str, chunks: List[str]):
    """批量生成文本嵌入向量"""
    from skyone_shuge.ml.embedding import EmbeddingService
    
    embedding_service = EmbeddingService()
    embeddings = []
    
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        # 每10个更新一次进度
        if i % 10 == 0:
            self.update_state(
                state='PROGRESS',
                meta={'current': i, 'total': total, 'percent': int(i/total*100)}
            )
        
        embedding = embedding_service.embed_text(chunk)
        embeddings.append(embedding)
    
    # 保存到临时存储
    save_embeddings_temp(document_id, embeddings)
    
    return {'document_id': document_id, 'embedding_count': len(embeddings)}
```

#### 索引任务 (`tasks/index_tasks.py`)

```python
@shared_task(bind=True)
def index_document(self, document_id: str, embedding_result: Dict):
    """将向量索引到 Qdrant"""
    from skyone_shuge.ml.vector_db import VectorDB
    
    vector_db = VectorDB()
    embeddings = load_embeddings_temp(document_id)
    
    # 批量入库
    vector_db.upsert_vectors(
        collection="documents",
        vectors=embeddings,
        metadata={'document_id': document_id}
    )
    
    # 更新文档状态
    update_document_status(document_id, 'indexed')
    
    return {'document_id': document_id, 'status': 'indexed'}
```

---

## 3. 文档端到端工作流

### 3.1 状态机设计

```
                    ┌──────────────────────────────────────┐
                    │                                      │
                    ▼                                      │
┌──────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐  │
│ UPLOADED │──▶│ PARSING │──▶│ CHUNKING │──▶│EMBEDDING│  │
└──────────┘   └────┬────┘   └────┬─────┘   └────┬─────┘  │
     │              │             │              │         │
     │              │             │              │         │
     │         ┌────▼─────────────▼──────────────▼────┐   │
     │         │                                       │   │
     └────────▶│              FAILED                   │───┘
               │                                       │
               └───────────────────────────────────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │    COMPLETED     │
                              └──────────────────┘
```

### 3.2 数据流设计

| 阶段 | 输入 | 输出 | 数据存储 |
|------|------|------|----------|
| UPLOADED | HTTP Multipart File | 临时文件路径 | 本地磁盘 `./uploads/temp/` |
| PARSING | 临时文件路径 | 纯文本内容 | 内存 / 临时表 |
| CHUNKING | 纯文本内容 | 文本块列表 | `document_chunks` 表 |
| EMBEDDING | 文本块列表 | 向量列表 | Redis 临时存储 |
| INDEXING | 向量列表 | 索引确认 | Qdrant + 元数据表 |
| COMPLETED | - | 完成状态 | `documents` 表状态更新 |

### 3.3 新增数据模型

**文档处理任务表**:

```python
# models/processing_task.py
from sqlalchemy import Column, String, Integer, DateTime, Enum, JSON, ForeignKey, Text
from skyone_shuge.models.base import Base
import enum

class ProcessingStage(enum.Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskStatus(enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DocumentProcessingTask(Base):
    __tablename__ = "document_processing_tasks"
    
    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    celery_task_id = Column(String(255), nullable=True, index=True)
    
    # 当前阶段和状态
    stage = Column(Enum(ProcessingStage), default=ProcessingStage.UPLOADED)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100
    
    # 各阶段详情
    stage_results = Column(JSON, default=dict)  # {"parsing": {...}, "chunking": {...}}
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    
    # 时间戳
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## 4. WebSocket 实时通知

### 4.1 架构设计

```python
# core/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio

class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # task_id -> Set[WebSocket]
        self.task_connections: Dict[str, Set[WebSocket]] = {}
        # user_id -> Set[WebSocket]
        self.user_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect_to_task(self, websocket: WebSocket, task_id: str):
        """客户端连接到特定任务"""
        await websocket.accept()
        if task_id not in self.task_connections:
            self.task_connections[task_id] = set()
        self.task_connections[task_id].add(websocket)
    
    def disconnect_from_task(self, websocket: WebSocket, task_id: str):
        """断开任务连接"""
        if task_id in self.task_connections:
            self.task_connections[task_id].discard(websocket)
    
    async def broadcast_to_task(self, task_id: str, message: Dict):
        """广播消息给任务的所有订阅者"""
        if task_id not in self.task_connections:
            return
        
        disconnected = []
        for connection in self.task_connections[task_id]:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.task_connections[task_id].discard(conn)

# 全局管理器实例
manager = ConnectionManager()
```

### 4.2 WebSocket 路由

```python
# api/routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from skyone_shuge.core.websocket import manager

router = APIRouter()

@router.websocket("/ws/tasks/{task_id}")
async def task_websocket(websocket: WebSocket, task_id: str):
    """
    WebSocket 端点：订阅任务进度
    
    消息格式:
    - 客户端 -> 服务端: {"action": "subscribe"}
    - 服务端 -> 客户端: {"type": "progress", "progress": 50, ...}
    """
    await manager.connect_to_task(websocket, task_id)
    try:
        while True:
            # 保持连接，接收心跳
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect_from_task(websocket, task_id)
```

### 4.3 任务进度推送

```python
# tasks/notification_tasks.py
from celery import shared_task
from skyone_shuge.core.websocket import manager
import asyncio

@shared_task
def push_task_progress(task_id: str, document_id: str, stage: str, progress: int):
    """推送任务进度到 WebSocket"""
    message = {
        "type": "task_progress",
        "task_id": task_id,
        "document_id": document_id,
        "stage": stage,
        "progress": progress,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # 使用 asyncio 运行异步函数
    asyncio.run(manager.broadcast_to_task(task_id, message))
```

---

## 5. Agent 工具集成

### 5.1 RAG Tool 实现

```python
# agents/tools/rag_tool.py
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class RAGSearchInput(BaseModel):
    """RAG 搜索输入参数"""
    query: str = Field(description="搜索查询语句")
    top_k: int = Field(default=5, description="返回结果数量")
    category_id: Optional[str] = Field(None, description="分类过滤")
    tag_ids: Optional[list] = Field(None, description="标签过滤")
    date_from: Optional[str] = Field(None, description="开始日期")
    date_to: Optional[str] = Field(None, description="结束日期")

class RAGTool:
    """RAG 检索工具"""
    
    name = "knowledge_search"
    description = """搜索知识库中的文档内容。
    
    当用户询问关于特定主题、概念、技术细节时，使用此工具检索相关知识。
    
    示例:
    - "什么是第一性原理？"
    - "找一下机器学习的相关资料"
    - "总结文档中关于 AI 的观点"
    """
    
    args_schema = RAGSearchInput
    
    def __init__(self, rag_engine):
        self.rag_engine = rag_engine
    
    async def run(
        self,
        query: str,
        top_k: int = 5,
        category_id: Optional[str] = None,
        tag_ids: Optional[list] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """执行检索"""
        
        # 构建过滤器
        filters = {}
        if category_id:
            filters["category_id"] = category_id
        if tag_ids:
            filters["tag_ids"] = tag_ids
        if kwargs.get('date_from'):
            filters["date_from"] = kwargs['date_from']
        if kwargs.get('date_to'):
            filters["date_to"] = kwargs['date_to']
        
        # 执行 RAG 查询
        result = await self.rag_engine.query(
            query=query,
            top_k=top_k,
            filters=filters if filters else None
        )
        
        # 格式化返回结果
        return {
            "query": query,
            "answer": result.answer,
            "confidence": result.confidence,
            "sources": [
                {
                    "document_id": s.document_id,
                    "title": s.title or s.file_name,
                    "content_preview": s.content[:200] + "..." if len(s.content) > 200 else s.content,
                    "similarity": round(s.similarity_score, 3)
                }
                for s in result.sources
            ],
            "total_sources": result.total_sources,
            "response_time_ms": result.took
        }
```

### 5.2 Agent 注册

```python
# agents/registry.py
from skyone_shuge.agents.tools.rag_tool import RAGTool

class AgentRegistry:
    """Agent 工具注册中心"""
    
    def __init__(self):
        self.tools: Dict[str, Any] = {}
        self.rag_engine = None
    
    def initialize_rag(self, rag_engine):
        """初始化 RAG 引擎"""
        self.rag_engine = rag_engine
        self.register_tool(RAGTool(rag_engine))
    
    def register_tool(self, tool):
        """注册工具"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[Any]:
        """获取工具"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict]:
        """列出所有可用工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools.values()
        ]

# 全局注册表
registry = AgentRegistry()
```

---

## 6. 部署配置

### 6.1 Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
      - qdrant

  celery_worker:
    build: .
    command: celery -A skyone_shuge.core.celery_app worker --loglevel=info --concurrency=4
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
      - qdrant

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  redis_data:
  qdrant_data:
```

### 6.2 环境变量

```bash
# .env
# Celery 配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_ALWAYS_EAGER=false  # 生产环境设为 false

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# Worker 配置
WORKER_CONCURRENCY=4
WORKER_MAX_TASKS_PER_CHILD=1000
```

---

## 7. 项目结构

```
skyone-shuge/
├── src/skyone_shuge/
│   ├── agents/
│   │   ├── base.py
│   │   ├── registry.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       └── rag_tool.py          # RAG Agent 工具
│   ├── api/
│   │   ├── main.py
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── documents.py
│   │       ├── websocket.py         # WebSocket 路由 (新增)
│   │       └── ...
│   ├── core/
│   │   ├── celery_app.py            # Celery 配置 (新增)
│   │   ├── websocket.py             # WebSocket 管理器 (新增)
│   │   └── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── processing_task.py       # 处理任务模型 (新增)
│   ├── schemas/
│   │   └── websocket.py             # WebSocket 消息模型 (新增)
│   └── tasks/                        # Celery 任务模块 (新增)
│       ├── __init__.py
│       ├── document_tasks.py
│       ├── embedding_tasks.py
│       ├── index_tasks.py
│       └── notification_tasks.py
├── celery_worker.py                  # Worker 启动入口
├── docker-compose.yml
└── requirements.txt
```

---

**文档结束**
