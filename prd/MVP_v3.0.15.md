# 天一阁 PRD v3.0.15

**版本**: v3.0.15
**日期**: 2026-04-04
**阶段**: 监控与可观测性 + API 限流与成本控制 + 多级缓存架构 + 性能优化架构 + 高级搜索增强架构 + LLM 成本追踪与预算控制

---

## 📋 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0.15 | 2026-04-04 | 监控与可观测性架构 + API 限流与成本控制架构 + 多级缓存架构 + 性能优化架构 + 高级搜索增强架构 + LLM 成本追踪与预算控制 |
| v3.0.14 | 2026-04-03 | 智能推荐系统 + 文档版本对比 + 自动化工作流 + 高级分析报告 + 多语言支持完善 |
| v3.0.13 | 2026-03-30 | 移动端适配 + AI 辅助写作 + 知识图谱可视化 + 高级权限管理 + 数据备份与恢复 |

---

## 🎯 本次迭代目标

### 核心交付物
- [ ] **监控与可观测性架构**: Prometheus + Grafana 指标采集、OpenTelemetry 分布式追踪、ELK 结构化日志、告警规则与通知渠道
- [ ] **API 限流与成本控制架构**: 令牌桶限流算法、用户/组织级别限流、LLM API 调用配额管理、成本实时计算与预警
- [ ] **多级缓存架构**: 应用层内存缓存（Cachette/LRU）、Redis 分布式缓存、数据库查询缓存、缓存预热与失效策略
- [ ] **性能优化架构**: PostgreSQL 连接池（PgBouncer）、Redis 连接池优化、数据库查询分析与优化、异步 I/O 与并发控制
- [ ] **高级搜索增强架构**: Elasticsearch 分面搜索（Facet Search）、搜索词分析与建议、搜索分析报表、个性化搜索排序
- [ ] **LLM 成本追踪与预算控制**: LLM API 使用量统计、成本分摊到用户/组织、预算阈值与告警、成本优化建议

---

## ✅ 一、监控与可观测性架构

### 1.1 可观测性架构概览

```typescript
// types/observability.ts
export interface ObservabilityConfig {
  metrics: MetricsConfig;
  tracing: TracingConfig;
  logging: LoggingConfig;
  alerting: AlertingConfig;
}

export interface MetricsConfig {
  enabled: boolean;
  prometheus: {
    port: number;
    path: string;
    scrape_interval_ms: number;
  };
  grafana: {
    dashboard_dir: string;
    datasources: GrafanaDatasource[];
  };
  collectors: MetricCollector[];
}

export interface GrafanaDatasource {
  name: string;
  type: 'prometheus' | 'influxdb' | 'elasticsearch';
  url: string;
  access: 'proxy' | 'direct';
}

export interface MetricCollector {
  name: string;
  type: 'counter' | 'gauge' | 'histogram' | 'summary';
  labels: string[];
  description: string;
}

export interface TracingConfig {
  enabled: boolean;
  service_name: string;
  otlp: {
    endpoint: string;
    insecure: boolean;
  };
  sampling: {
    type: 'fixed' | 'rate' | 'adaptive';
    rate?: number;
    adaptive?: AdaptiveSamplingConfig;
  };
  propagation: ContextPropagation[];
}

export interface AdaptiveSamplingConfig {
  min_rate: number;
  max_rate: number;
  target_rps: number;
}

export type ContextPropagation = 'tracecontext' | 'baggage' | 'b3' | 'jaeger';

export interface LoggingConfig {
  level: LogLevel;
  format: 'json' | 'text' | 'pretty';
  outputs: LogOutput[];
  sampling: LogSamplingConfig;
}

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';

export interface LogOutput {
  type: 'stdout' | 'file' | 'elasticsearch' | 'loki';
  level?: LogLevel[];
  filters?: LogFilter[];
}

export interface LogFilter {
  field: string;
  operator: 'eq' | 'neq' | 'contains' | 'regex';
  value: string;
}

export interface LogSamplingConfig {
  enabled: boolean;
  debug_rate: number;
  error_burst: number;
}

export interface AlertingConfig {
  enabled: boolean;
  routes: AlertRoute[];
  receivers: AlertReceiver[];
  rules: AlertRule[];
  mute_times: MuteTime[];
}

export interface AlertRoute {
  receiver: string;
  matchers: AlertMatcher[];
  group_by: string[];
  continue: boolean;
}

export interface AlertMatcher {
  label: string;
  operator: '=' | '!=' | '=~' | '!~';
  value: string;
}

export interface AlertReceiver {
  name: string;
  type: 'email' | 'slack' | 'webhook' | 'pagerduty' | 'feishu';
  config: Record<string, unknown>;
}

export interface AlertRule {
  name: string;
  expr: string;
  for: string;
  labels: Record<string, string>;
  annotations: Record<string, string>;
  severity: 'critical' | 'warning' | 'info';
}

export interface MuteTime {
  name: string;
  start_time: string;
  end_time: string;
  weekdays?: string[];
}
```

### 1.2 Prometheus 指标定义

```typescript
// services/metrics/MetricsCollector.ts
export const METRIC_NAMES = {
  // HTTP 指标
  HTTP_REQUESTS_TOTAL: 'http_requests_total',
  HTTP_REQUEST_DURATION_SECONDS: 'http_request_duration_seconds',
  HTTP_REQUESTS_IN_FLIGHT: 'http_requests_in_flight',

  // 业务指标
  LLM_API_CALLS_TOTAL: 'llm_api_calls_total',
  LLM_API_COST_USD: 'llm_api_cost_usd',
  LLM_API_LATENCY_SECONDS: 'llm_api_latency_seconds',
  LLM_API_ERRORS_TOTAL: 'llm_api_errors_total',

  // 搜索指标
  SEARCH_REQUESTS_TOTAL: 'search_requests_total',
  SEARCH_LATENCY_SECONDS: 'search_latency_seconds',
  SEARCH_FACET_REQUESTS_TOTAL: 'search_facet_requests_total',

  // 缓存指标
  CACHE_HIT_RATIO: 'cache_hit_ratio',
  CACHE_OPERATIONS_TOTAL: 'cache_operations_total',
  CACHE_MEMORY_BYTES: 'cache_memory_bytes',

  // 数据库指标
  DB_POOL_CONNECTIONS: 'db_pool_connections',
  DB_QUERY_DURATION_SECONDS: 'db_query_duration_seconds',
  DB_TRANSACTION_DURATION_SECONDS: 'db_transaction_duration_seconds',

  // 连接池指标
  REDIS_POOL_CONNECTIONS: 'redis_pool_connections',
  REDIS_POOL_WAIT_SECONDS: 'redis_pool_wait_seconds',

  // 限流指标
  RATE_LIMIT_TOKENS: 'rate_limit_tokens',
  RATE_LIMIT_REJECTED_TOTAL: 'rate_limit_rejected_total',

  // 用户指标
  ACTIVE_USERS_GAUGE: 'active_users_gauge',
  USER_API_CALLS_TOTAL: 'user_api_calls_total',
} as const;

export interface HttpMetricsLabels {
  method: string;
  path: string;
  status_code: string;
  user_type?: string;
}

export interface LlmMetricsLabels {
  provider: string;
  model: string;
  operation: 'chat' | 'embedding' | 'completion';
  error_type?: string;
}

export interface CacheMetricsLabels {
  cache_layer: 'memory' | 'redis' | 'db';
  cache_name: string;
  operation: 'get' | 'set' | 'delete' | 'hit' | 'miss';
}
```

### 1.3 指标采集服务实现

```typescript
// services/metrics/PrometheusMetricsService.ts
import { Counter, Gauge, Histogram, Registry } from 'prom-client';
import { METRIC_NAMES } from './MetricsCollector';

export class PrometheusMetricsService {
  private registry: Registry;
  private httpRequestsTotal: Counter<string>;
  private httpRequestDuration: Histogram<string>;
  private httpRequestsInFlight: Gauge<string>;
  private llmApiCallsTotal: Counter<string>;
  private llmApiCostUsd: Counter<string>;
  private llmApiLatency: Histogram<string>;
  private llmApiErrorsTotal: Counter<string>;
  private cacheHitRatio: Gauge<string>;
  private dbPoolConnections: Gauge<string>;
  private dbQueryDuration: Histogram<string>;
  private rateLimitRejected: Counter<string>;
  private activeUsers: Gauge<string>;

  constructor(config: MetricsConfig) {
    this.registry = new Registry();
    this.registry.setDefaultLabels({ app: 'skyone-shuge' });

    // HTTP 指标
    this.httpRequestsTotal = new Counter({
      name: METRIC_NAMES.HTTP_REQUESTS_TOTAL,
      help: 'Total HTTP requests',
      labelNames: ['method', 'path', 'status_code', 'user_type'],
      registers: [this.registry],
    });

    this.httpRequestDuration = new Histogram({
      name: METRIC_NAMES.HTTP_REQUEST_DURATION_SECONDS,
      help: 'HTTP request duration in seconds',
      labelNames: ['method', 'path'],
      buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
      registers: [this.registry],
    });

    this.httpRequestsInFlight = new Gauge({
      name: METRIC_NAMES.HTTP_REQUESTS_IN_FLIGHT,
      help: 'Number of HTTP requests currently in flight',
      registers: [this.registry],
    });

    // LLM 指标
    this.llmApiCallsTotal = new Counter({
      name: METRIC_NAMES.LLM_API_CALLS_TOTAL,
      help: 'Total LLM API calls',
      labelNames: ['provider', 'model', 'operation'],
      registers: [this.registry],
    });

    this.llmApiCostUsd = new Counter({
      name: METRIC_NAMES.LLM_API_COST_USD,
      help: 'Total LLM API cost in USD',
      labelNames: ['provider', 'model', 'operation'],
      registers: [this.registry],
    });

    this.llmApiLatency = new Histogram({
      name: METRIC_NAMES.LLM_API_LATENCY_SECONDS,
      help: 'LLM API latency in seconds',
      labelNames: ['provider', 'model', 'operation'],
      buckets: [0.5, 1, 2, 5, 10, 30, 60, 120],
      registers: [this.registry],
    });

    this.llmApiErrorsTotal = new Counter({
      name: METRIC_NAMES.LLM_API_ERRORS_TOTAL,
      help: 'Total LLM API errors',
      labelNames: ['provider', 'model', 'error_type'],
      registers: [this.registry],
    });

    // 缓存指标
    this.cacheHitRatio = new Gauge({
      name: METRIC_NAMES.CACHE_HIT_RATIO,
      help: 'Cache hit ratio by layer',
      labelNames: ['cache_layer', 'cache_name'],
      registers: [this.registry],
    });

    // 数据库连接池指标
    this.dbPoolConnections = new Gauge({
      name: METRIC_NAMES.DB_POOL_CONNECTIONS,
      help: 'Database pool connections',
      labelNames: ['state'],
      registers: [this.registry],
    });

    this.dbQueryDuration = new Histogram({
      name: METRIC_NAMES.DB_QUERY_DURATION_SECONDS,
      help: 'Database query duration in seconds',
      labelNames: ['query_type', 'table'],
      buckets: [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1],
      registers: [this.registry],
    });

    // 限流指标
    this.rateLimitRejected = new Counter({
      name: METRIC_NAMES.RATE_LIMIT_REJECTED_TOTAL,
      help: 'Total requests rejected by rate limiter',
      labelNames: ['user_id', 'tier', 'reason'],
      registers: [this.registry],
    });

    // 用户指标
    this.activeUsers = new Gauge({
      name: METRIC_NAMES.ACTIVE_USERS_GAUGE,
      help: 'Number of active users',
      labelNames: ['period'],
      registers: [this.registry],
    });
  }

  async getMetrics(): Promise<string> {
    return this.registry.metrics();
  }

  // HTTP 中间件记录
  recordHttpRequest(
    method: string,
    path: string,
    statusCode: number,
    durationMs: number,
    userType?: string
  ): void {
    this.httpRequestsTotal.inc({ method, path, status_code: statusCode.toString(), user_type: userType });
    this.httpRequestDuration.observe({ method, path }, durationMs / 1000);
  }

  // LLM 调用记录
  recordLlmCall(
    provider: string,
    model: string,
    operation: string,
    costUsd: number,
    latencyMs: number,
    error?: string
  ): void {
    this.llmApiCallsTotal.inc({ provider, model, operation });
    this.llmApiCostUsd.inc({ provider, model, operation }, costUsd);
    this.llmApiLatency.observe({ provider, model, operation }, latencyMs / 1000);
    if (error) {
      this.llmApiErrorsTotal.inc({ provider, model, error_type: error });
    }
  }

  // 缓存命中率记录
  recordCacheMetrics(
    layer: 'memory' | 'redis' | 'db',
    name: string,
    hits: number,
    misses: number
  ): void {
    const total = hits + misses;
    const ratio = total > 0 ? hits / total : 0;
    this.cacheHitRatio.set({ cache_layer: layer, cache_name: name }, ratio);
  }

  // 数据库查询记录
  recordDbQuery(queryType: string, table: string, durationMs: number): void {
    this.dbQueryDuration.observe({ query_type: queryType, table }, durationMs / 1000);
  }

  // 限流拒绝记录
  recordRateLimitReject(userId: string, tier: string, reason: string): void {
    this.rateLimitRejected.inc({ user_id: userId, tier, reason });
  }
}
```

