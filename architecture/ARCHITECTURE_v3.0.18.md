# 天一阁架构文档 v3.0.18

**版本**: v3.0.18
**日期**: 2026-04-09
**主题**: 生产环境部署 + 监控告警 + 性能压测优化 + 用户手册

---

## 📋 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0.18 | 2026-04-09 | 生产环境部署配置 + 监控告警规则 + 性能压测优化 + 用户手册 |
| v3.0.17 | 2026-04-08 | 监控/限流/缓存 API 实现 + 前后端联调 + 端到端测试 |
| v3.0.16 | 2026-04-05 | 实现代码开发 + 前端 UI 组件开发 + 单元测试与集成测试 |
| v3.0.15 | 2026-04-04 | 监控架构 + 限流架构 + 多级缓存架构 + 性能优化架构 + 搜索增强架构 + LLM 成本追踪架构 |

---

## 🏗️ 系统架构总览

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              完整生产环境架构                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           用户访问层 (External)                                 │   │
│  │                                                                              │   │
│  │   浏览器 / 移动端 ──► CDN ──► 负载均衡器 (SLB)                               │   │
│  │                                │                                              │   │
│  │                                ▼                                              │   │
│  │   Grafana / Prometheus ──► 内网访问 (带 Auth Proxy)                        │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Kubernetes 集群 (K8s)                                │   │
│  │                                                                              │   │
│  │   ┌────────────────────────────────────────────────────────────────────┐   │   │
│  │   │                    Namespace: skyone-prod                           │   │   │
│  │   │                                                                    │   │   │
│  │   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │   │   │
│  │   │   │ skyone-api │  │skyone-worker│  │ skyone-beat │  │ nginx   │ │   │   │
│  │   │   │  (3 pods)  │  │  (4 pods)  │  │  (1 pod)   │  │ ingress │ │   │   │
│  │   │   └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │   │   │
│  │   │         │                 │                                    │      │   │
│  │   └─────────┼─────────────────┼────────────────────────────────────┘      │   │
│  │             │                 │                                             │   │
│  │   ┌─────────┴─────────────────┴────────────────────────────────────┐      │   │
│  │   │                    数据层 (PVC / ConfigMap / Secret)             │      │   │
│  │   │                                                                    │      │   │
│  │   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │      │   │
│  │   │   │   Redis    │  │ PostgreSQL  │  │    S3      │              │      │   │
│  │   │   │  (Cluster) │  │   (RDS)    │  │  (OSS)     │              │      │   │
│  │   │   └─────────────┘  └─────────────┘  └─────────────┘              │      │   │
│  │   └────────────────────────────────────────────────────────────────┘      │   │
│  │                                                                              │   │
│  │   ┌────────────────────────────────────────────────────────────────────┐   │   │
│  │   │                    监控层 (Prometheus Stack)                        │   │   │
│  │   │                                                                    │   │   │
│  │   │   ServiceMonitor ──► Prometheus ──► Alertmanager ──► 通知渠道     │   │   │
│  │   │          │                                  │                       │   │   │
│  │   │          ▼                                  ▼                       │   │   │
│  │   │   kube-state-metrics ──► Grafana (Dashboards)                       │   │   │
│  │   └────────────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 一、生产环境部署架构

