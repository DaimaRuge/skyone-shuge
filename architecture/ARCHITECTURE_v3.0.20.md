# 天一阁架构文档 v3.0.20

**版本**: v3.0.20
**日期**: 2026-04-12
**主题**: 多模态 RAG + 企业级集成 + AI 模型微调与服务化

---

## 📋 文档历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0.20 | 2026-04-12 | 多模态 RAG + 企业集成 + AI 模型微调与服务化 |
| v3.0.19 | 2026-04-10 | 安全加固架构 + 高可用性架构 + 灾难恢复增强 |
| v3.0.18 | 2026-04-09 | 生产环境部署架构 + 监控告警架构 + 性能压测架构 + 文档站点架构 |
| v3.0.17 | 2026-04-08 | 监控 API 架构 + 限流 API 架构 + 缓存 API 架构 + E2E 测试架构 |
| v3.0.16 | 2026-04-05 | 监控 SDK 架构 + 限流中间件架构 + 多级缓存架构 + ES 客户端架构 |

---

## 🎯 一、多模态 RAG 技术架构

### 1.1 整体技术架构

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            多模态 RAG 技术架构                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                              文档输入层 (Ingestion)                             │   │
│  │                                                                              │   │
│  │   PDF ──┐                                                                      │   │
│  │   DOCX ─┼──▶ Document Parser ──▶ Layout Analyzer ──▶ Element Splitter         │   │
│  │   PPT ──┤     (pdfplumber/     (YOLO/LayoutLM)  (语义分块)                    │   │
│  │   IMG ──┤      python-docx)                                                            │   │
│  │   HTML ─┤                                                                       │   │
│  │   EPUB ─┘                                                                       │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                           │
│  ┌───────────────────────────────────────▼───────────────────────────────────────┐   │
│  │                              多模态理解层 (Understanding)                      │   │
│  │                                                                              │   │
│  │   Text ──────────────────▶ Text Embedding ────▶ Text Vector (384d)            │   │
│  │                                                                              │   │
│  │   Image ──▶ Vision Encoder ──▶ Vision Embedding ──▶ Image Vector (384d)      │   │
│  │             (CLIP/SigLIP)         (Projector)                                  │   │
│  │                                                                              │   │
│  │   Table ──▶ Table Parser ──▶ Structure Analysis ──▶ Table Vector (384d)       │   │
│  │              (TableFormer)    (行列结构/合并单元格)                             │   │
│  │                                                                              │   │
│  │   Chart ─▶ Chart Parser ──▶ Data Extraction ──▶ Chart Vector (384d)          │   │
│  │             (ChartOCR)       (趋势/对比/分布)                                  │   │
│  │                                                                              │   │
│  │   Formula ─▶ LaTeX Parser ──▶ Math Understanding ──▶ Formula Vector           │   │
│  │               (Instruk-Math)  (符号/公式语义)                                  │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                           │
│  ┌───────────────────────────────────────▼───────────────────────────────────────┐   │
│  │                              向量存储层 (Storage)                               │   │
│  │                                                                              │   │
│  │   ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │   │                        Qdrant Vector Database                       │   │   │
│  │   │                                                                      │   │   │
│  │   │   collections:                                                       │   │   │
│  │   │   ├── text_chunks (384d, hnsw, cosine)                              │   │   │
│  │   │   ├── image_chunks (384d, hnsw, cosine)                             │   │   │
│  │   │   ├── table_chunks (384d, hnsw, cosine)                            │   │   │
│  │   │   └── cross_modal (768d, hnsw, multi-vector)                       │   │   │
│  │   │                                                                      │   │   │
│  │   │   payload indexes:                                                   │   │   │
│  │   │   ├── document_id (keyword)                                         │   │   │
│  │   │   ├── page_num (integer)                                            │   │   │
│  │   │   ├── element_type (text/image/table/chart)                         │   │   │
│  │   │   └── created_at (datetime)                                         │   │   │
│  │   └─────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                              │   │
│  │   ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │   │                        PostgreSQL (metadata store)                  │   │   │
│  │   │                                                                      │   │   │
│  │   │   tables:                                                           │   │   │
│  │   │   ├── documents (id, title, source, created_at, ...)               │   │   │
│  │   │   ├── elements (id, doc_id, type, content, bbox, ...)              │   │   │
│  │   │   ├── images (id, element_id, base64, caption, OCR, ...)           │   │   │
│  │   │   └── tables (id, element_id, html, json, summary, ...)             │   │   │
│  │   └─────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                           │
│  ┌───────────────────────────────────────▼───────────────────────────────────────┐   │
│  │                              检索引擎层 (Retrieval)                            │   │
│  │                                                                              │   │
│  │   Query ──▶ Query Decomposer ──▶ Sub-queries                                │   │
│  │                                              │                                 │   │
│  │   Sub-Queries ──▶ Parallel Retrieval ──▶ Results                             │   │
│  │                        │                                                     │   │
│  │                        ├── Dense Retrieval (向量检索) ──▶ Top-50             │   │
│  │                        ├── Sparse Retrieval (BM25) ──▶ Top-50              │   │
│  │                        └── Keyword Retrieval ──▶ Top-50                   │   │
│  │                                                                              │   │
│  │   Results ──▶ Score Fusion (RRF) ──▶ Candidates                              │   │
│  │                                                                              │   │
│  │   Candidates ──▶ Cross-Encoder Reranker ──▶ Top-K                           │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                           │
│  ┌───────────────────────────────────────▼───────────────────────────────────────┐   │
│  │                              生成增强层 (Augmentation)                         │   │
│  │                                                                              │   │
│  │   Top-K Chunks ──▶ Context Assembler ──▶ Prompt Template                     │   │
│  │                                          │                                    │   │
│  │   Prompt + History ──▶ LLM (GPT-4o / Qwen-VL) ──▶ Response                    │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 图像多模态处理流程

