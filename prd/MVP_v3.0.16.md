# 天一阁 PRD v3.0.16

**版本**: v3.0.16
**日期**: 2026-04-05
**阶段**: 实现代码开发 + 前端 UI 组件开发 + 单元测试与集成测试

---

## 📋 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0.16 | 2026-04-05 | 实现代码开发 + 前端 UI 组件开发 + 单元测试与集成测试 |
| v3.0.15 | 2026-04-04 | 监控与可观测性架构 + API 限流与成本控制架构 + 多级缓存架构 + 性能优化架构 + 高级搜索增强架构 + LLM 成本追踪与预算控制 |
| v3.0.14 | 2026-04-03 | 智能推荐系统架构 + 文档版本对比架构 + 自动化工作流架构 + 高级分析报告架构 + 多语言支持架构 |

---

## 🎯 本次迭代目标

### 核心交付物
- [ ] **后端核心模块实现**: 监控 SDK 集成、限流中间件实现、多级缓存封装、性能优化中间件、ES 搜索封装、LLM 成本追踪服务
- [ ] **前端 UI 组件开发**: 监控仪表盘、限流配置面板、缓存管理界面、搜索控制台、成本展示面板
- [ ] **单元测试框架**: pytest 配置、测试用例编写、Mock 策略、覆盖率配置
- [ ] **集成测试方案**: API 集成测试、数据库集成测试、Redis 集成测试、端到端测试

---

## ✅ 一、后端核心模块实现

### 1.1 监控 SDK 集成

#### 1.1.1 Prometheus Metrics 客户端

```python
# src/skyone_shuge/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from prometheus_client.exposition import generate_latest, CONTENT_TYPE_LATEST
from typing import Optional
import time

class MetricsCollector:
    """统一指标采集器"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self._init_metrics()
    
    def _init_metrics(self):
        # HTTP 请求指标
        self.http_requests_total = Counter(
            'skyone_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'skyone_http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
            registry=self.registry
        )
        
        # LLM 调用指标
        self.llm_requests_total = Counter(
            'skyone_llm_requests_total',
            'Total LLM requests',
            ['provider', 'model', 'status'],
            registry=self.registry
        )
        
        self.llm_tokens_total = Counter(
            'skyone_llm_tokens_total',
            'Total LLM tokens used',
            ['provider', 'model', 'type'],  # type: prompt/completion
            registry=self.registry
        )
        
        self.llm_request_duration = Histogram(
            'skyone_llm_request_duration_seconds',
            'LLM request duration',
            ['provider', 'model'],
            buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0),
            registry=self.registry
        )
        
        self.llm_cost_total = Counter(
            'skyone_llm_cost_total_usd',
            'Total LLM cost in USD',
            ['provider', 'model'],
            registry=self.registry
        )
        
        # 缓存指标
        self.cache_hits_total = Counter(
            'skyone_cache_hits_total',
            'Total cache hits',
            ['cache_level', 'cache_name'],
            registry=self.registry
        )
        
        self.cache_misses_total = Counter(
            'skyone_cache_misses_total',
            'Total cache misses',
            ['cache_level', 'cache_name'],
            registry=self.registry
        )
        
        self.cache_hit_ratio = Gauge(
            'skyone_cache_hit_ratio',
            'Cache hit ratio',
            ['cache_level', 'cache_name'],
            registry=self.registry
        )
        
        # 数据库指标
        self.db_pool_connections = Gauge(
            'skyone_db_connections',
            'Database connection pool status',
            ['state'],  # active, idle, total
            registry=self.registry
        )
        
        self.db_query_duration = Histogram(
            'skyone_db_query_duration_seconds',
            'Database query duration',
            ['operation', 'table'],
            buckets=(0.001, 0.01, 0.1, 0.5, 1.0),
            registry=self.registry
        )
        
        # 搜索指标
        self.search_requests_total = Counter(
            'skyone_search_requests_total',
            'Total search requests',
            ['search_type', 'status'],
            registry=self.registry
        )
        
        self.search_duration = Histogram(
            'skyone_search_duration_seconds',
            'Search request duration',
            ['search_type'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0),
            registry=self.registry
        )
        
        self.search_results_count = Histogram(
            'skyone_search_results_count',
            'Number of search results',
            ['search_type'],
            buckets=(0, 10, 50, 100, 500, 1000),
            registry=self.registry
        )
    
    def track_http_request(self, method: str, endpoint: str):
        """HTTP 请求跟踪上下文管理器"""
        return HttpRequestTracker(self, method, endpoint)
    
    def track_llm_request(self, provider: str, model: str):
        """LLM 请求跟踪上下文管理器"""
        return LlmRequestTracker(self, provider, model)
    
    def record_cache_access(self, level: str, name: str, hit: bool):
        """记录缓存访问"""
        if hit:
            self.cache_hits_total.labels(cache_level=level, cache_name=name).inc()
        else:
            self.cache_misses_total.labels(cache_level=level, cache_name=name).inc()
    
    def get_metrics(self) -> bytes:
        """获取 Prometheus 格式指标"""
        return generate_latest(self.registry)


class HttpRequestTracker:
    """HTTP 请求跟踪器"""
    
    def __init__(self, collector: MetricsCollector, method: str, endpoint: str):
        self.collector = collector
        self.method = method
        self.endpoint = endpoint
        self.start_time = None
        self.status = 200
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        self.collector.http_requests_total.labels(
            method=self.method,
            endpoint=self.endpoint,
            status=self.status
        ).inc()
        self.collector.http_request_duration.labels(
            method=self.method,
            endpoint=self.endpoint
        ).observe(duration)


class LlmRequestTracker:
    """LLM 请求跟踪器"""
    
    def __init__(self, collector: MetricsCollector, provider: str, model: str):
        self.collector = collector
        self.provider = provider
        self.model = model
        self.start_time = None
        self.tokens_used = 0
        self.cost = 0.0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        status = 'success' if exc_type is None else 'error'
        
        self.collector.llm_requests_total.labels(
            provider=self.provider,
            model=self.model,
            status=status
        ).inc()
        
        self.collector.llm_request_duration.labels(
            provider=self.provider,
            model=self.model
        ).observe(duration)
        
        if self.tokens_used > 0:
            self.collector.llm_tokens_total.labels(
                provider=self.provider,
                model=self.model,
                type='total'
            ).inc(self.tokens_used)
        
        if self.cost > 0:
            self.collector.llm_cost_total.labels(
                provider=self.provider,
                model=self.model
            ).inc(self.cost)


# 全局指标采集器实例
metrics_collector = MetricsCollector()
```

#### 1.1.2 OpenTelemetry Tracing 集成

