# 天一阁架构文档 v3.0.12

**版本**: v3.0.12
**日期**: 2026-03-29
**主题**: LibIndex One 同步服务 + 项目级管理 + 协作功能 + 插件系统

---

## 📋 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0.12 | 2026-03-29 | LibIndex One 同步架构 + 项目管理架构 + 协作架构 + 插件架构 |
| v3.0.11 | 2026-03-29 | 前端认证架构 + 向量搜索架构 + 批量操作架构 |
| v3.0.10 | 2026-03-25 | WebSocket 客户端架构 + Knowledge QA Agent 架构 + 断点续传架构 |

---

## 🏗️ 系统架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端层 (React)                           │
├─────────────────────────────────────────────────────────────────┤
│  Project UI  │  Collaboration  │  Plugin System  │  Sync UI    │
│  - Switcher  │  - Editor       │  - Marketplace  │  - Status   │
│  - Template  │  - Comments     │  - Manager      │  - Conflict │
│  - Settings  │  - Activity     │  - Sandbox      │  - Config   │
└─────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                         API 层 (FastAPI)                         │
├─────────────────────────────────────────────────────────────────┤
│  /projects  │  /collaboration  │  /plugins  │  /sync          │
│  - CRUD     │  - WS Handler    │  - CRUD    │  - LibIndex     │
│  - Members  │  - Comments      │  - Hooks   │  - Jobs         │
│  - Templates│  - Activities    │  - Execute │  - Conflicts    │
└─────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                      服务层 (Services)                           │
├─────────────────────────────────────────────────────────────────┤
│  ProjectService  │  CollaborationService  │  PluginManager    │
│  - Multi-tenancy │  - CRDT (Yjs)          │  - Sandbox        │
│  - Permissions   │  - Awareness           │  - Hooks          │
│  - Templates     │  - Comments            │  - Security       │
├─────────────────────────────────────────────────────────────────┤
│                    LibIndexSyncService                           │
│  - Bidirectional Sync  │  - Conflict Resolution  │  - Queue       │
└─────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                      数据层 (PostgreSQL)                         │
├─────────────────────────────────────────────────────────────────┤
│  projects  │  project_members  │  comments  │  activity_logs  │
│  plugins   │  plugin_hooks     │  sync_mappings             │
│  sync_conflicts                                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔗 一、LibIndex One 同步架构

### 1.1 同步服务架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     LibIndexSyncService                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Sync Engine │  │ Job Queue   │  │ Conflict Resolver       │  │
│  │             │  │             │  │                         │  │
│  │ - Full Sync │  │ - Priority  │  │ - Auto Resolution       │  │
│  │ - Increment │  │ - Retry     │  │ - Manual Resolution     │  │
│  │ - Metadata  │  │ - Schedule  │  │ - Merge Strategy        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Change      │  │ Version     │  │ Sync Mapping            │  │
│  │ Detector    │  │ Control     │  │ Repository              │  │
│  │             │  │             │  │                         │  │
│  │ - Hash Diff │  │ - Vector    │  │ - Local ↔ Remote        │  │
│  │ - Timestamp │  │ - Clock     │  │ - Version Tracking      │  │
│  │ - Event Log │  │ - History   │  │ - Status Management     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Local Store   │  │   Sync Queue    │  │  LibIndex One   │
│                 │  │                 │  │                 │
│  - PostgreSQL   │  │  - Redis        │  │  - REST API     │
│  - Vector DB    │  │  - Celery       │  │  - WebSocket    │
│  - File Storage │  │  - Scheduler    │  │  - GraphQL      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 1.2 同步状态机

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  PENDING │───▶│ RUNNING  │───▶│COMPLETED │    │  FAILED  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                     │                              │
                     ▼                              │
                ┌──────────┐    ┌──────────┐       │
                │ CONFLICT │───▶│ RESOLVED │───────┘
                └──────────┘    └──────────┘
```

### 1.3 冲突解决策略

```typescript
// services/sync/ConflictResolver.ts
export enum ConflictResolutionStrategy {
  LOCAL_WINS = 'local',      // 本地版本优先
  REMOTE_WINS = 'remote',    // 远程版本优先
  TIMESTAMP = 'timestamp',   // 最新时间戳优先
  MERGE = 'merge',           // 尝试合并
  MANUAL = 'manual'          // 人工解决
}