### 1.4 OpenTelemetry 追踪集成

```typescript
// services/tracing/OpenTelemetryService.ts
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { HttpInstrumentation } from '@opentelemetry/instrumentation-http';
import { ExpressInstrumentation } from '@opentelemetry/instrumentation-express';
import { PgInstrumentation } from '@opentelemetry/instrumentation-pg';
import { RedisInstrumentation } from '@opentelemetry/instrumentation-redis-4';
import { LlmInstrumentation } from '@arize-ai/opentelemetry-instrumentation-llm';
import { trace, context, SpanStatusCode, Span } from '@opentelemetry/api';

export interface TracingServiceConfig {
  serviceName: string;
  otlpEndpoint: string;
  samplingRate: number;
  enabled: boolean;
}

export class OpenTelemetryService {
  private sdk: NodeSDK;
  private tracer: ReturnType<typeof trace.getTracer>;

  constructor(config: TracingServiceConfig) {
    const resource = new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: config.serviceName,
      [SemanticResourceAttributes.SERVICE_VERSION]: '3.0.15',
      environment: process.env.NODE_ENV || 'development',
    });

    const traceExporter = new OTLPTraceExporter({
      url: `${config.otlpEndpoint}/v1/traces`,
    });

    this.sdk = new NodeSDK({
      resource,
      spanProcessor: new BatchSpanProcessor(traceExporter),
      instrumentations: [
        new HttpInstrumentation({
          ignoreIncomingPaths: ['/health', '/metrics', '/ready'],
        }),
        new ExpressInstrumentation(),
        new PgInstrumentation(),
        new RedisInstrumentation(),
        new LlmInstrumentation({
          providers: ['openai', 'anthropic'],
          captureContent: true,
        }),
      ],
    });

    this.tracer = trace.getTracer(config.serviceName, '3.0.15');
  }

  async start(): Promise<void> {
    await this.sdk.start();
    console.log('OpenTelemetry SDK started');
  }

  async shutdown(): Promise<void> {
    await this.sdk.shutdown();
  }

  createSpan<T>(
    name: string,
    attributes: Record<string, string | number | boolean>,
    fn: (span: Span) => Promise<T>
  ): Promise<T> {
    return this.tracer.startActiveSpan(name, { attributes }, async (span) => {
      try {
        const result = await fn(span);
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (error) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error instanceof Error ? error.message : 'Unknown error',
        });
        span.recordException(error as Error);
        throw error;
      } finally {
        span.end();
      }
    });
  }

  getCurrentSpan(): Span | undefined {
    return trace.getActiveSpan();
  }

  addSpanAttributes(attributes: Record<string, string | number | boolean>): void {
    const span = this.getCurrentSpan();
    if (span) {
      span.setAttributes(attributes);
    }
  }
}
```

### 1.5 结构化日志服务

```typescript
// services/logging/StructuredLogger.ts
import pino from 'pino';
import { ElasticsearchSink } from 'pino-elasticsearch';
import { LokiSink } from 'pino-loki';

export interface LogContext {
  requestId: string;
  userId?: string;
  organizationId?: string;
  traceId?: string;
  spanId?: string;
  operation?: string;
  durationMs?: number;
  metadata?: Record<string, unknown>;
}

export class StructuredLogger {
  private logger: pino.Logger;

  constructor(config: LoggingConfig) {
    const sinks: pino.DestinationStream[] = [];

    for (const output of config.outputs) {
      switch (output.type) {
        case 'elasticsearch':
          sinks.push(
            new ElasticsearchSink({
              index: 'skyone-shuge-logs',
             /node: output.config?.['node'] || 'http://localhost:9200',
              flushBytes: 1000,
            })
          );
          break;
        case 'loki':
          sinks.push(
            new LokiSink({
              host: output.config?.['host'] || 'http://localhost:3100',
              labels: { app: 'skyone-shuge', version: '3.0.15' },
            })
          );
          break;
        case 'file':
          sinks.push(
            pino.destination({
              dest: output.config?.['path'] || '/var/log/skyone-shuge/app.log',
              sync: false,
            })
          );
          break;
        default:
          sinks.push(pino.destination({ dest: 1, sync: false }));
      }
    }

    this.logger = pino({
      level: config.level || 'info',
      formatters: {
        level: (label) => ({ level: label }),
        bindings: () => ({
          service: 'skyone-shuge',
          version: '3.0.15',
          env: process.env.NODE_ENV || 'development',
        }),
      },
      timestamp: () => `,"@timestamp":"${new Date().toISOString()}"`,
      ...(config.format === 'pretty' && { transport: { target: 'pino-pretty' } }),
    }, pino.multistream(sinks));
  }

  child(bindings: LogContext): StructuredLogger {
    const childLogger = this.logger.child(bindings);
    const child = Object.create(this);
    child.logger = childLogger;
    return child;
  }

  info(message: string, context?: Partial<LogContext>): void {
    this.logger.info({ ...context }, message);
  }

  warn(message: string, context?: Partial<LogContext>): void {
    this.logger.warn({ ...context }, message);
  }

  error(message: string, error?: Error, context?: Partial<LogContext>): void {
    this.logger.error({ ...context, error: { message: error?.message, stack: error?.stack } }, message);
  }

  debug(message: string, context?: Partial<LogContext>): void {
    this.logger.debug({ ...context }, message);
  }

  fatal(message: string, context?: Partial<LogContext>): void {
    this.logger.fatal({ ...context }, message);
  }

  // 业务日志方法
  logSearch(query: string, userId: string, durationMs: number, resultCount: number): void {
    this.info('Search executed', { operation: 'search', metadata: { query, resultCount, durationMs }, userId, durationMs });
  }

  logLlmCall(provider: string, model: string, tokens: number, costUsd: number, latencyMs: number): void {
    this.info('LLM API call', { operation: 'llm_call', metadata: { provider, model, tokens, costUsd, latencyMs }, durationMs: latencyMs });
  }

  logCacheOperation(operation: 'hit' | 'miss' | 'set' | 'delete', key: string, layer: string): void {
    this.debug('Cache operation', { operation: 'cache', metadata: { cacheOp: operation, key, layer } });
  }

  logRateLimit(userId: string, tier: string, limit: number, current: number): void {
    this.warn('Rate limit approached', { operation: 'rate_limit', userId, metadata: { tier, limit, current } });
  }
}
```

### 1.6 告警规则配置

```yaml
# config/alerts/v3.0.15/alerts.yaml
groups:
  - name: skyone-shuge.lLm
    rules:
      - alert: LLMHighErrorRate
        expr: |
          rate(llm_api_errors_total[5m]) / rate(llm_api_calls_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
          team: ai
        annotations:
          summary: "LLM API 错误率超过 5%"
          description: "Provider {{ $labels.provider }}, Model {{ $labels.model }} 错误率: {{ $value | humanizePercentage }}"

      - alert: LLMCostOverBudget
        expr: |
          llm_api_cost_usd / on(org_id) group_left(budget_limit) llm_budget_limit > 0.9
        for: 5m
        labels:
          severity: warning
          team: finance
        annotations:
          summary: "LLM 成本达到预算 90%"
          description: "组织 {{ $labels.org_id }} LLM 成本已达 ${{ $value | humanize }}, 超过预算 90%"

      - alert: LLMHighLatency
        expr: |
          histogram_quantile(0.95, rate(llm_api_latency_seconds_bucket[5m])) > 30
        for: 5m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "LLM API P95 延迟超过 30 秒"
          description: "Model {{ $labels.model }} P95 延迟: {{ $value | humanizeDuration }}"

  - name: skyone-shuge.infrastructure
    rules:
      - alert: HighCacheMissRate
        expr: |
          cache_hit_ratio < 0.6
        for: 10m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "缓存命中率低于 60%"
          description: "缓存层 {{ $labels.cache_layer }}, 名称 {{ $labels.cache_name }}, 命中率: {{ $value }}"

      - alert: DatabasePoolExhausted
        expr: |
          db_pool_connections{state="used"} / on(instance) db_pool_connections{state="total"} > 0.9
        for: 5m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "数据库连接池接近耗尽"
          description: "实例 {{ $labels.instance }} 连接池使用率: {{ $value | humanizePercentage }}"

      - alert: HighRateLimitRejection
        expr: |
          rate(rate_limit_rejected_total[5m]) > 100
        for: 5m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "限流拒绝率异常升高"
          description: "最近 5 分钟被拒绝请求: {{ $value | humanize }}"

  - name: skyone-shuge.business
    rules:
      - alert: SearchLatencyHigh
        expr: |
          histogram_quantile(0.95, rate(search_latency_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
          team: product
        annotations:
          summary: "搜索 P95 延迟超过 5 秒"
          description: "搜索服务 P95 延迟: {{ $value | humanizeDuration }}"

      - alert: ActiveUsersDrop
        expr: |
          active_users_gauge{period="5m"} < active_users_gauge{period="5m"} offset 1h * 0.5
        for: 30m
        labels:
          severity: info
          team: product
        annotations:
          summary: "活跃用户数显著下降"
          description: "当前 5 分钟活跃用户: {{ $value }}, 较 1 小时前下降超过 50%"
```

---

## ✅ 二、API 限流与成本控制架构

### 2.1 限流类型定义

```typescript
// types/rate-limit.ts
export interface RateLimitConfig {
  enabled: boolean;
  algorithm: 'token_bucket' | 'sliding_window' | 'leaky_bucket';
  defaultLimits: RateLimitTier;
  tiers: Record<string, RateLimitTier>;
}

export interface RateLimitTier {
  requests_per_second: number;
  requests_per_minute: number;
  requests_per_hour: number;
  requests_per_day: number;
  burst_size: number;
  llm_tokens_per_minute: number;
  llm_requests_per_minute: number;
  llm_budget_per_day_usd: number;
}

export interface RateLimitScope {
  user_id?: string;
  organization_id?: string;
  api_key?: string;
  ip_address?: string;
  endpoint?: string;
}

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  limit: number;
  reset_at: Date;
  retry_after_ms?: number;
  scope: RateLimitScope;
  tier: string;
}

export interface RateLimitCounter {
  key: string;
  count: number;
  window_start: number;
  tokens: number;
  last_refill: number;
}

export interface LlmQuotaConfig {
  organization_id: string;
  model: string;
  quotas: {
    daily_tokens: number;
    daily_requests: number;
    daily_budget_usd: number;
  };
  used: {
    daily_tokens: number;
    daily_requests: number;
    daily_cost_usd: number;
  };
  reset_at: Date;
}

export interface CostAlert {
  organization_id: string;
  user_id?: string;
  threshold_percent: number;
  current_cost_usd: number;
  budget_usd: number;
  notified_at?: Date;
}
```

