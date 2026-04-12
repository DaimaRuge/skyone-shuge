# 天一阁 PRD v3.0.20

**版本**: v3.0.20
**日期**: 2026-04-12
**阶段**: 多模态 RAG + 企业级集成 + AI 模型微调

---

## 📋 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0.20 | 2026-04-12 | 多模态 RAG + 企业集成 + AI 模型微调与服务化 |
| v3.0.19 | 2026-04-10 | 安全加固架构 + 高可用性架构 + 灾难恢复增强 |
| v3.0.18 | 2026-04-09 | 生产环境部署配置 + 监控告警规则 + 性能压测优化 + 用户手册 |
| v3.0.17 | 2026-04-08 | 监控/限流/缓存 API 实现 + 前后端联调 + 端到端测试 |
| v3.0.16 | 2026-04-05 | 实现代码开发 + 前端 UI 组件开发 + 单元测试与集成测试 |

---

## 📅 本次迭代目标

### 核心交付物
- [ ] **多模态 RAG 架构**: 图像/表格/图表/LaTeX 理解与检索、跨模态关联查询
- [ ] **企业级集成架构**: SSO/LDAP、Notion/Salesforce/Confluence 同步、企业通讯集成
- [ ] **AI 模型微调与服务化**: 领域自适应微调、模型服务化、AB 测试框架
- [ ] **高级检索增强**: 混合检索优化、上下文窗口扩展、检索结果重排序

---

## 🎯 一、多模态 RAG 架构

### 1.1 多模态文档理解

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            多模态 RAG 架构                                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           文档输入层                                          │   │
│  │                                                                              │   │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │   │
│  │   │  PDF    │  │  Word  │  │  PPT    │  │  图片   │  │  扫描件  │           │   │
│  │   │ .xlsx  │  │ .md    │  │ .html   │  │ .ePub   │  │  LaTeX  │           │   │
│  │   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘           │   │
│  │        │            │            │            │            │                  │   │
│  │        └────────────┴────────────┴─────┬──────┴────────────┘                  │   │
│  │                                          │                                    │   │
│  │                                          ▼                                    │   │
│  │                              ┌────────────────────┐                          │   │
│  │                              │   智能文档解析器    │                          │   │
│  │                              │  DocumentParser    │                          │   │
│  │                              └─────────┬──────────┘                          │   │
│  └─────────────────────────────────────────┼────────────────────────────────────┘   │
│                                            │                                          │
│  ┌─────────────────────────────────────────┼────────────────────────────────────┐   │
│  │                              内容理解层  │                                    │   │
│  │                                          ▼                                    │   │
│  │   ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │   │                    多模态 Embedding 服务                              │   │   │
│  │   │                                                                      │   │   │
│  │   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐               │   │   │
│  │   │  │ 文本     │  │  图像    │  │  表格    │  │  公式    │               │   │   │
│  │   │  │ Segment │  │  Patch   │  │  Cell    │  │  Block   │               │   │   │
│  │   │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘               │   │   │
│  │   │       │             │             │             │                      │   │   │
│  │   │       └─────────────┴──────┬──────┴─────────────┘                      │   │   │
│  │   │                            ▼                                         │   │   │
│  │   │                   ┌─────────────────┐                                │   │   │
│  │   │                   │  统一向量表示    │                                │   │   │
│  │   │                   │ UnifiedVector  │                                │   │   │
│  │   │                   └────────┬────────┘                                │   │   │
│  │   └─────────────────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                            │                                          │
│  ┌─────────────────────────────────────────┼────────────────────────────────────┐   │
│  │                              检索引擎层  │                                    │   │
│  │                                          ▼                                    │   │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │   │
│  │   │  稠密检索    │    │  稀疏检索    │    │  混合检索    │                   │   │
│  │   │  (向量)     │    │  (BM25)     │    │  (RRF Fusion)│                   │   │
│  │   └──────────────┘    └──────────────┘    └──────┬───────┘                   │   │
│  │                                                   │                          │   │
│  │                                                   ▼                          │   │
│  │                                          ┌──────────────┐                     │   │
│  │                                          │  重排序模型   │                     │   │
│  │                                          │  (Cross-    │                     │   │
│  │                                          │   Encoder)  │                     │   │
│  │                                          └──────────────┘                     │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                            │                                          │
│                                            ▼                                          │
│                              ┌─────────────────────────┐                           │
│                              │     LLM 生成层          │                           │
│                              │  (上下文组装 + 生成)     │                           │
│                              └─────────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 图像理解与 Caption 生成

