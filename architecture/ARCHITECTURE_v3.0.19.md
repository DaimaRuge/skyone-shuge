# 天一阁架构文档 v3.0.19

**版本**: v3.0.19  
**日期**: 2026-04-10  
**主题**: 安全加固 + 高可用性架构 + 灾难恢复增强

---

## 📋 文档历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0.19 | 2026-04-10 | 安全加固架构 + 高可用性架构 + 灾难恢复增强 |
| v3.0.18 | 2026-04-09 | 生产环境部署架构 + 监控告警架构 + 性能压测架构 + 文档站点架构 |
| v3.0.17 | 2026-04-08 | 监控 API 架构 + 限流 API 架构 + 缓存 API 架构 + E2E 测试架构 |
| v3.0.16 | 2026-04-05 | 监控 SDK 架构 + 限流中间件架构 + 多级缓存架构 + ES 客户端架构 |

---

## 🎯 一、WAF 安全加固架构

### 1.1 ModSecurity WAF 部署架构

```yaml
# WAF Deployment (Kubernetes)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: skyone-waf
  namespace: skyone-prod
spec:
  replicas: 2
  selector:
    matchLabels:
      app: skyone-waf
  template:
    metadata:
      labels:
        app: skyone-waf
    spec:
      containers:
      - name: waf
        image: owasp/modsecurity:3.0-apache
        ports:
        - containerPort: 80
        - containerPort: 443
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        volumeMounts:
        - name: rules
          mountPath: /etc/modsecurity.d/rules
        - name: logs
          mountPath: /var/log/modsecurity
        env:
        - name: BACKEND_URL
          value: "http://skyone-api-svc:8000"
      volumes:
      - name: rules
        configMap:
          name: waf-rules
      - name: logs
        emptyDir: {}
---
# WAF Service
apiVersion: v1
kind: Service
metadata:
  name: skyone-waf-svc
  namespace: skyone-prod
spec:
  type: LoadBalancer
  selector:
    app: skyone-waf
  ports:
  - name: http
    port: 80
    targetPort: 80
  - name: https
    port: 443
    targetPort: 443
```

### 1.2 WAF 规则配置 (CRS 3.3)

```apache
# Core Rule Set (CRS) Configuration
# File: /etc/modsecurity.d/rules/crs-setup.conf

# CRS Configuration
SecAction \
  "id:900990,\
   phase:1,\
   pass,\
   t:none,\
   setvar:'tx.crs_exclusion_ratescore=0',\
   setvar:'tx.blocking_score=0',\
   setvar:'tx.paranoia_level=1',\
   setvar:'tx.request_inspect_limit=100000',\
   setvar:'tx.response_body_access=On',\
   setvar:'tx.response_body_limit=524288'"

# SQL Injection Detection
SecRule REQUEST_URI|REQUEST_HEADERS|ARGS "@rx (union\s+select|union\s+all\s+select|exec\s*\(|execute\s*\(|sp_executesql|xp_cmdshell|load_file|into\s+outfile|into\s+dumpfile)" \
  "id:1001,\
   phase:2,\
   deny,\
   status:403,\
   log,\
   auditlog,\
   msg:'SQL Injection Attack Detected',\
   logdata:'Matched: %{MATCHED_VAR}',\
   tag:'application-multi',\
   tag:'language-multi',\
   tag:'platform-database',\
   ctl:ruleRemoveById=1001"

# XSS Attack Detection  
SecRule ARGS|REQUEST_HEADERS "@rx <script[^>]*>.*?</script>|javascript:|on\w+\s*=" \
  "id:1002,\
   phase:2,\
   deny,\
   status:403,\
   msg:'Cross-Site Scripting (XSS) Attack',\
   logdata:'Matched: %{MATCHED_VAR}',\
   tag:'attack-xss'"

# Command Injection Detection
SecRule ARGS "@rx (;\s*|\|\s*|`\s*|\$\(\s*|\\\s*)" \
  "id:1003,\
   phase:2,\
   deny,\
   status:403,\
   msg:'Remote Command Execution Attempt',\
   tag:'attack-rce'"

# Path Traversal Detection
SecRule REQUEST_URI|ARGS "@rx (\.\.\/|\.\.\\|%2e%2e%2f|%2e%2e\/|%2e%2e%5c)" \
  "id:1004,\
   phase:2,\
   deny,\
   status:403,\
   msg:'Path Traversal Attempt',\
   tag:'attack-lfi'"

# CSRF Protection
SecRule REQUEST_METHOD "@rx ^(POST|PUT|DELETE|PATCH)$" \
  "id:1005,\
   phase:1,\
   chain,\
   t:none"
SecRule &ARGS:csrf_token "@eq 0" \
  "id:1006,\
   deny,\
   status:403,\
   msg:'CSRF Token Missing',\
   tag:'attack-csrf'"

# Rate Limiting (100 requests per minute per IP)
SecRule IP:REPUTATION_SCORE "@gt 50" \
  "id:1007,\
   phase:1,\
   deny,\
   status:429,\
   msg:'Rate Limit Exceeded',\
   logdata:'IP: %{REMOTE_ADDR}, Score: %{IP:REPUTATION_SCORE}'"