### 1.1 Kubernetes 部署架构

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Kubernetes 集群架构                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           多环境 Namespace 设计                                  │   │
│  │                                                                              │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐               │   │
│  │  │  skyone-prod    │  │ skyone-staging  │  │   skyone-dev   │               │   │
│  │  │  ────────────  │  │  ────────────  │  │  ────────────  │               │   │
│  │  │  replicas: 3-10 │  │  replicas: 2    │  │  replicas: 1   │               │   │
│  │  │  resources: 高  │  │  resources: 中  │  │  resources: 低  │               │   │
│  │  │  PDB: 2 min     │  │  PDB: 1 min    │  │  PDB: 0        │               │   │
│  │  │  HPA: 70% CPU   │  │  无 HPA        │  │  无 HPA        │               │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘               │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Pod 反亲和性设计                                      │   │
│  │                                                                              │   │
│  │  # 避免同一服务的多个 Pod 调度到同一节点                                        │   │
│  │  affinity:                                                                  │   │
│  │    podAntiAffinity:                                                         │   │
│  │      preferredDuringSchedulingIgnoredDuringExecution:                       │   │
│  │        - weight: 100                                                        │   │
│  │          podAffinityTerm:                                                   │   │
│  │            labelSelector:                                                   │   │
│  │              matchLabels:                                                   │   │
│  │                app: skyone-api                                             │   │
│  │            topologyKey: kubernetes.io/hostname                             │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           资源配额设计                                          │   │
│  │                                                                              │   │
│  │  ResourceQuota:                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  # 命名空间级别 CPU/Memory 限制                                         │  │   │
│  │  │  spec:                                                               │  │   │
│  │  │    hard:                                                            │  │   │
│  │  │      requests.cpu: "20"                                            │  │   │
│  │  │      requests.memory: "40Gi"                                       │  │   │
│  │  │      limits.cpu: "40"                                              │  │   │
│  │  │      limits.memory: "80Gi"                                         │  │   │
│  │  │      pods: "50"                                                    │  │   │
│  │  │      services: "20"                                                │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  │  LimitRange:                                                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  # 每个 Pod 的默认资源限制                                            │  │   │
│  │  │  spec:                                                               │  │   │
│  │  │    limits:                                                          │  │   │
│  │  │      - type: Pod                                                    │  │   │
│  │  │        max:                                                         │  │   │
│  │  │          cpu: "4"                                                   │  │   │
│  │  │          memory: "8Gi"                                              │  │   │
│  │  │      - type: Container                                               │  │   │
│  │  │        default:                                                     │  │   │
│  │  │          cpu: "500m"                                                │  │   │
│  │  │          memory: "512Mi"                                            │  │   │
│  │  │        defaultRequest:                                               │  │   │
│  │  │          cpu: "200m"                                                │  │   │
│  │  │          memory: "256Mi"                                            │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Helm Chart 详细设计

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Helm Chart 核心配置                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Chart.yaml                                           │   │
│  │                                                                              │   │
│  │  apiVersion: v2                                                             │   │
│  │  name: skyone-shuge                                                         │   │
│  │  version: 3.0.18                                                            │   │
│  │  appVersion: "v3.0.18"                                                     │   │
│  │  description: SkyOne Shuge - Intelligent Document Management Platform       │   │
│  │                                                                              │   │
│  │  keywords:                                                                 │   │
│  │    - document-management                                                   │   │
│  │    - rag                                                                   │   │
│  │    - knowledge-base                                                        │   │
│  │                                                                              │   │
│  │  maintainers:                                                              │   │
│  │    - name: SkyOne Team                                                     │   │
│  │      email: team@skyskyone.com                                             │   │
│  │                                                                              │   │
│  │  dependencies:                                                              │   │
│  │    - name: postgresql                                                      │   │
│  │      version: "12.x.x"                                                     │   │
│  │      repository: "https://charts.bitnami.com/bitnami"                      │   │
│  │      condition: postgresql.enabled                                         │   │
│  │    - name: redis                                                          │   │
│  │      version: "18.x.x"                                                     │   │
│  │      repository: "https://charts.bitnami.com/bitnami"                      │   │
│  │      condition: redis.enabled                                             │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           values-prod.yaml (生产环境)                          │   │
│  │                                                                              │   │
│  │  image:                                                                   │   │
│  │    repository: registry.skyskyone.com/skyone/shuge                       │   │
│  │    tag: "v3.0.18"                                                        │   │
│  │    pullPolicy: IfNotPresent                                              │   │
│  │    pullSecrets:                                                          │   │
│  │      - name: skyone-registry                                             │   │
│  │                                                                         │   │
│  │  api:                                                                    │   │
│  │    replicaCount: 3                                                       │   │
│  │    autoscaling:                                                          │   │
│  │      enabled: true                                                       │   │
│  │      minReplicas: 3                                                      │   │
│  │      maxReplicas: 10                                                     │   │
│  │      targetCPUUtilizationPercentage: 70                                  │   │
│  │      targetMemoryUtilizationPercentage: 80                                │   │
│  │    podDisruptionBudget:                                                  │   │
│  │      enabled: true                                                       │   │
│  │      minAvailable: 2                                                     │   │
│  │    resources:                                                            │   │
│  │      requests: { cpu: 500m, memory: 512Mi }                              │   │
│  │      limits: { cpu: 2000m, memory: 2Gi }                                  │   │
│  │    livenessProbe: { failureThreshold: 3, periodSeconds: 10 }             │   │
│  │    readinessProbe: { failureThreshold: 3, periodSeconds: 5 }             │   │
│  │                                                                         │   │
│  │  worker:                                                                 │   │
│  │    replicaCount: 4                                                       │   │
│  │    resources:                                                            │   │
│  │      requests: { cpu: 1000m, memory: 1Gi }                               │   │
│  │      limits: { cpu: 4000m, memory: 4Gi }                                 │   │
│  │    concurrency: 4                                                        │   │
│  │    maxTasksPerChild: 1000                                                │   │
│  │                                                                         │   │
│  │  redis:                                                                  │   │
│  │    enabled: true                                                         │   │
│  │    architecture: replication                                             │   │
│  │    auth:                                                                  │   │
│  │      enabled: true                                                        │   │
│  │      secretKeyRef: { name: skyone-secrets, key: REDIS_PASSWORD }        │   │
│  │    master:                                                                │   │
│  │      persistence:                                                        │   │
│  │        enabled: true                                                     │   │
│  │        size: 10Gi                                                        │   │
│  │        storageClass: "ssd"                                               │   │
│  │    replica:                                                               │   │
│  │      replicaCount: 2                                                     │   │
│  │                                                                         │   │
│  │  postgresql:                                                             │   │
│  │    enabled: false  # 使用外部 RDS                                         │   │
│  │                                                                         │   │
│  │  ingress:                                                                │   │
│  │    enabled: true                                                         │   │
│  │    className: nginx                                                      │   │
│  │    annotations:                                                          │   │
│  │      cert-manager.io/cluster-issuer: "letsencrypt-prod"                  │   │
│  │      nginx.ingress.kubernetes.io/proxy-body-size: "100m"                  │   │
│  │      nginx.ingress.kubernetes.io/proxy-read-timeout: "300"              │   │
│  │    hosts:                                                                 │   │
│  │      - host: api.skyskyone.com                                           │   │
│  │        paths:                                                            │   │
│  │          - path: /                                                       │   │
│  │            pathType: Prefix                                              │   │
│  │    tls:                                                                  │   │
│  │      - secretName: skyone-tls                                            │   │
│  │        hosts: [api.skyskyone.com]                                        │   │
│  │                                                                         │   │
│  │  monitoring:                                                            │   │
│  │    enabled: true                                                         │   │
│  │    serviceMonitor:                                                       │   │
│  │      enabled: true                                                       │   │
│  │      interval: 15s                                                        │   │
│  │    prometheusRule:                                                       │   │
│  │      enabled: true                                                       │   │
│  │      rules: {}  # 使用默认规则                                             │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Docker Compose 生产配置

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Docker Compose 生产架构                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           服务分层架构                                         │   │
│  │                                                                              │   │
│  │   接入层                                                                      │   │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐                                    │   │
│  │   │  Nginx  │  │  API    │  │ Flower  │                                    │   │
│  │   │ Reverse │  │ FastAPI │  │ Monitor │                                    │   │
│  │   │  Proxy  │  │         │  │         │                                    │   │
│  │   └────┬────┘  └────┬────┘  └─────────┘                                    │   │
│  │        │           │                                                        │   │
│  │        └─────┬─────┘                                                        │   │
│  │              │                                                              │   │
│  │        数据层│                                                              │   │
│  │   ┌─────────┴─────────┐                                                   │   │
│  │   │                   │                                                    │   │
│  │   ▼                   ▼                                                    │   │
│  │ ┌──────┐  ┌──────────────┐  ┌──────────────┐                            │   │
│  │ │Redis │  │  PostgreSQL  │  │  Prometheus  │                            │   │
│  │ │Cache │  │   (RDS)     │  │   Metrics    │                            │   │
│  │ │ + MQ │  │             │  │              │                            │   │
│  │ └──────┘  └──────────────┘  └──────┬───────┘                            │   │
│  │                                      │                                      │   │
│  │                                ┌─────┴─────┐                               │   │
│  │                                │  Grafana  │                               │   │
│  │                                │ Dashboard │                               │   │
│  │                                └───────────┘                               │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Nginx 生产配置                                      │   │
│  │                                                                              │   │
│  │  nginx/nginx.conf:                                                          │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  worker_processes auto;                                               │  │   │
│  │  │  error_log /var/log/nginx/error.log warn;                            │  │   │
│  │  │  pid /var/run/nginx.pid;                                            │  │   │
│  │  │                                                                     │  │   │
│  │  │  events {                                                            │  │   │
│  │  │      worker_connections 10240;                                        │  │   │
│  │  │      multi_accept on;                                                │  │   │
│  │  │      use epoll;                                                      │  │   │
│  │  │  }                                                                   │  │   │
│  │  │                                                                     │  │   │
│  │  │  http {                                                              │  │   │
│  │  │      include /etc/nginx/mime.types;                                  │  │   │
│  │  │      default_type application/octet-stream;                          │  │   │
│  │  │                                                                     │  │   │
│  │  │      # 日志格式                                                       │  │   │
│  │  │      log_format main '$remote_addr - $remote_user [$time_local] '   │  │   │
│  │  │                        '"$request" $status $body_bytes_sent '        │  │   │
│  │  │                        '"$http_referer" "$http_user_agent" '         │  │   │
│  │  │                        'rt=$request_time uct="$upstream_connect_time"'; │  │   │
│  │  │                                                                     │  │   │
│  │  │      access_log /var/log/nginx/access.log main;                      │  │   │
│  │  │                                                                     │  │   │
│  │  │      # 性能优化                                                       │  │   │
│  │  │      sendfile on;                                                   │  │   │
│  │  │      tcp_nopush on;                                                 │  │   │
│  │  │      tcp_nodelay on;                                                │  │   │
│  │  │      keepalive_timeout 65;                                          │  │   │
│  │  │      types_hash_max_size 2048;                                      │  │   │
│  │  │                                                                     │  │   │
│  │  │      # Gzip 压缩                                                     │  │   │
│  │  │      gzip on;                                                       │  │   │
│  │  │      gzip_vary on;                                                  │  │   │
│  │  │      gzip_proxied any;                                              │  │   │
│  │  │      gzip_comp_level 6;                                             │  │   │
│  │  │      gzip_types text/plain text/css application/json                │  │   │
│  │  │                      application/javascript text/xml application/xml; │  │   │
│  │  │                                                                     │  │   │
│  │  │      # 上传限制                                                       │  │   │
│  │  │      client_max_body_size 100m;                                      │  │   │
│  │  │      client_body_buffer_size 10m;                                    │  │   │
│  │  │                                                                     │  │   │
│  │  │      # 代理配置                                                       │  │   │
│  │  │      proxy_http_version 1.1;                                        │  │   │
│  │  │      proxy_set_header Host $host;                                    │  │   │
│  │  │      proxy_set_header X-Real-IP $remote_addr;                       │  │   │
│  │  │      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;   │  │   │
│  │  │      proxy_set_header X-Forwarded-Proto $scheme;                   │  │   │
│  │  │      proxy_buffering on;                                             │  │   │
│  │  │      proxy_buffer_size 4k;                                         │  │   │
│  │  │      proxy_buffers 8 4k;                                           │  │   │
│  │  │      proxy_busy_buffers_size 8k;                                    │  │   │
│  │  │      proxy_connect_timeout 30s;                                      │  │   │
│  │  │      proxy_read_timeout 300s;                                       │  │   │
│  │  │      proxy_send_timeout 30s;                                        │  │   │
│  │  │  }                                                                   │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  │  nginx/conf.d/api.conf:                                                    │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  upstream skyone_api {                                               │  │   │
│  │  │      least_conn;  # 最少连接负载均衡                                  │  │   │
│  │  │      server api:8000 max_fails=3 fail_timeout=30s;                  │  │   │
│  │  │  }                                                                   │  │   │
│  │  │                                                                     │  │   │
│  │  │  server {                                                            │  │   │
│  │  │      listen 80;                                                     │  │   │
│  │  │      server_name api.skyskyone.com;                                 │  │   │
│  │  │                                                                     │  │   │
│  │  │      # 强制跳转 HTTPS                                                 │  │   │
│  │  │      if ($scheme = http) {                                          │  │   │
│  │  │          return 301 https://$server_name$request_uri;               │  │   │
│  │  │      }                                                               │  │   │
│  │  │                                                                     │  │   │
│  │  │      location / {                                                    │  │   │
│  │  │          proxy_pass http://skyone_api;                              │  │   │
│  │  │          # 限流                                                       │  │   │
│  │  │          limit_req zone=api_limit burst=100 nodelay;               │  │   │
│  │  │          limit_conn addr 10;                                        │  │   │
│  │  │      }                                                               │  │   │
│  │  │                                                                     │  │   │
│  │  │      # WebSocket                                                     │  │   │
│  │  │      location /ws {                                                 │  │   │
│  │  │          proxy_pass http://skyone_api;                             │  │   │
│  │  │          proxy_http_version 1.1;                                    │  │   │
│  │  │          proxy_set_header Upgrade $http_upgrade;                   │  │   │
│  │  │          proxy_set_header Connection "upgrade";                    │  │   │
│  │  │          proxy_read_timeout 86400s;                                  │  │   │
│  │  │      }                                                               │  │   │
│  │  │  }                                                                   │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 限流配置                                                           │  │   │
│  │  │  limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s; │  │   │
│  │  │  limit_conn_zone $binary_remote_addr zone=addr:10m;                 │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.4 环境隔离与灰度发布

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              灰度发布架构                                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           金丝雀发布流程                                       │   │
│  │                                                                              │   │
│  │   v3.0.17 (稳定版)                      v3.0.18 (金丝雀)                     │   │
│  │   ┌──────────────────┐                ┌──────────────────┐                   │   │
│  │   │  90% 流量        │ ────────────► │   10% 流量       │                   │   │
│  │   │                  │                │                  │                   │   │
│  │   │  3 pods (稳定)   │                │  1 pod (新版本)  │                   │   │
│  │   │                  │                │                  │                   │   │
│  │   │  监控: 正常告警   │                │  监控: 详细追踪   │                   │   │
│  │   └──────────────────┘                └──────────────────┘                   │   │
│  │          │                                    │                              │   │
│  │          └──────────────┬─────────────────────┘                              │   │
│  │                         │                                                     │   │
│  │                         ▼                                                     │   │
│  │              ┌──────────────────┐                                           │   │
│  │              │   指标对比分析    │                                           │   │
│  │              │  - 错误率         │                                           │   │
│  │              │  - 延迟 P95/P99   │                                           │   │
│  │              │  - 业务成功率     │                                           │   │
│  │              └────────┬─────────┘                                           │   │
│  │                       │                                                      │   │
│  │         ┌─────────────┴─────────────┐                                       │   │
│  │         │                           │                                        │   │
│  │         ▼                           ▼                                        │   │
│  │   指标正常                      指标异常                                     │   │
│  │   ┌──────────────┐           ┌──────────────┐                              │   │
│  │   │ 全量发布     │           │ 自动回滚      │                              │   │
│  │   │ v3.0.18     │           │ 保持 v3.0.17  │                              │   │
│  │   │ + 流量 100%  │           │ + 告警通知    │                              │   │
│  │   └──────────────┘           └──────────────┘                              │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Argo Rollouts 配置                                   │   │
│  │                                                                              │   │
│  │  api-rollout.yaml:                                                         │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  apiVersion: argoproj.io/v1alpha1                                   │  │   │
│  │  │  kind: Rollout                                                       │  │   │
│  │  │  metadata:                                                          │  │   │
│  │  │    name: skyone-api                                                 │  │   │
│  │  │  spec:                                                              │  │   │
│  │  │    replicas: 4                                                      │  │   │
│  │  │    strategy:                                                        │  │   │
│  │  │      canary:                                                       │  │   │
│  │  │        steps:                                                      │  │   │
│  │  │          - setWeight: 10                                           │  │   │
│  │  │          - pause: { duration: 10m }  # 观察 10 分钟                │  │   │
│  │  │          - setWeight: 30                                           │  │   │
│  │  │          - pause: { duration: 10m }                                │  │   │
│  │  │          - setWeight: 50                                           │  │   │
│  │  │          - pause: { duration: 5m }                                 │  │   │
│  │  │          - setWeight: 100                                          │  │   │
│  │  │        canaryMetadata:                                              │  │   │
│  │  │          labels:                                                    │  │   │
│  │  │            role: canary                                             │  │   │
│  │  │        stableMetadata:                                             │  │   │
│  │  │          labels:                                                    │  │   │
│  │  │            role: stable                                            │  │   │
│  │  │        trafficRouting:                                             │  │   │
│  │  │          nginx:                                                     │  │   │
│  │  │            configuration: api-nginx-config                          │  │   │
│  │  │        analysis:                                                   │  │   │
│  │  │          templates:                                                │  │   │
│  │  │            - templateName: success-rate                             │  │   │
│  │  │          args:                                                      │  │   │
│  │  │            - name: service-name                                     │  │   │
│  │  │              value: skyone-api-canary                              │  │   │
│  │  │        maxSurge: 1                                                  │  │   │
│  │  │        maxUnavailable: 0                                           │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔔 二、监控告警规则架构

