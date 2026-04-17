# 天一阁架构文档 v3.0.24

> **版本**: v3.0.24  
> **日期**: 2026-04-17  
> **主题**: 高级安全架构 + 多租户 SaaS 架构 + 实时协作 + 智能文档生成  
> **依赖版本**: v3.0.23

---

## 版本概述

v3.0.24 架构在 v3.0.23 基础上新增四大核心能力升级：

1. **高级安全架构**: 零信任安全模型 (ZTNA)、安全红队演练、SBOM
2. **多租户 SaaS 架构**: 租户隔离策略、租户计费系统、租户管理控制台
3. **实时协作与共同编辑**: CRDTs 算法、协作感知、版本协作
4. **智能文档自动生成**: 模板引擎、自动生成策略、生成质量控制

---

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    天一阁 v3.0.24                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                              │
│  │   Web UI    │    │  Mobile UI  │    │  API Client │                              │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                              │
│         │                   │                   │                                      │
│         └───────────────────┼───────────────────┘                                      │
│                             │                                                           │
│                    ┌────────▼────────┐                                               │
│                    │   API Gateway   │                                               │
│                    │  (Kong/Traefik) │                                               │
│                    └────────┬────────┘                                               │
│                             │                                                           │
│         ┌───────────────────┼───────────────────┐                                      │
│         │                   │                   │                                      │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐                                │
│  │   Auth Svc  │    │  Search Svc │    │  Oper. Svc  │                                │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                                │
│         │                   │                   │                                      │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐                                │
│  │  User Svc   │    │   RAG Svc   │    │  AIOps Svc  │                                │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                                │
│         │                   │                   │                                      │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐                                │
│  │Personalization│   │ Cache Layer│    │Self-Healing│                                │
│  │   Engine    │    │(Redis/ANN) │    │  Engine    │                                │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                                │
│         │                   │                   │                                      │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐                                │
│  │  Scheduler  │    │  Neo4j / Qdrant│   │ Prediction │                                │
│  │  (Cost-Aware)│   │    (Cache)     │   │   Engine  │                                │
│  └─────────────┘    └───────────────┘    └─────────────┘                                │
│                                                                                        │
│  ╔═══════════════════════════════════════════════════════════════════════════════════╗ │
│  ║                  高级安全架构 (v3.0.24 新增)                                      ║ │
│  ║  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               ║ │
│  ║  │ Zero Trust │ │ Micro       │ │ Red Team   │ │   SBOM     │               ║ │
│  ║  │   Engine   │ │ Segmentation│ │  Engine    │ │  Generator │               ║ │
│  ║  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘               ║ │
│  ╚═══════════════════════════════════════════════════════════════════════════════════╝ │
│                                                                                        │
│  ╔═══════════════════════════════════════════════════════════════════════════════════╗ │
│  ║                  多租户 SaaS 架构 (v3.0.24 新增)                                   ║ │
│  ║  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               ║ │
│  ║  │  Tenant     │ │  Billing    │ │  Tenant    │ │   Usage    │               ║ │
│  ║  │  Isolation  │ │  System     │ │  Console   │ │  Tracker   │               ║ │
│  ║  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘               ║ │
│  ╚═══════════════════════════════════════════════════════════════════════════════════╝ │
│                                                                                        │
│  ╔═══════════════════════════════════════════════════════════════════════════════════╗ │
│  ║                  实时协作与共同编辑 (v3.0.24 新增)                                 ║ │
│  ║  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               ║ │
│  ║  │  CRDTs     │ │  Collab     │ │  Version    │ │  Comment    │               ║ │
│  ║  │  Engine     │ │  Awareness  │ │  Control    │ │   System    │               ║ │
│  ║  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘               ║ │
│  ╚═══════════════════════════════════════════════════════════════════════════════════╝ │
│                                                                                        │
│  ╔═══════════════════════════════════════════════════════════════════════════════════╗ │
│  ║                  智能文档自动生成 (v3.0.24 新增)                                   ║ │
│  ║  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               ║ │
│  ║  │  Template   │ │  Document   │ │  Quality   │ │   AI Gen   │               ║ │
│  ║  │  Engine     │ │  Generator  │ │  Controller │ │   Service   │               ║ │
│  ║  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘               ║ │
│  ╚═══════════════════════════════════════════════════════════════════════════════════╝ │
│                                                                                        │
│  ╔═══════════════════════════════════════════════════════════════════════════════════╗ │
│  ║                  测试与质量保障平台 (v3.0.23)                                      ║ │
│  ║  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               ║ │
│  ║  │ AI Test    │ │  Auto       │ │Coverage    │ │ Quality    │               ║ │
│  ║  │ Generator  │ │ Regression  │ │ Optimizer  │ │  Scanner   │               ║ │
│  ║  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘               ║ │
│  ║  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               ║ │
│  ║  │ Security   │ │Benchmark   │ │  Audit     │ │  Alert     │               ║ │
│  ║  │ Scanner    │ │  Engine    │ │  Tracker   │ │  Response  │               ║ │
│  ║  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘               ║ │
│  ╚═══════════════════════════════════════════════════════════════════════════════════╝ │
│                                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              运维基础设施层                                      │   │
│  │  Prometheus │ Grafana │ Loki │ Tempo │ AlertManager │ PagerDuty │ Vault │   │
│  └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                        │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 模块架构详解

