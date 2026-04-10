# 天一阁 PRD v3.0.17

**版本**: v3.0.17
**日期**: 2026-04-08
**阶段**: 监控/限流/缓存 API 实现 + 前后端联调 + 端到端测试

---

## 📋 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0.17 | 2026-04-08 | 监控/限流/缓存 API 实现 + 前后端联调 + 端到端测试 |
| v3.0.16 | 2026-04-05 | 实现代码开发 + 前端 UI 组件开发 + 单元测试与集成测试 |
| v3.0.15 | 2026-04-04 | 监控与可观测性架构 + API 限流与成本控制架构 + 多级缓存架构 + 性能优化架构 + 高级搜索增强架构 + LLM 成本追踪与预算控制 |
| v3.0.14 | 2026-04-03 | 智能推荐系统架构 + 文档版本对比架构 + 自动化工作流架构 + 高级分析报告架构 + 多语言支持架构 |

---

## 🎯 本次迭代目标

### 核心交付物
- [ ] **监控后端 API 端点**: Prometheus metrics API、OpenTelemetry traces API、监控仪表盘数据 API
- [ ] **限流后端 API 端点**: 限流状态查询、配额管理、限流规则 CRUD
- [ ] **缓存管理后端 API**: 缓存状态查询、缓存清理、缓存预热
- [ ] **前后端联调**: API 端点对接、前端组件调试、数据流连通性测试
- [ ] **端到端测试**: 用户流程 E2E 测试、API 集成测试、WebSocket 联接测试

---

## ✅ 一、监控后端 API 端点实现

### 1.1 Prometheus Metrics API

#### 1.1.1 基础 Metrics 端点

```python
# src/skyone_shuge/api/v1/metrics.py
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from src.skyone_shuge.monitoring.metrics import metrics_collector

router = APIRouter(prefix="/metrics", tags=["监控指标"])


@router.get("", response_class=Response)
async def get_metrics():
    """
    获取 Prometheus 格式指标
    GET /metrics
    
    Returns:
        Prometheus 格式指标数据
    """
    return Response(
        content=metrics_collector.get_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/summary")
async def get_metrics_summary():
    """
    获取指标摘要（JSON 格式）
    GET /metrics/summary
    
    Returns:
        {
            "http_requests_total": {...},
            "llm_requests_total": {...},
            "cache_hits_total": {...},
            ...
        }
    """
    from prometheus_client import REGISTRY
    from collections import defaultdict
    
    summary = defaultdict(dict)
    
    for collector in REGISTRY._names_to_collectors.values():
        if hasattr(collector, '_metrics'):
            for name, metric in collector._metrics.items():
                metric_name = name
                
                if hasattr(metric, '_metrics'):
                    for suffix, metric_type in metric._metrics.items():
                        full_name = f"{metric_name}_{suffix}"
                        try:
                            # 获取当前值
                            if hasattr(metric_type, '_value'):
                                summary[metric_name][suffix] = {
                                    'type': metric_type.__class__.__name__,
                                    'value': metric_type._value.get()
                                }
                        except Exception:
                            pass
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": dict(summary)
    }


@router.get("/health")
async def get_monitoring_health():
    """
    获取监控子系统健康状态
    GET /metrics/health
    """
    return {
        "status": "healthy",
        "components": {
            "prometheus_client": "up",
            "metrics_collector": "up"
        }
    }
```

#### 1.1.2 监控仪表盘数据 API

```python
# src/skyone_shuge/api/v1/dashboard.py
from fastapi import APIRouter, Query
from typing import Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

router = APIRouter(prefix="/dashboard", tags=["监控仪表盘"])


@dataclass
class TimeSeriesPoint:
    timestamp: str
    value: float


@dataclass
class DashboardMetrics:
    """仪表盘指标数据"""
    metric_name: str
    current_value: float
    previous_value: float
    change_percent: float
    trend: str  # up, down, stable
    timeseries: List[TimeSeriesPoint]


@router.get("/overview")
async def get_dashboard_overview(
    period: str = Query("1h", description="时间范围: 1h, 6h, 24h, 7d")
) -> dict:
    """
    获取仪表盘概览数据
    GET /dashboard/overview?period=1h
    
    Returns:
        {
            "http_requests": {...},
            "llm_usage": {...},
            "cache_performance": {...},
            "error_rate": {...}
        }
    """
    # 根据时间范围计算时间点
    period_map = {
        "1h": (60, 1),    # 60个点，每点1分钟
        "6h": (72, 5),    # 72个点，每点5分钟
        "24h": (96, 15),  # 96个点，每点15分钟
        "7d": (168, 60)   # 168个点，每点1小时
    }
    
    points, interval_minutes = period_map.get(period, (60, 1))
    
    # 获取 HTTP 请求概览
    http_requests = await _get_http_requests_summary(points, interval_minutes)
    
    # 获取 LLM 使用概览
    llm_usage = await _get_llm_usage_summary(points, interval_minutes)
    
    # 获取缓存性能
    cache_perf = await _get_cache_performance_summary(points, interval_minutes)
    
    # 获取错误率
    error_rate = await _get_error_rate_summary(points, interval_minutes)
    
    return {
        "period": period,
        "generated_at": datetime.utcnow().isoformat(),
        "http_requests": http_requests,
        "llm_usage": llm_usage,
        "cache_performance": cache_perf,
        "error_rate": error_rate
    }


@router.get("/http-requests")
async def get_http_requests_dashboard(
    period: str = Query("1h"),
    service: Optional[str] = None
) -> dict:
    """
    获取 HTTP 请求仪表盘数据
    """
    return {
        "total_requests": await _get_total_http_requests(period),
        "requests_by_status": await _get_http_requests_by_status(period, service),
        "requests_by_endpoint": await _get_http_requests_by_endpoint(period, service),
        "latency_percentiles": await _get_http_latency_percentiles(period, service),
        "requests_timeline": await _get_http_requests_timeline(period)
    }


@router.get("/llm-usage")
async def get_llm_usage_dashboard(
    period: str = Query("1h")
) -> dict:
    """
    获取 LLM 使用仪表盘数据
    """
    return {
        "total_tokens": await _get_total_tokens(period),
        "tokens_by_provider": await _get_tokens_by_provider(period),
        "tokens_by_model": await _get_tokens_by_model(period),
        "cost_summary": await _get_cost_summary(period),
        "latency_percentiles": await _get_llm_latency_percentiles(period),
        "usage_timeline": await _get_llm_usage_timeline(period)
    }


@router.get("/cache-dashboard")
async def get_cache_dashboard() -> dict:
    """
    获取缓存仪表盘数据
    """
    return {
        "memory_cache": await _get_memory_cache_stats(),
        "redis_cache": await _get_redis_cache_stats(),
        "hit_ratio_trend": await _get_cache_hit_ratio_trend(),
        "top_keys": await _get_top_cache_keys()
    }
```

---

### 1.2 OpenTelemetry Traces API

#### 1.2.1 Trace 查询端点