```python
# ml/multimodal/image_understanding.py

from dataclasses import dataclass
from typing import Optional
import base64

@dataclass
class ImageChunk:
    """图像块"""
    chunk_id: str
    image_data: bytes  # 原始图像数据
    caption: str  # AI 生成的描述
    OCR_text: str  # OCR 提取的文字
    layout_info: dict  # 布局信息 (标题/正文/图表区域)
    embedding: list[float]
    page_num: int
    source_document_id: str


class MultimodalImageProcessor:
    """
    多模态图像理解处理器
    
    支持:
    - 图像 caption 生成 (GPT-4V / LLaVA)
    - OCR 文字提取 (PaddleOCR / EasyOCR)
    - 布局分析 (LayoutLM / YOLO)
    - 图表理解 (ChartOCR / Matplotlib parsing)
    """

    def __init__(self, config: MultimodalConfig):
        self.vision_model = self._init_vision_model(config.vision_provider)
        self.ocr_engine = self._init_ocr_engine(config.ocr_engine)
        self.layout_model = self._init_layout_model(config.layout_model)
        self.embedding_model = self._init_embedding_model(config.embedding_model)

    async def process_image(
        self,
        image_data: bytes,
        context: Optional[dict] = None
    ) -> ImageChunk:
        """处理单张图像，提取多模态信息"""
        
        # Step 1: OCR 文字提取
        ocr_result = await self.ocr_engine.extract_text(image_data)
        
        # Step 2: 布局分析
        layout_result = await self.layout_model.analyze(image_data)
        
        # Step 3: 图像 Caption 生成
        caption = await self._generate_caption(image_data, context)
        
        # Step 4: 图表特殊处理 (如果是图表类图像)
        if self._is_chart_image(layout_result):
            chart_data = await self._extract_chart_data(image_data, ocr_result)
        else:
            chart_data = None
        
        # Step 5: 生成统一 embedding
        combined_text = self._combine_texts(
            ocr_result.text,
            caption,
            chart_data
        )
        embedding = await self.embedding_model.embed(combined_text)
        
        return ImageChunk(
            chunk_id=self._generate_id(),
            image_data=image_data,
            caption=caption,
            OCR_text=ocr_result.text,
            layout_info=layout_result.to_dict(),
            embedding=embedding,
            page_num=context.get('page_num', 0) if context else 0,
            source_document_id=context.get('doc_id', '') if context else ''
        )

    async def _generate_caption(
        self,
        image_data: bytes,
        context: Optional[dict]
    ) -> str:
        """使用视觉语言模型生成图像描述"""
        prompt = self._build_caption_prompt(context)
        
        response = await self.vision_model.generate(
            image=image_data,
            prompt=prompt
        )
        return response.caption

    def _build_caption_prompt(self, context: Optional[dict]) -> str:
        """构建图像描述提示词"""
        base_prompt = (
            "描述这张图像的详细内容，包括:\n"
            "1. 图像中的主要元素和布局\n"
            "2. 文字内容（如果有）\n"
            "3. 图表/图形的数据趋势（如果是图表）\n"
            "4. 图像在文档中的作用和上下文\n"
        )
        
        if context:
            doc_title = context.get('title', '')
            section_title = context.get('section', '')
            doc_summary = context.get('summary', '')
            
            return f"""
文档标题: {doc_title}
章节标题: {section_title}
文档摘要: {doc_summary}

{base_prompt}
"""
        return base_prompt
```

### 1.3 表格理解与结构化

