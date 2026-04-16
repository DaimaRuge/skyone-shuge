# 天一阁 PRD v3.0.21

> **版本**: v3.0.21  
> **日期**: 2026-04-13  
> **主题**: 知识图谱增强 + 跨文档智能 + 语义缓存 + 自适应个性化引擎  
> **迭代周期**: 每日连续迭代

---

## 📋 版本概述

本次迭代 (v3.0.21) 在 v3.0.20 多模态 RAG 与高级检索增强的基础上，重点解决以下问题：

1. **知识图谱增强**: 从文档级理解走向实体级理解，构建知识网络
2. **跨文档智能**: 发现文档间的隐性关联，实现知识发现
3. **语义缓存**: 降低重复 LLM 调用成本，提升响应速度
4. **自适应个性化**: 学习用户行为，提供智能默认与主动推荐

---

## 🗂️ 目录

- [1. 知识图谱增强架构](#1-知识图谱增强架构)
- [2. 跨文档智能发现](#2-跨文档智能发现)
- [3. 语义缓存引擎](#3-语义缓存引擎)
- [4. 自适应个性化引擎](#4-自适应个性化引擎)
- [5. 技术实现细节](#5-技术实现细节)
- [6. PRD Checkpoint](#6-prd-checkpoint)

---

## 1. 知识图谱增强架构

### 1.1 概述

知识图谱增强在现有文档向量检索基础上，引入**结构化知识表示**，将非结构化文档转化为可推理的知识网络。

### 1.2 核心概念

```
实体 (Entity)
├── 人物 (Person)
├── 组织 (Organization)
├── 概念 (Concept)
├── 事件 (Event)
└── 文档 (Document)

关系 (Relation)
├── 人物-组织: 任职、创立、投资
├── 人物-人物: 合作、竞争、亲属
├── 概念-概念: 包含、对立、因果
├── 事件-人物: 参与、组织
└── 文档-实体: 提及、讨论、引用
```

### 1.3 实体提取流程

```python
class EntityExtractor:
    """实体提取器 - 从文档中提取结构化知识"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.entity_types = [
            "人物", "组织", "概念", "事件", 
            "地点", "时间", "文档"
        ]
    
    async def extract(self, document: Document) -> ExtractionResult:
        """
        从文档中提取实体和关系
        
        流程:
        1. 分块处理 (chunking)
        2. 并行实体识别 (NER + LLM)
        3. 关系抽取 (relation extraction)
        4. 共指消解 (coreference resolution)
        5. 知识融合 (knowledge fusion)
        """
        
        # Step 1: 文档分块
        chunks = self._chunk_document(document)
        
        # Step 2: 并行实体识别
        extraction_tasks = [
            self._extract_chunk_entities(chunk) 
            for chunk in chunks
        ]
        chunk_results = await asyncio.gather(*extraction_tasks)
        
        # Step 3: 关系抽取
        relations = await self._extract_relations(
            chunks, chunk_results
        )
        
        # Step 4: 共指消解
        merged_entities = self._coreference_resolution(
            chunk_results
        )
        
        # Step 5: 知识融合
        kg_triples = self._fuse_knowledge(
            merged_entities, relations
        )
        
        return ExtractionResult(
            entities=merged_entities,
            relations=relations,
            triples=kg_triples,
            confidence_scores=self._compute_confidence(kg_triples)
        )
    
    async def _extract_chunk_entities(
        self, chunk: DocumentChunk
    ) -> ChunkExtraction:
        """从单个块中提取实体"""
        
        prompt = f"""
        从以下文本中提取实体和关系。

        文本:
        {chunk.content}

        要求:
        1. 识别所有实体及其类型
        2. 识别实体间的关系
        3. 为每个提取结果给出置信度 (0-1)

        输出格式 (JSON):
        {{
            "entities": [
                {{
                    "name": "实体名",
                    "type": "实体类型",
                    "mentions": ["出现位置"],
                    "confidence": 0.95
                }}
            ],
            "relations": [
                {{
                    "source": "实体A",
                    "target": "实体B", 
                    "relation": "关系类型",
                    "confidence": 0.88
                }}
            ]
        }}
        """
        
        response = await self.llm.acomplete(prompt)
        return self._parse_extraction(response)
```

### 1.4 实体类型定义

| 实体类型 | 标识 | 示例 | 提取方法 |
|---------|------|------|---------|
| 人物 | PERSON | 张三、李明 | NER + 角色识别 |
| 组织 | ORG | 阿里巴巴、华为 | NER + 组织名识别 |
| 概念 | CONCEPT | 人工智能、机器学习 | 术语识别 + LLM |
| 事件 | EVENT | 产品发布、并购 | 事件抽取 + 触发词 |
| 地点 | LOCATION | 北京、杭州 | NER + 地名识别 |
| 时间 | TIME | 2024年、Q3 | 时间表达式识别 |
| 文档 | DOCUMENT | 本文档、XXX报告 | 引用识别 |

### 1.5 关系类型定义

| 关系类型 | 标识 | 示例 | 反关系 |
|---------|------|------|--------|
| 包含 | CONTAINS | 杭州 包含 西湖区 | IS_PART_OF |
| 关联 | RELATED_TO | 张三 关联 李四 | RELATED_TO |
| 因果 | CAUSES | A 导致 B | CAUSED_BY |
| 时序 | OCCURS_BEFORE | 事件A 先于 事件B | OCCURS_AFTER |
| 引用 | CITES | 文档A 引用 文档B | CITED_BY |
| 属于 | BELONGS_TO | 张三 属于 技术部 | HAS_MEMBER |
| 创建 | CREATED_BY | 文档 由 张三创建 | CREATES |
| 任职 | WORKS_AT | 张三 任职于 阿里巴巴 | EMPLOYS |

---

## 2. 跨文档智能发现

### 2.1 概述

跨文档智能发现通过分析多个文档之间的**隐性关联**，帮助用户发现未曾主动寻找但可能重要的知识。

### 2.2 发现类型

```
跨文档发现类型
├── 实体关联发现
│   ├── 同一实体在不同文档中的讨论
│   ├── 实体间的隐藏关系
│   └── 实体热点分析
│
├── 知识缺口发现
│   ├── 引用了但未提供内容的文档
│   ├── 逻辑链路的缺失环节
│   └── 矛盾观点检测
│
├── 知识演变发现
│   ├── 概念的历史演变
│   ├── 技术栈的演进轨迹
│   └── 组织的人员变动
│
└── 协同引用发现
    ├── 多文档共同引用的核心资料
    ├── 不同观点的代表性文档
    └── 跨领域的知识桥梁
```

### 2.3 实体关联分析器

```python
class CrossDocEntityAnalyzer:
    """跨文档实体关联分析"""
    
    def __init__(self, kg_store: KnowledgeGraphStore):
        self.kg = kg_store
    
    async def find_entity_connections(
        self, 
        entity_name: str,
        depth: int = 2
    ) -> EntityConnectionGraph:
        """
        查找实体的关联网络
        
        depth=1: 直接关联的实体
        depth=2: 关联实体的关联
        """
        
        # BFS 遍历知识图谱
        visited = set()
        levels = {entity_name: 0}
        connections = []
        
        queue = deque([entity_name])
        
        while queue:
            current = queue.popleft()
            if levels[current] >= depth:
                continue
                
            # 获取直接关联
            related = await self.kg.get_related_entities(
                current, 
                max_results=20
            )
            
            for rel_entity, relation_type in related:
                connections.append({
                    "from": current,
                    "to": rel_entity,
                    "relation": relation_type,
                    "depth": levels[current] + 1
                })
                
                if rel_entity not in visited:
                    visited.add(rel_entity)
                    levels[rel_entity] = levels[current] + 1
                    queue.append(rel_entity)
        
        return EntityConnectionGraph(
            central_entity=entity_name,
            connections=connections,
            subgraph=self._build_subgraph(connections)
        )
    
    async def detect_knowledge_gaps(
        self, 
        topic: str
    ) -> list[KnowledgeGap]:
        """
        检测知识缺口
        
        1. 找出引用了但未收录的文档
        2. 找出逻辑链路缺失
        3. 找出矛盾观点
        """
        
        # 获取主题相关文档
        related_docs = await self.kg.get_documents_by_topic(topic)
        
        gaps = []
        
        # 检测引用缺口
        citation_gaps = await self._find_citation_gaps(related_docs)
        gaps.extend(citation_gaps)
        
        # 检测逻辑缺口
        logic_gaps = await self._find_logic_gaps(related_docs)
        gaps.extend(logic_gaps)
        
        # 检测矛盾
        contradictions = await self._find_contradictions(related_docs)
        gaps.extend(contradictions)
        
        return gaps
```

### 2.4 文档关联度计算

```python
class DocRelationScorer:
    """文档关联度评分"""
    
    async def compute_relatedness(
        self,
        source_doc: Document,
        target_docs: list[Document]
    ) -> list[tuple[str, float]]:
        """
        计算文档间关联度
        
        评分维度:
        - 实体重叠度 (40%)
        - 概念重叠度 (30%)
        - 引用关系 (20%)
        - 向量相似度 (10%)
        """
        
        source_entities = await self._get_doc_entities(source_doc)
        source_concepts = await self._get_doc_concepts(source_doc)
        
        scores = []
        
        for doc in target_docs:
            # 实体重叠度
            doc_entities = await self._get_doc_entities(doc)
            entity_overlap = len(
                source_entities & doc_entities
            ) / max(len(source_entities), len(doc_entities))
            
            # 概念重叠度
            doc_concepts = await self._get_doc_concepts(doc)
            concept_overlap = len(
                source_concepts & doc_concepts
            ) / max(len(source_concepts), len(doc_concepts))
            
            # 引用关系
            citation_score = 1.0 if self._is_cited(doc, source_doc) else 0.0
            
            # 向量相似度
            vector_sim = await self._compute_vector_sim(
                source_doc, doc
            )
            
            # 加权求和
            final_score = (
                entity_overlap * 0.4 +
                concept_overlap * 0.3 +
                citation_score * 0.2 +
                vector_sim * 0.1
            )
            
            scores.append((doc.id, final_score))
        
        return sorted(scores, key=lambda x: x[1], reverse=True)
```

---

## 3. 语义缓存引擎

### 3.1 概述

语义缓存通过识别**语义相似**的查询，复用已有计算结果，显著降低 LLM 调用成本和响应延迟。

### 3.2 缓存架构

```
语义缓存架构
├── 缓存存储层
│   ├── Memory Cache (LRU, 1000 条)
│   ├── Redis Cache (TTL 24h, 10000 条)
│   └── Disk Cache (持久化, 100000 条)
│
├── 缓存键生成
│   ├── 查询向量化 (embedding)
│   ├── 语义哈希 (semantic hash)
│   └── 缓存键: hash(embedding + model + params)
│
├── 相似度匹配
│   ├── 近似最近邻 (ANN) 搜索
│   ├── 相似度阈值: 0.95 (完全匹配) / 0.85 (缓存命中)
│   └── 重排序: 精匹配 > 语义相似 > 新计算
│
└── 缓存策略
    ├── 读写策略: Cache-Aside
    ├── 淘汰策略: LRU + LFU 混合
    └── 预热策略: 基于历史查询模式
```

### 3.3 语义缓存实现

```python
class SemanticCache:
    """语义缓存 - 降低 LLM 调用成本"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        redis_client: Redis,
        config: CacheConfig
    ):
        self.vector_store = vector_store  # 用于 ANN 相似度搜索
        self.redis = redis_client
        self.config = config
        self.embedding_model = config.embedding_model
        
        # 语义相似度阈值
        self.exact_match_threshold = 0.95
        self.cache_hit_threshold = 0.85
        
        # 统计
        self.stats = CacheStats()
    
    def _generate_cache_key(
        self, 
        query: str, 
        model: str,
        params: dict
    ) -> str:
        """生成缓存键"""
        
        # 语义哈希: 结合查询向量 + 模型 + 参数
        query_vector = self.embedding_model.encode(query)
        
        cache_input = json.dumps({
            "query_vector": query_vector.tolist(),
            "model": model,
            "params": params
        }, sort_keys=True)
        
        return f"sem_cache:{hashlib.sha256(cache_input).hexdigest()}"
    
    async def get_or_compute(
        self,
        query: str,
        model: str,
        params: dict,
        compute_fn: Callable
    ) -> CacheResult:
        """
        语义缓存查询接口
        
        流程:
        1. 精确匹配 (cache key)
        2. 语义相似匹配 (ANN search)
        3. 缓存命中 → 返回缓存结果
        4. 缓存未命中 → 执行计算 → 存入缓存
        """
        
        # Step 1: 精确匹配
        exact_key = self._generate_cache_key(query, model, params)
        exact_result = await self._get_from_redis(exact_key)
        
        if exact_result:
            self.stats.record_hit("exact")
            return CacheResult(
                result=exact_result,
                hit_type="exact",
                cached=True
            )
        
        # Step 2: 语义相似匹配
        query_vector = self.embedding_model.encode(query)
        
        similar = await self.vector_store.search(
            query_vector=query_vector,
            collection="semantic_cache",
            top_k=5,
            score_threshold=self.cache_hit_threshold
        )
        
        if similar:
            # 找到语义相似的缓存
            cached_result = similar[0]
            
            self.stats.record_hit("semantic")
            
            # 异步更新缓存 (不阻塞返回)
            asyncio.create_task(
                self._update_cache_stats(similar)
            )
            
            return CacheResult(
                result=cached_result.payload["result"],
                hit_type="semantic",
                similarity=cached_result.score,
                cached=True
            )
        
        # Step 3: 缓存未命中，执行计算
        self.stats.record_miss()
        
        result = await compute_fn()
        
        # Step 4: 存入缓存
        await self._store_in_cache(
            key=exact_key,
            query=query,
            query_vector=query_vector,
            model=model,
            params=params,
            result=result
        )
        
        return CacheResult(
            result=result,
            hit_type="miss",
            cached=False
        )
    
    async def _store_in_cache(
        self,
        key: str,
        query: str,
        query_vector: np.ndarray,
        model: str,
        params: dict,
        result: Any
    ):
        """存储到缓存"""
        
        # 存储到 Redis (快速访问)
        cache_entry = {
            "query": query,
            "model": model,
            "params": params,
            "result": result,
            "created_at": time.time(),
            "access_count": 0
        }
        
        await self.redis.setex(
            key,
            self.config.redis_ttl,
            json.dumps(cache_entry)
        )
        
        # 存储向量到向量库 (语义搜索)
        await self.vector_store.insert(
            collection="semantic_cache",
            vector=query_vector.tolist(),
            payload={
                "cache_key": key,
                "query": query,
                "result": result,
                "model": model
            }
        )
```

### 3.4 缓存策略配置

```python
@dataclass
class CacheConfig:
    """缓存配置"""
    
    # 存储层级
    enable_memory_cache: bool = True
    enable_redis_cache: bool = True
    enable_disk_cache: bool = False
    
    # 容量限制
    memory_cache_size: int = 1000      # 内存缓存条数
    redis_cache_size: int = 10000      # Redis 缓存条数
    disk_cache_size: int = 100000      # 磁盘缓存条数
    
    # TTL 配置
    redis_ttl: int = 86400             # 24 小时
    disk_cache_ttl: int = 604800       # 7 天
    
    # 相似度阈值
    exact_match_threshold: float = 0.95
    cache_hit_threshold: float = 0.85
    
    # 预热配置
    enable_warmup: bool = True
    warmup_queries: int = 100          # 启动时预热查询数
```

---

## 4. 自适应个性化引擎

### 4.1 概述

自适应个性化引擎通过学习用户的**查询行为、浏览偏好和交互模式**，动态调整系统行为，提供个性化的知识服务体验。

### 4.2 用户画像

```python
@dataclass
class UserProfile:
    """用户画像"""
    
    # 基础信息
    user_id: str
    created_at: datetime
    last_active: datetime
    
    # 专业领域
    expertise_domains: list[str]          # 专业领域
    skill_levels: dict[str, float]         # 技能水平 (0-1)
    
    # 行为特征
    query_patterns: list[QueryPattern]     # 查询模式
    preferred_doc_types: list[str]        # 偏好文档类型
    reading_depth: float                   # 阅读深度 (平均文档长度)
    
    # 交互偏好
    result_page_size: int                 # 每页结果数
    preferred_summary_length: str          # 摘要长度偏好
    notification_preferences: dict        # 通知偏好
    
    # 知识需求
    followed_topics: list[str]             # 关注的话题
    saved_searches: list[SavedSearch]     # 保存的搜索
    recent_interests: list[str]            # 最近兴趣


@dataclass
class QueryPattern:
    """查询模式"""
    
    pattern_type: str                     # "exact", "browsing", "exploration"
    typical_queries: list[str]             # 典型查询
    typical_time: str                      # 典型查询时间
    avg_session_length: int               # 平均会话时长
    success_rate: float                    # 查询成功率
```

### 4.3 个性化推荐器

```python
class PersonalizationEngine:
    """个性化推荐引擎"""
    
    def __init__(
        self,
        user_profile_store: UserProfileStore,
        recommendation_model: RecommendationModel
    ):
        self.profile_store = user_profile_store
        self.model = recommendation_model
    
    async def get_personalized_results(
        self,
        user_id: str,
        query: str,
        raw_results: list[SearchResult]
    ) -> list[PersonalizedResult]:
        """
        对原始搜索结果进行个性化重排序
        
        排序因素:
        - 用户历史交互 (30%)
        - 专业领域匹配 (25%)
        - 查询相似度 (20%)
        - 时效性 (15%)
        - 社交信任 (10%)
        """
        
        profile = await self.profile_store.get(user_id)
        
        if not profile:
            # 无用户画像，使用默认排序
            return [PersonalizedResult(r, score=1.0) for r in raw_results]
        
        # 计算各维度得分
        scored_results = []
        
        for result in raw_results:
            scores = {}
            
            # 历史交互得分
            scores["interaction"] = self._calc_interaction_score(
                profile, result
            )
            
            # 领域匹配得分
            scores["domain"] = self._calc_domain_score(
                profile, result
            )
            
            # 查询相似度
            scores["query_sim"] = self._calc_query_similarity(
                profile, query, result
            )
            
            # 时效性得分
            scores["freshness"] = self._calc_freshness_score(result)
            
            # 社交信任得分
            scores["trust"] = self._calc_trust_score(result)
            
            # 加权求和
            final_score = (
                scores["interaction"] * 0.30 +
                scores["domain"] * 0.25 +
                scores["query_sim"] * 0.20 +
                scores["freshness"] * 0.15 +
                scores["trust"] * 0.10
            )
            
            scored_results.append(PersonalizedResult(
                original_result=result,
                score=final_score,
                score_breakdown=scores
            ))
        
        # 重排序
        return sorted(
            scored_results, 
            key=lambda x: x.score, 
            reverse=True
        )
    
    async def record_interaction(
        self,
        user_id: str,
        interaction: UserInteraction
    ):
        """记录用户交互，更新画像"""
        
        profile = await self.profile_store.get(user_id)
        
        # 更新交互历史
        profile.interaction_history.append(interaction)
        
        # 动态更新兴趣标签
        if interaction.type == "click":
            await self._update_interests_from_click(
                profile, interaction
            )
        elif interaction.type == "query":
            await self._update_interests_from_query(
                profile, interaction
            )
        elif interaction.type == "save":
            await self._update_interests_from_save(
                profile, interaction
            )
        
        # 衰减旧兴趣，强化新兴趣
        self._decay_old_interests(profile)
        
        await self.profile_store.save(profile)
    
    def _decay_old_interests(self, profile: UserProfile):
        """衰减旧的兴趣标签"""
        
        decay_factor = 0.95  # 每月衰减 5%
        current_time = datetime.now()
        
        for interest in profile.recent_interests:
            months_old = (
                current_time - interest.last_mentioned
            ).days / 30
            interest.strength *= (decay_factor ** months_old)
        
        # 移除强度过低的兴趣
        profile.recent_interests = [
            i for i in profile.recent_interests
            if i.strength > 0.1
        ]
```

### 4.4 智能默认系统

```python
class SmartDefaults:
    """智能默认 - 根据用户习惯自动设置"""
    
    def __init__(self, profile_store: UserProfileStore):
        self.profile_store = profile_store
    
    async def get_default_params(
        self,
        user_id: str,
        param_type: str
    ) -> Any:
        """
        获取用户个性化的默认参数
        
        参数类型:
        - search.page_size: 每页结果数
        - search.result_type: 结果类型 (详细/摘要)
        - summary.length: 摘要长度
        - filter.date_range: 默认日期范围
        - filter.doc_types: 默认文档类型过滤
        """
        
        profile = await self.profile_store.get(user_id)
        
        if not profile:
            return self._get_global_defaults(param_type)
        
        # 从历史行为中学习最佳默认
        return self._learn_from_history(profile, param_type)
    
    def _learn_from_history(
        self,
        profile: UserProfile,
        param_type: str
    ) -> Any:
        """从历史行为学习最佳默认"""
        
        history = profile.interaction_history
        
        if param_type == "search.page_size":
            # 分析用户实际使用的 page_size
            used_sizes = [
                i.params.get("page_size", 10) 
                for i in history 
                if "page_size" in i.params
            ]
            if used_sizes:
                # 返回最常用的大小
                return max(set(used_sizes), key=used_sizes.count)
            return 10
        
        elif param_type == "summary.length":
            # 分析用户的阅读深度
            avg_doc_length = profile.reading_depth
            if avg_doc_length > 5000:
                return "short"
            elif avg_doc_length > 2000:
                return "medium"
            return "detailed"
        
        elif param_type == "filter.date_range":
            # 分析用户查询的时效性偏好
            query_times = [i.timestamp for i in history]
            if self._prefers_recent(profile):
                return "last_month"
            return "all_time"
        
        return self._get_global_defaults(param_type)
```

---

## 5. 技术实现细节

### 5.1 知识图谱存储

```python
# 知识图谱使用 Neo4j 存储
# 支持高效的关系查询和路径发现

NEO4J_SCHEMA = """
    // 实体节点
    (:Entity {
        id: string,
        name: string,
        type: string,       // PERSON/ORG/CONCEPT/EVENT/LOCATION/TIME
        description: string,
        confidence: float,
        first_seen: datetime,
        last_updated: datetime
    })

    // 文档节点
    (:Document {
        id: string,
        title: string,
        doc_type: string,
        created_at: datetime
    })

    // 关系
    (:Entity)-[:RELATES_TO {
        relation_type: string,
        confidence: float,
        source_doc: string,
        created_at: datetime
    }]->(:Entity)

    (:Document)-[:MENTIONS {
        entities: list[string],
        context: string,
        confidence: float
    }]->(:Entity)
"""
```

### 5.2 API 端点

```
知识图谱 API
POST   /api/v1/kg/extract              # 实体提取
GET    /api/v1/kg/entity/{name}        # 查询实体
GET    /api/v1/kg/entity/{name}/graph # 获取关联图
POST   /api/v1/kg/discover             # 跨文档发现
GET    /api/v1/kg/topics/{topic}/gaps # 知识缺口检测

缓存 API
GET    /api/v1/cache/stats             # 缓存统计
POST   /api/v1/cache/invalidate        # 手动失效
GET    /api/v1/cache/hit-rate          # 命中率

个性化 API
GET    /api/v1/user/profile           # 获取用户画像
POST   /api/v1/user/interaction       # 记录交互
GET    /api/v1/user/recommendations    # 获取推荐
PUT    /api/v1/user/preferences        # 更新偏好
```

### 5.3 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 实体提取延迟 | < 2s/文档 | 1000 token 文档 |
| 跨文档关联查询 | < 500ms | 10万实体规模 |
| 语义缓存命中率 | > 60% | 生产环境预估 |
| 缓存加速比 | > 5x | 命中 vs 未命中 |
| 个性化重排延迟 | < 50ms | 单次查询 |

---

## 6. PRD Checkpoint v3.0.21

### 完成标准

- [ ] 知识图谱增强架构设计完成
- [ ] 跨文档智能发现方案设计完成
- [ ] 语义缓存引擎方案设计完成
- [ ] 自适应个性化引擎方案设计完成
- [ ] PRD v3.0.21 文档完成
- [ ] 架构 v3.0.21 文档完成
- [ ] ITERATION_LOG.md 更新至 v3.0.21
- [ ] ITERATION_PLAN.md 更新至 v3.0.21

---

## 📧 邮件发送

- **发送时间**: 2026-04-13 09:00
- **接收邮箱**: broadbtinp@gmail.com, dulie@foxmail.com
- **附件**: PRD v3.0.21