```python
# src/skyone_shuge/api/v1/traces.py
from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter(prefix="/traces", tags=["链路追踪"])


class Span(BaseModel):
    spanId: str
    parentSpanId: Optional[str]
    traceId: str
    operationName: str
    serviceName: str
    duration: float  # milliseconds
    startTime: int  # Unix timestamp in nanoseconds
    endTime: int
    status: str  # ok, error
    tags: dict
    logs: list


class Trace(BaseModel):
    traceId: str
    spans: List[Span]
    totalSpans: int
    duration: float  # total duration in ms
    startTime: int
    endTime: int


@router.get("/{trace_id}", response_model=Trace)
async def get_trace(
    trace_id: str = Path(..., description="Trace ID")
):
    """
    获取指定 Trace 的完整信息
    GET /traces/{trace_id}
    
    Returns:
        Trace 对象，包含所有 spans
    """
    from src.skyone_shuge.monitoring.tracing import tracing_manager
    
    with tracing_manager.create_span("api.get_trace") as span:
        span.set_attribute("trace_id", trace_id)
        
        # 从 Jaeger/OTLP 后端获取 trace
        trace_data = await _fetch_trace_from_backend(trace_id)
        
        if not trace_data:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        return trace_data


@router.get("/list/traces")
async def list_traces(
    service: Optional[str] = Query(None, description="服务名称"),
    operation: Optional[str] = Query(None, description="操作名称"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量")
) -> dict:
    """
    查询 Trace 列表
    GET /traces/list?service=api&limit=100&offset=0
    
    Returns:
        {
            "traces": [...],
            "total": 1234,
            "limit": 100,
            "offset": 0
        }
    """
    # 设置默认时间范围
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=1)
    
    traces = await _query_traces_from_backend(
        service=service,
        operation=operation,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset
    )
    
    total = await _count_traces_from_backend(
        service=service,
        operation=operation,
        start_time=start_time,
        end_time=end_time
    )
    
    return {
        "traces": traces,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/services")
async def list_services() -> dict:
    """
    获取所有服务列表
    GET /traces/services
    """
    services = await _get_service_list_from_backend()
    
    return {
        "services": [
            {
                "name": s["name"],
                "spans_count": s.get("spans_count", 0),
                "error_rate": s.get("error_rate", 0.0),
                "p99_latency": s.get("p99_latency", 0.0)
            }
            for s in services
        ]
    }


@router.get("/dependencies")
async def get_service_dependencies() -> dict:
    """
    获取服务依赖关系图
    GET /traces/dependencies
    """
    dependencies = await _get_dependency_graph_from_backend()
    
    return {
        "nodes": dependencies["nodes"],
        "edges": dependencies["edges"]
    }
```

---

### 1.3 日志查询 API

```python
# src/skyone_shuge/api/v1/logs.py
from fastapi import APIRouter, Query
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter(prefix="/logs", tags=["日志查询"])


class LogEntry(BaseModel):
    timestamp: str
    level: str  # INFO, WARNING, ERROR
    message: str
    service: str
    trace_id: Optional[str]
    span_id: Optional[str]
    fields: dict


@router.get("")
async def query_logs(
    query: Optional[str] = Query(None, description="查询表达式"),
    level: Optional[str] = Query(None, description="日志级别"),
    service: Optional[str] = Query(None, description="服务名称"),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> dict:
    """
    查询日志
    GET /logs?query=level:ERROR&service=api&limit=100
    """
    # 设置默认时间范围
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=1)
    
    logs = await _query_logs_from_loki(
        query=query,
        level=level,
        service=service,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset
    )
    
    total = await _count_logs_from_loki(
        query=query,
        level=level,
        service=service,
        start_time=start_time,
        end_time=end_time
    )
    
    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/aggregations")
async def get_log_aggregations(
    field: str = Query(..., description="聚合字段"),
    query: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None)
) -> dict:
    """
    获取日志聚合统计
    GET /logs/aggregations?field=level&query=service:api
    """
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=1)
    
    aggregations = await _get_log_aggregations_from_loki(
        field=field,
        query=query,
        start_time=start_time,
        end_time=end_time
    )
    
    return {
        "field": field,
        "aggregations": aggregations
    }
```

---

## ✅ 二、限流后端 API 端点实现

### 2.1 限流状态查询 API

```python
# src/skyone_shuge/api/v1/rate_limit.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/rate-limit", tags=["限流管理"])


class RateLimitStatus(BaseModel):
    """限流状态"""
    client_id: str
    client_type: str  # user, ip, api_key
    limit_type: str  # per_user, per_org, global
    tokens: float
    capacity: int
    remaining: float
    reset_at: datetime
    rpm: float  # requests per minute


class RateLimitRule(BaseModel):
    """限流规则"""
    id: str
    name: str
    rule_type: str  # user, endpoint, global
    rate: float
    capacity: int
    window_seconds: int
    enabled: bool
    priority: int


@router.get("/status")
async def get_rate_limit_status(
    client_id: Optional[str] = Query(None, description="客户端 ID"),
    client_type: str = Query("user", description="客户端类型: user, ip, api_key")
) -> RateLimitStatus:
    """
    获取当前限流状态
    GET /rate-limit/status?client_id=user:123&client_type=user
    
    Returns:
        当前用户的限流状态
    """
    if not client_id:
        # 从请求上下文中获取
        client_id = f"{client_type}:default"
    
    limiter_key = f"ratelimit:{client_type}:{client_id}"
    
    # 从 Redis 获取限流器状态
    status = await _get_limiter_status(limiter_key)
    
    return RateLimitStatus(
        client_id=client_id,
        client_type=client_type,
        limit_type="per_user",
        tokens=status["tokens"],
        capacity=status["capacity"],
        remaining=status["remaining"],
        reset_at=status["reset_at"],
        rpm=status["rpm"]
    )


@router.get("/status/batch")
async def get_batch_rate_limit_status(
    client_ids: str = Query(..., description="逗号分隔的客户端 ID 列表")
) -> dict:
    """
    批量获取限流状态
    GET /rate-limit/status/batch?client_ids=user:1,user:2,ip:192.168.1.1
    """
    ids_list = client_ids.split(",")
    
    statuses = []
    for cid in ids_list:
        client_type, client_id = cid.split(":", 1) if ":" in cid else ("unknown", cid)
        status = await _get_limiter_status(f"ratelimit:{client_type}:{client_id}")
        statuses.append({
            "client_id": cid,
            "client_type": client_type,
            "remaining": status["remaining"],
            "capacity": status["capacity"]
        })
    
    return {"statuses": statuses}
```

### 2.2 配额管理 API

