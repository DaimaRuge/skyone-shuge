# 天一阁 PRD v3.0.7

**版本**: v3.0.7  
**日期**: 2026-03-17  
**阶段**: MVP + 异步任务队列与工作流集成

---

## 📋 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0.7 | 2026-03-17 | 异步任务队列 + 文档工作流集成 + 前后端联调方案 |
| v3.0.6 | 2026-03-16 | API 服务层完整实现：10 个路由模块 + 扩展 Schemas |
| v3.0.5 | 2026-03-10 | RAG 引擎与高级搜索实现（混合搜索、重排序） |
| v3.0.3 | 2026-03-07 | Agent 框架、文档解析器、工作流引擎实现 |

---

## 📅 迭代记录 (v3.0.7)

### 本次迭代完成目标
- [ ] **异步任务队列架构**：引入 Celery + Redis 实现真正的异步后台任务运行逻辑
- [ ] **任务执行引擎**：实现 TaskExecutor 与 Celery Worker 对接，支持长耗时任务异步处理
- [ ] **文档端到端流程**：整合文档上传 → 解析 → 切分 → 向量化 → 索引的完整工作流
- [ ] **Agent 工作流接入**：将 RAG 检索能力作为 Agent Tool 对外暴露
- [ ] **前后端联调方案**：定义 API 对接规范、数据格式、错误处理机制
- [ ] **WebSocket 实时通知**：实现任务进度实时推送机制

---

## 🎯 一、异步任务队列架构

### 1.1 技术选型

| 组件 | 技术 | 说明 |
|------|------|------|
| 任务队列 | **Celery** | 成熟的分布式任务队列，支持定时任务、任务链、结果存储 |
| 消息代理 | **Redis** | 高性能内存数据库，作为 Celery 的 Broker 和 Backend |
| 结果存储 | Redis + SQLite | 任务结果临时存储于 Redis，持久化记录存储于 SQLite |
| 监控工具 | Flower (可选) | Celery 实时监控界面，查看任务状态、Worker 状态 |

### 1.2 Celery 配置

**位置**: `src/skyone_shuge/core/celery_app.py`

```python
from celery import Celery

celery_app = Celery(
    "skyone_shuge",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=[
        "skyone_shuge.tasks.document_tasks",
        "skyone_shuge.tasks.embedding_tasks",
        "skyone_shuge.tasks.index_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    worker_prefetch_multiplier=1,  # 公平调度
)
```

### 1.3 任务模块划分

| 模块 | 路径 | 职责 |
|------|------|------|
| 文档任务 | `tasks/document_tasks.py` | 文档上传、解析、格式转换 |
| Embedding 任务 | `tasks/embedding_tasks.py` | 文本切分、向量化计算 |
| 索引任务 | `tasks/index_tasks.py` | 向量入库、索引更新、元数据同步 |
| 通知任务 | `tasks/notification_tasks.py` | WebSocket 推送、邮件通知 |

### 1.4 核心任务定义

#### 文档处理任务链

```python
@app.task(bind=True, max_retries=3)
def process_document_upload(self, document_id: str, file_path: str):
    """文档上传后处理任务链"""
    try:
        # 1. 文档解析
        parse_result = parse_document.delay(document_id, file_path)
        
        # 2. 文本切分
        chunks = chunk_document.delay(document_id)
        
        # 3. 向量化
        embeddings = generate_embeddings.delay(document_id)
        
        # 4. 索引入库
        index_result = index_document.delay(document_id)
        
        return {
            "document_id": document_id,
            "status": "completed",
            "tasks": [parse_result.id, chunks.id, embeddings.id, index_result.id]
        }
    except Exception as exc:
        self.retry(countdown=60, exc=exc)
```

#### 批量索引任务

```python
@app.task(bind=True)
def batch_index_documents(self, document_ids: List[str]):
    """批量文档索引任务"""
    total = len(document_ids)
    for i, doc_id in enumerate(document_ids):
        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={'current': i + 1, 'total': total, 'percent': int((i + 1) / total * 100)}
        )
        # 处理单个文档
        process_single_document.delay(doc_id)
```

---

## 🏗️ 二、文档端到端工作流

