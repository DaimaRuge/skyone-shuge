# 天一阁 PRD v3.0.14

**版本**: v3.0.14
**日期**: 2026-04-03
**阶段**: 智能推荐系统 + 文档版本对比 + 自动化工作流 + 高级分析报告 + 多语言支持完善

---

## 📋 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0.14 | 2026-04-03 | 智能推荐系统 + 文档版本对比 + 自动化工作流 + 高级分析报告 + 多语言支持完善 |
| v3.0.13 | 2026-03-30 | 移动端适配 + AI 辅助写作 + 知识图谱可视化 + 高级权限管理 + 数据备份与恢复 |
| v3.0.12 | 2026-03-29 | LibIndex One 同步服务 + 项目级管理 + 协作功能 + 插件系统 |

---

## 🎯 本次迭代目标

### 核心交付物
- [ ] **智能推荐系统**: 基于协同过滤 + 内容画像的个性化文档/知识推荐
- [ ] **文档版本对比**: 语义级 diff、变更高亮、版本历史时间轴
- [ ] **自动化工作流**: 可视化流程编排器、触发器与动作定义、状态机驱动
- [ ] **高级分析报告**: 用户行为分析、文档热度排名、团队协作洞察
- [ ] **多语言支持完善**: i18n 架构、RTL 支持、实时语言切换

---

## ✅ 一、智能推荐系统

### 1.1 推荐系统架构

```typescript
// types/recommendation.ts
export interface RecommendationRequest {
  user_id: string;
  context?: {
    current_doc_id?: string;
    search_query?: string;
    project_id?: string;
  };
  limit?: number;
  filters?: RecommendationFilters;
}

export interface RecommendationFilters {
  doc_types?: DocType[];
  tags?: string[];
  date_range?: { start: Date; end: Date };
  exclude_ids?: string[];
}

export interface RecommendationItem {
  doc_id: string;
  title: string;
  excerpt: string;
  score: number;
  reasons: RecommendationReason[];
  metadata: {
    doc_type: DocType;
    tags: string[];
    updated_at: Date;
    relevance_score: number;
    popularity_score: number;
  };
}

export type RecommendationReason = 
  | { type: 'similar_content'; message: string }
  | { type: 'same_project'; message: string }
  | { type: 'frequent_access'; message: string }
  | { type: 'collab_access'; message: string }
  | { type: 'trending'; message: string };

export interface UserProfile {
  user_id: string;
  interests: TagWeight[];
  access_history: AccessRecord[];
  collaboration_graph: CollaborationNode[];
  preferences: UserPreferences;
  embedding: number[];
}

export interface TagWeight {
  tag: string;
  weight: number;
}

export interface AccessRecord {
  doc_id: string;
  access_type: 'view' | 'edit' | 'comment' | 'share';
  timestamp: Date;
  duration_ms?: number;
}

export interface CollaborationNode {
  user_id: string;
  weight: number;
}
```

### 1.2 推荐算法引擎