```python
# ml/multimodal/table_understanding.py

from dataclasses import dataclass
from typing import Literal

@dataclass
class TableChunk:
    """表格块"""
    chunk_id: str
    table_html: str  # HTML 格式表格
    table_md: str  # Markdown 格式
    table_json: list[dict]  # 结构化 JSON
    summary: str  # 表格摘要
    headers: list[str]  # 表头
    embedding: list[float]
    source_document_id: str


class TableParser:
    """
    表格理解与结构化解析
    
    支持:
    - HTML 表格解析
    - 文本表格解析 (ASCII 表格、CSV 格式)
    - 图片表格识别 (表格检测 + 结构识别)
    - 表格摘要生成
    """

    def __init__(self, config: TableParserConfig):
        self.detection_model = self._init_table_detector()
        self.structure_recognizer = self._init_structure_recognizer()
        self.llm = self._init_llm(config.llm_provider)

    async def parse_table_from_pdf(
        self,
        page_image: bytes,
        bbox: tuple[int, int, int, int]
    ) -> TableChunk:
        """从 PDF 页面图像中提取表格"""
        
        # Step 1: 表格检测
        detected_cells = await self.detection_model.detect(
            page_image,
            bbox
        )
        
        # Step 2: 结构识别 (行列合并、边框分析)
        table_structure = await self.structure_recognizer.recognize(
            detected_cells
        )
        
        # Step 3: 转换为结构化格式
        table_json = self._to_json(table_structure)
        table_html = self._to_html(table_structure)
        table_md = self._to_markdown(table_structure)
        
        # Step 4: 生成表格摘要
        summary = await self._generate_summary(table_json)
        
        # Step 5: 生成 embedding
        combined_text = f"{summary}\n{table_md}"
        embedding = await self.embedding_model.embed(combined_text)
        
        return TableChunk(...)

    async def _generate_summary(self, table_json: list[dict]) -> str:
        """使用 LLM 生成表格摘要"""
        prompt = f"""
这是一个表格的数据:
{json.dumps(table_json[:10], ensure_ascii=False, indent=2)}
(共 {len(table_json)} 行)

请生成一段简短的摘要，描述:
1. 表格的主题和目的
2. 主要的数据维度/指标
3. 关键数据特征或趋势

请用中文回答，摘要不超过 100 字。
"""
        
        response = await self.llm.generate(prompt)
        return response.text
```

### 1.4 跨模态检索流程

```python
# ml/multimodal/cross_modal_retrieval.py

class CrossModalRetriever:
    """
    跨模态检索器
    
    支持:
    - 文本 → 图像检索
    - 图像 → 文本检索
    - 混合查询 (文本 + 图像同时检索)
    """

    def __init__(
        self,
        vector_store: VectorStore,
        text_store: VectorStore,
        image_store: VectorStore,
        fusion_method: Literal["RRF", "COLABER", "DIRECT_SCORE"] = "RRF"
    ):
        self.vector_store = vector_store
        self.text_store = text_store
        self.image_store = image_store
        self.fusion_method = fusion_method

    async def retrieve(
        self,
        query: Query,
        top_k: int = 10
    ) -> list[RetrievedChunk]:
        """
        跨模态检索主流程
        
        Args:
            query: 查询对象，支持 text / image / text+image
            top_k: 返回结果数量
        """
        
        sub_queries = await self._decompose_query(query)
        
        # 并行执行多路检索
        retrieval_tasks = []
        for sq in sub_queries:
            if sq.type == "text":
                retrieval_tasks.append(
                    self._retrieve_text(sq, top_k * 2)
                )
            elif sq.type == "image":
                retrieval_tasks.append(
                    self._retrieve_image(sq, top_k * 2)
                )
            elif sq.type == "table":
                retrieval_tasks.append(
                    self._retrieve_table(sq, top_k * 2)
                )
        
        results = await asyncio.gather(*retrieval_tasks)
        
        # 混合融合
        fused_results = self._fuse_results(results)
        
        # 重排序
        reranked = await self._rerank(query, fused_results, top_k)
        
        return reranked

    async def _rerank(
        self,
        query: Query,
        candidates: list[RetrievedChunk],
        top_k: int
    ) -> list[RetrievedChunk]:
        """使用 Cross-Encoder 重排序"""
        
        pairs = [(query.text, doc.content) for doc in candidates]
        
        scores = await self.cross_encoder.score(pairs)
        
        scored_docs = zip(candidates, scores)
        sorted_docs = sorted(scored_docs, key=lambda x: x[1], reverse=True)
        
        return [doc for doc, _ in sorted_docs[:top_k]]
```

---

## 🎯 二、企业级集成架构