### 2.2 令牌桶限流器实现

```typescript
// services/rate-limit/TokenBucketRateLimiter.ts
import { RateLimitConfig, RateLimitResult, RateLimitScope, RateLimitCounter } from '../../types/rate-limit';
import { Redis } from 'ioredis';

export class TokenBucketRateLimiter {
  private redis: Redis;
  private config: RateLimitConfig;

  constructor(config: RateLimitConfig, redis: Redis) {
    this.config = config;
    this.redis = redis;
  }

  /**
   * 检查限流
   * 令牌桶算法：桶容量 = burst_size, 补充速率 = requests_per_second
   */
  async check(scope: RateLimitScope, tier: string): Promise<RateLimitResult> {
    const tierConfig = this.config.tiers[tier] || this.config.defaultLimits;
    const key = this.buildKey(scope);

    // Lua 脚本保证原子性
    const luaScript = `
      local key = KEYS[1]
      local bucket_key = KEYS[2]
      local capacity = tonumber(ARGV[1])
      local refill_rate = tonumber(ARGV[2])
      local now = tonumber(ARGV[3])
      local requested = tonumber(ARGV[4])

      local bucket = redis.call('HMGET', bucket_key, 'tokens', 'last_refill')
      local tokens = tonumber(bucket[1]) or capacity
      local last_refill = tonumber(bucket[2]) or now

      -- 计算应该补充的令牌数
      local elapsed = now - last_refill
      local refill = math.floor(elapsed * refill_rate)
      tokens = math.min(capacity, tokens + refill)

      local allowed = 0
      if tokens >= requested then
        tokens = tokens - requested
        allowed = 1
      end

      redis.call('HMSET', bucket_key, 'tokens', tokens, 'last_refill', now)
      redis.call('EXPIRE', bucket_key, 3600)

      local reset_at = now + math.ceil((capacity - tokens) / refill_rate)

      return {allowed, math.floor(tokens), capacity, reset_at}
    `;

    const now = Date.now() / 1000;
    const result = await this.redis.eval(
      luaScript,
      2,
      key,
      `${key}:bucket`,
      tierConfig.burst_size,
      tierConfig.requests_per_second,
      now,
      1
    ) as [number, number, number, number];

    const [allowed, remaining, limit, resetAt] = result;

    return {
      allowed: allowed === 1,
      remaining,
      limit,
      reset_at: new Date(resetAt * 1000),
      retry_after_ms: allowed === 1 ? undefined : Math.ceil((1 - remaining) * 1000),
      scope,
      tier,
    };
  }

  /**
   * 多维度限流检查（用户 + 组织 + 端点）
   */
  async checkAll(scope: RateLimitScope, tier: string): Promise<RateLimitResult[]> {
    const results: RateLimitResult[] = [];

    // 1. 用户维度限流
    if (scope.user_id) {
      results.push(await this.check({ user_id: scope.user_id }, tier));
    }

    // 2. 组织维度限流
    if (scope.organization_id) {
      results.push(await this.check({ organization_id: scope.organization_id }, tier));
    }

    // 3. IP 维度限流
    if (scope.ip_address) {
      results.push(await this.check({ ip_address: scope.ip_address }, 'ip'));
    }

    // 4. 端点维度限流
    if (scope.endpoint) {
      results.push(await this.check({ endpoint: scope.endpoint }, tier));
    }

    // 如果任何一个拒绝，则整体拒绝
    const rejected = results.find(r => !r.allowed);
    if (rejected) {
      return results;
    }

    return results;
  }

  private buildKey(scope: RateLimitScope): string {
    const parts: string[] = ['ratelimit'];
    if (scope.user_id) parts.push(`user:${scope.user_id}`);
    if (scope.organization_id) parts.push(`org:${scope.organization_id}`);
    if (scope.ip_address) parts.push(`ip:${scope.ip_address}`);
    if (scope.endpoint) parts.push(`ep:${scope.endpoint}`);
    return parts.join(':');
  }
}
```

### 2.3 LLM 配额管理器

```typescript
// services/rate-limit/LlmQuotaManager.ts
import { LlmQuotaConfig, CostAlert } from '../../types/rate-limit';
import { Redis } from 'ioredis';
import { MetricsCollector } from '../metrics/MetricsCollector';

export class LlmQuotaManager {
  private redis: Redis;
  private metrics: MetricsCollector;
  private alertThresholds = [0.5, 0.75, 0.9, 0.95, 1.0];

  constructor(redis: Redis, metrics: MetricsCollector) {
    this.redis = redis;
    this.metrics = metrics;
  }

  /**
   * 预检配额（调用 LLM API 前）
   */
  async checkQuota(orgId: string, userId: string, model: string, estimatedTokens: number): Promise<{
    allowed: boolean;
    reason?: string;
    quota?: LlmQuotaConfig;
  }> {
    const key = `llm:quota:${orgId}:${model}:${this.getDailyKey()}`;
    const quota = await this.getQuotaConfig(orgId, model);

    const currentTokens = await this.redis.hget(key, 'tokens') || 0;
    const currentCost = await this.redis.hget(key, 'cost') || 0;
    const currentRequests = await this.redis.hget(key, 'requests') || 0;

    // 检查日 token 限额
    if (currentTokens + estimatedTokens > quota.quotas.daily_tokens) {
      return { allowed: false, reason: 'DAILY_TOKEN_LIMIT_EXCEEDED', quota };
    }

    // 检查日成本限额
    const estimatedCost = this.estimateCost(model, estimatedTokens);
    if (currentCost + estimatedCost > quota.quotas.daily_budget_usd) {
      return { allowed: false, reason: 'DAILY_BUDGET_LIMIT_EXCEEDED', quota };
    }

    // 检查分钟请求频率
    const minuteKey = `llm:quota:${orgId}:${model}:minute:${this.getMinuteKey()}`;
    const minuteRequests = await this.redis.get(minuteKey) || 0;
    const minuteLimit = quota.quotas.daily_requests / 1440 * 10; // 简化：均匀分布的 10 倍

    if (parseInt(minuteRequests) >= minuteLimit) {
      return { allowed: false, reason: 'MINUTE_RATE_LIMIT_EXCEEDED', quota };
    }

    return { allowed: true, quota };
  }

  /**
   * 记录 LLM 使用
   */
  async recordUsage(
    orgId: string,
    userId: string,
    model: string,
    inputTokens: number,
    outputTokens: number,
    costUsd: number
  ): Promise<void> {
    const dailyKey = `llm:quota:${orgId}:${model}:${this.getDailyKey()}`;
    const minuteKey = `llm:quota:${orgId}:${model}:minute:${this.getMinuteKey()}`;

    const pipeline = this.redis.pipeline();

    // 累计日用量
    pipeline.hincrby(dailyKey, 'tokens', inputTokens + outputTokens);
    pipeline.hincrbyfloat(dailyKey, 'cost', costUsd);
    pipeline.hincrby(dailyKey, 'requests', 1);
    pipeline.expire(dailyKey, 86400 * 2); // 保留 2 天

    // 累计分钟用量
    pipeline.incr(minuteKey);
    pipeline.expire(minuteKey, 120);

    // 按用户分摊
    const userKey = `llm:quota:${orgId}:user:${userId}:${this.getDailyKey()}`;
    pipeline.hincrbyfloat(userKey, 'cost', costUsd);
    pipeline.hincrby(userKey, 'tokens', inputTokens + outputTokens);
    pipeline.expire(userKey, 86400 * 2);

    await pipeline.exec();

    // 检查告警阈值
    await this.checkCostAlerts(orgId, userId, costUsd);

    // 记录指标
    this.metrics.recordLlmCall('openai', model, 'chat', costUsd, 0);
  }

  /**
   * 获取配额配置
   */
  async getQuotaConfig(orgId: string, model: string): Promise<LlmQuotaConfig> {
    const key = `llm:quota:config:${orgId}:${model}`;
    const cached = await this.redis.hgetall(key);

    if (Object.keys(cached).length === 0) {
      // 默认配置
      return {
        organization_id: orgId,
        model,
        quotas: {
          daily_tokens: 1000000,
          daily_requests: 10000,
          daily_budget_usd: 100,
        },
        used: {
          daily_tokens: 0,
          daily_requests: 0,
          daily_cost_usd: 0,
        },
        reset_at: this.getDailyResetTime(),
      };
    }

    return {
      organization_id: orgId,
      model,
      quotas: {
        daily_tokens: parseInt(cached.daily_tokens),
        daily_requests: parseInt(cached.daily_requests),
        daily_budget_usd: parseFloat(cached.daily_budget_usd),
      },
      used: {
        daily_tokens: parseInt(cached.used_tokens || '0'),
        daily_requests: parseInt(cached.used_requests || '0'),
        daily_cost_usd: parseFloat(cached.used_cost || '0'),
      },
      reset_at: new Date(cached.reset_at),
    };
  }

  private async checkCostAlerts(orgId: string, userId: string, additionalCostUsd: number): Promise<void> {
    const userKey = `llm:quota:${orgId}:user:${userId}:${this.getDailyKey()}`;
    const totalCost = parseFloat(await this.redis.hget(userKey, 'cost') || '0');
    const orgKey = `llm:quota:config:${orgId}:default`;
    const budget = parseFloat(await this.redis.hget(orgKey, 'daily_budget_usd') || '100');

    const threshold = totalCost / budget;

    for (const alertThreshold of this.alertThresholds) {
      const alertKey = `llm:alert:${orgId}:${userId}:${alertThreshold}`;
      const notified = await this.redis.get(alertKey);

      if (!notified && threshold >= alertThreshold) {
        await this.sendCostAlert(orgId, userId, threshold, totalCost, budget);
        await this.redis.setex(alertKey, 86400, JSON.stringify({ notified_at: new Date() }));
      }
    }
  }

  private async sendCostAlert(
    orgId: string,
    userId: string,
    threshold: number,
    currentCost: number,
    budget: number
  ): Promise<void> {
    console.log(`[ALERT] LLM Cost ${(threshold * 100).toFixed(0)}% reached: $${currentCost.toFixed(4)} / $${budget}`);
    // 触发告警通知（飞书/Slack/Email）
  }

  private estimateCost(model: string, tokens: number): number {
    const pricing: Record<string, { input: number; output: number }> = {
      'gpt-4o': { input: 0.000005, output: 0.000015 },
      'gpt-4o-mini': { input: 0.00000015, output: 0.0000006 },
      'claude-3-5-sonnet': { input: 0.000003, output: 0.000015 },
    };
    const rates = pricing[model] || { input: 0.000005, output: 0.000015 };
    return tokens * (rates.input * 0.5 + rates.output * 0.5);
  }

  private getDailyKey(): string {
    const now = new Date();
    return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, '0')}-${String(now.getUTCDate()).padStart(2, '0')}`;
  }

  private getMinuteKey(): string {
    return `${Math.floor(Date.now() / 60000)}`;
  }

  private getDailyResetTime(): Date {
    const tomorrow = new Date();
    tomorrow.setUTCDate(tomorrow.getUTCDate() + 1);
    tomorrow.setUTCHours(0, 0, 0, 0);
    return tomorrow;
  }
}
```

### 2.4 成本计算 API

```typescript
// types/cost.ts
export interface CostCalculationRequest {
  organization_id: string;
  start_date: Date;
  end_date: Date;
  granularity: 'hour' | 'day' | 'week' | 'month';
  group_by?: ('user_id' | 'model' | 'operation' | 'day')[];
  filters?: CostFilter[];
}

export interface CostFilter {
  field: 'user_id' | 'model' | 'operation';
  operator: 'eq' | 'in';
  value: string | string[];
}

export interface CostBreakdown {
  total_cost_usd: number;
  total_tokens: number;
  by_model: Record<string, ModelCost>;
  by_user: Record<string, UserCost>;
  by_day: Record<string, DailyCost>;
  trend: CostTrend;
}

export interface ModelCost {
  model: string;
  cost_usd: number;
  input_tokens: number;
  output_tokens: number;
  request_count: number;
  avg_latency_ms: number;
}