```typescript
// services/recommendation/RecommendationEngine.ts
export class RecommendationEngine {
  constructor(
    private vectorStore: VectorStore,
    private userProfileStore: UserProfileStore,
    private docStore: DocumentStore,
    private analytics: AnalyticsService
  ) {}

  /**
   * 混合推荐算法：结合协同过滤 + 内容相似度 + 热度
   */
  async recommend(req: RecommendationRequest): Promise<RecommendationItem[]> {
    const userProfile = await this.userProfileStore.get(req.user_id);
    
    // 1. 基于内容的推荐（向量相似度）
    const contentBased = await this.contentBasedRecommend(userProfile, req);
    
    // 2. 协同过滤推荐
    const collaborative = await this.collaborativeRecommend(userProfile, req);
    
    // 3. 热门推荐（全局热度）
    const trending = await this.trendingRecommend(req);
    
    // 4. 加权融合
    const fused = this.hybridFusion(
      contentBased,
      collaborative,
      trending,
      { content: 0.4, collab: 0.35, trending: 0.25 }
    );
    
    // 5. 去重和过滤
    return this.deduplicateAndFilter(fused, req);
  }

  private async contentBasedRecommend(
    userProfile: UserProfile,
    req: RecommendationRequest
  ): Promise<ScoredDoc[]> {
    // 获取用户兴趣向量
    const userEmbedding = await this.computeUserInterestEmbedding(userProfile);
    
    // 语义搜索
    const results = await this.vectorStore.similaritySearch(userEmbedding, {
      limit: req.limit || 20,
      filters: this.buildFilters(req.filters)
    });
    
    return results.map(r => ({
      doc_id: r.doc_id,
      score: r.score,
      reasons: [{ type: 'similar_content', message: '内容与你的兴趣相关' }]
    }));
  }

  private async collaborativeRecommend(
    userProfile: UserProfile,
    req: RecommendationRequest
  ): Promise<ScoredDoc[]> {
    // 找到相似用户
    const similarUsers = await this.findSimilarUsers(userProfile.user_id);
    
    // 获取相似用户访问但当前用户未访问的文档
    const candidateDocs = await this.getCandidateDocsFromUsers(similarUsers);
    
    return candidateDocs.map(d => ({
      doc_id: d.doc_id,
      score: d.score,
      reasons: [{ type: 'collab_access', message: '与你相似的用户也在看' }]
    }));
  }

  private async trendingRecommend(
    req: RecommendationRequest
  ): Promise<ScoredDoc[]> {
    // 最近 N 天访问量排名
    const trending = await this.analytics.getTrendingDocs({
      days: 7,
      limit: req.limit || 10,
      project_id: req.context?.project_id
    });
    
    return trending.map((d, i) => ({
      doc_id: d.doc_id,
      score: 1 - (i / trending.length),
      reasons: [{ type: 'trending', message: '近期热门文档' }]
    }));
  }

  private hybridFusion(
    content: ScoredDoc[],
    collab: ScoredDoc[],
    trending: ScoredDoc[],
    weights: { content: number; collab: number; trending: number }
  ): ScoredDoc[] {
    const scoreMap = new Map<string, { doc: DocMeta; score: number; reasons: any[] }>();
    
    // 归一化并加权
    const maxScore = (arr: ScoredDoc[]) => Math.max(...arr.map(d => d.score), 0.001);
    
    content.forEach(d => {
      const w = weights.content * (d.score / maxScore(content));
      scoreMap.set(d.doc_id, { doc: d, score: w, reasons: d.reasons });
    });
    
    collab.forEach(d => {
      const existing = scoreMap.get(d.doc_id);
      const w = weights.collab * (d.score / maxScore(collab));
      if (existing) {
        existing.score += w;
        existing.reasons.push(...d.reasons);
      } else {
        scoreMap.set(d.doc_id, { doc: d, score: w, reasons: d.reasons });
      }
    });
    
    trending.forEach(d => {
      const existing = scoreMap.get(d.doc_id);
      const w = weights.trending * (d.score / maxScore(trending));
      if (existing) {
        existing.score += w;
        existing.reasons.push(...d.reasons);
      } else {
        scoreMap.set(d.doc_id, { doc: d, score: w, reasons: d.reasons });
      }
    });
    
    return Array.from(scoreMap.values())
      .sort((a, b) => b.score - a.score)
      .map(e => ({ ...e.doc, score: e.score, reasons: e.reasons }));
  }

  private async computeUserInterestEmbedding(profile: UserProfile): Promise<number[]> {
    // 基于用户的标签权重和访问历史计算兴趣向量
    const tagVectors = await Promise.all(
      profile.interests.map(async ({ tag, weight }) => {
        const tagVector = await this.vectorStore.getTagVector(tag);
        return tagVector.map(v => v * weight);
      })
    );
    
    // 聚合向量
    return this.averageVectors(tagVectors);
  }

  private averageVectors(vectors: number[][]): number[] {
    if (vectors.length === 0) return [];
    const dim = vectors[0].length;
    const sum = new Array(dim).fill(0);
    vectors.forEach(v => v.forEach((val, i) => sum[i] += val));
    return sum.map(s => s / vectors.length);
  }
}
```

### 1.3 推荐服务 API

```typescript
// api/routes/recommendation.ts
import { Router } from 'express';
const router = Router();

/**
 * GET /api/recommendations
 * 获取个性化推荐
 */
router.get('/', async (req, res) => {
  const { user_id, context, limit, doc_type, tags } = req.query;
  
  const result = await recommendationEngine.recommend({
    user_id,
    context: context ? JSON.parse(context) : undefined,
    limit: parseInt(limit) || 10,
    filters: { doc_types: doc_type?.split(','), tags: tags?.split(',') }
  });
  
  res.json({ success: true, data: result });
});

/**
 * POST /api/recommendations/feedback
 * 记录推荐反馈
 */
router.post('/feedback', async (req, res) => {
  const { user_id, doc_id, action, reason } = req.body;
  
  await analyticsService.recordRecommendationFeedback({
    user_id, doc_id, action, reason, timestamp: new Date()
  });
  
  res.json({ success: true });
});

/**
 * GET /api/recommendations/trending
 * 获取热门推荐
 */
router.get('/trending', async (req, res) => {
  const { project_id, days, limit } = req.query;
  
  const trending = await analyticsService.getTrendingDocs({
    project_id,
    days: parseInt(days) || 7,
    limit: parseInt(limit) || 10
  });
  
  res.json({ success: true, data: trending });
});
```

### 1.4 用户画像更新

```typescript
// services/recommendation/UserProfileUpdater.ts
export class UserProfileUpdater {
  constructor(
    private userProfileStore: UserProfileStore,
    private vectorStore: VectorStore
  ) {}

  /**
   * 实时更新用户画像
   */
  async updateProfile(userId: string, event: UserEvent): Promise<void> {
    const profile = await this.userProfileStore.get(userId);
    
    switch (event.type) {
      case 'doc_access':
        await this.handleDocAccess(profile, event);
        break;
      case 'doc_edit':
        await this.handleDocEdit(profile, event);
        break;
      case 'comment':
        await this.handleComment(profile, event);
        break;
      case 'search':
        await this.handleSearch(profile, event);
        break;
    }
    
    // 异步重建兴趣向量
    this.rebuildInterestEmbedding(profile);
    
    await this.userProfileStore.save(profile);
  }

  private async handleDocAccess(profile: UserProfile, event: UserEvent): Promise<void> {
    // 记录访问历史
    profile.access_history.push({
      doc_id: event.doc_id,
      access_type: 'view',
      timestamp: event.timestamp,
      duration_ms: event.duration_ms
    });
    
    // 保持历史在合理范围（最近 1000 条）
    if (profile.access_history.length > 1000) {
      profile.access_history = profile.access_history.slice(-1000);
    }
    
    // 更新标签权重
    const doc = event.doc;
    doc.tags.forEach(tag => {
      const existing = profile.interests.find(t => t.tag === tag);
      if (existing) {
        existing.weight = Math.min(existing.weight + 0.1, 1.0);
      } else {
        profile.interests.push({ tag, weight: 0.1 });
      }
    });
  }

  private async handleSearch(profile: UserProfile, event: UserEvent): Promise<void> {
    // 搜索词可以作为临时兴趣
    const searchEmbedding = await this.vectorStore.embedText(event.query);
    
    // 与现有兴趣向量融合
    if (profile.embedding.length === 0) {
      profile.embedding = searchEmbedding;
    } else {
      profile.embedding = profile.embedding.map(
        (v, i) => v * 0.9 + searchEmbedding[i] * 0.1
      );
    }
  }

  private async rebuildInterestEmbedding(profile: UserProfile): Promise<void> {
    // 基于更新的标签权重重新计算向量
    const vectors = await Promise.all(
      profile.interests.map(({ tag, weight }) =>
        this.vectorStore.getTagVector(tag).then(v => v.map(val => val * weight))
      )
    );
    
    profile.embedding = this.averageVectors(vectors);
  }
}
```