### 2.1 SSO/LDAP 身份认证集成

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           企业身份认证集成架构                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│   │   企业用户   │    │   LDAP/AD   │    │    SAML       │    │    OIDC      │      │
│   │   访问       │───▶│   目录服务   │───▶│   2.0         │───▶│   Provider   │      │
│   └──────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘      │
│                                                                        │              │
│                                                                        ▼              │
│                                                             ┌──────────────────┐       │
│                                                             │   统一身份网关    │       │
│                                                             │  Identity Gateway │       │
│                                                             │   (Keycloak/     │       │
│                                                             │    Authelia)     │       │
│                                                             └────────┬─────────┘       │
│                                                                       │                 │
│                                        ┌──────────────────────────────┼──────────────┐  │
│                                        │                              │              │  │
│                                        ▼                              ▼              ▼  │
│                               ┌──────────────┐           ┌──────────────┐  ┌────────┐ │
│                               │   SAML IDP   │           │   OIDC IDP   │  │ LDAP  │ │
│                               └──────────────┘           └──────────────┘  └────────┘ │
│                                                                                      │
│   ┌──────────────────────────────────────────────────────────────────────────────┐   │
│   │                              天一阁应用层                                      │   │
│   │                                                                              │   │
│   │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │   │
│   │   │  用户    │  │  权限    │  │  审计    │  │  组织    │  │  同步    │   │   │
│   │   │  管理    │  │  管理    │  │  日志    │  │  架构    │  │  服务    │   │   │
│   │   └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │   │
│   └──────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Notion 双向同步

```python
# integrations/notion/sync_service.py

from dataclasses import dataclass
from typing import Literal
from datetime import datetime

@dataclass
class NotionSyncConfig:
    """Notion 同步配置"""
    api_key: str
    database_id: str
    sync_direction: Literal["uni", "bi"]  # 单向/双向
    conflict_resolution: Literal["notion_wins", "local_wins", "newer_wins"]
    sync_interval_minutes: int = 15


class NotionSyncService:
    """
    Notion 双向同步服务
    
    功能:
    - Notion Database → 天一阁: 定期同步文档
    - 天一阁 → Notion Database: 推送天一阁知识到 Notion
    - 变更检测与冲突解决
    - 实时 Webhook 接收 Notion 更新
    """

    def __init__(self, config: NotionSyncConfig):
        self.notion_client = NotionClient(config.api_key)
        self.local_store = DocumentStore()
        self.change_detector = ChangeDetector()
        self.conflict_resolver = ConflictResolver(config.conflict_resolution)

    async def sync_from_notion(self) -> SyncResult:
        """从 Notion 同步文档到天一阁"""
        
        # Step 1: 获取 Notion Database 中最近更新的页面
        recent_pages = await self.notion_client.get_recently_updated_pages(
            database_id=self.config.database_id,
            since=self._get_last_sync_time()
        )
        
        # Step 2: 逐个处理页面
        synced = []
        conflicts = []
        
        for page in recent_pages:
            local_doc = await self.local_store.get_by_notion_id(page.id)
            
            if local_doc is None:
                # 新文档，直接导入
                new_doc = await self._import_notion_page(page)
                await self.local_store.save(new_doc)
                synced.append(new_doc)
                
            else:
                # 已有文档，检测冲突
                if self.change_detector.has_conflict(page, local_doc):
                    conflicts.append({
                        'notion': page,
                        'local': local_doc
                    })
                else:
                    # 无冲突，更新
                    updated = await self._import_notion_page(page)
                    await self.local_store.save(updated)
                    synced.append(updated)
        
        # Step 3: 处理冲突
        resolved = await self._resolve_conflicts(conflicts)
        
        return SyncResult(synced=len(synced), conflicts=len(resolved))

    async def sync_to_notion(self, doc: Document) -> bool:
        """将天一阁文档同步到 Notion"""
        
        # 检查是否已关联 Notion 页面
        if doc.notion_page_id:
            # 更新现有页面
            await self.notion_client.update_page(
                page_id=doc.notion_page_id,
                properties=doc.to_notion_properties(),
                content=doc.to_notion_blocks()
            )
        else:
            # 创建新页面
            new_page = await self.notion_client.create_page(
                database_id=self.config.database_id,
                properties=doc.to_notion_properties(),
                content=doc.to_notion_blocks()
            )
            # 记录关联
            doc.notion_page_id = new_page.id
            await self.local_store.save(doc)
        
        return True
```

### 2.3 企业通讯集成