```yaml
# 配置: multimodal/pipeline.yaml

multimodal_pipeline:
  # ─── 图像处理配置 ───────────────────────────────
  image_processing:
    enabled: true
    
    # 视觉编码器配置
    vision_encoder:
      provider: "openai"  # openai / anthropic / local
      model: "gpt-4o"      # gpt-4o / claude-3.5-sonnet / Qwen-VL-Max
      batch_size: 10
      
    # OCR 引擎配置
    ocr_engine:
      provider: "paddleocr"  # paddleocr / easyocr / azure_ocr
      languages: ["chinese", "english"]
      use_angle_cls: true
      det_algorithm: "DB"
      rec_algorithm: "CRNN"
      
    # 布局分析配置
    layout_analysis:
      provider: "layoutlm"  # layoutlm / yolo / paddleocr
      model: "microsoft/layoutlm-base-uncased"
      detect_elements:
        - title
        - text
        - table
        - figure
        - caption
        - footer
        - header
        
    # 图像切片策略
    image_chunking:
      method: "grid"  # grid / semantic / sliding_window
      grid_size: [512, 512]  # 像素为单位
      overlap: 64  # 重叠像素
      min_image_size: 256  # 最小图像尺寸
      
  # ─── 表格处理配置 ───────────────────────────────
  table_processing:
    enabled: true
    
    # 表格检测
    table_detection:
      provider: "table_transformer"  # table_transformer / paddleocr
      model: "microsoft/table-transformer-detection"
      confidence_threshold: 0.8
      
    # 表格结构识别
    table_structure:
      provider: "table_structure_recognizer"
      model: "microsoft/table-transformer-structure-recognition"
      recognize_merged_cells: true
      recognize_rotated_tables: true
      
    # 表格转结构化
    table_to_json:
      include_headers: true
      merge_merged_cells: false  # false=保留原始结构，true=合并内容
      numeric_precision: 4
        
  # ─── 图表处理配置 ───────────────────────────────
  chart_processing:
    enabled: true
    
    chart_types:
      - bar_chart
      - line_chart
      - pie_chart
      - scatter_plot
      - histogram
      - heatmap
      
    # 图表数据提取
    data_extraction:
      provider: "chartocr"  # chartocr / matplotlib_parse
      extract_series: true
      extract_legend: true
      extract_axis_labels: true
      
    # 图表描述生成
    caption_generation:
      provider: "vision_llm"
      prompt_template: |
        描述这个图表的以下方面:
        1. 图表类型和整体趋势
        2. 主要数据点和极值
        3. X轴和Y轴的含义
        4. 关键洞察和发现
        
  # ─── 公式处理配置 ───────────────────────────────
  formula_processing:
    enabled: true
    
    latex_parser:
      provider: "instruk-math"  # instruk-math / mathpix
      ocr_enabled: true
      
    formula_understanding:
      # 公式语义理解，用于检索
      embed_formula_semantics: true
      
  # ─── Embedding 配置 ─────────────────────────────
  embedding:
    # 多模态统一 embedding 模型
    model: "google/siglip-so400m-patch14-384"  # SigLIP for vision
    text_model: "BAAI/bge-m3"  # BGE-M3 for text (支持多语言)
    
    # Embedding 维度
    embedding_dim: 384
    
    # 跨模态映射
    cross_modal_projection:
      method: "linear"  # linear / mlp / attention
      output_dim: 384
```

### 1.3 核心代码实现