export class ConflictResolver {
  resolve(
    local: DocumentVersion,
    remote: DocumentVersion,
    strategy: ConflictResolutionStrategy
  ): ResolutionResult {
    switch (strategy) {
      case ConflictResolutionStrategy.LOCAL_WINS:
        return { winner: 'local', action: 'push' };
        
      case ConflictResolutionStrategy.REMOTE_WINS:
        return { winner: 'remote', action: 'pull' };
        
      case ConflictResolutionStrategy.TIMESTAMP:
        return local.updatedAt > remote.updatedAt
          ? { winner: 'local', action: 'push' }
          : { winner: 'remote', action: 'pull' };
          
      case ConflictResolutionStrategy.MERGE:
        return this.attemptMerge(local, remote);
        
      case ConflictResolutionStrategy.MANUAL:
        return { winner: null, action: 'conflict', requiresManual: true };
    }
  }
  
  private attemptMerge(local: DocumentVersion, remote: DocumentVersion): ResolutionResult {
    // 使用 diff3 或类似算法尝试合并
    const merged = this.threeWayMerge(
      local.content,
      remote.content,
      this.findCommonAncestor(local, remote)
    );
    
    if (merged.hasConflicts) {
      return { winner: null, action: 'conflict', requiresManual: true };
    }
    
    return { winner: 'merged', action: 'commit', content: merged.content };
  }
}
```

---

## 👥 二、项目级管理架构

### 2.1 多租户架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      租户隔离层                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│   │  Project A  │    │  Project B  │    │  Project C  │        │
│   │             │    │             │    │             │        │
│   │ ┌─────────┐ │    │ ┌─────────┐ │    │ ┌─────────┐ │        │
│   │ │ Tenant  │ │    │ │ Tenant  │ │    │ │ Tenant  │ │        │
│   │ │ Context │ │    │ │ Context │ │    │ │ Context │ │        │
│   │ └─────────┘ │    │ └─────────┘ │    │ └─────────┘ │        │
│   │             │    │             │    │             │        │
│   │ - Documents │    │ - Documents │    │ - Documents │        │
│   │ - Folders   │    │ - Folders   │    │ - Folders   │        │
│   │ - Members   │    │ - Members   │    │ - Members   │        │
│   │ - Settings  │    │ - Settings  │    │ - Settings  │        │
│   └─────────────┘    └─────────────┘    └─────────────┘        │
│                                                                  │
│   隔离策略:                                                      │
│   - Row-level Security (RLS)                                    │
│   - Project ID 过滤                                             │
│   - 权限中间件                                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 权限系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      权限控制层 (RBAC)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   角色层次:                                                       │
│   ┌─────────────────────────────────────────────────────┐        │
│   │  Owner (所有者)                                     │        │
│   │   └── 全部权限                                      │        │
│   │       ├─ 删除项目                                   │        │
│   │       ├─ 管理成员                                   │        │
│   │       ├─ 修改设置                                   │        │
│   │       └─ 所有 Admin 权限                            │        │
│   │                                                   │        │
│   │  Admin (管理员)                                   │        │
│   │   └── 管理权限                                      │        │
│   │       ├─ 邀请成员                                   │        │
│   │       ├─ 分配角色                                   │        │
│   │       ├─ 管理模板                                   │        │
│   │       └─ 所有 Editor 权限                           │        │
│   │                                                   │        │
│   │  Editor (编辑者)                                  │        │
│   │   └── 编辑权限                                      │        │
│   │       ├─ 创建/编辑文档                              │        │
│   │       ├─ 上传文件                                   │        │
│   │       ├─ 添加标签                                   │        │
│   │       └─ 所有 Viewer 权限                           │        │
│   │                                                   │        │
│   │  Viewer (查看者)                                  │        │
│   │   └── 只读权限                                      │        │
│   │       ├─ 查看文档                                   │        │
│   │       ├─ 搜索内容                                   │        │
│   │       └─ 添加评论                                   │        │
│   └─────────────────────────────────────────────────────┘        │
│                                                                  │
│   权限检查流程:                                                   │
│   Request ──▶ Auth Middleware ──▶ Role Check ──▶ Permission     │
│                                     (JWT)        (Policy)        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 项目模板引擎

```typescript
// services/project/TemplateEngine.ts
export class TemplateEngine {
  constructor(
    private folderService: FolderService,
    private documentService: DocumentService,
    private tagService: TagService
  ) {}