```python
# src/skyone_shuge/monitoring/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TracingManager:
    """OpenTelemetry 追踪管理器"""
    
    def __init__(self, service_name: str, otlp_endpoint: str):
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint
        self.provider: Optional[TracerProvider] = None
        self.tracer: Optional[trace.Tracer] = None
    
    def setup(self):
        """初始化追踪 provider"""
        # 创建资源
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": "1.0.0",
            "deployment.environment": "production"
        })
        
        # 创建 provider
        self.provider = TracerProvider(resource=resource)
        
        # 配置 OTLP 导出器
        otlp_exporter = OTLPSpanExporter(
            endpoint=self.otlp_endpoint,
            insecure=True
        )
        
        # 添加批量处理器
        span_processor = BatchSpanProcessor(otlp_exporter)
        self.provider.add_span_processor(span_processor)
        
        # 设置全局 provider
        trace.set_tracer_provider(self.provider)
        
        # 设置全局 propagator
        set_global_textmap(TraceContextTextMapPropagator())
        
        # 获取 tracer
        self.tracer = trace.get_tracer(__name__)
        
        logger.info(f"Tracing initialized for {self.service_name}")
    
    def instrument_fastapi(self, app):
        """Instrument FastAPI 应用"""
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="health,metrics,ready",
            service_name=self.service_name
        )
    
    def instrument_sqlalchemy(self, engine):
        """Instrument SQLAlchemy"""
        SQLAlchemyInstrumentor().instrument(
            engine=engine,
            service="skyone-database"
        )
    
    def create_span(self, name: str, attributes: dict = None):
        """创建 span 上下文管理器"""
        if not self.tracer:
            return self._NoOpSpan()
        return self.tracer.start_as_current_span(name, attributes or {})
    
    def shutdown(self):
        """关闭追踪 provider"""
        if self.provider:
            self.provider.shutdown()


class _NoOpSpan:
    """无操作 span（未初始化时使用）"""
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def set_attribute(self, key, value):
        pass
    def set_status(self, status):
        pass
    def record_exception(self, exception):
        pass


# 全局追踪管理器
tracing_manager = TracingManager(
    service_name="skyone-shuge",
    otlp_endpoint=os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
)
```

#### 1.1.3 结构化日志封装

```python
# src/skyone_shuge/monitoring/logging.py
import logging
import json
from typing import Any, Dict
from datetime import datetime
from pythonjsonlogger import jsonlogger
from opentelemetry import trace


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_handler()
    
    def _setup_handler(self):
        """配置 JSON 格式日志处理器"""
        handler = logging.StreamHandler()
        
        # JSON 格式化
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            rename_fields={'levelname': 'level', 'name': 'logger'}
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _get_context(self) -> Dict[str, Any]:
        """获取日志上下文"""
        context = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'skyone-shuge'
        }
        
        # 添加 trace context
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            context['trace_id'] = format(span.get_span_context().trace_id, '032x')
            context['span_id'] = format(span.get_span_context().span_id, '016x')
        
        return context
    
    def info(self, message: str, **kwargs):
        """Info 级别日志"""
        self.logger.info(message, extra={**self._get_context(), **kwargs})
    
    def error(self, message: str, **kwargs):
        """Error 级别日志"""
        self.logger.error(message, extra={**self._get_context(), **kwargs})
    
    def warning(self, message: str, **kwargs):
        """Warning 级别日志"""
        self.logger.warning(message, extra={**self._get_context(), **kwargs})
    
    def debug(self, message: str, **kwargs):
        """Debug 级别日志"""
        self.logger.debug(message, extra={**self._get_context(), **kwargs})
    
    def log_request(self, method: str, path: str, status: int, duration: float):
        """记录 HTTP 请求"""
        self.info(
            "HTTP request",
            event="http_request",
            method=method,
            path=path,
            status=status,
            duration_ms=round(duration * 1000, 2)
        )
    
    def log_llm_request(self, provider: str, model: str, tokens: int, cost: float):
        """记录 LLM 请求"""
        self.info(
            "LLM request",
            event="llm_request",
            provider=provider,
            model=model,
            tokens=tokens,
            cost_usd=cost
        )
    
    def log_cache_access(self, level: str, name: str, hit: bool, key: str):
        """记录缓存访问"""
        self.info(
            "Cache access",
            event="cache_access",
            cache_level=level,
            cache_name=name,
            hit=hit,
            key=key
        )


# 全局日志实例
logger = StructuredLogger("skyone")
```

---

### 1.2 限流中间件实现

#### 1.2.1 令牌桶限流器

```python
# src/skyone_shuge/middleware/rate_limiter.py
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple
import time
import hashlib


class TokenBucket:
    """令牌桶算法实现"""
    
    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: 每秒添加的令牌数
            capacity: 桶的容量
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
    
    def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        """
        尝试消费令牌
        Returns:
            (是否成功, 剩余令牌数)
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True, self.tokens
        return False, self.tokens
    
    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_update
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_update = now


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis = redis_client
        # 默认限制: 100请求/分钟
        self.default_limit = TokenBucket(rate=100/60, capacity=100)
        # 按用户/组织的限流器缓存
        self.limiters: Dict[str, TokenBucket] = {}
    
    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        # 优先使用用户 ID
        if hasattr(request.state, 'user_id'):
            return f"user:{request.state.user_id}"
        
        # 否则使用 IP
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    async def dispatch(self, request: Request, call_next):
        client_id = self._get_client_id(request)
        
        # 获取或创建限流器
        limiter = self.limiters.get(client_id)
        if limiter is None:
            limiter = self.default_limit
            self.limiters[client_id] = limiter
        
        # 尝试消费令牌
        allowed, remaining = limiter.consume()
        
        # 添加限流头
        response = await call_next(request)
        response.headers['X-RateLimit-Limit'] = str(limiter.capacity)
        response.headers['X-RateLimit-Remaining'] = str(int(remaining))
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    'Retry-After': '60',
                    'X-RateLimit-Limit': str(limiter.capacity),
                    'X-RateLimit-Remaining': '0'
                }
            )
        
        return response


class RedisTokenBucket:
    """基于 Redis 的分布式令牌桶"""
    
    SCRIPT = """
    local key = KEYS[1]
    local rate = tonumber(ARGV[1])
    local capacity = tonumber(ARGV[2])
    local now = tonumber(ARGV[3])
    local requested = tonumber(ARGV[4])
    
    -- 获取当前状态
    local data = redis.call('HMGET', key, 'tokens', 'last_update')
    local tokens = tonumber(data[1]) or capacity
    local last_update = tonumber(data[2]) or now
    
    -- 计算应该补充的令牌
    local elapsed = now - last_update
    local new_tokens = elapsed * rate
    tokens = math.min(capacity, tokens + new_tokens)
    
    -- 尝试消费
    local allowed = 0
    if tokens >= requested then
        tokens = tokens - requested
        allowed = 1
    end
    
    -- 更新状态
    redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
    redis.call('EXPIRE', key, 3600)
    
    return {allowed, tokens}
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.script_sha = None
    
    async def consume(self, key: str, rate: float, capacity: int, tokens: int = 1) -> Tuple[bool, float]:
        """分布式令牌桶消费"""
        if not self.script_sha:
            self.script_sha = await self.redis.script_load(self.SCRIPT)
        
        now = time.time()
        result = await self.redis.evalsha(
            self.script_sha,
            1,  # number of keys
            key,  # KEYS[1]
            rate,  # ARGV[1]
            capacity,  # ARGV[2]
            now,  # ARGV[3]
            tokens  # ARGV[4]
        )
        
        return result[0] == 1, result[1]
```

#### 1.2.2 LLM 配额管理器