### 2.1 Prometheus 指标体系

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              SkyOne 指标体系                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           指标分类与命名规范                                     │   │
│  │                                                                              │   │
│  │  前缀: skyone_                                                               │   │
│  │                                                                              │   │
│  │  ┌────────────────┬──────────────────────────────────────────────────────┐  │   │
│  │  │   类别         │   指标名称示例                                        │  │   │
│  │  ├────────────────┼──────────────────────────────────────────────────────┤  │   │
│  │  │ http_requests  │ skyone_http_requests_total                          │  │   │
│  │  │                │ skyone_http_request_duration_seconds                 │  │   │
│  │  │                │ skyone_http_requests_in_flight                      │  │   │
│  │  ├────────────────┼──────────────────────────────────────────────────────┤  │   │
│  │  │ llm            │ skyone_llm_requests_total                           │  │   │
│  │  │                │ skyone_llm_tokens_total                             │  │   │
│  │  │                │ skyone_llm_cost_usd_total                           │  │   │
│  │  │                │ skyone_llm_request_duration_seconds                  │  │   │
│  │  ├────────────────┼──────────────────────────────────────────────────────┤  │   │
│  │  │ cache          │ skyone_cache_hits_total                             │  │   │
│  │  │                │ skyone_cache_misses_total                           │  │   │
│  │  │                │ skyone_cache_operations_total                        │  │   │
│  │  │                │ skyone_cache_size_bytes                             │  │   │
│  │  ├────────────────┼──────────────────────────────────────────────────────┤  │   │
│  │  │ search         │ skyone_search_requests_total                        │  │   │
│  │  │                │ skyone_search_duration_seconds                      │  │   │
│  │  │                │ skyone_search_results_count                         │  │   │
│  │  ├────────────────┼──────────────────────────────────────────────────────┤  │   │
│  │  │ celery         │ skyone_celery_tasks_total                           │  │   │
│  │  │                │ skyone_celery_task_duration_seconds                 │  │   │
│  │  │                │ skyone_celery_queue_length                          │  │   │
│  │  │                │ skyone_celery_worker_up                             │  │   │
│  │  ├────────────────┼──────────────────────────────────────────────────────┤  │   │
│  │  │ quota          │ skyone_quota_usage_total                           │  │   │
│  │  │                │ skyone_quota_limit_total                            │  │   │
│  │  │                │ skyone_quota_exceeded_total                         │  │   │
│  │  ├────────────────┼──────────────────────────────────────────────────────┤  │   │
│  │  │ auth           │ skyone_auth_requests_total                         │  │   │
│  │  │                │ skyone_auth_failures_total                          │  │   │
│  │  │                │ skyone_active_sessions_total                        │  │   │
│  │  ├────────────────┼──────────────────────────────────────────────────────┤  │   │
│  │  │ document       │ skyone_documents_total                             │  │   │
│  │  │                │ skyone_document_processing_seconds                 │  │   │
│  │  │                │ skyone_document_upload_bytes_total                  │  │   │
│  │  └────────────────┴──────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Recording Rules (预聚合)                              │   │
│  │                                                                              │   │
│  │  skyone-recording-rules.yml:                                                │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  groups:                                                           │  │   │
│  │  │    - name: skyone_api_sli                                          │  │   │
│  │  │      interval: 30s                                                 │  │   │
│  │  │      rules:                                                        │  │   │
│  │  │        # API 可用性                                                  │  │   │
│  │  │        - record: skyone:api_availability:5m                       │  │   │
│  │  │          expr: |                                                    │  │   │
│  │  │            1 - (                                                        │  │   │
│  │  │              rate(skyone_http_requests_total{status=~"5.."}[5m])  │  │   │
│  │  │              / rate(skyone_http_requests_total[5m])                │  │   │
│  │  │            )                                                         │  │   │
│  │  │                                                                     │  │   │
│  │  │        # 请求率                                                       │  │   │
│  │  │        - record: skyone:api_request_rate:5m                        │  │   │
│  │  │          expr: rate(skyone_http_requests_total[5m])                │  │   │
│  │  │                                                                     │  │   │
│  │  │        # P99 延迟                                                     │  │   │
│  │  │        - record: skyone:api_latency_p99:5m                        │  │   │
│  │  │          expr: |                                                    │  │   │
│  │  │            histogram_quantile(0.99,                                 │  │   │
│  │  │              rate(skyone_http_request_duration_seconds_bucket[5m]) │  │   │
│  │  │            )                                                         │  │   │
│  │  │                                                                     │  │   │
│  │  │        # LLM 成本率                                                   │  │   │
│  │  │        - record: skyone:llm_cost_per_min:5m                        │  │   │
│  │  │          expr: rate(skyone_llm_cost_usd_total[5m]) * 60           │  │   │
│  │  │                                                                     │  │   │
│  │  │        # 缓存命中率                                                   │  │   │
│  │  │        - record: skyone:cache_hit_rate:5m                          │  │   │
│  │  │          expr: |                                                    │  │   │
│  │  │            rate(skyone_cache_hits_total[5m])                       │  │   │
│  │  │            / (                                                         │  │   │
│  │  │              rate(skyone_cache_hits_total[5m])                     │  │   │
│  │  │              + rate(skyone_cache_misses_total[5m])                │  │   │
│  │  │            )                                                         │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Grafana Dashboard 设计

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Grafana Dashboard 架构                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Dashboard 列表                                       │   │
│  │                                                                              │   │
│  │  1. SkyOne Overview (总览仪表盘)                                             │   │
│  │  2. SkyOne API Performance (API 性能)                                        │   │
│  │  3. SkyOne LLM Cost & Usage (LLM 成本)                                       │   │
│  │  4. SkyOne Cache Performance (缓存性能)                                       │   │
│  │  5. SkyOne Celery Workers (任务队列)                                         │   │
│  │  6. SkyOne Infrastructure (基础设施)                                         │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Overview Dashboard 面板布局                           │   │
│  │                                                                              │   │
│  │  Row 1: SLI 概览 (4 列)                                                      │   │
│  │  ┌────────────┬────────────┬────────────┬────────────┐                       │   │
│  │  │ 可用性      │ 请求率      │ P99 延迟   │ 错误率     │                       │   │
│  │  │ 99.9%      │ 500 rps    │ 150ms     │ 0.1%      │                       │   │
│  │  └────────────┴────────────┴────────────┴────────────┘                       │   │
│  │                                                                              │   │
│  │  Row 2: 时间序列图 (2 列)                                                    │   │
│  │  ┌───────────────────────────┬───────────────────────────┐                   │   │
│  │  │  请求量趋势                │  延迟分布                  │                   │   │
│  │  │  [Line Chart]             │  [Heatmap]               │                   │   │
│  │  └───────────────────────────┴───────────────────────────┘                   │   │
│  │                                                                              │   │
│  │  Row 3: 服务状态 (2 列)                                                      │   │
│  │  ┌───────────────────────────┬───────────────────────────┐                   │   │
│  │  │  Pod 状态                  │  队列积压                  │                   │   │
│  │  │  [Status Panel]           │  [Bar Chart]              │                   │   │
│  │  └───────────────────────────┴───────────────────────────┘                   │   │
│  │                                                                              │   │
│  │  Row 4: 业务指标 (3 列)                                                      │   │
│  │  ┌──────────────┬──────────────┬──────────────┐                            │   │
│  │  │ LLM Token   │ 活跃用户     │ 文档处理     │                            │   │
│  │  │ 今日: 1.2M   │ 在线: 150    │ 队列: 25     │                            │   │
│  │  └──────────────┴──────────────┴──────────────┘                            │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Dashboard Provisioning                               │   │
│  │                                                                              │   │
│  │  grafana/provisioning/dashboards/dashboards.yml:                            │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  apiVersion: 1                                                     │  │   │
│  │  │                                                                     │  │   │
│  │  │  providers:                                                        │  │   │
│  │  │    - name: 'SkyOne Dashboards'                                     │  │   │
│  │  │      orgId: 1                                                       │  │   │
│  │  │      folder: 'SkyOne'                                              │  │   │
│  │  │      type: file                                                     │  │   │
│  │  │      disableDeletion: false                                        │  │   │
│  │  │      editable: true                                                │  │   │
│  │  │      options:                                                       │  │   │
│  │  │        path: /etc/grafana/provisioning/dashboards/skyone            │  │   │
│  │  │                                                                     │  │   │
│  │  │  - name: 'SkyOne Datasources'                                      │  │   │
│  │  │    orgId: 1                                                         │  │   │
│  │  │    folder: ''                                                       │  │   │
│  │  │    type: file                                                       │  │   │
│  │  │    disableDeletion: false                                          │  │   │
│  │  │    updateIntervalSeconds: 60                                        │  │   │
│  │  │    allowUiUpdates: true                                            │  │   │
│  │  │    options:                                                         │  │   │
│  │  │      path: /etc/grafana/provisioning/datasources                    │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Alertmanager 告警路由

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              告警生命周期管理                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           告警生命周期                                          │   │
│  │                                                                              │   │
│  │   ┌─────────────┐                                                           │   │
│  │   │   Pending   │  ◄── 告警规则触发，但未达到 for 时间                        │   │
│  │   │  (等待中)    │                                                           │   │
│  │   └──────┬──────┘                                                           │   │
│  │          │ 达到 for 时间                                                     │   │
│  │          ▼                                                                  │   │
│  │   ┌─────────────┐                                                           │   │
│  │   │   Firing   │  ◄── 告警激活，发送通知                                     │   │
│  │   │  (触发中)    │      - 计算 group_key                                     │   │
│  │   └──────┬──────┘      - 路由到对应 receiver                                 │   │
│  │          │                                                                  │   │
│  │          │ 条件恢复                                                          │   │
│  │          ▼                                                                  │   │
│  │   ┌─────────────┐                                                           │   │
│  │   │  Resolved   │  ◄── 发送 resolved 通知                                   │   │
│  │   │  (已恢复)    │      (部分 receiver 支持)                                 │   │
│  │   └─────────────┘                                                           │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           告警模板 (Go template)                               │   │
│  │                                                                              │   │
│  │  templates/skyone-alerts.tmpl:                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  {{ define "skyone.html_alert" }}                                   │  │   │
│  │  │  <html>                                                             │  │   │
│  │  │  <body>                                                             │  │   │
│  │  │    <h2>{{ .Status | toUpper }} - {{ .Labels.alertname }}</h2>        │  │   │
│  │  │    <p><strong>严重程度:</strong> {{ .Labels.severity }}</p>         │  │   │
│  │  │    <p><strong>团队:</strong> {{ .Labels.team }}</p>                  │  │   │
│  │  │    <p><strong>实例:</strong> {{ .Labels.instance }}</p>              │  │   │
│  │  │    <p><strong>时间:</strong> {{ .StartsAt }}</p>                     │  │   │
│  │  │    <hr/>                                                             │  │   │
│  │  │    <h3>描述</h3>                                                     │  │   │
│  │  │    <p>{{ .Annotations.description }}</p>                             │  │   │
│  │  │    <h3>摘要</h3>                                                     │  │   │
│  │  │    <p>{{ .Annotations.summary }}</p>                                │  │   │
│  │  │    <h3>当前值</h3>                                                   │  │   │
│  │  │    <pre>{{ .Annotations.current_value }}</pre>                      │  │   │
│  │  │    <hr/>                                                             │  │   │
│  │  │    <p><small>此告警由 SkyOne 监控系统生成</small></p>                │  │   │
│  │  │  </body>                                                             │  │   │
│  │  │  </html>                                                             │  │   │
│  │  │  {{ end }}                                                          │  │   │
│  │  │                                                                     │  │   │
│  │  │  {{ define "skyone.slack" }}                                        │  │   │
│  │  │  {{ if eq .Status "firing" }}                                       │  │   │
│  │  │  :fire: *{{ .Labels.alertname }}*                                   │  │   │
│  │  │  严重程度: `{{ .Labels.severity }}`                                  │  │   │
│  │  │  {{ else }}                                                         │  │   │
│  │  │  :white_check_mark: *{{ .Labels.alertname }} 已恢复*               │  │   │
│  │  │  {{ end }}                                                          │  │   │
│  │  │  {{ end }}                                                          │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ 三、性能压测架构