  async applyTemplate(
    projectId: string,
    template: ProjectTemplate
  ): Promise<void> {
    // 1. 创建文件夹结构
    const folderMap = await this.createFolderStructure(
      projectId,
      template.structure
    );
    
    // 2. 创建默认标签
    const tags = await this.createDefaultTags(
      projectId,
      template.defaultTags
    );
    
    // 3. 创建 AI Prompt 模板
    await this.createPromptTemplates(
      projectId,
      template.aiPrompts
    );
    
    // 4. 注册工作流模板
    await this.createWorkflowTemplates(
      projectId,
      template.workflows
    );
  }
  
  private async createFolderStructure(
    projectId: string,
    structure: FolderStructure,
    parentId?: string
  ): Promise<Map<string, string>> {
    const folderMap = new Map<string, string>();
    
    const createRecursive = async (
      item: FolderStructure,
      parent?: string
    ): Promise<void> => {
      const folder = await this.folderService.create({
        projectId,
        name: item.name,
        parentId: parent,
        defaultTags: item.defaultTags
      });
      
      folderMap.set(item.name, folder.id);
      
      if (item.children) {
        for (const child of item.children) {
          await createRecursive(child, folder.id);
        }
      }
    };
    
    await createRecursive(structure, parentId);
    return folderMap;
  }
}
```

---

## 🤝 三、实时协作架构

### 3.1 CRDT 协作架构 (Yjs)

```
┌─────────────────────────────────────────────────────────────────┐
│                    协作编辑架构 (Yjs + WebSocket)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Client A          Server           Client B          Client C  │
│  ┌──────┐         ┌──────┐         ┌──────┐         ┌──────┐   │
│  │ Y.Doc│◄───────►│Y-WS  │◄───────►│ Y.Doc│         │ Y.Doc│   │
│  │      │  sync   │Server│  sync   │      │         │      │   │
│  └──┬───┘         └──┬───┘         └──┬───┘         └──┬───┘   │
│     │                │                │                │        │
│     ▼                ▼                ▼                ▼        │
│  ┌──────┐         ┌──────┐         ┌──────┐         ┌──────┐   │
│  │Aware-│         │Aware-│         │Aware-│         │Aware-│   │
│  │ness  │◄───────►│ness  │◄───────►│ness  │         │ness  │   │
│  │      │  update │State │  update │      │         │      │   │
│  └──────┘         └──────┘         └──────┘         └──────┘   │
│                                                                  │
│  Awareness 状态:                                                 │
│  - 光标位置                                                      │
│  - 选中文本                                                      │
│  - 用户信息                                                      │
│  - 在线状态                                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 协作数据流

```
User A 编辑文本:
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────┐
│  Input  │────▶│   Yjs Doc   │────▶│  WebSocket  │────▶│ Server  │
│  Event  │     │   Update    │     │   Publish   │     │         │
└─────────┘     └─────────────┘     └─────────────┘     └────┬────┘
                                                               │
                                    ┌──────────────────────────┼───┐
                                    │                          │   │
                                    ▼                          ▼   ▼
                              ┌─────────┐                 ┌─────────┐
                              │ Client B│                 │ Client C│
                              │  Apply  │                 │  Apply  │
                              │  Update │                 │  Update │
                              └─────────┘                 └─────────┘
```

### 3.3 评论系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      评论系统架构                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │                   CommentService                         │     │
│  │                                                          │     │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │     │
│  │  │ Threading   │  │ Anchoring   │  │ Notification    │  │     │
│  │  │ Engine      │  │ Engine      │  │ Service         │  │     │
│  │  │             │  │             │  │                 │  │     │
│  │  │ - Tree      │  │ - Position  │  │ - Mention       │  │     │
│  │  │ - Reply     │  │ - Selection │  │ - Email         │  │     │
│  │  │ - Resolve   │  │ - Range     │  │ - Push          │  │     │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │     │
│  └─────────────────────────────────────────────────────────┘     │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │                   存储层                                  │     │
│  │                                                          │     │
│  │  ┌───────────┐  ┌───────────┐  ┌─────────────────────┐  │     │
│  │  │ comments  │  │reactions  │  │comment_mentions     │  │     │
│  │  │           │  │           │  │                     │  │     │
│  │  │- content  │  │- emoji    │  │- user_id            │  │     │
│  │  │- position │  │- count    │  │- comment_id         │  │     │
│  │  │- parent_id│  │           │  │- read_status        │  │     │
│  │  └───────────┘  └───────────┘  └─────────────────────┘  │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔌 四、插件系统架构