### 1. 高级安全架构

```
security/
├── zero_trust/
│   ├── zero_trust_engine.py        # 零信任安全引擎
│   ├── identity_provider.py          # 身份提供者
│   ├── device_tracker.py             # 设备信任追踪
│   ├── risk_engine.py               # 风险评估引擎
│   ├── policy_engine.py              # 策略引擎 (OPA)
│   └── access_decision.py            # 访问决策
├── micro_segmentation/
│   ├── micro_seg_engine.py           # 微隔离引擎
│   ├── network_policy_manager.py     # 网络策略管理
│   ├── service_mesh_security.py     # 服务网格安全
│   └── traffic_monitor.py           # 流量监控
├── red_team/
│   ├── red_team_engine.py           # 红队演练引擎
│   ├── pentest_framework.py         # 渗透测试框架
│   ├── threat_modeler.py             # 威胁建模器
│   ├── vuln_bounty.py               # 漏洞赏金集成
│   └── attack_path_analyzer.py       # 攻击路径分析
└── sbom/
    ├── sbom_generator.py            # SBOM 生成器
    ├── dependency_analyzer.py        # 依赖分析器
    ├── vuln_scanner.py               # 漏洞扫描器
    ├── license_checker.py            # 许可证检查器
    └── supply_chain_tracker.py       # 供应链追踪器
```

### 2. 多租户 SaaS 架构

```
multi_tenant/
├── tenant_isolation/
│   ├── isolation_manager.py         # 隔离管理器
│   ├── database_isolator.py          # 数据库隔离
│   ├── compute_isolator.py           # 计算隔离
│   ├── network_isolator.py           # 网络隔离
│   └── rls_policy_manager.py         # RLS 策略管理
├── billing/
│   ├── billing_system.py            # 计费系统
│   ├── usage_tracker.py              # 用量追踪
│   ├── pricing_engine.py             # 定价引擎
│   ├── invoice_generator.py          # 账单生成
│   └── payment_gateway.py            # 支付网关
└── tenant_management/
    ├── tenant_registry.py           # 租户注册
    ├── onboarding_workflow.py        # 入驻工作流
    ├── health_monitor.py             # 健康监控
    └── config_manager.py             # 配置管理
```

### 3. 实时协作与共同编辑

```
collaboration/
├── crdt_engine/
│   ├── crdt_collaboration_engine.py # CRDTs 协作引擎
│   ├── yjs_provider.py               # Yjs 提供者
│   ├── awareness_protocol.py         # 感知协议
│   ├── operation_transformer.py       # 操作转换
│   └── conflict_resolver.py          # 冲突解决
├── collab_awareness/
│   ├── presence_service.py           # 在线状态
│   ├── cursor_tracker.py             # 光标追踪
│   ├── selection_sync.py              # 选择同步
│   └── notification_service.py       # 通知服务
├── version_control/
│   ├── branch_manager.py             # 分支管理
│   ├── merge_engine.py               # 合并引擎
│   ├── version_snapshot.py            # 版本快照
│   └── change_history.py             # 变更历史
└── comments/
    ├── comment_system.py            # 评论系统
    ├── comment_thread.py              # 评论线程
    ├── approval_workflow.py          # 审批工作流
    └── mention_parser.py              # @提及解析
```