```python
# integrations/enterprise/teams_integration.py

class TeamsIntegrationService:
    """
    Microsoft Teams 集成服务
    
    功能:
    - 频道消息推送 (文档更新通知)
    - 主动搜索 (在 Teams 中搜索天一阁知识)
    - 消息卡片渲染 (富文本卡片展示)
    - 通知订阅 (文档变更实时通知)
    """

    def __init__(self, config: TeamsConfig):
        self.graph_client = GraphClient(config)
        self.notification_service = NotificationService()

    async def post_document_update(
        self,
        channel_id: str,
        document: Document,
        update_type: str
    ):
        """向 Teams 频道推送文档更新消息"""
        
        adaptive_card = self._build_update_card(document, update_type)
        
        await self.graph_client.send_message(
            channel_id=channel_id,
            content_type="application/vnd.microsoft.card.adaptive",
            content=adaptive_card
        )

    def _build_update_card(
        self,
        document: Document,
        update_type: str
    ) -> dict:
        """构建 Adaptive Card 消息"""
        
        return {
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": f"📄 文档更新: {document.title}",
                    "weight": "Bolder",
                    "size": "Medium"
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {"title": "更新类型", "value": update_type},
                        {"title": "更新时间", "value": document.updated_at},
                        {"title": "更新人", "value": document.last_editor}
                    ]
                },
                {
                    "type": "TextBlock",
                    "text": document.summary[:200] + "..." if len(document.summary) > 200 else document.summary
                }
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "查看文档",
                    "url": f"{APP_URL}/documents/{document.id}"
                },
                {
                    "type": "Action.OpenUrl",
                    "title": "查看变更",
                    "url": f"{APP_URL}/documents/{document.id}/diff"
                }
            ]
        }
```

---

## 🎯 三、AI 模型微调与服务化

### 3.1 领域自适应微调流程

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          AI 模型微调与服务化架构                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                              数据准备层                                        │   │
│  │                                                                              │   │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │   │
│  │   │ 天一阁知识库  │    │  领域数据    │    │  标注数据    │                  │   │
│  │   │  (用户文档)  │    │  (外部数据)  │    │  (QA 对)    │                  │   │
│  │   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │   │
│  │          │                   │                   │                           │   │
│  │          └───────────────────┴───────┬───────────┘                           │   │
│  │                                       ▼                                       │   │
│  │                            ┌──────────────────┐                               │   │
│  │                            │   数据清洗管道    │                               │   │
│  │                            │  (去噪/去重/格式) │                               │   │
│  │                            └────────┬─────────┘                               │   │
│  └──────────────────────────────────────┼────────────────────────────────────────┘   │
│                                          │                                            │
│  ┌──────────────────────────────────────┼────────────────────────────────────────┐   │
│  │                              训练管理层  │                                      │   │
│  │                                          ▼                                        │   │
│  │   ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │   │                    分布式训练 (Ray Train / DeepSpeed)                │    │   │
│  │   │                                                                      │    │   │
│  │   │   Node 1 (GPU x4)   Node 2 (GPU x4)   Node 3 (GPU x4)                │    │   │
│  │   │        │                │                │                          │    │   │
│  │   │        └────────────────┼────────────────┘                          │    │   │
│  │   │                         ▼                                           │    │   │
│  │   │              ┌─────────────────────┐                                 │    │   │
│  │   │              │   Parameter Server │                                 │    │   │
│  │   │              │   / AllReduce       │                                 │    │   │
│  │   │              └──────────┬──────────┘                                 │    │   │
│  │   └─────────────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                            │
│                                          ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                              模型服务层                                        │   │
│  │                                                                              │   │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │   │
│  │   │  vLLM        │    │  TensorRT-LLM│    │   SGLang     │                  │   │
│  │   │  (通用推理)  │    │  (优化推理)  │    │  (高并发)    │                  │   │
│  │   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │   │
│  │          │                   │                   │                           │   │
│  │          └───────────────────┴───────┬───────────┘                           │   │
│  │                                      ▼                                        │   │
│  │                           ┌─────────────────────┐                             │   │
│  │                           │   模型路由 (Router)  │                             │   │
│  │                           │   (AB Test / Load   │                             │   │
│  │                           │    Balancing)       │                             │   │
│  │                           └──────────┬──────────┘                             │   │
│  └──────────────────────────────────────┼────────────────────────────────────────┘   │
│                                          │                                            │
│                                          ▼                                            │
│                               ┌─────────────────────┐                               │
│                               │    模型注册中心      │                               │
│                               │   (Model Registry)  │                               │
│                               │  版本管理/A/B测试   │                               │
│                               └─────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 模型微调训练器