### 4.1 插件架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                      插件系统架构                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │                    PluginManager                         │     │
│  │                                                          │     │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │     │
│  │  │ Lifecycle   │  │ Hook        │  │ Security        │  │     │
│  │  │ Manager     │  │ Registry    │  │ Manager         │  │     │
│  │  │             │  │             │  │                 │  │     │
│  │  │ - Install   │  │ - Register  │  │ - Permission    │  │     │
│  │  │ - Enable    │  │ - Execute   │  │ - Sandbox       │  │     │
│  │  │ - Disable   │  │ - Priority  │  │ - Validation    │  │     │
│  │  │ - Uninstall │  │             │  │                 │  │     │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │     │
│  └─────────────────────────────────────────────────────────┘     │
│                              │                                   │
│           ┌──────────────────┼──────────────────┐                │
│           │                  │                  │                │
│           ▼                  ▼                  ▼                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐      │
│  │  Core API   │    │  Plugin A   │    │  Plugin B       │      │
│  │             │    │             │    │                 │      │
│  │ - Database  │    │ ┌─────────┐ │    │ ┌─────────────┐ │      │
│  │ - Storage   │    │ │Sandbox  │ │    │ │   Sandbox   │ │      │
│  │ - AI/ML     │    │ │(iframe) │ │    │ │  (iframe)   │ │      │
│  │ - Events    │    │ └────┬────┘ │    │ └──────┬──────┘ │      │
│  │             │    │      │      │    │        │        │      │
│  │             │    │ ┌────┴────┐ │    │ ┌──────┴──────┐ │      │
│  │             │    │ │ Hooks   │ │    │ │    Hooks    │ │      │
│  │             │    │ │ - UI    │ │    │ │  - Storage  │ │      │
│  │             │    │ │ - API   │ │    │ │  - API      │ │      │
│  │             │    │ │ - Event │ │    │ │  - Event    │ │      │
│  │             │    │ └─────────┘ │    │ └─────────────┘ │      │
│  └─────────────┘    └─────────────┘    └─────────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 插件沙箱架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      插件沙箱 (iframe)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  Parent Window (天一阁主应用)                            │     │
│  │                                                          │     │
│  │  ┌─────────────────────────────────────────────────┐     │     │
│  │  │           PluginManager (Host API)               │     │     │
│  │  │  - exposePluginAPI()                            │     │     │
│  │  │  - validateMessage()                            │     │     │
│  │  │  - handleRequest()                              │     │     │
│  │  └─────────────────────────────────────────────────┘     │     │
│  │                      │                                   │     │
│  │                      │ postMessage (单向)                │     │
│  │                      ▼                                   │     │
│  └─────────────────────────────────────────────────────────┘     │
│                      │                                           │
│                      │ 沙箱边界 (iframe sandbox)                 │
│                      │                                           │
│                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  Child Window (插件沙箱)                                 │     │
│  │  sandbox="allow-scripts allow-same-origin"              │     │
│  │                                                          │     │
│  │  ┌─────────────────────────────────────────────────┐     │     │
│  │  │           Plugin Runtime (isolated)              │     │     │
│  │  │  - plugin.init()                                │     │     │
│  │  │  - plugin.hooks                                 │     │     │
│  │  │  - window.parent.postMessage()                  │     │     │
│  │  └─────────────────────────────────────────────────┘     │     │
│  │                                                          │     │
│  │  限制:                                                   │     │
│  │  - 无法访问主应用 DOM                                    │     │
│  │  - 无法访问 localStorage/cookies                         │     │
│  │  - 只能使用暴露的 API                                    │     │
│  │                                                          │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 插件 Hook 系统