```python
# ml/multimodal/pipeline.py

from dataclasses import dataclass, field
from typing import AsyncGenerator
import asyncio

@dataclass
class MultimodalDocument:
    """多模态文档对象"""
    doc_id: str
    title: str
    source_type: str  # pdf, docx, html, ...
    elements: list[DocumentElement] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class DocumentElement:
    """文档元素基类"""
    element_id: str
    element_type: str  # text, image, table, chart, formula
    content: str  # 原始内容/OCR文本/LaTeX
    bbox: tuple[int, int, int, int]  # 边界框 (x1, y1, x2, y2)
    page_num: int
    embedding: list[float] = field(default_factory=list)


class MultimodalIndexingPipeline:
    """
    多模态文档索引管道
    
    处理流程:
    1. 文档解析 (PDF/DOCX/HTML)
    2. 布局分析 (检测标题/正文/表格/图表)
    3. 元素分块 (语义分块)
    4. 多模态理解 (OCR/Caption/Table解析)
    5. 向量嵌入 (文本+图像+表格)
    6. 索引存储 (Qdrant + PostgreSQL)
    """

    def __init__(self, config: MultimodalPipelineConfig):
        self.config = config
        self.parser = self._init_parser(config.parser)
        self.layout_analyzer = self._init_layout_analyzer(config.layout)
        self.element_splitter = SemanticChunker(config.chunker)
        self.ocr_engine = self._init_ocr(config.ocr)
        self.vision_model = self._init_vision_model(config.vision)
        self.embedding_model = self._init_embedding(config.embedding)
        self.vector_store = QdrantStore(config.qdrant)
        self.metadata_store = PostgresStore(config.postgres)

    async def index_document(
        self,
        file_path: str,
        metadata: dict = None
    ) -> str:
        """索引单个多模态文档"""
        
        # Step 1: 解析文档
        raw_elements = await self.parser.parse(file_path)
        
        # Step 2: 布局分析
        layout_elements = await self.layout_analyzer.analyze(raw_elements)
        
        # Step 3: 元素分块
        chunks = await self.element_splitter.chunk(layout_elements)
        
        # Step 4: 多模态理解与 embedding
        enriched_chunks = await self._process_multimodal(chunks)
        
        # Step 5: 存储
        doc_id = await self.vector_store.upsert_document(
            chunks=enriched_chunks,
            metadata=metadata or {}
        )
        
        # Step 6: 存储 metadata
        await self.metadata_store.save_document_metadata(
            doc_id=doc_id,
            elements=layout_elements,
            metadata=metadata
        )
        
        return doc_id

    async def _process_multimodal(
        self,
        chunks: list[DocumentChunk]
    ) -> list[EnrichedChunk]:
        """多模态理解与 embedding"""
        
        tasks = []
        for chunk in chunks:
            if chunk.type == "text":
                task = self._process_text_chunk(chunk)
            elif chunk.type == "image":
                task = self._process_image_chunk(chunk)
            elif chunk.type == "table":
                task = self._process_table_chunk(chunk)
            elif chunk.type == "chart":
                task = self._process_chart_chunk(chunk)
            else:
                task = self._process_text_chunk(chunk)
            
            tasks.append(task)
        
        return await asyncio.gather(*tasks)

    async def _process_image_chunk(
        self,
        chunk: DocumentChunk
    ) -> EnrichedChunk:
        """处理图像块"""
        
        # 并行执行 OCR 和 Caption
        ocr_task = self.ocr_engine.extract_text(chunk.image_data)
        caption_task = self.vision_model.generate_caption(
            image=chunk.image_data,
            prompt=self._build_caption_prompt(chunk.context)
        )
        
        ocr_result, caption = await asyncio.gather(ocr_task, caption_task)
        
        # 组合文本
        combined_text = f"{caption}\n{ocr_result.text}"
        
        # 生成 embedding
        embedding = await self.embedding_model.embed(combined_text)
        
        return EnrichedChunk(
            chunk_id=chunk.chunk_id,
            element_type="image",
            content=combined_text,
            embedding=embedding,
            metadata={
                "ocr_text": ocr_result.text,
                "caption": caption,
                "layout_info": chunk.layout_info,
                "image_data": chunk.image_data  # 存储在对象存储
            }
        )

    async def _process_table_chunk(
        self,
        chunk: DocumentChunk
    ) -> EnrichedChunk:
        """处理表格块"""
        
        # 表格结构识别
        table_structure = await self._recognize_table_structure(chunk)
        
        # 生成表格摘要
        summary = await self._generate_table_summary(table_structure)
        
        # 生成 embedding
        combined_text = f"{summary}\n{table_structure.markdown}"
        embedding = await self.embedding_model.embed(combined_text)
        
        return EnrichedChunk(
            chunk_id=chunk.chunk_id,
            element_type="table",
            content=combined_text,
            embedding=embedding,
            metadata={
                "html": table_structure.html,
                "json": table_structure.json,
                "summary": summary,
                "headers": table_structure.headers
            }
        )
```

---

## 🎯 二、企业级集成架构

### 2.1 身份认证与 SSO

```yaml
# integrations/enterprise/auth/sso.yaml

enterprise_auth:
  # ─── SSO 提供商配置 ───────────────────────────
  providers:
    - type: "saml2"
      name: "Okta"
      enabled: true
      config:
        entity_id: "urn:skyone:shuge"
        sso_url: "https://company.okta.com/app/.../sso/saml"
        certificate_path: "/secrets/okta.crt"
        metadata_url: "https://company.okta.com/app/.../metadata"
        sign_requests: true
        # 属性映射
        attribute_mapping:
          email: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
          name: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
          groups: "http://schemas.xmlsoap.org/claims/Group"
          
    - type: "oidc"
      name: "Azure AD"
      enabled: true
      config:
        client_id: "${AZURE_CLIENT_ID}"
        client_secret: "${AZURE_CLIENT_SECRET}"
        issuer: "https://login.microsoftonline.com/{tenant}/v2.0"
        scopes: ["openid", "profile", "email", "api://skyone-shuge/.default"]
        # 属性映射
        claim_mapping:
          email: "email"
          name: "name"
          department: "department"
          
    - type: "ldap"
      name: "OpenLDAP"
      enabled: false
      config:
        server: "ldap://ldap.company.com:389"
        use_tls: true
        bind_dn: "cn=admin,dc=company,dc=com"
        bind_password: "${LDAP_BIND_PASSWORD}"
        base_dn: "ou=users,dc=company,dc=com"
        user_filter: "(uid={username})"
        group_filter: "(member={user_dn})"
        attribute_mapping:
          uid: "uid"
          email: "mail"
          name: "cn"
          groups: "memberOf"

  # ─── 会话管理 ───────────────────────────────
  session:
    provider: "redis"  # redis / memory
    ttl_seconds: 28800  # 8 hours
    refresh_token_ttl_days: 30
    max_concurrent_sessions: 5
    
  # ─── 组织架构同步 ───────────────────────────────
  org_sync:
    enabled: true
    sync_interval_minutes: 60
    sources:
      - type: "azure_ad"
        sync_groups: true
        sync_departments: true
        default_role: "member"
        
      - type: "ldap"
        sync_ous: true
        group_to_role_mapping:
          "cn=admins,ou=groups": "admin"
          "cn=editors,ou=groups": "editor"
          "cn=viewers,ou=groups": "viewer"
```