```python
# src/skyone_shuge/api/v1/quota.py
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/rate-limit/quota", tags=["配额管理"])


class QuotaConfig(BaseModel):
    """配额配置"""
    id: str
    name: str
    quota_type: str  # user, organization
    user_id: Optional[str]
    org_id: Optional[str]
    daily_tokens: int
    daily_cost_usd: float
    monthly_tokens: int
    monthly_cost_usd: float
    requests_per_minute: int
    status: str  # active, paused
    created_at: datetime
    updated_at: datetime


class QuotaUsage(BaseModel):
    """配额使用情况"""
    quota_id: str
    daily: dict  # { used_tokens, used_cost, limit_tokens, limit_cost, remaining }
    monthly: dict
    today_reset_at: datetime
    month_reset_at: datetime


class QuotaCreateRequest(BaseModel):
    name: str
    quota_type: str
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    daily_tokens: int = 100000
    daily_cost_usd: float = 10.0
    monthly_tokens: int = 1000000
    monthly_cost_usd: float = 100.0
    requests_per_minute: int = 60


@router.get("/quotas")
async def list_quotas(
    quota_type: Optional[str] = Query(None, description="配额类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> dict:
    """
    获取配额列表
    GET /rate-limit/quota/quotas?quota_type=user&page=1&page_size=20
    """
    quotas = await _list_quotas_from_db(
        quota_type=quota_type,
        status=status,
        page=page,
        page_size=page_size
    )
    
    total = await _count_quotas(
        quota_type=quota_type,
        status=status
    )
    
    return {
        "quotas": quotas,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/quotas")
async def create_quota(
    request: QuotaCreateRequest
) -> QuotaConfig:
    """
    创建配额
    POST /rate-limit/quota/quotas
    """
    # 检查是否已存在相同配额
    existing = await _check_existing_quota(
        quota_type=request.quota_type,
        user_id=request.user_id,
        org_id=request.org_id
    )
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Quota already exists for this entity"
        )
    
    quota = await _create_quota_in_db(request)
    
    return quota


@router.get("/quotas/{quota_id}")
async def get_quota(
    quota_id: str
) -> QuotaConfig:
    """
    获取配额详情
    GET /rate-limit/quota/quotas/{quota_id}
    """
    quota = await _get_quota_from_db(quota_id)
    
    if not quota:
        raise HTTPException(status_code=404, detail="Quota not found")
    
    return quota


@router.put("/quotas/{quota_id}")
async def update_quota(
    quota_id: str,
    request: QuotaCreateRequest
) -> QuotaConfig:
    """
    更新配额
    PUT /rate-limit/quota/quotas/{quota_id}
    """
    quota = await _update_quota_in_db(quota_id, request)
    
    if not quota:
        raise HTTPException(status_code=404, detail="Quota not found")
    
    return quota


@router.delete("/quotas/{quota_id}")
async def delete_quota(
    quota_id: str
) -> dict:
    """
    删除配额
    DELETE /rate-limit/quota/quotas/{quota_id}
    """
    success = await _delete_quota_from_db(quota_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Quota not found")
    
    return {"message": "Quota deleted successfully"}


@router.get("/quotas/{quota_id}/usage")
async def get_quota_usage(
    quota_id: str
) -> QuotaUsage:
    """
    获取配额使用情况
    GET /rate-limit/quota/quotas/{quota_id}/usage
    """
    from src.skyone_shuge.services.quota_manager import quota_manager
    
    usage = await quota_manager.get_quota_status(
        user_id=quota_id.split(":")[1] if ":" in quota_id else quota_id
    )
    
    return QuotaUsage(
        quota_id=quota_id,
        daily=usage["daily"],
        monthly=usage["monthly"],
        today_reset_at=usage.get("today_reset_at"),
        month_reset_at=usage.get("month_reset_at")
    )


@router.post("/quotas/{quota_id}/pause")
async def pause_quota(
    quota_id: str
) -> QuotaConfig:
    """
    暂停配额
    POST /rate-limit/quota/quotas/{quota_id}/pause
    """
    quota = await _update_quota_status(quota_id, "paused")
    
    if not quota:
        raise HTTPException(status_code=404, detail="Quota not found")
    
    return quota


@router.post("/quotas/{quota_id}/resume")
async def resume_quota(
    quota_id: str
) -> QuotaConfig:
    """
    恢复配额
    POST /rate-limit/quota/quotas/{quota_id}/resume
    """
    quota = await _update_quota_status(quota_id, "active")
    
    if not quota:
        raise HTTPException(status_code=404, detail="Quota not found")
    
    return quota
```

### 2.3 限流规则 CRUD API

```python
# src/skyone_shuge/api/v1/rate_limit_rules.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/rate-limit/rules", tags=["限流规则"])


class RateLimitRuleCreate(BaseModel):
    name: str
    rule_type: str  # user, endpoint, global
    target: Optional[str] = None  # endpoint path or user pattern
    rate: float  # tokens per second
    capacity: int  # bucket capacity
    window_seconds: int = 60
    enabled: bool = True
    priority: int = 0


class RateLimitRuleResponse(BaseModel):
    id: str
    name: str
    rule_type: str
    target: Optional[str]
    rate: float
    capacity: int
    window_seconds: int
    enabled: bool
    priority: int


@router.get("/rules")
async def list_rate_limit_rules(
    rule_type: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> dict:
    """
    获取限流规则列表
    GET /rate-limit/rules/rules?rule_type=endpoint&page=1&page_size=20
    """
    rules = await _list_rules_from_db(
        rule_type=rule_type,
        enabled=enabled,
        page=page,
        page_size=page_size
    )
    
    total = await _count_rules(rule_type=rule_type, enabled=enabled)
    
    return {
        "rules": rules,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/rules")
async def create_rate_limit_rule(
    rule: RateLimitRuleCreate
) -> RateLimitRuleResponse:
    """
    创建限流规则
    POST /rate-limit/rules/rules
    """
    created_rule = await _create_rule_in_db(rule)
    return created_rule


@router.get("/rules/{rule_id}")
async def get_rate_limit_rule(
    rule_id: str
) -> RateLimitRuleResponse:
    """
    获取限流规则详情
    GET /rate-limit/rules/rules/{rule_id}
    """
    rule = await _get_rule_from_db(rule_id)
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return rule


@router.put("/rules/{rule_id}")
async def update_rate_limit_rule(
    rule_id: str,
    rule: RateLimitRuleCreate
) -> RateLimitRuleResponse:
    """
    更新限流规则
    PUT /rate-limit/rules/rules/{rule_id}
    """
    updated_rule = await _update_rule_in_db(rule_id, rule)
    
    if not updated_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return updated_rule


@router.delete("/rules/{rule_id}")
async def delete_rate_limit_rule(
    rule_id: str
) -> dict:
    """
    删除限流规则
    DELETE /rate-limit/rules/rules/{rule_id}
    """
    success = await _delete_rule_from_db(rule_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return {"message": "Rule deleted successfully"}


@router.post("/rules/{rule_id}/enable")
async def enable_rate_limit_rule(
    rule_id: str
) -> RateLimitRuleResponse:
    """
    启用限流规则
    POST /rate-limit/rules/rules/{rule_id}/enable
    """
    rule = await _update_rule_status(rule_id, enabled=True)
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return rule


@router.post("/rules/{rule_id}/disable")
async def disable_rate_limit_rule(
    rule_id: str
) -> RateLimitRuleResponse:
    """
    禁用限流规则
    POST /rate-limit/rules/rules/{rule_id}/disable
    """
    rule = await _update_rule_status(rule_id, enabled=False)
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return rule
```

---

## ✅ 三、缓存管理后端 API 实现

### 3.1 缓存状态查询 API