### 4. 智能文档自动生成

```
document_generation/
├── template_engine/
│   ├── template_engine.py            # 模板引擎核心
│   ├── template_library.py           # 模板库
│   ├── template_market.py            # 模板市场
│   ├── template_renderer.py          # 模板渲染器
│   └── variable_resolver.py          # 变量解析器
├── generators/
│   ├── document_generator.py         # 文档生成器
│   ├── summarizer.py                  # 摘要生成
│   ├── translator.py                   # 翻译引擎
│   ├── report_generator.py            # 报告生成
│   └── knowledge_card_generator.py    # 知识卡片生成
└── quality_control/
    ├── quality_controller.py         # 质量控制器
    ├── hallucination_detector.py      # Hallucination 检测
    ├── fact_checker.py               # 事实核查
    ├── style_checker.py               # 风格检查
    └── completeness_checker.py        # 完整性检查
```

---

## 核心设计

### 1. 零信任安全架构

```python
# 零信任访问评估流程
class ZeroTrustEngine:
    """零信任安全引擎"""
    
    async def evaluate_access(self,
                               user_id: str,
                               device_id: str,
                               resource: str,
                               action: str,
                               context: dict) -> AccessDecision:
        """
        零信任访问评估流程:
        
        1. 身份验证 - MFA + 行为分析
        2. 设备信任评估 - 合规 + 态势
        3. 风险评估 - 实时评分
        4. 动态策略 - OPA 策略引擎
        5. 持续监控 - 会话行为分析
        """
        
        # 身份验证
        identity = await self.identity_provider.verify(
            user_id, context.get("auth_method")
        )
        
        # 设备信任
        device_trust = await self.device_tracker.assess(device_id)
        
        # 风险评估
        risk = await self.risk_engine.calculate(
            user_id, device_id, resource, action
        )
        
        # 策略决策
        decision = await self.policy_engine.evaluate(
            identity=identity,
            device=device_trust,
            risk=risk,
            resource=resource,
            action=action
        )
        
        return decision


class MicroSegmentationEngine:
    """微隔离网络引擎"""
    
    async def enforce_segmentation(self, workload_id: str):
        """
        微隔离策略执行:
        
        1. 工作负载分类
        2. 网络策略生成 (白名单模式)
        3. 服务网格配置 (mTLS)
        4. 持续流量监控
        """
        
        classification = await self._classify_workload(workload_id)
        policy = self._generate_policy(classification)
        
        await self.network_policy.apply(workload_id, policy)
        await self.service_mesh.configure(workload_id, policy.mtls)
        
        return policy
```

### 2. 多租户隔离架构

```python
# 租户隔离管理器
class TenantIsolationManager:
    """租户隔离管理器"""
    
    async def provision_tenant(self, tenant_id: str, config: TenantConfig):
        """
        租户隔离配置流程:
        
        1. Schema 创建 (PostgreSQL)
        2. RLS 策略配置
        3. Kubernetes Namespace 创建
        4. VPC/网络隔离
        """
        
        # 数据库隔离
        await self.db_isolator.create_schema(tenant_id)
        await self.rls_manager.apply_policies(tenant_id)
        
        # 计算隔离
        await self.compute_isolator.create_namespace(tenant_id)
        await self.compute_isolator.set_quota(tenant_id, config.quota)
        
        # 网络隔离
        await self.network_isolator.create_vpc(tenant_id)
        
        return TenantIsolationContext(tenant_id=tenant_id)


class TenantBillingSystem:
    """租户计费系统"""
    
    async def calculate_and_invoice(self, tenant_id: str, period: BillingPeriod):
        """
        账单生成流程:
        
        1. 用量计量 (API/存储/带宽)
        2. 定价计算
        3. 折扣应用
        4. 账单生成 + 审计
        """
        
        usage = await self.usage_tracker.get_usage(tenant_id, period)
        pricing = await self.pricing_engine.calculate(usage)
        invoice = await self.invoice_generator.generate(
            tenant_id, period, pricing
        )
        
        await self._audit_invoice(invoice)
        return invoice
```

### 3. CRDTs 协作引擎