---

## ✅ 二、文档版本对比

### 2.1 版本对比引擎

```typescript
// types/version.ts
export interface DocVersion {
  version_id: string;
  doc_id: string;
  version_number: number;
  content: string;
  content_hash: string;
  created_at: Date;
  created_by: string;
  comment?: string;
  change_stats?: ChangeStats;
}

export interface ChangeStats {
  lines_added: number;
  lines_deleted: number;
  lines_modified: number;
  files_changed: number;
}

export interface VersionDiff {
  base_version: string;
  target_version: string;
  hunks: DiffHunk[];
  summary: DiffSummary;
}

export interface DiffHunk {
  oldStart: number;
  oldLines: number;
  newStart: number;
  newLines: number;
  changes: DiffChange[];
}

export type DiffChange = 
  | { type: 'context'; lines: string[] }
  | { type: 'add'; lines: string[] }
  | { type: 'delete'; lines: string[] };

export interface DiffSummary {
  insertions: number;
  deletions: number;
  modifications: number;
  unchanged: number;
}
```

### 2.2 语义级 Diff 算法

```typescript
// services/version/SemanticDiffEngine.ts
export class SemanticDiffEngine {
  constructor(
    private tokenizer: Tokenizer,
    private similarity: SimilarityEngine
  ) {}

  /**
   * 语义级文档对比
   */
  async computeDiff(doc1: DocVersion, doc2: DocVersion): Promise<VersionDiff> {
    const tokens1 = this.tokenizer.tokenize(doc1.content);
    const tokens2 = this.tokenizer.tokenize(doc2.content);
    
    // 1. 句子级别的 LCS（最长公共子序列）
    const sentenceAlignment = this.alignSentences(tokens1.sentences, tokens2.sentences);
    
    // 2. 计算语义相似度，决定是否标记为"修改"而非"删除+新增"
    const semanticChanges = await this.detectSemanticChanges(sentenceAlignment);
    
    // 3. 行级别的细粒度 diff
    const lineDiff = this.computeLineDiff(doc1.content, doc2.content);
    
    // 4. 合并结果
    return this.mergeResults(lineDiff, semanticChanges, doc1, doc2);
  }

  private async detectSemanticChanges(
    alignment: SentenceAlignment[]
  ): Promise<SemanticChange[]> {
    const changes: SemanticChange[] = [];
    
    for (const align of alignment) {
      if (align.type === 'modified') {
        const similarity = await this.similarity.compute(
          align.sentence1.text,
          align.sentence2.text
        );
        
        // 相似度 > 0.7 认为是语义修改，< 0.7 是替换
        if (similarity > 0.7) {
          changes.push({
            type: 'semantic_modify',
            oldRange: align.range1,
            newRange: align.range2,
            similarity,
            wordChanges: this.computeWordChanges(align.sentence1, align.sentence2)
          });
        } else {
          changes.push({
            type: 'replace',
            oldRange: align.range1,
            newRange: align.range2,
            similarity
          });
        }
      }
    }
    
    return changes;
  }

  private computeWordChanges(s1: Sentence, s2: Sentence): WordChange[] {
    const words1 = s1.text.split(/\s+/);
    const words2 = s2.text.split(/\s+/);
    
    // LCS 计算词级别差异
    const lcs = this.lcs(words1, words2);
    const changes: WordChange[] = [];
    
    let i1 = 0, i2 = 0, iLcs = 0;
    while (i1 < words1.length || i2 < words2.length) {
      if (iLcs < lcs.length) {
        if (words1[i1] !== lcs[iLcs]) {
          changes.push({ type: 'delete', word: words1[i1], position: i1 });
          i1++;
        } else if (words2[i2] !== lcs[iLcs]) {
          changes.push({ type: 'add', word: words2[i2], position: i2 });
          i2++;
        } else {
          i1++; i2++; iLcs++;
        }
      } else {
        if (i1 < words1.length) {
          changes.push({ type: 'delete', word: words1[i1], position: i1 });
          i1++;
        }
        if (i2 < words2.length) {
          changes.push({ type: 'add', word: words2[i2], position: i2 });
          i2++;
        }
      }
    }
    
    return changes;
  }

  private lcs(a: string[], b: string[]): string[] {
    const m = a.length, n = b.length;
    const dp: number[][] = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));
    
    for (let i = 1; i <= m; i++) {
      for (let j = 1; j <= n; j++) {
        if (a[i - 1] === b[j - 1]) {
          dp[i][j] = dp[i - 1][j - 1] + 1;
        } else {
          dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
        }
      }
    }
    
    // 回溯
    const result: string[] = [];
    let i = m, j = n;
    while (i > 0 && j > 0) {
      if (a[i - 1] === b[j - 1]) {
        result.unshift(a[i - 1]);
        i--; j--;
      } else if (dp[i - 1][j] > dp[i][j - 1]) {
        i--;
      } else {
        j--;
      }
    }
    
    return result;
  }

  private computeLineDiff(content1: string, content2: string): LineDiffResult {
    const lines1 = content1.split('\n');
    const lines2 = content2.split('\n');
    
    const hunks: DiffHunk[] = [];
    let i = 0, j = 0;
    
    while (i < lines1.length || j < lines2.length) {
      const changes: DiffChange[] = [];
      let oldStart = i + 1, oldLines = 0;
      let newStart = j + 1, newLines = 0;
      
      // 寻找下一个差异块
      while (i < lines1.length && j < lines2.length && lines1[i] === lines2[j]) {
        changes.push({ type: 'context', lines: [lines1[i]] });
        i++; j++;
        oldLines++; newLines++;
      }
      
      // 检测删除和新增
      while (i < lines1.length && (j >= lines2.length || lines1[i] !== lines2[j])) {
        changes.push({ type: 'delete', lines: [lines1[i]] });
        i++; oldLines++;
      }
      
      while (j < lines2.length && (i >= lines1.length || lines2[j] !== lines1[i])) {
        changes.push({ type: 'add', lines: [lines2[j]] });
        j++; newLines++;
      }
      
      if (changes.length > 0 && (oldLines > 0 || newLines > 0)) {
        hunks.push({ oldStart, oldLines, newStart, newLines, changes });
      }
    }
    
    return { hunks };
  }
}
```

