# 天一阁 PRD v3.0.18

**版本**: v3.0.18  
**日期**: 2026-04-09  
**阶段**: 生产环境部署 + 监控告警 + 性能压测优化 + 文档完善

---

## 📋 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0.18 | 2026-04-09 | 生产环境部署配置 + 监控告警规则 + 性能压测优化 + 用户手册 |
| v3.0.17 | 2026-04-08 | 监控/限流/缓存 API 实现 + 前后端联调 + 端到端测试 |
| v3.0.16 | 2026-04-05 | 实现代码开发 + 前端 UI 组件开发 + 单元测试与集成测试 |
| v3.0.15 | 2026-04-04 | 监控架构 + 限流架构 + 多级缓存架构 + 性能优化架构 + 搜索增强架构 + LLM 成本追踪架构 |

---

## 📅 本次迭代目标

### 核心交付物
- [ ] **Kubernetes 部署配置**: Helm Chart、Docker Compose 生产配置、环境隔离、灰度发布
- [ ] **监控告警规则**: Prometheus 告警规则、告警通道集成、告警升级策略、阈值模板
- [ ] **性能压测方案**: JMeter/k6 压测工具选型、压测场景设计、性能基线建立
- [ ] **用户手册**: 文档站点设计、API 文档、运维手册、故障排查指南

---

## 🎯 一、生产环境部署配置架构

### 1.1 Kubernetes 部署架构

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Kubernetes 部署架构                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Namespace 隔离设计                                   │   │
│  │                                                                              │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐               │   │
│  │  │  skyone-prod    │  │  skyone-staging │  │  skyone-dev     │               │   │
│  │  │  ─────────────  │  │  ─────────────  │  │  ─────────────  │               │   │
│  │  │  api (3 pods)  │  │  api (2 pods)  │  │  api (1 pod)   │               │   │
│  │  │  worker (4 pod)│  │  worker (2 pod)│  │  worker (1 pod) │               │   │
│  │  │  redis         │  │  redis         │  │  redis         │               │   │
│  │  │  postgres      │  │  postgres      │  │  sqlite        │               │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘               │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           API Deployment 配置                                   │   │
│  │                                                                              │   │
│  │  api-deployment.yaml:                                                        │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │  │  apiVersion: apps/v1                                                  │    │   │
│  │  │  kind: Deployment                                                    │    │   │
│  │  │  metadata:                                                          │    │   │
│  │  │    name: skyone-api                                                 │    │   │
│  │  │    namespace: skyone-prod                                           │    │   │
│  │  │  spec:                                                             │    │   │
│  │  │    replicas: 3                                                      │    │   │
│  │  │    selector:                                                        │    │   │
│  │  │      matchLabels: { app: skyone-api }                              │    │   │
│  │  │    template:                                                        │    │   │
│  │  │      metadata:                                                      │    │   │
│  │  │        labels: { app: skyone-api, version: v3.0.18 }               │    │   │
│  │  │      spec:                                                          │    │   │
│  │  │        containers:                                                  │    │   │
│  │  │        - name: api                                                  │    │   │
│  │  │          image: skyone/shuge:v3.0.18                               │    │   │
│  │  │          ports:                                                     │    │   │
│  │  │          - containerPort: 8000                                      │    │   │
│  │  │          resources:                                                 │    │   │
│  │  │            requests: { cpu: 500m, memory: 512Mi }                   │    │   │
│  │  │            limits: { cpu: 2000m, memory: 2Gi }                      │    │   │
│  │  │          livenessProbe:                                             │    │   │
│  │  │            httpGet: { path: /health, port: 8000 }                   │    │   │
│  │  │            initialDelaySeconds: 30                                  │    │   │
│  │  │            periodSeconds: 10                                        │    │   │
│  │  │          readinessProbe:                                           │    │   │
│  │  │            httpGet: { path: /ready, port: 8000 }                   │    │   │
│  │  │            initialDelaySeconds: 5                                   │    │   │
│  │  │            periodSeconds: 5                                         │    │   │
│  │  └─────────────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Service & Ingress 配置                               │   │
│  │                                                                              │   │
│  │  api-service.yaml:                                                           │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │  │  kind: Service                                                        │    │   │
│  │  │  metadata:                                                            │    │   │
│  │  │    name: skyone-api-svc                                               │    │   │
│  │  │  spec:                                                               │    │   │
│  │  │    type: ClusterIP                                                    │    │   │
│  │  │    selector: { app: skyone-api }                                     │    │   │
│  │  │    ports:                                                            │    │   │
│  │  │    - port: 80                                                        │    │   │
│  │  │      targetPort: 8000                                                │    │   │
│  │  │    - port: 443                                                       │    │   │
│  │  │      targetPort: 8000                                                │    │   │
│  │  └─────────────────────────────────────────────────────────────────────┘    │   │
│  │                                                                              │   │
│  │  ingress.yaml:                                                               │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │  │  apiVersion: networking.k8s.io/v1                                    │    │   │
│  │  │  kind: Ingress                                                       │    │   │
│  │  │  metadata:                                                          │    │   │
│  │  │    name: skyone-ingress                                              │    │   │
│  │  │    annotations:                                                      │    │   │
│  │  │      nginx.ingress.kubernetes.io/ssl-redirect: "true"               │    │   │
│  │  │      nginx.ingress.kubernetes.io/proxy-body-size: "100m"            │    │   │
│  │  │      nginx.ingress.kubernetes.io/proxy-read-timeout: "300"          │    │   │
│  │  │  spec:                                                              │    │   │
│  │  │    tls:                                                             │    │   │
│  │  │    - hosts: [api.skyskyone.com]                                     │    │   │
│  │  │      secretName: skyone-tls                                          │    │   │
│  │  │    rules:                                                           │    │   │
│  │  │    - host: api.skyskyone.com                                        │    │   │
│  │  │      http:                                                          │    │   │
│  │  │        paths:                                                       │    │   │
│  │  │        - path: /                                                    │    │   │
│  │  │          pathType: Prefix                                          │    │   │
│  │  │          backend: { service: { name: skyone-api-svc, port: 80 } }   │    │   │
│  │  └─────────────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Helm Chart 结构

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Helm Chart 目录结构                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  skyone-shuge/                                                                      │
│  ├── Chart.yaml                        # Chart 元信息                                  │
│  ├── values.yaml                       # 默认配置 values                              │
│  ├── values-prod.yaml                   # 生产环境 values                             │
│  ├── values-staging.yaml               # 预发环境 values                             │
│  ├── templates/                        # K8s 资源模板                                 │
│  │   ├── _helpers.tpl                 # 通用模板 helpers                             │
│  │   ├── namespace.yaml                # Namespace 定义                             │
│  │   ├── api-deployment.yaml           # API Deployment                            │
│  │   ├── api-service.yaml              # API Service                               │
│  │   ├── worker-deployment.yaml        # Celery Worker Deployment                  │
│  │   ├── ingress.yaml                  # Ingress 配置                             │
│  │   ├── configmap.yaml                # ConfigMap (非敏感配置)                     │
│  │   ├── secrets.yaml                  # Secrets (敏感配置)                         │
│  │   ├── pvc.yaml                      # PersistentVolumeClaim                      │
│  │   ├── hpa.yaml                      # HorizontalPodAutoscaler                    │
│  │   ├── pdb.yaml                      # PodDisruptionBudget                        │
│  │   └── servicemonitor.yaml           # Prometheus ServiceMonitor                  │
│  └── charts/                          # 依赖的子 Chart                              │
│                                                                                      │
│  values.yaml 结构:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐            │
│  │  # 全局配置                                                          │            │
│  │  global:                                                           │            │
│  │    imageRegistry: registry.skyskyone.com                           │            │
│  │    imagePullSecrets: [skyone-registry]                             │            │
│  │                                                                   │            │
│  │  # API 配置                                                         │            │
│  │  api:                                                              │            │
│  │    replicaCount: 3                                                 │            │
│  │    image: { repository: skyone/shuge, tag: "v3.0.18" }             │            │
│  │    service: { type: ClusterIP, port: 80 }                          │            │
│  │    resources:                                                      │            │
│  │      requests: { cpu: 500m, memory: 512Mi }                         │            │
│  │      limits: { cpu: 2000m, memory: 2Gi }                            │            │
│  │    autoscaling:                                                    │            │
│  │      enabled: true                                                │            │
│  │      minReplicas: 3                                               │            │
│  │      maxReplicas: 10                                              │            │
│  │      targetCPUUtilizationPercentage: 70                           │            │
│  │                                                                   │            │
│  │  # Worker 配置                                                     │            │
│  │  worker:                                                          │            │
│  │    replicaCount: 4                                                │            │
│  │    image: { repository: skyone/shuge, tag: "v3.0.18" }             │            │
│  │    resources:                                                      │            │
│  │      requests: { cpu: 1000m, memory: 1Gi }                         │            │
│  │      limits: { cpu: 4000m, memory: 4Gi }                          │            │
│  │    queues: [documents, embeddings, index, notifications]          │            │
│  │                                                                   │            │
│  │  # Redis 配置                                                       │            │
│  │  redis:                                                           │            │
│  │    enabled: true                                                  │            │
│  │    architecture: replication                                      │            │
│  │    auth: { enabled: true, password: "" }  # 从 Secrets 注入       │            │
│  │    master: { persistence: { enabled: true, size: 10Gi } }        │            │
│  │                                                                   │            │
│  │  # PostgreSQL 配置 (可选，使用外部 RDS)                              │            │
│  │  postgresql:                                                      │            │
│  │    enabled: false  # 生产环境使用外部 RDS                            │            │
│  │                                                                   │            │
│  │  # Ingress 配置                                                     │            │
│  │  ingress:                                                         │            │
│  │    enabled: true                                                  │            │
│  │    className: nginx                                               │            │
│  │    annotations: {}                                                │            │
│  │    hosts:                                                         │            │
│  │      - host: api.skyskyone.com                                    │            │
│  │        paths: [{ path: /, pathType: Prefix }]                     │            │
│  │    tls:                                                           │            │
│  │      - secretName: skyone-tls                                     │            │
│  │        hosts: [api.skyskyone.com]                                 │            │
│  │                                                                   │            │
│  │  # 监控配置                                                         │            │
│  │  monitoring:                                                      │            │
│  │    enabled: true                                                  │            │
│  │    serviceMonitor: { enabled: true }                              │            │
│  │    prometheusRule: { enabled: true }                              │            │
│  └─────────────────────────────────────────────────────────────────────┘            │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Docker Compose 生产配置

