# 天一阁架构文档 v3.0.8

**版本**: v3.0.8  
**日期**: 2026-03-19  
**主题**: WebSocket 实时通信 + Agent RAG 工具 + 工作流编排

---

## 1. 架构概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              客户端层                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                      │
│  │  Web UI     │  │  Mobile     │  │  Agent      │                      │
│  │  (React)    │  │  (iOS/安卓)  │  │  (AI)       │                      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                      │
└─────────┼────────────────┼────────────────┼──────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              API 网关层                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │
│  │  REST API       │  │  WebSocket      │  │  GraphQL        │          │
│  │  (FastAPI)      │  │  (实时通信)      │  │  (可选)         │          │
│  └────────┬────────┘  └────────┬────────┘  └─────────────────┘          │
└───────────┼────────────────────┼─────────────────────────────────────────┘
            │                    │
            ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              业务服务层                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Auth       │  │  Document   │  │  Search     │  │  RAG        │     │
│  │  Service    │  │  Service    │  │  Service    │  │  Engine     │     │
│  └─────────────┘  └──────┬──────┘  └─────────────┘  └──────┬──────┘     │
│                          │                                  │            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Workflow   │  │  Agent      │  │  Task       │  │  Notify     │     │
│  │  Engine     │  │  Tools      │  │  Queue      │  │  Service    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              任务队列层                                  │
│                    ┌─────────────────────────┐                          │
│                    │      Celery + Redis     │                          │
│                    │  ┌─────────┐ ┌────────┐ │                          │
│                    │  │documents│ │embeddings│                          │
│                    │  └─────────┘ └────────┘ │                          │
│                    │  ┌─────────┐ ┌────────┐ │                          │
│                    │  │  index  │ │notifications│                       │
│                    │  └─────────┘ └────────┘ │                          │
│                    └─────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              数据存储层                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  SQLite/    │  │  Qdrant     │  │  Redis      │  │  File       │     │
│  │  PostgreSQL │  │  (向量库)    │  │  (缓存/队列) │  │  Storage    │     │
│  │  (元数据)    │  │  (Embeddings)│  │  (Broker)   │  │  (上传文件)  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. WebSocket 实时通信架构

### 2.1 组件交互图

```
┌─────────────┐                    ┌─────────────┐
│   Client    │◄──── WebSocket ───►│   Server    │
│  (Browser)  │    bidirectional   │  (FastAPI)  │
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       │  1. Connect with JWT             │
       │─────────────────────────────────►│
       │                                  │
       │  2. Connection Accepted          │
       │◄─────────────────────────────────│
       │                                  │
       │  3. Subscribe Task Progress      │
       │─────────────────────────────────►│
       │                                  │
       │         ┌──────────────┐         │
       │         │   Celery     │         │
       │         │   Worker     │         │
       │         └──────┬───────┘         │
       │                │                 │
       │                │ Task Update     │
       │                │────────────────►│
       │                                  │
       │  4. Progress Update (WS Push)    │
       │◄─────────────────────────────────│
       │                                  │
       │  5. Task Completed               │
       │◄─────────────────────────────────│
```

### 2.2 ConnectionManager 类图

```
┌─────────────────────────────────────────────────────────┐
│                    ConnectionManager                    │
├─────────────────────────────────────────────────────────┤
│ - user_connections: Dict[str, Set[WebSocket]]           │
│ - connection_info: Dict[WebSocket, Dict]                │
├─────────────────────────────────────────────────────────┤
│ + connect(websocket, user_id): None                     │
│ + disconnect(websocket): None                           │
│ + send_to_user(user_id, message): None                  │
│ + send_to_connection(websocket, message): None          │
│ + broadcast(message): None                              │
│ + get_user_connections(user_id): Set[WebSocket]         │
└─────────────────────────────────────────────────────────┘
```

### 2.3 消息格式规范