### 2.3 版本历史 API

```typescript
// api/routes/version.ts
const router = Router();

/**
 * GET /api/docs/:doc_id/versions
 * 获取文档版本列表
 */
router.get('/:doc_id/versions', async (req, res) => {
  const { doc_id } = req.params;
  const { page, limit } = req.query;
  
  const versions = await versionService.getVersions(doc_id, {
    page: parseInt(page) || 1,
    limit: parseInt(limit) || 20
  });
  
  res.json({ success: true, data: versions });
});

/**
 * GET /api/docs/:doc_id/versions/:version_id
 * 获取特定版本内容
 */
router.get('/:doc_id/versions/:version_id', async (req, res) => {
  const { doc_id, version_id } = req.params;
  
  const version = await versionService.getVersion(doc_id, version_id);
  res.json({ success: true, data: version });
});

/**
 * GET /api/docs/:doc_id/diff
 * 对比两个版本
 */
router.get('/:doc_id/diff', async (req, res) => {
  const { doc_id } = req.params;
  const { base, target, semantic } = req.query;
  
  const diff = await diffEngine.computeDiff(doc_id, base, target, {
    semantic: semantic === 'true'
  });
  
  res.json({ success: true, data: diff });
});

/**
 * POST /api/docs/:doc_id/versions
 * 创建新版本（保存快照）
 */
router.post('/:doc_id/versions', async (req, res) => {
  const { doc_id } = req.params;
  const { content, comment } = req.body;
  
  const version = await versionService.createVersion(doc_id, {
    content,
    comment,
    created_by: req.user.id
  });
  
  res.json({ success: true, data: version });
});

/**
 * POST /api/docs/:doc_id/restore/:version_id
 * 恢复指定版本
 */
router.post('/:doc_id/restore/:version_id', async (req, res) => {
  const { doc_id, version_id } = req.params;
  
  const restored = await versionService.restoreVersion(doc_id, version_id);
  res.json({ success: true, data: restored });
});
```

---

## ✅ 三、自动化工作流

### 3.1 工作流定义模型

```typescript
// types/workflow.ts
export interface Workflow {
  id: string;
  name: string;
  description?: string;
  trigger: Trigger;
  steps: WorkflowStep[];
  conditions?: Condition[];
  config: WorkflowConfig;
  status: WorkflowStatus;
  created_by: string;
  created_at: Date;
  updated_at: Date;
}

export type Trigger = 
  | { type: 'doc_created'; filters?: DocFilter[] }
  | { type: 'doc_updated'; filters?: DocFilter[]; debounce_seconds?: number }
  | { type: 'doc_tagged'; tags: string[] }
  | { type: 'schedule'; cron: string; timezone?: string }
  | { type: 'webhook'; url: string; secret?: string }
  | { type: 'manual'; };

export interface DocFilter {
  field: 'doc_type' | 'tags' | 'project_id' | 'created_by' | 'name';
  operator: 'equals' | 'contains' | 'regex' | 'in';
  value: any;
}

export interface WorkflowStep {
  id: string;
  name: string;
  action: StepAction;
  config: Record<string, any>;
  on_error?: StepErrorHandler;
  retry?: RetryConfig;
}

export type StepAction =
  | { type: 'notification'; channel: 'email' | 'feishu' | 'webhook'; template: string }
  | { type: 'doc_operation'; operation: 'tag' | 'move' | 'share' | 'archive' }
  | { type: 'ai_process'; task: 'summarize' | 'translate' | 'classify' | 'extract' }
  | { type: 'http_request'; method: string; url: string; headers?: Record<string, string> }
  | { type: 'transform'; transformer: 'to_summary' | 'to_markdown' | 'to_json' }
  | { type: 'condition'; branches: ConditionBranch[] }
  | { type: 'delay'; seconds: number }
  | { type: 'iterator'; items: string[]; step_id: string };

export interface ConditionBranch {
  condition: Condition;
  steps: WorkflowStep[];
}

export interface Condition {
  field: string;
  operator: 'equals' | 'not_equals' | 'contains' | 'greater' | 'less' | 'and' | 'or';
  value: any;
}

export interface RetryConfig {
  max_attempts: number;
  backoff_seconds: number;
  exponential: boolean;
}

export type WorkflowStatus = 'active' | 'paused' | 'draft';

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  trigger_data: Record<string, any>;
  status: ExecutionStatus;
  current_step?: string;
  step_results: Record<string, StepResult>;
  started_at: Date;
  completed_at?: Date;
  error?: string;
}

export type ExecutionStatus = 'running' | 'completed' | 'failed' | 'cancelled';

export interface StepResult {
  step_id: string;
  output: any;
  duration_ms: number;
  error?: string;
}
```