export interface UserCost {
  user_id: string;
  cost_usd: number;
  tokens: number;
  request_count: number;
  percent_of_total: number;
}

export interface DailyCost {
  date: string;
  cost_usd: number;
  tokens: number;
  request_count: number;
  budget_usd: number;
  budget_usage_percent: number;
}

export interface CostTrend {
  direction: 'up' | 'down' | 'stable';
  change_percent: number;
  avg_daily_cost: number;
  projected_monthly_cost: number;
}

export interface CostAlertThreshold {
  organization_id: string;
  user_id?: string;
  thresholds: AlertThreshold[];
}

export interface AlertThreshold {
  percent: number;
  enabled: boolean;
  last_triggered?: Date;
}

export interface CostRecommendation {
  type: 'model_switch' | 'batch_processing' | 'caching' | 'prompt_optimization';
  priority: 'high' | 'medium' | 'low';
  potential_savings_usd: number;
  description: string;
  action_items: string[];
}
```

---

## ✅ 三、多级缓存架构

### 3.1 缓存层次结构

```typescript
// types/cache.ts
export interface CacheConfig {
  layers: CacheLayerConfig[];
  default_ttl_seconds: number;
  warm_up_enabled: boolean;
  invalidation: InvalidationConfig;
}

export interface CacheLayerConfig {
  name: string;
  type: 'memory' | 'redis' | 'db' | 'cdn';
  enabled: boolean;
  ttl_seconds: number;
  max_size_mb?: number;
  eviction_policy: 'lru' | 'lfu' | 'fifo' | 'ttl';
  compression?: 'gzip' | 'lz4' | 'none';
  serializer: 'json' | 'msgpack' | 'protobuf';
}

export interface InvalidationConfig {
  strategy: 'immediate' | 'delayed' | 'scheduled';
  cascade: boolean;
  patterns: InvalidationPattern[];
}

export interface InvalidationPattern {
  key_pattern: string;
  invalidation_type: 'match' | 'prefix' | 'regex';
  source_table?: string;
  trigger_event?: 'insert' | 'update' | 'delete';
}

export interface CacheKey {
  namespace: string;
  version?: string;
  components: Record<string, string | number>;
  scope?: 'user' | 'org' | 'global';
}

export interface CacheEntry<T = unknown> {
  key: string;
  value: T;
  created_at: Date;
  expires_at: Date;
  version?: string;
  metadata?: {
    size_bytes: number;
    hit_count: number;
    last_hit?: Date;
  };
}

export interface CacheStats {
  hits: number;
  misses: number;
  evictions: number;
  size_bytes: number;
  item_count: number;
  hit_ratio: number;
}
```

### 3.2 多级缓存管理器

```typescript
// services/cache/MultiLevelCache.ts
import { LRUCache } from 'lru-cache';
import { Redis } from 'ioredis';
import { CacheConfig, CacheEntry, CacheStats, CacheKey } from '../../types/cache';
import { MetricsCollector } from '../metrics/MetricsCollector';
import { StructuredLogger } from '../logging/StructuredLogger';

export class MultiLevelCache<T = unknown> {
  private memoryCache: LRUCache<string, CacheEntry<T>>;
  private redis: Redis;
  private config: CacheConfig;
  private metrics: MetricsCollector;
  private logger: StructuredLogger;
  private stats: CacheStats = { hits: 0, misses: 0, evictions: 0, size_bytes: 0, item_count: 0, hit_ratio: 0 };

  constructor(config: CacheConfig, redis: Redis, metrics: MetricsCollector, logger: StructuredLogger) {
    this.config = config;
    this.redis = redis;
    this.metrics = metrics;
    this.logger = logger;

    // 初始化 LRU 内存缓存
    const memoryConfig = config.layers.find(l => l.type === 'memory');
    this.memoryCache = new LRUCache({
      max: memoryConfig?.max_size_mb ? memoryConfig.max_size_mb * 1024 * 1024 : 50 * 1024 * 1024,
      maxSize: memoryConfig?.max_size_mb ? memoryConfig.max_size_mb * 1024 * 1024 : 50 * 1024 * 1024,
      sizeCalculation: (value: CacheEntry<T>) => JSON.stringify(value).length,
      ttl: memoryConfig?.ttl_seconds ? memoryConfig.ttl_seconds * 1000 : 60000,
    });
  }

  /**
   * 获取缓存（三级穿透：Memory -> Redis -> DB）
   */
  async get(key: CacheKey): Promise<T | null> {
    const keyStr = this.buildKeyString(key);

    // 1. 尝试内存缓存
    const memoryEntry = this.memoryCache.get(keyStr);
    if (memoryEntry && new Date(memoryEntry.expires_at) > new Date()) {
      this.stats.hits++;
      await this.incrementHitCount('memory', keyStr);
      this.logger.logCacheOperation('hit', keyStr, 'memory');
      return memoryEntry.value;
    }

    // 2. 尝试 Redis 缓存
    const redisEntry = await this.redis.get(keyStr);
    if (redisEntry) {
      const entry: CacheEntry<T> = JSON.parse(redisEntry);
      this.stats.hits++;
      await this.incrementHitCount('redis', keyStr);

      // 回填内存缓存
      this.memoryCache.set(keyStr, entry);
      this.logger.logCacheOperation('hit', keyStr, 'redis');
      return entry.value;
    }

    // 3. 未命中
    this.stats.misses++;
    this.logger.logCacheOperation('miss', keyStr, 'all');
    return null;
  }

  /**
   * 设置缓存（写入所有层级）
   */
  async set(key: CacheKey, value: T, options?: { ttl_seconds?: number; source?: string }): Promise<void> {
    const keyStr = this.buildKeyString(key);
    const ttl = options?.ttl_seconds || this.config.default_ttl_seconds;

    const entry: CacheEntry<T> = {
      key: keyStr,
      value,
      created_at: new Date(),
      expires_at: new Date(Date.now() + ttl * 1000),
      metadata: { size_bytes: JSON.stringify(value).length, hit_count: 0 },
    };

    // 1. 写入内存缓存
    this.memoryCache.set(keyStr, entry);

    // 2. 写入 Redis（带 TTL）
    const redisTTL = this.getRedisTTL(key.scope || 'global');
    await this.redis.setex(keyStr, redisTTL, JSON.stringify(entry));

    // 3. 如果有 DB 层，写入 DB 缓存
    // await this.writeDbCache(key, entry);

    this.logger.logCacheOperation('set', keyStr, 'all');
  }

  /**
   * 删除缓存（支持级联删除）
   */
  async delete(key: CacheKey, cascade: boolean = false): Promise<void> {
    const keyStr = this.buildKeyString(key);

    // 1. 删除内存缓存
    this.memoryCache.delete(keyStr);

    // 2. 删除 Redis 缓存
    await this.redis.del(keyStr);

    // 3. 级联删除相关缓存
    if (cascade) {
      const pattern = `${key.namespace}:${key.components[key.scope || 'user'] || '*'}`;
      const relatedKeys = await this.redis.keys(pattern);
      if (relatedKeys.length > 0) {
        await this.redis.del(...relatedKeys);
      }
    }
  }

  /**
   * 批量获取
   */
  async mget(keys: CacheKey[]): Promise<(T | null)[]> {
    return Promise.all(keys.map(key => this.get(key)));
  }

  /**
   * 批量设置
   */
  async mset(entries: Array<{ key: CacheKey; value: unknown }>): Promise<void> {
    await Promise.all(entries.map(e => this.set(e.key, e.value as T)));
  }

  /**
   * 缓存预热
   */
  async warmUp(queries: Array<{ key: CacheKey; loader: () => Promise<T> }>): Promise<void> {
    if (!this.config.warm_up_enabled) return;

    this.logger.info('Starting cache warm-up', { metadata: { item_count: queries.length } });

    const startTime = Date.now();
    let warmed = 0;
    let errors = 0;

    for (const { key, loader } of queries) {
      try {
        const cached = await this.get(key);
        if (!cached) {
          const value = await loader();
          await this.set(key, value);
          warmed++;
        }
      } catch (error) {
        errors++;
        this.logger.error('Cache warm-up error', error as Error, { metadata: { key: this.buildKeyString(key) } });
      }
    }

    const duration = Date.now() - startTime;
    this.logger.info('Cache warm-up completed', {
      metadata: { warmed, errors, duration_ms: duration }
    });
  }

  /**
   * 获取缓存统计
   */
  getStats(): CacheStats {
    this.stats.item_count = this.memoryCache.size;
    this.stats.size_bytes = this.memoryCache.calculatedSize;
    this.stats.hit_ratio = this.stats.hits / (this.stats.hits + this.stats.misses) || 0;
    return { ...this.stats };
  }

  private buildKeyString(key: CacheKey): string {
    const components = Object.entries(key.components)
      .map(([k, v]) => `${k}:${v}`)
      .join(':');
    return `${key.namespace}:${key.version || 'v1'}:${components}`;
  }

  private async incrementHitCount(layer: string, key: string): Promise<void> {
    const hitKey = `${key}:hits`;
    await this.redis.hincrby(hitKey, layer, 1);
    await this.redis.expire(hitKey, 86400);
  }

  private getRedisTTL(scope: 'user' | 'org' | 'global'): number {
    switch (scope) {
      case 'user': return 3600; // 1 小时
      case 'org': return 1800;  // 30 分钟
      case 'global': return 300; // 5 分钟
      default: return 900;
    }
  }
}
```

### 3.3 缓存预热策略

```typescript
// services/cache/CacheWarmUpService.ts
import { MultiLevelCache } from './MultiLevelCache';
import { DocumentStore } from '../storage/DocumentStore';

export class CacheWarmUpService {
  private cache: MultiLevelCache;
  private docStore: DocumentStore;

  constructor(cache: MultiLevelCache, docStore: DocumentStore) {
    this.cache = cache;
    this.docStore = docStore;
  }

  /**
   * 启动时缓存预热
   */
  async warmUpOnStartup(): Promise<void> {
    // 1. 热门文档缓存
    await this.warmUpHotDocuments();

    // 2. 用户最近访问文档
    await this.warmUpRecentUserAccesses();

    // 3. 搜索建议缓存
    await this.warmUpSearchSuggestions();

    // 4. 组织配置缓存
    await this.warmUpOrgConfigs();
  }

  private async warmUpHotDocuments(): Promise<void> {
    const hotDocs = await this.docStore.getHotDocuments({ limit: 1000, days: 7 });

    await this.cache.warmUp(
      hotDocs.map(doc => ({
        key: { namespace: 'doc', components: { id: doc.id }, scope: 'global' as const },
        loader: () => Promise.resolve(doc),
      }))
    );
  }

  private async warmUpRecentUserAccesses(): Promise<void> {
    const recentAccesses = await this.docStore.getRecentAccesses({ limit: 100 });

    await this.cache.warmUp(
      recentAccesses.map(access => ({
        key: { namespace: 'access', components: { user_id: access.user_id, doc_id: access.doc_id }, scope: 'user' as const },
        loader: () => Promise.resolve(access),
      }))
    );
  }

  private async warmUpSearchSuggestions(): Promise<void> {
    const suggestions = await this.docStore.getPopularSearchTerms({ limit: 500 });

    await this.cache.warmUp(
      suggestions.map(term => ({
        key: { namespace: 'suggest', components: { term }, scope: 'global' as const },
        loader: () => Promise.resolve(term),
      }))
    );
  }

  private async warmUpOrgConfigs(): Promise<void> {
    const orgs = await this.docStore.getActiveOrganizations();

    await this.cache.warmUp(
      orgs.map(org => ({
        key: { namespace: 'org', components: { id: org.id }, scope: 'org' as const },
        loader: () => this.docStore.getOrganizationConfig(org.id),
      }))
    );
  }
}
```

---

## ✅ 四、性能优化架构

### 4.1 数据库连接池配置

```typescript
// types/database.ts
export interface DatabasePoolConfig {
  pgbouncer: PgBouncerConfig;
  application: ApplicationPoolConfig;
  monitoring: PoolMonitoringConfig;
  query_analysis: QueryAnalysisConfig;
}