```python
# src/skyone_shuge/services/quota_manager.py
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio


@dataclass
class QuotaLimit:
    """配额限制配置"""
    daily_tokens: int
    daily_cost_usd: float
    monthly_tokens: int
    monthly_cost_usd: float
    requests_per_minute: int


class LlmQuotaManager:
    """LLM 配额管理器"""
    
    def __init__(self, redis_client, db_session):
        self.redis = redis_client
        self.db = db_session
    
    def _get_quota_key(self, user_id: str, org_id: str = None) -> str:
        """获取配额 Redis key"""
        base = f"quota:llm:{user_id}"
        if org_id:
            base = f"quota:llm:org:{org_id}"
        return base
    
    async def check_quota(
        self,
        user_id: str,
        org_id: str = None,
        estimated_tokens: int = 0,
        estimated_cost: float = 0.0
    ) -> Tuple[bool, str, Dict]:
        """
        检查配额是否允许请求
        Returns:
            (是否允许, 拒绝原因, 配额状态)
        """
        quota_key = self._get_quota_key(user_id, org_id)
        
        # 获取用户配额配置
        quota_config = await self._get_user_quota(user_id, org_id)
        
        # 检查日配额
        daily_used = await self._get_daily_usage(quota_key)
        
        if daily_used['tokens'] + estimated_tokens > quota_config.daily_tokens:
            return False, "Daily token quota exceeded", daily_used
        
        if daily_used['cost'] + estimated_cost > quota_config.daily_cost_usd:
            return False, "Daily cost quota exceeded", daily_used
        
        # 检查月配额
        monthly_used = await self._get_monthly_usage(quota_key)
        
        if monthly_used['tokens'] + estimated_tokens > quota_config.monthly_tokens:
            return False, "Monthly token quota exceeded", monthly_used
        
        if monthly_used['cost'] + estimated_cost > quota_config.monthly_cost_usd:
            return False, "Monthly cost quota exceeded", monthly_used
        
        return True, "OK", daily_used
    
    async def record_usage(
        self,
        user_id: str,
        org_id: str = None,
        tokens: int = 0,
        cost: float = 0.0,
        provider: str = "openai",
        model: str = "gpt-4"
    ):
        """记录 LLM 使用量"""
        quota_key = self._get_quota_key(user_id, org_id)
        
        today = datetime.utcnow().strftime('%Y-%m-%d')
        month = datetime.utcnow().strftime('%Y-%m')
        
        pipe = self.redis.pipeline()
        
        # 记录日使用量
        daily_tokens_key = f"{quota_key}:daily:{today}"
        pipe.hincrby(daily_tokens_key, 'tokens', tokens)
        pipe.hincrbyfloat(daily_tokens_key, 'cost', cost)
        pipe.expire(daily_tokens_key, 86400 * 2)  # 保留 2 天
        
        # 记录月使用量
        monthly_tokens_key = f"{quota_key}:monthly:{month}"
        pipe.hincrby(monthly_tokens_key, 'tokens', tokens)
        pipe.hincrbyfloat(monthly_tokens_key, 'cost', cost)
        pipe.expire(monthly_tokens_key, 86400 * 62)  # 保留 62 天
        
        # 记录总使用量
        total_key = f"{quota_key}:total"
        pipe.hincrby(total_key, 'tokens', tokens)
        pipe.hincrbyfloat(total_key, 'cost', cost)
        
        # 记录详细日志
        detail_key = f"{quota_key}:detail:{today}"
        pipe.lpush(detail_key, f"{datetime.utcnow().isoformat()},{provider},{model},{tokens},{cost}")
        pipe.ltrim(detail_key, 0, 999)  # 保留最近 1000 条
        
        await pipe.execute()
        
        # 检查是否触发告警
        await self._check_alerts(user_id, org_id, tokens, cost)
    
    async def get_quota_status(self, user_id: str, org_id: str = None) -> Dict:
        """获取配额状态"""
        quota_key = self._get_quota_key(user_id, org_id)
        quota_config = await self._get_user_quota(user_id, org_id)
        daily_used = await self._get_daily_usage(quota_key)
        monthly_used = await self._get_monthly_usage(quota_key)
        
        return {
            'config': quota_config,
            'daily': {
                'used_tokens': daily_used['tokens'],
                'used_cost': daily_used['cost'],
                'limit_tokens': quota_config.daily_tokens,
                'limit_cost': quota_config.daily_cost_usd,
                'remaining_tokens': quota_config.daily_tokens - daily_used['tokens'],
                'remaining_cost': quota_config.daily_cost_usd - daily_used['cost']
            },
            'monthly': {
                'used_tokens': monthly_used['tokens'],
                'used_cost': monthly_used['cost'],
                'limit_tokens': quota_config.monthly_tokens,
                'limit_cost': quota_config.monthly_cost_usd,
                'remaining_tokens': quota_config.monthly_tokens - monthly_used['tokens'],
                'remaining_cost': quota_config.monthly_cost_usd - monthly_used['cost']
            }
        }
```

---

### 1.3 多级缓存封装

#### 1.3.1 缓存管理器

```python
# src/skyone_shuge/cache/multi_level.py
from typing import Optional, Any, Callable, TypeVar, Generic
from functools import wraps
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheLevel:
    """缓存层级配置"""
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"


class MultiLevelCache:
    """多级缓存管理器"""
    
    def __init__(self, redis_client=None, memory_size: int = 1000):
        self.redis = redis_client
        self.memory_cache = {}  # LRU 简单实现
        self.memory_size = memory_size
        self.memory_order = []  # 记录访问顺序
    
    def _generate_key(self, namespace: str, *args, **kwargs) -> str:
        """生成缓存 key"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"skyone:cache:{namespace}:{key_hash}"
    
    def _get_from_memory(self, key: str) -> Optional[Any]:
        """从内存缓存获取"""
        if key in self.memory_cache:
            # 移动到末尾（最新访问）
            self.memory_order.remove(key)
            self.memory_order.append(key)
            return self.memory_cache[key]
        return None
    
    def _set_to_memory(self, key: str, value: Any):
        """设置到内存缓存"""
        if key in self.memory_cache:
            self.memory_order.remove(key)
        elif len(self.memory_cache) >= self.memory_size:
            # 淘汰最旧的
            oldest = self.memory_order.pop(0)
            del self.memory_cache[oldest]
        
        self.memory_cache[key] = value
        self.memory_order.append(key)
    
    async def get(
        self,
        key: str,
        levels: list = None
    ) -> Optional[Any]:
        """
        获取缓存
        Args:
            key: 缓存 key
            levels: 查询的层级列表，默认 [MEMORY, REDIS, DATABASE]
        """
        if levels is None:
            levels = [CacheLevel.MEMORY, CacheLevel.REDIS]
        
        # L1: 内存缓存
        if CacheLevel.MEMORY in levels:
            value = self._get_from_memory(key)
            if value is not None:
                logger.debug(f"Cache hit L1: {key}")
                return value
        
        # L2: Redis 缓存
        if CacheLevel.REDIS in levels and self.redis:
            try:
                value = await self.redis.get(key)
                if value:
                    value = json.loads(value)
                    # 回填 L1
                    self._set_to_memory(key, value)
                    logger.debug(f"Cache hit L2: {key}")
                    return value
            except Exception as e:
                logger.error(f"Redis cache get error: {e}")
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        levels: list = None
    ):
        """
        设置缓存
        Args:
            key: 缓存 key
            value: 缓存值
            ttl: 过期时间（秒）
            levels: 写入的层级列表
        """
        if levels is None:
            levels = [CacheLevel.MEMORY, CacheLevel.REDIS]
        
        # L1: 内存缓存
        if CacheLevel.MEMORY in levels:
            self._set_to_memory(key, value)
        
        # L2: Redis 缓存
        if CacheLevel.REDIS in levels and self.redis:
            try:
                await self.redis.setex(
                    key,
                    ttl,
                    json.dumps(value, default=str)
                )
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")
    
    async def delete(self, key: str, levels: list = None):
        """删除缓存"""
        if levels is None:
            levels = [CacheLevel.MEMORY, CacheLevel.REDIS]
        
        if CacheLevel.MEMORY in levels:
            if key in self.memory_cache:
                del self.memory_cache[key]
                self.memory_order.remove(key)
        
        if CacheLevel.REDIS in levels and self.redis:
            try:
                await self.redis.delete(key)
            except Exception as e:
                logger.error(f"Redis cache delete error: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """批量删除匹配 pattern 的缓存"""
        if self.redis:
            try:
                keys = []
                async for key in self.redis.scan_iter(match=pattern):
                    keys.append(key)
                if keys:
                    await self.redis.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} cache keys: {pattern}")
            except Exception as e:
                logger.error(f"Redis pattern invalidate error: {e}")
        
        # 清理内存缓存
        for key in list(self.memory_cache.keys()):
            if pattern.replace('*', '') in key:
                del self.memory_cache[key]
                self.memory_order.remove(key)


def cached(
    namespace: str,
    ttl: int = 3600,
    levels: list = None,
    key_builder: Callable = None
):
    """
    缓存装饰器
    Example:
        @cached("user", ttl=1800)
        async def get_user(user_id: int):
            return await db.get_user(user_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存 key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = f"skyone:cache:{namespace}:{func.__name__}:{args}:{sorted(kwargs.items())}"
            
            # 尝试获取缓存
            cache = get_cache()  # 获取全局缓存实例
            cached_value = await cache.get(cache_key, levels)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 写入缓存
            if result is not None:
                await cache.set(cache_key, result, ttl, levels)
            
            return result
        return wrapper
    return decorator


# 全局缓存实例
_cache_instance: Optional[MultiLevelCache] = None


def get_cache() -> MultiLevelCache:
    """获取全局缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = MultiLevelCache()
    return _cache_instance
```