### 3.2 工作流引擎

```typescript
// services/workflow/WorkflowEngine.ts
export class WorkflowEngine {
  private executionQueue: AsyncQueue<WorkflowExecution>;
  
  constructor(
    private workflowStore: WorkflowStore,
    private executionStore: ExecutionStore,
    private stepExecutors: Map<string, StepExecutor>
  ) {
    this.executionQueue = new AsyncQueue({ concurrency: 5 });
  }

  /**
   * 触发工作流
   */
  async trigger(trigger: Trigger, context: TriggerContext): Promise<WorkflowExecution[]> {
    const matchingWorkflows = await this.findMatchingWorkflows(trigger, context);
    
    const executions: WorkflowExecution[] = [];
    for (const workflow of matchingWorkflows) {
      const execution = await this.createExecution(workflow, context);
      this.executionQueue.push(() => this.run(execution));
      executions.push(execution);
    }
    
    return executions;
  }

  private async run(execution: WorkflowExecution): Promise<void> {
    try {
      execution.status = 'running';
      await this.executionStore.save(execution);
      
      const workflow = await this.workflowStore.get(execution.workflow_id);
      
      for (const step of workflow.steps) {
        execution.current_step = step.id;
        await this.executionStore.save(execution);
        
        const result = await this.executeStep(step, execution);
        execution.step_results[step.id] = result;
        
        if (result.error && step.on_error) {
          await this.handleError(step, result.error, execution);
        }
        
        if (execution.status === 'cancelled') {
          return;
        }
      }
      
      execution.status = 'completed';
      execution.completed_at = new Date();
    } catch (error) {
      execution.status = 'failed';
      execution.error = error.message;
      execution.completed_at = new Date();
    } finally {
      await this.executionStore.save(execution);
    }
  }

  private async executeStep(step: WorkflowStep, execution: WorkflowExecution): Promise<StepResult> {
    const startTime = Date.now();
    const executor = this.stepExecutors.get(step.action.type);
    
    if (!executor) {
      return { step_id: step.id, output: null, duration_ms: 0, error: `Unknown action type: ${step.action.type}` };
    }
    
    let attempts = 0;
    const maxAttempts = step.retry?.max_attempts || 1;
    
    while (attempts < maxAttempts) {
      try {
        const output = await executor.execute(step.action, {
          workflow: execution,
          context: execution.trigger_data,
          previousResults: execution.step_results
        });
        return { step_id: step.id, output, duration_ms: Date.now() - startTime };
      } catch (error) {
        attempts++;
        if (attempts >= maxAttempts) {
          return { step_id: step.id, output: null, duration_ms: Date.now() - startTime, error: error.message };
        }
        if (step.retry) {
          const delay = step.retry.exponential 
            ? step.retry.backoff_seconds * Math.pow(2, attempts - 1) * 1000
            : step.retry.backoff_seconds * 1000;
          await sleep(delay);
        }
      }
    }
  }
}
```

### 3.3 工作流编排 API

```typescript
// api/routes/workflow.ts
const router = Router();

/**
 * GET /api/workflows
 * 获取工作流列表
 */
router.get('/', async (req, res) => {
  const { status, page, limit } = req.query;
  
  const workflows = await workflowStore.find({
    status: status as WorkflowStatus,
    created_by: req.user.id,
    page: parseInt(page) || 1,
    limit: parseInt(limit) || 20
  });
  
  res.json({ success: true, data: workflows });
});

/**
 * POST /api/workflows
 * 创建工作流
 */
router.post('/', async (req, res) => {
  const workflow = await workflowEngine.create({
    ...req.body,
    created_by: req.user.id
  });
  
  res.json({ success: true, data: workflow });
});

/**
 * PUT /api/workflows/:id
 * 更新工作流
 */
router.put('/:id', async (req, res) => {
  const workflow = await workflowEngine.update(req.params.id, req.body);
  res.json({ success: true, data: workflow });
});

/**
 * POST /api/workflows/:id/test
 * 测试工作流（手动触发）
 */
router.post('/:id/test', async (req, res) => {
  const execution = await workflowEngine.trigger(
    { type: 'manual' },
    { test_mode: true, ...req.body.context }
  );
  
  res.json({ success: true, data: execution });
});

/**
 * GET /api/workflows/:id/executions
 * 获取工作流执行历史
 */
router.get('/:id/executions', async (req, res) => {
  const { status, page, limit } = req.query;
  
  const executions = await executionStore.find({
    workflow_id: req.params.id,
    status: status as ExecutionStatus,
    page: parseInt(page) || 1,
    limit: parseInt(limit) || 20
  });
  
  res.json({ success: true, data: executions });
});

/**
 * POST /api/workflows/:id/pause
 * 暂停工作流
 */
router.post('/:id/pause', async (req, res) => {
  await workflowEngine.updateStatus(req.params.id, 'paused');
  res.json({ success: true });
});
```