### 2.1 完整流程图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   文件上传   │────▶│  文件验证   │────▶│  存储到磁盘  │────▶│  触发任务   │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
                                                                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  索引完成   │◀────│  向量入库   │◀────│  生成Embedding│◀────│  文档解析   │
└──────┬──────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│ WebSocket   │────▶│  前端通知   │
│  进度推送   │     │  处理完成   │
└─────────────┘     └─────────────┘
```

### 2.2 工作流状态机

```
UPLOADED → PARSING → CHUNKING → EMBEDDING → INDEXING → COMPLETED
              │           │            │           │
              └───────────┴────────────┴───────────┴──▶ FAILED
```

### 2.3 各阶段详细说明

| 阶段 | 处理内容 | 耗时预估 | 失败处理 |
|------|----------|----------|----------|
| UPLOADED | 接收文件，存储到临时目录 | <1s | 清理临时文件 |
| PARSING | 调用 Parser 提取文本内容 | 1-10s | 记录错误类型(格式不支持/损坏) |
| CHUNKING | 按策略切分文本块 | 1-5s | 回退到简单切分策略 |
| EMBEDDING | 调用 Embedding Model 生成向量 | 5-30s | 分批重试 |
| INDEXING | 批量写入 Qdrant + 更新元数据 | 2-10s | 标记为待索引 |
| COMPLETED | 更新文档状态，发送通知 | <1s | - |

### 2.4 新增数据库模型

**文档处理任务表** (`DocumentProcessingTask`):

```python
class DocumentProcessingTask(Base):
    __tablename__ = "document_processing_tasks"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    celery_task_id = Column(String(255), nullable=True)  # Celery 任务ID
    
    stage = Column(Enum(ProcessingStage), default=ProcessingStage.UPLOADED)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100
    
    stage_results = Column(JSON, default={})  # 各阶段结果
    error_message = Column(Text, nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## 🔌 三、Agent 工作流接入

### 3.1 RAG 作为 Agent Tool

**位置**: `src/skyone_shuge/agents/tools/rag_tool.py`

```python
from skyone_shuge.ml.rag import RAGEngine

class RAGSearchTool(BaseTool):
    """RAG 检索工具 - 供 Agent 调用"""
    
    name = "knowledge_search"
    description = """搜索知识库中的文档内容，返回相关片段和总结。
    
    Args:
        query: 搜索查询语句
        top_k: 返回结果数量(默认5)
        filters: 可选的过滤条件(分类、标签、日期等)
    """
    
    def __init__(self, rag_engine: RAGEngine):
        self.rag_engine = rag_engine
    
    async def run(self, query: str, top_k: int = 5, **filters) -> Dict:
        """执行检索"""
        result = await self.rag_engine.query(
            query=query,
            top_k=top_k,
            filters=filters
        )
        return {
            "answer": result.answer,
            "sources": [s.dict() for s in result.sources],
            "confidence": result.confidence
        }
```

### 3.2 Agent 集成示例

```python
from skyone_shuge.agents.registry import AgentRegistry

# 注册 RAG 工具
registry = AgentRegistry()
registry.register_tool(RAGSearchTool(rag_engine))

# Agent 使用示例
agent = registry.create_agent("document_assistant")
response = await agent.run(
    "帮我找一下关于机器学习的第一性原理资料"
)
# Agent 会自动调用 knowledge_search 工具
```

### 3.3 工具调用流程

```
用户提问
    │
    ▼
Agent 理解意图
    │
    ├──▶ 需要检索知识库 ──▶ 调用 knowledge_search 工具
    │                         │
    │                         ▼
    │                      RAG Engine 执行检索
    │                         │
    │                         ▼
    │                      返回检索结果给 Agent
    │                         │
    ▼                         │
Agent 整合回答 ◀───────────────┘
    │
    ▼
返回给用户
```

---

## 🌐 四、前后端联调方案

### 4.1 API 接口规范

#### 文档上传接口

```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data

{
  "file": <binary>,
  "category_id": "optional",
  "tags": ["tag1", "tag2"],
  "metadata": {}
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "document_id": "doc_xxx",
    "filename": "document.pdf",
    "status": "processing",
    "task_id": "task_xxx",
    "message": "文档上传成功，正在处理中"
  }
}
```

#### WebSocket 连接

```javascript
// 连接 WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/tasks/{task_id}');

// 接收进度推送
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`进度: ${data.progress}%`);
  console.log(`阶段: ${data.stage}`);
};
```

**推送消息格式**:
```json
{
  "type": "task_progress",
  "task_id": "task_xxx",
  "document_id": "doc_xxx",
  "stage": "embedding",
  "progress": 65,
  "status": "running",
  "message": "正在生成向量嵌入...",
  "timestamp": "2026-03-17T10:30:00Z"
}
```

### 4.2 错误处理规范

| 错误码 | 场景 | 前端处理 |
|--------|------|----------|
| 400 | 参数错误/文件格式不支持 | 提示用户检查文件 |
| 413 | 文件过大 | 提示文件大小限制 |
| 422 | 文档解析失败 | 显示解析错误详情 |
| 429 | 任务队列满 | 提示稍后再试 |
| 500 | 服务器内部错误 | 显示友好错误页 |

**错误响应格式**:
```json
{
  "success": false,
  "error": {
    "code": "DOCUMENT_PARSE_ERROR",
    "message": "无法解析 PDF 文件，可能已损坏",
    "details": {
      "file": "document.pdf",
      "stage": "parsing"
    }
  }
}
```

### 4.3 前端状态管理

**推荐实现** (Zustand Store):

```typescript
interface DocumentUploadState {
  // 上传队列
  uploadQueue: UploadTask[];
  // 正在处理的任务
  processingTasks: Map<string, ProcessingTask>;
  
  // Actions
  addToQueue: (file: File) => void;
  removeFromQueue: (taskId: string) => void;
  updateProgress: (taskId: string, progress: number) => void;
  connectWebSocket: (taskId: string) => void;
}
```

---

## 📦 五、部署与启动

### 5.1 依赖安装

```bash
# 安装 Celery + Redis 依赖
pip install celery[redis] redis flower

# 启动 Redis
redis-server

# 启动 Celery Worker
celery -A skyone_shuge.core.celery_app worker --loglevel=info --concurrency=4

# 启动 Celery Beat (定时任务，可选)
celery -A skyone_shuge.core.celery_app beat --loglevel=info

# 启动 Flower 监控 (可选)
celery -A skyone_shuge.core.celery_app flower --port=5555
```

### 5.2 项目结构更新

```
skyone-shuge/
├── src/skyone_shuge/
│   ├── agents/
│   │   └── tools/
│   │       └── rag_tool.py       # RAG Agent 工具
│   ├── api/
│   │   └── routers/
│   │       └── websocket.py      # WebSocket 路由
│   ├── core/
│   │   ├── celery_app.py         # Celery 应用配置
│   │   └── websocket.py          # WebSocket 管理器
│   ├── tasks/                     # Celery 任务模块
│   │   ├── __init__.py
│   │   ├── document_tasks.py     # 文档处理任务
│   │   ├── embedding_tasks.py    # Embedding 任务
│   │   ├── index_tasks.py        # 索引任务
│   │   └── notification_tasks.py # 通知任务
│   └── models/
│       └── processing_task.py    # 处理任务数据模型
├── celery_worker.py              # Worker 启动入口
└── requirements.txt              # 更新依赖
```

---

## ✅ 六、v3.0.7 任务清单

### 后端开发
- [ ] 创建 `core/celery_app.py` Celery 配置
- [ ] 创建 `tasks/` 模块及任务实现
- [ ] 创建 `models/processing_task.py` 数据模型
- [ ] 更新 `routers/documents.py` 支持异步上传
- [ ] 创建 `routers/websocket.py` WebSocket 路由
- [ ] 创建 `agents/tools/rag_tool.py` Agent 工具
- [ ] 更新 `core/config.py` 添加 Celery 配置
- [ ] 创建 `celery_worker.py` 启动脚本
- [ ] 更新数据库迁移脚本

### 接口与文档
- [ ] 更新 `ITERATION_LOG.md` 至 v3.0.7
- [ ] 创建 API 联调文档
- [ ] 更新 `requirements.txt` 依赖

### 测试验证
- [ ] Celery Worker 启动测试
- [ ] 文档上传端到端流程测试
- [ ] WebSocket 进度推送测试
- [ ] Agent RAG 工具调用测试

---

**文档结束**  
*下一版本：v3.0.8 (前端界面实现与完整联调)*