export interface PgBouncerConfig {
  enabled: boolean;
  host: string;
  port: number;
  database: string;
  pool_mode: 'transaction' | 'session' | 'statement';
  max_client_conn: number;
  default_pool_size: number;
  min_pool_size: number;
  server_idle_timeout: number;
  server_connect_timeout: number;
  query_timeout: number;
  auth_type: 'md5' | 'plain' | 'trust' | 'cert';
  auth_file: string;
}

export interface ApplicationPoolConfig {
  max_connections: number;
  idle_timeout_ms: number;
  connection_timeout_ms: number;
  statement_timeout_ms: number;
  retry: {
    max_attempts: number;
    backoff_ms: number;
  };
  health_check: {
    enabled: boolean;
    interval_ms: number;
    timeout_ms: number;
  };
}

export interface PoolMonitoringConfig {
  log_slow_queries: boolean;
  slow_query_threshold_ms: number;
  track_connection_wait: boolean;
  track_query_execution_time: boolean;
}

export interface QueryAnalysisConfig {
  enabled: boolean;
  log_analyzed_queries: boolean;
  slow_query_analyzer: {
    enabled: boolean;
    threshold_ms: number;
    limit: number;
  };
  explain_plans: {
    enabled: boolean;
    auto_explain_sample_rate: number;
  };
}

export interface ConnectionPoolStats {
  total_connections: number;
  idle_connections: number;
  used_connections: number;
  waiting_clients: number;
  avg_wait_time_ms: number;
  max_wait_time_ms: number;
  poolUtilization: number;
}

export interface QueryExecutionPlan {
  query: string;
  plan: unknown;
  planning_time_ms: number;
  execution_time_ms: number;
  estimated_cost: number;
  actual_rows: number;
  suggestions: string[];
}
```

### 4.2 PgBouncer 连接池管理

```typescript
// services/database/PgBouncerPoolManager.ts
import { Pool, PoolClient, QueryResult } from 'pg';
import { DatabasePoolConfig, ConnectionPoolStats } from '../../types/database';
import { MetricsCollector } from '../metrics/MetricsCollector';
import { StructuredLogger } from '../logging/StructuredLogger';

export class PgBouncerPoolManager {
  private pool: Pool;
  private config: DatabasePoolConfig;
  private metrics: MetricsCollector;
  private logger: StructuredLogger;
  private statsInterval?: NodeJS.Timeout;

  constructor(config: DatabasePoolConfig, metrics: MetricsCollector, logger: StructuredLogger) {
    this.config = config;
    this.metrics = metrics;
    this.logger = logger;

    if (config.pgbouncer.enabled) {
      this.pool = new Pool({
        host: config.pgbouncer.host,
        port: config.pgbouncer.port,
        database: config.pgbouncer.database,
        max: config.application.max_connections,
        idleTimeoutMillis: config.application.idle_timeout_ms,
        connectionTimeoutMillis: config.application.connection_timeout_ms,
      });
    } else {
      this.pool = new Pool({
        max: config.application.max_connections,
        idleTimeoutMillis: config.application.idle_timeout_ms,
        connectionTimeoutMillis: config.application.connection_timeout_ms,
      });
    }

    this.setupPoolEvents();
    this.startStatsCollection();
  }

  /**
   * 执行查询（带自动重试和慢查询记录）
   */
  async query<T = unknown>(
    sql: string,
    params?: unknown[],
    options?: { timeout_ms?: number; slow_query_threshold_ms?: number }
  ): Promise<QueryResult<T>> {
    const startTime = Date.now();
    const timeout = options?.timeout_ms || this.config.application.statement_timeout_ms;
    const slowThreshold = options?.slow_query_threshold_ms || this.config.monitoring.slow_query_threshold_ms;

    try {
      const result = await Promise.race([
        this.pool.query<T>(sql, params),
        this.timeoutPromise(timeout),
      ]) as QueryResult<T>;

      const duration = Date.now() - startTime;

      // 记录慢查询
      if (duration > slowThreshold && this.config.monitoring.log_slow_queries) {
        this.logger.warn('Slow query detected', {
          metadata: { sql: this.sanitizeSql(sql), duration_ms: duration, row_count: result.rowCount },
        });
      }

      // 记录指标
      this.metrics.recordDbQuery(this.classifyQuery(sql), this.extractTable(sql), duration);

      return result;
    } catch (error) {
      const duration = Date.now() - startTime;
      this.logger.error('Query failed', error as Error, {
        metadata: { sql: this.sanitizeSql(sql), duration_ms: duration },
      });
      throw error;
    }
  }

  /**
   * 获取连接池统计
   */
  async getPoolStats(): Promise<ConnectionPoolStats> {
    const client = await this.pool.connect();
    try {
      const result = await client.query(`
        SELECT
          total_connections,
          idle_connections,
          used_connections,
          maxwait as avg_wait_time_ms,
          maxwait as max_wait_time_ms
        FROM pgbouncer.pools
        WHERE database = current_database()
      `);

      const stats = result.rows[0] || {};
      return {
        total_connections: stats.total_connections || 0,
        idle_connections: stats.idle_connections || 0,
        used_connections: stats.used_connections || 0,
        waiting_clients: stats.waiting_clients || 0,
        avg_wait_time_ms: parseFloat(stats.avg_wait_time_ms || '0'),
        max_wait_time_ms: parseFloat(stats.max_wait_time_ms || '0'),
        poolUtilization: stats.total_connections > 0
          ? (stats.used_connections / stats.total_connections) * 100
          : 0,
      };
    } finally {
      client.release();
    }
  }

  /**
   * 预热连接池
   */
  async warmUp(): Promise<void> {
    const connections = [];
    for (let i = 0; i < this.config.pgbouncer.min_pool_size; i++) {
      connections.push(this.pool.connect());
    }
    await Promise.all(connections);
    connections.forEach(conn => conn.release());
    this.logger.info('Connection pool warmed up', { metadata: { size: this.config.pgbouncer.min_pool_size } });
  }

  private setupPoolEvents(): void {
    this.pool.on('error', (err) => {
      this.logger.error('Pool error', err);
    });

    this.pool.on('connect', () => {
      this.logger.debug('New pool connection');
    });
  }

  private startStatsCollection(): void {
    this.statsInterval = setInterval(async () => {
      try {
        const stats = await this.getPoolStats();
        this.metrics.recordDbPoolMetrics(stats);
      } catch {
        // ignore errors
      }
    }, 30000); // 每 30 秒采集一次
  }

  private timeoutPromise(ms: number): Promise<never> {
    return new Promise((_, reject) => {
      setTimeout(() => reject(new Error(`Query timeout after ${ms}ms`)), ms);
    });
  }

  private sanitizeSql(sql: string): string {
    return sql.replace(/\s+/g, ' ').substring(0, 200);
  }

  private classifyQuery(sql: string): string {
    const upper = sql.toUpperCase();
    if (upper.includes('SELECT')) return 'select';
    if (upper.includes('INSERT')) return 'insert';
    if (upper.includes('UPDATE')) return 'update';
    if (upper.includes('DELETE')) return 'delete';
    return 'other';
  }

  private extractTable(sql: string): string {
    const match = sql.match(/FROM\s+(\w+)/i) || sql.match(/INTO\s+(\w+)/i) || sql.match(/UPDATE\s+(\w+)/i);
    return match ? match[1] : 'unknown';
  }

  async shutdown(): Promise<void> {
    if (this.statsInterval) clearInterval(this.statsInterval);
    await this.pool.end();
  }
}
```

### 4.3 Redis 连接池优化

```typescript
// services/database/RedisConnectionPool.ts
import Redis from 'ioredis';
import { EventEmitter } from 'events';
import { MetricsCollector } from '../metrics/MetricsCollector';

export interface RedisPoolConfig {
  sentinels?: Array<{ host: string; port: number }>;
  masterName?: string;
  host?: string;
  port?: number;
  password?: string;
  db?: number;
  family?: 4 | 6;
  pool: {
    min: number;
    max: number;
    acquireTimeoutMs: number;
    idleTimeoutMs: number;
    validateOnBorrow: boolean;
    retryDelayMs: number;
    maxRetries: number;
  };
}

export class RedisConnectionPool extends EventEmitter {
  private pool: Redis[];
  private available: Redis[] = [];
  private acquired: Set<Redis> = new Set();
  private waiting: Array<{
    resolve: (client: Redis) => void;
    reject: (err: Error) => void;
    timeout: NodeJS.Timeout;
  }> = [];
  private config: RedisPoolConfig;
  private metrics: MetricsCollector;
  private closed = false;

  constructor(config: RedisPoolConfig, metrics: MetricsCollector) {
    super();
    this.config = config;
    this.metrics = metrics;
    this.initialize();
  }

  private async initialize(): Promise<void> {
    const nodes = this.config.sentinels
      ? this.config.sentinels.map(s => ({ host: s.host, port: s.port }))
      : [{ host: this.config.host!, port: this.config.port! }];

    // 预创建最小连接数
    for (let i = 0; i < this.config.pool.min; i++) {
      const client = this.createClient();
      this.available.push(client);
    }
  }

  private createClient(): Redis {
    const options: ConstructorParameters<typeof Redis>[0] = {
      password: this.config.password,
      db: this.config.db || 0,
      family: this.config.family || 4,
      retryStrategy: (times) => {
        if (times > this.config.pool.maxRetries) return null;
        return Math.min(times * this.config.pool.retryDelayMs, 2000);
      },
      maxRetriesPerRequest: this.config.pool.maxRetries,
      enableReadyCheck: true,
      lazyConnect: true,
    };

    let client: Redis;
    if (this.config.sentinels && this.config.masterName) {
      client = new Redis({
        ...options,
        sentinels: this.config.sentinels,
        name: this.config.masterName,
        role: 'master',
      });
    } else {
      client = new Redis({
        ...options,
        host: this.config.host,
        port: this.config.port,
      } as ConstructorParameters<typeof Redis>[0]);
    }

    client.on('error', (err) => this.emit('error', err));
    client.on('ready', () => this.emit('ready'));

    return client;
  }

  /**
   * 获取连接
   */
  async acquire(): Promise<Redis> {
    if (this.closed) throw new Error('Pool is closed');

    // 1. 优先使用可用连接
    const available = this.available.pop();
    if (available) {
      this.acquired.add(available);

      // 验证连接
      if (this.config.pool.validateOnBorrow) {
        const valid = await this.validateConnection(available);
        if (!valid) {
          this.acquired.delete(available);
          available.disconnect();
          return this.acquire();
        }
      }

      this.metrics.recordRedisPoolWait(0);
      return available;
    }

    // 2. 如果连接数未达上限，创建新连接
    if (this.acquired.size + this.available.length < this.config.pool.max) {
      const client = this.createClient();
      await client.connect();
      this.acquired.add(client);
      return client;
    }

    // 3. 等待可用连接
    return this.waitForConnection();
  }

  /**
   * 释放连接
   */
  release(client: Redis): void {
    if (!this.acquired.has(client)) return;
    this.acquired.delete(client);

    if (this.closed) {
      client.disconnect();
      return;
    }

    // 检查连接是否仍然有效
    if (this.config.pool.validateOnBorrow && !this.isConnectionOk(client)) {
      client.disconnect();
      return;
    }

    this.available.push(client);

    // 唤醒等待者
    const waiter = this.waiting.shift();
    if (waiter) {
      clearTimeout(waiter.timeout);
      waiter.resolve(client);
      this.acquired.add(client);
    }
  }

  /**
   * 批量操作
   */
  async withConnection<T>(fn: (client: Redis) => Promise<T>): Promise<T> {
    const client = await this.acquire();
    try {
      return await fn(client);
    } finally {
      this.release(client);
    }
  }

  async mExecute<T>(commands: Array<(client: Redis) => Promise<T>>): Promise<T[]> {
    const client = await this.acquire();
    try {
      const pipeline = client.pipeline();
      const p = commands.map(cmd => cmd(client));
      return await Promise.all(p);
    } finally {
      this.release(client);
    }
  }