---

## ✅ 四、高级分析报告

### 4.1 分析指标定义

```typescript
// types/analytics.ts
export interface AnalyticsReport {
  id: string;
  type: ReportType;
  period: { start: Date; end: Date };
  generated_at: Date;
  data: ReportData;
}

export type ReportType = 
  | 'user_activity'
  | 'doc_popularity'
  | 'team_collaboration'
  | 'knowledge_gaps'
  | 'engagement_metrics';

export interface ReportData {
  summary: MetricSummary;
  charts: ChartData[];
  insights: Insight[];
  recommendations: string[];
}

export interface MetricSummary {
  total_users: number;
  active_users: number;
  total_docs: number;
  active_docs: number;
  avg_session_duration: number;
  total_collaborations: number;
}

export interface ChartData {
  id: string;
  type: 'line' | 'bar' | 'pie' | 'heatmap';
  title: string;
  data: any;
  config?: Record<string, any>;
}

export interface Insight {
  type: 'trend' | 'anomaly' | 'correlation' | 'pattern';
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'critical';
  related_metrics: string[];
}

export interface UserActivityMetrics {
  user_id: string;
  period: { start: Date; end: Date };
  metrics: {
    sessions: number;
    total_time: number;
    docs_viewed: number;
    docs_edited: number;
    comments_made: number;
    searches: number;
  };
  activity_timeline: ActivityEvent[];
}

export interface DocPopularityMetrics {
  doc_id: string;
  title: string;
  metrics: {
    views: number;
    unique_viewers: number;
    edits: number;
    comments: number;
    shares: number;
    avg_time_spent: number;
  };
  trend: 'rising' | 'stable' | 'declining';
  rank: number;
}
```

### 4.2 分析引擎

```typescript
// services/analytics/AnalyticsEngine.ts
export class AnalyticsEngine {
  constructor(
    private eventStore: EventStore,
    private docStore: DocumentStore,
    private userStore: UserStore
  ) {}

  /**
   * 生成综合分析报告
   */
  async generateReport(
    type: ReportType,
    period: { start: Date; end: Date },
    filters?: ReportFilters
  ): Promise<AnalyticsReport> {
    switch (type) {
      case 'user_activity':
        return this.generateUserActivityReport(period, filters);
      case 'doc_popularity':
        return this.generateDocPopularityReport(period, filters);
      case 'team_collaboration':
        return this.generateTeamCollaborationReport(period, filters);
      case 'knowledge_gaps':
        return this.generateKnowledgeGapsReport(period, filters);
      default:
        throw new Error(`Unknown report type: ${type}`);
    }
  }

  private async generateUserActivityReport(
    period: { start: Date; end: Date },
    filters?: ReportFilters
  ): Promise<AnalyticsReport> {
    const events = await this.eventStore.getEvents({
      type: 'user_activity',
      start: period.start,
      end: period.end,
      project_id: filters?.project_id
    });
    
    // 聚合用户活动
    const userMetrics = this.aggregateUserMetrics(events);
    
    // 计算趋势
    const trend = this.computeTrend(userMetrics);
    
    // 生成洞察
    const insights = this.generateActivityInsights(userMetrics, trend);
    
    return {
      id: generateId(),
      type: 'user_activity',
      period,
      generated_at: new Date(),
      data: {
        summary: this.computeSummary(userMetrics),
        charts: [
          this.buildActivityTimeline(events),
          this.buildUserEngagementChart(userMetrics),
          this.buildSessionDurationChart(events)
        ],
        insights,
        recommendations: this.generateRecommendations(insights)
      }
    };
  }

  private aggregateUserMetrics(events: AnalyticsEvent[]): Map<string, UserActivityMetrics> {
    const metricsMap = new Map<string, UserActivityMetrics>();
    
    for (const event of events) {
      if (!metricsMap.has(event.user_id)) {
        metricsMap.set(event.user_id, {
          user_id: event.user_id,
          period: { start: event.timestamp, end: event.timestamp },
          metrics: { sessions: 0, total_time: 0, docs_viewed: 0, docs_edited: 0, comments_made: 0, searches: 0 },
          activity_timeline: []
        });
      }
      
      const metrics = metricsMap.get(event.user_id)!;
      
      switch (event.event_type) {
        case 'session_start':
          metrics.metrics.sessions++;
          break;
        case 'doc_view':
          metrics.metrics.docs_viewed++;
          break;
        case 'doc_edit':
          metrics.metrics.docs_edited++;
          break;
        case 'comment':
          metrics.metrics.comments_made++;
          break;
        case 'search':
          metrics.metrics.searches++;
          break;
      }
      
      metrics.activity_timeline.push(event);
    }
    
    return metricsMap;
  }

  private computeTrend(metrics: Map<string, UserActivityMetrics>): TrendData {
    const sortedMetrics = Array.from(metrics.values())
      .sort((a, b) => a.period.start.getTime() - b.period.start.getTime());
    
    // 计算移动平均
    const windowSize = 7;
    const movingAvg = sortedMetrics.map((m, i) => {
      const window = sortedMetrics.slice(Math.max(0, i - windowSize + 1), i + 1);
      const avgMetrics = {
        sessions: window.reduce((s, m) => s + m.metrics.sessions, 0) / window.length,
        docs_viewed: window.reduce((s, m) => s + m.metrics.docs_viewed, 0) / window.length
      };
      return { timestamp: m.period.start, ...avgMetrics };
    });
    
    return { data: movingAvg, direction: this.detectTrendDirection(movingAvg) };
  }

  private generateActivityInsights(
    metrics: Map<string, UserActivityMetrics>,
    trend: TrendData
  ): Insight[] {
    const insights: Insight[] = [];
    
    // 检测异常
    const outlierUsers = this.detectOutliers(metrics);
    if (outlierUsers.length > 0) {
      insights.push({
        type: 'anomaly',
        title: '异常用户活动检测',
        description: `${outlierUsers.length} 位用户活动量显著偏离正常范围`,
        severity: 'warning',
        related_metrics: ['sessions', 'docs_viewed']
      });
    }
    
    // 检测趋势变化
    if (trend.direction === 'declining') {
      insights.push({
        type: 'trend',
        title: '用户活跃度下降',
        description: '过去7天用户活跃度呈下降趋势',
        severity: 'warning',
        related_metrics: ['sessions', 'docs_viewed']
      });
    }
    
    return insights;
  }
}
```