```yaml
# docker-compose.prod.yml
version: "3.8"

services:
  # ============================================
  # API 服务
  # ============================================
  api:
    image: skyone/shuge:v3.0.18
    container_name: skyone-api
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
      - LOG_FORMAT=json
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - LLM_API_KEY=${LLM_API_KEY}
      - LLM_BASE_URL=${LLM_BASE_URL}
      - PROMETHEUS_ENABLED=true
      - OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT}
    volumes:
      - /data/skyone/uploads:/app/uploads
      - /data/skyone/media:/app/media
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    networks:
      - skyone-net
    logging:
      driver: json-file
      options:
        max-size: "100m"
        max-file: "5"

  # ============================================
  # Celery Worker
  # ============================================
  worker:
    image: skyone/shuge:v3.0.18
    container_name: skyone-worker
    restart: unless-stopped
    command: celery -A skyone_shuge.core.celery_app worker --loglevel=info --concurrency=4 --max-tasks-per-child=1000
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
      - LOG_FORMAT=json
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - /data/skyone/uploads:/app/uploads
      - /data/skyone/media:/app/media
    depends_on:
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 1G
    networks:
      - skyone-net
    logging:
      driver: json-file
      options:
        max-size: "100m"
        max-file: "5"

  # ============================================
  # Celery Beat (定时任务调度器)
  # ============================================
  celery-beat:
    image: skyone/shuge:v3.0.18
    container_name: skyone-beat
    restart: unless-stopped
    command: celery -A skyone_shuge.core.celery_app beat --loglevel=info
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - skyone-net
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "3"

  # ============================================
  # Flower (Celery 监控)
  # ============================================
  flower:
    image: mher/flower:latest
    container_name: skyone-flower
    restart: unless-stopped
    ports:
      - "127.0.0.1:5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - skyone-net
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "3"

  # ============================================
  # Redis (缓存 + 消息队列)
  # ============================================
  redis:
    image: redis:7-alpine
    container_name: skyone-redis
    restart: unless-stopped
    command: >
      redis-server
      --appendonly yes
      --maxmemory 2gb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - /data/skyone/redis:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 2G
    networks:
      - skyone-net
    logging:
      driver: json-file
      options:
        max-size: "100m"
        max-file: "5"

  # ============================================
  # Nginx (反向代理 + 静态文件)
  # ============================================
  nginx:
    image: nginx:alpine
    container_name: skyone-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - /data/skyone/media:/usr/share/nginx/media:ro
    depends_on:
      - api
    networks:
      - skyone-net
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "3"

  # ============================================
  # Prometheus (指标收集)
  # ============================================
  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: skyone-prometheus
    restart: unless-stopped
    ports:
      - "127.0.0.1:9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/rules:/etc/prometheus/rules:ro
      - /data/skyone/prometheus:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
      - '--web.enable-lifecycle'
    networks:
      - skyone-net

  # ============================================
  # Grafana (可视化仪表盘)
  # ============================================
  grafana:
    image: grafana/grafana:10.0.0
    container_name: skyone-grafana
    restart: unless-stopped
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=https://grafana.skyskyone.com
    volumes:
      - /data/skyone/grafana:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    depends_on:
      - prometheus
    networks:
      - skyone-net

networks:
  skyone-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16

volumes:
  redis-data:
  prometheus-data:
  grafana-data:
```

