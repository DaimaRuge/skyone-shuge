# 天一阁架构文档 v3.0.21

> **版本**: v3.0.21  
> **日期**: 2026-04-13  
> **主题**: 知识图谱增强 + 跨文档智能 + 语义缓存 + 自适应个性化  
> **依赖版本**: v3.0.20

---

## 📋 版本概述

v3.0.21 架构在 v3.0.20 基础上新增四大核心模块：

1. **知识图谱增强模块**: 实体提取、关系推理、知识存储
2. **跨文档智能模块**: 关联发现、知识缺口检测
3. **语义缓存模块**: 多级缓存、相似度匹配
4. **个性化引擎模块**: 用户画像、推荐重排

---

## 🏗️ 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              天一阁 v3.0.21                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │
│  │   Web UI    │    │  Mobile UI  │    │  API Client │                │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                │
│         │                   │                   │                       │
│         └───────────────────┼───────────────────┘                       │
│                             │                                            │
│                    ┌────────▼────────┐                                 │
│                    │   API Gateway   │                                 │
│                    │  (Kong/Traefik) │                                 │
│                    └────────┬────────┘                                 │
│                             │                                            │
│         ┌───────────────────┼───────────────────┐                     │
│         │                   │                   │                       │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐               │
│  │   Auth Svc  │    │  Search Svc  │    │   Cache Svc  │               │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘               │
│         │                   │                   │                       │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐               │
│  │  User Svc   │    │   RAG Svc   │    │    KG Svc    │               │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘               │
│         │                   │                   │                       │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐               │
│  │Personalization│   │ Cache Layer│    │   Neo4j     │               │
│  │   Engine    │    │(Redis/ANN) │    │ (Knowledge) │               │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘               │
│         │                   │                   │                       │
│         └───────────────────┼───────────────────┘                       │
│                             │                                            │
│  ┌──────────────────────────▼──────────────────────────┐                │
│  │                     LLM Gateway                     │                │
│  │     (OpenAI / Anthropic / 本地模型 / 模型路由)      │                │
│  └──────────────────────────┬──────────────────────────┘                │
│                             │                                            │
│         ┌───────────────────┼───────────────────┐                       │
│         │                   │                   │                        │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐                │
│  │  Qdrant     │    │  PostgreSQL │    │    Redis    │                │
│  │ (Vectors)   │    │   (PGVEC)   │    │  (Cache)    │                │
│  └─────────────┘    └─────────────┘    └─────────────┘                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 模块架构详解

### 1. 知识图谱模块 (Knowledge Graph)

```
knowledge_graph/
├── kg_service.py              # 知识图谱主服务
├── entity_extractor.py        # 实体提取器
├── relation_classifier.py     # 关系分类器
├── coreference_resolver.py    # 共指消解
├── graph_store.py             # 图存储接口 (Neo4j)
└── queries.py                 # 图查询模板

知识图谱存储设计:

Neo4j 节点:
  - Entity(name, type, description, confidence)
  - Document(doc_id, title, type)
  
Neo4j 关系:
  - (e1:Entity)-[:RELATES_TO{type, confidence}]->(e2:Entity)
  - (d:Document)-[:MENTIONS{entities}]->(e:Entity)
  - (e:Entity)-[:APPEARS_IN]->(d:Document)
```

### 2. 语义缓存模块 (Semantic Cache)

```
semantic_cache/
├── cache_service.py           # 缓存主服务
├── embedding_index.py         # ANN 索引 (Faiss/SQNS)
├── cache_key.py               # 缓存键生成
├── similarity_search.py       # 相似度搜索
└── cache_warmer.py           # 缓存预热

缓存层级:
  L1: Memory (LRU, 1000 items, ~10ms)
  L2: Redis (TTL 24h, 10000 items, ~1ms)
  L3: Disk (TTL 7d, 100000 items, ~10ms)
```

### 3. 个性化引擎 (Personalization)

```
personalization/
├── engine.py                  # 个性化主引擎
├── user_profile.py            # 用户画像
├── interaction_tracker.py    # 交互追踪
├── recommendation.py          # 推荐算法
├── reranker.py                # 结果重排
└── smart_defaults.py          # 智能默认

用户画像存储:
  PostgreSQL user_profiles 表
  - user_id, expertise_domains, skill_levels
  - preferred_doc_types, reading_depth
  - result_page_size, followed_topics
```

---

## 🔌 API 架构

### 知识图谱 API