```python
# src/skyone_shuge/api/v1/cache.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/cache", tags=["缓存管理"])


class MemoryCacheStats(BaseModel):
    """内存缓存统计"""
    size: int  # 当前条目数
    capacity: int  # 最大容量
    hit_count: int
    miss_count: int
    hit_rate: float
    eviction_count: int


class RedisCacheStats(BaseModel):
    """Redis 缓存统计"""
    keys: int  # 总键数
    memory_used: int  # 内存使用 (bytes)
    memory_peak: int  # 峰值内存
    hit_count: int
    miss_count: int
    hit_rate: float
    connected_clients: int
    uptime_seconds: int


class CacheStats(BaseModel):
    """完整缓存统计"""
    memory: MemoryCacheStats
    redis: RedisCacheStats
    total_hit_rate: float
    last_updated: datetime


class CacheKeyInfo(BaseModel):
    """缓存键信息"""
    key: str
    ttl: int  # 剩余 TTL (秒)
    size_bytes: int
    access_count: int
    last_access: Optional[datetime]


@router.get("/stats", response_model=CacheStats)
async def get_cache_stats():
    """
    获取缓存统计信息
    GET /cache/stats
    
    Returns:
        内存缓存和 Redis 缓存的详细统计
    """
    from src.skyone_shuge.cache.multi_level import get_cache
    
    cache = get_cache()
    
    # 获取内存缓存统计
    memory_stats = _get_memory_cache_stats(cache)
    
    # 获取 Redis 缓存统计
    redis_stats = await _get_redis_cache_stats()
    
    # 计算总命中率
    total_hits = memory_stats.hit_count + redis_stats.hit_count
    total_accesses = total_hits + memory_stats.miss_count + redis_stats.miss_count
    total_hit_rate = total_hits / total_accesses if total_accesses > 0 else 0.0
    
    return CacheStats(
        memory=memory_stats,
        redis=redis_stats,
        total_hit_rate=total_hit_rate,
        last_updated=datetime.utcnow()
    )


@router.get("/stats/memory")
async def get_memory_cache_stats() -> MemoryCacheStats:
    """
    获取内存缓存统计
    GET /cache/stats/memory
    """
    from src.skyone_shuge.cache.multi_level import get_cache
    
    cache = get_cache()
    return _get_memory_cache_stats(cache)


@router.get("/stats/redis")
async def get_redis_cache_stats() -> RedisCacheStats:
    """
    获取 Redis 缓存统计
    GET /cache/stats/redis
    """
    return await _get_redis_cache_stats()


@router.get("/keys")
async def list_cache_keys(
    pattern: str = Query("*", description="键匹配模式"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> dict:
    """
    列出缓存键
    GET /cache/keys?pattern=user:*&limit=100&offset=0
    """
    keys = await _list_redis_keys(pattern, limit, offset)
    
    total = await _count_redis_keys(pattern)
    
    key_infos = []
    for key in keys:
        info = await _get_key_info(key)
        key_infos.append(info)
    
    return {
        "keys": key_infos,
        "total": total,
        "pattern": pattern,
        "limit": limit,
        "offset": offset
    }


@router.get("/keys/{key}")
async def get_cache_key_info(
    key: str
) -> CacheKeyInfo:
    """
    获取指定缓存键的详细信息
    GET /cache/keys/{key}
    """
    info = await _get_key_info(key)
    
    if not info:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return info
```

### 3.2 缓存清理 API

```python
# src/skyone_shuge/api/v1/cache_invalidate.py
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter(prefix="/cache", tags=["缓存清理"])


class CacheInvalidateRequest(BaseModel):
    """缓存清理请求"""
    pattern: Optional[str] = None  # 键匹配模式
    keys: Optional[List[str]] = None  # 指定键列表
    reason: Optional[str] = None  # 清理原因


class CacheInvalidateResponse(BaseModel):
    """缓存清理响应"""
    invalidated_count: int  # 清理的键数量
    pattern: Optional[str]
    keys: Optional[List[str]]
    duration_ms: int


@router.post("/invalidate")
async def invalidate_cache(
    request: CacheInvalidateRequest
) -> CacheInvalidateResponse:
    """
    清理缓存
    POST /cache/invalidate
    
    Body:
        {"pattern": "user:*"} 或 {"keys": ["key1", "key2"]}
    """
    import time
    start_time = time.time()
    
    from src.skyone_shuge.cache.multi_level import get_cache
    
    cache = get_cache()
    invalidated_count = 0
    
    if request.pattern:
        # 按模式批量清理
        invalidated_count = await cache.invalidate_pattern(
            f"skyone:cache:{request.pattern}"
        )
    
    if request.keys:
        # 按指定键清理
        for key in request.keys:
            await cache.delete(key)
            invalidated_count += 1
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    return CacheInvalidateResponse(
        invalidated_count=invalidated_count,
        pattern=request.pattern,
        keys=request.keys,
        duration_ms=duration_ms
    )


@router.post("/invalidate/user/{user_id}")
async def invalidate_user_cache(
    user_id: str,
    reason: Optional[str] = Query(None)
) -> CacheInvalidateResponse:
    """
    清理用户相关缓存
    POST /cache/invalidate/user/{user_id}?reason=profile_update
    """
    import time
    from src.skyone_shuge.cache.multi_level import get_cache
    
    start_time = time.time()
    cache = get_cache()
    
    invalidated_count = await cache.invalidate_pattern(f"skyone:cache:user:{user_id}:*")
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    return CacheInvalidateResponse(
        invalidated_count=invalidated_count,
        pattern=f"user:{user_id}:*",
        keys=None,
        duration_ms=duration_ms
    )


@router.post("/invalidate/document/{doc_id}")
async def invalidate_document_cache(
    doc_id: str,
    reason: Optional[str] = Query(None)
) -> CacheInvalidateResponse:
    """
    清理文档相关缓存
    POST /cache/invalidate/document/{doc_id}
    """
    import time
    from src.skyone_shuge.cache.multi_level import get_cache
    
    start_time = time.time()
    cache = get_cache()
    
    invalidated_count = await cache.invalidate_pattern(f"skyone:cache:document:{doc_id}:*")
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    return CacheInvalidateResponse(
        invalidated_count=invalidated_count,
        pattern=f"document:{doc_id}:*",
        keys=None,
        duration_ms=duration_ms
    )


@router.post("/invalidate/search")
async def invalidate_search_cache(
    reason: Optional[str] = Query(None)
) -> CacheInvalidateResponse:
    """
    清理所有搜索缓存
    POST /cache/invalidate/search
    """
    import time
    from src.skyone_shuge.cache.multi_level import get_cache
    
    start_time = time.time()
    cache = get_cache()
    
    invalidated_count = await cache.invalidate_pattern("skyone:cache:search:*")
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    return CacheInvalidateResponse(
        invalidated_count=invalidated_count,
        pattern="search:*",
        keys=None,
        duration_ms=duration_ms
    )


@router.post("/flush")
async def flush_all_cache(
    reason: str = Body(..., description="清空原因（必填）")
) -> CacheInvalidateResponse:
    """
    清空所有缓存（谨慎使用）
    POST /cache/flush
    
    Warning: 这将清空所有缓存，包括内存缓存和 Redis 缓存
    """
    import time
    from src.skyone_shuge.cache.multi_level import get_cache
    
    start_time = time.time()
    cache = get_cache()
    
    # 清空 Redis
    await cache.redis.flushdb()
    
    # 清空内存缓存
    cache.memory_cache.clear()
    cache.memory_order.clear()
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    return CacheInvalidateResponse(
        invalidated_count=-1,  # 表示全部清空
        pattern="*",
        keys=None,
        duration_ms=duration_ms
    )
```

### 3.3 缓存预热 API