```python
# CRDTs 协作编辑
class CRDTCollaborationEngine:
    """CRDTs 协作编辑引擎"""
    
    async def create_document(self, doc_id: str):
        """
        创建协作文档:
        
        1. 初始化 Yjs Document
        2. WebSocket Provider 配置
        3. 离线持久化 (IndexedDB)
        4. 感知协议初始化
        """
        
        ydoc = Y.Doc()
        provider = WebsocketProvider(f"wss://collab/{doc_id}", ydoc)
        persistence = IndexeddbPersistence(doc_id, ydoc)
        
        return CollabDocument(
            doc_id=doc_id,
            ydoc=ydoc,
            provider=provider,
            persistence=persistence
        )
    
    async def apply_operation(self, doc_id: str, op: CollabOperation):
        """应用协作操作 - CRDTs 保证无冲突"""
        
        doc = await self._get_document(doc_id)
        ytext = doc.ydoc.getText("content")
        
        if op.type == "insert":
            ytext.insert(op.index, op.content)
        elif op.type == "delete":
            ytext.delete(op.index, op.length)
        
        return OperationResult(success=True)


class CollaborationAwareness:
    """协作感知"""
    
    async def track_presence(self, doc_id: str, user_id: str):
        """在线用户状态追踪"""
        
        await self.presence.register(doc_id, user_id, "online")
        await self._broadcast_join(doc_id, user_id)
        
        asyncio.create_task(self._heartbeat_loop(doc_id, user_id))
    
    async def sync_cursor(self, doc_id: str, user_id: str, position: Cursor):
        """光标位置同步"""
        
        state = {"user_id": user_id, "position": position}
        await self.cursor_tracker.update(doc_id, user_id, state)
        await self._broadcast_cursor(doc_id, user_id, state)
```

### 4. 智能文档生成架构

```python
# 文档自动生成
class DocumentAutoGenerator:
    """文档自动生成器"""
    
    async def generate_from_template(self, template_id: str, variables: dict):
        """
        模板生成流程:
        
        1. 模板加载 + 变量解析
        2. AI 内容生成 (摘要/翻译/报告)
        3. 质量检查 (Hallucination/事实/风格)
        4. 渲染输出
        """
        
        template = await self.template_library.get(template_id)
        resolved = await self.variable_resolver.resolve(template.vars, variables)
        
        # AI 生成
        content = {}
        for spec in template.ai_content_specs:
            content[spec.id] = await self._generate_ai(spec, resolved)
        
        # 质量检查
        quality = await self.quality_controller.check(content)
        
        # 渲染
        return await self.template_renderer.render(template, resolved, content)
    
    async def generate_summary(self, content: str, type: str = "abstractive"):
        """内容摘要生成"""
        
        if type == "extractive":
            return await self.summarizer.extractive(content)
        else:
            return await self.summarizer.abstractive(content)


class GenerationQualityController:
    """生成质量控制器"""
    
    async def check_quality(self, content: str, context: dict):
        """
        质量检查流程:
        
        1. Hallucination 检测
        2. 事实一致性验证
        3. 风格一致性检查
        4. 完整性检查
        """
        
        hallu = await self.hallucination_detector.detect(content, context)
        facts = await self.fact_checker.verify(content, context)
        style = await self.style_checker.check(content, context)
        
        score = self._calculate_score(hallu, facts, style)
        
        return QualityReport(
            score=score,
            passed=score >= 0.8,
            issues={"hallucination": hallu, "facts": facts, "style": style}
        )
```

---

## API 接口设计

### 安全 API

