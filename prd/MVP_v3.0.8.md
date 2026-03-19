# 天一阁 PRD v3.0.8

**版本**: v3.0.8  
**日期**: 2026-03-19  
**阶段**: MVP + WebSocket 实时通信 + Agent RAG 工具集成

---

## 📋 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0.8 | 2026-03-19 | WebSocket 实时通信 + Agent RAG 工具 + 工作流编排 |
| v3.0.7 | 2026-03-17 | 异步任务队列 + Celery + Redis 架构 |
| v3.0.6 | 2026-03-16 | API 服务层完整实现 |
| v3.0.5 | 2026-03-10 | RAG 引擎与高级搜索实现 |
| v3.0.3 | 2026-03-07 | Agent 框架、文档解析器、工作流引擎 |

---

## 📅 本次迭代目标

### 核心交付物
- [ ] **WebSocket 连接管理器**: 实现实时双向通信，支持任务进度推送
- [ ] **Agent RAG 工具**: 将 RAG 检索能力封装为 Agent Tool
- [ ] **文档工作流编排**: 端到端文档处理流程的状态机管理
- [ ] **Celery Worker 启动脚本**: 便捷的 worker 启动和监控工具
- [ ] **Docker 配置**: 完整的容器化部署方案

---

## 🎯 一、WebSocket 实时通信

### 1.1 技术方案

| 组件 | 技术 | 说明 |
|------|------|------|
| WebSocket 框架 | **FastAPI WebSocket** | 原生支持，与现有 API 集成 |
| 连接管理 | **ConnectionManager** | 用户级连接池管理 |
| 消息格式 | **JSON** | 标准化消息结构 |
| 认证方式 | **JWT Token** | URL 查询参数传递 |

### 1.2 消息类型定义

```python
# WebSocket 消息类型枚举
class WSMessageType(str, Enum):
    # 系统消息
    PING = "ping"                    # 心跳
    PONG = "pong"                    # 心跳响应
    AUTH = "auth"                    # 认证
    AUTH_SUCCESS = "auth_success"    # 认证成功
    AUTH_FAILED = "auth_failed"      # 认证失败
    
    # 任务进度
    TASK_CREATED = "task_created"    # 任务创建
    TASK_STARTED = "task_started"    # 任务开始
    TASK_PROGRESS = "task_progress"  # 进度更新
    TASK_COMPLETED = "task_completed" # 任务完成
    TASK_FAILED = "task_failed"      # 任务失败
    TASK_CANCELLED = "task_cancelled" # 任务取消
    
    # 文档处理
    DOC_UPLOADED = "doc_uploaded"    # 文档上传
    DOC_PARSING = "doc_parsing"      # 解析中
    DOC_CHUNKING = "doc_chunking"    # 切分中
    DOC_EMBEDDING = "doc_embedding"  # 向量化中
    DOC_INDEXING = "doc_indexing"    # 索引中
    DOC_COMPLETED = "doc_completed"  # 处理完成
    DOC_FAILED = "doc_failed"        # 处理失败
    
    # 通知
    NOTIFICATION = "notification"    # 一般通知
```

### 1.3 ConnectionManager 设计

```python
class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # 用户ID -> WebSocket 连接集合
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> 用户信息
        self.connection_info: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """建立连接"""
        await websocket.accept()
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        self.connection_info[websocket] = {"user_id": user_id}
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """断开连接"""
        info = self.connection_info.pop(websocket, None)
        if info:
            user_id = info["user_id"]
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(websocket)
    
    async def send_to_user(self, user_id: str, message: dict) -> None:
        """发送消息给指定用户的所有连接"""
        if user_id in self.user_connections:
            disconnected = []
            for ws in self.user_connections[user_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(ws)
            # 清理断开的连接
            for ws in disconnected:
                await self.disconnect(ws)
    
    async def broadcast(self, message: dict) -> None:
        """广播给所有连接"""
        for user_id, connections in self.user_connections.items():
            for ws in connections:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass
```

### 1.4 WebSocket 端点