  private async waitForConnection(): Promise<Redis> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        const idx = this.waiting.findIndex(w => w.resolve === resolve);
        if (idx !== -1) this.waiting.splice(idx, 1);
        reject(new Error('Acquire timeout'));
      }, this.config.pool.acquireTimeoutMs);

      const startTime = Date.now();
      this.waiting.push({ resolve, reject, timeout });

      // 定期检查是否有可用连接
      const checkInterval = setInterval(() => {
        const available = this.available.pop();
        if (available) {
          clearTimeout(timeout);
          const idx = this.waiting.findIndex(w => w.resolve === resolve);
          if (idx !== -1) this.waiting.splice(idx, 1);
          clearInterval(checkInterval);
          this.metrics.recordRedisPoolWait(Date.now() - startTime);
          this.acquired.add(available);
          resolve(available);
        }
      }, 100);
    });
  }

  private async validateConnection(client: Redis): Promise<boolean> {
    try {
      const result = await Promise.race([
        client.ping(),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Ping timeout')), 1000)),
      ]);
      return result === 'PONG';
    } catch {
      return false;
    }
  }

  private isConnectionOk(client: Redis): boolean {
    return client.status === 'ready';
  }

  async shutdown(): Promise<void> {
    this.closed = true;
    clearInterval(undefined as never);

    for (const client of this.available) {
      client.disconnect();
    }
    for (const client of this.acquired) {
      client.disconnect();
    }

    this.waiting.forEach(w => {
      clearTimeout(w.timeout);
      w.reject(new Error('Pool closed'));
    });
  }
}
```

---

## ✅ 五、高级搜索增强架构

### 5.1 分面搜索类型定义

```typescript
// types/search.ts
export interface FacetedSearchRequest {
  query: string;
  filters?: SearchFilters;
  facets: FacetDefinition[];
  pagination: {
    page: number;
    page_size: number;
  };
  sort?: SearchSort;
  highlight?: HighlightConfig;
  suggest?: SuggestConfig;
}

export interface SearchFilters {
  doc_type?: DocType[];
  tags?: string[];
  date_range?: { start: Date; end: Date };
  organization_id?: string;
  project_id?: string;
  author_id?: string;
  language?: string[];
  status?: 'draft' | 'published' | 'archived';
}

export interface FacetDefinition {
  field: string;
  type: 'terms' | 'range' | 'histogram' | 'date_histogram';
  options: FacetOptions;
  size?: number;
  min_doc_count?: number;
}

export interface FacetOptions {
  // terms facet
  terms?: {
    field: string;
    size?: number;
    order?: 'count' | 'term';
    min_doc_count?: number;
  };
  // range facet
  range?: {
    field: string;
    ranges: Array<{ from?: number; to?: number; label?: string }>;
  };
  // histogram facet
  histogram?: {
    field: string;
    interval: number;
    min_doc_count?: number;
  };
  // date_histogram facet
  date_histogram?: {
    field: string;
    calendar_interval: 'hour' | 'day' | 'week' | 'month' | 'year';
    format?: string;
    min_doc_count?: number;
  };
}

export interface FacetedSearchResult<T = unknown> {
  hits: SearchHit<T>[];
  total: number;
  facets: Record<string, FacetResult>;
  took_ms: number;
  suggest?: SearchSuggestion[];
  aggregations?: Record<string, unknown>;
}

export interface SearchHit<T = unknown> {
  id: string;
  score: number;
  source: T;
  highlights: Record<string, string[]>;
  sort?: (string | number)[];
  inner_hits?: Record<string, SearchHit<T>[]>;
}

export interface FacetResult {
  field: string;
  type: string;
  buckets?: FacetBucket[];
  buckets_array?: Array<{ key: string; doc_count: number; [key: string]: unknown }>;
}

export interface FacetBucket {
  key: string | number;
  doc_count: number;
  label?: string;
  from?: number;
  to?: number;
  from_as_string?: string;
  to_as_string?: string;
}

export interface SearchSuggestion {
  text: string;
  highlighted: string;
  score: number;
  type: 'term' | 'phrase' | 'completion';
  options?: Array<{
    text: string;
    score: number;
    freq: number;
  }>;
}

export interface HighlightConfig {
  fields: Record<string, HighlightFieldConfig>;
  pre_tags?: string[];
  post_tags?: string[];
  fragment_size?: number;
  number_of_fragments?: number;
}

export interface HighlightFieldConfig {
  fragment_size?: number;
  number_of_fragments?: number;
  pre_tags?: string[];
  post_tags?: string[];
  require_field_match?: boolean;
}

export interface SuggestConfig {
  term?: {
    field: string;
    size?: number;
    suggest_mode?: 'popular' | 'always' | 'missing';
  };
  phrase?: {
    field: string;
    size?: number;
    gram_size?: number;
    direct_generator?: boolean;
  };
  completion?: {
    field: string;
    size?: number;
    skip_duplicates?: boolean;
    fuzzy?: boolean;
  };
}

export interface SearchAnalytics {
  query: string;
  user_id: string;
  organization_id: string;
  result_count: number;
  clicked_doc_ids: string[];
  facets_used: string[];
  search_time_ms: number;
  timestamp: Date;
  session_id: string;
}

export interface PersonalizedRankingConfig {
  enabled: boolean;
  factors: RankingFactor[];
  user_profile_boost: number;
  freshness_decay: number;
  popularity_weight: number;
}

export interface RankingFactor {
  name: string;
  weight: number;
  type: 'relevance' | 'popularity' | 'freshness' | 'user_interest_match';
  params?: Record<string, unknown>;
}
```

### 5.2 Elasticsearch 分面搜索服务

```typescript
// services/search/ElasticsearchFacetService.ts
import { Client } from '@elastic/elasticsearch';
import { FacetedSearchRequest, FacetedSearchResult, SearchHit, FacetResult, FacetBucket } from '../../types/search';
import { MetricsCollector } from '../metrics/MetricsCollector';

export class ElasticsearchFacetService {
  private client: Client;
  private index: string;
  private metrics: MetricsCollector;

  constructor(client: Client, index: string, metrics: MetricsCollector) {
    this.client = client;
    this.index = index;
    this.metrics = metrics;
  }

  /**
   * 执行分面搜索
   */
  async search<T = unknown>(req: FacetedSearchRequest): Promise<FacetedSearchResult<T>> {
    const startTime = Date.now();

    // 构建 Elasticsearch 查询
    const query = this.buildQuery(req);
    const aggs = this.buildAggregations(req.facets);

    const response = await this.client.search({
      index: this.index,
      body: {
        query,
        aggs,
        from: (req.pagination.page - 1) * req.pagination.page_size,
        size: req.pagination.page_size,
        highlight: req.highlight ? this.buildHighlight(req.highlight) : undefined,
        suggest: req.suggest ? this.buildSuggest(req.suggest) : undefined,
        sort: req.sort ? this.buildSort(req.sort) : undefined,
        _source: true,
      },
    });

    const tookMs = response.took;

    // 解析 facets
    const facets = this.parseFacets(response.aggregations, req.facets);

    // 解析 hits
    const hits: SearchHit<T>[] = (response.hits.hits as unknown[]).map((hit: any) => ({
      id: hit._id,
      score: hit._score,
      source: hit._source,
      highlights: hit.highlight || {},
      sort: hit.sort,
    }));

    return {
      hits,
      total: typeof response.hits.total === 'number' ? response.hits.total : response.hits.total?.value || 0,
      facets,
      took_ms: tookMs,
      suggest: response.suggest ? this.parseSuggest(response.suggest) : undefined,
    };
  }

  /**
   * 获取分面统计（用于搜索分析报表）
   */
  async getFacetStats(
    field: string,
    filter?: { date_range?: { start: Date; end: Date } }
  ): Promise<FacetBucket[]> {
    const query: any = { bool: { must: [] } };

    if (filter?.date_range) {
      query.bool.must.push({
        range: {
          created_at: {
            gte: filter.date_range.start,
            lte: filter.date_range.end,
          },
        },
      });
    }

    const response = await this.client.search({
      index: this.index,
      body: {
        query,
        aggs: {
          facet_stats: {
            terms: {
              field,
              size: 100,
              order: { _count: 'desc' },
            },
          },
        },
        size: 0,
      },
    });

    const agg = response.aggregations?.facet_stats as any;
    return (agg?.buckets || []) as FacetBucket[];
  }

  /**
   * 搜索分析报表
   */
  async generateSearchReport(params: {
    organization_id: string;
    start_date: Date;
    end_date: Date;
    group_by: 'day' | 'week' | 'month';
  }): Promise<{
    total_searches: number;
    avg_result_count: number;
    top_queries: Array<{ query: string; count: number; avg_position: number }>;
    zero_result_queries: Array<{ query: string; count: number }>;
    top_facets_used: Array<{ facet: string; count: number }>;
    user_search_patterns: Record<string, number>;
  }> {
    const response = await this.client.search({
      index: this.index + '-analytics',
      body: {
        query: {
          bool: {
            must: [
              { term: { organization_id: params.organization_id } },
              {
                range: {
                  timestamp: {
                    gte: params.start_date,
                    lte: params.end_date,
                  },
                },
              },
            ],
          },
        },
        aggs: {
          daily_searches: {
            date_histogram: {
              field: 'timestamp',
              calendar_interval: params.group_by,
            },
          },
          top_queries: {
            terms: { field: 'query.keyword', size: 20, order: { _count: 'desc' } },
            aggs: { avg_position: { avg: { field: 'avg_click_position' } } },
          },
          zero_results: {
            filter: { term: { result_count: 0 } },
            aggs: {
              queries: { terms: { field: 'query.keyword', size: 10 } },
            },
          },
          facets_usage: {
            terms: { field: 'facets_used.keyword', size: 10 },
          },
        },
        size: 0,
      },
    });

    return {
      total_searches: (response.hits.total as any)?.value || 0,
      avg_result_count: 0, // 需要从 response 中提取
      top_queries: [], // 从 aggs.top_queries.buckets 提取
      zero_result_queries: [], // 从 aggs.zero_results.queries.buckets 提取
      top_facets_used: [], // 从 aggs.facets_usage.buckets 提取
      user_search_patterns: {},
    };
  }

  private buildQuery(req: FacetedSearchRequest): any {
    const must: any[] = [];
    const filter: any[] = [];

    // 全文检索
    if (req.query) {
      must.push({
        multi_match: {
          query: req.query,
          fields: ['title^3', 'content^1', 'tags^2', 'summary'],
          type: 'best_fields',
          fuzziness: 'AUTO',
        },
      });
    }

    // 过滤器
    if (req.filters) {
      if (req.filters.doc_type?.length) {
        filter.push({ terms: { doc_type: req.filters.doc_type } });
      }
      if (req.filters.tags?.length) {
        filter.push({ terms: { tags: req.filters.tags } });
      }
      if (req.filters.date_range) {
        filter.push({
          range: {
            created_at: {
              gte: req.filters.date_range.start,
              lte: req.filters.date_range.end,
            },
          },
        });
      }
      if (req.filters.organization_id) {
        filter.push({ term: { organization_id: req.filters.organization_id } });
      }
      if (req.filters.status) {
        filter.push({ term: { status: req.filters.status } });
      }
    }

    return {
      bool: {
        must: must.length > 0 ? must : [{ match_all: {} }],
        filter,
      },
    };
  }