```yaml
# 零信任访问评估 API
POST /api/v1/security/zero-trust/evaluate
Request:
  {
    "user_id": "user_xxx",
    "device_id": "device_xxx",
    "resource": "/api/v1/documents",
    "action": "read",
    "context": {"session_id": "xxx", "auth_level": "mfa"}
  }
Response:
  {
    "allowed": true,
    "risk_score": 0.15,
    "conditions": ["device_compliant", "mfa_verified"],
    "token_ttl": 3600
  }

# 设备信任评估 API
POST /api/v1/security/device/assess
Request:
  {
    "device_id": "device_xxx",
    "user_id": "user_xxx"
  }
Response:
  {
    "device_id": "device_xxx",
    "trust_score": 0.85,
    "compliance_status": "compliant",
    "security_posture": "healthy",
    "issues": []
  }

# SBOM 生成 API
POST /api/v1/security/sbom/generate
Request:
  {
    "project_path": "/app",
    "format": "spdx"
  }
Response:
  {
    "sbom_id": "sbom_xxx",
    "format": "spdx",
    "packages": [...],
    "vulnerability_summary": {
      "total": 5,
      "critical": 0,
      "high": 2
    },
    "license_compliance": {...}
  }

# 渗透测试 API
POST /api/v1/security/pentest/run
Request:
  {
    "target_scope": ["api.skyone.shuge.app"],
    "exercise_type": "full"
  }
Response:
  {
    "pentest_id": "pentest_xxx",
    "status": "running",
    "assets_discovered": 10
  }
```

### 多租户 API

```yaml
# 租户入驻 API
POST /api/v1/tenant/onboard
Request:
  {
    "company_name": "示例公司",
    "admin_email": "admin@example.com",
    "plan": "enterprise"
  }
Response:
  {
    "tenant_id": "tenant_xxx",
    "status": "active",
    "isolation_context": {...},
    "admin_credentials": {...}
  }

# 用量查询 API
GET /api/v1/tenant/{tenant_id}/usage?period=2026-04
Response:
  {
    "tenant_id": "tenant_xxx",
    "period": "2026-04",
    "api_usage": {
      "total_requests": 100000,
      "compute_seconds": 50000
    },
    "storage_usage": {
      "documents_gb": 10.5,
      "vectors_gb": 2.3
    },
    "bandwidth_usage": {
      "inbound_gb": 50.2,
      "outbound_gb": 120.8
    }
  }

# 账单生成 API
POST /api/v1/tenant/{tenant_id}/billing/invoice
Request:
  {
    "billing_period": "2026-04"
  }
Response:
  {
    "invoice_id": "inv_xxx",
    "total_amount": 5000.00,
    "line_items": [...],
    "status": "draft"
  }

# 租户健康监控 API
GET /api/v1/tenant/{tenant_id}/health
Response:
  {
    "tenant_id": "tenant_xxx",
    "health_score": 0.95,
    "status": "healthy",
    "resources": {...},
    "services": {...}
  }
```

### 协作 API

```yaml
# 创建协作文档 API
POST /api/v1/collab/document
Request:
  {
    "name": "会议记录",
    "initial_content": ""
  }
Response:
  {
    "doc_id": "collab_xxx",
    "websocket_url": "wss://collab.skyone.shuge.app/collab_xxx",
    "awareness_url": "wss://awareness.skyone.shuge.app/collab_xxx"
  }

# 应用操作 API
POST /api/v1/collab/document/{doc_id}/operations
Request:
  {
    "operation": {
      "type": "insert",
      "index": 42,
      "content": "新文本"
    },
    "user_id": "user_xxx"
  }
Response:
  {
    "operation_id": "op_xxx",
    "version": 15,
    "success": true
  }

# 创建分支 API
POST /api/v1/collab/document/{doc_id}/branch
Request:
  {
    "branch_name": "feature/discussion",
    "base_branch": "main"
  }
Response:
  {
    "branch_id": "branch_xxx",
    "name": "feature/discussion",
    "status": "active"
  }

# 合并分支 API
POST /api/v1/collab/branch/{branch_id}/merge
Request:
  {
    "target_branch": "main",
    "strategy": "auto"
  }
Response:
  {
    "merge_id": "merge_xxx",
    "status": "merged",
    "conflicts": []
  }

# 添加评论 API
POST /api/v1/collab/document/{doc_id}/comments
Request:
  {
    "content": "@张三 请审核这段内容",
    "selection": {"start": 0, "end": 50},
    "mentions": ["user_xxx"]
  }
Response:
  {
    "comment_id": "comment_xxx",
    "created_at": "2026-04-17T00:00:00Z"
  }
```

### 文档生成 API