---

### 1.4 性能优化中间件

#### 1.4.1 数据库连接池管理

```python
# src/skyone_shuge/core/database.py
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool, Pool
from contextlib import contextmanager
from typing import Generator
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库连接池管理器"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self._setup_engine()
    
    def _setup_engine(self):
        """配置数据库引擎"""
        # 根据数据库类型选择连接池
        if 'postgresql' in self.database_url:
            pool_class = QueuePool
            pool_config = {
                'pool_size': 20,
                'max_overflow': 10,
                'pool_pre_ping': True,
                'pool_recycle': 3600,
            }
        else:
            pool_class = QueuePool
            pool_config = {
                'pool_size': 10,
                'max_overflow': 5,
                'pool_pre_ping': True,
            }
        
        self.engine = create_engine(
            self.database_url,
            poolclass=pool_class,
            **pool_config,
            echo=False  # 生产环境关闭 SQL 日志
        )
        
        # 配置事件监听
        self._setup_event_listeners()
        
        # 创建 session factory
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        
        logger.info("Database engine initialized with connection pool")
    
    def _setup_event_listeners(self):
        """配置数据库事件监听"""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """连接创建时"""
            logger.debug("New database connection established")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """连接从池中取出时"""
            logger.debug("Connection checked out from pool")
        
        @event.listents_for(self.engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """连接归还到池时"""
            logger.debug("Connection checked in to pool")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库 session"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_pool_status(self) -> dict:
        """获取连接池状态"""
        pool = self.engine.pool
        return {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'total': pool.size() + pool.overflow()
        }
    
    def close(self):
        """关闭连接池"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection pool closed")
```

#### 1.4.2 异步 I/O 优化

```python
# src/skyone_shuge/core/async_optimization.py
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

logger = logging.getLogger(__name__)


class AsyncOptimizationMiddleware(BaseHTTPMiddleware):
    """异步优化中间件"""
    
    async def dispatch(self, request, call_next):
        # 并发执行多个独立任务
        response = await call_next(request)
        return response


@asynccontextmanager
async def lifespan_optimized(app: FastAPI):
    """优化的应用生命周期管理"""
    # 启动时预热
    await warm_up()
    
    yield
    
    # 关闭时清理
    await cleanup()


async def warm_up():
    """应用启动预热"""
    logger.info("Starting application warm-up...")
    
    # 预热缓存
    asyncio.create_task(warm_up_cache())
    
    # 预热数据库连接
    asyncio.create_task(warm_up_db())
    
    # 预加载配置
    asyncio.create_task(warm_up_config())
    
    logger.info("Application warm-up completed")


async def warm_up_cache():
    """预热缓存"""
    from src.skyone_shuge.cache.multi_level import get_cache
    cache = get_cache()
    # 加载热点数据
    logger.info("Cache warm-up completed")


async def warm_up_db():
    """预热数据库连接"""
    logger.info("Database connection warm-up completed")


async def warm_up_config():
    """预加载配置"""
    logger.info("Configuration warm-up completed")


async def cleanup():
    """应用关闭清理"""
    logger.info("Starting application cleanup...")
    # 关闭连接池
    # 刷新缓存
    # 保存状态
    logger.info("Application cleanup completed")
```

---

### 1.5 ES 搜索封装

#### 1.5.1 Elasticsearch 客户端封装

```python
# src/skyone_shuge/search/elasticsearch_client.py
from typing import List, Dict, Any, Optional
from elasticsearch import AsyncElasticsearch
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""
    total: int
    hits: List[Dict[str, Any]]
    facets: Dict[str, Any]
    suggestions: List[str]
    took_ms: int


class ElasticsearchClient:
    """Elasticsearch 搜索客户端"""
    
    def __init__(self, hosts: List[str], index_prefix: str = "skyone"):
        self.client = AsyncElasticsearch(hosts=hosts)
        self.index_prefix = index_prefix
    
    async def search(
        self,
        index: str,
        query: str,
        filters: Dict[str, Any] = None,
        facets: List[str] = None,
        page: int = 1,
        page_size: int = 20,
        highlight: bool = True
    ) -> SearchResult:
        """
        执行搜索
        Args:
            index: 索引名
            query: 搜索关键词
            filters: 过滤条件
            facets: 分面字段列表
            page: 页码
            page_size: 每页数量
            highlight: 是否高亮
        """
        # 构建查询
        es_query = self._build_query(query, filters)
        
        # 构建聚合（分面搜索）
        aggs = self._build_aggregations(facets) if facets else None
        
        # 高亮配置
        highlight_config = {
            "fields": {
                "content": {},
                "title": {}
            },
            "pre_tags": ["<em>"],
            "post_tags": ["</em>"]
        } if highlight else None
        
        # 执行搜索
        body = {
            "query": es_query,
            "from": (page - 1) * page_size,
            "size": page_size,
            "aggs": aggs,
            "highlight": highlight_config
        }
        
        response = await self.client.search(
            index=f"{self.index_prefix}_{index}",
            body=body
        )
        
        # 解析结果
        hits = []
        for hit in response['hits']['hits']:
            item = {
                '_id': hit['_id'],
                '_score': hit['_score'],
                '_source': hit['_source']
            }
            if 'highlight' in hit:
                item['highlight'] = hit['highlight']
            hits.append(item)
        
        # 解析分面
        facet_results = {}
        if 'aggregations' in response:
            facet_results = self._parse_aggregations(response['aggregations'])
        
        # 解析建议
        suggestions = []
        if 'suggest' in response:
            suggestions = self._parse_suggestions(response['suggest'])
        
        return SearchResult(
            total=response['hits']['total']['value'],
            hits=hits,
            facets=facet_results,
            suggestions=suggestions,
            took_ms=response['took']
        )
    
    def _build_query(self, query: str, filters: Dict[str, Any] = None) -> Dict:
        """构建 ES 查询"""
        must = []
        filter_clauses = []
        
        # 全文搜索
        if query:
            must.append({
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content", "tags^2"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        
        # 过滤条件
        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    filter_clauses.append({"terms": {field: value}})
                elif isinstance(value, dict):
                    filter_clauses.append({"range": {field: value}})
                else:
                    filter_clauses.append({"term": {field: value}})
        
        return {
            "bool": {
                "must": must if must else [{"match_all": {}}],
                "filter": filter_clauses
            }
        }
    
    def _build_aggregations(self, facets: List[str]) -> Dict:
        """构建聚合查询"""
        aggs = {}
        for facet in facets:
            aggs[facet] = {
                "terms": {
                    "field": facet,
                    "size": 20
                }
            }
        return aggs
    
    def _parse_aggregations(self, aggs: Dict) -> Dict[str, List[Dict]]:
        """解析聚合结果"""
        result = {}
        for name, agg in aggs.items():
            if 'buckets' in agg:
                result[name] = [
                    {'key': bucket['key'], 'count': bucket['doc_count']}
                    for bucket in agg['buckets']
                ]
        return result
    
    def _parse_suggestions(self, suggest: Dict) -> List[str]:
        """解析搜索建议"""
        suggestions = []
        for _, suggestion_list in suggest.items():
            for suggestion in suggestion_list:
                if 'options' in suggestion:
                    for option in suggestion['options']:
                        suggestions.append(option['text'])
        return list(set(suggestions))
    
    async def close(self):
        """关闭客户端"""
        await self.client.close()
```