  private buildAggregations(facets: FacetDefinition[]): Record<string, any> {
    const aggs: Record<string, any> = {};

    for (const facet of facets) {
      switch (facet.type) {
        case 'terms':
          aggs[facet.field] = {
            terms: {
              field: facet.options.terms!.field,
              size: facet.options.terms!.size || 10,
              order: facet.options.terms!.order || { _count: 'desc' },
              min_doc_count: facet.options.terms!.min_doc_count || 1,
            },
          };
          break;

        case 'range':
          aggs[facet.field] = {
            range: {
              field: facet.options.range!.field,
              ranges: facet.options.range!.ranges,
            },
          };
          break;

        case 'histogram':
          aggs[facet.field] = {
            histogram: {
              field: facet.options.histogram!.field,
              interval: facet.options.histogram!.interval,
              min_doc_count: facet.options.histogram!.min_doc_count || 0,
            },
          };
          break;

        case 'date_histogram':
          aggs[facet.field] = {
            date_histogram: {
              field: facet.options.date_histogram!.field,
              calendar_interval: facet.options.date_histogram!.calendar_interval,
              format: facet.options.date_histogram!.format || 'yyyy-MM-dd',
              min_doc_count: facet.options.date_histogram!.min_doc_count || 0,
            },
          };
          break;
      }
    }

    return aggs;
  }

  private parseFacets(
    aggregations: Record<string, any>,
    facetDefs: FacetDefinition[]
  ): Record<string, FacetResult> {
    const result: Record<string, FacetResult> = {};

    for (const def of facetDefs) {
      const agg = aggregations[def.field];
      if (!agg) continue;

      const facetResult: FacetResult = {
        field: def.field,
        type: def.type,
        buckets: [],
      };

      if (agg.buckets) {
        facetResult.buckets = agg.buckets.map((b: any) => ({
          key: b.key,
          doc_count: b.doc_count,
          label: b.key_as_string,
          from: b.from,
          to: b.to,
        }));
      }

      result[def.field] = facetResult;
    }

    return result;
  }

  private buildHighlight(config: HighlightConfig): any {
    const hlFields: Record<string, any> = {};
    for (const [field, fieldConfig] of Object.entries(config.fields)) {
      hlFields[field] = {
        fragment_size: fieldConfig.fragment_size || 150,
        number_of_fragments: fieldConfig.number_of_fragments || 3,
      };
    }

    return {
      fields: hlFields,
      pre_tags: config.pre_tags || ['<em>'],
      post_tags: config.post_tags || ['</em>'],
    };
  }

  private buildSuggest(suggest: SuggestConfig): any {
    const suggestBody: Record<string, any[]> = {};

    if (suggest.term) {
      suggestBody.term_suggest = [{
        text: suggest.term.field,
        term: {
          field: suggest.term.field,
          size: suggest.term.size || 5,
          suggest_mode: suggest.term.suggest_mode || 'popular',
        },
      }];
    }

    if (suggest.phrase) {
      suggestBody.phrase_suggest = [{
        text: suggest.phrase.field,
        phrase: {
          field: suggest.phrase.field,
          size: suggest.phrase.size || 5,
          gram_size: suggest.phrase.gram_size || 3,
        },
      }];
    }

    return suggestBody;
  }

  private buildSort(sort: SearchSort): any[] {
    const sortFields: any[] = [];

    if (sort.field) {
      sortFields.push({ [sort.field]: { order: sort.order || 'desc' } });
    }

    if (sort._score !== false) {
      sortFields.push({ _score: { order: 'desc' } });
    }

    return sortFields;
  }

  private parseSuggest(suggest: any): any[] {
    const results: any[] = [];
    for (const [name, suggestions] of Object.entries(suggest)) {
      for (const s of suggestions as any[]) {
        if (s.options?.length) {
          results.push(...s.options.map((opt: any) => ({
            text: opt.text,
            score: opt.score,
            type: name.replace('_suggest', ''),
          })));
        }
      }
    }
    return results;
  }
}
```

---

## ✅ 六、LLM 成本追踪与预算控制

### 6.1 成本追踪类型定义

```typescript
// types/llm-cost.ts
export interface LlmCostConfig {
  tracking_enabled: boolean;
  budget_alerts: BudgetAlertConfig[];
  cost_allocation: CostAllocationConfig;
  optimization: CostOptimizationConfig;
}

export interface BudgetAlertConfig {
  organization_id: string;
  thresholds: Array<{
    percent: number;
    enabled: boolean;
    channels: Array<'email' | 'slack' | 'feishu' | 'webhook'>;
  }>;
  daily_limit?: number;
  monthly_limit?: number;
  per_user_daily_limit?: number;
}

export interface CostAllocationConfig {
  enabled: boolean;
  allocation_level: 'organization' | 'user' | 'project' | 'document';
  billable_metrics: BillableMetric[];
}

export interface BillableMetric {
  name: string;
  unit_cost_usd: number;
  calculation: 'per_token' | 'per_request' | 'per_minute' | 'flat_rate';
  model: string;
}

export interface CostOptimizationConfig {
  enabled: boolean;
  strategies: CostOptimizationStrategy[];
  auto_apply_threshold: number; // 自动应用节省比例 > 此值时
}

export interface CostOptimizationStrategy {
  type: 'model_downgrade' | 'batch_processing' | 'result_caching' | 'prompt_compression';
  trigger_conditions: TriggerCondition[];
  potential_savings_percent: number;
  description: string;
  auto_apply: boolean;
}

export interface TriggerCondition {
  metric: 'avg_cost_per_call' | 'total_daily_cost' | 'token_usage' | 'latency_p99';
  operator: 'gt' | 'lt' | 'eq' | 'gte';
  value: number;
}

export interface LlmUsageRecord {
  id: string;
  organization_id: string;
  user_id: string;
  project_id?: string;
  document_id?: string;
  provider: 'openai' | 'anthropic' | 'google' | 'local';
  model: string;
  operation: 'chat' | 'embedding' | 'completion' | 'moderation';
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  latency_ms: number;
  timestamp: Date;
  metadata?: {
    prompt_id?: string;
    cache_hit?: boolean;
    batch_size?: number;
  };
}

export interface LlmBudget {
  organization_id: string;
  user_id?: string;
  budget_type: 'daily' | 'monthly' | 'one_time';
  budget_usd: number;
  used_usd: number;
  remaining_usd: number;
  reset_at: Date;
  alerts_sent: Array<{ threshold: number; at: Date }>;
}

export interface CostSummary {
  total_cost_usd: number;
  total_tokens: number;
  by_provider: Record<string, { cost_usd: number; tokens: number; requests: number }>;
  by_model: Record<string, { cost_usd: number; tokens: number; requests: number }>;
  by_user: Record<string, { cost_usd: number; tokens: number; requests: number; percent: number }>;
  by_day: Record<string, { cost_usd: number; tokens: number }>;
  projected_monthly_cost: number;
  budget_usage_percent: number;
}
```

### 6.2 LLM 成本追踪服务

```typescript
// services/llm-cost/LlmCostTracker.ts
import { LlmUsageRecord, LlmBudget, CostSummary, CostOptimizationStrategy, CostRecommendation } from '../../types/llm-cost';
import { Redis } from 'ioredis';
import { MetricsCollector } from '../metrics/MetricsCollector';
import { StructuredLogger } from '../logging/StructuredLogger';

export class LlmCostTracker {
  private redis: Redis;
  private metrics: MetricsCollector;
  private logger: StructuredLogger;
  private pricing: Record<string, { input: number; output: number }>;

  constructor(redis: Redis, metrics: MetricsCollector, logger: StructuredLogger) {
    this.redis = redis;
    this.metrics = metrics;
    this.logger = logger;

    // LLM 定价（美元/千 token）
    this.pricing = {
      'gpt-4o': { input: 5.0, output: 15.0 },
      'gpt-4o-mini': { input: 0.15, output: 0.6 },
      'gpt-4-turbo': { input: 10.0, output: 30.0 },
      'claude-3-5-sonnet': { input: 3.0, output: 15.0 },
      'claude-3-5-haiku': { input: 0.8, output: 4.0 },
      'gemini-1.5-pro': { input: 3.5, output: 10.5 },
      'gemini-1.5-flash': { input: 0.075, output: 0.3 },
    };
  }

  /**
   * 记录 LLM 使用
   */
  async recordUsage(record: LlmUsageRecord): Promise<void> {
    const pipeline = this.redis.pipeline();

    // 1. 按组织记录
    const orgKey = `llm:cost:org:${record.organization_id}:${this.getDayKey(record.timestamp)}`;
    pipeline.hincrbyfloat(orgKey, 'cost_usd', record.cost_usd);
    pipeline.hincrby(orgKey, 'input_tokens', record.input_tokens);
    pipeline.hincrby(orgKey, 'output_tokens', record.output_tokens);
    pipeline.hincrby(orgKey, 'requests', 1);
    pipeline.expire(orgKey, 86400 * 90); // 保留 90 天

    // 2. 按用户记录
    const userKey = `llm:cost:user:${record.user_id}:${this.getDayKey(record.timestamp)}`;
    pipeline.hincrbyfloat(userKey, 'cost_usd', record.cost_usd);
    pipeline.hincrby(userKey, 'tokens', record.input_tokens + record.output_tokens);
    pipeline.hincrby(userKey, 'requests', 1);
    pipeline.expire(userKey, 86400 * 90);

    // 3. 按模型记录
    const modelKey = `llm:cost:model:${record.model}:${this.getDayKey(record.timestamp)}`;
    pipeline.hincrbyfloat(modelKey, 'cost_usd', record.cost_usd);
    pipeline.hincrby(modelKey, 'tokens', record.input_tokens + record.output_tokens);
    pipeline.hincrby(modelKey, 'requests', 1);
    pipeline.expire(modelKey, 86400 * 90);

    // 4. 记录明细
    const detailKey = `llm:cost:detail:${record.id}`;
    pipeline.set(detailKey, JSON.stringify(record));
    pipeline.expire(detailKey, 86400 * 90);

    await pipeline.exec();

    // 5. 更新指标
    this.metrics.recordLlmCall(
      record.provider,
      record.model,
      record.operation,
      record.cost_usd,
      record.latency_ms
    );

    this.logger.logLlmCall(record.provider, record.model, record.input_tokens + record.output_tokens, record.cost_usd, record.latency_ms);

    // 6. 检查预算阈值
    await this.checkBudgetThresholds(record.organization_id, record.user_id);
  }

  /**
   * 计算成本
   */
  calculateCost(model: string, inputTokens: number, outputTokens: number): number {
    const rate = this.pricing[model] || { input: 5.0, output: 15.0 };
    return (inputTokens / 1000) * rate.input + (outputTokens / 1000) * rate.output;
  }

  /**
   * 获取成本汇总
   */
  async getCostSummary(
    organizationId: string,
    startDate: Date,
    endDate: Date
  ): Promise<CostSummary> {
    const days = this.getDaysBetween(startDate, endDate);
    let totalCost = 0;
    let totalTokens = 0;
    const byProvider: Record<string, any> = {};
    const byModel: Record<string, any> = {};
    const byUser: Record<string, any> = {};
    const byDay: Record<string, any> = {};

    for (const day of days) {
      const key = `llm:cost:org:${organizationId}:${day}`;
      const data = await this.redis.hgetall(key);

      if (Object.keys(data).length > 0) {
        const cost = parseFloat(data.cost_usd || '0');
        const tokens = parseInt(data.input_tokens || '0') + parseInt(data.output_tokens || '0');
        totalCost += cost;
        totalTokens += tokens;
        byDay[day] = { cost_usd: cost, tokens };
      }
    }

    // 获取用户分布（采样前 100 用户）
    const userKeys = await this.redis.keys(`llm:cost:user:*:${days[0]}`);
    for (const key of userKeys.slice(0, 100)) {
      const data = await this.redis.hgetall(key);
      const userId = key.split(':')[3];
      if (data.cost_usd) {
        byUser[userId] = {
          cost_usd: parseFloat(data.cost_usd),
          tokens: parseInt(data.tokens || '0'),
          requests: parseInt(data.requests || '0'),
          percent: 0,
        };
      }
    }

    // 计算百分比
    for (const user of Object.values(byUser)) {
      (user as any).percent = totalCost > 0 ? ((user as any).cost_usd / totalCost) * 100 : 0;
    }

    // 获取项目月度预算
    const budgetKey = `llm:budget:${organizationId}`;
    const budgetData = await this.redis.hgetall(budgetKey);
    const budgetUsd = parseFloat(budgetData?.budget_usd || '100');
    const budgetUsagePercent = budgetUsd > 0 ? (totalCost / budgetUsd) * 100 : 0;

    return {
      total_cost_usd: Math.round(totalCost * 10000) / 10000,
      total_tokens: totalTokens,
      by_provider: byProvider,
      by_model: byModel,
      by_user: byUser,
      by_day: byDay,
      projected_monthly_cost: totalCost / days.length * 30,
      budget_usage_percent: Math.round(budgetUsagePercent * 100) / 100,
    };
  }