### 1.4 CI/CD 流水线

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              CI/CD 流水线架构                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           GitOps 流程                                          │   │
│  │                                                                              │   │
│  │   GitHub Repo                                                                │   │
│  │   ├── main branch ──► 自动部署到 staging                                     │   │
│  │   └── release/* ───► 自动部署到 production                                  │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           GitHub Actions Workflow                              │   │
│  │                                                                              │   │
│  │  .github/workflows/ci.yml:                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │  │  name: CI/CD Pipeline                                                │    │   │
│  │  │                                                                     │    │   │
│  │  │  on:                                                                 │    │   │
│  │  │    push:                                                            │    │   │
│  │  │      branches: [main, 'release/*']                                  │    │   │
│  │  │    pull_request:                                                    │    │   │
│  │  │      branches: [main]                                               │    │   │
│  │  │                                                                     │    │   │
│  │  │  jobs:                                                              │    │   │
│  │  │    lint:                                                           │    │   │
│  │  │      runs-on: ubuntu-latest                                        │    │   │
│  │  │      steps:                                                        │    │   │
│  │  │        - uses: actions/checkout@v4                                 │    │   │
│  │  │        - name: Run Ruff Linter                                     │    │   │
│  │  │          run: pip install ruff && ruff check src/                  │    │   │
│  │  │        - name: Run MyPy                                            │    │   │
│  │  │          run: pip install mypy && mypy src/                        │    │   │
│  │  │                                                                     │    │   │
│  │  │    test:                                                           │    │   │
│  │  │      runs-on: ubuntu-latest                                        │    │   │
│  │  │      services:                                                     │    │   │
│  │  │        redis: { image: redis:7-alpine, ports: {6379:6379} }        │    │   │
│  │  │        postgres: { image: postgres:15, ports: {5432:5432}, env:   │    │   │
│  │  │                       POSTGRES_DB: skyone_test                      │    │   │
│  │  │      steps:                                                        │    │   │
│  │  │        - uses: actions/checkout@v4                                 │    │   │
│  │  │        - name: Run pytest                                          │    │   │
│  │  │          run: |                                                      │    │   │
│  │  │            pip install -e ".[test]"                                │    │   │
│  │  │            pytest tests/ -v --cov=src/                             │    │   │
│  │  │                                                                     │    │   │
│  │  │    build:                                                          │    │   │
│  │  │      runs-on: ubuntu-latest                                        │    │   │
│  │  │      needs: [lint, test]                                           │    │   │
│  │  │      steps:                                                        │    │   │
│  │  │        - uses: actions/checkout@v4                                 │    │   │
│  │  │        - name: Set up Docker Buildx                                │    │   │
│  │  │          uses: docker/setup-buildx-action@v3                       │    │   │
│  │  │        - name: Login to Registry                                   │    │   │
│  │  │          uses: docker/login-action@v3                              │    │   │
│  │  │          with:                                                      │    │   │
│  │  │            registry: ${{ secrets.REGISTRY }}                       │    │   │
│  │  │            username: ${{ secrets.REGISTRY_USER }}                  │    │   │
│  │  │            password: ${{ secrets.REGISTRY_TOKEN }}                │    │   │
│  │  │        - name: Build and Push                                      │    │   │
│  │  │          uses: docker/build-push-action@v5                          │    │   │
│  │  │          with:                                                      │    │   │
│  │  │            context: .                                             │    │   │
│  │  │            push: ${{ github.event_name != 'pull_request' }}       │    │   │
│  │  │            tags: |                                                  │    │   │
│  │  │              ${{ secrets.REGISTRY }}/skyone/shuge:${{ github.sha }}   │    │   │
│  │  │              ${{ secrets.REGISTRY }}/skyone/shuge:latest            │    │   │
│  │  │                                                                     │    │   │
│  │  │    deploy-staging:                                                 │    │   │
│  │  │      runs-on: ubuntu-latest                                        │    │   │
│  │  │      if: github.ref == 'refs/heads/main'                          │    │   │
│  │  │      needs: [build]                                                │    │   │
│  │  │      steps:                                                        │    │   │
│  │  │        - name: Deploy to Staging                                  │    │   │
│  │  │          uses: ./.github/actions/deploy-staging                    │    │   │
│  │  │          with:                                                      │    │   │
│  │  │            image_tag: ${{ github.sha }}                           │    │   │
│  │  │            kubeconfig: ${{ secrets.STAGING_KUBECONFIG }}          │    │   │
│  │  │                                                                     │    │   │
│  │  │    deploy-production:                                             │    │   │
│  │  │      runs-on: ubuntu-latest                                        │    │   │
│  │  │      if: startsWith(github.ref, 'refs/heads/release/')          │    │   │
│  │  │      needs: [build]                                                │    │   │
│  │  │      steps:                                                        │    │   │
│  │  │        - name: Deploy to Production                               │    │   │
│  │  │          uses: ./.github/actions/deploy-production                │    │   │
│  │  │          with:                                                      │    │   │
│  │  │            image_tag: ${{ github.sha }}                           │    │   │
│  │  │            kubeconfig: ${{ secrets.PROD_KUBECONFIG }}            │    │   │
│  │  └─────────────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.5 环境变量与 Secrets 管理

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Secrets 管理架构                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Secret 层级设计                                      │   │
│  │                                                                              │   │
│  │  Level 1: 应用级 Secrets (Kubernetes Secret / Vault)                          │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │  │  Secret Name: skyone-app-secrets                                    │    │   │
│  │  │  ├── DATABASE_URL: postgresql://user:pass@host:5432/skyone       │    │   │
│  │  │  ├── SECRET_KEY: <生成的安全随机密钥>                                │    │   │
│  │  │  ├── LLM_API_KEY: <LLM API Key>                                   │    │   │
│  │  │  ├── LLM_BASE_URL: https://api.openai.com                         │    │   │
│  │  │  ├── REDIS_PASSWORD: <Redis 密码>                                  │    │   │
│  │  │  ├── GRAFANA_PASSWORD: <Grafana 密码>                              │    │   │
│  │  │  └── ALLOWED_HOSTS: api.skyskyone.com                              │    │   │
│  │  └─────────────────────────────────────────────────────────────────────┘    │   │
│  │                                                                              │   │
│  │  Level 2: 外部服务凭据 (AWS Secrets Manager / HashiCorp Vault)               │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │  │  Registry Credentials:                                              │    │   │
│  │  │  ├── REGISTRY: registry.skyskyone.com                             │    │   │
│  │  │  ├── REGISTRY_USER: <镜像仓库用户名>                               │    │   │
│  │  │  └── REGISTRY_TOKEN: <镜像仓库 Token>                              │    │   │
│  │  │                                                                     │    │   │
│  │  │  External Services:                                                 │    │   │
│  │  │  ├── AWS_ACCESS_KEY_ID: <AWS 访问密钥>                             │    │   │
│  │  │  ├── AWS_SECRET_ACCESS_KEY: <AWS 私钥>                            │    │   │
│  │  │  └── SENTRY_DSN: <Sentry DSN>                                      │    │   │
│  │  └─────────────────────────────────────────────────────────────────────┘    │   │
│  │                                                                              │   │
│  │  Level 3: 证书管理 (cert-manager / AWS ACM)                                  │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │  │  TLS Secret: skyone-tls                                             │    │   │
│  │  │  ├── tls.crt: <证书公钥>                                            │    │   │
│  │  │  └── tls.key: <证书私钥>                                            │    │   │
│  │  └─────────────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Kubernetes Secret 注入                               │   │
│  │                                                                              │   │
│  │  secret.yaml:                                                               │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │  │  apiVersion: v1                                                      │    │   │
│  │  │  kind: Secret                                                        │    │   │
│  │  │  metadata:                                                          │    │   │
│  │  │    name: skyone-secrets                                             │    │   │
│  │  │    namespace: skyone-prod                                           │    │   │
│  │  │  type: Opaque                                                       │    │   │
│  │  │  stringData:                                                        │    │   │
│  │  │    DATABASE_URL: postgresql://<用户名>:<密码>@<主机>:5432/skyone  │    │   │
│  │  │    SECRET_KEY: <生成的 64 字符随机密钥>                            │    │   │
│  │  │    LLM_API_KEY: <API Key>                                          │    │   │
│  │  │    LLM_BASE_URL: <Base URL>                                         │    │   │
│  │  │    GRAFANA_PASSWORD: <Grafana 密码>                                  │    │   │
│  │  └─────────────────────────────────────────────────────────────────────┘    │   │
│  │                                                                              │   │
│  │  api-deployment.yaml (引用 Secret):                                          │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │  │  env:                                                               │    │   │
│  │  │    - name: DATABASE_URL                                            │    │   │
│  │  │      valueFrom:                                                    │    │   │
│  │  │        secretKeyRef:                                                │    │   │
│  │  │          name: skyone-secrets                                      │    │   │
│  │  │          key: DATABASE_URL                                         │    │   │
│  │  │    - name: SECRET_KEY                                              │    │   │
│  │  │      valueFrom:                                                    │    │   │
│  │  │        secretKeyRef:                                                │    │   │
│  │  │          name: skyone-secrets                                      │    │   │
│  │  │          key: SECRET_KEY                                           │    │   │
│  │  │    - name: LLM_API_KEY                                             │    │   │
│  │  │      valueFrom:                                                    │    │   │
│  │  │        secretKeyRef:                                                │    │   │
│  │  │          name: skyone-secrets                                      │    │   │
│  │  │          key: LLM_API_KEY                                          │    │   │
│  │  └─────────────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 二、监控告警规则架构

### 2.1 Prometheus 告警规则

```yaml
# prometheus/rules/skyone-alerts.yml
groups:
  # ============================================
  # 服务可用性告警
  # ============================================
  - name: skyone_availability
    interval: 30s
    rules:
      - alert: SkyOneAPIInstanceDown
        expr: up{job="skyone-api"} == 0
        for: 1m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "SkyOne API 实例不可用"
          description: "SkyOne API 实例 {{ $labels.instance }} 已停止运行超过 1 分钟"

      - alert: SkyOneWorkerDown
        expr: |
          (count(celery_worker_up == 0) by (job) / count(celery_worker_up) by (job)) > 0.5
        for: 2m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "SkyOne Celery Worker 半数以上实例不可用"
          description: "超过 50% 的 Celery Worker 实例不可用"

      - alert: SkyOneHighErrorRate
        expr: |
          rate(skyone_http_requests_total{status=~"5.."}[5m])
          / rate(skyone_http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "SkyOne API 错误率高于 5%"
          description: "过去 5 分钟内，API 错误率 (5xx) 为 {{ $value | humanizePercentage }}"

      - alert: SkyOneCriticalErrorRate
        expr: |
          rate(skyone_http_requests_total{status=~"5.."}[5m])
          / rate(skyone_http_requests_total[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "SkyOne API 严重错误率高于 1%"
          description: "过去 2 分钟内，API 严重错误率 (5xx) 为 {{ $value | humanizePercentage }}"

  # ============================================
  # 性能指标告警
  # ============================================
  - name: skyone_performance
    interval: 30s
    rules:
      - alert: SkyOneHighLatencyP95
        expr: |
          histogram_quantile(0.95, 
            rate(skyone_http_request_duration_seconds_bucket[5m])
          ) > 2
        for: 10m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "SkyOne API P95 延迟高于 2 秒"
          description: "API P95 响应时间为 {{ $value | humanizeDuration }}"

      - alert: SkyOneCriticalLatencyP99
        expr: |
          histogram_quantile(0.99, 
            rate(skyone_http_request_duration_seconds_bucket[5m])
          ) > 5
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "SkyOne API P99 延迟高于 5 秒"
          description: "API P99 响应时间为 {{ $value | humanizeDuration }}"

      - alert: SkyOneHighLLMLatency
        expr: |
          histogram_quantile(0.95,
            rate(skyone_llm_request_duration_seconds_bucket[5m])
          ) > 30
        for: 5m
        labels:
          severity: warning
          team: ai
        annotations:
          summary: "SkyOne LLM 请求延迟高于 30 秒"
          description: "LLM 请求 P95 延迟为 {{ $value | humanizeDuration }}"

      - alert: SkyOneHighMemoryUsage
        expr: |
          (container_memory_working_set_bytes{container="api"}
          / container_spec_memory_limit_bytes{container="api"}) > 0.85
        for: 5m
        labels:
          severity: warning
          team: ops
        annotations:
          summary: "SkyOne API 内存使用率高于 85%"
          description: "API 容器内存使用率为 {{ $value | humanizePercentage }}"

      - alert: SkyOneCriticalMemoryUsage
        expr: |
          (container_memory_working_set_bytes{container="api"}
          / container_spec_memory_limit_bytes{container="api"}) > 0.95
        for: 1m
        labels:
          severity: critical
          team: ops
        annotations:
          summary: "SkyOne API 内存使用率高于 95%"
          description: "API 容器内存即将耗尽，当前使用率为 {{ $value | humanizePercentage }}"

      - alert: SkyOneHighCPUUsage
        expr: |
          rate(container_cpu_usage_seconds_total{container="api"}[5m])
          / container_spec_cpu_quota{container="api"} > 0.80
        for: 10m
        labels:
          severity: warning
          team: ops
        annotations:
          summary: "SkyOne API CPU 使用率持续高于 80%"
          description: "API 容器 CPU 使用率为 {{ $value | humanizePercentage }}"

  # ============================================
  # 业务指标告警
  # ============================================
  - name: skyone_business
    interval: 60s
    rules:
      - alert: SkyOneHighQuotaUsage
        expr: |
          skyone_quota_usage_percentage > 80
        for: 5m
        labels:
          severity: warning
          team: product
        annotations:
          summary: "SkyOne 用户配额使用率高于 80%"
          description: "用户 {{ $labels.user_id }} 的 {{ $labels.quota_type }} 配额已使用 {{ $value | humanizePercentage }}"

      - alert: SkyOneQuotaExceeded
        expr: |
          skyone_quota_exceeded_total > 0
        for: 1m
        labels:
          severity: warning
          team: product
        annotations:
          summary: "SkyOne 用户配额超限"
          description: "用户 {{ $labels.user_id }} 的 {{ $labels.quota_type }} 配额已超限"

      - alert: SkyOneHighLLMCost
        expr: |
          increase(skyone_llm_cost_usd_total[1h]) > 100
        for: 5m
        labels:
          severity: warning
          team: finance
        annotations:
          summary: "SkyOne LLM 成本每小时增长超过 $100"
          description: "过去 1 小时 LLM 成本增长 ${{ $value | humanize }}"

      - alert: SkyOneDocumentProcessingBacklog
        expr: |
          sum(celery_queue_length{queue="documents"}) > 100
        for: 15m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "SkyOne 文档处理队列积压超过 100"
          description: "文档处理队列积压 {{ $value }} 个任务"

      - alert: SkyOneSearchLatencyHigh
        expr: |
          histogram_quantile(0.95,
            rate(skyone_search_duration_seconds_bucket[5m])
          ) > 1
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "SkyOne 搜索 P95 延迟高于 1 秒"
          description: "搜索请求 P95 延迟为 {{ $value | humanizeDuration }}"

  # ============================================
  # 基础设施告警
  # ============================================
  - name: skyone_infrastructure
    interval: 30s
    rules:
      - alert: SkyOneRedisDown
        expr: |
          redis_up{job="skyone-redis"} == 0
        for: 1m
        labels:
          severity: critical
          team: ops
        annotations:
          summary: "SkyOne Redis 不可用"
          description: "Redis 实例不可用超过 1 分钟"

      - alert: SkyOneRedisHighMemory
        expr: |
          redis_memory_used_bytes / redis_memory_max_bytes > 0.85
        for: 5m
        labels:
          severity: warning
          team: ops
        annotations:
          summary: "SkyOne Redis 内存使用率高于 85%"
          description: "Redis 内存使用率为 {{ $value | humanizePercentage }}"

      - alert: SkyOneRedisHighConnections
        expr: |
          redis_connected_clients > 10000
        for: 5m
        labels:
          severity: warning
          team: ops
        annotations:
          summary: "SkyOne Redis 连接数高于 10000"
          description: "Redis 连接数为 {{ $value }}"

      - alert: SkyOneDatabaseConnectionPoolExhausted
        expr: |
          sqla_pooloverflow > 10
        for: 5m
        labels:
          severity: warning
          team: ops
        annotations:
          summary: "SkyOne 数据库连接池溢出"
          description: "数据库连接池溢出次数: {{ $value }}"
```

### 2.2 告警阈值配置模板

```yaml
# prometheus/rules/thresholds.yml
# 可配置的告警阈值模板，支持通过 ConfigMap 动态更新

apiVersion: v1
kind: ConfigMap
metadata:
  name: skyone-alert-thresholds
  namespace: skyone-prod
data:
  # 性能阈值
  latency_p95_threshold: "2"           # 秒
  latency_p99_threshold: "5"           # 秒
  error_rate_warning: "0.05"          # 5%
  error_rate_critical: "0.01"          # 1%
  
  # 资源阈值
  memory_usage_warning: "0.85"         # 85%
  memory_usage_critical: "0.95"        # 95%
  cpu_usage_warning: "0.80"           # 80%
  
  # 业务阈值
  quota_usage_warning: "0.80"         # 80%
  llm_cost_per_hour_warning: "100"    # 美元
  queue_backlog_warning: "100"        # 任务数
  
  # 基础设施阈值
  redis_memory_warning: "0.85"        # 85%
  redis_connections_warning: "10000"  # 连接数
```

### 2.3 告警路由与通知渠道

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Alertmanager 告警路由架构                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Alertmanager 配置                                     │   │
│  │                                                                              │   │
│  │  alertmanager.yml:                                                           │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │  │  global:                                                           │    │   │
│  │  │    resolve_timeout: 5m                                             │    │   │
│  │  │    smtp_smarthost: 'smtp.gmail.com:587'                          │    │   │
│  │  │    smtp_from: 'alerts@skyskyone.com'                              │    │   │
│  │  │    smtp_auth_username: 'alerts@skyskyone.com'                    │    │   │
│  │  │    smtp_auth_password: '<password>'                               │    │   │
│  │  │                                                                   │    │   │
│  │  │  templates:                                                       │    │   │
│  │  │    - '/etc/alertmanager/templates/*.tmpl'                         │    │   │
│  │  │                                                                   │    │   │
│  │  │  route:                                                           │    │   │
│  │  │    group_by: ['alertname', 'severity', 'team']                   │    │   │
│  │  │    group_wait: 30s                                                │    │   │
│  │  │    group_interval: 5m                                             │    │   │
│  │  │    repeat_interval: 4h                                            │    │   │
│  │  │    receiver: 'default-receiver'                                  │    │   │
│  │  │                                                                   │    │   │
│  │  │    routes:                                                        │    │   │
│  │  │    # Critical 级别 - 立即通知 + 电话                                │    │   │
│  │  │    - match: { severity: critical }                                │    │   │
│  │  │      receiver: 'critical-receiver'                               │    │   │
│  │  │      group_wait: 0s                                               │    │   │
│  │  │      repeat_interval: 1h                                          │    │   │
│  │  │                                                                   │    │   │
│  │  │    # 后端团队告警                                                  │    │   │
│  │  │    - match: { team: backend }                                     │    │   │
│  │  │      receiver: 'backend-receiver'                                │    │   │
│  │  │      routes:                                                      │    │   │
│  │  │        - match: { severity: critical }                            │    │   │
│  │  │          receiver: 'pagerduty-critical'                          │    │   │
│  │  │                                                                   │    │   │
│  │  │    # AI 团队告警                                                  │    │   │
│  │  │    - match: { team: ai }                                          │    │   │
│  │  │      receiver: 'ai-receiver'                                     │    │   │
│  │  │                                                                   │    │   │
│  │  │    # 运维团队告警                                                  │    │   │
│  │  │    - match: { team: ops }                                          │    │   │
│  │  │      receiver: 'ops-receiver'                                     │    │   │
│  │  │                                                                   │    │   │
│  │  │    # 财务告警 - 仅工作时间                                        │    │   │
│  │  │    - match: { team: finance }                                     │    │   │
│  │  │      receiver: 'finance-receiver'                                 │    │   │
│  │  │      mute_time_intervals:                                         │    │   │
│  │  │        - off-hours                                                │    │   │
│  │  │                                                                   │    │   │
│  │  │  inhibit_rules:                                                   │    │   │
│  │  │    # 当实例 down 时，抑制该实例的所有其他告警                        │    │   │
│  │  │    - source_match: { alertname: 'SkyOneAPIInstanceDown' }        │    │   │
│  │  │      source_labels: [instance]                                    │    │   │
│  │  │      equal: [instance]                                            │    │   │
│  │  │      target_match: { severity: warning }                          │    │   │
│  │  │      target_re: 'SkyOne.*'                                       │    │   │
│  │  │                                                                   │    │   │
│  │  │  receivers:                                                       │    │   │
│  │  │  - name: 'default-receiver'                                      │    │   │
│  │  │    email_configs:                                                 │    │   │
│  │  │    - to: 'team@skyskyone.com'                                    │    │   │
│  │  │                                                                   │    │   │
│  │  │  - name: 'critical-receiver'                                     │    │   │
│  │  │    slack_configs:                                                 │    │   │
│  │  │    - channel: '#alerts-critical'                                 │    │   │
│  │  │      send_resolved: true                                          │    │   │
│  │  │      webhook_url: '<slack_webhook_url>'                          │    │   │
│  │  │    email_configs:                                                 │    │   │
│  │  │    - to: 'on-call@skyskyone.com'                                 │    │   │
│  │  │                                                                   │    │   │
│  │  │  - name: 'pagerduty-critical'                                    │    │   │
│  │  │    pagerduty_configs:                                             │    │   │
│  │  │    - service_key: '<pagerduty_service_key>'                     │    │   │
│  │  │      severity: critical                                          │    │   │
│  │  │      description: '{{ .GroupLabels.alertname }}'                  │    │   │
│  │  │      details:                                                     │    │   │
│  │  │        severity: '{{ .Labels.severity }}'                         │    │   │
│  │  │        team: '{{ .Labels.team }}'                                 │    │   │
│  │  │                                                                   │    │   │
│  │  │  - name: 'backend-receiver'                                       │    │   │
│  │  │    slack_configs:                                                 │    │   │
│  │  │    - channel: '#alerts-backend'                                  │    │   │
│  │  │                                                                   │    │   │
│  │  │  - name: 'ops-receiver'                                          │    │   │
│  │  │    slack_configs:                                                 │    │   │
│  │  │    - channel: '#alerts-ops'                                     │    │   │
│  │  │    email_configs:                                                 │    │   │
│  │  │    - to: 'ops-team@skyskyone.com'                               │    │   │
│  │  │                                                                   │    │   │
│  │  │  - name: 'ai-receiver'                                          │    │   │
│  │  │    slack_configs:                                                 │    │   │
│  │  │    - channel: '#alerts-ai'                                       │    │   │
│  │  │                                                                   │    │   │
│  │  │  - name: 'finance-receiver'                                      │    │   │
│  │  │    email_configs:                                                 │    │   │
│  │  │    - to: 'finance@skyskyone.com'                                │    │   │
│  │  │                                                                   │    │   │
│  │  │  time_intervals:                                                   │    │   │
│  │  │  - name: off-hours                                               │    │   │
│  │  │    time_intervals:                                               │    │   │
│  │  │    - weekdays: 'off-hours'                                       │    │   │
│  │  │      times:                                                       │    │   │
│  │  │      - start_time: '18:00'                                       │    │   │
│  │  │        end_time: '09:00'                                         │    │   │
│  │  └─────────────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 告警升级策略

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              告警升级策略                                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           告警升级流程                                          │   │
│  │                                                                              │   │
│  │  Level 1: Warning (0 min) ──────────────────────────────────────────────►   │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  通知方式: Slack #alerts-{team}                                      │  │   │
│  │  │  响应时间: 30 分钟内                                                  │  │   │
│  │  │  处理人: 当值工程师                                                   │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                    │                                        │   │
│  │                                    ▼ (未响应 30 分钟)                         │   │
│  │  Level 2: Warning Escalation ────────────────────────────────────────►   │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  通知方式: + 邮件发送给团队负责人                                      │  │   │
│  │  │  响应时间: 15 分钟内                                                  │  │   │
│  │  │  处理人: 团队 Tech Lead                                               │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                    │                                        │   │
│  │                                    ▼ (未响应 15 分钟)                         │   │
│  │  Level 3: Critical Immediate ────────────────────────────────────────►   │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  通知方式: PagerDuty 呼叫 + Slack #alerts-critical @on-call        │  │   │
│  │  │  响应时间: 5 分钟内                                                   │  │   │
│  │  │  处理人: On-Call 工程师                                              │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                    │                                        │   │
│  │                                    ▼ (未响应 5 分钟)                          │   │
│  │  Level 4: Critical Escalation ────────────────────────────────────────►   │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  通知方式: 电话呼叫 On-Call + 短信给部门经理                          │  │   │
│  │  │  响应时间: 立即                                                       │  │   │
│  │  │  处理人: 部门经理 / CTO                                              │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           告警聚合与去重策略                                    │   │
│  │                                                                              │   │
│  │  Group By: alertname + severity + team                                       │   │
│  │  Group Wait: 30 秒 (等待是否有相关告警一起发出)                                │   │
│  │  Group Interval: 5 分钟 (首次告警后，5 分钟内的同类告警聚合)                  │   │
│  │  Repeat Interval: 4 小时 (告警未解决，4 小时后重复通知)                       │   │
│  │                                                                              │   │
│  │  去重规则:                                                                   │   │
│  │  - 相同 alertname + labels 在 24 小时内只发送一次                            │   │
│  │  - resolved 状态也会发送一次通知                                             │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 三、性能压测与优化架构

### 3.1 压测工具选型

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              压测工具对比与选型                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌───────────────────┬────────────────────────┬────────────────────────┐            │
│  │     维度          │        JMeter          │          k6            │            │
│  ├───────────────────┼────────────────────────┼────────────────────────┤            │
│  │ 协议支持          │ HTTP, JDBC, SOAP, JMS  │ HTTP, gRPC, WebSocket  │            │
│  │                   │ Kafka, MQTT 等        │ SQL, Prometheus 等    │            │
│  ├───────────────────┼────────────────────────┼────────────────────────┤            │
│  │ 学习曲线          │ 陡峭 (GUI 操作)         │ 平缓 (JavaScript DSL)  │            │
│  ├───────────────────┼────────────────────────┼────────────────────────┤            │
│  │ 分布式压测         │ 支持 (Master-Slave)    │ 支持 (k6 operator)    │            │
│  ├───────────────────┼────────────────────────┼────────────────────────┤            │
│  │ 报告能力          │ 丰富 (Dashboard)        │ 内置 (InfluxDB/Graf)  │            │
│  ├───────────────────┼────────────────────────┼────────────────────────┤            │
│  │ CI/CD 集成        │ 一般 (Maven/Ant)       │ 优秀 (原生支持)         │            │
│  ├───────────────────┼────────────────────────┼────────────────────────┤            │
│  │ 资源消耗           │ 较高                   │ 低                    │            │
│  ├───────────────────┼────────────────────────┼────────────────────────┤            │
│  │ 推荐场景          │ 复杂协议、传统企业测试   │ 云原生、微服务、API    │            │
│  └───────────────────┴────────────────────────┴────────────────────────┘            │
│                                                                                      │
│  最终选型:                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  工具        │ 用途                        │ 部署方式                        │   │
│  ├──────────────┼─────────────────────────────┼───────────────────────────────┤   │
│  │  k6          │ 主要压测工具 (API、WebSocket) │ Docker / Kubernetes           │   │
│  │  JMeter      │ 复杂场景、JDBC 测试          │ 独立部署                        │   │
│  │  Locust      │ Python 用户自定义场景       │ 独立部署 / distributed         │   │
│  │  Prometheus   │ 压测指标收集                │ 复用现有监控栈                  │   │
│  │  Grafana     │ 压测结果可视化              │ 复用现有监控栈                  │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 k6 压测场景设计

```javascript
// k6/scenarios/api-load-test.js
import http from 'k6/http';
import websocket from 'k6/ws';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// ============================================
// 自定义指标定义
// ============================================
const successRate = new Rate('success_rate');
const apiLatency = new Trend('api_latency');
const searchLatency = new Trend('search_latency');
const llmLatency = new Trend('llm_latency');
const errorCounter = new Counter('error_count');

// ============================================
// 测试配置
// ============================================
export const options = {
  // 场景1: 基础负载测试 (SLA 验证)
  scenarios: {
    baseline_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },    // 0 → 50 VU (2分钟)
        { duration: '5m', target: 50 },    // 保持 50 VU (5分钟)
        { duration: '2m', target: 0 },     // 50 → 0 VU (2分钟)
      ],
      tags: { scenario: 'baseline' },
    },

    // 场景2: 峰值负载测试
    peak_load: {
      executor: 'ramping-arrival-rate',
      startRate: 1,
      timeUnit: '1s',
      preAllocatedVUs: 100,
      maxVUs: 500,
      stages: [
        { duration: '1m', target: 10 },    // 10 req/s
        { duration: '2m', target: 50 },    // 50 req/s
        { duration: '3m', target: 100 },  // 100 req/s
        { duration: '1m', target: 200 },  // 200 req/s (峰值)
        { duration: '2m', target: 100 },  // 100 req/s
        { duration: '1m', target: 0 },    // 停止
      ],
      tags: { scenario: 'peak' },
    },

    // 场景3: 压力测试 (找瓶颈)
    stress_test: {
      executor: 'peak-growth',
      startTime: '30s',
      stages: [
        { duration: '5m', target: 500 },   // 逐步增加到 500 VU
      ],
      tags: { scenario: 'stress' },
    },

    // 场景4: 浸泡测试 (长期稳定性)
    soak_test: {
      executor: 'constant-vus',
      vus: 50,
      duration: '8h',
      tags: { scenario: 'soak' },
    },

    // 场景5: 尖刺测试 (突发流量)
    spike_test: {
      executor: 'stepping-arrival-rate',
      startRate: 10,
      steps: [
        { duration: '1m', target: 10 },   // 10 req/s
        { duration: '10s', target: 200 },  // 尖刺到 200 req/s
        { duration: '5m', target: 200 },  // 保持 5 分钟
        { duration: '10s', target: 10 },   // 恢复到 10 req/s
        { duration: '5m', target: 10 },   // 观察恢复
      ],
      tags: { scenario: 'spike' },
    },
  },

  // 阈值 (SLA 定义)
  thresholds: {
    // HTTP 指标
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],
    'http_req_failed': ['rate<0.01'],  // 错误率 < 1%

    // 自定义指标
    'api_latency': ['p(95)<300', 'p(99)<800'],
    'search_latency': ['p(95)<1000', 'p(99)<2000'],
    'llm_latency': ['p(95)<30000', 'p(99)<60000'],

    // 成功率
    'success_rate': ['rate>0.99'],

    // 告警阈值
    'error_count': ['count<100'],
  },

  // 全局标签
  tags: {
    service: 'skyone-api',
    version: 'v3.0.18',
  },
};

// ============================================
// 测试数据生成
// ============================================
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

function generateTestUser(index) {
  return {
    email: `loadtest${index}@example.com`,
    name: `Load Test User ${index}`,
  };
}

// ============================================
// 测试场景
// ============================================
export default function () {
  // 模拟真实用户行为
  group('Search Flow', () => {
    // 1. 用户登录
    const loginRes = http.post(
      `${BASE_URL}/api/v1/auth/login`,
      JSON.stringify({
        email: `loadtest${__VU}@example.com`,
        password: 'testpassword',
      }),
      { headers: { 'Content-Type': 'application/json' } }
    );

    let token = null;
    if (loginRes.status === 200) {
      token = loginRes.json('access_token');
      successRate.add(1);
    } else {
      successRate.add(0);
      errorCounter.add(1, { type: 'login_failed' });
      return;
    }

    // 2. 执行搜索
    const searchRes = http.get(
      `${BASE_URL}/api/v1/search`,
      {
        params: {
          q: 'test query',
          limit: 20,
        },
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    );

    const searchSuccess = check(searchRes, {
      'search status 200': (r) => r.status === 200,
      'search has results': (r) => r.json('total') > 0,
    });

    successRate.add(searchSuccess);
    searchLatency.add(searchRes.timings.duration);

    if (!searchSuccess) {
      errorCounter.add(1, { type: 'search_failed' });
    }

    sleep(1);

    // 3. 查看文档详情
    if (searchRes.status === 200 && searchRes.json('items').length > 0) {
      const docId = searchRes.json('items')[0].id;
      const docRes = http.get(
        `${BASE_URL}/api/v1/documents/${docId}`,
        {
          headers: { 'Authorization': `Bearer ${token}` },
        }
      );

      check(docRes, {
        'doc status 200': (r) => r.status === 200,
      });

      successRate.add(docRes.status === 200);
    }

    sleep(2);
  });

  group('Document Upload Flow', () => {
    // 1. 获取上传 URL
    const uploadRes = http.post(
      `${BASE_URL}/api/v1/documents/upload-url`,
      JSON.stringify({
        filename: `test-${__VU}-${__ITER}.pdf`,
        content_type: 'application/pdf',
        size: 1024 * 1024, // 1MB
      }),
      {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      }
    );

    if (uploadRes.status !== 200) {
      successRate.add(0);
      errorCounter.add(1, { type: 'upload_url_failed' });
      return;
    }

    // 2. 上传到 OSS (简化)
    const uploadUrl = uploadRes.json('upload_url');
    const fileData = http.put(
      uploadUrl,
      Array(1024 * 1024).fill('x').join(''), // 1MB 假数据
      {
        headers: {
          'Content-Type': 'application/pdf',
        },
      }
    );

    check(uploadRes, {
      'upload success': (r) => r.status === 200,
    });

    sleep(3);
  });

  group('LLM Query Flow', () => {
    // LLM 查询 (受限于 API 成本，QPS 较低)
    const llmRes = http.post(
      `${BASE_URL}/api/v1/llm/query`,
      JSON.stringify({
        query: 'Summarize the document',
        document_ids: ['doc1', 'doc2'],
        model: 'gpt-4',
      }),
      {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        tags: { name: 'llm' },
      }
    );

    const llmSuccess = check(llmRes, {
      'llm status 200': (r) => r.status === 200,
      'llm has response': (r) => r.json('answer') !== undefined,
    });

    successRate.add(llmSuccess);
    llmLatency.add(llmRes.timings.duration);

    if (!llmSuccess) {
      errorCounter.add(1, { type: 'llm_failed' });
    }

    sleep(5);
  });

  // WebSocket 连接测试 (单独运行)
  if (__Config.scenario === 'websocket') {
    const wsUrl = BASE_URL.replace('http', 'ws') + '/ws';
    const ws = new websocket.WebSocket(wsUrl, null, {
      headers: { 'Authorization': `Bearer ${token}` },
    });

    ws.onOpen = () => {
      ws.send(JSON.stringify({ type: 'ping' }));
    };

    ws.onMessage = (msg) => {
      const data = JSON.parse(msg);
      if (data.type === 'pong') {
        successRate.add(1);
      }
    };

    ws.onError = (e) => {
      successRate.add(0);
      errorCounter.add(1, { type: 'ws_error' });
    };

    ws.sleep(10);
    ws.close();
  }
}
```

### 3.3 性能指标与基线

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              性能指标与基线定义                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           API 性能基线                                         │   │
│  │                                                                              │   │
│  │  端点类型              │ 指标         │ 日常基线  │ 峰值基线  │ 告警阈值      │   │
│  │  ─────────────────────┼──────────────┼───────────┼───────────┼──────────────│   │
│  │  简单查询              │ P50 (ms)     │ < 20      │ < 50      │ > 100        │   │
│  │  (GET /metrics 等)    │ P95 (ms)     │ < 50      │ < 100     │ > 200        │   │
│  │                       │ P99 (ms)     │ < 100     │ < 200     │ > 500        │   │
│  │                       │ Error Rate   │ < 0.1%    │ < 0.5%    │ > 1%         │   │
│  │  ─────────────────────┼──────────────┼───────────┼───────────┼──────────────│   │
│  │  中等复杂度             │ P50 (ms)     │ < 100     │ < 200     │ > 500        │   │
│  │  (POST /search 等)    │ P95 (ms)     │ < 300     │ < 500     │ > 1000       │   │
│  │                       │ P99 (ms)     │ < 800     │ < 1000    │ > 2000       │   │
│  │                       │ Error Rate   │ < 0.5%    │ < 1%      │ > 3%         │   │
│  │  ─────────────────────┼──────────────┼───────────┼───────────┼──────────────│   │
│  │  复杂查询              │ P50 (ms)     │ < 500     │ < 1000    │ > 2000       │   │
│  │  (POST /llm/query 等) │ P95 (ms)     │ < 2000    │ < 5000    │ > 10000      │   │
│  │                       │ P99 (ms)     │ < 5000    │ < 10000   │ > 30000      │   │
│  │                       │ Error Rate   │ < 1%      │ < 3%      │ > 5%         │   │
│  │  ─────────────────────┼──────────────┼───────────┼───────────┼──────────────│   │
│  │  搜索功能              │ P50 (ms)     │ < 200     │ < 500     │ > 1000       │   │
│  │  (ES 查询)            │ P95 (ms)     │ < 800     │ < 1500    │ > 3000       │   │
│  │                       │ P99 (ms)     │ < 1500    │ < 3000    │ > 5000       │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           系统级性能基线                                       │   │
│  │                                                                              │   │
│  │  指标                    │ 目标值        │ 峰值目标      │ 绝对上限           │   │
│  │  ───────────────────────┼───────────────┼──────────────┼────────────────────│   │
│  │  API QPS (综合)         │ 500 req/s     │ 1000 req/s   │ 2000 req/s        │   │
│  │  并发用户数             │ 200           │ 500          │ 1000              │   │
│  │  CPU 使用率             │ < 60%         │ < 75%        │ > 85%             │   │
│  │  Memory 使用率          │ < 70%         │ < 80%        │ > 90%             │   │
│  │  Redis 连接数           │ < 5000        │ < 8000       │ > 10000           │   │
│  │  数据库连接池使用率      │ < 60%         │ < 80%        │ > 90%             │   │
│  │  网络 I/O (Mbps)        │ < 500         │ < 1000       │ > 2000            │   │
│  │  磁盘 I/O (IOPS)        │ < 5000        │ < 10000      │ > 20000           │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           容量规划对照表                                       │   │
│  │                                                                              │   │
│  │  并发用户数    │ 预估 QPS    │ API 实例数  │ Worker 数   │ Redis 内存       │   │
│  │  ────────────┼────────────┼────────────┼────────────┼──────────────────│   │
│  │  50           │ 100         │ 2           │ 2           │ 1 GB             │   │
│  │  200          │ 400         │ 3           │ 4           │ 2 GB             │   │
│  │  500          │ 1000        │ 5           │ 6           │ 4 GB             │   │
│  │  1000         │ 2000        │ 8           │ 10          │ 8 GB             │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 瓶颈分析与优化方案

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              瓶颈分析与优化方案                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           1. 数据库瓶颈                                        │   │
│  │                                                                              │   │
│  │  瓶颈表现:                                                                   │   │
│  │  - 连接池耗尽 (ORA-12541, too many connections)                               │   │
│  │  - 查询延迟增加 (P99 > 500ms)                                                │   │
│  │  - 锁等待时间增加                                                            │   │
│  │                                                                              │   │
│  │  诊断命令:                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  # 查看连接数                                                          │  │   │
│  │  │  SELECT count(*) FROM pg_stat_activity WHERE state = 'active';       │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 查看慢查询                                                          │  │   │
│  │  │  SELECT query, calls, mean_time, total_time FROM pg_stat_statements  │  │   │
│  │  │  ORDER BY total_time DESC LIMIT 10;                                 │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 查看锁等待                                                          │  │   │
│  │  │  SELECT * FROM pg_locks WHERE NOT granted;                          │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  │  优化方案:                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  1. 连接池优化 (PgBouncer)                                           │  │   │
│  │  │     - pool_mode: transaction                                         │  │   │
│  │  │     - max_client_conn: 1000                                          │  │   │
│  │  │     - default_pool_size: 50                                          │  │   │
│  │  │     - server_idle_timeout: 600s                                       │  │   │
│  │  │                                                                     │  │   │
│  │  │  2. 读写分离                                                          │  │   │
│  │  │     - 读请求路由到 replica                                            │  │   │
│  │  │     - 写请求路由到 primary                                            │  │   │
│  │  │                                                                     │  │   │
│  │  │  3. 查询优化                                                          │  │   │
│  │  │     - 添加适当索引                                                    │  │   │
│  │  │     - 使用 EXPLAIN ANALYZE 分析执行计划                               │  │   │
│  │  │     - 避免 N+1 查询                                                   │  │   │
│  │  │                                                                     │  │   │
│  │  │  4. 缓存热点数据                                                       │  │   │
│  │  │     - 用户配置等静态数据缓存到 Redis                                   │  │   │
│  │  │     - 缓存 TTL: 5-30 分钟                                             │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           2. Redis 瓶颈                                        │   │
│  │                                                                              │   │
│  │  瓶颈表现:                                                                   │   │
│  │  - redis-oom: 内存不足                                                      │   │
│  │  - 延迟突增 (> 10ms)                                                        │   │
│  │  - 连接数耗尽                                                                │   │
│  │                                                                              │   │
│  │  优化方案:                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  1. 内存优化                                                          │  │   │
│  │  │     - maxmemory: 2gb                                                 │  │   │
│  │  │     - maxmemory-policy: allkeys-lru (非严格场景)                     │  │   │
│  │  │     - 合理设置 TTL                                                    │  │   │
│  │  │                                                                     │  │   │
│  │  │  2. 连接池优化 (Redis Cluster / Sentinel)                            │  │   │
│  │  │     - 使用连接池而非直连                                               │  │   │
│  │  │     - max_connections: 10000                                         │  │   │
│  │  │                                                                     │  │   │
│  │  │  3. 热点 Key 优化                                                      │  │   │
│  │  │     - 使用 Redis Cluster 分散热点                                     │  │   │
│  │  │     - 本地缓存 + Redis 二级缓存                                        │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           3. API 服务瓶颈                                      │   │
│  │                                                                              │   │
│  │  瓶颈表现:                                                                   │   │
│  │  - CPU 使用率 > 80%                                                          │   │
│  │  - 请求排队 (Pending Requests)                                               │   │
│  │  - HPA 频繁扩容                                                             │   │
│  │                                                                              │   │
│  │  优化方案:                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  1. 水平扩展 (HPA)                                                    │  │   │
│  │  │     - minReplicas: 3                                                │  │   │
│  │  │     - maxReplicas: 20                                               │  │   │
│  │  │     - targetCPUUtilizationPercentage: 70                            │  │   │
│  │  │                                                                     │  │   │
│  │  │  2. 异步处理                                                          │  │   │
│  │  │     - 非关键请求异步化 (Webhook, 通知)                                │  │   │
│  │  │     - 使用 Celery 任务队列                                            │  │   │
│  │  │                                                                     │  │   │
│  │  │  3. 限流保护                                                          │  │   │
│  │  │     - API 限流: 100 req/s/用户                                        │  │   │
│  │  │     - 整体限流: 1000 req/s                                            │  │   │
│  │  │                                                                     │  │   │
│  │  │  4. 代码优化                                                          │  │   │
│  │  │     - 使用 asyncio 异步 I/O                                           │  │   │
│  │  │     - 减少同步阻塞调用                                                │  │   │
│  │  │     - 使用 Cython 优化热点代码                                        │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           4. LLM API 瓶颈                                     │   │
│  │                                                                              │   │
│  │  瓶颈表现:                                                                   │   │
│  │  - LLM 请求延迟 > 30s                                                        │   │
│  │  - Token 配额耗尽                                                            │   │
│  │  - API 429 错误增多                                                          │   │
│  │                                                                              │   │
│  │  优化方案:                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  1. 多 API Key 负载均衡                                               │  │   │
│  │  │     - 配置多个 API Key                                                │  │   │
│  │  │     - 轮询或加权分发请求                                              │  │   │
│  │  │                                                                     │  │   │
│  │  │  2. 请求缓存                                                          │  │   │
│  │  │     - 相同 query 的结果缓存 5 分钟                                    │  │   │
│  │  │     - 基于 query hash 缓存                                           │  │   │
│  │  │                                                                     │  │   │
│  │  │  3. 模型降级                                                          │  │   │
│  │  │     - 优先使用 GPT-3.5 (低延迟、低成本)                               │  │   │
│  │  │     - 仅复杂查询使用 GPT-4                                            │  │   │
│  │  │                                                                     │  │   │
│  │  │  4. 批量处理                                                          │  │   │
│  │  │     - 合并多个文档分析请求                                            │  │   │
│  │  │     - 使用 async/await 并发处理                                       │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 四、文档完善与用户手册架构

### 4.1 用户文档结构

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              用户文档站点架构                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  文档站点: https://docs.skyskyone.com                                                │
│  技术栈: MkDocs + Material Theme + GitHub Pages                                     │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           文档目录结构                                         │   │
│  │                                                                              │   │
│  │  docs/                                                                         │   │
│  │  ├── index.md                      # 文档首页                                  │   │
│  │  ├── getting-started/                                                     │   │
│  │  │   ├── index.md                  # 快速开始                                │   │
│  │  │   ├── installation.md           # 安装部署                                │   │
│  │  │   ├── configuration.md          # 配置指南                                │   │
│  │  │   └── quick-start.md            # 5 分钟快速上手                           │   │
│  │  │                                                                     │   │
│  │  ├── user-guide/                                                          │   │
│  │  │   ├── index.md                  # 用户指南目录                            │   │
│  │  │   ├── authentication.md         # 认证授权                                │   │
│  │  │   ├── documents.md              # 文档管理                                │   │
│  │  │   ├── search.md                 # 搜索功能                                │   │
│  │  │   ├── collaboration.md          # 协作功能                                │   │
│  │  │   ├── notifications.md          # 通知设置                                │   │
│  │  │   └── quota-management.md       # 配额管理                                │   │
│  │  │                                                                     │   │
│  │  ├── api-reference/                                                         │   │
│  │  │   ├── index.md                  # API 文档目录                            │   │
│  │  │   ├── authentication.md         # 认证方式                                │   │
│  │  │   ├── documents-api.md         # 文档 API                                │   │
│  │  │   ├── search-api.md            # 搜索 API                                │   │
│  │  │   ├── llm-api.md               # LLM API                                │   │
│  │  │   ├── monitoring-api.md        # 监控 API                                │   │
│  │  │   ├── rate-limit-api.md        # 限流 API                                │   │
│  │  │   ├── cache-api.md             # 缓存 API                                │   │
│  │  │   └── websocket-api.md         # WebSocket API                           │   │
│  │  │                                                                     │   │
│  │  ├── admin-guide/                                                         │   │
│  │  │   ├── index.md                  # 运维指南目录                            │   │
│  │  │   ├── deployment.md             # 部署运维                                │   │
│  │  │   ├── monitoring.md            # 监控告警                                │   │
│  │  │   ├── backup-restore.md        # 备份恢复                                │   │
│  │  │   ├── troubleshooting.md       # 故障排查                                │   │
│  │  │   ├── performance-tuning.md    # 性能调优                                │   │
│  │  │   └── security.md              # 安全配置                                │   │
│  │  │                                                                     │   │
│  │  ├── developer-guide/                                                      │   │
│  │  │   ├── index.md                  # 开发指南目录                            │   │
│  │  │   ├── architecture.md          # 系统架构                                │   │
│  │  │   ├── local-development.md     # 本地开发                                │   │
│  │  │   ├── testing.md               # 测试指南                                │   │
│  │  │   ├── contributing.md          # 贡献指南                                │   │
│  │  │   └── changelog.md             # 更新日志                                │   │
│  │  │                                                                     │   │
│  │  └── reference/                                                           │   │
│  │      ├── config-reference.md     # 配置参数参考                            │   │
│  │      ├── error-codes.md          # 错误码参考                              │   │
│  │      ├── cli-reference.md        # CLI 命令参考                            │   │
│  │      └── webhook-events.md       # Webhook 事件                            │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 API 文档示例

```markdown
# API Reference - 搜索 API

## POST /api/v1/search

执行混合搜索，结合关键词匹配和向量相似度。

### 请求

**Headers**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 是 | Bearer {token} |
| Content-Type | string | 是 | application/json |

**Body**

```json
{
  "q": "string",              // 搜索关键词 (必填)
  "top_k": 10,                // 返回结果数量 (默认 10, 最大 100)
  "search_mode": "hybrid",    // 搜索模式: hybrid/keyword/vector (默认 hybrid)
  "filters": {                // 可选过滤条件
    "document_type": ["pdf", "doc"],
    "date_range": {
      "start": "2026-01-01",
      "end": "2026-12-31"
    },
    "tags": ["技术", "产品"],
    "owner_id": "user_xxx"
  },
  "include_highlights": true,  // 是否返回高亮片段 (默认 true)
  "rerank": false             // 是否启用重排序 (默认 false)
}
```

### 响应

**200 OK**

```json
{
  "total": 125,
  "items": [
    {
      "id": "doc_abc123",
      "title": "产品需求文档 v2.0",
      "snippet": "...搜索关键词在上下文中<em>高亮</em>显示...",
      "score": 0.95,
      "document_type": "pdf",
      "created_at": "2026-03-15T10:30:00Z",
      "updated_at": "2026-04-01T14:20:00Z",
      "highlights": [
        "...这是包含搜索关键词的<em>高亮</em>片段..."
      ]
    }
  ],
  "query_time_ms": 45,
  "search_mode": "hybrid"
}
```

### 错误

| 状态码 | 错误码 | 描述 |
|--------|--------|------|
| 400 | INVALID_REQUEST | 请求参数错误 |
| 401 | UNAUTHORIZED | 未认证或 token 无效 |
| 403 | QUOTA_EXCEEDED | 搜索配额已用尽 |
| 429 | RATE_LIMITED | 请求过于频繁 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

### 示例

```bash
curl -X POST https://api.skyskyone.com/api/v1/search \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "q": "产品需求文档",
    "top_k": 5,
    "search_mode": "hybrid",
    "filters": {
      "document_type": ["pdf"]
    }
  }'
```
</syntaxhighlight>
```

### 4.3 运维手册目录

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              运维手册目录                                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ## 1. 日常运维操作                                                                 │
│                                                                                      │
│  ### 1.1 服务状态检查                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  # 检查所有服务状态                                                          │   │
│  │  kubectl get pods -n skyone-prod                                           │   │
│  │                                                                           │   │
│  │  # 检查 API 服务日志                                                        │   │
│  │  kubectl logs -n skyone-prod -l app=skyone-api --tail=100 -f              │   │
│  │                                                                           │   │
│  │  # 检查 Worker 任务队列                                                     │   │
│  │  celery -A skyone_shuge inspect active                                   │   │
│  │                                                                           │   │
│  │  # 检查 Redis 状态                                                          │   │
│  │  redis-cli -h redis.svc.cluster.local ping                                │   │
│  │  redis-cli -h redis.svc.cluster.local info clients                        │   │
│  │                                                                           │   │
│  │  # 检查数据库连接                                                           │   │
│  │  SELECT count(*) FROM pg_stat_activity;                                   │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ### 1.2 监控指标检查                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  Grafana Dashboard: https://grafana.skyskyone.com                          │   │
│  │                                                                           │   │
│  │  重点关注:                                                                  │   │
│  │  - API 请求 QPS 和延迟                                                      │   │
│  │  - 错误率 (5xx)                                                            │   │
│  │  - LLM Token 使用量                                                         │   │
│  │  - 队列积压情况                                                             │   │
│  │  - CPU / Memory 使用率                                                      │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ## 2. 常见故障处理                                                                 │
│                                                                                      │
│  ### 2.1 API 服务不可用                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  1. 检查 Pod 状态                                                           │   │
│  │     kubectl get pods -n skyone-prod -l app=skyone-api                     │   │
│  │                                                                           │   │
│  │  2. 查看 Pod 日志                                                           │   │
│  │     kubectl logs -n skyone-prod <pod-name> --previous                      │   │
│  │                                                                           │   │
│  │  3. 检查 HPA 是否触发扩容                                                   │   │
│  │     kubectl get hpa -n skyone-prod                                         │   │
│  │                                                                           │   │
│  │  4. 重启服务 (如果需要)                                                     │   │
│  │     kubectl rollout restart deployment/skyone-api -n skyone-prod           │   │
│  │                                                                           │   │
│  │  5. 回滚到上一版本 (如果需要)                                               │   │
│  │     kubectl rollout undo deployment/skyone-api -n skyone-prod            │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ### 2.2 任务队列积压                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  1. 查看队列长度                                                             │   │
│  │     celery -A skyone_shuge inspect stats                                   │   │
│  │                                                                           │   │
│  │  2. 查看活跃 Worker                                                          │   │
│  │     kubectl get pods -n skyone-prod -l app=skyone-worker                  │   │
│  │                                                                           │   │
│  │  3. 扩容 Worker                                                             │   │
│  │     kubectl scale deployment/skyone-worker -n skyone-prod --replicas=8    │   │
│  │                                                                           │   │
│  │  4. 清理过期任务                                                             │   │
│  │     celery -A skyone_shuge purge -Q documents,embeddings                 │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ### 2.3 数据库连接问题                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  1. 检查连接池状态                                                           │   │
│  │     # PgBouncer 管理界面                                                    │   │
│  │     psql -h pgbouncer -p 6432 -U pgbouncer -c "SHOW POOLS"               │   │
│  │                                                                           │   │
│  │  2. 检查慢查询                                                              │   │
│  │     SELECT * FROM pg_stat_activity WHERE state = 'active'                 │   │
│  │                                                                           │   │
│  │  3. 重启 PgBouncer (谨慎)                                                   │   │
│  │     kubectl rollout restart deployment/pgbouncer -n skyone-prod           │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ## 3. 变更操作流程                                                                 │
│                                                                                      │
│  ### 3.1 配置变更                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  1. 提交变更申请 (包含变更内容、原因、预期影响)                               │   │
│  │  2. 在测试环境验证                                                          │   │
│  │  3. 配置变更使用 ConfigMap/Secret                                           │   │
│  │     kubectl apply -f configmap-updated.yaml -n skyone-prod                │   │
│  │  4. 滚动更新 Pod                                                           │   │
│  │     kubectl rollout restart deployment/skyone-api -n skyone-prod         │   │
│  │  5. 验证服务正常                                                             │   │
│  │  6. 记录变更日志                                                            │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ### 3.2 版本发布                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  1. 创建 Release Branch                                                    │   │
│  │     git checkout -b release/v3.0.18                                        │   │
│  │  2. 更新版本号和 Changelog                                                  │   │
│  │  3. 提交 PR 并审查                                                          │   │
│  │  4. 合并到 main                                                            │   │
│  │  5. CI/CD 自动构建镜像                                                      │   │
│  │  6. 在 Staging 环境验证                                                     │   │
│  │  7. 使用 Helm 升级 Production                                               │   │
│  │     helm upgrade skyone skyone-shuge -f values-prod.yaml -n skyone-prod │   │
│  │  8. 监控关键指标 30 分钟                                                     │   │
│  │  9. 如有问题立即回滚                                                        │   │
│  │     helm rollback skyone -n skyone-prod                                   │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ## 4. 应急响应                                                                 │
│                                                                                      │
│  ### 4.1 告警响应 SLA                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  Critical: 5 分钟内响应，30 分钟内恢复                                       │   │
│  │  Warning:  30 分钟内响应，2 小时内恢复                                       │   │
│  │  Info:     工作时间内响应，24 小时内处理                                     │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ### 4.2 重大故障处理                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  1. 立即切换到故障模式 (启用 Incident Commander)                              │   │
│  │  2. 评估影响范围和时间                                                        │   │
│  │  3. 启动应急预案 (降级、回滚、限流)                                           │   │
│  │  4. 通知相关方 (用户、团队、管理层)                                           │   │
│  │  5. 故障恢复后提交复盘报告                                                    │   │
│  │  6. 制定改进措施防止复发                                                     │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.4 故障排查指南

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              故障排查流程图                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│                           用户报告问题                                                │
│                                │                                                    │
│                                ▼                                                    │
│                    ┌─────────────────────┐                                          │
│                    │  问题分类            │                                          │
│                    └──────────┬──────────┘                                          │
│                               │                                                    │
│            ┌──────────────────┼──────────────────┐                                │
│            │                  │                  │                                │
│            ▼                  ▼                  ▼                                │
│    ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                         │
│    │  功能性问题    │  │  性能问题      │  │  可用性问题    │                         │
│    │  (功能不工作)  │  │  (响应慢)      │  │  (服务不可用)  │                         │
│    └───────┬───────┘  └───────┬───────┘  └───────┬───────┘                         │
│            │                  │                  │                                  │
│            ▼                  ▼                  ▼                                  │
│    ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                         │
│    │ 1. 检查 API   │  │ 1. 检查监控    │  │ 1. 检查状态    │                         │
│    │    返回错误码  │  │    仪表盘     │  │    页面        │                         │
│    │               │  │              │  │               │                         │
│    │ 2. 查看 API   │  │ 2. 分析延迟   │  │ 2. 检查 Pod   │                         │
│    │    服务日志   │  │    分布      │  │    状态       │                         │
│    │               │  │              │  │               │                         │
│    │ 3. 检查数据   │  │ 3. 检查资源   │  │ 3. 检查资源   │                         │
│    │    完整性     │  │    使用      │  │    使用       │                         │
│    │               │  │              │  │               │                         │
│    │ 4. 复现问题   │  │ 4. 压力测试   │  │ 4. 查看事件   │                         │
│    │               │  │    定位瓶颈  │  │    日志      │                         │
│    └───────┬───────┘  └───────┬───────┘  └───────┬───────┘                         │
│            │                  │                  │                                  │
│            └──────────────────┼──────────────────┘                                  │
│                               │                                                    │
│                               ▼                                                    │
│                    ┌─────────────────────┐                                          │
│                    │  制定解决方案        │                                          │
│                    └──────────┬──────────┘                                          │
│                               │                                                    │
│            ┌──────────────────┼──────────────────┐                                │
│            │                  │                  │                                │
│            ▼                  ▼                  ▼                                │
│    ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                         │
│    │  配置修复     │  │  扩容/优化     │  │  重启/回滚    │                         │
│    └───────┬───────┘  └───────┬───────┘  └───────┬───────┘                         │
│            │                  │                  │                                  │
│            └──────────────────┼──────────────────┘                                  │
│                               │                                                    │
│                               ▼                                                    │
│                    ┌─────────────────────┐                                          │
│                    │  验证并关闭问题      │                                          │
│                    └─────────────────────┘                                          │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 文件结构

```
skyone-shuge/
├── docker-compose.prod.yml             # 生产 Docker 配置
├── Dockerfile.prod                      # 生产环境 Dockerfile
├── helm/
│   ├── Chart.yaml                       # Helm Chart 定义
│   ├── values.yaml                      # 默认 values
│   ├── values-prod.yaml                 # 生产环境 values
│   ├── values-staging.yaml              # 预发环境 values
│   └── templates/                        # K8s 资源模板
├── kubernetes/
│   ├── namespace.yaml                    # Namespace 定义
│   ├── configmap.yaml                    # ConfigMap
│   ├── secrets.yaml                      # Secrets 模板
│   ├── api-deployment.yaml               # API Deployment
│   ├── worker-deployment.yaml            # Worker Deployment
│   ├── api-service.yaml                  # API Service
│   ├── ingress.yaml                     # Ingress
│   ├── hpa.yaml                         # HPA 配置
│   ├── pdb.yaml                         # PodDisruptionBudget
│   └── servicemonitor.yaml              # Prometheus 监控
├── prometheus/
│   ├── prometheus.yml                   # Prometheus 配置
│   ├── rules/
│   │   ├── skyone-alerts.yml            # 告警规则
│   │   └── skyone-recording-rules.yml  # 记录规则
│   └── alertmanager.yml                 # Alertmanager 配置
├── k6/
│   ├── scenarios/
│   │   ├── api-load-test.js            # API 负载测试
│   │   ├── websocket-test.js            # WebSocket 测试
│   │   └── stress-test.js               # 压力测试
│   └── config/
│       └── thresholds.yml              # 性能阈值配置
├── docs/                                # 用户文档 (MkDocs)
│   ├── docs/
│   │   ├── getting-started/
│   │   ├── user-guide/
│   │   ├── api-reference/
│   │   ├── admin-guide/
│   │   └── developer-guide/
│   └── mkdocs.yml                       # MkDocs 配置
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                       # CI/CD 流水线
│   │   └── release.yml                  # Release 流程
│   └── actions/
│       ├── deploy-staging/
│       └── deploy-production/
├── prd/
│   └── MVP_v3.0.18.md                   # 本 PRD 文档
└── architecture/
    └── ARCHITECTURE_v3.0.18.md         # 架构文档
```

---

## ✅ 验收标准

### 部署配置
- [ ] Helm Chart 可一键部署到 Kubernetes
- [ ] Docker Compose 生产配置可运行
- [ ] CI/CD 流水线正常工作
- [ ] 环境变量和 Secrets 管理规范

### 监控告警
- [ ] Prometheus 告警规则完整
- [ ] Alertmanager 路由配置正确
- [ ] 告警通知可正常发送 (邮件、Slack、PagerDuty)
- [ ] 告警升级策略已定义

### 性能压测
- [ ] k6 压测脚本可执行
- [ ] 性能基线已建立
- [ ] 瓶颈分析文档完整
- [ ] 优化方案已制定

### 文档完善
- [ ] MkDocs 文档站点可构建
- [ ] API 文档完整
- [ ] 运维手册内容完整
- [ ] 故障排查指南可用

---

## 📧 邮件发送

**发送命令**:
```bash
# 发送代码包邮件
python scripts/send_code_email.py

# 发送 PRD 邮件
python scripts/send_prd_email.py --version v3.0.18
```

**收件人**: broadbtinp@gmail.com, dulie@foxmail.com