# GeoIP Blocking (if needed)
# SecRule GEO:COUNTRY_CODE "@within XX,YY,ZZ" \
#   "id:1008,\
#    deny,\
#    status:403"
```

### 1.3 OWASP Top 10 防护矩阵

| OWASP Top 10 | 防护规则 | 触发条件 | 处理方式 |
|--------------|----------|----------|----------|
| A01: Broken Access Control | 900990 | 未授权访问 | 403 + 审计日志 |
| A02: Cryptographic Failures | TLS 1.3 | 旧版 TLS | 拒绝连接 |
| A03: Injection | 1001, 1003 | SQL/命令注入 | 403 + 阻断 |
| A04: Insecure Design | 1005, 1006 | CSRF | 403 + Token 验证 |
| A05: Security Misconfiguration | 900990 | 配置错误 | 403 + 告警 |
| A06: Vulnerable Components | - | 依赖扫描 | CI/CD 检查 |
| A07: Auth Failures | 1007 | 暴力破解 | 429 + IP 封禁 |
| A08: Data Integrity Failures | 整数溢出 | 整数溢出 | 400 + 审计 |
| A09: Logging Failures | ModSecurity | 未记录 | 强制审计 |
| A10: SSRF | 1004 | 路径穿越 | 403 + 阻断 |

---

## 🎯 二、DDoS 防护架构

### 2.1 云原生 DDoS 防护 (AWS/AWS Shield)

```yaml
# AWS Shield Configuration
# Layer 7 DDoS Protection via AWS WAF + Shield Advanced

AWSS::Shield::Protection:
  Properties:
    Name: skyone-ddos-protection
    ResourceArn: !Sub "arn:aws:elasticloadbalancing:${AWS::Region}:${AWS::AccountId}:loadbalancer/net/skyone-${Environment}"
    HealthCheckArns:
      - !Sub "arn:aws:route53:::hostedzone/${HostedZone}/healthcheck/${HealthCheck}"
    ProtectionGroup: skyone-protection-group
    AutoRenew: ENABLED

# Rate-Based Rule
AWS::WAFv2::RuleGroup:
  Properties:
    Name: skyone-rate-limit
    Scope: CLOUDFRONT
    Capacity: 100
    Rules:
      - Name: RateLimitRule
        Priority: 0
        Action:
          Block: {}
        Statement:
          RateBasedStatement:
            Limit: 1000
            EvaluationWindowSec: 60
            ForwardedIPConfig:
              HeaderName: X-Forwarded-For
              FallbackIP: REMOTE_ADDR
```

### 2.2 Nginx 限流配置

```nginx
# /etc/nginx/conf.d/rate-limit.conf

# IP 白名单 (不受限流影响)
geo $limited {
    default 1;
    10.0.0.0/8 0;
    172.16.0.0/12 0;
    192.168.0.0/16 0;
}

# 速率限制区域
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login_limit:1m rate=1r/s;
limit_conn_zone $binary_remote_addr zone=addr:10m;

# API 限流
server {
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        limit_conn addr 10;
        
        # 代理到后端
        proxy_pass http://skyone-api-backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # 登录接口更严格
    location /api/auth/login {
        limit_req zone=login_limit burst=5 nodelay;
        
        # 验证码挑战
        auth_request /captcha-check;
        proxy_pass http://skyone-api-backend;
    }
}

# 验证码服务
server {
    location /captcha-check {
        internal;
        
        # 检查是否需要验证码
        set $captcha_required 0;
        
        if ($cookie_captcha_solved != "true") {
            set $captcha_required 1;
        }
        
        if ($arg_skip_captcha = "true") {
            set $captcha_required 0;
        }
        
        # 返回 200 表示通过, 401 表示需要验证码
        return $captcha_required;
    }
}
```

---

## 🎯 三、API 安全架构

### 3.1 JWT 安全实现

```python
# core/security/jwt.py

from datetime import datetime, timedelta
from typing import Optional
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