  /**
   * 获取成本优化建议
   */
  async getOptimizationRecommendations(organizationId: string): Promise<CostRecommendation[]> {
    const summary = await this.getCostSummary(
      organizationId,
      new Date(Date.now() - 7 * 86400000),
      new Date()
    );

    const recommendations: CostRecommendation[] = [];

    // 1. 检查是否使用了高价模型
    const expensiveModels = ['gpt-4o', 'claude-3-5-sonnet'];
    const usedExpensive = Object.keys(summary.by_model).filter(m => expensiveModels.includes(m));
    if (usedExpensive.length > 0 && summary.total_cost_usd > 50) {
      recommendations.push({
        type: 'model_switch',
        priority: 'high',
        potential_savings_usd: summary.total_cost_usd * 0.4,
        description: `检测到使用了高价模型 (${usedExpensive.join(', ')}), 可考虑切换到 gpt-4o-mini 或 claude-3-5-haiku`,
        action_items: [
          '评估是否可以切换到轻量模型',
          '设置模型使用审批流程',
          '对简单任务强制使用轻量模型',
        ],
      });
    }

    // 2. 检查 token 使用效率
    if (summary.total_tokens > 1000000) {
      recommendations.push({
        type: 'prompt_optimization',
        priority: 'medium',
        potential_savings_usd: summary.total_tokens * 0.000001 * 0.3,
        description: 'Token 使用量较高，可通过提示词优化减少 token 消耗',
        action_items: [
          '审查提示词模板，去除冗余描述',
          '使用 few-shot 示例代替详细说明',
          '考虑结果压缩策略',
        ],
      });
    }

    // 3. 检查缓存利用率
    const cacheHitKey = `llm:cost:cache_hits:${organizationId}`;
    const cacheHits = parseInt(await this.redis.get(cacheHitKey) || '0');
    const cacheMissRate = 1 - (cacheHits / (cacheHits + summary.total_tokens));

    if (cacheMissRate > 0.8) {
      recommendations.push({
        type: 'caching',
        priority: 'medium',
        potential_savings_usd: summary.total_cost_usd * cacheMissRate * 0.5,
        description: `缓存命中率较低 (${(1 - cacheMissRate) * 100.toFixed(1)}%), 可通过增加缓存提升`,
        action_items: [
          '扩大缓存容量',
          '优化缓存 key 设计',
          '实现语义缓存',
        ],
      });
    }

    return recommendations;
  }

  /**
   * 设置预算阈值
   */
  async setBudgetThreshold(
    organizationId: string,
    userId: string | undefined,
    thresholdPercent: number,
    enabled: boolean
  ): Promise<void> {
    const key = `llm:budget:threshold:${organizationId}:${userId || 'org'}`;
    await this.redis.hset(key, thresholdPercent.toString(), JSON.stringify({ enabled, last_triggered: null }));
  }

  private async checkBudgetThresholds(organizationId: string, userId: string): Promise<void> {
    const summary = await this.getCostSummary(
      organizationId,
      new Date(Date.now() - 86400000),
      new Date()
    );

    const thresholdKey = `llm:budget:threshold:${organizationId}:${userId}`;
    const thresholds = await this.redis.hgetall(thresholdKey);

    for (const [percent, data] of Object.entries(thresholds)) {
      const config = JSON.parse(data);
      if (!config.enabled) continue;

      const threshold = parseFloat(percent);
      if (summary.budget_usage_percent >= threshold) {
        await this.sendBudgetAlert(organizationId, userId, threshold, summary.total_cost_usd);
        await this.redis.hset(thresholdKey, percent, JSON.stringify({
          enabled: true,
          last_triggered: new Date().toISOString(),
        }));
      }
    }
  }

  private async sendBudgetAlert(
    orgId: string,
    userId: string,
    threshold: number,
    currentCost: number
  ): Promise<void> {
    this.logger.warn('Budget threshold reached', {
      metadata: { orgId, userId, threshold, currentCost },
    });
    // 发送飞书/Slack/Email 通知
  }

  private getDayKey(date: Date): string {
    return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}-${String(date.getUTCDate()).padStart(2, '0')}`;
  }

  private getDaysBetween(start: Date, end: Date): string[] {
    const days: string[] = [];
    const current = new Date(start);
    while (current <= end) {
      days.push(this.getDayKey(current));
      current.setUTCDate(current.getUTCDate() + 1);
    }
    return days;
  }
}
```

---

## 📊 七、API 接口设计

### 7.1 监控与可观测性 API

```
# Prometheus 指标采集端点
GET  /metrics                    # Prometheus 格式指标

# Grafana Dashboard 配置
GET  /api/v1/dashboards          # 获取仪表板列表
GET  /api/v1/dashboards/:id      # 获取指定仪表板

# 告警管理
GET    /api/v1/alerts            # 获取告警列表
GET    /api/v1/alerts/:id        # 获取告警详情
POST   /api/v1/alerts/rules      # 创建告警规则
PUT    /api/v1/alerts/rules/:id  # 更新告警规则
DELETE /api/v1/alerts/rules/:id  # 删除告警规则
GET    /api/v1/alerts/history    # 获取告警历史

# 日志查询
GET  /api/v1/logs                # 查询日志
POST /api/v1/logs/search         # 复杂日志搜索

# 链路追踪
GET  /api/v1/traces              # 查询链路
GET  /api/v1/traces/:trace_id    # 获取指定链路详情
```

### 7.2 限流与配额 API

```
# 限流状态查询
GET  /api/v1/rate-limit/status           # 获取当前用户限流状态
GET  /api/v1/rate-limit/status/:user_id  # 获取指定用户限流状态（管理员）

# LLM 配额管理
GET  /api/v1/quotas                      # 获取当前配额
PUT  /api/v1/quotas                      # 更新配额配置
GET  /api/v1/quotas/usage                # 获取配额使用情况
POST /api/v1/quotas/reset                # 重置配额（管理员）

# 成本管理
GET  /api/v1/costs/summary              # 获取成本汇总
GET  /api/v1/costs breakdown            # 获取成本分摊
GET  /api/v1/costs/recommendations      # 获取优化建议
POST /api/v1/costs/budget               # 设置预算
GET  /api/v1/costs/budget               # 获取预算信息
```

### 7.3 缓存管理 API

```
# 缓存操作
GET   /api/v1/cache/stats               # 获取缓存统计
POST  /api/v1/cache/invalidate          # 手动失效缓存
POST  /api/v1/cache/warm-up             # 触发缓存预热
DELETE /api/v1/cache/:key               # 删除指定缓存

# 连接池管理
GET   /api/v1/pools/db/stats            # 数据库连接池统计
GET   /api/v1/pools/redis/stats         # Redis 连接池统计
POST  /api/v1/pools/warm-up             # 预热连接池
```

### 7.4 搜索增强 API

```
# 分面搜索
POST /api/v1/search/faceted            # 执行分面搜索
GET  /api/v1/search/facets/:field       # 获取指定字段分面

# 搜索分析
GET  /api/v1/search/analytics           # 获取搜索分析报表
GET  /api/v1/search/suggestions         # 获取搜索建议
POST /api/v1/search/record              # 记录搜索行为

# 个性化排序
GET  /api/v1/search/ranking/config      # 获取排序配置
PUT  /api/v1/search/ranking/config      # 更新排序配置
```

---

## 🗄️ 八、数据库设计

### 8.1 新增表

```sql
-- LLM 使用记录表（历史数据量大，使用 TimescaleDB）
CREATE TABLE llm_usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    document_id UUID REFERENCES documents(id),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    operation VARCHAR(50) NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd DECIMAL(10, 6) NOT NULL,
    latency_ms INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('llm_usage_records', 'created_at',
    chunk_time_interval => INTERVAL '1 day');

CREATE INDEX idx_llm_usage_org_date ON llm_usage_records(organization_id, created_at DESC);
CREATE INDEX idx_llm_usage_user_date ON llm_usage_records(user_id, created_at DESC);
CREATE INDEX idx_llm_usage_model ON llm_usage_records(model, created_at DESC);

-- LLM 预算表
CREATE TABLE llm_budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    budget_type VARCHAR(20) NOT NULL CHECK (budget_type IN ('daily', 'monthly', 'one_time')),
    budget_usd DECIMAL(10, 2) NOT NULL,
    used_usd DECIMAL(10, 2) DEFAULT 0,
    reset_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, user_id, budget_type)
);

-- 搜索分析表
CREATE TABLE search_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    session_id VARCHAR(100) NOT NULL,
    query TEXT NOT NULL,
    result_count INTEGER NOT NULL,
    facets_used JSONB DEFAULT '[]',
    clicked_doc_ids JSONB DEFAULT '[]',
    search_time_ms INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('search_analytics', 'created_at',
    chunk_time_interval => INTERVAL '1 hour');

CREATE INDEX idx_search_analytics_org ON search_analytics(organization_id, created_at DESC);
CREATE INDEX idx_search_analytics_session ON search_analytics(session_id, created_at DESC);

-- 告警记录表
CREATE TABLE alert_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_name VARCHAR(200) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'firing',
    labels JSONB NOT NULL,
    annotations JSONB DEFAULT '{}',
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alert_history_status ON alert_history(status, started_at DESC);
```

---

## 📁 目录结构

```
skyone-shuge/
├── src/
│   ├── services/
│   │   ├── metrics/
│   │   │   ├── PrometheusMetricsService.ts
│   │   │   └── MetricsCollector.ts
│   │   ├── tracing/
│   │   │   └── OpenTelemetryService.ts
│   │   ├── logging/
│   │   │   └── StructuredLogger.ts
│   │   ├── rate-limit/
│   │   │   ├── TokenBucketRateLimiter.ts
│   │   │   └── LlmQuotaManager.ts
│   │   ├── cache/
│   │   │   ├── MultiLevelCache.ts
│   │   │   └── CacheWarmUpService.ts
│   │   ├── database/
│   │   │   ├── PgBouncerPoolManager.ts
│   │   │   └── RedisConnectionPool.ts
│   │   ├── search/
│   │   │   └── ElasticsearchFacetService.ts
│   │   └── llm-cost/
│   │       └── LlmCostTracker.ts
│   └── types/
│       ├── observability.ts
│       ├── rate-limit.ts
│       ├── cost.ts
│       ├── cache.ts
│       ├── database.ts
│       ├── search.ts
│       └── llm-cost.ts
├── config/
│   ├── alerts/
│   │   └── v3.0.15/
│   │       └── alerts.yaml
│   ├── grafana/
│   │   └── dashboards/
│   │       ├── overview.json
│   │       ├── llm-costs.json
│   │       └── search-performance.json
│   └── prometheus/
│       └── scrape-configs.yaml
├── prd/
│   └── MVP_v3.0.15.md
└── architecture/
    └── ARCHITECTURE_v3.0.15.md
```

---

## ⏱️ 里程碑计划

| 阶段 | 交付物 | 预计工期 |
|------|--------|----------|
| Week 1 | 监控基础设施（Prometheus + Grafana + OpenTelemetry） + 基础日志服务 | 5 days |
| Week 2 | API 限流 + LLM 配额管理 + 成本追踪核心模块 | 5 days |
| Week 3 | 多级缓存架构 + 数据库连接池优化 | 5 days |
| Week 4 | 分面搜索 + 搜索分析 + 个性化排序 | 5 days |
| Week 5 | LLM 成本分析报表 + 预算告警 + 优化建议 | 5 days |
| Week 6 | 集成测试 + 性能测试 + 文档完善 | 5 days |