### 3.1 压测场景设计

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              压测场景矩阵                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           场景 1: 基础负载测试                                  │   │
│  │                                                                              │   │
│  │  目标: 验证系统在日常负载下的稳定性                                            │   │
│  │  虚拟用户: 50 VU                                                             │   │
│  │  持续时间: 9 分钟 (2min ramp + 5min steady + 2min down)                      │   │
│  │  预期结果: SLA 达成率 100%                                                   │   │
│  │                                                                              │   │
│  │  场景分布:                                                                   │   │
│  │  - 搜索请求: 60%                                                             │   │
│  │  - 文档查询: 25%                                                             │   │
│  │  - LLM 查询: 10%                                                             │   │
│  │  - 管理 API: 5%                                                              │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           场景 2: 峰值负载测试                                  │   │
│  │                                                                              │   │
│  │  目标: 验证系统在峰值流量下的处理能力                                          │   │
│  │  请求率: 10 → 100 → 200 req/s (阶梯增长)                                      │   │
│  │  持续时间: 10 分钟                                                           │   │
│  │  预期结果: 系统自动扩容，无请求失败                                            │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           场景 3: 压力测试                                    │   │
│  │                                                                              │   │
│  │  目标: 找到系统的性能瓶颈和上限                                               │   │
│  │  策略: 逐步增加负载直到系统崩溃                                              │   │
│  │  持续时间: 30 分钟 (或直到系统不可用)                                        │   │
│  │  监控重点: 错误率、延迟、资源使用率                                            │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           场景 4: 尖刺测试                                    │   │
│  │                                                                              │   │
│  │  目标: 验证系统对突发流量的响应和恢复能力                                     │   │
│  │  流量模式: 10 req/s → 200 req/s (10秒内) → 5分钟保持 → 恢复                  │   │
│  │  监控重点: 扩容速度、请求排队情况、恢复时间                                    │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           场景 5: 浸泡测试                                    │   │
│  │                                                                              │   │
│  │  目标: 验证系统长时间运行的稳定性 (内存泄漏、连接泄漏)                       │   │
│  │  虚拟用户: 50 VU (恒定)                                                      │   │
│  │  持续时间: 8 小时                                                            │   │
│  │  监控重点: 内存趋势、连接数趋势、错误率趋势                                    │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           场景 6: 故障注入测试                                │   │
│  │                                                                              │   │
│  │  目标: 验证系统在组件故障时的容错能力                                         │   │
│  │  测试内容:                                                                   │   │
│  │  - 模拟 API Pod 故障 (终止 Pod)                                              │   │
│  │  - 模拟 Redis 不可用                                                        │   │
│  │  - 模拟网络分区                                                              │   │
│  │  - 模拟数据库连接超时                                                        │   │
│  │  监控重点: 错误率、熔断触发、超时处理                                          │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 JMeter 复杂场景配置

```xml
<!-- jmeter/scenarios/complex_load_test.jmx -->
<!-- JMeter 用于复杂协议测试，如 JDBC、消息队列等 -->

<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan>
  <hashTree>
    <!-- 测试计划配置 -->
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan">
      <stringProp name="TestPlan.comments">SkyOne Complex Load Test</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
    </TestPlan>

    <!-- 线程组配置 -->
    <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup">
      <stringProp name="ThreadGroup.num_threads">100</stringProp>
      <stringProp name="ThreadGroup.ramp_time">60</stringProp>
      <stringProp name="ThreadGroup.duration">3600</stringProp>
      <stringProp name="ThreadGroup.delay">0</stringProp>
      <boolProp name="ThreadGroup.scheduler">true</boolProp>
    </ThreadGroup>

    <!-- HTTP 请求默认值 -->
    <ConfigTestElement guiclass="HttpDefaultsGui">
      <stringProp name="HTTPSampler.domain">api.skyskyone.com</stringProp>
      <stringProp name="HTTPSampler.port">443</stringProp>
      <stringProp name="HTTPSampler.protocol">https</stringProp>
      <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
      <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
      <stringProp name="HTTPSampler.contentEncoding">UTF-8</stringProp>
      <stringProp name="HTTPSampler.connect_timeout">5000</stringProp>
      <stringProp name="HTTPSampler.response_timeout">30000</stringProp>
    </ConfigTestElement>

    <!-- CSV 数据配置 (模拟不同用户) -->
    <CSVDataSet guiclass="TestBeanGUI" testclass="CSVDataSet">
      <stringProp name="delimiter">,</stringProp>
      <stringProp name="fileEncoding">UTF-8</stringProp>
      <boolProp name="ignoreFirstLine">true</boolProp>
      <stringProp name="variableNames">user_id,email,token</stringProp>
      <stringProp name="filename">test-data/users.csv</stringProp>
      <boolProp name="quotedData">false</boolProp>
      <boolProp name="recycle">true</boolProp>
    </CSVDataSet>

    <!-- 请求 1: 用户认证 -->
    <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy">
      <stringProp name="TestPlan.comments">User Authentication</stringProp>
      <stringProp name="HTTPSampler.path">/api/v1/auth/login</stringProp>
      <stringProp name="HTTPSampler.method">POST</stringProp>
      <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
      <elementProp name="HTTPsampler.Arguments">
        <collectionProp name="Arguments.arguments">
          <elementProp name="email" elementType="Argument">
            <stringProp name="Argument.name">email</stringProp>
            <stringProp name="Argument.value">${email}</stringProp>
          </elementProp>
          <elementProp name="password" elementType="Argument">
            <stringProp name="Argument.name">password</stringProp>
            <stringProp name="Argument.value">testpassword</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
    </HTTPSamplerProxy>

    <!-- 请求 2: 执行搜索 -->
    <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy">
      <stringProp name="TestPlan.comments">Search Documents</stringProp>
      <stringProp name="HTTPSampler.path">/api/v1/search</stringProp>
      <stringProp name="HTTPSampler.method">GET</stringProp>
      <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
      <elementProp name="HTTPsampler.Arguments">
        <collectionProp name="Arguments.arguments">
          <elementProp name="q" elementType="Argument">
            <stringProp name="Argument.name">q</stringProp>
            <stringProp name="Argument.value">test query</stringProp>
          </elementProp>
          <elementProp name="limit" elementType="Argument">
            <stringProp name="Argument.name">limit</stringProp>
            <stringProp name="Argument.value">20</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
    </HTTPSamplerProxy>

    <!-- 响应断言 -->
    <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion">
      <collectionProp name="Asserion.test_strings">
        <stringProp name="0">200</stringProp>
      </collectionProp>
      <stringProp name="Assertion.test_field">Assertion.response_code</stringProp>
    </ResponseAssertion>

    <!-- 持续时间断言 (P95 < 500ms) -->
    <DurationAssertion guiclass="DurationAssertionGui" testclass="DurationAssertion">
      <stringProp name="DurationAssertion.duration">500</stringProp>
    </DurationAssertion>

    <!-- 聚合报告 -->
    <Summariser guiclass="SummariserGui" testclass="Summariser"/>
    
    <!-- 后端监听器 (输出到 InfluxDB) -->
    <BackendListener guiclass="BackendListenerGui">
      <elementProp name="arguments" elementType="Arguments">
        <collectionProp name="Arguments.arguments">
          <elementProp name="influxdbMetricsSender" elementType="Argument">
            <stringProp name="Argument.name">influxdbMetricsSender</stringProp>
            <stringProp name="Argument.value">org.apache.jmeter.visualizers.influxdb.influxdbMetricsSender</stringProp>
          </elementProp>
          <elementProp name="influxdbUrl" elementType="Argument">
            <stringProp name="Argument.name">influxdbUrl</stringProp>
            <stringProp name="Argument.value">http://influxdb:8086/write?db=jmeter</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
    </BackendListener>
  </hashTree>
</jmeterTestPlan>
```