```python
# ml/fine_tuning/trainer.py

from dataclasses import dataclass
import ray

@dataclass
class FineTuningConfig:
    """微调配置"""
    base_model: str  # e.g., "Qwen2-7B-Instruct"
    dataset_path: str
    num_gpus: int = 4
    num_epochs: int = 3
    learning_rate: float = 2e-5
    batch_size: int = 8
    max_seq_length: int = 4096
    lora_rank: int = 16
    lora_alpha: int = 32
    target_modules: list[str] = None  # 需要微调的模块


class DomainFineTuner:
    """
    领域自适应微调器
    
    使用 LoRA/QLoRA 进行参数高效微调
    
    支持:
    - 增量预训练 (IPT)
    - 指令微调 (SFT)
    - 人类反馈强化学习 (RLHF)
    - DPO (Direct Preference Optimization)
    """

    def __init__(self, config: FineTuningConfig):
        self.config = config
        self.ray_cluster = self._init_ray_cluster()
        self.trainer = self._init_trainer()

    async def fine_tune(
        self,
        training_type: Literal["ipt", "sft", "dpo"] = "sft"
    ) -> ModelCheckpoint:
        """执行模型微调"""
        
        # 数据加载与预处理
        dataset = await self._load_and_prepare_dataset(training_type)
        
        # 配置训练参数
        training_args = self._build_training_args(training_type)
        
        # 启动分布式训练
        if training_type == "dpo":
            result = await self._train_dpo(dataset, training_args)
        else:
            result = await self._train_sft(dataset, training_args)
        
        # 保存检查点
        checkpoint = await self._save_checkpoint(result)
        
        return checkpoint

    async def _train_dpo(
        self,
        dataset,
        training_args
    ) -> TrainingResult:
        """DPO 偏好优化训练"""
        
        from trl import DPOTrainer
        
        dpo_trainer = DPOTrainer(
            model=self.config.base_model,
            ref_model=self.config.base_model,  # 原始模型作为参考
            args=training_args,
            beta=0.1,  # KL 正则化系数
            dataset_text_field="text",
            dataset_num_proc=8,
        )
        
        result = dpo_trainer.train()
        return result
```

### 3.3 模型 AB 测试框架

```python
# ml/model_routing/ab_test.py

from dataclasses import dataclass
from typing import Callable
import hashlib

@dataclass
class ABTestConfig:
    """A/B 测试配置"""
    test_id: str
    model_a: str  # 对照组模型
    model_b: str  # 实验组模型
    traffic_split: float = 0.5  # 实验组流量比例
    metrics: list[str]  # 评估指标
    min_sample_size: int = 1000  # 最小样本量
    significance_level: float = 0.05  # 显著性水平


class ModelABRouter:
    """
    模型 A/B 测试路由器
    
    功能:
    - 用户流量分割 (基于 user_id hash)
    - 请求路由到不同模型
    - 效果数据收集
    - 统计显著性检验
    """

    def __init__(
        self,
        config: ABTestConfig,
        model_registry: ModelRegistry,
        metrics_collector: MetricsCollector
    ):
        self.config = config
        self.model_registry = model_registry
        self.metrics = metrics_collector

    async def route_and_generate(
        self,
        user_id: str,
        prompt: str,
        **kwargs
    ) -> GenerationResult:
        """路由请求到对应模型并收集指标"""
        
        # Step 1: 流量分割
        model_name = self._get_model_for_user(user_id)
        
        # Step 2: 执行生成
        start_time = time.time()
        model = self.model_registry.get_model(model_name)
        
        result = await model.generate(prompt, **kwargs)
        
        latency = time.time() - start_time
        
        # Step 3: 收集指标
        await self.metrics.record(
            test_id=self.config.test_id,
            model_name=model_name,
            user_id=user_id,
            prompt=prompt,
            response=result.text,
            latency=latency,
            token_count=result.usage.total_tokens
        )
        
        return result

    def _get_model_for_user(self, user_id: str) -> str:
        """基于用户 ID hash 确定流量分配"""
        hash_value = int(
            hashlib.md5(f"{self.config.test_id}:{user_id}".encode()).hexdigest(),
            16
        )
        bucket = (hash_value % 10000) / 10000.0
        
        if bucket < self.config.traffic_split:
            return self.config.model_b  # 实验组
        else:
            return self.config.model_a  # 对照组

    async def analyze_results(self) -> ABTestReport:
        """分析 A/B 测试结果，进行统计检验"""
        
        # 收集各模型指标
        model_a_metrics = await self.metrics.get_model_metrics(
            self.config.test_id,
            self.config.model_a
        )
        model_b_metrics = await self.metrics.get_model_metrics(
            self.config.test_id,
            self.config.model_b
        )
        
        # 统计检验
        report = ABTestReport(
            test_id=self.config.test_id,
            sample_size_a=len(model_a_metrics),
            sample_size_b=len(model_b_metrics),
            metrics={}
        )
        
        for metric_name in self.config.metrics:
            stat_result = self._statistical_test(
                model_a_metrics[metric_name],
                model_b_metrics[metric_name]
            )
            
            report.metrics[metric_name] = MetricComparison(
                mean_a=np.mean(model_a_metrics[metric_name]),
                mean_b=np.mean(model_b_metrics[metric_name]),
                p_value=stat_result.pvalue,
                significant=stat_result.pvalue < self.config.significance_level,
                recommendation="采用 B" if stat_result.pvalue < self.config.significance_level else "保持 A"
            )
        
        return report
```