```yaml
# 实体提取
POST /api/v1/kg/extract
Request:
  {
    "document_id": "doc_xxx",
    "extract_options": {
      "entity_types": ["PERSON", "ORG", "CONCEPT"],
      "min_confidence": 0.7
    }
  }
Response:
  {
    "entities": [...],
    "relations": [...],
    "triples": [...]
  }

# 实体查询
GET /api/v1/kg/entity/{entity_name}
Response:
  {
    "entity": {...},
    "connections": [...],  # 直接关联
    "subgraph": {...}      # 关联子图
  }

# 跨文档发现
POST /api/v1/kg/discover
Request:
  {
    "topic": "人工智能",
    "discovery_types": ["entity", "gap", "evolution"],
    "depth": 2
  }
Response:
  {
    "related_entities": [...],
    "knowledge_gaps": [...],
    "evolution_tracks": [...]
  }
```

### 语义缓存 API

```yaml
# 缓存统计
GET /api/v1/cache/stats
Response:
  {
    "hit_rate": 0.62,
    "total_requests": 100000,
    "cache_hits": 62000,
    "memory_size": 850,
    "redis_size": 7500
  }

# 缓存预热
POST /api/v1/cache/warmup
Request:
  {
    "strategy": "historical",  # or "predicted"
    "num_queries": 100
  }
```

### 个性化 API

```yaml
# 用户画像
GET /api/v1/user/profile
Response:
  {
    "user_id": "user_xxx",
    "expertise_domains": ["AI", "Software"],
    "skill_levels": {"AI": 0.8, "Python": 0.9},
    "recent_interests": [...]
  }

# 记录交互
POST /api/v1/user/interaction
Request:
  {
    "type": "click",  # click/query/save/share
    "document_id": "doc_xxx",
    "query": "搜索query",
    "duration": 120,   # 交互时长(秒)
    "params": {...}
  }

# 个性化推荐
GET /api/v1/user/recommendations
Response:
  {
    "recommended_docs": [...],
    "explore_queries": [...],
    "smart_defaults": {...}
  }
```

---

## 💾 数据模型

### 用户画像表 (PostgreSQL)

```sql
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP,
    
    -- 专业领域 (JSONB)
    expertise_domains JSONB DEFAULT '[]',
    skill_levels JSONB DEFAULT '{}',
    
    -- 行为特征 (JSONB)
    query_patterns JSONB DEFAULT '[]',
    preferred_doc_types JSONB DEFAULT '[]',
    reading_depth FLOAT DEFAULT 0,
    
    -- 交互偏好 (JSONB)
    preferences JSONB DEFAULT '{}',
    
    -- 知识需求 (JSONB)
    followed_topics JSONB DEFAULT '[]',
    recent_interests JSONB DEFAULT '[]',
    
    -- 索引
    INDEX idx_expertise USING GIN(expertise_domains),
    INDEX idx_last_active(last_active)
);
```

### 知识图谱表 (Neo4j)

```cypher
// 实体
CREATE (e:Entity {
    name: "人工智能",
    type: "CONCEPT",
    description: "研究如何让机器具有人类智能",
    confidence: 0.95,
    first_seen: datetime(),
    last_updated: datetime()
})

// 关系
MATCH (e1:Entity {name: "张亚勤"}),
      (e2:Entity {name: "百度"})
CREATE (e1)-[:WORKS_AT {
    relation_type: "EMPLOYS",
    confidence: 0.9,
    source_doc: "doc_xxx",
    created_at: datetime()
}]->(e2)
```

### 语义缓存表 (Qdrant)

```json
// Collection: semantic_cache
{
    "name": "semantic_cache",
    "vector_size": 1536,
    "distance": "Cosine",
    "payload_schema": {
        "cache_key": "keyword",
        "query": "text",
        "result": "text",
        "model": "keyword",
        "created_at": "datetime"
    }
}
```

---

## 🔄 数据流设计

### 实体提取流程

```
Document Upload
      │
      ▼
┌─────────────┐
│  Document   │
│  Parser     │  (PDF/Word/HTML → Text)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Chunking   │  (RecursiveCharacter → 512 tokens/chunk)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Entity    │  (LLM + NER → Entities)
│  Extractor  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Relation   │  (LLM → Relations)
│  Extractor  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Coreference │  (He/she/it → Resolved)
│  Resolver   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Neo4j     │  (Store KG)
│   Writer    │
└─────────────┘
```