```typescript
// plugin-system/HookSystem.ts
export class HookSystem {
  private hooks: Map<string, HookEntry[]> = new Map();

  // 注册 Hook
  register(hookName: string, handler: HookHandler, priority: number = 0): void {
    if (!this.hooks.has(hookName)) {
      this.hooks.set(hookName, []);
    }
    
    const entries = this.hooks.get(hookName)!;
    entries.push({ handler, priority });
    
    // 按优先级排序
    entries.sort((a, b) => b.priority - a.priority);
  }

  // 执行 Hook
  async execute(hookName: string, context: HookContext): Promise<HookResult> {
    const entries = this.hooks.get(hookName) || [];
    
    for (const entry of entries) {
      try {
        const result = await entry.handler(context);
        
        // 如果返回 false，停止后续执行
        if (result === false) {
          return { continue: false, context };
        }
        
        // 如果返回对象，更新上下文
        if (result && typeof result === 'object') {
          context = { ...context, ...result };
        }
      } catch (error) {
        console.error(`Hook ${hookName} failed:`, error);
      }
    }
    
    return { continue: true, context };
  }
}

// 预定义 Hooks
export enum CoreHooks {
  // UI Hooks
  UI_MOUNT = 'ui:mount',
  UI_UNMOUNT = 'ui:unmount',
  
  // Document Hooks
  DOCUMENT_CREATE = 'document:create',
  DOCUMENT_UPDATE = 'document:update',
  DOCUMENT_DELETE = 'document:delete',
  
  // Search Hooks
  SEARCH_QUERY = 'search:query',
  SEARCH_RESULT = 'search:result',
  
  // AI Hooks
  AI_PROMPT = 'ai:prompt',
  AI_RESPONSE = 'ai:response',
  
  // Sync Hooks
  SYNC_START = 'sync:start',
  SYNC_COMPLETE = 'sync:complete'
}
```

---

## 🗄️ 五、数据模型

### 5.1 实体关系图

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    users    │       │   projects  │       │   plugins   │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id          │◄──────┤ owner_id    │       │ id          │
│ email       │       │ name        │       │ name        │
│ name        │       │ description │       │ version     │
│ avatar      │       │ settings    │       │ enabled     │
└─────────────┘       └──────┬──────┘       └─────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
       ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
       │project_members│ │   folders   │ │ sync_mappings│
       ├─────────────┤ ├─────────────┤ ├─────────────┤
       │ project_id  │ │ project_id  │ │ local_doc_id│
       │ user_id     │ │ parent_id   │ │ remote_id   │
       │ role        │ │ name        │ │ status      │
       └─────────────┘ └─────────────┘ └─────────────┘

┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  comments   │       │activity_logs│       │sync_conflicts│
├─────────────┤       ├─────────────┤       ├─────────────┤
│ document_id │       │ project_id  │       │ document_id │
│ author_id   │       │ user_id     │       │ local_ver   │
│ content     │       │ action      │       │ remote_ver  │
│ position    │       │ details     │       │ status      │
│ parent_id   │       │ timestamp   │       └─────────────┘
└─────────────┘       └─────────────┘
```

---

## 🔄 六、事件驱动架构

### 6.1 事件总线

```
┌─────────────────────────────────────────────────────────────────┐
│                      事件总线 (Event Bus)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │                    EventBus                              │     │
│  │                                                          │     │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │     │
│  │  │ Event       │  │ Subscriber  │  │ Middleware      │  │     │
│  │  │ Store       │  │ Registry    │  │ Chain           │  │     │
│  │  │             │  │             │  │                 │  │     │
│  │  │ - Persist   │  │ - Add       │  │ - Validation    │  │     │
│  │  │ - Replay    │  │ - Remove    │  │ - Transform     │  │     │
│  │  │ - Query     │  │ - Notify    │  │ - Audit         │  │     │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │     │
│  └─────────────────────────────────────────────────────────┘     │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │                   事件类型                               │     │
│  │                                                          │     │
│  │  Domain Events              │  Integration Events        │     │
│  │  ─────────────────          │  ──────────────────        │     │
│  │  - DocumentCreated          │  - SyncStarted             │     │
│  │  - DocumentUpdated          │  - SyncCompleted           │     │
│  │  - CommentAdded             │  - PluginInstalled         │     │
│  │  - MemberJoined             │  - WebhookTriggered        │     │
│  │                                                          │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 七、部署架构

### 7.1 服务拓扑