---

### 1.6 LLM 成本追踪服务

#### 1.6.1 LLM 使用量追踪器

```python
# src/skyone_shuge/services/llm_cost_tracker.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)


@dataclass
class LlmUsageRecord:
    """LLM 使用记录"""
    id: int
    user_id: str
    org_id: Optional[str]
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: int
    created_at: datetime


class LlmCostTracker:
    """LLM 成本追踪器"""
    
    # LLM 定价（每 1000 tokens）
    PRICING = {
        'openai': {
            'gpt-4': {'prompt': 0.03, 'completion': 0.06},
            'gpt-4-turbo': {'prompt': 0.01, 'completion': 0.03},
            'gpt-3.5-turbo': {'prompt': 0.0005, 'completion': 0.0015}
        },
        'anthropic': {
            'claude-3-opus': {'prompt': 0.015, 'completion': 0.075},
            'claude-3-sonnet': {'prompt': 0.003, 'completion': 0.015}
        }
    }
    
    def __init__(self, db_session, redis_client):
        self.db = db_session
        self.redis = redis_client
    
    def calculate_cost(self, provider: str, model: str, tokens: Dict[str, int]) -> float:
        """计算 LLM 调用成本"""
        if provider not in self.PRICING:
            logger.warning(f"Unknown provider: {provider}")
            return 0.0
        
        if model not in self.PRICING[provider]:
            logger.warning(f"Unknown model: {model}")
            return 0.0
        
        pricing = self.PRICING[provider][model]
        prompt_cost = (tokens.get('prompt', 0) / 1000) * pricing['prompt']
        completion_cost = (tokens.get('completion', 0) / 1000) * pricing['completion']
        
        return prompt_cost + completion_cost
    
    async def record_usage(
        self,
        user_id: str,
        org_id: Optional[str],
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int
    ) -> LlmUsageRecord:
        """记录 LLM 使用量"""
        total_tokens = prompt_tokens + completion_tokens
        cost = self.calculate_cost(
            provider, model,
            {'prompt': prompt_tokens, 'completion': completion_tokens}
        )
        
        # 保存到数据库
        record = LlmUsageRecord(
            id=0,  #将由数据库生成
            user_id=user_id,
            org_id=org_id,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            created_at=datetime.utcnow()
        )
        
        self.db.add(record)
        await self.db.flush()
        
        # 更新 Redis 实时统计
        await self._update_realtime_stats(user_id, org_id, provider, model, total_tokens, cost)
        
        logger.info(
            f"LLM usage recorded: {provider}/{model}, "
            f"tokens={total_tokens}, cost=${cost:.4f}"
        )
        
        return record
    
    async def _update_realtime_stats(
        self,
        user_id: str,
        org_id: Optional[str],
        provider: str,
        model: str,
        tokens: int,
        cost: float
    ):
        """更新 Redis 实时统计"""
        today = datetime.utcnow().strftime('%Y-%m-%d')
        
        pipe = self.redis.pipeline()
        
        # 用户日统计
        user_key = f"llm:stats:user:{user_id}:{today}"
        pipe.hincrby(user_key, 'requests', 1)
        pipe.hincrby(user_key, 'tokens', tokens)
        pipe.hincrbyfloat(user_key, 'cost', cost)
        pipe.expire(user_key, 86400 * 2)
        
        # 组织日统计
        if org_id:
            org_key = f"llm:stats:org:{org_id}:{today}"
            pipe.hincrby(org_key, 'requests', 1)
            pipe.hincrby(org_key, 'tokens', tokens)
            pipe.hincrbyfloat(org_key, 'cost', cost)
            pipe.expire(org_key, 86400 * 2)
        
        # 提供商统计
        provider_key = f"llm:stats:provider:{provider}:{today}"
        pipe.hincrby(provider_key, 'tokens', tokens)
        pipe.hincrbyfloat(provider_key, 'cost', cost)
        pipe.expire(provider_key, 86400 * 2)
        
        await pipe.execute()
    
    async def get_user_cost_summary(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """获取用户成本汇总"""
        from src.skyone_shuge.models.llm_usage import LlmUsage
        
        records = await self.db.query(LlmUsage).filter(
            and_(
                LlmUsage.user_id == user_id,
                LlmUsage.created_at >= start_date,
                LlmUsage.created_at <= end_date
            )
        ).all()
        
        summary = {
            'total_requests': len(records),
            'total_tokens': sum(r.total_tokens for r in records),
            'total_cost': sum(r.cost_usd for r in records),
            'by_provider': {},
            'by_model': {}
        }
        
        for record in records:
            if record.provider not in summary['by_provider']:
                summary['by_provider'][record.provider] = {'tokens': 0, 'cost': 0}
            summary['by_provider'][record.provider]['tokens'] += record.total_tokens
            summary['by_provider'][record.provider]['cost'] += record.cost_usd
            
            model_key = f"{record.provider}/{record.model}"
            if model_key not in summary['by_model']:
                summary['by_model'][model_key] = {'tokens': 0, 'cost': 0}
            summary['by_model'][model_key]['tokens'] += record.total_tokens
            summary['by_model'][model_key]['cost'] += record.cost_usd
        
        return summary
```

---

## ✅ 二、前端 UI 组件开发

### 2.1 监控仪表盘组件

#### 2.1.1 指标图表组件