### 2.2 企业数据源集成

```python
# integrations/enterprise/connector_registry.py

class ConnectorRegistry:
    """
    企业数据源连接器注册表
    
    支持的数据源:
    - Notion
    - Confluence
    - SharePoint
    - Google Drive
    - Salesforce
    - Slack
    - Microsoft Teams
    """

    def __init__(self):
        self.connectors: dict[str, EnterpriseConnector] = {}
        self._register_default_connectors()

    def _register_default_connectors(self):
        self.register("notion", NotionConnector())
        self.register("confluence", ConfluenceConnector())
        self.register("sharepoint", SharePointConnector())
        self.register("gdrive", GoogleDriveConnector())
        self.register("salesforce", SalesforceConnector())
        self.register("slack", SlackConnector())
        self.register("teams", TeamsConnector())

    def register(self, name: str, connector: EnterpriseConnector):
        self.connectors[name] = connector

    async def sync_all(self) -> dict[str, SyncResult]:
        """同步所有已配置的数据源"""
        tasks = []
        for name, connector in self.connectors.items():
            if connector.is_enabled():
                tasks.append(connector.sync())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return dict(zip(self.connectors.keys(), results))


# integrations/enterprise/notion/connector.py

class NotionConnector(EnterpriseConnector):
    """
    Notion 数据源连接器
    
    功能:
    - 列出所有可用 Database
    - 增量同步页面内容
    - 双向同步 (读取和写入)
    - Webhook 实时更新
    """

    def __init__(self):
        self.client: NotionClient = None
        self.sync_state: NotionSyncState = SyncStateStore()
        self.webhook_handler: NotionWebhookHandler = None

    async def connect(self, config: NotionConnectorConfig):
        self.client = NotionClient(api_key=config.api_key)
        
        # 注册 Webhook (Notion API v2)
        self.webhook_handler = WebhookHandler(
            webhook_url=f"{API_BASE_URL}/webhooks/notion",
            events=["page.created", "page.updated", "page.deleted"]
        )
        await self.webhook_handler.register()

    async def list_databases(self) -> list[NotionDatabase]:
        """列出所有 Notion Database"""
        databases = []
        cursor = None
        
        while True:
            response = await self.client.search(
                filter={"property": "object", "value": "database"},
                start_cursor=cursor
            )
            databases.extend(response.results)
            
            if not response.has_more:
                break
            cursor = response.next_cursor
        
        return databases

    async def sync_page(self, page_id: str) -> SyncedDocument:
        """同步单个 Notion 页面"""
        
        # 获取页面属性和内容块
        page = await self.client.pages.retrieve(page_id)
        blocks = await self._get_all_blocks(page_id)
        
        # 转换为天一阁文档格式
        doc = self._to_skyone_document(page, blocks)
        
        # 保存到天一阁
        saved_doc = await self.document_store.upsert(doc)
        
        # 记录同步状态
        await self.sync_state.update(page_id, saved_doc.id)
        
        return saved_doc

    async def _get_all_blocks(self, page_id: str) -> list[Block]:
        """递归获取页面所有块"""
        blocks = []
        cursor = None
        
        while True:
            response = await self.client.blocks.children.list(
                block_id=page_id,
                start_cursor=cursor
            )
            blocks.extend(response.results)
            
            if not response.has_more:
                break
            cursor = response.next_cursor
        
        # 处理子块
        for block in blocks:
            if block.has_children:
                block.children = await self._get_all_blocks(block.id)
        
        return blocks
```

### 2.3 企业通讯集成

```python
# integrations/enterprise/teams/bot_service.py

class TeamsBotService:
    """
    Microsoft Teams Bot 服务
    
    功能:
    - 接收 @mention 消息
    - 搜索天一阁知识库
    - 推送文档更新通知
    - 卡片消息渲染
    """

    def __init__(self, config: TeamsConfig):
        self.graph_client = GraphClient(config)
        self.search_service = SearchService()
        self.notification_queue = asyncio.Queue()

    async def handle_mention(
        self,
        activity: TeamsActivity
    ) -> AdaptiveCardMessage:
        """处理 Teams @mention 消息"""
        
        # 解析用户查询
        query_text = self._extract_query(activity)
        
        # 搜索天一阁知识库
        results = await self.search_service.search(
            query=query_text,
            top_k=5,
            filters={"access_level": {"$lte": self._get_user_access_level(activity.from_user)}}
        )
        
        # 构建响应卡片
        card = self._build_search_result_card(results)
        
        return card

    def _build_search_result_card(
        self,
        results: list[SearchResult]
    ) -> AdaptiveCardMessage:
        """构建搜索结果卡片"""
        
        card = {
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": f"🔍 搜索到 {len(results)} 条相关结果",
                    "weight": "Bolder",
                    "size": "Medium"
                },
                {"type": "Container", "items": []}
            ],
            "actions": []
        }
        
        for result in results[:5]:
            # 添加文档摘要
            item = {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": result.document.title,
                        "weight": "Bolder",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": result.snippet,
                        "wrap": True,
                        "isSubtle": True,
                        "maxLines": 3
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {"title": "相似度", "value": f"{result.score:.2%}"},
                            {"title": "更新时间", "value": result.document.updated_at}
                        ]
                    }
                ]
            }
            card["body"][1]["items"].append(item)
        
        return AdaptiveCardMessage(content=card)
```