### 3.3 并发模型与容量规划

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              并发模型与容量规划                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Little's Law 应用                                   │   │
│  │                                                                              │   │
│  │  L = λW                                                                      │   │
│  │                                                                              │   │
│  │  L = 系统平均并发数 (Concurrent Users)                                        │   │
│  │  λ = 系统吞吐量 (Requests/Second)                                             │   │
│  │  W = 平均响应时间 (Seconds)                                                    │   │
│  │                                                                              │   │
│  │  示例计算:                                                                   │   │
│  │  - 目标 QPS: 500 req/s                                                       │   │
│  │  - 平均响应时间: 100ms = 0.1s                                                │   │
│  │  - 所需并发数: L = 500 × 0.1 = 50 并发                                       │   │
│  │                                                                              │   │
│  │  安全系数: 峰值 QPS = 日常 QPS × 2.5                                         │   │
│  │  预留容量: 扩容后 30% buffer                                                  │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           容量规划对照表 (Kubernetes)                           │   │
│  │                                                                              │   │
│  │  目标 QPS    │ API Pods │ Worker Pods │ Redis Memory │ 预估 CPU   │ 预估 Memory │   │
│  │  ──────────┼──────────┼────────────┼─────────────┼───────────┼─────────────│   │
│  │  100 rps   │    2     │     2      │    1 GB    │   500m    │    1 GB    │   │
│  │  500 rps   │    3     │     4      │    2 GB    │   2000m   │    4 GB    │   │
│  │  1000 rps  │    5     │     6      │    4 GB    │   4000m   │    8 GB    │   │
│  │  2000 rps  │    8     │    10      │    8 GB    │   8000m   │   16 GB    │   │
│  │  5000 rps  │   15     │    15      │   16 GB    │  15000m   │   32 GB    │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           瓶颈点识别决策树                                      │   │
│  │                                                                              │   │
│  │                          CPU > 80%?                                          │   │
│  │                         /           \                                        │   │
│  │                       是              否                                       │   │
│  │                       /                 \                                      │   │
│  │              扩展 API Pods?      Memory > 85%?                               │   │
│  │                   /     \              /     \                                │   │
│  │                 否      是           是      否                               │   │
│  │                 /        \          /        \                               │   │
│  │         检查代码热     增加     检查内存    检查延迟分布                        │   │
│  │         点优化        Pods      泄漏         /     \                          │   │
│  │                                    /       是      否                         │   │
│  │                              扩展 Pods   /    \    分析依赖服务                  │   │
│  │                               或优化    是     否                              │   │
│  │                                      /      \   /     \                       │   │
│  │                               检查 GC   检查    扩展    等待恢复                 │   │
│  │                               压力      网络    服务     或忽略                   │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 四、性能优化架构