```python
# 基础消息结构
{
    "type": "message_type",      # 消息类型
    "timestamp": "2026-03-19T23:00:00Z",  # ISO8601 时间戳
    "payload": { ... }           # 具体数据
}

# 任务进度消息
{
    "type": "task_progress",
    "timestamp": "2026-03-19T23:00:00Z",
    "payload": {
        "task_id": "uuid",
        "document_id": "uuid",
        "status": "processing",
        "step": "embedding",
        "progress": 65,           # 0-100
        "message": "正在生成向量嵌入..."
    }
}

# 心跳消息
{
    "type": "ping",
    "timestamp": "2026-03-19T23:00:00Z"
}

# 心跳响应
{
    "type": "pong",
    "timestamp": "2026-03-19T23:00:00Z"
}
```

---

## 3. Agent RAG 工具架构

### 3.1 工具注册流程

```
┌──────────────────────────────────────────────────────────┐
│                      Agent 初始化                         │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│               register_rag_tools(agent)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  RAGTool    │  │ SearchTool  │  │  DocTool    │       │
│  │ (rag_search)│  │(search_docs)│  │ (get_doc)   │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
└─────────┼────────────────┼────────────────┼──────────────┘
          │                │                │
          ▼                ▼                ▼
┌──────────────────────────────────────────────────────────┐
│                   Agent.tool_registry                     │
│  {                                                        │
│    "rag_search": RAGTool(),                              │
│    "search_docs": SearchTool(),                          │
│    "get_doc": DocTool()                                  │
│  }                                                        │
└──────────────────────────────────────────────────────────┘
```

### 3.2 RAGTool 调用流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Agent    │────►│   RAGTool   │────►│  RAGEngine  │
│             │     │             │     │             │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                    │
                           │    RAGQuery        │
                           │───────────────────►│
                           │                    │
                           │    RAGResponse     │
                           │◄───────────────────│
                           │                    │
                    ┌──────┴──────┐     ┌──────┴──────┐
                    │ SearchService│     │  LLMService │
                    │  (retrieve)  │     │  (generate) │
                    └─────────────┘     └─────────────┘
```

### 3.3 工具接口定义

```python
class BaseTool(ABC):
    """Agent 工具基类"""
    
    name: str
    description: str
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具逻辑"""
        pass
    
    def to_openai_function(self) -> Dict:
        """转换为 OpenAI Function 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema()
            }
        }