```
┌─────────────────────────────────────────────────────────────────┐
│                        生产环境部署                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐                                                │
│  │   CDN       │ 静态资源 (前端构建产物)                         │
│  │  (CloudFlare)│                                               │
│  └──────┬──────┘                                                │
│         │                                                        │
│  ┌──────┴──────┐                                                │
│  │  Nginx LB   │ 负载均衡 + SSL 终止                             │
│  │  (2 nodes)  │                                                │
│  └──────┬──────┘                                                │
│         │                                                        │
│    ┌────┴────┬────────┬────────┐                                 │
│    │         │        │        │                                 │
│    ▼         ▼        ▼        ▼                                 │
│  ┌────┐   ┌────┐   ┌────┐   ┌────┐                              │
│  │API │   │API │   │API │   │API │   FastAPI 应用 (4 nodes)     │
│  │ #1 │   │ #2 │   │ #3 │   │ #4 │                              │
│  └────┘   └────┘   └────┘   └────┘                              │
│    │         │        │        │                                 │
│    └─────────┴────┬───┴────────┘                                 │
│                   │                                              │
│         ┌────────┴────────┐                                      │
│         │                 │                                      │
│         ▼                 ▼                                      │
│  ┌─────────────┐   ┌─────────────┐                               │
│  │  PostgreSQL │   │    Redis    │                               │
│  │  (Primary)  │   │   Cluster   │                               │
│  │  + Replica  │   │             │                               │
│  └─────────────┘   └─────────────┘                               │
│         │                 │                                      │
│         ▼                 ▼                                      │
│  ┌─────────────┐   ┌─────────────┐                               │
│  │  Qdrant     │   │  Celery     │                               │
│  │  (Vectors)  │   │  Workers    │                               │
│  │             │   │             │                               │
│  └─────────────┘   └─────────────┘                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📈 八、性能优化

### 8.1 缓存策略

```
┌─────────────────────────────────────────────────────────────────┐
│                      多级缓存架构                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  L1: 客户端缓存                                                  │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  - React Query Cache                                     │     │
│  │  - Service Worker (PWA)                                  │     │
│  │  - LocalStorage (用户设置)                               │     │
│  └─────────────────────────────────────────────────────────┘     │
│                              │                                   │
│                              ▼                                   │
│  L2: CDN 缓存                                                    │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  - 静态资源 (JS/CSS/图片)                                │     │
│  │  - 文档预览图                                            │     │
│  │  - 公共 API 响应 (配置/模板)                             │     │
│  └─────────────────────────────────────────────────────────┘     │
│                              │                                   │
│                              ▼                                   │
│  L3: 应用缓存                                                    │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  - Redis (Session/API 响应)                              │     │
│  │  - 向量缓存 (Qdrant)                                     │     │
│  │  - 数据库查询缓存                                        │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔒 九、安全架构

### 9.1 安全层

```
┌─────────────────────────────────────────────────────────────────┐
│                      安全架构                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: 传输安全                                               │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  - TLS 1.3                                              │     │
│  │  - Certificate Pinning                                  │     │
│  │  - HSTS                                                 │     │
│  └─────────────────────────────────────────────────────────┘     │
│                              │                                   │
│                              ▼                                   │
│  Layer 2: 认证授权                                               │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  - JWT (RS256)                                          │     │
│  │  - OAuth 2.0 / OIDC                                     │     │
│  │  - RBAC 权限模型                                        │     │
│  └─────────────────────────────────────────────────────────┘     │
│                              │                                   │
│                              ▼                                   │
│  Layer 3: 输入验证                                               │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  - Pydantic Schema Validation                           │     │
│  │  - SQL Injection Prevention                             │     │
│  │  - XSS Prevention                                       │     │
│  │  - CSRF Protection                                      │     │
│  └─────────────────────────────────────────────────────────┘     │
│                              │                                   │
│                              ▼                                   │
│  Layer 4: 数据安全                                               │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  - 敏感数据加密 (AES-256)                               │     │
│  │  - 字段级加密                                           │     │
│  │  - 密钥管理 (KMS)                                       │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ 十、下一步架构规划 (v3.0.13)

- [ ] **移动端架构**: React Native / PWA
- [ ] **AI 服务架构**: 模型路由 + A/B 测试
- [ ] **知识图谱架构**: 图数据库 (Neo4j) 集成
- [ ] **事件溯源**: CQRS + Event Sourcing
- [ ] **多区域部署**: 异地多活架构

---

**更新时间**: 2026-03-29 23:00