### 语义缓存流程

```
Query Input
    │
    ├──► Exact Key Match ──► Return Cached Result
    │
    └──► ANN Search ──► Similarity > 0.85 ──► Return Cached Result
                  │
                  │ No Match
                  ▼
           LLM Compute ──► Store in Cache ──► Return Result
```

---

## ⚙️ 配置设计

### 环境变量

```bash
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=xxx

# Redis Cache
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=86400
CACHE_MAX_SIZE=10000

# Semantic Cache
SEMANTIC_CACHE_ENABLED=true
EXACT_MATCH_THRESHOLD=0.95
CACHE_HIT_THRESHOLD=0.85

# Personalization
PERSONALIZATION_ENABLED=true
INTERACTION_decay=0.95
```

---

## 📊 监控指标

### 知识图谱指标

| 指标 | 类型 | 告警阈值 |
|------|------|---------|
| entity_extraction_latency | histogram | p99 > 5s |
| kg_query_latency | histogram | p99 > 500ms |
| neo4j_connection_errors | counter | > 10/min |
| entity_extraction_failures | counter | > 5/min |

### 缓存指标

| 指标 | 类型 | 告警阈值 |
|------|------|---------|
| cache_hit_rate | gauge | < 0.5 |
| cache_latency_p99 | histogram | > 50ms |
| memory_cache_size | gauge | > 1000 |
| redis_cache_size | gauge | > 10000 |
| semantic_search_precision | gauge | < 0.85 |

### 个性化指标

| 指标 | 类型 | 告警阈值 |
|------|------|---------|
| personalization_latency | histogram | p99 > 100ms |
| rerank_precision | gauge | < 0.7 |
| profile_update_failures | counter | > 5/min |
| interaction_recording_errors | counter | > 10/min |

---

## 🧪 测试策略

### 单元测试

```python
# test_entity_extractor.py
def test_entity_extraction():
    extractor = EntityExtractor(llm_client=MockLLM())
    
    result = extractor.extract("张三在阿里巴巴工作。")
    
    assert len(result.entities) >= 2
    assert any(e.name == "张三" for e in result.entities)
    assert any(e.name == "阿里巴巴" for e in result.entities)

# test_semantic_cache.py
def test_cache_hit():
    cache = SemanticCache(...)
    
    result1 = cache.get_or_compute(
        "什么是人工智能",
        compute_fn=lambda: "AI is..."
    )
    
    result2 = cache.get_or_compute(
        "人工智能是什么",
        compute_fn=lambda: "..."  # 不应调用
    )
    
    assert result2.cached == True
    assert result2.hit_type == "semantic"
```

### 集成测试

```python
# test_kg_pipeline.py
async def test_full_extraction_pipeline():
    # 1. 上传文档
    doc = await upload_document("test.pdf")
    
    # 2. 提取实体
    extraction = await kg_service.extract(doc.id)
    
    # 3. 验证存储
    entities = await neo4j.query_entities(doc.id)
    assert len(entities) > 0
    
    # 4. 验证关联查询
    graph = await kg_service.get_entity_graph(
        entities[0].name
    )
    assert graph is not None
```

---

## 🚀 部署架构

### Kubernetes 部署

```yaml
# kg-service deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kg-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: kg-service
        image: skyone/kg-service:v3.0.21
        env:
        - name: NEO4J_URI
          valueFrom:
            secretKeyRef:
              name: neo4j-secret
              key: uri
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"

---
# semantic-cache deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: semantic-cache
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: cache-service
        image: skyone/cache-service:v3.0.21
        env:
        - name: REDIS_URL
          value: "redis://redis-cluster:6379"
```

---

## 🔮 未来迭代

### v3.0.22 规划方向

- [ ] 多语言知识图谱融合
- [ ] 实时知识图谱更新
- [ ] 图神经网络推理
- [ ] 分布式缓存一致性

### v4.0 规划方向

- [ ] 知识图谱对话式查询
- [ ] 自动化知识验证
- [ ] 外部知识库集成 (Wikipedia, DBpedia)
- [ ] 知识图谱可视化编辑器

---

## ✅ 架构 Checkpoint v3.0.21

- [x] 知识图谱增强架构设计
- [x] 跨文档智能发现架构设计
- [x] 语义缓存引擎架构设计
- [x] 自适应个性化引擎架构设计
- [x] API 接口设计
- [x] 数据模型设计
- [x] 监控指标设计