```yaml
# 模板生成 API
POST /api/v1/generation/from-template
Request:
  {
    "template_id": "template_monthly_report",
    "variables": {
      "company_name": "示例公司",
      "month": "2026年4月"
    },
    "options": {
      "output_format": "markdown"
    }
  }
Response:
  {
    "document_id": "doc_gen_xxx",
    "title": "示例公司月度报告 - 2026年4月",
    "content": "...",
    "quality_score": 0.92
  }

# 摘要生成 API
POST /api/v1/generation/summary
Request:
  {
    "source_content": "...",
    "summary_type": "abstractive",
    "length": "medium",
    "focus_topics": ["营收", "增长"]
  }
Response:
  {
    "summary_id": "sum_xxx",
    "content": "...",
    "key_points": [...],
    "quality_score": 0.88
  }

# 翻译 API
POST /api/v1/generation/translate
Request:
  {
    "source_content": "...",
    "source_lang": "zh",
    "target_lang": "en",
    "style": "formal"
  }
Response:
  {
    "translation_id": "trans_xxx",
    "content": "...",
    "quality_score": 0.95
  }

# 报告生成 API
POST /api/v1/generation/report
Request:
  {
    "report_type": "quarterly_business",
    "data": {
      "revenue": 1000000,
      "customers": 500
    },
    "template": "template_qbr"
  }
Response:
  {
    "report_id": "rpt_xxx",
    "content": {...},
    "charts": [...],
    "key_insights": [...]
  }

# 质量检查 API
POST /api/v1/generation/quality-check
Request:
  {
    "content": "...",
    "context": {
      "source_docs": ["doc_xxx"]
    }
  }
Response:
  {
    "passed": true,
    "score": 0.91,
    "hallucination_risk": "low",
    "fact_consistency": "verified",
    "style_consistency": "passed"
  }
```

---

## 数据模型

### 安全数据存储

```sql
-- 零信任访问日志表
CREATE TABLE zt_access_logs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    device_id VARCHAR(100),
    resource VARCHAR(255),
    action VARCHAR(50),
    decision VARCHAR(20),  -- allow/deny/condition
    risk_score FLOAT,
    conditions JSONB,
    evaluated_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 设备信任表
CREATE TABLE device_trust (
    device_id VARCHAR(100) PRIMARY KEY,
    user_id UUID,
    trust_score FLOAT,
    compliance_status VARCHAR(20),
    security_posture VARCHAR(20),
    last_assessed_at TIMESTAMP,
    issues JSONB
);

-- SBOM 表
CREATE TABLE sboms (
    id UUID PRIMARY KEY,
    project_path VARCHAR(255),
    format VARCHAR(20),
    content JSONB,  -- 完整 SBOM 内容
    packages_count INT,
    vulnerabilities_count INT,
    generated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 渗透测试报告表
CREATE TABLE pentest_reports (
    id UUID PRIMARY KEY,
    target_scope JSONB,
    status VARCHAR(20),
    assets_discovered INT,
    vulnerabilities JSONB,
    attack_paths JSONB,
    risk_score FLOAT,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 多租户数据存储

```sql
-- 租户表
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    plan VARCHAR(50),
    status VARCHAR(20),  -- active/suspended/pending
    isolation_level VARCHAR(20),  -- schema/row
    created_at TIMESTAMP DEFAULT NOW(),
    activated_at TIMESTAMP
);

-- 租户资源配额表
CREATE TABLE tenant_quotas (
    tenant_id UUID PRIMARY KEY,
    api_requests_per_month BIGINT,
    storage_gb INT,
    bandwidth_gb INT,
    ai_generations_per_month INT,
    concurrent_users INT
);