```python
# src/skyone_shuge/api/v1/cache_warmup.py
from fastapi import APIRouter, BackgroundTasks, Query
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/cache", tags=["缓存预热"])


class WarmupTask(BaseModel):
    """预热任务"""
    task_id: str
    target: str  # user, document, search, all
    target_id: Optional[str]  # specific ID if target is specific
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    items_warmed: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]


@router.post("/warmup")
async def start_cache_warmup(
    target: str = Query("all", description="预热目标: all, user, document, search"),
    target_id: Optional[str] = Query(None, description="特定目标 ID"),
    background: bool = Query(True, description="是否后台执行")
) -> WarmupTask:
    """
    启动缓存预热
    POST /cache/warmup?target=all&background=true
    """
    import uuid
    
    task_id = str(uuid.uuid4())
    
    warmup_task = WarmupTask(
        task_id=task_id,
        target=target,
        target_id=target_id,
        status="pending",
        progress=0,
        items_warmed=0,
        started_at=None,
        completed_at=None,
        error=None
    )
    
    if background:
        # 后台执行
        await _run_warmup_background(warmup_task)
        return warmup_task
    else:
        # 同步执行
        return await _run_warmup_sync(warmup_task)


@router.get("/warmup/{task_id}")
async def get_warmup_status(
    task_id: str
) -> WarmupTask:
    """
    获取预热任务状态
    GET /cache/warmup/{task_id}
    """
    task = await _get_warmup_task(task_id)
    
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Warmup task not found")
    
    return task


@router.get("/warmup")
async def list_warmup_tasks(
    status: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100)
) -> dict:
    """
    列出预热任务
    GET /cache/warmup?status=running&limit=10
    """
    tasks = await _list_warmup_tasks(status, limit)
    
    return {
        "tasks": tasks,
        "count": len(tasks)
    }


async def _run_warmup_background(task: WarmupTask):
    """后台执行预热"""
    import asyncio
    
    task.status = "running"
    task.started_at = datetime.utcnow()
    await _save_warmup_task(task)
    
    try:
        if task.target == "all":
            await _warmup_all(task)
        elif task.target == "user":
            await _warmup_user_data(task, task.target_id)
        elif task.target == "document":
            await _warmup_document_data(task, task.target_id)
        elif task.target == "search":
            await _warmup_search_data(task)
        
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.progress = 100
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
    
    await _save_warmup_task(task)


async def _warmup_all(task: WarmupTask):
    """预热所有数据"""
    # 预热热门用户数据
    await _warmup_user_data(task)
    
    # 预热热门文档
    await _warmup_document_data(task)
    
    # 预热热门搜索
    await _warmup_search_data(task)


async def _warmup_user_data(task: WarmupTask, user_id: Optional[str] = None):
    """预热用户数据缓存"""
    from src.skyone_shuge.cache.multi_level import get_cache
    
    cache = get_cache()
    
    if user_id:
        # 预热特定用户
        user_keys = [f"skyone:cache:user:{user_id}:profile"]
        items = 1
    else:
        # 预热热门用户
        hot_users = await _get_hot_users(limit=100)
        user_keys = [f"skyone:cache:user:{uid}:profile" for uid in hot_users]
        items = len(hot_users)
    
    task.progress = 20
    await _save_warmup_task(task)
    
    for i, key in enumerate(user_keys):
        # 从数据库加载并写入缓存
        data = await _load_user_from_db(key)
        if data:
            await cache.set(key, data, ttl=3600)
        task.items_warmed = i + 1
        task.progress = 20 + int((i / items) * 30)
        await _save_warmup_task(task)


async def _warmup_document_data(task: WarmupTask, doc_id: Optional[str] = None):
    """预热文档数据缓存"""
    from src.skyone_shuge.cache.multi_level import get_cache
    
    cache = get_cache()
    
    if doc_id:
        doc_keys = [f"skyone:cache:document:{doc_id}"]
        items = 1
    else:
        hot_docs = await _get_hot_documents(limit=100)
        doc_keys = [f"skyone:cache:document:{did}" for did in hot_docs]
        items = len(hot_docs)
    
    task.progress = 50
    await _save_warmup_task(task)
    
    for i, key in enumerate(doc_keys):
        data = await _load_document_from_db(key)
        if data:
            await cache.set(key, data, ttl=3600)
        task.items_warmed = i + 1
        task.progress = 50 + int((i / items) * 30)
        await _save_warmup_task(task)


async def _warmup_search_data(task: WarmupTask):
    """预热搜索结果缓存"""
    from src.skyone_shuge.cache.multi_level import get_cache
    
    cache = get_cache()
    
    popular_searches = await _get_popular_searches(limit=50)
    
    task.progress = 80
    await _save_warmup_task(task)
    
    for i, query in enumerate(popular_searches):
        results = await _execute_search(query)
        key = f"skyone:cache:search:{query}"
        await cache.set(key, results, ttl=1800)  # 搜索缓存较短
        task.items_warmed = i + 1
        task.progress = 80 + int((i / len(popular_searches)) * 20)
        await _save_warmup_task(task)
```

---

## ✅ 四、前端与后端联调

### 4.1 API 服务层联调