```python
@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    manager: ConnectionManager = Depends(get_connection_manager)
):
    """WebSocket 连接端点"""
    # 验证 JWT Token
    user = await verify_token(token)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    # 建立连接
    await manager.connect(websocket, user.id)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": now()})
            elif msg_type == "subscribe_task":
                # 订阅任务进度
                task_id = data.get("task_id")
                # 添加到订阅列表
            # ... 其他消息处理
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
```

---

## 🎯 二、Agent RAG 工具集成

### 2.1 设计目标

将 RAG 检索能力封装为 Agent Tool，使 Agent 能够：
- 检索相关知识库内容
- 基于检索结果回答问题
- 引用来源文档

### 2.2 RAGTool 实现

```python
class RAGTool(BaseTool):
    """RAG 检索工具 - 为 Agent 提供知识库检索能力"""
    
    name = "rag_search"
    description = """检索知识库中的相关文档，返回基于检索结果的回答。
    
    参数:
    - query: 用户的问题或查询语句
    - top_k: 返回的相关文档数量 (默认 5)
    - filters: 可选的过滤条件，如分类、标签、时间范围等
    
    返回:
    - answer: 基于检索结果生成的回答
    - sources: 引用的来源文档列表
    - confidence: 回答的置信度
    """
    
    def __init__(
        self,
        rag_engine: RAGEngine,
        search_service: SearchService
    ):
        self.rag_engine = rag_engine
        self.search_service = search_service
    
    async def execute(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """执行 RAG 检索"""
        
        # 构建 RAG 查询
        rag_query = RAGQuery(
            query=query,
            top_k=top_k,
            search_mode=SearchMode.HYBRID,
            filters=filters or {},
            generate_answer=True,
            include_sources=True
        )
        
        # 执行检索
        result = await self.rag_engine.query(rag_query)
        
        # 格式化输出
        return {
            "answer": result.answer,
            "sources": [
                {
                    "document_id": src.document_id,
                    "document_title": src.document_title,
                    "chunk_index": src.chunk_index,
                    "content": src.content[:200] + "..." if len(src.content) > 200 else src.content,
                    "score": src.relevance_score
                }
                for src in result.sources
            ],
            "confidence": result.confidence,
            "retrieval_time_ms": result.retrieval_time_ms
        }
```

### 2.3 工具注册

```python
# 在 Agent 初始化时注册工具
def register_rag_tools(agent: BaseAgent, rag_engine: RAGEngine, search_service: SearchService):
    """为 Agent 注册 RAG 相关工具"""
    
    # RAG 检索工具
    rag_tool = RAGTool(rag_engine, search_service)
    agent.register_tool(rag_tool)
    
    # 简单搜索工具（仅返回文档列表）
    search_tool = SearchTool(search_service)
    agent.register_tool(search_tool)
```

### 2.4 Agent 集成示例

```python
class KnowledgeAgent(BaseAgent):
    """知识库问答 Agent"""
    
    system_prompt = """你是一个知识库助手，专门回答关于文档内容的问题。
    
    当用户提问时：
    1. 使用 rag_search 工具检索相关知识
    2. 基于检索结果生成回答
    3. 明确引用来源文档
    4. 如果检索结果不足以回答问题，请说明
    """
    
    def __init__(self, rag_engine: RAGEngine, search_service: SearchService):
        super().__init__()
        register_rag_tools(self, rag_engine, search_service)
```

---

## 🎯 三、文档工作流编排

### 3.1 状态机设计

```
┌──────────┐    upload      ┌──────────┐    parse       ┌──────────┐
│  PENDING │ ────────────▶ │ UPLOADED │ ────────────▶ │ PARSING  │
└──────────┘               └──────────┘               └────┬─────┘
                                                           │
                                                           ▼
┌──────────┐   complete    ┌──────────┐   index      ┌──────────┐
│COMPLETED │ ◀──────────── │ INDEXING │ ◀─────────── │EMBEDDING │
└──────────┘               └──────────┘               └────┬─────┘
     ▲                                                     │
     │                                                     ▼
┌────┴─────┐   chunk       ┌──────────┐  embed       ┌──────────┐
│  FAILED  │ ◀──────────── │ CHUNKING │ ◀─────────── │  PARSED  │
└──────────┘               └──────────┘               └──────────┘
     ▲
     │ (任何阶段都可能失败)
     └──────────────────────────────────────────────────────────
```