---

## 🎯 三、AI 模型微调与服务化架构

### 3.1 模型服务化架构

```yaml
# ml/model_serving/config.yaml

model_serving:
  # ─── 模型服务配置 ───────────────────────────────
  servers:
    # 通用 GPT 风格模型 (vLLM)
    - name: "gpt-server"
      provider: "vllm"
      model_path: "Qwen/Qwen2.5-72B-Instruct"
      tensor_parallel: 4
      gpu_memory_utilization: 0.92
      max_num_seqs: 256
      port: 8100
      
    # 视觉语言模型
    - name: "vl-server"
      provider: "vllm"
      model_path: "Qwen/Qwen2-VL-72B-Instruct"
      tensor_parallel: 4
      port: 8101
      
    # Embedding 模型
    - name: "embedding-server"
      provider: "vllm"
      model_path: "BAAI/bge-m3"
      tensor_parallel: 1
      port: 8102

  # ─── 模型路由 ───────────────────────────────
  router:
    strategy: "ab_test"  # ab_test / load_balance / quality_routing
    
    routes:
      - name: "default"
        models: ["gpt-server"]
        weight: 100
        
      - name: "quality-test"
        models: ["gpt-server", "qwen-plus"]
        weights: [50, 50]
        
    # 质量路由配置
    quality_routing:
      enabled: false
      thresholds:
        simple_query: 0.3   # 简单查询用小模型
        medium_query: 0.7   # 中等复杂度
        complex_query: 0.9  # 复杂查询用大模型
      model_mapping:
        simple_query: "qwen-turbo"
        medium_query: "qwen-plus"
        complex_query: "qwen2-72b"

  # ─── A/B 测试配置 ───────────────────────────────
  ab_tests:
    - test_id: "model-quality-ab"
      name: "模型质量对比测试"
      description: "对比 Qwen2.5-72B 和 Qwen2.5-7B 在知识问答上的质量差异"
      models: ["qwen-72b", "qwen-7b"]
      traffic_split: 0.2  # 20% 流量到实验组
      metrics:
        - name: "response_quality"
          type: "llm_judge"  # LLM 作为裁判评判
        - name: "latency"
          type: "p50_p99"
        - name: "user_satisfaction"
          type: "thumbs_up_rate"
      min_sample_size: 500
      run_duration_days: 7

  # ─── 模型注册表 ───────────────────────────────
  model_registry:
    storage: "postgres"
    
    models:
      - model_id: "qwen-72b"
        name: "Qwen 72B"
        type: "chat"
        provider: "vllm"
        endpoint: "http://vllm-gpt:8100/v1/chat/completions"
        cost_per_1k_tokens: 0.001
        capabilities: ["chat", "function_call", "json_mode"]
        
      - model_id: "qwen-7b"
        name: "Qwen 7B"
        type: "chat"
        provider: "vllm"
        endpoint: "http://vllm-small:8103/v1/chat/completions"
        cost_per_1k_tokens: 0.0001
        capabilities: ["chat", "function_call"]
        
      - model_id: "bge-m3"
        name: "BGE-M3 Embedding"
        type: "embedding"
        provider: "vllm"
        endpoint: "http://vllm-embed:8102/v1/embeddings"
        dimension: 1024
        cost_per_1k_tokens: 0.00001
```

### 3.2 微调训练管道