```typescript
// frontend/src/services/api/monitoring.ts
import { apiClient } from './client';

export const monitoringApi = {
  // Prometheus Metrics
  async getMetrics(): Promise<string> {
    const response = await apiClient.get('/metrics');
    return response.data;
  },

  async getMetricsSummary(): Promise<any> {
    const response = await apiClient.get('/metrics/summary');
    return response.data;
  },

  // Dashboard
  async getDashboardOverview(period: string = '1h'): Promise<any> {
    const response = await apiClient.get('/dashboard/overview', {
      params: { period }
    });
    return response.data;
  },

  async getHttpRequestsDashboard(period: string = '1h'): Promise<any> {
    const response = await apiClient.get('/dashboard/http-requests', {
      params: { period }
    });
    return response.data;
  },

  async getLlmUsageDashboard(period: string = '1h'): Promise<any> {
    const response = await apiClient.get('/dashboard/llm-usage', {
      params: { period }
    });
    return response.data;
  },

  async getCacheDashboard(): Promise<any> {
    const response = await apiClient.get('/dashboard/cache-dashboard');
    return response.data;
  },

  // Traces
  async getTrace(traceId: string): Promise<any> {
    const response = await apiClient.get(`/traces/${traceId}`);
    return response.data;
  },

  async listTraces(params: {
    service?: string;
    operation?: string;
    start_time?: string;
    end_time?: string;
    limit?: number;
    offset?: number;
  }): Promise<any> {
    const response = await apiClient.get('/traces/list', { params });
    return response.data;
  },

  async getServices(): Promise<any> {
    const response = await apiClient.get('/traces/services');
    return response.data;
  },

  // Logs
  async queryLogs(params: {
    query?: string;
    level?: string;
    service?: string;
    start_time?: string;
    end_time?: string;
    limit?: number;
  }): Promise<any> {
    const response = await apiClient.get('/logs', { params });
    return response.data;
  }
};

// frontend/src/services/api/rateLimit.ts
export const rateLimitApi = {
  // Status
  async getRateLimitStatus(clientId?: string, clientType: string = 'user'): Promise<any> {
    const response = await apiClient.get('/rate-limit/status', {
      params: { client_id: clientId, client_type: clientType }
    });
    return response.data;
  },

  async getBatchRateLimitStatus(clientIds: string[]): Promise<any> {
    const response = await apiClient.get('/rate-limit/status/batch', {
      params: { client_ids: clientIds.join(',') }
    });
    return response.data;
  },

  // Quotas
  async listQuotas(params: {
    quota_type?: string;
    status?: string;
    page?: number;
    page_size?: number;
  }): Promise<any> {
    const response = await apiClient.get('/rate-limit/quota/quotas', { params });
    return response.data;
  },

  async createQuota(data: any): Promise<any> {
    const response = await apiClient.post('/rate-limit/quota/quotas', data);
    return response.data;
  },

  async getQuota(quotaId: string): Promise<any> {
    const response = await apiClient.get(`/rate-limit/quota/quotas/${quotaId}`);
    return response.data;
  },

  async updateQuota(quotaId: string, data: any): Promise<any> {
    const response = await apiClient.put(`/rate-limit/quota/quotas/${quotaId}`, data);
    return response.data;
  },

  async deleteQuota(quotaId: string): Promise<any> {
    const response = await apiClient.delete(`/rate-limit/quota/quotas/${quotaId}`);
    return response.data;
  },

  async getQuotaUsage(quotaId: string): Promise<any> {
    const response = await apiClient.get(`/rate-limit/quota/quotas/${quotaId}/usage`);
    return response.data;
  },

  async pauseQuota(quotaId: string): Promise<any> {
    const response = await apiClient.post(`/rate-limit/quota/quotas/${quotaId}/pause`);
    return response.data;
  },

  async resumeQuota(quotaId: string): Promise<any> {
    const response = await apiClient.post(`/rate-limit/quota/quotas/${quotaId}/resume`);
    return response.data;
  },

  // Rules
  async listRules(params: {
    rule_type?: string;
    enabled?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<any> {
    const response = await apiClient.get('/rate-limit/rules/rules', { params });
    return response.data;
  },

  async createRule(data: any): Promise<any> {
    const response = await apiClient.post('/rate-limit/rules/rules', data);
    return response.data;
  },

  async updateRule(ruleId: string, data: any): Promise<any> {
    const response = await apiClient.put(`/rate-limit/rules/rules/${ruleId}`, data);
    return response.data;
  },

  async deleteRule(ruleId: string): Promise<any> {
    const response = await apiClient.delete(`/rate-limit/rules/rules/${ruleId}`);
    return response.data;
  }
};

// frontend/src/services/api/cache.ts
export const cacheApi = {
  // Stats
  async getCacheStats(): Promise<any> {
    const response = await apiClient.get('/cache/stats');
    return response.data;
  },

  async getMemoryCacheStats(): Promise<any> {
    const response = await apiClient.get('/cache/stats/memory');
    return response.data;
  },

  async getRedisCacheStats(): Promise<any> {
    const response = await apiClient.get('/cache/stats/redis');
    return response.data;
  },

  // Keys
  async listCacheKeys(params: {
    pattern?: string;
    limit?: number;
    offset?: number;
  }): Promise<any> {
    const response = await apiClient.get('/cache/keys', { params });
    return response.data;
  },

  async getCacheKeyInfo(key: string): Promise<any> {
    const response = await apiClient.get(`/cache/keys/${encodeURIComponent(key)}`);
    return response.data;
  },

  // Invalidate
  async invalidateCache(data: { pattern?: string; keys?: string[]; reason?: string }): Promise<any> {
    const response = await apiClient.post('/cache/invalidate', data);
    return response.data;
  },

  async invalidateUserCache(userId: string, reason?: string): Promise<any> {
    const response = await apiClient.post(`/cache/invalidate/user/${userId}`, null, {
      params: { reason }
    });
    return response.data;
  },

  async invalidateDocumentCache(docId: string, reason?: string): Promise<any> {
    const response = await apiClient.post(`/cache/invalidate/document/${docId}`, null, {
      params: { reason }
    });
    return response.data;
  },

  async flushAllCache(reason: string): Promise<any> {
    const response = await apiClient.post('/cache/flush', null, {
      data: { reason }
    });
    return response.data;
  },

  // Warmup
  async startCacheWarmup(params: {
    target?: string;
    target_id?: string;
    background?: boolean;
  }): Promise<any> {
    const response = await apiClient.post('/cache/warmup', null, { params });
    return response.data;
  },

  async getWarmupStatus(taskId: string): Promise<any> {
    const response = await apiClient.get(`/cache/warmup/${taskId}`);
    return response.data;
  },

  async listWarmupTasks(params: { status?: string; limit?: number }): Promise<any> {
    const response = await apiClient.get('/cache/warmup', { params });
    return response.data;
  }
};
```

### 4.2 监控仪表盘前端组件

```typescript
// frontend/src/pages/MonitoringDashboard.tsx
import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Spin, Select, DatePicker, Table, Tag, Progress } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { monitoringApi } from '@/services/api/monitoring';
import './MonitoringDashboard.less';

const { RangePicker } = DatePicker;

interface DashboardData {
  http_requests: any;
  llm_usage: any;
  cache_performance: any;
  error_rate: any;
}

export const MonitoringDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('1h');
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [services, setServices] = useState<any[]>([]);
  const [traces, setTraces] = useState<any[]>([]);

  useEffect(() => {
    fetchDashboardData();
    fetchServices();
    // 定时刷新
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, [period]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [overview, cacheDash] = await Promise.all([
        monitoringApi.getDashboardOverview(period),
        monitoringApi.getCacheDashboard()
      ]);
      setDashboardData({ ...overview, cache_performance: cacheDash });
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchServices = async () => {
    try {
      const data = await monitoringApi.getServices();
      setServices(data.services || []);
    } catch (error) {
      console.error('Failed to fetch services:', error);
    }
  };

  return (
    <div className="monitoring-dashboard">
      <div className="dashboard-header">
        <h1>监控仪表盘</h1>
        <div className="header-controls">
          <Select value={period} onChange={setPeriod} style={{ width: 150 }}>
            <Select.Option value="1h">最近 1 小时</Select.Option>
            <Select.Option value="6h">最近 6 小时</Select.Option>
            <Select.Option value="24h">最近 24 小时</Select.Option>
            <Select.Option value="7d">最近 7 天</Select.Option>
          </Select>
        </div>
      </div>

      <Spin spinning={loading}>
        {/* HTTP 请求概览 */}
        <Row gutter={16} className="stats-row">
          <Col span={6}>
            <Card>
              <Statistic
                title="总请求数"
                value={dashboardData?.http_requests?.total_requests || 0}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="平均延迟"
                value={dashboardData?.http_requests?.avg_latency || 0}
                suffix="ms"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="错误率"
                value={(dashboardData?.error_rate?.rate || 0) * 100}
                suffix="%"
                valueStyle={{ color: (dashboardData?.error_rate?.rate || 0) > 0.01 ? '#f5222d' : '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="LLM 成本"
                value={dashboardData?.llm_usage?.total_cost || 0}
                prefix="$"
              />
            </Card>
          </Col>
        </Row>

        {/* 图表区域 */}
        <Row gutter={16} className="charts-row">
          <Col span={12}>
            <Card title="请求量趋势">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={dashboardData?.http_requests?.timeline || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="requests" stroke="#1890ff" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </Col>
          <Col span={12}>
            <Card title="LLM Token 使用">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={dashboardData?.llm_usage?.timeline || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="tokens" stroke="#52c41a" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>

        {/* 服务状态 */}
        <Card title="服务状态" className="services-card">
          <Table
            dataSource={services}
            rowKey="name"
            pagination={false}
            columns={[
              { title: '服务', dataIndex: 'name' },
              { title: 'Span 数', dataIndex: 'spans_count' },
              {
                title: '错误率',
                dataIndex: 'error_rate',
                render: (rate: number) => (
                  <Tag color={rate > 0.01 ? 'red' : 'green'}>
                    {(rate * 100).toFixed(2)}%
                  </Tag>
                )
              },
              {
                title: 'P99 延迟',
                dataIndex: 'p99_latency',
                render: (lat: number) => `${lat.toFixed(2)}ms`
              }
            ]}
          />
        </Card>

        {/* 缓存状态 */}
        <Row gutter={16} className="cache-row">
          <Col span={12}>
            <Card title="内存缓存 (L1)">
              <Progress
                percent={Math.round(
                  (dashboardData?.cache_performance?.memory?.size /
                    dashboardData?.cache_performance?.memory?.capacity) * 100
                )}
                format={() =>
                  `${dashboardData?.cache_performance?.memory?.size}/${dashboardData?.cache_performance?.memory?.capacity}`
                }
              />
              <p>命中率: {((dashboardData?.cache_performance?.memory?.hit_rate || 0) * 100).toFixed(2)}%</p>
            </Card>
          </Col>
          <Col span={12}>
            <Card title="Redis 缓存 (L2)">
              <Statistic title="键数量" value={dashboardData?.cache_performance?.redis?.keys || 0} />
              <p>命中率: {((dashboardData?.cache_performance?.redis?.hit_rate || 0) * 100).toFixed(2)}%</p>
            </Card>
          </Col>
        </Row>
      </Spin>
    </div>
  );
};
```