### 3.2 WorkflowEngine 实现

```python
class DocumentWorkflowEngine:
    """文档处理工作流引擎"""
    
    def __init__(
        self,
        db: AsyncSession,
        celery_app: Celery,
        ws_manager: ConnectionManager
    ):
        self.db = db
        self.celery_app = celery_app
        self.ws_manager = ws_manager
    
    async def start_workflow(
        self,
        document_id: str,
        user_id: str,
        options: Optional[Dict] = None
    ) -> str:
        """启动文档处理工作流"""
        
        # 创建工作流任务
        workflow_task = DocumentProcessingTask(
            id=generate_uuid(),
            document_id=document_id,
            user_id=user_id,
            status=TaskStatus.PENDING,
            current_step=WorkflowStep.PENDING,
            created_at=datetime.utcnow()
        )
        self.db.add(workflow_task)
        await self.db.commit()
        
        # 启动 Celery 任务链
        task_chain = (
            process_document_upload.s(document_id, user_id)
            | parse_document.s()
            | chunk_document.s()
            | generate_embeddings.s()
            | index_document.s()
        )
        
        result = task_chain.apply_async()
        
        # 更新任务 ID
        workflow_task.celery_task_id = result.id
        await self.db.commit()
        
        # 发送 WebSocket 通知
        await self._notify_user(user_id, {
            "type": "task_created",
            "task_id": workflow_task.id,
            "document_id": document_id,
            "status": "pending"
        })
        
        return workflow_task.id
    
    async def _notify_user(self, user_id: str, message: dict):
        """发送 WebSocket 通知"""
        await self.ws_manager.send_to_user(user_id, message)
    
    async def get_workflow_status(self, task_id: str) -> Optional[Dict]:
        """获取工作流状态"""
        task = await self.db.get(DocumentProcessingTask, task_id)
        if not task:
            return None
        
        return {
            "task_id": task.id,
            "document_id": task.document_id,
            "status": task.status.value,
            "current_step": task.current_step.value,
            "progress": task.progress_percent,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message
        }
```

### 3.3 任务回调更新状态

```python
@celery_app.task(bind=True)
def process_document_step(self, document_id: str, step: str, user_id: str):
    """处理文档工作流步骤"""
    
    # 更新任务状态
    update_task_status.delay(
        task_id=self.request.id,
        status=TaskStatus.PROCESSING.value,
        step=step,
        progress=get_step_progress(step)
    )
    
    # 发送进度通知
    send_ws_notification.delay(
        user_id=user_id,
        message={
            "type": f"doc_{step}",
            "document_id": document_id,
            "progress": get_step_progress(step)
        }
    )
    
    # 执行实际处理逻辑...
```

---

## 🎯 四、Celery Worker 启动脚本

### 4.1 启动脚本

```bash
#!/bin/bash
# scripts/start_worker.sh

WORKER_NAME=${1:-"worker1"}
LOG_LEVEL=${2:-"info"}
CONCURRENCY=${3:-4}

echo "🚀 Starting Celery Worker: $WORKER_NAME"
echo "   Log Level: $LOG_LEVEL"
echo "   Concurrency: $CONCURRENCY"

celery -A skyone_shuge.core.celery_app worker \
    --hostname="$WORKER_NAME@%h" \
    --loglevel="$LOG_LEVEL" \
    --concurrency="$CONCURRENCY" \
    --queues=documents,embeddings,index,notifications \
    -E  # 启用事件监控
```

### 4.2 Python 启动器

