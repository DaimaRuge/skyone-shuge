# 天一阁 PRD v3.0.22

> **版本**: v3.0.22  
> **日期**: 2026-04-15  
> **主题**: 智能运维 + 自愈架构 + 预测性维护  
> **迭代周期**: 每日连续迭代

---

## 版本概述

本次迭代 (v3.0.22) 在 v3.0.21 知识图谱与语义缓存基础上，引入**智能运维体系**，重点解决：

1. **AIOps 自动化**: 异常检测、根因分析、故障自愈
2. **预测性维护**: 容量预测、健康度评估、主动干预
3. **自愈架构**: 故障隔离、自动恢复、降级策略
4. **智能调度**: 动态资源分配、成本优化、负载均衡

---

## 目录

- [1. 智能运维体系](#1-智能运维体系)
- [2. AIOps 自动化架构](#2-aiops-自动化架构)
- [3. 预测性维护引擎](#3-预测性维护引擎)
- [4. 自愈架构设计](#4-自愈架构设计)
- [5. 智能资源调度](#5-智能资源调度)
- [6. 技术实现细节](#6-技术实现细节)
- [7. PRD Checkpoint](#7-prd-checkpoint)

---

## 1. 智能运维体系

### 1.1 概述

智能运维 (AIOps) 将 AI 能力融入运维全流程，实现从被动响应到主动预防的转变。

### 1.2 核心目标

| 指标 | 传统运维 | 智能运维 v3.0.22 |
|------|----------|-----------------|
| MTTR (平均恢复时间) | 30-60 分钟 | < 5 分钟 |
| 故障预测准确率 | N/A | > 85% |
| 主动干预覆盖率 | 0% | > 80% |
| 资源利用率 | 30-40% | 60-70% |
| 运维成本 | 基准 | -40% |

### 1.3 监控指标体系

```
四层监控指标:
├── 基础设施层
│   ├── CPU / 内存 / 磁盘 I/O
│   ├── 网络吞吐 / 连接数
│   └── 容器健康 / Pod 调度
│
├── 应用服务层
│   ├── API 响应时间 / QPS
│   ├── 错误率 / 超时率
│   ├── 向量检索延迟
│   └── LLM 调用成功率
│
├── 业务逻辑层
│   ├── 文档处理吞吐量
│   ├── 用户活跃度 / 会话数
│   ├── 知识图谱查询 QPS
│   └── 缓存命中率
│
└── AI 模型层
    ├── 模型推理延迟
    ├── Token 消耗速率
    ├── Embedding 质量指标
    └── RAG 准确率 / 相关性
```

---

## 2. AIOps 自动化架构

### 2.1 异常检测引擎

```python
class AnomalyDetector:
    """多维度异常检测引擎"""
    
    def __init__(self, metrics_store: MetricsStore):
        self.metrics = metrics_store
        self.models = {
            "statistical": StatisticalDetector(),
            "ml": MLAnomalyDetector(),
            "deep_learning": LSTMDetector()
        }
        self.baselines = {}
    
    async def detect(self, metric_name: str, value: float, 
                     timestamp: datetime) -> AnomalyResult:
        """
        多模型融合异常检测
        
        策略:
        1. 统计检测 (Z-score / IQR) - 快速过滤
        2. ML 检测 (Isolation Forest) - 捕捉复杂模式
        3. 时序检测 (LSTM) - 考虑时间依赖
        4. 融合判决 - 加权投票
        """
        
        # 并行多模型检测
        results = await asyncio.gather(
            self.models["statistical"].detect(value, self.baselines[metric_name]),
            self.models["ml"].predict(metric_name, value),
            self.models["deep_learning"].forecast(metric_name, timestamp)
        )
        
        # 加权融合
        scores = [r.anomaly_score for r in results]
        weights = [0.3, 0.3, 0.4]  # 统计/ML/深度学习
        
        fused_score = sum(s * w for s, w in zip(scores, weights))
        
        return AnomalyResult(
            metric=metric_name,
            value=value,
            fused_score=fused_score,
            is_anomaly=fused_score > 0.7,
            confidence=1 - (max(scores) - min(scores)),  # 一致性置信度
            models_triggered=[r for r, s in zip(results, scores) if s > 0.5]
        )
```

### 2.2 根因分析 (RCA) 引擎

```python
class RootCauseAnalyzer:
    """基于知识图谱的根因分析"""
    
    def __init__(self, knowledge_graph: KnowledgeGraph,
                 trace_store: TraceStore):
        self.kg = knowledge_graph
        self.traces = trace_store
    
    async def analyze(self, anomaly: AnomalyResult) -> RCAReport:
        """
        根因分析流程:
        
        1. 故障传播图构建
           - 从异常指标出发
           - 沿服务依赖关系逆向追溯
           - 标记可能的故障传播路径
        
        2. 时序相关性分析
           - 找到异常前后的关键事件
           - 计算时间窗口内的因果强度
        
        3. 知识推理
           - 利用知识图谱中的故障模式
           - 匹配历史相似案例
        
        4. 根因排序
           - 综合多维度打分
           - 返回 Top-K 可能根因
        """
        
        # Step 1: 获取依赖图
        dependency_graph = await self.kg.get_dependency_graph(
            anomaly.metric
        )
        
        # Step 2: 故障传播分析
        propagation_paths = self._analyze_propagation(
            dependency_graph, anomaly
        )
        
        # Step 3: 时序分析
        time_window = timedelta(minutes=10)
        related_events = await self.traces.query(
            start_time=anomaly.timestamp - time_window,
            end_time=anomaly.timestamp,
            service=anomaly.affected_service
        )
        
        # Step 4: 根因推理
        candidate_causes = []
        for path in propagation_paths:
            cause_score = await self._calculate_cause_score(
                path, related_events, anomaly
            )
            candidate_causes.append((path, cause_score))
        
        # 排序返回
        candidate_causes.sort(key=lambda x: x[1], reverse=True)
        
        return RCAReport(
            primary_cause=candidate_causes[0][0],
            alternative_causes=candidate_causes[1:4],
            evidence=[e.description for e in related_events],
            recommended_actions=self._get_remediation_actions(
                candidate_causes[0][0]
            ),
            confidence=candidate_causes[0][1]
        )
```

### 2.3 自动修复工作流

```python
class AutoRemediationEngine:
    """自动修复执行引擎"""
    
    def __init__(self, workflow_engine: WorkflowEngine,
                 action_registry: ActionRegistry):
        self.workflow = workflow_engine
        self.actions = action_registry
    
    async def remediate(self, rca_report: RCAReport) -> RemediationResult:
        """
        自动修复流程:
        
        1. 验证修复条件
           - 检查前置依赖
           - 评估影响范围
           - 确认回滚计划
        
        2. 执行修复策略
           - 遵循最小影响原则
           - 渐进式执行
           - 实时监控效果
        
        3. 回滚保护
           - 设置检查点
           - 超时自动回滚
           - 失败人工介入
        """
        
        # 获取匹配的修复策略
        strategy = self.actions.get_strategy(rca_report.primary_cause)
        
        if not strategy:
            return RemediationResult(
                status="manual_required",
                message="未找到匹配自动修复策略，需要人工处理"
            )
        
        # 执行前检查
        pre_check = await strategy.pre_check(rca_report)
        if not pre_check.passed:
            return RemediationResult(
                status="precheck_failed",
                message=f"前置检查失败: {pre_check.reason}",
                suggested_action=pre_check.suggested_action
            )
        
        # 执行修复
        try:
            execution = await self.workflow.execute(
                strategy.as_workflow(),
                context={
                    "rca": rca_report,
                    "rollback_timeout": 300  # 5分钟
                }
            )
            
            # 验证效果
            if await self._verify_fix(execution):
                return RemediationResult(
                    status="resolved",
                    execution_id=execution.id,
                    resolved_in=execution.duration
                )
            else:
                # 触发回滚
                await execution.rollback()
                return RemediationResult(
                    status="rollback_triggered",
                    message="修复效果验证失败，已自动回滚"
                )
                
        except Exception as e:
            return RemediationResult(
                status="failed",
                message=f"修复执行异常: {str(e)}",
                escalation="oncall_engineer"
            )
```

---

## 3. 预测性维护引擎

### 3.1 容量预测模型

```python
class CapacityPredictor:
    """基于时序预测的容量规划"""
    
    def __init__(self, model_store: ModelStore):
        self.prophet = ProphetPredictor()
        self.arima = ARIMAPredictor()
        self.ensemble = EnsemblePredictor()
    
    async def predict_demand(self, service: str, 
                              horizon_hours: int = 72) -> DemandForecast:
        """
        多模型融合需求预测
        
        方法:
        - Prophet: 捕捉周期性和趋势
        - ARIMA: 处理非平稳时间序列
        - 集成学习: 综合多模型优势
        """
        
        historical_data = await self._get_historical_metrics(
            service, days=30
        )
        
        # 多模型并行预测
        forecasts = await asyncio.gather(
            self.prophet.forecast(historical_data, horizon_hours),
            self.arima.forecast(historical_data, horizon_hours),
            self.ensemble.forecast(historical_data, horizon_hours)
        )
        
        # 加权集成
        final_forecast = self._weighted_ensemble(forecasts)
        
        return DemandForecast(
            service=service,
            predictions=final_forecast,
            confidence_interval=self._calculate_confidence(forecasts),
            peak_window=self._identify_peak_hours(final_forecast),
            recommended_capacity=self._calculate_recommended_capacity(
                final_forecast
            )
        )
    
    def _calculate_recommended_capacity(self, forecast: pd.DataFrame) -> dict:
        """计算推荐容量（考虑峰值 + 安全裕度）"""
        peak_qps = forecast["yhat"].max()
        safety_margin = 1.3  # 30% 安全裕度
        
        return {
            "current_replicas": forecast.get("current_replicas", 1),
            "recommended_replicas": int(peak_qps * safety_margin / 100) + 1,
            "scale_up_threshold": int(peak_qps * 0.7 / 100) + 1,
            "scale_down_threshold": int(peak_qps * 0.3 / 100) + 1,
            "estimated_monthly_cost": int(peak_qps * safety_margin * 0.02)  # 粗略估算
        }
```

### 3.2 健康度评估系统

```python
class HealthEvaluator:
    """多维度服务健康度评估"""
    
    def __init__(self, metrics_store: MetricsStore):
        self.metrics = metrics_store
        self.weights = {
            "availability": 0.25,
            "latency": 0.25,
            "error_rate": 0.20,
            "throughput": 0.15,
            "resource_util": 0.15
        }
    
    async def evaluate(self, service: str) -> HealthScore:
        """
        综合健康度评分 (0-100)
        
        维度:
        - 可用性 (25%): SLA 达成率
        - 延迟 (25%): P99 响应时间
        - 错误率 (20%): 5xx + 超时比例
        - 吞吐 (15%): 实际 QPS / 目标 QPS
        - 资源利用率 (15%): 偏离最佳区间程度
        """
        
        scores = {}
        
        # 各维度评分
        scores["availability"] = await self._calc_availability_score(service)
        scores["latency"] = await self._calc_latency_score(service)
        scores["error_rate"] = await self._calc_error_score(service)
        scores["throughput"] = await self._calc_throughput_score(service)
        scores["resource_util"] = await self._calc_resource_score(service)
        
        # 加权总分
        total_score = sum(
            scores[k] * self.weights[k] 
            for k in self.weights
        )
        
        return HealthScore(
            service=service,
            overall=total_score,
            dimensions=scores,
            grade=self._score_to_grade(total_score),
            recommendations=self._generate_recommendations(scores),
            trend=self._calculate_trend(service)  # 周环比
        )
    
    def _score_to_grade(self, score: float) -> str:
        if score >= 95: return "A+"
        elif score >= 90: return "A"
        elif score >= 80: return "B"
        elif score >= 70: return "C"
        elif score >= 60: return "D"
        else: return "F"
```

---

## 4. 自愈架构设计

### 4.1 故障隔离策略

```python
class CircuitBreaker:
    """熔断器实现 - 防止故障扩散"""
    
    def __init__(self, name: str,
                 failure_threshold: float = 0.5,
                 recovery_timeout: int = 60,
                 half_open_max_calls: int = 3):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = "closed"  # closed / open / half_open
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
    
    async def call(self, func: Callable, *args, **kwargs):
        """
        熔断器调用流程:
        
        CLOSED (正常):
        - 执行请求
        - 失败 count++
        - 失败率 > 阈值 → OPEN
        - 成功 count++，连续成功 → 重置
        
        OPEN (熔断):
        - 快速失败 (抛出 CircuitOpenException)
        - 超时后 → HALF_OPEN
        
        HALF_OPEN (试探):
        - 允许 limited 数量的探测请求
        - 成功 → CLOSED
        - 失败 → OPEN
        """
        
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
                self.success_count = 0
            else:
                raise CircuitOpenException(
                    f"Circuit {self.name} is OPEN"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failure_count = 0
        self.success_count += 1
        
        if self.state == "half_open":
            if self.success_count >= self.half_open_max_calls:
                self.state = "closed"
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        failure_rate = self.failure_count / (
            self.failure_count + self.success_count + 1
        )
        
        if failure_rate > self.failure_threshold:
            self.state = "open"
```

### 4.2 自动伸缩策略

```yaml
# Kubernetes HPA 配置 - 智能伸缩
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: skyone-shuge-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: skyone-shuge-api
  minReplicas: 2
  maxReplicas: 20
  
  metrics:
    # CPU 自动伸缩
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
    
    # 内存自动伸缩
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 70
    
    # 自定义 QPS 伸缩
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "100"
    
    # 基于预测的预伸缩 (v3.0.22 新增)
    - type: External
      external:
        metric:
          name: predicted_demand
          selector:
            matchLabels:
              service: skyone-api
        target:
          type: AverageValue
          averageValue: "150"  # 预测值触发
```

### 4.3 降级策略分级

```python
class DegradationManager:
    """服务降级管理器 - 保障核心功能"""
    
    # 降级级别定义
    DEGRADATION_LEVELS = {
        0: {  # 正常
            "name": "full_functionality",
            "features": ["kg_query", "semantic_cache", "personalization", 
                       "cross_doc_discovery", "advanced_rag"]
        },
        1: {  # 轻度降级
            "name": "reduced_features",
            "disabled": ["cross_doc_discovery"],  # 关闭跨文档发现
            "cache_ttl": 3600,  # 缓存延长至1小时
            "max_context_length": 4096,  # 缩短上下文
        },
        2: {  # 中度降级
            "name": "core_only",
            "disabled": ["kg_query", "cross_doc_discovery", 
                        "advanced_rag", "personalization"],
            "fallback_rag": "simple_keyword_match",
            "max_documents": 5,
        },
        3: {  # 紧急降级
            "name": "emergency",
            "disabled": ["llm_response", "kg_query", "advanced_rag"],
            "fallback": "static_response",
            "message": "系统繁忙，请稍后再试"
        }
    }
    
    async def should_degrade(self) -> int:
        """评估当前应处于哪个降级级别"""
        
        metrics = await self._collect_current_metrics()
        
        # 评估各指标
        health_score = await self._get_health_score()
        queue_depth = metrics.queue_depth
        error_rate = metrics.error_rate
        active_connections = metrics.active_connections
        
        # 决策逻辑
        if health_score < 50 or error_rate > 0.2:
            return 3
        elif health_score < 70 or queue_depth > 1000:
            return 2
        elif health_score < 85 or queue_depth > 500:
            return 1
        else:
            return 0
```

---

## 5. 智能资源调度

### 5.1 成本感知调度

```python
class CostAwareScheduler:
    """成本感知调度器 - 平衡性能和成本"""
    
    def __init__(self, cost_calculator: CostCalculator,
                 resource_manager: ResourceManager):
        self.cost = cost_calculator
        self.resources = resource_manager
    
    async def schedule(self, task: AITask) -> ScheduleDecision:
        """
        智能任务调度决策
        
        考虑因素:
        1. 任务优先级 (SLA 等级)
        2. 延迟敏感性 (同步/异步)
        3. 成本预算 (按需/预留)
        4. 当前负载 (空闲/繁忙)
        5. 模型适用性 (小模型/大模型)
        """
        
        # 获取可用选项
        options = await self._get_routing_options(task)
        
        # 多目标优化
        decisions = []
        for opt in options:
            score = self._calculate_score(
                task=task,
                option=opt,
                latency_weight=0.4 if task.latency_sensitive else 0.1,
                cost_weight=0.3 if task.budget_constrained else 0.1,
                quality_weight=0.3 if task.quality_required else 0.1
            )
            decisions.append((opt, score))
        
        decisions.sort(key=lambda x: x[1], reverse=True)
        
        return ScheduleDecision(
            selected_option=decisions[0][0],
            alternatives=decisions[1:3],
            estimated_latency=decisions[0][0].latency,
            estimated_cost=decisions[0][0].cost,
            reasoning=self._explain_decision(decisions[0])
        )
    
    def _calculate_score(self, task, option, 
                         latency_weight, cost_weight, quality_weight) -> float:
        latency_score = 1 - min(option.latency / task.max_latency, 1.0)
        cost_score = 1 - min(option.cost / task.max_cost, 1.0) if task.max_cost else 1.0
        quality_score = option.quality_score if task.quality_required else 1.0
        
        return (latency_score * latency_weight + 
                cost_score * cost_weight + 
                quality_score * quality_weight)
```

---

## 6. 技术实现细节

### 6.1 关键技术选型

| 模块 | 技术选型 | 说明 |
|------|----------|------|
| 指标采集 | Prometheus + OpenTelemetry | 云原生监控事实标准 |
| 日志分析 | Loki + Promtail | 与 Prometheus 统一生态 |
| 链路追踪 | Jaeger / Tempo | 分布式追踪 |
| 告警管理 | AlertManager + PagerDuty | 告警聚合与升级 |
| 时序预测 | Prophet + ARIMA | 成熟的时间序列预测 |
| 异常检测 | Isolation Forest + LSTM | 统计+机器学习融合 |
| 自动化修复 | Temporal / Prefect | 工作流编排引擎 |
| 配置管理 | Consul / etcd | 动态配置中心 |

### 6.2 部署架构

```
智能运维组件部署:

┌─────────────────────────────────────────────────────────────┐
│                    运维管理集群 (独立)                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Prometheus  │  │ AlertManager │  │   Grafana   │        │
│  │  (采集+存储) │  │   (告警)     │  │  (可视化)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Loki/Promtail│ │  Tempo       │  │  PagerDuty  │        │
│  │  (日志)      │  │  (追踪)      │  │  (告警升级)  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │            AIOps 平台 (自研)                      │       │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐     │       │
│  │  │ 异常检测器 │ │ RCA 引擎  │ │ 自愈执行器 │     │       │
│  │  └───────────┘ └───────────┘ └───────────┘     │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. PRD Checkpoint

### 7.1 功能清单

| 功能 | 优先级 | 状态 |
|------|--------|------|
| 多维度异常检测 | P0 | 待实现 |
| 根因分析 (RCA) | P0 | 待实现 |
| 自动故障恢复 | P0 | 待实现 |
| 熔断器策略 | P0 | 待实现 |
| 智能容量预测 | P1 | 待实现 |
| 健康度评估 | P1 | 待实现 |
| 多级降级策略 | P1 | 待实现 |
| 成本感知调度 | P2 | 待实现 |
| 预测性伸缩 | P2 | 待实现 |

### 7.2 依赖关系

```
v3.0.22 依赖:
├── v3.0.20 (多模态 RAG / 检索增强)
│   └── v3.0.19 (安全 / 高可用)
│       └── v3.0.18 (监控 / 压测 / 部署)
└── 无新增外部依赖
```

### 7.3 预估工时

| 模块 | 人天 |
|------|------|
| AIOps 异常检测 + RCA | 5 |
| 自愈执行引擎 | 3 |
| 预测性维护模块 | 4 |
| 降级 + 熔断策略 | 2 |
| 智能调度器 | 3 |
| 测试 + 集成 | 3 |
| **合计** | **20** |