---

## ✅ 五、端到端测试完善

### 5.1 用户流程 E2E 测试

```python
# tests/e2e/test_user_flows.py
import pytest
from playwright.sync_api import sync_playwright, Page, expect
from fastapi.testclient import TestClient


class TestUserJourney:
    """用户旅程 E2E 测试"""
    
    @pytest.fixture(scope="class")
    def browser(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            yield browser
            browser.close()
    
    @pytest.fixture
    def page(self, browser):
        context = browser.new_context()
        page = context.new_page()
        yield page
        context.close()
    
    @pytest.fixture
    def api_client(self):
        from src.main import app
        return TestClient(app)
    
    def test_user_registration_flow(self, page: Page):
        """测试用户注册流程"""
        page.goto("http://localhost:3000/register")
        
        # 填写注册表单
        page.fill('input[name="username"]', 'testuser')
        page.fill('input[name="email"]', 'test@example.com')
        page.fill('input[name="password"]', 'SecurePass123!')
        
        # 点击注册按钮
        page.click('button[type="submit"]')
        
        # 验证注册成功
        expect(page.locator('.success-message')).to_be_visible()
        expect(page).to_have_url("/dashboard")
    
    def test_document_search_flow(self, page: Page, api_client):
        """测试文档搜索流程"""
        # 先登录
        page.goto("http://localhost:3000/login")
        page.fill('input[name="email"]', 'test@example.com')
        page.fill('input[name="password"]', 'SecurePass123!')
        page.click('button[type="submit"]')
        
        # 等待跳转
        page.wait_for_url("/dashboard")
        
        # 进入搜索页面
        page.goto("http://localhost:3000/search")
        
        # 执行搜索
        page.fill('input[placeholder="搜索文档..."]', '测试文档')
        page.click('button.search-button')
        
        # 验证搜索结果
        expect(page.locator('.search-results')).to_be_visible()
        expect(page.locator('.result-item')).to_have_count(min=1)
    
    def test_monitoring_dashboard_flow(self, page: Page, api_client):
        """测试监控仪表盘流程"""
        # 登录
        page.goto("http://localhost:3000/login")
        page.fill('input[name="email"]', 'admin@example.com')
        page.fill('input[name="password"]', 'AdminPass123!')
        page.click('button[type="submit"]')
        
        # 进入监控仪表盘
        page.goto("http://localhost:3000/monitoring")
        
        # 验证页面加载
        expect(page.locator('.monitoring-dashboard')).to_be_visible()
        expect(page.locator('.stats-row')).to_be_visible()
        
        # 验证指标图表
        expect(page.locator('.chart-container')).to_be_visible()


class TestApiIntegration:
    """API 集成 E2E 测试"""
    
    def test_metrics_endpoint(self, api_client):
        """测试指标端点"""
        response = api_client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
    
    def test_dashboard_overview(self, api_client):
        """测试仪表盘概览"""
        response = api_client.get("/dashboard/overview?period=1h")
        assert response.status_code == 200
        data = response.json()
        assert "http_requests" in data
        assert "llm_usage" in data
        assert "cache_performance" in data
    
    def test_trace_list(self, api_client):
        """测试追踪列表"""
        response = api_client.get("/traces/list?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "traces" in data
        assert "total" in data
    
    def test_rate_limit_status(self, api_client):
        """测试限流状态"""
        response = api_client.get("/rate-limit/status?client_type=user")
        assert response.status_code == 200
        data = response.json()
        assert "client_id" in data
        assert "remaining" in data
        assert "capacity" in data
    
    def test_quota_crud(self, api_client):
        """测试配额 CRUD"""
        # Create
        create_response = api_client.post("/rate-limit/quota/quotas", json={
            "name": "test_quota",
            "quota_type": "user",
            "user_id": "test_user",
            "daily_tokens": 100000,
            "daily_cost_usd": 10.0,
            "monthly_tokens": 1000000,
            "monthly_cost_usd": 100.0,
            "requests_per_minute": 60
        })
        assert create_response.status_code == 200
        quota_id = create_response.json()["id"]
        
        # Read
        get_response = api_client.get(f"/rate-limit/quota/quotas/{quota_id}")
        assert get_response.status_code == 200
        
        # Update
        update_response = api_client.put(
            f"/rate-limit/quota/quotas/{quota_id}",
            json={"name": "updated_quota", "daily_tokens": 200000}
        )
        assert update_response.status_code == 200
        
        # Delete
        delete_response = api_client.delete(f"/rate-limit/quota/quotas/{quota_id}")
        assert delete_response.status_code == 200
    
    def test_cache_stats(self, api_client):
        """测试缓存统计"""
        response = api_client.get("/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "memory" in data
        assert "redis" in data
        assert "total_hit_rate" in data
    
    def test_cache_warmup(self, api_client):
        """测试缓存预热"""
        response = api_client.post("/cache/warmup?target=all&background=false")
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
```

### 5.2 WebSocket 联接测试