### 4.1 数据库连接池优化

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              数据库连接池优化架构                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           PgBouncer 连接池配置                                │   │
│  │                                                                              │   │
│  │  pgbouncer.ini:                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  [databases]                                                        │  │   │
│  │  │  skyone = host=postgres.rds.amazonaws.com port=5432                │  │   │
│  │  │       dbname=skyone pool_size=50                                   │  │   │
│  │  │                                                                     │  │   │
│  │  │  [pgbouncer]                                                        │  │   │
│  │  │  listen_port = 6432                                                │  │   │
│  │  │  listen_addr = 0.0.0.0                                             │  │   │
│  │  │  auth_type = md5                                                   │  │   │
│  │  │  auth_file = /etc/pgbouncer/userlist.txt                          │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 连接池模式                                                       │  │   │
│  │  │  pool_mode = transaction  # 推荐: transaction                      │  │   │
│  │  │  max_client_conn = 1000                                            │  │   │
│  │  │  default_pool_size = 50     # 每个用户/数据库的连接数                │  │   │
│  │  │  min_pool_size = 10         # 保持的最小连接数                      │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 超时配置                                                         │  │   │
│  │  │  server_idle_timeout = 600     # 空闲连接超时 (秒)                  │  │   │
│  │  │  server_connect_timeout = 15   # 连接超时                           │  │   │
│  │  │  server_lifetime = 3600        # 连接生命周期 (1小时)                │  │   │
│  │  │  server_login_retry = 5        # 登录重试次数                        │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 查询限制                                                         │  │   │
│  │  │  query_wait_timeout = 30       # 查询等待超时 (秒)                  │  │   │
│  │  │  query_timeout = 60            # 查询最大超时                        │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 日志                                                             │  │   │
│  │  │  log_connections = 0                                                │  │   │
│  │  │  log_disconnections = 0                                             │  │   │
│  │  │  log_pooler_errors = 1                                              │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           SQLAlchemy 连接池配置                                │   │
│  │                                                                              │   │
│  │  database.py:                                                               │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  from sqlalchemy import create_engine                               │  │   │
│  │  │  from sqlalchemy.orm import sessionmaker                            │  │   │
│  │  │  from sqlalchemy.pool import QueuePool                               │  │   │
│  │  │                                                                     │  │   │
│  │  │  engine = create_engine(                                            │  │   │
│  │  │      DATABASE_URL,                                                  │  │   │
│  │  │      poolclass=QueuePool,                                           │  │   │
│  │  │      pool_size=20,          # 基础连接数                             │  │   │
│  │  │      max_overflow=10,       # 额外连接数 (总 30)                     │  │   │
│  │  │      pool_pre_ping=True,    # 连接前检测                             │  │   │
│  │  │      pool_recycle=3600,     # 连接回收时间 (1小时)                    │  │   │
│  │  │      pool_timeout=30,       # 获取连接超时                            │  │   │
│  │  │      echo=False,                                                     │  │   │
│  │  │  )                                                                   │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 异步引擎 (用于 FastAPI)                                            │  │   │
│  │  │  from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession │  │   │
│  │  │                                                                     │  │   │
│  │  │  async_engine = create_async_engine(                                │  │   │
│  │  │      ASYNC_DATABASE_URL,                                            │  │   │
│  │  │      poolclass=QueuePool,                                           │  │   │
│  │  │      pool_size=20,                                                  │  │   │
│  │  │      max_overflow=10,                                               │  │   │
│  │  │      pool_pre_ping=True,                                            │  │   │
│  │  │      pool_recycle=3600,                                             │  │   │
│  │  │  )                                                                   │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 缓存命中率优化

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              缓存命中率优化策略                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           缓存分层策略                                          │   │
│  │                                                                              │   │
│  │   L1: 进程内缓存 (LRU) ────────► 最热数据 (命中率目标 > 95%)                   │   │
│  │   │  - 大小: 1000 items                                                     │   │
│  │   │  - TTL: 5 分钟                                                           │   │
│  │   │  - 延迟: < 1ms                                                           │   │
│  │   │                                                                         │   │
│  │   L2: Redis 分布式缓存 ───────► 热点数据 (命中率目标 > 90%)                   │   │
│  │   │  - 大小: 10000 items                                                     │   │
│  │   │  - TTL: 30 分钟                                                           │   │
│  │   │  - 延迟: 1-5ms                                                           │   │
│  │   │                                                                         │   │
│  │   L3: 数据库 ──────────────► 冷数据                                           │   │
│  │       - 延迟: 5-50ms                                                          │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           缓存键设计规范                                       │   │
│  │                                                                              │   │
│  │  命名格式: <module>:<entity>:<id>:<field>                                     │   │
│  │                                                                              │   │
│  │  示例:                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  # 用户缓存                                                            │  │   │
│  │  │  user:profile:12345                                                  │  │   │
│  │  │  user:session:abc123def456                                           │  │   │
│  │  │  user:quota:12345                                                   │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 文档缓存                                                            │  │   │
│  │  │  doc:metadata:67890                                                 │  │   │
│  │  │  doc:content:67890                                                  │  │   │
│  │  │  doc:chunks:67890                                                   │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 搜索缓存 (带查询哈希)                                               │  │   │
│  │  │  search:query:a1b2c3d4e5f6    # a1b2c3 = MD5(q + filters)            │  │   │
│  │  │                                                                     │  │   │
│  │  │  # LLM 缓存 (带语义哈希)                                               │  │   │
│  │  │  llm:response:gpt4:zhangsan:mnopq  # mnopq = query embedding hash   │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           缓存预热策略                                          │   │
│  │                                                                              │   │
│  │  启动时预热:                                                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  @app.on_event("startup")                                          │  │   │
│  │  │  async def warm_cache():                                            │  │   │
│  │  │      # 1. 预热活跃用户缓存 (Top 100)                                  │  │   │
│  │  │      users = await UserService.get_active_users(limit=100)          │  │   │
│  │  │      for user in users:                                             │  │   │
│  │  │          await cache.set(f"user:profile:{user.id}", user)          │  │   │
│  │  │                                                                     │  │   │
│  │  │      # 2. 预热热门文档缓存 (Top 100)                                   │  │   │
│  │  │      docs = await DocumentService.get_popular_docs(limit=100)       │  │   │
│  │  │      for doc in docs:                                               │  │   │
│  │  │          await cache.set(f"doc:metadata:{doc.id}", doc)             │  │   │
│  │  │                                                                     │  │   │
│  │  │      # 3. 预热配置缓存                                                │  │   │
│  │  │      configs = await ConfigService.get_all_configs()                │  │   │
│  │  │      for config in configs:                                         │  │   │
│  │  │          await cache.set(f"config:{config.key}", config)            │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  │  定时预热 (Celery Beat):                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  # 每天凌晨 3:00 执行全量预热                                        │  │   │
│  │  │  @celery_app.task                                                   │  │   │
│  │  │  def daily_cache_warmup():                                          │  │   │
│  │  │      warm_all_user_caches.delay()                                   │  │   │
│  │  │      warm_popular_docs.delay()                                      │  │   │
│  │  │      warm_system_configs.delay()                                    │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 每小时执行增量预热                                                │  │   │
│  │  │  @celery_app.task                                                   │  │   │
│  │  │  def hourly_cache_warmup():                                        │  │   │
│  │  │      warm_recent_users.delay()                                      │  │   │
│  │  │      warm_trending_docs.delay()                                    │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 异步处理优化

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              异步处理优化架构                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           任务队列优先级设计                                    │   │
│  │                                                                              │   │
│  │   Priority Queue Design:                                                    │   │
│  │   ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │   │  Priority   │  Queue Name       │  Use Case           │  SLA       │  │   │
│  │   │  ──────────┼──────────────────┼────────────────────┼─────────────│  │   │
│  │   │  1 (最高)  │  critical        │  支付、认证         │  < 10s    │  │   │
│  │   │  2 (高)    │  documents       │  文档处理           │  < 1min   │  │   │
│  │   │  3 (中)    │  embeddings      │  向量化任务         │  < 5min   │  │   │
│  │   │  4 (低)    │  index           │  索引构建           │  < 10min  │  │   │
│  │   │  5 (最低)  │  notifications   │  通知、邮件         │  < 30min  │  │   │
│  │   │  6 (后台)  │  analytics       │  统计、分析         │  < 1h     │  │   │
│  │   └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  │   Celery 配置:                                                               │   │
│  │   ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │   │  celery_app.conf.update(                                            │  │   │
│  │   │      task_default_queue='documents',                                │  │   │
│  │   │      task_queues={                                                   │  │   │
│  │   │          'critical': Queue('critical', routing_key='critical'),     │  │   │
│  │   │          'documents': Queue('documents', routing_key='doc.*'),     │  │   │
│  │   │          'embeddings': Queue('embeddings', routing_key='embed.*'), │  │   │
│  │   │          'index': Queue('index', routing_key='index.*'),           │  │   │
│  │   │          'notifications': Queue('notifications', routing_key='notif.*'),│ │   │
│  │   │          'analytics': Queue('analytics', routing_key='analytics.*'),│ │   │
│  │   │      },                                                              │  │   │
│  │   │      task_routes={                                                   │  │   │
│  │   │          'tasks.auth.*': {'queue': 'critical'},                     │  │   │
│  │   │          'tasks.documents.*': {'queue': 'documents'},             │  │   │
│  │   │          'tasks.embeddings.*': {'queue': 'embeddings'},           │  │   │
│  │   │          'tasks.index.*': {'queue': 'index'},                     │  │   │
│  │   │          'tasks.notifications.*': {'queue': 'notifications'},    │  │   │
│  │   │          'tasks.analytics.*': {'queue': 'analytics'},           │  │   │
│  │   │      },                                                              │  │   │
│  │   │      worker_prefetch_multiplier=4,  # 预取任务数                     │  │   │
│  │   │      task_acks_late=True,          # 任务完成确认                     │  │   │
│  │   │      task_reject_on_worker_lost=True,                             │  │   │
│  │   │  )                                                                   │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           异步 I/O 优化 (asyncio)                             │   │
│  │                                                                              │   │
│  │  FastAPI 异步最佳实践:                                                        │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  # 正确: 使用 async/await                                            │  │   │
│  │  │  @app.get("/documents/{doc_id}")                                    │  │   │
│  │  │  async def get_document(doc_id: str):                                │  │   │
│  │  │      doc = await DocumentService.get_by_id(doc_id)                   │  │   │
│  │  │      return doc                                                       │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 正确: 并发执行多个 I/O 操作                                        │  │   │
│  │  │  @app.get("/dashboard")                                             │  │   │
│  │  │  async def get_dashboard():                                          │  │   │
│  │  │      # 并发获取多个数据源                                             │  │   │
│  │  │      user_task = get_user_info()                                     │  │   │
│  │  │      stats_task = get_statistics()                                   │  │   │
│  │  │      recent_task = get_recent_activity()                             │  │   │
│  │  │                                                                     │  │   │
│  │  │      user, stats, recent = await asyncio.gather(                     │  │   │
│  │  │          user_task, stats_task, recent_task                           │  │   │
│  │  │      )                                                                │  │   │
│  │  │      return {"user": user, "stats": stats, "recent": recent}        │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 错误: 在 async 函数中使用同步 I/O                                  │  │   │
│  │  │  @app.get("/bad-example")                                           │  │   │
│  │  │  async def bad_example():                                           │  │   │
│  │  │      # 这会阻塞事件循环!                                              │  │   │
│  │  │      result = requests.get("http://example.com/api")  # 不要这样做!  │  │   │
│  │  │      return result.json()                                           │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 正确: 使用 httpx/aiohttp 进行异步 HTTP                             │  │   │
│  │  │  @app.get("/good-example")                                          │  │   │
│  │  │  async def good_example():                                          │  │   │
│  │  │      async with httpx.AsyncClient() as client:                      │  │   │
│  │  │          response = await client.get("http://example.com/api")      │  │   │
│  │  │          return response.json()                                     │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.4 CDN 加速配置

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              CDN 加速架构                                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           CDN 缓存策略                                         │   │
│  │                                                                              │   │
│  │   ┌──────────────────────────────────────────────────────────────────────┐  │   │
│  │   │   资源类型          │   缓存时间   │   缓存 Key                │  │   │
│  │   │   ───────────────┼─────────────┼─────────────────────────────┤  │   │
│  │   │   静态资源         │   30 天     │   URL + Query              │  │   │
│  │   │   (JS/CSS/图片)   │             │                             │  │   │
│  │   │   ───────────────┼─────────────┼─────────────────────────────┤  │   │
│  │   │   API 动态响应    │   5 分钟    │   URL + Auth Header         │  │   │
│  │   │   (JSON)        │             │   (Vary: Authorization)     │  │   │
│  │   │   ───────────────┼─────────────┼─────────────────────────────┤  │   │
│  │   │   文档预览        │   7 天      │   URL                      │  │   │
│  │   │   ───────────────┼─────────────┼─────────────────────────────┤  │   │
│  │   │   用户头像        │   30 天     │   URL                      │  │   │
│  │   │   ───────────────┼─────────────┼─────────────────────────────┤  │   │
│  │   │   搜索建议        │   5 分钟    │   Query Hash               │  │   │
│  │   └──────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           CDN 配置 (阿里云 CDN 为例)                          │   │
│  │                                                                              │   │
│  │  缓存配置:                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  # 忽略 URL 参数中的时间戳                                            │  │   │
│  │  │  ignore_query_string: false  # 保留搜索参数                         │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 静态资源缓存                                                        │  │   │
│  │  │  cache_config:                                                      │  │   │
│  │  │    - path: /static/*                                               │  │   │
│  │  │      ttl: 2592000  # 30 天                                           │  │   │
│  │  │      weight: 100                                                    │  │   │
│  │  │    - path: /media/*                                                 │  │   │
│  │  │      ttl: 604800   # 7 天                                            │  │   │
│  │  │      weight: 80                                                     │  │   │
│  │  │    - path: /api/*                                                   │  │   │
│  │  │      ttl: 300     # 5 分钟 (API 不缓存)                              │  │   │
│  │  │      weight: 0                                                      │  │   │
│  │  │                                                                     │  │   │
│  │  │  # HTTP 头配置                                                        │  │   │
│  │  │  headers:                                                           │  │   │
│  │  │    - Cache-Control: public, max-age=3600                            │  │   │
│  │  │    - Vary: Accept-Encoding                                          │  │   │
│  │  │    - Access-Control-Allow-Origin: *                                │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  │  防盗链配置:                                                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  referer_white_list:                                               │  │   │
│  │  │    - https://skyskyone.com                                         │  │   │
│  │  │    - https://*.skyskyone.com                                       │  │   │
│  │  │                                                                     │  │   │
│  │  │  referer_black_list: []                                            │  │   │
│  │  │                                                                     │  │   │
│  │  │  ip_black_list: []                                                 │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 鉴权配置 (高级防盗链)                                               │  │   │
│  │  │  auth_type: type_a                                                 │  │   │
│  │  │  auth_key1: ${PRIVATE_KEY}                                          │  │   │
│  │  │  auth_key2: ${BACKUP_KEY}                                           │  │   │
│  │  │  auth_timeout: 3600  # 1 小时                                       │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📚 五、用户手册架构

### 5.1 MkDocs 文档站点配置

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              文档站点架构                                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           mkdocs.yml 配置                                      │   │
│  │                                                                              │   │
│  │  site_name: SkyOne Shuge 文档                                                │   │
│  │  site_url: https://docs.skyskyone.com                                        │   │
│  │  site_description: 天一阁 - 智能文档管理与知识库平台                          │   │
│  │  site_author: SkyOne Team                                                    │   │
│  │                                                                              │   │
│  │  # 仓库配置                                                                   │   │
│  │  repo_name: skyone-shuge                                                    │   │
│  │  repo_url: https://github.com/skyskyone/skyone-shuge                        │   │
│  │                                                                              │   │
│  │  # 主题配置 (Material for MkDocs)                                            │   │
│  │  theme:                                                                     │   │
│  │    name: material                                                            │   │
│  │    language: zh                                                              │   │
│  │    palette:                                                                 │   │
│  │      scheme: default                                                         │   │
│  │      primary: indigo                                                        │   │
│  │      accent: indigo                                                         │   │
│  │    font:                                                                    │   │
│  │      text: Roboto                                                           │   │
│  │      code: Roboto Mono                                                      │   │
│  │    features:                                                                │   │
│  │      - navigation.instant         # 即时导航                                 │   │
│  │      - navigation.tracking         # URL 跟随导航                            │   │
│  │      - navigation.tabs            # 顶部 Tab 导航                           │   │
│  │      - navigation.sections        # 左侧分组导航                             │   │
│  │      - toc.integrate               # 目录集成                               │   │
│  │      - search.suggest              # 搜索建议                               │   │
│  │      - search.highlight            # 搜索高亮                               │   │
│  │      - content.code.copy           # 代码复制                               │   │
│  │      - content.code.annotate      # 代码注释                               │   │
│  │                                                                              │   │
│  │  # 插件配置                                                                   │   │
│  │  plugins:                                                                   │   │
│  │    - search:                                                                │   │
│  │        lang:                                                                │   │
│  │          - en                                                               │   │
│  │          - zh                                                               │   │
│  │    - minify:                                                                │   │
│  │        minify_html: true                                                    │   │
│  │        minify_js: true                                                      │   │
│  │        minify_css: true                                                     │   │
│  │    - git-revision-date-localized:                                           │   │
│  │        enable_creation_date: true                                           │   │
│  │    - mermaid2                   # 流程图支持                                │   │
│  │    - drawio:                                                                  │   │
│  │        default_style: presentation                                         │   │
│  │                                                                              │   │
│  │  # Markdown 扩展                                                            │   │
│  │  markdown_extensions:                                                       │   │
│  │    - pymdownx.highlight:       # 代码高亮                                   │   │
│  │        anchor_linenums: true                                               │   │
│  │    - pymdownx.inlinehilite:    # 行内代码                                   │   │
│  │    - pymdownx.snippets:        # 文本片段包含                               │   │
│  │    - pymdownx.superfences:     # 超级代码块 (流程图等)                      │   │
│  │    - pymdownx.tabbed:          # Tab 支持                                   │   │
│  │    - admonition:               # 提示块                                     │   │
│  │    - toc:                                                                     │   │
│  │        permalink: true                                                      │   │
│  │    - tables:                  # 表格支持                                     │   │
│  │                                                                              │   │
│  │  # 额外 CSS/JS                                                                │   │
│  │  extra_css:                                                                   │   │
│  │    - stylesheets/extra.css                                                 │   │
│  │                                                                              │   │
│  │  # 社交链接                                                                   │   │
│  │  extra:                                                                     │   │
│  │    social:                                                                  │   │
│  │      - link: https://github.com/skyskyone                                   │   │
│  │        name: GitHub                                                        │   │
│  │      - link: https://twitter.com/skyskyone                                 │   │
│  │        name: Twitter                                                       │   │
│  │                                                                              │   │
│  │  # 贡献者                                                                     │   │
│  │    generator: false                                                        │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           导航结构配置                                         │   │
│  │                                                                              │   │
│  │  nav:                                                                     │   │
│  │    - 首页: "index.md"                                                        │   │
│  │    - 快速开始:                                                              │   │
│  │      - 简介: "getting-started/index.md"                                    │   │
│  │      - 安装部署: "getting-started/installation.md"                        │   │
│  │      - 配置指南: "getting-started/configuration.md"                        │   │
│  │      - 快速开始: "getting-started/quickstart.md"                           │   │
│  │    - 用户指南:                                                              │   │
│  │      - 认证授权: "user-guide/authentication.md"                            │   │
│  │      - 文档管理: "user-guide/documents.md"                                 │   │
│  │      - 搜索功能: "user-guide/search.md"                                    │   │
│  │      - 协作功能: "user-guide/collaboration.md"                             │   │
│  │    - API 参考:                                                              │   │
│  │      - 概述: "api-reference/index.md"                                       │   │
│  │      - 认证: "api-reference/authentication.md"                             │   │
│  │      - 文档 API: "api-reference/documents-api.md"                          │   │
│  │      - 搜索 API: "api-reference/search-api.md"                              │   │
│  │    - 运维指南:                                                              │   │
│  │      - 部署运维: "admin-guide/deployment.md"                               │   │
│  │      - 监控告警: "admin-guide/monitoring.md"                               │   │
│  │      - 故障排查: "admin-guide/troubleshooting.md"                          │   │
│  │      - 性能调优: "admin-guide/performance-tuning.md"                        │   │
│  │    - 开发指南:                                                              │   │
│  │      - 系统架构: "developer-guide/architecture.md"                          │   │
│  │      - 本地开发: "developer-guide/local-development.md"                     │   │
│  │      - 测试指南: "developer-guide/testing.md"                               │   │
│  │      - 更新日志: "developer-guide/changelog.md"                              │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 文档内容结构示例

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              文档内容页面结构                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           快速开始页面示例                                      │   │
│  │                                                                              │   │
│  │  getting-started/quickstart.md:                                              │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  ---                                                                │  │   │
│  │  │  hide:                                                              │  │   │
│  │  │    - navigation                                                 │  │   │
│  │  │    - toc                                                           │  │   │
│  │  │  ---                                                                │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 5 分钟快速开始                                                   │  │   │
│  │  │                                                                     │  │   │
│  │  │  <div class="result" markdown>                                     │  │   │
│  │  │                                                                     │  │   │
│  │  │  ## 前置要求                                                        │  │   │
│  │  │                                                                     │  │   │
│  │  │  - Python 3.10+                                                    │  │   │
│  │  │  - Docker 和 Docker Compose                                        │  │   │
│  │  │  - API Key (用于 LLM 服务)                                         │  │   │
│  │  │                                                                     │  │   │
│  │  │  ## 步骤 1: 克隆项目                                                │  │   │
│  │  │                                                                     │  │   │
│  │  │  ```bash                                                           │  │   │
│  │  │  git clone https://github.com/skyskyone/skyone-shuge.git          │  │   │
│  │  │  cd skyone-shuge                                                   │  │   │
│  │  │  ```                                                                │  │   │
│  │  │                                                                     │  │   │
│  │  │  ## 步骤 2: 配置环境变量                                            │  │   │
│  │  │                                                                     │  │   │
│  │  │  ```bash                                                           │  │   │
│  │  │  cp .env.example .env                                              │  │   │
│  │  │  # 编辑 .env 文件，填入必要的配置                                   │  │   │
│  │  │  ```                                                                │  │   │
│  │  │                                                                     │  │   │
│  │  │  !!! tip "需要配置哪些环境变量？"                                    │  │   │
│  │  │      - `SECRET_KEY`: 应用密钥                                        │  │   │
│  │  │      - `OPENAI_API_KEY`: LLM API Key                                │  │   │
│  │  │      - `DATABASE_URL`: 数据库连接字符串                              │  │   │
│  │  │                                                                     │  │   │
│  │  │  ## 步骤 3: 启动服务                                                │  │   │
│  │  │                                                                     │  │   │
│  │  │  ```bash                                                           │  │   │
│  │  │  docker-compose up -d                                             │  │   │
│  │  │  ```                                                                │  │   │
│  │  │                                                                     │  │   │
│  │  │  ## 步骤 4: 访问应用                                                │  │   │
│  │  │                                                                     │  │   │
│  │  │  - API 服务: http://localhost:8000                                 │  │   │
│  │  │  - API 文档: http://localhost:8000/docs                           │  │   │
│  │  │  - Grafana: http://localhost:3000                                 │  │   │
│  │  │                                                                     │  │   │
│  │  │  ## 下一步                                                          │  │   │
│  │  │                                                                     │  │   │
│  │  │  - [配置指南](configuration.md) - 了解更多配置选项                   │  │   │
│  │  │  - [用户指南](../user-guide/documents.md) - 学习核心功能           │  │   │
│  │  │  - [API 参考](../api-reference/index.md) - 查看完整 API 文档        │  │   │
│  │  │                                                                     │  │   │
│  │  │  </div>                                                             │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           故障排查页面示例                                      │   │
│  │                                                                              │   │
│  │  admin-guide/troubleshooting.md:                                            │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  # 故障排查指南                                                       │  │   │
│  │  │                                                                     │  │   │
│  │  │  ## 常见问题                                                          │  │   │
│  │  │                                                                     │  │   │
│  │  │  ### 1. 服务无法启动                                                  │  │   │
│  │  │                                                                     │  │   │
│  │  │  === "症状"                                                          │  │   │
│  │  │      ```                                                             │  │   │
│  │  │      Error: Cannot connect to database                               │  │   │
│  │  │      ```                                                             │  │   │
│  │  │                                                                     │  │   │
│  │  │  === "原因"                                                          │  │   │
│  │  │      - 数据库服务未启动                                               │  │   │
│  │  │      - 数据库连接配置错误                                             │  │   │
│  │  │      - 网络连接问题                                                   │  │   │
│  │  │                                                                     │  │   │
│  │  │  === "解决方案"                                                      │  │   │
│  │  │      1. 检查数据库服务状态:                                           │  │   │
│  │  │         ```bash                                                      │  │   │
│  │  │         docker-compose ps postgres                                   │  │   │
│  │  │         ```                                                          │  │   │
│  │  │      2. 检查连接配置:                                                 │  │   │
│  │  │         ```bash                                                      │  │   │
│  │  │         cat .env | grep DATABASE                                     │  │   │
│  │  │         ```                                                          │  │   │
│  │  │      3. 重启服务:                                                     │  │   │
│  │  │         ```bash                                                      │  │   │
│  │  │         docker-compose restart api                                   │  │   │
│  │  │         ```                                                          │  │   │
│  │  │                                                                     │  │   │
│  │  │  ---                                                                 │  │   │
│  │  │                                                                     │  │   │
│  │  │  ### 2. LLM 请求超时                                                 │  │   │
│  │  │                                                                     │  │   │
│  │  │  === "症状"                                                          │  │   │
│  │  │      ```                                                             │  │   │
│  │  │      TimeoutError: LLM request timeout after 60s                    │  │   │
│  │  │      ```                                                             │  │   │
│  │  │                                                                     │  │   │
│  │  │  === "原因"                                                          │  │   │
│  │  │      - API Key 额度用尽                                             │  │   │
│  │  │      - 网络延迟过高                                                   │  │   │
│  │  │      - 请求负载过高                                                   │  │   │
│  │  │                                                                     │  │   │
│  │  │  === "解决方案"                                                      │  │   │
│  │  │      1. 检查 API Key 配额:                                            │  │   │
│  │  │         登录 OpenAI/Claude 控制台查看用量                            │  │   │
│  │  │      2. 使用缓存减少 LLM 调用:                                       │  │   │
│  │  │         设置 `LLM_CACHE_ENABLED=true`                               │  │   │
│  │  │      3. 配置多个 API Key 负载均衡:                                    │  │   │
│  │  │         在 `.env` 中配置 `OPENAI_API_KEY_2`, `OPENAI_API_KEY_3`      │  │   │
│  │  │                                                                     │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 搜索功能配置

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              文档搜索功能配置                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           本地搜索配置 (lunr.js)                               │   │
│  │                                                                              │   │
│  │  - 内置，无需外部服务                                                        │   │
│  │  - 支持中文分词 (结巴分词)                                                    │   │
│  │  - 搜索结果实时高亮                                                          │   │
│  │                                                                              │   │
│  │  搜索优化配置:                                                               │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  # mkdocs.yml                                                        │  │   │
│  │  │  plugins:                                                            │  │   │
│  │  │    - search:                                                         │  │   │
│  │  │        tokenizer: 'lunr.tokenizer'  # 默认                            │  │   │
│  │  │       预处理器: 'lunr.preprocessor'                                  │  │   │
│  │  │                                                                     │  │   │
│  │  │        # 搜索配置                                                      │  │   │
│  │  │        min_search_length: 2     # 最小搜索词长度                      │  │   │
│  │  │        max_search_length: 50    # 最大搜索词长度                      │  │   │
│  │  │        boost:                  # 字段权重                             │  │   │
│  │  │          title: 10                                                 │  │   │
│  │  │          headings: 5                                               │  │   │
│  │  │          content: 1                                                 │  │   │
│  │  │                                                                     │  │   │
│  │  │        # 忽略的词 (停用词)                                            │  │   │
│  │  │        stop_words:                                                  │  │   │
│  │  │          - 'the'                                                    │  │   │
│  │  │          - 'a'                                                     │  │   │
│  │  │          - 'an'                                                     │  │   │
│  │  │                                                                     │  │   │
│  │  │        # 索引生成配置                                                 │  │   │
│  │  │        index_docs: true         # 是否索引文档内容                   │  │   │
│  │  │        index_path: 'search_index.json'  # 索引文件路径               │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           版本管理配置                                         │   │
│  │                                                                              │   │
│  │  多版本文档配置:                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │   │
│  │  │  # 文档版本结构                                                        │  │   │
│  │  │  docs/                                                               │  │   │
│  │  │  ├── v3.0/                                                          │  │   │
│  │  │  │   ├── index.md                                                   │  │   │
│  │  │  │   ├── getting-started/                                           │  │   │
│  │  │  │   └── ...                                                        │  │   │
│  │  │  ├── v2.0/                                                          │  │   │
│  │  │  │   ├── index.md                                                   │  │   │
│  │  │  │   └── ...                                                        │  │   │
│  │  │  └── v1.0/                                                          │  │   │
│  │  │      └── ...                                                        │  │   │
│  │  │                                                                     │  │   │
│  │  │  # mkdocs.yml                                                       │  │   │
│  │  │  theme:                                                             │  │   │
│  │  │    version:                                                         │  │   │
│  │  │      provider: mike                                                 │  │   │
│  │  │      canonical: true                                                │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 版本选择器                                                         │  │   │
│  │  │  extra:                                                             │  │   │
│  │  │    version_selector: true                                           │  │   │
│  │  │    switcher: true                                                   │  │   │
│  │  │    explicit:                                                        │  │   │
│  │  │      v3.0: true  # 最新稳定版                                        │  │   │
│  │  │      v2.0: false                                                     │  │   │
│  │  │      v1.0: false                                                     │  │   │
│  │  │                                                                     │  │   │
│  │  │  # 目录链接                                                           │  │   │
│  │  │  version:                                                           │  │   │
│  │  │    default: v3.0                                                    │  │   │
│  │  │    v2.0:                                                            │  │   │
│  │  │      redirect: true                                                │  │   │
│  │  │    v1.0:                                                            │  │   │
│  │  │      redirect: true                                                │  │   │
│  │  └─────────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 六、文件结构总览

```
skyone-shuge/
├── prd/
│   └── MVP_v3.0.18.md                   # PRD 文档
│
├── architecture/
│   └── ARCHITECTURE_v3.0.18.md          # 架构文档
│
├── helm/
│   ├── Chart.yaml                       # Helm Chart 定义
│   ├── values.yaml                      # 默认 values
│   ├── values-prod.yaml                 # 生产环境 values
│   ├── values-staging.yaml              # 预发环境 values
│   ├── values-dev.yaml                  # 开发环境 values
│   └── templates/
│       ├── _helpers.tpl                # 通用模板
│       ├── namespace.yaml
│       ├── configmap.yaml
│       ├── secrets.yaml
│       ├── api-deployment.yaml
│       ├── api-service.yaml
│       ├── worker-deployment.yaml
│       ├── ingress.yaml
│       ├── hpa.yaml
│       ├── pdb.yaml
│       └── servicemonitor.yaml
│
├── kubernetes/
│   ├── base/
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   └── secrets.yaml
│   ├── overlays/
│   │   ├── prod/
│   │   │   ├── kustomization.yaml
│   │   │   └── replica-counts.yaml
│   │   └── staging/
│   │       └── kustomization.yaml
│   └── components/
│       ├── api/
│       ├── worker/
│       └── monitoring/
│
├── prometheus/
│   ├── prometheus.yml                   # Prometheus 配置
│   ├── rules/
│   │   ├── skyone-alerts.yml            # 告警规则
│   │   ├── skyone-recording-rules.yml  # 记录规则
│   │   └── skyone-slos.yml             # SLO 规则
│   └── alertmanager/
│       ├── alertmanager.yml             # Alertmanager 配置
│       └── templates/
│           └── skyone-alerts.tmpl       # 告警模板
│
├── grafana/
│   └── provisioning/
│       ├── dashboards/
│       │   ├── dashboards.yml
│       │   └── skyone/
│       │       ├── overview.json
│       │       ├── api-performance.json
│       │       ├── llm-cost.json
│       │       └── cache-performance.json
│       └── datasources/
│           └── datasources.yml
│
├── k6/
│   ├── scenarios/
│   │   ├── api-load-test.js            # API 负载测试
│   │   ├── websocket-test.js            # WebSocket 测试
│   │   ├── stress-test.js              # 压力测试
│   │   └── soak-test.js                # 浸泡测试
│   └── config/
│       └── thresholds.yml              # 性能阈值
│
├── jmeter/
│   └── scenarios/
│       ├── complex_load_test.jmx
│       └── jdbc_test.jmx
│
├── docs/
│   ├── docs/
│   │   ├── index.md
│   │   ├── getting-started/
│   │   │   ├── index.md
│   │   │   ├── installation.md
│   │   │   ├── configuration.md
│   │   │   └── quickstart.md
│   │   ├── user-guide/
│   │   │   ├── index.md
│   │   │   ├── authentication.md
│   │   │   ├── documents.md
│   │   │   ├── search.md
│   │   │   ├── collaboration.md
│   │   │   └── quota-management.md
│   │   ├── api-reference/
│   │   │   ├── index.md
│   │   │   ├── authentication.md
│   │   │   ├── documents-api.md
│   │   │   ├── search-api.md
│   │   │   ├── llm-api.md
│   │   │   ├── monitoring-api.md
│   │   │   ├── rate-limit-api.md
│   │   │   ├── cache-api.md
│   │   │   └── websocket-api.md
│   │   ├── admin-guide/
│   │   │   ├── index.md
│   │   │   ├── deployment.md
│   │   │   ├── monitoring.md
│   │   │   ├── backup-restore.md
│   │   │   ├── troubleshooting.md
│   │   │   ├── performance-tuning.md
│   │   │   └── security.md
│   │   ├── developer-guide/
│   │   │   ├── index.md
│   │   │   ├── architecture.md
│   │   │   ├── local-development.md
│   │   │   ├── testing.md
│   │   │   ├── contributing.md
│   │   │   └── changelog.md
│   │   └── reference/
│   │       ├── config-reference.md
│   │       ├── error-codes.md
│   │       ├── cli-reference.md
│   │       └── webhook-events.md
│   ├── overrides/
│   │   └── partials/
│   │       └── copyright.html
│   ├── stylesheets/
│   │   └── extra.css
│   └── mkdocs.yml
│
├── docker-compose.prod.yml              # 生产 Docker 配置
├── Dockerfile.prod                      # 生产 Dockerfile
├── Dockerfile                           # 开发 Dockerfile
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                       # CI 流水线
│   │   └── release.yml                  # Release 流程
│   └── actions/
│       ├── deploy-staging/
│       │   ├── action.yml
│       │   └── entrypoint.sh
│       └── deploy-production/
│           ├── action.yml
│           └── entrypoint.sh
│
└── scripts/
    ├── init_db.py
    ├── warmup_cache.py
    └── run_load_test.sh
```

---

## ✅ 验收标准

### 部署配置
- [x] Helm Chart 完整，包含所有 Kubernetes 资源模板
- [x] Docker Compose 生产配置包含所有必需服务
- [x] CI/CD 流水线配置完整 (GitHub Actions)
- [x] 环境变量和 Secrets 管理符合安全规范
- [x] 灰度发布配置完整 (Argo Rollouts)

### 监控告警
- [x] Prometheus 告警规则覆盖所有关键指标
- [x] Alertmanager 路由配置支持多级通知
- [x] 告警升级策略已定义
- [x] Grafana Dashboard 配置完整
- [x] Recording Rules 预聚合配置

### 性能压测
- [x] k6 压测脚本完整 (6 个场景)
- [x] JMeter 复杂场景配置
- [x] 性能基线和 SLA 定义
- [x] 容量规划对照表
- [x] 瓶颈分析方法论

### 性能优化
- [x] 数据库连接池优化配置
- [x] 缓存命中率优化策略
- [x] 异步处理优化架构
- [x] CDN 加速配置

### 文档完善
- [x] MkDocs 站点配置完整
- [x] 文档目录结构清晰
- [x] API 文档格式标准
- [x] 运维手册内容完整
- [x] 故障排查指南可用
- [x] 版本管理配置正确