```python
# ml/fine_tuning/pipeline.py

from dataclasses import dataclass
import ray

@dataclass
class FineTuningJob:
    """微调任务"""
    job_id: str
    base_model: str
    training_type: str  # ipt / sft / dpo
    dataset_id: str
    config: FineTuningConfig
    status: str  # pending / preparing / training / evaluating / deploying
    checkpoints: list[str] = field(default_factory=list)
    current_checkpoint: str = None


class FineTuningPipeline:
    """
    模型微调训练管道
    
    支持:
    - 增量预训练 (IPT) - 在领域语料上继续预训练
    - 监督微调 (SFT) - 使用指令数据微调
    - DPO 偏好优化 - 使用人类偏好数据优化
    """

    def __init__(self, config: FineTuningPipelineConfig):
        self.config = config
        self.ray_cluster = self._init_ray()
        self.data_processor = DataProcessor()
        self.trainer_factory = TrainerFactory()
        self.model_registry = ModelRegistry()
        self.metrics_store = MetricsStore()

    async def create_job(
        self,
        base_model: str,
        training_type: str,
        dataset_id: str,
        hyperparams: dict = None
    ) -> FineTuningJob:
        """创建微调任务"""
        
        job = FineTuningJob(
            job_id=self._generate_id(),
            base_model=base_model,
            training_type=training_type,
            dataset_id=dataset_id,
            config=self._build_config(hyperparams),
            status="pending"
        )
        
        await self.job_store.save(job)
        
        # 启动异步执行
        asyncio.create_task(self._run_job(job.job_id))
        
        return job

    async def _run_job(self, job_id: str):
        """执行微调任务"""
        
        job = await self.job_store.get(job_id)
        
        try:
            # Phase 1: 数据准备
            job.status = "preparing"
            await self.job_store.save(job)
            
            dataset = await self._prepare_dataset(job)
            
            # Phase 2: 训练
            job.status = "training"
            await self.job_store.save(job)
            
            checkpoint_path = await self._train(job, dataset)
            
            # Phase 3: 评估
            job.status = "evaluating"
            await self.job_store.save(job)
            
            eval_metrics = await self._evaluate(job, checkpoint_path)
            
            # Phase 4: 部署
            if eval_metrics.passed:
                job.status = "deploying"
                await self.job_store.save(job)
                
                deployed_model = await self._deploy(job, checkpoint_path)
                job.current_checkpoint = deployed_model
                job.checkpoints.append(checkpoint_path)
            
            job.status = "completed"
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
        
        await self.job_store.save(job)

    async def _prepare_dataset(self, job: FineTuningJob) -> Dataset:
        """准备训练数据集"""
        
        # Step 1: 从天一阁知识库获取数据
        raw_docs = await self.knowledge_base.get_documents(
            tags=["training_data"],
            min_length=100
        )
        
        # Step 2: 数据清洗
        cleaned_docs = await self.data_processor.clean(raw_docs)
        
        # Step 3: 根据训练类型格式化
        if job.training_type == "ipt":
            # 增量预训练格式: 连续文本
            formatted = [self._to_pretraining_format(doc) for doc in cleaned_docs]
        elif job.training_type == "sft":
            # 监督微调格式: instruction, input, output
            formatted = [self._to_sft_format(doc) for doc in cleaned_docs]
        elif job.training_type == "dpo":
            # DPO 格式: prompt, chosen, rejected
            formatted = [self._to_dpo_format(doc) for doc in cleaned_docs]
        
        # Step 4: 划分训练/验证集
        train_data, val_data = self._split_dataset(formatted, val_ratio=0.05)
        
        return Dataset(train=train_data, val=val_data)

    async def _train(
        self,
        job: FineTuningJob,
        dataset: Dataset
    ) -> str:
        """执行模型训练"""
        
        # 创建 Ray Trainer
        trainer = self.trainer_factory.create(
            training_type=job.training_type,
            base_model=job.base_model,
            config=job.config
        )
        
        # 启动分布式训练
        result = await trainer.train(
            dataset=dataset,
            num_gpus=job.config.num_gpus,
            callbacks=[
                # Wandb 日志
                WandbCallback(project="skyone-finetune", job_id=job.job_id),
                # 早停
                EarlyStoppingCallback(metric="eval_loss", patience=3),
                # Checkpoint 保存
                CheckpointCallback(
                    save_dir=f"{self.config.checkpoint_dir}/{job.job_id}",
                    save_interval=500
                )
            ]
        )
        
        return result.checkpoint_path
```

### 3.3 模型 A/B 测试实现