```python
# tests/e2e/test_websocket.py
import pytest
import asyncio
from websockets.client import connect
from fastapi.testclient import TestClient


class TestWebSocketConnection:
    """WebSocket 连接测试"""
    
    @pytest.fixture
    def ws_url(self):
        return "ws://localhost:8000/ws"
    
    @pytest.fixture
    def auth_token(self):
        # 获取测试 JWT token
        from src.main import app
        client = TestClient(app)
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123!"
        })
        return response.json()["access_token"]
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, ws_url, auth_token):
        """测试 WebSocket 连接"""
        async with connect(f"{ws_url}?token={auth_token}") as ws:
            # 接收连接成功消息
            message = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(message)
            assert data["type"] == "connected"
            assert "session_id" in data
    
    @pytest.mark.asyncio
    async def test_websocket_task_subscription(self, ws_url, auth_token):
        """测试任务订阅"""
        async with connect(f"{ws_url}?token={auth_token}") as ws:
            # 等待连接
            await ws.recv()
            
            # 订阅任务进度
            await ws.send(json.dumps({
                "action": "subscribe",
                "channel": "task_progress",
                "task_id": "test_task_123"
            }))
            
            # 接收订阅确认
            confirm = await asyncio.wait_for(ws.recv(), timeout=5)
            assert json.loads(confirm)["status"] == "subscribed"
    
    @pytest.mark.asyncio
    async def test_websocket_heartbeat(self, ws_url, auth_token):
        """测试心跳"""
        async with connect(f"{ws_url}?token={auth_token}") as ws:
            await ws.recv()  # 连接消息
            
            # 发送心跳
            await ws.send(json.dumps({"action": "ping"}))
            
            # 接收心跳响应
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)
            assert data["action"] == "pong"
    
    @pytest.mark.asyncio
    async def test_websocket_reconnection(self, ws_url, auth_token):
        """测试重连机制"""
        # 第一次连接
        ws1 = await connect(f"{ws_url}?token={auth_token}")
        await ws1.recv()
        
        # 模拟断开
        await ws1.close()
        
        # 重新连接
        ws2 = await connect(f"{ws_url}?token={auth_token}")
        message = await asyncio.wait_for(ws2.recv(), timeout=5)
        data = json.loads(message)
        assert data["type"] == "connected"
        
        await ws2.close()


class TestWebSocketMessaging:
    """WebSocket 消息测试"""
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self, ws_url, auth_token):
        """测试广播消息"""
        async with connect(f"{ws_url}?token={auth_token}") as ws:
            await ws.recv()
            
            # 订阅通知
            await ws.send(json.dumps({
                "action": "subscribe",
                "channel": "notifications"
            }))
            await ws.recv()
            
            # 管理员发送广播（通过 API）
            from src.main import app
            client = TestClient(app)
            client.headers = {"Authorization": f"Bearer {auth_token}"}
            response = client.post("/api/v1/ws/broadcast", json={
                "channel": "notifications",
                "message": {"type": "system", "content": "Test broadcast"}
            })
            
            # 接收广播
            message = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(message)
            assert data["type"] == "broadcast"
```

---

## ✅ 六、API 路由注册

```python
# src/skyone_shuge/api/v1/router.py
from fastapi import APIRouter
from . import metrics, traces, logs, dashboard, rate_limit, quota, cache, rate_limit_rules, cache_warmup

api_router = APIRouter()

# 监控相关
api_router.include_router(metrics.router)
api_router.include_router(traces.router)
api_router.include_router(logs.router)
api_router.include_router(dashboard.router)

# 限流相关
api_router.include_router(rate_limit.router)
api_router.include_router(quota.router)
api_router.include_router(rate_limit_rules.router)

# 缓存相关
api_router.include_router(cache.router)
api_router.include_router(cache_warmup.router)
```

---

## 📊 七、部署与配置

### 7.1 新增环境变量

```bash
# .env.production

# 监控配置
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
OTEL_ENABLED=true
OTEL_ENDPOINT=http://jaeger:4317
LOKI_ENABLED=true
LOKI_ENDPOINT=http://loki:3100

# 限流配置
RATE_LIMIT_STRATEGY=token_bucket
RATE_LIMIT_STORAGE=redis
RATE_LIMIT_DEFAULT_RPM=100
RATE_LIMIT_DEFAULT_CAPACITY=100

# 缓存配置
CACHE_L1_SIZE=1000
CACHE_L2_TTL=3600
CACHE_WARMUP_ENABLED=true
```

### 7.2 API 端点汇总

| 端点 | 方法 | 说明 |
|------|------|------|
| `/metrics` | GET | Prometheus 指标 |
| `/metrics/summary` | GET | 指标摘要 (JSON) |
| `/metrics/health` | GET | 监控健康状态 |
| `/dashboard/overview` | GET | 仪表盘概览 |
| `/dashboard/http-requests` | GET | HTTP 请求仪表盘 |
| `/dashboard/llm-usage` | GET | LLM 使用仪表盘 |
| `/dashboard/cache-dashboard` | GET | 缓存仪表盘 |
| `/traces/{id}` | GET | 获取 Trace |
| `/traces/list` | GET | 查询 Trace 列表 |
| `/traces/services` | GET | 服务列表 |
| `/traces/dependencies` | GET | 服务依赖关系 |
| `/logs` | GET | 查询日志 |
| `/logs/aggregations` | GET | 日志聚合 |
| `/rate-limit/status` | GET | 限流状态 |
| `/rate-limit/status/batch` | GET | 批量限流状态 |
| `/rate-limit/quota/quotas` | GET/POST | 配额列表/创建 |
| `/rate-limit/quota/quotas/{id}` | GET/PUT/DELETE | 配额详情 |
| `/rate-limit/quota/quotas/{id}/usage` | GET | 配额使用情况 |
| `/rate-limit/rules/rules` | GET/POST | 规则列表/创建 |
| `/rate-limit/rules/rules/{id}` | GET/PUT/DELETE | 规则详情 |
| `/cache/stats` | GET | 缓存统计 |
| `/cache/stats/memory` | GET | 内存缓存统计 |
| `/cache/stats/redis` | GET | Redis 缓存统计 |
| `/cache/keys` | GET | 缓存键列表 |
| `/cache/invalidate` | POST | 清理缓存 |
| `/cache/warmup` | POST | 预热缓存 |
| `/cache/warmup/{task_id}` | GET | 预热任务状态 |

---

## ✅ 验收标准

### 后端 API
- [ ] Prometheus `/metrics` 端点正常返回指标
- [ ] `/metrics/summary` 返回 JSON 格式指标摘要
- [ ] `/traces/{id}` 和 `/traces/list` 正常工作
- [ ] `/rate-limit/status` 返回正确限流状态
- [ ] `/rate-limit/quota/quotas` CRUD 操作正常
- [ ] `/rate-limit/rules/rules` CRUD 操作正常
- [ ] `/cache/stats` 返回完整缓存统计
- [ ] `/cache/invalidate` 按模式和键清理缓存
- [ ] `/cache/warmup` 预热任务正常执行

### 前端联调
- [ ] 监控仪表盘正确显示 HTTP/LLM/缓存指标
- [ ] 追踪查看器正确显示 Trace 瀑布图
- [ ] 限流配置面板正确调用后端 API
- [ ] 缓存管理界面正确显示状态并支持操作

### E2E 测试
- [ ] 用户注册/登录流程正常
- [ ] 文档搜索流程正常
- [ ] 监控仪表盘页面正常加载
- [ ] WebSocket 连接/订阅/心跳正常
- [ ] API 集成测试覆盖所有新端点