### 4.3 分析 API

```typescript
// api/routes/analytics.ts
const router = Router();

/**
 * GET /api/analytics/report
 * 生成分析报告
 */
router.get('/report', async (req, res) => {
  const { type, start_date, end_date, project_id } = req.query;
  
  const report = await analyticsEngine.generateReport(
    type as ReportType,
    { start: new Date(start_date), end: new Date(end_date) },
    { project_id }
  );
  
  res.json({ success: true, data: report });
});

/**
 * GET /api/analytics/dashboard
 * 获取仪表盘数据
 */
router.get('/dashboard', async (req, res) => {
  const { project_id } = req.query;
  
  const [
    summary,
    trendingDocs,
    activeUsers,
    collaborationGraph
  ] = await Promise.all([
    analyticsEngine.getSummary({ project_id, period: '7d' }),
    analyticsEngine.getTrendingDocs({ project_id, limit: 10 }),
    analyticsEngine.getActiveUsers({ project_id, limit: 10 }),
    analyticsEngine.getCollaborationGraph({ project_id })
  ]);
  
  res.json({ success: true, data: { summary, trendingDocs, activeUsers, collaborationGraph } });
});

/**
 * GET /api/analytics/export
 * 导出分析数据
 */
router.get('/export', async (req, res) => {
  const { type, format, start_date, end_date } = req.query;
  
  const data = await analyticsEngine.exportData({
    type: type as ReportType,
    start: new Date(start_date),
    end: new Date(end_date)
  });
  
  if (format === 'csv') {
    const csv = this.toCSV(data);
    res.setHeader('Content-Type', 'text/csv');
    res.send(csv);
  } else {
    res.json({ success: true, data });
  }
});
```

---

## ✅ 五、多语言支持完善

### 5.1 i18n 架构

```typescript
// types/i18n.ts
export interface LocaleConfig {
  code: LocaleCode;
  name: string;
  nativeName: string;
  direction: 'ltr' | 'rtl';
  dateFormat: string;
  timeFormat: string;
  numberFormat: NumberFormatConfig;
}

export type LocaleCode = 'zh-CN' | 'en-US' | 'ja-JP' | 'ko-KR' | 'es-ES' | 'fr-FR' | 'de-DE';

export interface NumberFormatConfig {
  decimal: string;
  thousands: string;
  precision: number;
}

export interface TranslationResource {
  locale: LocaleCode;
  namespace: string;
  translations: Record<string, string>;
  pluralRules?: (n: number) => string;
}

export interface I18nContext {
  locale: LocaleCode;
  translations: Map<string, Record<string, string>>;
  format: Formatter;
  dir: 'ltr' | 'rtl';
}

// hooks/useTranslation.ts
export function useTranslation(namespace?: string) {
  const context = useContext(I18nContext);
  
  const t = useCallback((key: string, params?: Record<string, string | number>): string => {
    const translation = context.translations.get(namespace || 'common')?.[key]
      || context.translations.get('common')?.[key]
      || key;
    
    if (params) {
      return Object.entries(params).reduce(
        (str, [k, v]) => str.replace(new RegExp(`{{${k}}}`, 'g'), String(v)),
        translation
      );
    }
    
    return translation;
  }, [context, namespace]);
  
  return { t, locale: context.locale, dir: context.dir };
}
```

### 5.2 翻译管理服务