-- 用量记录表
CREATE TABLE usage_records (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    period VARCHAR(20),  -- YYYY-MM
    metric_type VARCHAR(50),  -- api/storage/bandwidth/ai
    metric_value BIGINT,
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- 账单表
CREATE TABLE invoices (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    invoice_number VARCHAR(50) UNIQUE,
    billing_period VARCHAR(20),
    subtotal DECIMAL(10, 2),
    discount DECIMAL(10, 2),
    total_amount DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'CNY',
    status VARCHAR(20),  -- draft/issued/paid/overdue
    issued_at TIMESTAMP,
    due_date TIMESTAMP,
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 账单明细表
CREATE TABLE invoice_line_items (
    id UUID PRIMARY KEY,
    invoice_id UUID NOT NULL,
    service VARCHAR(50),
    description TEXT,
    quantity BIGINT,
    unit_price DECIMAL(10, 4),
    amount DECIMAL(10, 2)
);
```

### 协作数据存储

```sql
-- 协作文档表
CREATE TABLE collab_documents (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    owner_id UUID,
    current_branch VARCHAR(50),
    status VARCHAR(20),
    yjs_state BLOB,  -- Yjs 文档状态
    version BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 分支表
CREATE TABLE collab_branches (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    name VARCHAR(100),
    base_branch VARCHAR(50),
    created_by UUID,
    status VARCHAR(20),
    created_at TIMESTAMP,
    merged_at TIMESTAMP
);

-- 评论表
CREATE TABLE comments (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    version_id VARCHAR(50),
    user_id UUID NOT NULL,
    content TEXT,
    selection JSONB,
    mentions JSONB,
    parent_id UUID,
    status VARCHAR(20),  -- open/resolved
    created_at TIMESTAMP,
    resolved_at TIMESTAMP
);

-- 变更历史表
CREATE TABLE change_history (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    user_id UUID NOT NULL,
    operation_type VARCHAR(20),
    operation_details JSONB,
    version BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 在线状态表
CREATE TABLE user_presence (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    user_id UUID NOT NULL,
    status VARCHAR(20),
    cursor_position JSONB,
    last_seen_at TIMESTAMP
);
```

### 文档生成数据存储

```sql
-- 模板表
CREATE TABLE templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(50),  -- report/summary/translation/qa
    content TEXT,
    variables JSONB,  -- 模板变量定义
    created_by UUID,
    is_public BOOLEAN DEFAULT FALSE,
    usage_count INT DEFAULT 0,
    rating FLOAT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 生成记录表
CREATE TABLE generation_records (
    id UUID PRIMARY KEY,
    template_id UUID,
    document_type VARCHAR(50),
    input_variables JSONB,
    output_content TEXT,
    quality_score FLOAT,
    generation_time_ms INT,
    created_at TIMESTAMP
);

-- 质量检查记录表
CREATE TABLE quality_check_records (
    id UUID PRIMARY KEY,
    generation_id UUID,
    hallucination_score FLOAT,
    fact_consistency_score FLOAT,
    style_score FLOAT,
    overall_score FLOAT,
    issues JSONB,
    checked_at TIMESTAMP
);
```

---

## 配置示例

### 零信任配置

```yaml
# zero_trust_config.yaml
zero_trust:
  enabled: true
  
  identity:
    auth_methods:
      - password
      - mfa_totp
      - mfa_webauthn
    session_timeout: 3600
    step_up_threshold: 0.7
  
  device_trust:
    required_compliance:
      - antivirus
      - disk_encryption
      - os_updated
    min_trust_score: 0.6
  
  risk_engine:
    factors:
      - user_behavior
      - device_posture
      - network_location
      - time_pattern
    threshold: 0.5
  
  policy_engine:
    provider: "opa"
    policies_path: "/policies"
```

### 多租户配置

```yaml
# multi_tenant_config.yaml
multi_tenant:
  isolation_mode: "schema"  # schema / row
  
  database:
    rls_enabled: true
    default_tables: ["documents", "folders", "tags"]
  
  quota_defaults:
    free:
      api_requests: 1000
      storage_gb: 1
      bandwidth_gb: 10
    pro:
      api_requests: 100000
      storage_gb: 100
      bandwidth_gb: 1000
    enterprise:
      api_requests: -1  # unlimited
      storage_gb: -1
      bandwidth_gb: -1
  
  billing:
    currency: "CNY"
    billing_cycle: "monthly"
    payment_terms_days: 30
```

### 协作配置

```yaml
# collaboration_config.yaml
collaboration:
  crdt_engine:
    provider: "yjs"
    sync_interval_ms: 50
    awareness_interval_ms: 100
  
  websocket:
    url: "wss://collab.skyone.shuge.app"
    heartbeat_interval: 30000
    reconnect_delay: 1000
    max_reconnect_attempts: 10
  
  offline:
    persistence: "indexeddb"
    sync_on_reconnect: true
  
  awareness:
    cursor_sync: true
    selection_sync: true
    presence_sync: true
```

### 文档生成配置

```yaml
# document_generation_config.yaml
generation:
  templates:
    library_path: "/templates"
    market_enabled: true
  
  ai:
    model: "claude-3-opus"
    max_tokens: 4000
    temperature: 0.7
    retry_attempts: 3
  
  quality:
    min_score: 0.8
    hallucination_threshold: 0.2
    fact_check_enabled: true
    style_check_enabled: true
  
  supported_languages:
    - zh
    - en
    - ja
    - ko
    - es
    - fr
    - de
```

---

## 部署清单

### Kubernetes 部署

```yaml
# security-platform-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: skyone-security-platform
  namespace: skyone
spec:
  replicas: 2
  selector:
    matchLabels:
      app: skyone-security
  template:
    metadata:
      labels:
        app: skyone-security
    spec:
      containers:
        - name: zero-trust
          image: skyone/zero-trust:v3.0.24
          ports:
            - containerPort: 8003
          env:
            - name: OPA_POLICY_PATH
              value: "/policies"
          resources:
            requests:
              cpu: 500m
              memory: 512Mi

---
# multi-tenant-platform-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: skyone-multi-tenant
  namespace: skyone
spec:
  replicas: 3
  selector:
    matchLabels:
      app: skyone-multi-tenant
  template:
    metadata:
      labels:
        app: skyone-multi-tenant
    spec:
      containers:
        - name: tenant-service
          image: skyone/tenant-service:v3.0.24
          ports:
            - containerPort: 8004
          env:
            - name: BILLING_CURRENCY
              value: "CNY"

---
# collaboration-platform-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: skyone-collaboration
  namespace: skyone
spec:
  replicas: 5
  selector:
    matchLabels:
      app: skyone-collaboration
  template:
    metadata:
      labels:
        app: skyone-collaboration
    spec:
      containers:
        - name: collab-engine
          image: skyone/collab-engine:v3.0.24
          ports:
            - containerPort: 8005
          env:
            - name: YJS_PROVIDER_URL
              value: "wss://collab.skyone.shuge.app"
          resources:
            requests:
              cpu: 1000m
              memory: 1Gi
            limits:
              cpu: 2000m
              memory: 2Gi
```

---

## 性能基准

| 操作 | P50 | P95 | P99 | 备注 |
|------|-----|-----|-----|------|
| 零信任访问评估 | 10ms | 50ms | 100ms | 策略缓存 |
| 设备信任评估 | 50ms | 200ms | 500ms | 外部查询 |
| SBOM 生成 | 5s | 15s | 30s | 取决于依赖数 |
| 租户入驻 | 30s | 60s | 120s | 含资源分配 |
| 用量计量查询 | 5ms | 20ms | 50ms | 聚合查询 |
| 账单生成 | 1s | 3s | 5s | 含费用计算 |
| 协作操作同步 | 50ms | 100ms | 200ms | WebSocket |
| 光标同步 | 10ms | 30ms | 50ms | 广播 |
| 模板生成 | 3s | 8s | 15s | AI 生成 |
| 摘要生成 | 2s | 5s | 10s | LLM 调用 |
| 翻译生成 | 5s | 15s | 30s | 取决于长度 |
| 质量检查 | 500ms | 1s | 2s | 并行检查 |

---

## 总结

v3.0.24 引入的高级安全架构、多租户 SaaS 架构、实时协作与共同编辑、智能文档自动生成功能，使天一阁具备：

1. **零信任安全**: "永不信任，始终验证"的安全理念，微隔离网络，设备持续评估
2. **安全红队**: 自动化渗透测试，威胁建模，漏洞赏金集成
3. **SBOM**: 完整的软件物料清单，依赖关系图谱，CVE 关联，供应链安全
4. **多租户隔离**: Schema/Row 级隔离，计算/网络/应用完全隔离
5. **租户计费**: 精确的用量计量，多级定价模型，完整的账单系统
6. **实时协作**: CRDTs 算法，无冲突协作，在线状态，光标同步
7. **版本协作**: 分支与合并，评论与审批，完整变更历史
8. **智能文档生成**: 模板引擎，自动摘要，多语言翻译，质量控制
9. **生成质量控制**: Hallucination 检测，事实一致性验证，风格检查

该架构与 v3.0.23 的测试与质量保障平台完全兼容，共同构成完整的企业级 SaaS 平台能力。