class RAGTool(BaseTool):
    """RAG 检索工具"""
    
    name = "rag_search"
    description = "检索知识库并生成回答"
    
    async def execute(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        # 实现检索逻辑
        pass
```

---

## 4. 文档工作流编排架构

### 4.1 状态机状态定义

```python
class WorkflowStep(Enum):
    """文档处理工作流步骤"""
    PENDING = "pending"           # 等待开始
    UPLOADED = "uploaded"         # 已上传
    PARSING = "parsing"           # 解析中
    PARSED = "parsed"             # 解析完成
    CHUNKING = "chunking"         # 切分中
    CHUNKED = "chunked"           # 切分完成
    EMBEDDING = "embedding"       # 向量化中
    EMBEDDED = "embedded"         # 向量化完成
    INDEXING = "indexing"         # 索引中
    COMPLETED = "completed"       # 完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 取消

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

### 4.2 工作流执行流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  PENDING  │────►│ UPLOADED │────►│ PARSING  │────►│  PARSED  │
└──────────┘     └──────────┘     └──────────┘     └────┬─────┘
                                                         │
                    ┌──────────┐     ┌──────────┐        │
◄───────────────────│ COMPLETED│◄────│ INDEXING │◄───────┤
│                   └──────────┘     └──────────┘        │
│                                                        ▼
│  ┌──────────┐     ┌──────────┐     ┌──────────┐  ┌──────────┐
└──│  FAILED  │◄────│ EMBEDDING│◄────│ CHUNKING │◄─│ CHUNKED  │
   └──────────┘     └──────────┘     └──────────┘  └──────────┘
        ▲
        │ (错误处理)
        └─────────────────────────────────────────────────────
```

### 4.3 Celery 任务链

```python
# 文档处理任务链
from celery import chain

workflow_chain = chain(
    # Step 1: 验证和预处理
    validate_document.s(document_id),
    
    # Step 2: 解析文档
    parse_document.s(),
    
    # Step 3: 文本切分
    chunk_document.s(),
    
    # Step 4: 生成向量嵌入
    generate_embeddings.s(),
    
    # Step 5: 索引到向量库
    index_to_vectorstore.s()
)

# 启动任务链
result = workflow_chain.apply_async()
```

### 4.4 任务状态追踪

```python
class DocumentProcessingTask(Base):
    """文档处理任务模型"""
    
    __tablename__ = "document_processing_tasks"
    
    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.id"))
    user_id = Column(String, ForeignKey("users.id"))
    
    # Celery 任务 ID
    celery_task_id = Column(String, nullable=True)
    
    # 状态
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    current_step = Column(Enum(WorkflowStep), default=WorkflowStep.PENDING)
    
    # 进度 (0-100)
    progress_percent = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    
    # 处理结果
    result_data = Column(JSON, default={})
```

---

## 5. 部署架构

### 5.1 Docker Compose 架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker Network                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    API      │  │   Worker    │  │      Flower         │  │
│  │   Service   │  │   Service   │  │    (Monitor)        │  │
│  │   :8000     │  │             │  │     :5555           │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────┘  │
│         │                │                                   │
│         └────────────────┼───────────────────┐               │
│                          │                   │               │
│                   ┌──────┴──────┐     ┌──────┴──────┐       │
│                   │    Redis    │     │   Qdrant    │       │
│                   │   :6379     │     │   :6333     │       │
│                   │  (Broker)   │     │ (Vector DB) │       │
│                   └─────────────┘     └─────────────┘       │
│                                                             │
│  Volumes:                                                   │
│   - app_data:/app/data      (SQLite)                        │
│   - uploads:/app/uploads    (上传文件)                       │
│   - redis_data:/data        (Redis 持久化)                   │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 服务依赖关系

```
              ┌─────────────┐
              │    Redis    │
              │   (基础)     │
              └──────┬──────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│    API      │ │   Worker    │ │   Flower    │
│   Service   │ │   Service   │ │   (可选)     │
└──────┬──────┘ └─────────────┘ └─────────────┘
       │
       ▼
┌─────────────┐
│   Qdrant    │
│ (向量检索)   │
└─────────────┘
```

### 5.3 环境变量配置

```bash
# 数据库
DATABASE_URL=sqlite:///data/app.db
# DATABASE_URL=postgresql://user:pass@postgres:5432/db

# Redis / Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Qdrant 向量库
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=

# OpenAI / Embedding
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 文件上传
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=104857600  # 100MB
```

---

## 6. 性能考虑

### 6.1 WebSocket 连接优化

| 优化策略 | 实现方式 | 效果 |
|---------|---------|------|
| 连接池管理 | ConnectionManager 维护用户-连接映射 | 支持多设备同时在线 |
| 心跳检测 | 30 秒 ping/pong | 及时清理死连接 |
| 消息批处理 | 任务进度累计后批量发送 | 减少网络开销 |
| 自动重连 | 客户端指数退避重连 | 提高连接稳定性 |

### 6.2 Celery 性能调优

```python
# celery_app.py 性能配置
celery_app.conf.update(
    # 并发模型
    worker_pool="prefork",  # 多进程
    
    # 预取配置
    worker_prefetch_multiplier=1,  # 公平调度，避免任务堆积
    
    # 任务超时
    task_time_limit=3600,  # 1 小时硬超时
    task_soft_time_limit=3300,  # 55 分钟软超时
    
    # 重试配置
    task_default_retry_delay=60,  # 默认 60 秒后重试
    task_max_retries=3,  # 最大重试 3 次
    
    # 结果后端
    result_expires=3600,  # 结果 1 小时后过期
    
    # 任务确认
    task_acks_late=True,  # 任务完成后确认，防止 Worker 崩溃丢失任务
    
    # 优先级队列
    task_queue_max_priority=10,
    task_default_priority=5,
)
```

### 6.3 数据库优化

```python
# 异步连接池
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,           # 连接池大小
    max_overflow=30,        # 最大溢出连接
    pool_timeout=30,        # 连接超时
    pool_recycle=1800,      # 连接回收时间
    echo=False
)
```

---

## 7. 监控与日志

### 7.1 Flower 监控指标

```
┌─────────────────────────────────────────────────────────┐
│                      Flower Dashboard                    │
├─────────────────────────────────────────────────────────┤
│  Workers: 4 active                                       │
│  Tasks:                                                 │
│    - Processed: 1,234                                   │
│    - Failed: 12 (0.97%)                                 │
│    - Active: 5                                          │
│    - Scheduled: 0                                       │
│  Queues:                                                │
│    - documents: 2 pending                               │
│    - embeddings: 0 pending                              │
│    - index: 1 pending                                   │
│    - notifications: 0 pending                           │
└─────────────────────────────────────────────────────────┘
```

### 7.2 日志结构

```json
{
    "timestamp": "2026-03-19T23:00:00.123Z",
    "level": "INFO",
    "logger": "skyone_shuge.workflows.document",
    "message": "Document workflow started",
    "context": {
        "task_id": "uuid",
        "document_id": "uuid",
        "user_id": "uuid",
        "step": "parsing"
    },
    "trace_id": "abc-123-def",
    "span_id": "xyz-789-uvw"
}
```

---

## 8. 安全考虑

### 8.1 WebSocket 安全

| 措施 | 实现 |
|-----|------|
| 认证 | JWT Token 通过 URL 参数传递，验证后才接受连接 |
| 授权 | 用户只能订阅自己的任务进度 |
| 限流 | 每用户最大 3 个并发连接 |
| 超时 | 空闲连接 5 分钟后自动断开 |

### 8.2 任务安全

| 措施 | 实现 |
|-----|------|
| 输入验证 | 所有任务参数使用 Pydantic 模型验证 |
| 沙箱执行 | 文档解析在受限环境中执行 |
| 资源限制 | 单个任务最大 1GB 内存、1 小时执行时间 |
| 审计日志 | 所有任务操作记录到数据库 |

---

## 9. 文件清单

```
skyone-shuge/
├── docker-compose.yml              # Docker 编排
├── Dockerfile                      # 服务镜像
├── scripts/
│   └── start_worker.sh             # Worker 启动脚本
├── src/skyone_shuge/
│   ├── api/
│   │   ├── main.py                 # FastAPI 应用入口
│   │   ├── deps.py                 # 依赖注入
│   │   └── routers/
│   │       ├── websocket.py        # WebSocket 端点
│   │       └── tasks.py            # 任务 API
│   ├── core/
│   │   ├── celery_app.py           # Celery 配置
│   │   └── connection_manager.py   # WebSocket 管理
│   ├── agents/
│   │   └── tools/
│   │       ├── base.py             # 工具基类
│   │       ├── rag_tool.py         # RAG 工具
│   │       └── search_tool.py      # 搜索工具
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── document_workflow.py    # 工作流引擎
│   │   └── steps.py                # 工作流步骤定义
│   ├── tasks/
│   │   ├── document_tasks.py       # 文档任务
│   │   ├── embedding_tasks.py      # 嵌入任务
│   │   ├── index_tasks.py          # 索引任务
│   │   └── notification_tasks.py   # 通知任务
│   └── cli/
│       └── worker.py               # Worker CLI
└── docs/
    ├── prd/MVP_v3.0.8.md           # PRD 文档
    └── architecture/ARCHITECTURE_v3.0.8.md  # 本文件
```

---

**更新时间**: 2026-03-19 23:00