```python
# ml/model_routing/ab_test.py

from dataclasses import dataclass
from typing import Callable
import hashlib
import numpy as np
from scipy import stats

@dataclass
class ABTestConfig:
    """A/B 测试配置"""
    test_id: str
    name: str
    control_model: str
    treatment_model: str
    traffic_split: float  # treatment 组流量比例
    metrics: list[ABMetric]
    min_sample_size: int
    significance_level: float = 0.05


@dataclass
class ABMetric:
    """A/B 测试指标"""
    name: str
    metric_type: str  # counter / gauge / histogram
    higher_is_better: bool = True


@dataclass
class ABTestResult:
    """A/B 测试结果"""
    test_id: str
    control_stats: dict
    treatment_stats: dict
    t_test_results: dict
    recommendation: str
    confidence_level: float


class ModelABRouter:
    """
    模型 A/B 测试路由器
    
    职责:
    - 用户流量分割 ( deterministic hash )
    - 请求路由到对应模型
    - 效果数据收集与存储
    - 统计显著性分析
    """

    def __init__(
        self,
        config: ABTestRouterConfig,
        metrics_store: MetricsStore
    ):
        self.config = config
        self.metrics_store = metrics_store
        self._init_routes()

    async def route(
        self,
        user_id: str,
        request: GenerationRequest
    ) -> GenerationResponse:
        """路由生成请求"""
        
        # 确定流量分组
        group = self._assign_group(user_id)
        model_name = (
            self.config.treatment_model
            if group == "treatment"
            else self.config.control_model
        )
        
        # 获取模型
        model = self.model_pool.get(model_name)
        
        # 执行生成
        start_time = time.time()
        response = await model.generate(request.prompt, **request.kwargs)
        latency = time.time() - start_time
        
        # 记录指标
        await self.metrics_store.record(
            test_id=self.config.test_id,
            group=group,
            user_id=user_id,
            request=request,
            response=response,
            latency_ms=latency * 1000,
            timestamp=datetime.utcnow()
        )
        
        # 添加测试元数据到响应
        response.metadata["ab_test"] = {
            "group": group,
            "model": model_name
        }
        
        return response

    def _assign_group(self, user_id: str) -> str:
        """基于用户 ID 确定性分配流量组"""
        hash_input = f"{self.config.test_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = (hash_value % 10000) / 10000.0
        
        return "treatment" if bucket < self.config.traffic_split else "control"

    async def analyze(self) -> ABTestResult:
        """分析 A/B 测试结果"""
        
        control_data = await self.metrics_store.get_group_data(
            self.config.test_id,
            "control"
        )
        treatment_data = await self.metrics_store.get_group_data(
            self.config.test_id,
            "treatment"
        )
        
        results = {}
        recommendations = []
        
        for metric in self.config.metrics:
            control_values = [getattr(r, metric.name) for r in control_data]
            treatment_values = [getattr(r, metric.name) for r in treatment_data]
            
            # 计算统计量
            control_mean = np.mean(control_values)
            treatment_mean = np.mean(treatment_values)
            
            # T 检验
            t_stat, p_value = stats.ttest_ind(control_values, treatment_values)
            
            # 效应量
            effect_size = (treatment_mean - control_mean) / np.std(control_values)
            
            is_significant = p_value < self.config.significance_level
            is_better = (
                treatment_mean > control_mean
                if metric.higher_is_better
                else treatment_mean < control_mean
            )
            
            results[metric.name] = {
                "control_mean": control_mean,
                "treatment_mean": treatment_mean,
                "delta": treatment_mean - control_mean,
                "delta_percent": (treatment_mean - control_mean) / control_mean * 100,
                "p_value": p_value,
                "significant": is_significant,
                "effect_size": effect_size,
                "sample_size": len(control_values)
            }
            
            if is_significant and is_better:
                recommendations.append(f"{metric.name}: 采用 treatment (提升 {results[metric.name]['delta_percent']:.2f}%)")
        
        # 综合推荐
        if len(recommendations) > len(self.config.metrics) * 0.5:
            recommendation = "采用 B 组模型"
        elif len(recommendations) == 0:
            recommendation = "保持 A 组模型 (无显著差异)"
        else:
            recommendation = "需要更多数据"
        
        return ABTestResult(
            test_id=self.config.test_id,
            control_stats={"mean": control_mean, "std": np.std(control_values)},
            treatment_stats={"mean": treatment_mean, "std": np.std(treatment_values)},
            t_test_results=results,
            recommendation=recommendation,
            confidence_level=1 - self.config.significance_level
        )
```

---

## 🎯 四、高级检索增强架构

### 4.1 混合检索架构

```yaml
# ml/retrieval/hybrid_search.yaml

hybrid_retrieval:
  # ─── 检索配置 ───────────────────────────────
  dense_retrieval:
    enabled: true
    vector_store: "qdrant"
    collection: "skyone_chunks"
    embedding_model: "BAAI/bge-m3"
    embedding_dim: 1024
    metric: "cosine"
    top_k: 50
    
  sparse_retrieval:
    enabled: true
    engine: "elasticsearch"  # elasticsearch / solr / opensearch
    index: "skyone_text"
    algorithm: "bm25"
    k1: 1.5  # BM25 参数
    b: 0.75  # BM25 参数
    top_k: 50
    
  # ─── 分数融合配置 ───────────────────────────────
  score_fusion:
    method: "rrf"  # rrf / convex / colaber
    rrf_k: 60  # RRF 超参数
    
    # Convex combination (当 method=convex 时)
    convex_weights:
      dense: 0.6
      sparse: 0.3
      keyword: 0.1

  # ─── 重排序配置 ───────────────────────────────
  reranking:
    enabled: true
    provider: "cross_encoder"  # cross_encoder / llm_rerank
    
    # Cross-Encoder 重排
    cross_encoder:
      model: "BAAI/bge-reranker-v2-m3"
      batch_size: 32
      max_length: 512
      
    # LLM 重排 (更准确但更慢)
    llm_rerank:
      enabled: false
      model: "qwen-72b"
      top_k: 20
      prompt: |
        请根据以下查询评估每个文档的相关性。
        查询: {query}
        文档: {documents}
        按相关性从高到低排序，输出 JSON 格式。

  # ─── 查询扩展 ───────────────────────────────
  query_expansion:
    enabled: true
    
    # HyDE (Hypothetical Document Embedding)
    hyde:
      enabled: true
      llm_model: "qwen-turbo"
      num_hypotheses: 3
      
    # 同义词扩展
    synonym_expansion:
      enabled: true
      synonyms_file: "/data/thesaurus.txt"
      
    # 查询改写
    query_rewrite:
      enabled: true
      llm_model: "qwen-plus"
      rewrite_prompt: |
        原始查询: {query}
        请改写查询，使其更加清晰和详细，以便检索相关文档。
```

### 4.2 检索核心实现