```typescript
// services/i18n/TranslationService.ts
export class TranslationService {
  constructor(
    private translationStore: TranslationStore,
    private cache: Cache
  ) {}

  /**
   * 获取翻译
   */
  async getTranslations(locale: LocaleCode, namespace: string): Promise<Record<string, string>> {
    const cacheKey = `translations:${locale}:${namespace}`;
    const cached = await this.cache.get(cacheKey);
    if (cached) return cached;
    
    const translations = await this.translationStore.get(locale, namespace);
    await this.cache.set(cacheKey, translations, { ttl: 3600 });
    
    return translations;
  }

  /**
   * 机器翻译辅助（人工审核）
   */
  async translateWithAI(
    text: string,
    sourceLocale: LocaleCode,
    targetLocale: LocaleCode
  ): Promise<string> {
    const translated = await this.aiService.translate(text, {
      from: sourceLocale,
      to: targetLocale
    });
    
    // 记录待审核
    await this.translationStore.createPending({
      source: text,
      target: translated,
      source_locale: sourceLocale,
      target_locale: targetLocale,
      status: 'pending_review'
    });
    
    return translated;
  }

  /**
   * 批量翻译
   */
  async batchTranslate(
    entries: { key: string; value: string }[],
    sourceLocale: LocaleCode,
    targetLocale: LocaleCode
  ): Promise<Record<string, string>> {
    const results: Record<string, string> = {};
    
    // 批量提交
    const batches = this.batch(entries, 50);
    
    for (const batch of batches) {
      const translated = await this.aiService.batchTranslate(
        batch.map(e => e.value),
        { from: sourceLocale, to: targetLocale }
      );
      
      batch.forEach((entry, i) => {
        results[entry.key] = translated[i];
      });
    }
    
    return results;
  }

  private batch<T>(arr: T[], size: number): T[][] {
    const batches: T[][] = [];
    for (let i = 0; i < arr.length; i += size) {
      batches.push(arr.slice(i, i + size));
    }
    return batches;
  }
}
```

### 5.3 RTL 支持

```typescript
// styles/RTLProvider.tsx
export const RTLProvider: React.FC<{ children: React.ReactNode; locale: LocaleCode }> = ({
  children,
  locale
}) => {
  const dir = this.isRTL(locale) ? 'rtl' : 'ltr';
  
  return (
    <div dir={dir} lang={locale} className={classNames('locale-root', { rtl: dir === 'rtl' })}>
      <StyleProvider locale={locale}>
        {children}
      </StyleProvider>
    </div>
  );
};

// styles/rtl.scss
.locale-root.rtl {
  // 文本对齐
  text-align: right;
  
  // 边框和间距翻转
  .card {
    margin-left: 0;
    margin-right: 1rem;
    padding-left: 0;
    padding-right: 1rem;
    border-left: none;
    border-right: 3px solid primary;
  }
  
  // 图标位置翻转
  .icon-left {
    margin-right: 0;
    margin-left: 0.5rem;
  }
  
  .icon-right {
    margin-left: 0;
    margin-right: 0.5rem;
  }
  
  // Flex 布局方向
  .horizontal-layout {
    flex-direction: row-reverse;
  }
  
  // 列表顺序翻转
  .nav-list {
    padding-right: 0;
    padding-left: 1rem;
  }
}
```

### 5.4 多语言 API

```typescript
// api/routes/i18n.ts
const router = Router();

/**
 * GET /api/i18n/locales
 * 获取支持的语言列表
 */
router.get('/locales', (req, res) => {
  const locales = [
    { code: 'zh-CN', name: '简体中文', nativeName: '简体中文', direction: 'ltr' },
    { code: 'en-US', name: 'English', nativeName: 'English', direction: 'ltr' },
    { code: 'ja-JP', name: '日本語', nativeName: '日本語', direction: 'ltr' },
    { code: 'ko-KR', name: '한국어', nativeName: '한국어', direction: 'ltr' },
    { code: 'es-ES', name: 'Español', nativeName: 'Español', direction: 'ltr' },
    { code: 'ar-SA', name: 'Arabic', nativeName: 'العربية', direction: 'rtl' },
    { code: 'he-IL', name: 'Hebrew', nativeName: 'עברית', direction: 'rtl' }
  ];
  
  res.json({ success: true, data: locales });
});

/**
 * GET /api/i18n/:locale/:namespace
 * 获取翻译资源
 */
router.get('/:locale/:namespace', async (req, res) => {
  const { locale, namespace } = req.params;
  
  const translations = await translationService.getTranslations(
    locale as LocaleCode,
    namespace
  );
  
  res.json({ success: true, data: translations });
});

/**
 * PUT /api/i18n/:locale/:namespace
 * 更新翻译
 */
router.put('/:locale/:namespace', async (req, res) => {
  const { locale, namespace } = req.params;
  const { key, value } = req.body;
  
  await translationService.updateTranslation(locale, namespace, key, value);
  res.json({ success: true });
});

/**
 * POST /api/i18n/ai-translate
 * AI 辅助翻译
 */
router.post('/ai-translate', async (req, res) => {
  const { text, source_locale, target_locale } = req.body;
  
  const translated = await translationService.translateWithAI(
    text,
    source_locale,
    target_locale
  );
  
  res.json({ success: true, data: { translated } });
});
```

---

## 📊 v3.0.14 交付清单

| 模块 | 功能点 | 状态 |
|------|--------|------|
| **智能推荐** | 推荐引擎（混合算法） | ⬜ |
| | 用户画像系统 | ⬜ |
| | 推荐 API | ⬜ |
| | 推荐反馈机制 | ⬜ |
| **版本对比** | 语义级 Diff 引擎 | ⬜ |
| | 版本历史管理 | ⬜ |
| | 版本对比 UI | ⬜ |
| | 版本恢复 | ⬜ |
| **自动化工作流** | 工作流定义模型 | ⬜ |
| | 工作流引擎 | ⬜ |
| | 步骤执行器 | ⬜ |
| | 工作流可视化编辑器 | ⬜ |
| **分析报告** | 分析指标体系 | ⬜ |
| | 报告生成引擎 | ⬜ |
| | 仪表盘 UI | ⬜ |
| | 数据导出 | ⬜ |
| **多语言** | i18n 架构 | ⬜ |
| | RTL 支持 | ⬜ |
| | 翻译管理 | ⬜ |
| | 实时语言切换 | ⬜ |