```typescript
// frontend/src/components/monitoring/MetricsChart.tsx
import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { Card, Spin, Select, DatePicker } from 'antd';
import moment from 'moment';
import './MetricsChart.less';

const { RangePicker } = DatePicker;

interface MetricsChartProps {
  metricName: string;
  title: string;
  unit?: string;
}

interface DataPoint {
  timestamp: string;
  value: number;
}

export const MetricsChart: React.FC<MetricsChartProps> = ({
  metricName,
  title,
  unit = ''
}) => {
  const [data, setData] = useState<DataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('1h');
  const [period, setPeriod] = useState('5m');

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, [metricName, timeRange, period]);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/v1/metrics/prometheus?metric=${metricName}&range=${timeRange}&period=${period}`
      );
      const result = await response.json();
      setData(result.data.map((d: any) => ({
        timestamp: moment(d.timestamp).format('HH:mm'),
        value: parseFloat(d.value.toFixed(2))
      })));
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="metrics-chart" loading={loading}>
      <div className="chart-header">
        <h3>{title}</h3>
        <div className="chart-controls">
          <Select
            value={timeRange}
            onChange={setTimeRange}
            size="small"
            style={{ width: 100 }}
          >
            <Select.Option value="1h">1小时</Select.Option>
            <Select.Option value="6h">6小时</Select.Option>
            <Select.Option value="24h">24小时</Select.Option>
            <Select.Option value="7d">7天</Select.Option>
          </Select>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="timestamp" stroke="#8c8c8c" fontSize={12} />
          <YAxis
            stroke="#8c8c8c"
            fontSize={12}
            tickFormatter={(v) => `${v}${unit}`}
          />
          <Tooltip
            formatter={(value: number) => [`${value}${unit}`, title]}
            labelFormatter={(label) => `时间: ${label}`}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#1890ff"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
};
```

#### 2.1.2 实时追踪查看器

```typescript
// frontend/src/components/monitoring/TraceViewer.tsx
import React, { useState, useEffect } from 'react';
import { Drawer, Table, Tag, Button, Space, Descriptions, Spin } from 'antd';
import { FullscreenOutlined, CopyOutlined } from '@ant-design/icons';
import './TraceViewer.less';

interface TraceViewerProps {
  traceId: string;
  visible: boolean;
  onClose: () => void;
}

interface Span {
  spanId: string;
  parentSpanId?: string;
  operationName: string;
  serviceName: string;
  duration: number;
  startTime: number;
  endTime: number;
  status: 'ok' | 'error';
  tags: Record<string, string>;
  logs: any[];
}

export const TraceViewer: React.FC<TraceViewerProps> = ({
  traceId,
  visible,
  onClose
}) => {
  const [spans, setSpans] = useState<Span[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSpan, setSelectedSpan] = useState<Span | null>(null);

  useEffect(() => {
    if (visible && traceId) {
      fetchTrace();
    }
  }, [visible, traceId]);

  const fetchTrace = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/traces/${traceId}`);
      const data = await response.json();
      setSpans(data.spans);
    } catch (error) {
      console.error('Failed to fetch trace:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDurationColor = (duration: number) => {
    if (duration < 100) return '#52c41a';
    if (duration < 500) return '#faad14';
    return '#f5222d';
  };

  const columns = [
    {
      title: '操作',
      dataIndex: 'operationName',
      key: 'operationName',
      ellipsis: true
    },
    {
      title: '服务',
      dataIndex: 'serviceName',
      key: 'serviceName',
      width: 150,
      render: (text: string) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '耗时',
      dataIndex: 'duration',
      key: 'duration',
      width: 100,
      render: (duration: number) => (
        <span style={{ color: getDurationColor(duration) }}>
          {duration.toFixed(2)}ms
        </span>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => (
        <Tag color={status === 'ok' ? 'green' : 'red'}>
          {status === 'ok' ? '成功' : '错误'}
        </Tag>
      )
    }
  ];

  return (
    <Drawer
      title="Trace 详情"
      placement="right"
      width={900}
      visible={visible}
      onClose={onClose}
    >
      <Spin spinning={loading}>
        <div className="trace-header">
          <Descriptions size="small" column={3}>
            <Descriptions.Item label="Trace ID">{traceId}</Descriptions.Item>
            <Descriptions.Item label="总耗时">
              {spans.length > 0
                ? (Math.max(...spans.map(s => s.endTime)) - Math.min(...spans.map(s => s.startTime))).toFixed(2)
                : 0}ms
            </Descriptions.Item>
            <Descriptions.Item label="Span 数量">{spans.length}</Descriptions.Item>
          </Descriptions>
        </div>
        
        <Table
          columns={columns}
          dataSource={spans}
          rowKey="spanId"
          size="small"
          onRow={(record) => ({
            onClick: () => setSelectedSpan(record),
            style: { cursor: 'pointer' }
          })}
        />

        {selectedSpan && (
          <div className="span-detail">
            <h4>Span 详情: {selectedSpan.operationName}</h4>
            <Descriptions column={2}>
              <Descriptions.Item label="Span ID">{selectedSpan.spanId}</Descriptions.Item>
              <Descriptions.Item label="Parent Span ID">
                {selectedSpan.parentSpanId || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="开始时间">
                {new Date(selectedSpan.startTime / 1000).toISOString()}
              </Descriptions.Item>
              <Descriptions.Item label="结束时间">
                {new Date(selectedSpan.endTime / 1000).toISOString()}
              </Descriptions.Item>
            </Descriptions>
          </div>
        )}
      </Spin>
    </Drawer>
  );
};
```

---

### 2.2 限流配置面板

```typescript
// frontend/src/pages/RateLimitConfig.tsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Tag,
  Button,
  Modal,
  Form,
  InputNumber,
  Space,
  message,
  Slider,
  Input
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import './RateLimitConfig.less';

interface QuotaConfig {
  id: string;
  name: string;
  type: 'user' | 'organization';
  dailyTokens: number;
  dailyCost: number;
  monthlyTokens: number;
  monthlyCost: number;
  requestsPerMinute: number;
  status: 'active' | 'paused';
}

export const RateLimitConfig: React.FC = () => {
  const [quotas, setQuotas] = useState<QuotaConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingQuota, setEditingQuota] = useState<QuotaConfig | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchQuotas();
  }, []);

  const fetchQuotas = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/rate-limit/quotas');
      const data = await response.json();
      setQuotas(data);
    } catch (error) {
      message.error('Failed to fetch quotas');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (quota: QuotaConfig) => {
    setEditingQuota(quota);
    form.setFieldsValue(quota);
    setModalVisible(true);
  };

  const handleCreate = () => {
    setEditingQuota(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      const url = editingQuota
        ? `/api/v1/rate-limit/quotas/${editingQuota.id}`
        : '/api/v1/rate-limit/quotas';
      const method = editingQuota ? 'PUT' : 'POST';
      
      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
      });
      
      message.success(editingQuota ? 'Quota updated' : 'Quota created');
      setModalVisible(false);
      fetchQuotas();
    } catch (error) {
      message.error('Operation failed');
    }
  };

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name'
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === 'user' ? 'blue' : 'green'}>
          {type === 'user' ? '用户' : '组织'}
        </Tag>
      )
    },
    {
      title: '日 Token 限额',
      dataIndex: 'dailyTokens',
      key: 'dailyTokens',
      render: (val: number) => val.toLocaleString()
    },
    {
      title: '日费用限额',
      dataIndex: 'dailyCost',
      key: 'dailyCost',
      render: (val: number) => `$${val.toFixed(2)}`
    },
    {
      title: '月 Token 限额',
      dataIndex: 'monthlyTokens',
      key: 'monthlyTokens',
      render: (val: number) => val.toLocaleString()
    },
    {
      title: '月费用限额',
      dataIndex: 'monthlyCost',
      key: 'monthlyCost',
      render: (val: number) => `$${val.toFixed(2)}`
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '生效中' : '已暂停'}
        </Tag>
      )
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: QuotaConfig) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Space>
      )
    }
  ];

  return (
    <div className="rate-limit-config">
      <Card
        title="LLM 配额管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            创建配额
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={quotas}
          loading={loading}
          rowKey="id"
        />
      </Card>

      <Modal
        title={editingQuota ? '编辑配额' : '创建配额'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="配额名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          
          <Form.Item name="type" label="配额类型" rules={[{ required: true }]}>
            <Input disabled={!!editingQuota} />
          </Form.Item>

          <div className="form-row">
            <Form.Item name="dailyTokens" label="日 Token 限额" rules={[{ required: true }]}>
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="dailyCost" label="日费用限额 ($)" rules={[{ required: true }]}>
              <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
            </Form.Item>
          </div>

          <div className="form-row">
            <Form.Item name="monthlyTokens" label="月 Token 限额" rules={[{ required: true }]}>
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="monthlyCost" label="月费用限额 ($)" rules={[{ required: true }]}>
              <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
            </Form.Item>
          </div>

          <Form.Item name="requestsPerMinute" label="每分钟请求限制">
            <Slider min={1} max={100} marks={{ 1: '1', 50: '50', 100: '100' }} />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
              <Button onClick={() => setModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
```

---

### 2.3 缓存管理界面

```typescript
// frontend/src/pages/CacheManagement.tsx
import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, Space, message, Progress, Statistic, Row, Col } from 'antd';
import { DeleteOutlined, ReloadOutlined, DatabaseOutlined } from '@ant-design/icons';
import './CacheManagement.less';

interface CacheStats {
  memory: {
    size: number;
    capacity: number;
    hits: number;
    misses: number;
    hitRate: number;
  };
  redis: {
    keys: number;
    memory: number;
    hits: number;
    misses: number;
    hitRate: number;
  };
}

export const CacheManagement: React.FC = () => {
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/cache/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      message.error('Failed to fetch cache stats');
    } finally {
      setLoading(false);
    }
  };

  const handleInvalidate = async (pattern: string) => {
    try {
      await fetch(`/api/v1/cache/invalidate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pattern })
      });
      message.success('Cache invalidated');
      fetchStats();
    } catch (error) {
      message.error('Invalidate failed');
    }
  };

  const handleWarmUp = async () => {
    try {
      await fetch('/api/v1/cache/warmup', { method: 'POST' });
      message.success('Cache warm-up started');
    } catch (error) {
      message.error('Warm-up failed');
    }
  };

  return (
    <div className="cache-management">
      <Row gutter={16} className="stats-row">
        <Col span={12}>
          <Card title="内存缓存 (L1)">
            {stats && (
              <>
                <Progress
                  percent={Math.round((stats.memory.size / stats.memory.capacity) * 100)}
                  format={() => `${stats.memory.size}/${stats.memory.capacity}`}
                />
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="命中率"
                      value={stats.memory.hitRate}
                      suffix="%"
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="命中次数"
                      value={stats.memory.hits}
                    />
                  </Col>
                </Row>
              </>
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Redis 缓存 (L2)">
            {stats && (
              <>
                <Statistic
                  title="键数量"
                  value={stats.redis.keys}
                  prefix={<DatabaseOutlined />}
                />
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="命中率"
                      value={stats.redis.hitRate}
                      suffix="%"
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="内存使用"
                      value={stats.redis.memory}
                      suffix="MB"
                    />
                  </Col>
                </Row>
              </>
            )}
          </Card>
        </Col>
      </Row>

      <Card
        title="缓存操作"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={handleWarmUp}>
              预热缓存
            </Button>
            <Button type="primary" danger icon={<DeleteOutlined />} onClick={() => handleInvalidate('*')}>
              清空所有缓存
            </Button>
          </Space>
        }
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            <Button onClick={() => handleInvalidate('user:*')}>清除用户缓存</Button>
            <Button onClick={() => handleInvalidate('document:*')}>清除文档缓存</Button>
            <Button onClick={() => handleInvalidate('search:*')}>清除搜索缓存</Button>
          </Space>
        </Space>
      </Card>
    </div>
  );
};
```

---

## ✅ 三、单元测试与集成测试

### 3.1 pytest 配置

```ini
# tests/pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --disable-warnings
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    redis: Tests requiring Redis
    db: Tests requiring database
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