```python
# ml/retrieval/hybrid_search_engine.py

class HybridSearchEngine:
    """
    混合检索引擎
    
    检索流程:
    1. 查询理解 (分词/扩展/改写)
    2. 并行多路检索 (Dense + Sparse + Keyword)
    3. 分数归一化与融合
    4. 重排序
    5. 结果组装
    """

    def __init__(self, config: HybridRetrievalConfig):
        self.config = config
        self.dense_retriever = DenseRetriever(config.dense)
        self.sparse_retriever = SparseRetriever(config.sparse)
        self.keyword_retriever = KeywordRetriever(config.keyword)
        self.fusion = ScoreFusion(config.fusion)
        self.reranker = Reranker(config.reranking)
        self.query_expander = QueryExpander(config.query_expansion)

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict = None,
        search_config: SearchConfig = None
    ) -> SearchResponse:
        """执行混合检索"""
        
        config = search_config or SearchConfig()
        
        # Step 1: 查询理解
        if config.enable_expansion:
            expanded_queries = await self.query_expander.expand(query)
        else:
            expanded_queries = [query]
        
        # Step 2: 多路并行检索
        retrieval_tasks = []
        for eq in expanded_queries:
            retrieval_tasks.append(
                self._parallel_retrieve(eq, top_k * 2, filters)
            )
        
        all_results = await asyncio.gather(*retrieval_tasks)
        
        # 合并多查询结果
        merged_results = self._merge_retrieval_results(all_results)
        
        # Step 3: 分数融合
        if config.enable_fusion:
            fused_results = self.fusion.fuse(
                dense_results=merged_results.get("dense", []),
                sparse_results=merged_results.get("sparse", []),
                keyword_results=merged_results.get("keyword", [])
            )
        else:
            fused_results = merged_results.get("dense", [])
        
        # Step 4: 重排序
        if config.enable_rerank and len(fused_results) > 0:
            reranked_results = await self.reranker.rerank(
                query=query,
                candidates=fused_results[:top_k * 3],
                top_k=top_k
            )
        else:
            reranked_results = fused_results[:top_k]
        
        # Step 5: 组装响应
        return SearchResponse(
            query=query,
            expanded_queries=expanded_queries if config.enable_expansion else None,
            total=len(reranked_results),
            results=reranked_results,
            metadata={
                "dense_count": len(merged_results.get("dense", [])),
                "sparse_count": len(merged_results.get("sparse", [])),
                "rerank_applied": config.enable_rerank
            }
        )

    async def _parallel_retrieve(
        self,
        query: str,
        top_k: int,
        filters: dict
    ) -> dict[str, list[RetrievalResult]]:
        """并行执行多路检索"""
        
        tasks = [
            self.dense_retriever.retrieve(query, top_k, filters),
            self.sparse_retriever.retrieve(query, top_k, filters),
            self.keyword_retriever.retrieve(query, top_k, filters)
        ]
        
        dense, sparse, keyword = await asyncio.gather(*tasks)
        
        return {
            "dense": dense,
            "sparse": sparse,
            "keyword": keyword
        }
```

---

## 📊 验收标准

### 多模态 RAG
- [ ] 支持 PDF/Word/PPT 中的图像理解，Caption 召回率 > 80%
- [ ] 表格结构识别准确率 > 90%，支持行列合并
- [ ] 跨模态检索: 图像查询文本结果，mAP > 0.75
- [ ] 多模态 Chunking 保持语义完整性，分块大小可配置

### 企业集成
- [ ] SSO 登录成功率 > 99%，登录延迟 < 3s
- [ ] Notion 双向同步延迟 < 5min
- [ ] Teams/Slack 消息卡片渲染正确率 > 95%

### AI 模型微调
- [ ] DPO 训练收敛时间 < 24h (8xA100)
- [ ] 微调后模型在领域任务上 Perplexity 下降 > 20%
- [ ] A/B 测试框架支持 Statistically Significant 的结果判定

### 高级检索
- [ ] 混合检索比纯向量检索 MRR 提升 > 15%
- [ ] Cross-Encoder 重排延迟 < 100ms (Top-100)
- [ ] 查询扩展后 Recall@10 提升 > 10%

---

## 📁 相关文件

```
skyone-shuge/
├── prd/
│   └── MVP_v3.0.20.md              # PRD v3.0.20
├── architecture/
│   └── ARCHITECTURE_v3.0.20.md     # 架构 v3.0.20
├── src/
│   ├── ml/
│   │   ├── multimodal/
│   │   │   ├── pipeline.py         # 多模态处理管道
│   │   │   ├── image_understanding.py
│   │   │   ├── table_understanding.py
│   │   │   └── cross_modal_retrieval.py
│   │   ├── fine_tuning/
│   │   │   ├── pipeline.py         # 微调训练管道
│   │   │   ├── trainer.py          # 训练器
│   │   │   └── dpo_trainer.py      # DPO 训练器
│   │   └── retrieval/
│   │       ├── hybrid_search_engine.py
│   │       └── reranker.py
│   └── integrations/
│       └── enterprise/
│           ├── sso/
│           │   ├── saml_connector.py
│           │   ├── oidc_connector.py
│           │   └── ldap_connector.py
│           ├── notion/
│           │   └── connector.py
│           └── teams/
│               └── bot_service.py
└── tests/
    ├── multimodal/
    │   ├── test_image_understanding.py
    │   ├── test_table_parsing.py
    │   └── test_cross_modal_retrieval.py
    └── integration/
        ├── test_sso.py
        └── test_notion_sync.py
```