---

## 🎯 四、高级检索增强

### 4.1 混合检索与重排序

```python
# ml/retrieval/hybrid_retriever.py

class HybridRetriever:
    """
    混合检索器
    
    结合多种检索方法:
    - 稠密检索 (Dense / 向量检索)
    - 稀疏检索 (Sparse / BM25)
    - 关键词检索 (Boolean)
    - 混合融合 (RRF / COLABER / Convex Combination)
    """

    def __init__(
        self,
        config: HybridRetrievalConfig,
        dense_store: VectorStore,
        sparse_store: SparseVectorStore,
        reranker: CrossEncoder
    ):
        self.config = config
        self.dense_store = dense_store
        self.sparse_store = sparse_store
        self.reranker = reranker

    async def retrieve(
        self,
        query: str,
        top_k: int = 20,
        filters: dict = None
    ) -> list[RetrievedChunk]:
        """执行混合检索"""
        
        # Step 1: 并行执行多路检索
        results = await asyncio.gather(
            self.dense_store.search(
                query_vector=await self._embed(query),
                top_k=top_k,
                filters=filters
            ),
            self.sparse_store.search(
                query_text=query,
                top_k=top_k,
                filters=filters
            )
        )
        
        dense_results, sparse_results = results
        
        # Step 2: 分数归一化
        normalized_dense = self._normalize_scores(dense_results)
        normalized_sparse = self._normalize_scores(sparse_results)
        
        # Step 3: 分数融合
        if self.config.fusion_method == "RRF":
            fused = self._rrf_fusion(normalized_dense, normalized_sparse)
        elif self.config.fusion_method == "COLABER":
            fused = self._colaber_fusion(normalized_dense, normalized_sparse)
        else:
            fused = self._convex_fusion(
                normalized_dense,
                normalized_sparse,
                alpha=self.config.fusion_alpha
            )
        
        # Step 4: 重排序
        reranked = await self.reranker.rerank(
            query=query,
            candidates=fused[:top_k * 3]  # 取更多候选进行重排序
        )
        
        return reranked[:top_k]

    def _rrf_fusion(
        self,
        dense: list[tuple[str, float]],
        sparse: list[tuple[str, float]]
    ) -> list[tuple[str, float]]:
        """Reciprocal Rank Fusion"""
        
        k = 60  # RRF 超参数
        
        scores = defaultdict(float)
        
        for rank, (doc_id, score) in enumerate(dense):
            scores[doc_id] += 1.0 / (k + rank + 1)
        
        for rank, (doc_id, score) in enumerate(sparse):
            scores[doc_id] += 1.0 / (k + rank + 1)
        
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores
```

---

## 📊 PRD Checkpoint v3.0.20

### 完成标准
- [ ] 多模态 RAG 完整流程设计完成
- [ ] 企业级集成方案设计完成
- [ ] AI 模型微调与服务化方案设计完成
- [ ] 高级检索增强方案设计完成
- [ ] PRD v3.0.20 文档完成
- [ ] 架构 v3.0.20 文档完成
- [ ] ITERATION_LOG.md 更新至 v3.0.20
- [ ] ITERATION_PLAN.md 更新至 v3.0.20