### 3.2 测试用例示例

#### 3.2.1 限流器测试

```python
# tests/unit/test_rate_limiter.py
import pytest
import time
from src.skyone_shuge.middleware.rate_limiter import TokenBucket


class TestTokenBucket:
    """令牌桶测试"""
    
    def test_initial_tokens(self):
        """测试初始令牌数量"""
        bucket = TokenBucket(rate=10, capacity=100)
        assert bucket.tokens == 100
    
    def test_consume_success(self):
        """测试成功消费令牌"""
        bucket = TokenBucket(rate=10, capacity=100)
        allowed, remaining = bucket.consume(1)
        assert allowed is True
        assert remaining == 99
    
    def test_consume_insufficient_tokens(self):
        """测试令牌不足"""
        bucket = TokenBucket(rate=1, capacity=1)
        bucket.tokens = 0
        allowed, remaining = bucket.consume(1)
        assert allowed is False
        assert remaining == 0
    
    def test_refill_tokens(self):
        """测试令牌补充"""
        bucket = TokenBucket(rate=10, capacity=100)
        bucket.tokens = 50
        bucket.last_update = time.time() - 1  # 1秒前
        bucket.consume(0)  # 触发补充
        # 应该补充约 10 个令牌
        assert bucket.tokens >= 55
    
    def test_capacity_limit(self):
        """测试容量限制"""
        bucket = TokenBucket(rate=100, capacity=100)
        bucket.last_update = time.time() - 10  # 10秒前
        bucket.consume(0)
        # 不应该超过容量
        assert bucket.tokens <= 100


class TestTokenBucketConcurrency:
    """令牌桶并发测试"""
    
    def test_concurrent_consume(self):
        """测试并发消费"""
        import threading
        
        bucket = TokenBucket(rate=1000, capacity=1000)
        results = []
        
        def consume():
            allowed, _ = bucket.consume(1)
            results.append(allowed)
        
        threads = [threading.Thread(target=consume) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 应该有约 900 次成功（考虑补充）
        success_count = sum(results)
        assert success_count >= 850  # 允许一定误差
```

#### 3.2.2 LLM 成本计算测试