class JWTManager:
    def __init__(self):
        # RSA 密钥对 (生产环境从 Vault 加载)
        self.private_key = self._load_private_key()
        self.public_key = self._load_public_key()
        self.algorithm = "RS256"
        self.access_token_expire = 15  # minutes
        self.refresh_token_expire = 7  # days
        self.token_blacklist = set()
    
    def _load_private_key(self) -> rsa.RSAPrivateKey:
        """从安全的密钥存储加载私钥"""
        # 实现: 从 Vault / Kubernetes Secret / AWS KMS 加载
        pass
    
    def create_access_token(
        self, 
        user_id: str, 
        roles: list[str],
        scopes: list[str]
    ) -> str:
        """创建访问令牌"""
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(minutes=self.access_token_expire),
            "type": "access",
            "roles": roles,
            "scopes": scopes,
            "jti": self._generate_jti(),  # JWT ID for revocation
        }
        return jwt.encode(payload, self.private_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """创建刷新令牌"""
        now = datetime.utcnow()
        payload = {
            "sub": _id,
            "iat": now,
            "exp": now + timedelta(days=self.refresh_token_expire),
            "type": "refresh",
            "jti": self._generate_jti(),
        }
        return jwt.encode(payload, self.private_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> dict:
        """验证令牌并返回 payload"""
        try:
            # 首先检查黑名单
            payload = jwt.decode(
                token, 
                self.public_key, 
                algorithms=[self.algorithm]
            )
            
            if payload.get("jti") in self.token_blacklist:
                raise jwt.InvalidTokenError("Token has been revoked")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")
    
    def revoke_token(self, token: str) -> None:
        """撤销令牌 (加入黑名单)"""
        try:
            payload = jwt.decode(
                token, 
                self.public_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # 允许撤销过期的 token
            )
            self.token_blacklist.add(payload["jti"])
        except jwt.InvalidTokenError:
            pass  # 如果 token 无效, 忽略
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """使用刷新令牌获取新的访问令牌"""
        payload = self.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise InvalidTokenError("Not a refresh token")
        
        # 可以从数据库加载用户最新信息, 检查用户状态
        user = self._get_user(payload["sub"])
        if not user or not user.is_active:
            raise UserDisabledError("User is disabled")
        
        return self.create_access_token(
            user_id=user.id,
            roles=user.roles,
            scopes=user.scopes
        )
```

### 3.2 API 权限控制 (RBAC + ABAC)

```python
# core/security/permissions.py

from functools import wraps
from typing import Callable, Optional
from fastapi import HTTPException, status

class Permission:
    """权限检查装饰器"""
    
    def __init__(self, resource: str, action: str):
        self.resource = resource
        self.action = action
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从 kwargs 获取当前用户 (由 Depends 注入)
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            
            # 检查权限
            if not self._check_permission(current_user, self.resource, self.action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {self.resource}:{self.action}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    
    def _check_permission(
        self, 
        user: User, 
        resource: str, 
        action: str
    ) -> bool:
        """检查用户权限 (RBAC + ABAC)"""
        # 1. RBAC 检查
        role_perms = ROLE_PERMISSIONS.get(user.role, [])
        if f"{resource}:{action}" in role_perms:
            return True
        
        # 2. ABAC 检查 (属性-based)
        return self._check_abac(user, resource, action)
    
    def _check_abac(
        self, 
        user: User, 
        resource: str, 
        action: str
    ) -> bool:
        """ABAC 属性检查"""
        # 示例: 检查用户是否只能访问自己的文档
        if resource == "document" and action == "read":
            # 如果用户不是 admin, 只能访问自己的
            if user.role != "admin":
                return False  # 由查询过滤器处理
        return False

# 使用示例
@router.get("/documents/{doc_id}")
@Permission("document", "read")
async def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_user)
):
    # 进一步检查用户是否拥有该文档的访问权限
    doc = await document_service.get(doc_id)
    if not doc or not current_user.can_access(doc):
        raise HTTPException(status_code=404)
    return doc

# 字段级权限
class FieldPermission:
    """字段级别访问控制"""
    
    FIELD_PERMISSIONS = {
        "user.email": ["admin", "owner"],
        "user.password_hash": ["admin"],
        "document.content": ["editor", "owner", "admin"],
        "document.metadata.internal_notes": ["admin"],
    }
    
    def filter_fields(self, user: User, document: dict, action: str) -> dict:
        """根据权限过滤字段"""
        filtered = document.copy()
        
        for field, allowed_roles in self.FIELD_PERMISSIONS.items():
            if user.role not in allowed_roles:
                self._remove_field(filtered, field)
        
        return filtered
    
    def _remove_field(self, doc: dict, field_path: str):
        """移除嵌套字段"""
        parts = field_path.split(".")
        current = doc
        for part in parts[:-1]:
            if part not in current:
                return
            current = current[part]
        if parts[-1] in current:
            del current[parts[-1]]
```

---

## 🎯 四、安全审计日志架构

### 4.1 审计事件模型

```python
# models/audit.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class AuditEventType(str, Enum):
    # 认证事件
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_REGISTER = "auth.register"
    AUTH_2FA_ENABLED = "auth.2fa_enabled"
    AUTH_2FA_DISABLED = "auth.2fa_disabled"
    AUTH_PASSWORD_CHANGED = "auth.password_changed"
    AUTH_TOKEN_REFRESHED = "auth.token_refreshed"
    AUTH_FAILED_LOGIN = "auth.failed_login"
    
    # 授权事件
    AUTHZ_ACCESS_GRANTED = "authz.access_granted"
    AUTHZ_ACCESS_REVOKED = "authz.access_revoked"
    AUTHZ_ROLE_CHANGED = "authz.role_changed"
    AUTHZ_PERMISSION_DENIED = "authz.permission_denied"
    
    # 数据事件
    DATA_DOCUMENT_CREATED = "data.document_created"
    DATA_DOCUMENT_READ = "data.document_read"
    DATA_DOCUMENT_UPDATED = "data.document_updated"
    DATA_DOCUMENT_DELETED = "data.document_deleted"
    DATA_DOCUMENT_EXPORTED = "data.document_exported"
    DATA_DOCUMENT_SHARED = "data.document_shared"
    
    # 敏感数据事件
    DATA_SENSITIVE_ACCESSED = "data.sensitive_accessed"
    DATA_SENSITIVE_EXPORTED = "data.sensitive_exported"
    DATA_SENSITIVE_DELETED = "data.sensitive_deleted"
    
    # 安全事件
    SECURITY_WAF_BLOCKED = "security.waf_blocked"
    SECURITY_RATE_LIMITED = "security.rate_limited"
    SECURITY_SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    SECURITY_API_KEY_CREATED = "security.api_key_created"
    SECURITY_API_KEY_REVOKED = "security.api_key_revoked"

class AuditEvent(BaseModel):
    """审计事件模型"""
    event_id: str = Field(..., description="唯一事件 ID (UUID)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: AuditEventType
    
    # 行为者信息
    actor: ActorInfo = Field(..., description="执行操作的主体")
    
    # 资源信息
    resource: Optional[ResourceInfo] = Field(None, description="被操作的资源")
    
    # 上下文信息
    context: AuditContext = Field(..., description="审计上下文")
    
    # 结果
    result: AuditResult = Field(..., description="操作结果")
    result_detail: Optional[str] = Field(None, description="结果详情")
    
    # 风险评估
    risk_score: float = Field(0.0, ge=0.0, le=1.0, description="风险评分")
    
    # 元数据
    metadata: dict = Field(default_factory=dict, description="额外元数据")

class ActorInfo(BaseModel):
    """行为者信息"""
    user_id: Optional[str] = Field(None, description="用户 ID")
    user_email: Optional[str] = Field(None, description="用户邮箱")
    api_key_id: Optional[str] = Field(None, description="API Key ID")
    ip_address: str = Field(..., description="IP 地址")
    user_agent: Optional[str] = Field(None, description="User Agent")
    geo_location: Optional[GeoLocation] = Field(None, description="地理位置")

class GeoLocation(BaseModel):
    """地理位置"""
    country: str
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ResourceInfo(BaseModel):
    """资源信息"""
    resource_type: str = Field(..., description="资源类型")
    resource_id: str = Field(..., description="资源 ID")
    resource_name: Optional[str] = Field(None, description="资源名称")
    owner_id: Optional[str] = Field(None, description="资源所有者")

class AuditContext(BaseModel):
    """审计上下文"""
    request_id: str = Field(..., description="请求 ID")
    session_id: Optional[str] = Field(None, description="会话 ID")
    service_name: str = Field(..., description="服务名称")
    service_version: str = Field(..., description="服务版本")
    environment: str = Field(..., description="环境 (prod/staging)")

class AuditResult(str, Enum):
    """审计结果"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    BLOCKED = "blocked"
```

### 4.2 审计日志服务

```python
# services/audit_service.py

import json
import asyncio
from datetime import datetime
from typing import Optional
from elasticsearch import AsyncElasticsearch
from kafka import KafkaProducer

class AuditService:
    """审计日志服务"""
    
    def __init__(self):
        self.es_client = AsyncElasticsearch(["https://es-skyone:9200"])
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=["kafka:9092"],
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        self.index_prefix = "skyone-audit"
    
    async def log_event(self, event: AuditEvent) -> None:
        """记录审计事件"""
        # 1. 计算风险评分
        risk_score = self._calculate_risk_score(event)
        event.risk_score = risk_score
        
        # 2. 异步发送到 Elasticsearch (热数据)
        asyncio.create_task(self._index_to_elasticsearch(event))
        
        # 3. 发送到 Kafka (用于实时分析)
        asyncio.create_task(self._send_to_kafka(event))
        
        # 4. 如果是高风险事件, 立即发送告警
        if risk_score > 0.7:
            asyncio.create_task(self._send_security_alert(event))
    
    async def _index_to_elasticsearch(self, event: AuditEvent) -> None:
        """索引到 Elasticsearch"""
        index_name = f"{self.index_prefix}-{datetime.utcnow():%Y.%m}"
        await self.es_client.index(
            index=index_name,
            id=event.event_id,
            document=event.model_dump()
        )
    
    async def _send_to_kafka(self, event: AuditEvent) -> None:
        """发送到 Kafka 进行实时分析"""
        self.kafka_producer.send(
            "skyone-audit-events",
            value=event.model_dump()
        )
    
    async def _send_security_alert(self, event: AuditEvent) -> None:
        """发送安全告警"""
        # 集成到告警系统
        await alert_service.send(
            severity="high",
            title=f"Security Alert: {event.event_type}",
            description=f"High risk activity detected from {event.actor.ip_address}",
            metadata=event.model_dump()
        )
    
    def _calculate_risk_score(self, event: AuditEvent) -> float:
        """计算风险评分"""
        score = 0.0
        
        # 失败登录
        if event.event_type == AuditEventType.AUTH_FAILED_LOGIN:
            score += 0.3
        
        # 异常时间访问 (非工作时间)
        hour = event.timestamp.hour
        if hour < 8 or hour > 22:
            score += 0.2
        
        # 新位置登录
        if event.event_type == AuditEventType.AUTH_LOGIN:
            if self._is_unusual_location(event):
                score += 0.3
        
        # 批量数据访问
        if event.event_type == AuditEventType.DATA_DOCUMENT_EXPORTED:
            count = event.metadata.get("document_count", 0)
            if count > 100:
                score += 0.2
        
        # 敏感数据访问
        if event.event_type == AuditEventType.DATA_SENSITIVE_ACCESSED:
            score += 0.4
        
        # WAF 拦截
        if event.event_type == AuditEventType.SECURITY_WAF_BLOCKED:
            score += 0.5
        
        return min(score, 1.0)
    
    async def query_logs(
        self,
        user_id: Optional[str] = None,
        event_types: Optional[list[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        risk_threshold: float = 0.0,
        size: int = 100
    ) -> list[AuditEvent]:
        """查询审计日志"""
        must_clauses = []
        
        if user_id:
            must_clauses.append({"term": {"actor.user_id": user_id}})
        
        if event_types:
            must_clauses.append({"terms": {"event_type": event_types}})
        
        if start_time or end_time:
            range_query = {"timestamp": {}}
            if start_time:
                range_query["timestamp"]["gte"] = start_time.isoformat()
            if end_time:
                range_query["timestamp"]["lte"] = end_time.isoformat()
            must_clauses.append({"range": range_query})
        
        if risk_threshold > 0:
            must_clauses.append({"range": {"risk_score": {"gte": risk_threshold}}})
        
        query = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}]
            }
        }
        
        result = await self.es_client.search(
            index=f"{self.index_prefix}-*",
            query=query,
            sort=[{"timestamp": "desc"}],
            size=size
        )
        
        return [AuditEvent(**hit["_source"]) for hit in result["hits"]["hits"]]
```

---

## 🎯 五、高可用性架构

### 5.1 Kubernetes 高可用部署

```yaml
# kubernetes/ha-deployment.yaml

---
# API Deployment (高可用)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: skyone-api
  namespace: skyone-prod
  labels:
    app: skyone-api
    version: v3.0.19
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: skyone-api
  template:
    metadata:
      labels:
        app: skyone-api
        version: v3.0.19
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - skyone-api
              topologyKey: kubernetes.io/hostname
      containers:
      - name: api
        image: skyone/shuge:v3.0.19
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 9090
          name: grpc
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "2000m"
            memory: "2Gi"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 3
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: skyone-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: skyone-secrets
              key: redis-url
        - name: JWT_PRIVATE_KEY
          valueFrom:
            secretKeyRef:
              name: skyone-secrets
              key: jwt-private-key
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 10"]
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: skyone-api

---
# API Service (ClusterIP with session affinity)
apiVersion: v1
kind: Service
metadata:
  name: skyone-api-svc
  namespace: skyone-prod
spec:
  type: ClusterIP
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
  selector:
    app: skyone-api
  ports:
  - name: http
    port: 80
    targetPort: 8000
  - name: grpc
    port: 9090
    targetPort: 9090

---
# HPA (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: skyone-api-hpa
  namespace: skyone-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: skyone-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Pods
        value: 4
        periodSeconds: 60
      - type: Percent
        value: 100
        periodSeconds: 60
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Pods
        value: 2
        periodSeconds: 60
      - type: Percent
        value: 10
        periodSeconds: 60
      selectPolicy: Min
```

### 5.2 PostgreSQL 高可用 (Patroni)

```yaml
# kubernetes/patroni-config.yaml

---
# Patroni Operator (使用 Zalando Operator)
apiVersion: acid.zalan.do/v1
kind: PatroniCluster
metadata:
  name: skyone-postgres
  namespace: skyone-prod
spec:
  teamId: skyone
  postgresVersion: "15"
  numberOfInstances: 3
  enableMasterLoadBalancer: true
  enableReplicaLoadBalancer: true
  loadBalancerSourceRanges:
    - 10.0.0.0/8
    - 192.168.0.0/16
  volume:
    size: 100Gi
    storageClass: ssd-regional
  resources:
    requests:
      cpu: "1"
      memory: "2Gi"
    limits:
      cpu: "4"
      memory: "8Gi"
  patroni:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
  bootstrap:
    initdb:
      encoding: UTF8
      locale: C
    users:
      admin:
        password: <admin-password>
        options:
          - SUPERUSER
          - LOGIN
      replicator:
        password: <replicator-password>
        options:
          - REPLICATION
    dcs:
      postgresql:
        parameters:
          max_connections: 500
          shared_buffers: 2GB
          effective_cache_size: 6GB
          maintenance_work_mem: 512MB
          checkpoint_completion_target: 0.9
          wal_buffers: 16MB
          default_statistics_target: 100
          random_page_cost: 1.1
          effective_io_concurrency: 200
          max_worker_processes: 8
          max_parallel_workers_per_gather: 4
          max_parallel_workers: 8
          max_parallel_maintenance_workers: 4
```

---

## 🎯 六、灾难恢复架构

### 6.1 Velero 备份配置

```yaml
# kubernetes/velero-config.yaml

---
# Velero BackupSchedule (定时备份)
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: skyone-backup-daily
  namespace: velero
spec:
  schedule: "0 2 * * *"  # 每天凌晨 2:00
  template:
    ttl: 720h  # 30 天保留
    includedNamespaces:
    - skyone-prod
    - skyone-staging
    excludedResources:
    - events
    - pods
    storageLocation: default
    volumeSnapshotLocations:
    - default
    hooks:
      resources:
      - name: postgresql-backup-hook
        includedNamespaces:
        - skyone-prod
        pre:
        - exec:
            container: postgres
            command:
            - /bin/sh
            - -c
            - "pg_dump -U postgres skyone > /tmp/pre-backup.sql"
            onError: Fail
            timeout: 5m
        post:
        - exec:
            container: postgres
            command:
            - /bin/sh
            - -c
            - "rm /tmp/pre-backup.sql"
            onError: Continue
            timeout: 1m

---
# BackupStorageLocation (S3 存储)
apiVersion: velero.io/v1
kind: BackupStorageLocation
metadata:
  name: default
  namespace: velero
spec:
  provider: aws
  objectStorage:
    bucket: skyone-backups
    prefix: velero
  config:
    region: cn-north-1
    s3ForcePathStyle: "true"
    s3Url: https://s3.cn-north-1.amazonaws.com.cn

---
# VolumeSnapshotLocation (EBS 快照)
apiVersion: velero.io/v1
kind: VolumeSnapshotLocation
metadata:
  name: default
  namespace: velero
spec:
  provider: aws
  config:
    region: cn-north-1
```

### 6.2 故障切换 Runbook Automation

```python
# scripts/failover.py

import asyncio
import subprocess
from datetime import datetime
from typing import Optional
import click
from kubernetes import client, config

class DisasterRecovery:
    """灾难恢复管理器"""
    
    def __init__(self, environment: str = "prod"):
        self.environment = environment
        self.primary_region = "cn-north-1"
        self.secondary_region = "cn-east-1"
        self.current_region = self._detect_current_region()
        self.is_primary = self.current_region == self.primary_region
    
    async def check_health(self) -> dict:
        """健康检查"""
        checks = {
            "database": await self._check_database(),
            "cache": await self._check_cache(),
            "storage": await self._check_storage(),
            "api": await self._check_api(),
        }
        
        all_healthy = all(checks.values())
        return {
            "healthy": all_healthy,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def trigger_failover(self, reason: str) -> dict:
        """触发故障切换"""
        if not await self._can_failover():
            return {"success": False, "error": "Failover not possible"}
        
        click.echo(f"⚠️ Starting failover: {reason}")
        
        # 1. 停止主区域写入
        await self._disable_primary_writes()
        
        # 2. 等待复制完成
        await self._wait_for_replication()
        
        # 3. 提升备用数据库
        await self._promote_standby()
        
        # 4. 更新 DNS
        await self._update_dns()
        
        # 5. 通知
        await self._send_notifications(f"Failover completed to {self.secondary_region}")
        
        return {"success": True, "new_primary": self.secondary_region}
    
    async def _check_database(self) -> bool:
        """检查数据库健康"""
        # Patroni API 检查
        try:
            async with aiohttp.get("http://patroni:8008/health") as resp:
                return resp.status == 200
        except:
            return False
    
    async def _promote_standby(self) -> None:
        """提升备用数据库为主节点"""
        # 执行 Patroni switchover
        result = subprocess.run([
            "kubectl", "exec", "-n", "skyone-prod",
            "skyone-postgres-0", "--", "patronictl", 
            "switchover", "--candidate", "skyone-postgres-1"
        ], capture_output=True)
        
        if result.returncode != 0:
            raise Exception(f"Switchover failed: {result.stderr.decode()}")
    
    async def _update_dns(self) -> None:
        """更新 DNS 记录"""
        # 更新 Route53
        client = boto3.client("route53")
        
        # 获取托管区域
        hosted_zones = client.list_hosted_zones()
        
        # 更新 API 记录
        # ...
    
    async def _send_notifications(self, message: str) -> None:
        """发送通知"""
        # 发送告警
        await alert_service.send(
            severity="critical",
            title="Disaster Recovery Event",
            description=message,
            channels=["email", "sms", "slack"]
        )

@click.group()
def cli():
    """灾难恢复命令行工具"""
    pass

@cli.command()
@click.option("--reason", required=True, help="Failover reason")
async def failover(reason: str):
    """触发故障切换"""
    dr = DisasterRecovery()
    
    # 检查是否应该切换
    health = await dr.check_health()
    if health["healthy"]:
        click.echo("✅ All systems healthy, no failover needed")
        return
    
    # 执行切换
    result = await dr.trigger_failover(reason)
    
    if result["success"]:
        click.echo(f"✅ Failover completed to {result['new_primary']}")
    else:
        click.echo(f"❌ Failover failed: {result['error']}")

if __name__ == "__main__":
    cli()
```

---

## 🎯 七、合规与隐私架构

### 7.1 GDPR 数据主体权利 API

```python
# api/routers/gdpr.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/gdpr", tags=["GDPR Compliance"])

class DataExportRequest(BaseModel):
    """数据导出请求"""
    include_documents: bool = True
    include_analytics: bool = True
    format: str = "json"  # json, csv, xml

class DataExportResponse(BaseModel):
    """数据导出响应"""
    request_id: str
    status: str
    estimated_completion: Optional[datetime]
    download_url: Optional[str]

class DataDeletionRequest(BaseModel):
    """数据删除请求"""
    confirmation: str = "DELETE_MY_DATA"
    reason: Optional[str] = None

class DataCorrectionRequest(BaseModel):
    """数据更正请求"""
    field: str
    old_value: str
    new_value: str
    justification: str

@router.get("/export", response_model=DataExportResponse)
async def request_data_export(
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """请求导出用户所有数据 (数据可携权)"""
    # 创建导出任务
    task = await gdpr_service.create_export_task(
        user_id=current_user.id,
        include_documents=True,
        include_analytics=True
    )
    
    # 后台处理大文件导出
    background_tasks.add_task(
        gdpr_service.process_export_task,
        task_id=task.id
    )
    
    return DataExportResponse(
        request_id=task.id,
        status="processing",
        estimated_completion=task.estimated_completion
    )

@router.delete("/delete", response_model=DataDeletionResponse)
async def request_data_deletion(
    request: DataDeletionRequest,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """请求删除所有用户数据 (被遗忘权)"""
    if request.confirmation != "DELETE_MY_DATA":
        raise HTTPException(
            status_code=400,
            detail="Invalid confirmation"
        )
    
    # 验证用户身份 (GDPR 要求额外验证)
    await auth_service.verify_identity(
        user_id=current_user.id,
        verification_type="password"
    )
    
    # 创建删除任务 (30 天冷静期)
    task = await gdpr_service.create_deletion_task(
        user_id=current_user.id,
        reason=request.reason,
        grace_period_days=30
    )
    
    # 发送确认邮件
    await email_service.send(
        to=current_user.email,
        template="gdpr_deletion_confirmation",
        context={
            "user": current_user,
            "deletion_date": task.scheduled_deletion,
            "cancel_url": f"/gdpr/delete/{task.id}/cancel"
        }
    )
    
    return DataDeletionResponse(
        request_id=task.id,
        status="pending_deletion",
        scheduled_deletion=task.scheduled_deletion,
        message="Your data will be deleted after 30 days. You can cancel this request."
    )

@router.post("/delete/{request_id}/cancel")
async def cancel_deletion(
    request_id: str,
    current_user: User = Depends(get_current_user)
):
    """取消删除请求"""
    task = await gdpr_service.get_deletion_task(request_id)
    
    if task.user_id != current_user.id:
        raise HTTPException(status_code=404)
    
    if task.status != "pending_deletion":
        raise HTTPException(
            status_code=400,
            detail="Deletion already in progress or completed"
        )
    
    await gdpr_service.cancel_deletion_task(request_id)
    
    return {"status": "cancelled"}

@router.put("/correct")
async def correct_data(
    request: DataCorrectionRequest,
    current_user: User = Depends(get_current_user)
):
    """更正不准确的数据 (更正权)"""
    # 验证更正请求的合理性
    correction = await gdpr_service.process_correction(
        user_id=current_user.id,
        field=request.field,
        old_value=request.old_value,
        new_value=request.new_value,
        justification=request.justification
    )
    
    # 记录更正日志 (审计)
    await audit_service.log(
        event_type="gdpr.data_corrected",
        actor=current_user,
        resource={"type": "user_data", "field": request.field},
        result="success",
        metadata={
            "old_value_hash": hashlib.sha256(request.old_value.encode()).hexdigest(),
            "justification": request.justification
        }
    )
    
    return {"status": "corrected", "correction": correction}

@router.get("/processing-records")
async def get_processing_records(
    current_user: User = Depends(get_current_user)
):
    """获取数据处理记录 (访问权)"""
    records = await gdpr_service.get_user_processing_records(
        user_id=current_user.id
    )
    
    return {
        "user_id": current_user.id,
        "records": records,
        "last_updated": datetime.utcnow().isoformat()
    }
```

### 7.2 数据脱敏服务

```python
# services/data_masking.py

import re
import hashlib
from typing import Any, Optional, Callable
from datetime import datetime
from enum import Enum

class MaskingType(str, Enum):
    """脱敏类型"""
    HASH = "hash"                    # SHA-256 哈希
    MASK = "mask"                    # 部分掩码
    GENERALIZE = "generalize"        # 泛化
    ENCRYPT = "encrypt"              # 加密
    TOKENIZE = "tokenize"            # 替换为 Token
    REMOVE = "remove"               # 删除

class SensitiveDataMasker:
    """敏感数据脱敏器"""
    
    # 内置脱敏规则
    RULES = {
        # 个人信息
        "email": {"type": MaskingType.MASK, "pattern": r"^(\w)[\w.*]*(@\w+)$", "replace": r"\1***\2"},
        "phone": {"type": MaskingType.MASK, "pattern": r"^(\d{3})\d{4}(\d{4})$", "replace": r"\1****\2"},
        "id_card": {"type": MaskingType.MASK, "pattern": r"^(\d{6})\d{8}(\d{4}[\dXx])$", "replace": r"\1********\2"},
        "name": {"type": MaskingType.MASK, "pattern": r"^(.{1})(.*)(.{1})$", "replace": r"\1***\3"},
        
        # 金融信息
        "bank_card": {"type": MaskingType.MASK, "pattern": r"^(\d{4})\d{8,12}(\d{4})$", "replace": r"\1****\2"},
        "cvv": {"type": MaskingType.REMOVE},
        
        # 认证信息
        "password": {"type": MaskingType.HASH},
        "api_key": {"type": MaskingType.MASK, "pattern": r"^(.{8}).+(.{4})$", "replace": r"\1****\2"},
        
        # 地址
        "address": {"type": MaskingType.GENERALIZE, "precision": "city"},
    }
    
    def mask(self, value: str, data_type: str, **kwargs) -> str:
        """根据类型脱敏"""
        rule = self.RULES.get(data_type)
        if not rule:
            return value
        
        mask_type = MaskingType(rule["type"])
        
        if mask_type == MaskingType.MASK:
            return re.sub(rule["pattern"], rule["replace"], value)
        
        elif mask_type == MaskingType.HASH:
            return hashlib.sha256(value.encode()).hexdigest()
        
        elif mask_type == MaskingType.GENERALIZE:
            return self._generalize(value, kwargs.get("precision", "city"))
        
        elif mask_type == MaskingType.REMOVE:
            return "[REDACTED]"
        
        elif mask_type == MaskingType.TOKENIZE:
            return self._tokenize(value)
        
        return value
    
    def mask_document(self, doc: dict, fields: list[str]) -> dict:
        """批量脱敏文档中的多个字段"""
        masked = doc.copy()
        
        for field_path, data_type in fields:
            value = self._get_nested_value(masked, field_path)
            if value is not None:
                masked_value = self.mask(str(value), data_type)
                self._set_nested_value(masked, field_path, masked_value)
        
        return masked
    
    def mask_for_logging(self, data: dict, log_level: str = "info") -> dict:
        """根据日志级别自动脱敏"""
        # 定义各日志级别的敏感字段
        sensitive_fields = {
            "debug": ["email", "phone", "id_card", "bank_card", "password"],
            "info": ["phone", "id_card", "bank_card", "password"],
            "warn": ["password", "api_key"],
            "error": [],  # 错误日志不自动脱敏, 但人工审查
        }
        
        fields_to_mask = sensitive_fields.get(log_level, [])
        result = data.copy()
        
        for field, data_type in fields_to_mask:
            if field in result:
                result[field] = self.mask(str(result[field]), data_type)
        
        return result
    
    def _generalize(self, value: str, precision: str) -> str:
        """泛化处理"""
        if precision == "city":
            # 只保留城市级别
            return value[:3] + "***"
        elif precision == "region":
            return value[:2] + "***"
        return "***"
    
    def _tokenize(self, value: str) -> str:
        """替换为 Token (用于测试环境)"""
        # 实际实现应从 Token Vault 获取
        token = hashlib.md5(value.encode()).hexdigest()[:16]
        return f"tok_{token}"
```

---

## 📊 部署检查清单

### 安全加固
- [ ] WAF 规则已部署并测试
- [ ] DDoS 防护已启用
- [ ] API 安全中间件已配置
- [ ] JWT 密钥已轮换
- [ ] 安全审计日志已启用

### 高可用性
- [ ] 多副本部署已确认
- [ ] HPA 配置已验证
- [ ] Pod 反亲和性已配置
- [ ] 区域分布已检查
- [ ] 故障转移机制已测试

### 灾难恢复
- [ ] 备份任务已配置
- [ ] 备份恢复已测试
- [ ] DNS 故障切换已验证
- [ ] RTO/RPO 已测量
- [ ] Runbook 已更新

### 合规
- [ ] GDPR API 已部署
- [ ] 数据脱敏已配置
- [ ] 隐私政策已更新
- [ ] 用户同意已收集

---

## 📁 相关文件

```
skyone-shuge/
├── prd/
│   └── MVP_v3.0.19.md              # PRD 文档
│
└── architecture/
    └── ARCHITECTURE_v3.0.19.md     # 本文档
```

---

**版本**: v3.0.19  
**更新日期**: 2026-04-10  
**状态**: 已完成