```python
#!/usr/bin/env python3
# src/skyone_shuge/cli/worker.py

import click
from skyone_shuge.core.celery_app import celery_app

@click.group()
def worker():
    """Celery Worker 管理命令"""
    pass

@worker.command()
@click.option("--name", default="worker1", help="Worker 名称")
@click.option("--log-level", default="info", help="日志级别")
@click.option("--concurrency", default=4, help="并发数")
@click.option("--queues", default="documents,embeddings,index,notifications", help="队列列表")
def start(name: str, log_level: str, concurrency: int, queues: str):
    """启动 Celery Worker"""
    celery_app.worker_main([
        "worker",
        f"--hostname={name}@%h",
        f"--loglevel={log_level}",
        f"--concurrency={concurrency}",
        f"--queues={queues}",
        "-E"
    ])

@worker.command()
def status():
    """查看 Worker 状态"""
    inspect = celery_app.control.inspect()
    active = inspect.active()
    stats = inspect.stats()
    
    click.echo("📊 Celery Worker 状态")
    click.echo("=" * 40)
    if stats:
        for worker_name, info in stats.items():
            click.echo(f"Worker: {worker_name}")
            click.echo(f"  - 处理中任务: {len(active.get(worker_name, []))}")
            click.echo(f"  - 总任务数: {info.get('total', {})}")
    else:
        click.echo("❌ 无可用 Worker")

if __name__ == "__main__":
    worker()
```

---

## 🎯 五、Docker 配置

### 5.1 docker-compose.yml

```yaml
version: "3.8"

services:
  # Redis - Celery Broker & Backend
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  # API 服务
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///data/app.db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    depends_on:
      - redis
    command: uvicorn skyone_shuge.api.main:app --host 0.0.0.0 --port 8000 --reload

  # Celery Worker
  worker:
    build: .
    environment:
      - DATABASE_URL=sqlite:///data/app.db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    depends_on:
      - redis
      - api
    command: celery -A skyone_shuge.core.celery_app worker --loglevel=info --concurrency=4

  # Flower - Celery 监控 (可选)
  flower:
    image: mher/flower:latest
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis

volumes:
  redis_data:
```

### 5.2 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY src/ ./src/
COPY prd/ ./prd/
COPY architecture/ ./architecture/

# 设置 Python 路径
ENV PYTHONPATH=/app/src:$PYTHONPATH

# 创建数据目录
RUN mkdir -p /app/data /app/uploads

EXPOSE 8000

CMD ["uvicorn", "skyone_shuge.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📁 文件结构

```
skyone-shuge/
├── docker-compose.yml              # Docker 编排配置
├── Dockerfile                      # API 服务镜像
├── scripts/
│   └── start_worker.sh             # Worker 启动脚本
├── src/skyone_shuge/
│   ├── api/
│   │   └── routers/
│   │       └── websocket.py        # WebSocket 端点
│   ├── core/
│   │   └── connection_manager.py   # WebSocket 连接管理
│   ├── agents/
│   │   └── tools/
│   │       └── rag_tool.py         # Agent RAG 工具
│   ├── workflows/
│   │   ├── __init__.py
│   │   └── document_workflow.py    # 文档工作流引擎
│   └── cli/
│       └── worker.py               # Worker CLI
├── prd/
│   └── MVP_v3.0.8.md               # 本 PRD 文档
└── architecture/
    └── ARCHITECTURE_v3.0.8.md      # 架构文档
```

---

## ✅ 验收标准

### WebSocket
- [ ] 客户端可通过 JWT Token 建立 WebSocket 连接
- [ ] 支持心跳检测 (ping/pong)
- [ ] 任务进度更新实时推送到客户端
- [ ] 用户级消息隔离，不会收到其他用户的通知

### Agent RAG 工具
- [ ] RAGTool 成功注册到 Agent 工具列表
- [ ] Agent 可调用 rag_search 工具检索知识库
- [ ] 返回结果包含回答、来源引用、置信度
- [ ] 支持过滤条件（分类、标签等）

### 工作流编排
- [ ] 文档上传后自动触发工作流
- [ ] 每个处理步骤状态可追踪
- [ ] 失败后可重试或查看错误详情
- [ ] WebSocket 实时推送各阶段进度

### 部署
- [ ] `docker-compose up` 一键启动所有服务
- [ ] Worker 自动消费任务队列
- [ ] Flower 可监控任务执行情况

---

## 📧 邮件发送

**发送命令**:
```bash
# 发送代码包邮件
python scripts/send_code_email.py

# 发送 PRD 邮件
python scripts/send_prd_email.py --version v3.0.8
```

**收件人**: broadbtinp@gmail.com, dulie@foxmail.com