```python
# tests/unit/test_llm_cost_tracker.py
import pytest
from src.skyone_shuge.services.llm_cost_tracker import LlmCostTracker


class TestLlmCostTracker:
    """LLM 成本追踪测试"""
    
    def test_calculate_cost_gpt4(self):
        """测试 GPT-4 成本计算"""
        tracker = LlmCostTracker(db_session=None, redis_client=None)
        
        tokens = {'prompt': 1000, 'completion': 500}
        cost = tracker.calculate_cost('openai', 'gpt-4', tokens)
        
        # GPT-4: prompt $0.03/1k, completion $0.06/1k
        expected = (1000 / 1000) * 0.03 + (500 / 1000) * 0.06
        assert cost == pytest.approx(expected, rel=0.01)
    
    def test_calculate_cost_gpt35(self):
        """测试 GPT-3.5-Turbo 成本计算"""
        tracker = LlmCostTracker(db_session=None, redis_client=None)
        
        tokens = {'prompt': 1000, 'completion': 1000}
        cost = tracker.calculate_cost('openai', 'gpt-3.5-turbo', tokens)
        
        # GPT-3.5-Turbo: prompt $0.0005/1k, completion $0.0015/1k
        expected = (1000 / 1000) * 0.0005 + (1000 / 1000) * 0.0015
        assert cost == pytest.approx(expected, rel=0.01)
    
    def test_calculate_cost_unknown_provider(self):
        """测试未知提供商"""
        tracker = LlmCostTracker(db_session=None, redis_client=None)
        
        cost = tracker.calculate_cost('unknown', 'gpt-4', {'prompt': 100, 'completion': 100})
        assert cost == 0.0
    
    def test_calculate_cost_unknown_model(self):
        """测试未知模型"""
        tracker = LlmCostTracker(db_session=None, redis_client=None)
        
        cost = tracker.calculate_cost('openai', 'unknown-model', {'prompt': 100, 'completion': 100})
        assert cost == 0.0
```

#### 3.2.3 多级缓存测试

```python
# tests/unit/test_multi_level_cache.py
import pytest
import asyncio
from src.skyone_shuge.cache.multi_level import MultiLevelCache, CacheLevel


class TestMultiLevelCache:
    """多级缓存测试"""
    
    @pytest.fixture
    def cache(self):
        """创建缓存实例"""
        return MultiLevelCache(memory_size=100)
    
    def test_memory_cache_set_get(self, cache):
        """测试内存缓存设置和获取"""
        asyncio.run(cache.set('test_key', 'test_value', levels=[CacheLevel.MEMORY]))
        result = asyncio.run(cache.get('test_key', levels=[CacheLevel.MEMORY]))
        assert result == 'test_value'
    
    def test_memory_cache_lru_eviction(self):
        """测试 LRU 淘汰"""
        cache = MultiLevelCache(memory_size=3)
        
        asyncio.run(cache.set('key1', 'value1', levels=[CacheLevel.MEMORY]))
        asyncio.run(cache.set('key2', 'value2', levels=[CacheLevel.MEMORY]))
        asyncio.run(cache.set('key3', 'value3', levels=[CacheLevel.MEMORY]))
        
        # 添加第4个，应该淘汰 key1
        asyncio.run(cache.set('key4', 'value4', levels=[CacheLevel.MEMORY]))
        
        result = asyncio.run(cache.get('key1', levels=[CacheLevel.MEMORY]))
        assert result is None  # key1 应该被淘汰
        assert asyncio.run(cache.get('key4', levels=[CacheLevel.MEMORY])) == 'value4'
    
    def test_cache_delete(self, cache):
        """测试缓存删除"""
        asyncio.run(cache.set('test_key', 'test_value', levels=[CacheLevel.MEMORY]))
        asyncio.run(cache.delete('test_key', levels=[CacheLevel.MEMORY]))
        result = asyncio.run(cache.get('test_key', levels=[CacheLevel.MEMORY]))
        assert result is None
    
    def test_key_generation(self, cache):
        """测试 key 生成"""
        key1 = cache._generate_key('namespace', 'arg1', kwarg1='value1')
        key2 = cache._generate_key('namespace', 'arg1', kwarg1='value1')
        key3 = cache._generate_key('namespace', 'arg2', kwarg1='value1')
        
        assert key1 == key2  # 相同参数生成相同 key
        assert key1 != key3  # 不同参数生成不同 key
        assert key1.startswith('skyone:cache:namespace:')  # 包含命名空间
```

### 3.3 集成测试示例

```python
# tests/integration/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope='module')
def test_client():
    """创建测试客户端"""
    from src.main import app
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope='module')
def db_session():
    """创建测试数据库会话"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class TestHealthEndpoints:
    """健康检查端点测试"""
    
    def test_health_check(self, test_client):
        """测试健康检查端点"""
        response = test_client.get('/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
    
    def test_ready_check(self, test_client):
        """测试就绪检查端点"""
        response = test_client.get('/ready')
        assert response.status_code == 200


class TestSearchEndpoints:
    """搜索端点集成测试"""
    
    def test_search_success(self, test_client):
        """测试搜索成功"""
        response = test_client.post('/api/v1/search', json={
            'query': 'test query',
            'page': 1,
            'page_size': 10
        })
        assert response.status_code == 200
        data = response.json()
        assert 'total' in data
        assert 'hits' in data
    
    def test_search_with_filters(self, test_client):
        """测试带过滤条件的搜索"""
        response = test_client.post('/api/v1/search', json={
            'query': 'test',
            'filters': {
                'category': 'document',
                'tags': ['important']
            }
        })
        assert response.status_code == 200


class TestRateLimitIntegration:
    """限流集成测试"""
    
    def test_rate_limit_headers(self, test_client):
        """测试限流响应头"""
        response = test_client.get('/api/v1/search')
        assert 'X-RateLimit-Limit' in response.headers
        assert 'X-RateLimit-Remaining' in response.headers
    
    def test_rate_limit_exceeded(self, test_client):
        """测试超出限流"""
        # 发送大量请求直到被限流
        for _ in range(150):
            response = test_client.get('/api/v1/search')
            if response.status_code == 429:
                assert True
                return
        pytest.fail('Should have been rate limited')
```

---

## 📊 四、部署与配置

### 4.1 环境变量配置

```bash
# .env.production

# 应用配置
APP_NAME=skyone-shuge
APP_ENV=production
LOG_LEVEL=info

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/skyone
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis 配置
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=20

# Elasticsearch 配置
ELASTICSEARCH_HOSTS=http://localhost:9200
ELASTICSEARCH_INDEX_PREFIX=skyone

# 监控配置
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
OTLP_ENDPOINT=http://localhost:4317

# LLM 提供商配置
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# 限流配置
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT_RPM=100

# 缓存配置
CACHE_ENABLED=true
CACHE_L1_SIZE=1000
CACHE_L2_TTL=3600
```

### 4.2 Docker Compose 扩展

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.45.0
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:10.0.0
    ports:
      - "3000:3000"
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  alertmanager:
    image: prom/alertmanager:v0.26.0
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml

  jaeger:
    image: jaegertracing/all-in-one:1.50
    ports:
      - "16686:16686"
      - "6831:6831/udp"
      - "4317:4317"

volumes:
  prometheus_data:
  grafana_data:
```

---

## ✅ 验收标准

### 后端模块
- [ ] 监控 SDK 正确采集和暴露指标
- [ ] OpenTelemetry 链路追踪正常工作
- [ ] 限流中间件正确限制请求
- [ ] 多级缓存正确工作并可配置
- [ ] LLM 成本追踪准确记录使用量

### 前端组件
- [ ] 监控仪表盘正确显示指标
- [ ] 限流配置面板可正常配置
- [ ] 缓存管理界面可查看状态和操作
- [ ] 搜索控制台正常工作

### 测试
- [ ] 单元测试覆盖核心模块
- [ ] 集成测试覆盖主要 API
- [ ] 测试覆盖率 >= 70%
