# 天一阁 PRD v3.0.12

**版本**: v3.0.12
**日期**: 2026-03-29
**阶段**: LibIndex One 同步服务 + 项目级管理 + 协作功能 + 插件系统

---

## 📋 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0.12 | 2026-03-29 | LibIndex One 同步服务 + 项目级管理 + 协作功能 + 插件系统 |
| v3.0.11 | 2026-03-28 | 用户认证界面 + 向量搜索集成 + 高级搜索 + 批量操作 + 导入导出 |
| v3.0.10 | 2026-03-25 | WebSocket 前端实现 + Knowledge QA Agent 实现 + 断点续传实现 |

---

## 🎯 本次迭代目标

### 核心交付物
- [ ] **LibIndex One 同步服务**: 与 LibIndex One 系统的双向数据同步
- [ ] **项目级管理**: 多项目支持、项目模板、项目权限
- [ ] **协作功能**: 实时协作编辑、评论系统、活动日志
- [ ] **插件系统**: 插件架构、API 扩展、第三方集成

---

## ✅ 一、LibIndex One 同步服务

### 1.1 同步架构设计

```typescript
// services/sync/LibIndexSyncService.ts
export interface LibIndexSyncConfig {
  endpoint: string;
  apiKey: string;
  syncInterval: number; // 分钟
  syncDirection: 'bidirectional' | 'upload' | 'download';
  conflictResolution: 'local' | 'remote' | 'timestamp' | 'manual';
}

export interface SyncJob {
  id: string;
  type: 'full' | 'incremental' | 'metadata';
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  startedAt: Date;
  completedAt?: Date;
  error?: string;
}

export class LibIndexSyncService {
  constructor(
    private config: LibIndexSyncConfig,
    private documentService: DocumentService,
    private vectorStore: VectorStore
  ) {}

  // 启动同步任务
  async startSync(type: SyncJob['type'] = 'incremental'): Promise<SyncJob> {
    // 实现同步逻辑
  }

  // 获取同步状态
  async getSyncStatus(jobId: string): Promise<SyncJob> {
    // 实现状态查询
  }

  // 解决冲突
  async resolveConflict(
    documentId: string,
    resolution: 'local' | 'remote' | 'merge'
  ): Promise<void> {
    // 实现冲突解决
  }
}
```

### 1.2 同步数据模型

```typescript
// models/sync.ts
export interface SyncMapping {
  id: string;
  localDocumentId: string;
  remoteDocumentId: string;
  lastSyncAt: Date;
  localVersion: number;
  remoteVersion: number;
  syncStatus: 'synced' | 'conflict' | 'pending' | 'error';
}

export interface SyncConflict {
  id: string;
  documentId: string;
  localVersion: DocumentVersion;
  remoteVersion: DocumentVersion;
  detectedAt: Date;
  resolution?: 'local' | 'remote' | 'merge';
}

export interface DocumentVersion {
  content: string;
  metadata: DocumentMetadata;
  updatedAt: Date;
  updatedBy: string;
}
```

### 1.3 同步策略

| 策略 | 描述 | 适用场景 |
|------|------|----------|
| 全量同步 | 同步所有文档 | 首次连接或数据恢复 |
| 增量同步 | 仅同步变更文档 | 定时同步 |
| 元数据同步 | 仅同步索引和标签 | 快速更新 |

---

## ✅ 二、项目级管理

### 2.1 项目数据模型

```typescript
// models/project.ts
export interface Project {
  id: string;
  name: string;
  description: string;
  ownerId: string;
  members: ProjectMember[];
  folders: Folder[];
  settings: ProjectSettings;
  template?: ProjectTemplate;
  createdAt: Date;
  updatedAt: Date;
}

export interface ProjectMember {
  userId: string;
  role: 'owner' | 'admin' | 'editor' | 'viewer';
  permissions: Permission[];
  joinedAt: Date;
}

export interface ProjectSettings {
  visibility: 'private' | 'team' | 'public';
  allowGuestAccess: boolean;
  defaultDocumentPermissions: Permission[];
  storageQuota: number; // MB
  aiFeatures: {
    enabled: boolean;
    allowedModels: string[];
    tokenLimit: number;
  };
}
```

### 2.2 项目模板

```typescript
// models/template.ts
export interface ProjectTemplate {
  id: string;
  name: string;
  description: string;
  category: 'research' | 'business' | 'education' | 'personal' | 'custom';
  structure: FolderStructure;
  defaultTags: string[];
  aiPrompts: PromptTemplate[];
  workflows: WorkflowTemplate[];
}

export interface FolderStructure {
  name: string;
  children?: FolderStructure[];
  defaultTags?: string[];
}

// 内置模板示例
export const RESEARCH_TEMPLATE: ProjectTemplate = {
  id: 'template-research',
  name: '学术研究',
  category: 'research',
  structure: {
    name: '研究项目',
    children: [
      { name: '01-文献综述', defaultTags: ['文献', '综述'] },
      { name: '02-实验数据', defaultTags: ['数据', '实验'] },
      { name: '03-分析报告', defaultTags: ['分析', '报告'] },
      { name: '04-论文草稿', defaultTags: ['论文', '草稿'] },
      { name: '05-参考文献', defaultTags: ['引用', '文献'] }
    ]
  },
  defaultTags: ['研究', '学术'],
  aiPrompts: [
    {
      name: '文献总结',
      template: '请总结以下文献的核心观点、研究方法和结论：\n\n{content}'
    },
    {
      name: '研究方法分析',
      template: '分析以下研究的方法论：\n\n{content}'
    }
  ],
  workflows: [
    {
      name: '文献处理流程',
      steps: ['upload', 'parse', 'summarize', 'tag', 'index']
    }
  ]
};
```

### 2.3 项目切换组件

```typescript
// components/ProjectSwitcher.tsx
import { Select, Dropdown, Button, Menu } from 'antd';
import { PlusOutlined, SettingOutlined } from '@ant-design/icons';

export function ProjectSwitcher() {
  const { currentProject, projects, switchProject, createProject } = useProjectStore();

  return (
    <div className="project-switcher">
      <Select
        value={currentProject?.id}
        onChange={switchProject}
        dropdownRender={(menu) => (
          <>
            {menu}
            <Divider style={{ margin: '8px 0' }} />
            <Button
              type="text"
              icon={<PlusOutlined />}
              onClick={() => createProject()}
            >
              新建项目
            </Button>
          </>
        )}
      >
        {projects.map(project => (
          <Select.Option key={project.id} value={project.id}>
            <Space>
              <ProjectIcon type={project.template?.category} />
              <span>{project.name}</span>
              {project.ownerId === currentUser.id && (
                <Tag color="blue">所有者</Tag>
              )}
            </Space>
          </Select.Option>
        ))}
      </Select>

      <Dropdown
        overlay={(
          <Menu>
            <Menu.Item icon={<SettingOutlined />}>
              项目设置
            </Menu.Item>
            <Menu.Item icon={<TeamOutlined />}>
              成员管理
            </Menu.Item>
            <Menu.Divider />
            <Menu.Item icon={<ExportOutlined />}>
              导出项目
            </Menu.Item>
          </Menu>
        )}
      >
        <Button icon={<MoreOutlined />} />
      </Dropdown>
    </div>
  );
}
```

---

## ✅ 三、协作功能

### 3.1 实时协作编辑

```typescript
// services/collaboration/CollaborationService.ts
export interface CollaborationSession {
  documentId: string;
  participants: Participant[];
  cursors: Map<string, CursorPosition>;
  selections: Map<string, TextSelection>;
  operations: Operation[];
}

export interface Participant {
  userId: string;
  name: string;
  avatar: string;
  color: string;
  lastActivity: Date;
}

export interface Operation {
  id: string;
  type: 'insert' | 'delete' | 'retain';
  position: number;
  content?: string;
  length?: number;
  userId: string;
  timestamp: Date;
}

export class CollaborationService {
  private ws: WebSocket;
  private document: Y.Doc;
  private awareness: awarenessProtocol.Awareness;

  constructor(documentId: string) {
    // 使用 Yjs 实现 CRDT
    this.document = new Y.Doc();
    this.awareness = new awarenessProtocol.Awareness(this.document);
    this.setupWebSocket(documentId);
  }

  // 加入协作会话
  async join(user: User): Promise<void> {
    this.awareness.setLocalStateField('user', {
      id: user.id,
      name: user.name,
      color: this.generateUserColor(user.id)
    });
  }

  // 应用本地操作
  applyOperation(operation: Operation): void {
    const text = this.document.getText('content');
    switch (operation.type) {
      case 'insert':
        text.insert(operation.position, operation.content!);
        break;
      case 'delete':
        text.delete(operation.position, operation.length!);
        break;
    }
  }

  // 获取光标位置
  getCursorPosition(userId: string): CursorPosition | undefined {
    return this.awareness.getStates().get(userId)?.cursor;
  }
}
```

### 3.2 评论系统

```typescript
// models/comment.ts
export interface Comment {
  id: string;
  documentId: string;
  content: string;
  author: User;
  position?: TextPosition; // 文档中的位置
  selection?: TextSelection; // 选中的文本
  parentId?: string; // 回复的评论
  replies: Comment[];
  reactions: Reaction[];
  resolved: boolean;
  resolvedBy?: User;
  resolvedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface TextPosition {
  paragraph: number;
  offset: number;
}

export interface TextSelection {
  start: TextPosition;
  end: TextPosition;
  text: string;
}

export interface Reaction {
  emoji: string;
  users: string[];
}

// 评论组件
export function CommentSystem({ documentId }: { documentId: string }) {
  const { comments, addComment, resolveComment } = useComments(documentId);

  return (
    <div className="comment-system">
      <CommentList
        comments={comments.filter(c => !c.parentId)}
        onReply={(parentId, content) => addComment({ parentId, content })}
        onResolve={(id) => resolveComment(id)}
      />
      <CommentInput
        onSubmit={(content, selection) => 
          addComment({ content, selection })
        }
      />
    </div>
  );
}
```

### 3.3 活动日志

```typescript
// models/activity.ts
export interface ActivityLog {
  id: string;
  projectId: string;
  documentId?: string;
  userId: string;
  action: ActivityAction;
  details: ActivityDetails;
  ipAddress: string;
  userAgent: string;
  timestamp: Date;
}

type ActivityAction = 
  | 'document.created'
  | 'document.updated'
  | 'document.deleted'
  | 'document.shared'
  | 'comment.added'
  | 'comment.resolved'
  | 'member.invited'
  | 'member.joined'
  | 'member.left'
  | 'member.role_changed';

interface ActivityDetails {
  documentName?: string;
  targetUserId?: string;
  oldValue?: any;
  newValue?: any;
  metadata?: Record<string, any>;
}

// 活动日志组件
export function ActivityFeed({ projectId }: { projectId: string }) {
  const { activities, hasMore, loadMore } = useActivities(projectId);

  return (
    <div className="activity-feed">
      <Timeline>
        {activities.map(activity => (
          <Timeline.Item
            key={activity.id}
            dot={<ActivityIcon action={activity.action} />}
          >
            <ActivityItem activity={activity} />
          </Timeline.Item>
        ))}
      </Timeline>
      {hasMore && (
        <Button onClick={loadMore} loading={isLoading}>
          加载更多
        </Button>
      )}
    </div>
  );
}
```

---

## ✅ 四、插件系统

### 4.1 插件架构

```typescript
// plugin-system/types.ts
export interface Plugin {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  entry: string;
  permissions: PluginPermission[];
  hooks: PluginHook[];
  components: PluginComponent[];
  settings?: PluginSetting[];
}

export interface PluginPermission {
  type: 'api' | 'storage' | 'ui' | 'event';
  resource: string;
  actions: string[];
}

export interface PluginHook {
  name: string;
  handler: (...args: any[]) => any;
}

export interface PluginComponent {
  name: string;
  type: 'page' | 'widget' | 'modal' | 'toolbar';
  component: React.ComponentType;
}

export interface PluginSetting {
  key: string;
  type: 'string' | 'number' | 'boolean' | 'select' | 'json';
  label: string;
  defaultValue: any;
  options?: { label: string; value: any }[];
}
```

### 4.2 插件管理器

```typescript
// plugin-system/PluginManager.ts
export class PluginManager {
  private plugins: Map<string, Plugin> = new Map();
  private hooks: Map<string, Function[]> = new Map();
  private sandbox: PluginSandbox;

  constructor() {
    this.sandbox = new PluginSandbox();
  }

  // 安装插件
  async installPlugin(pluginPackage: PluginPackage): Promise<Plugin> {
    // 验证插件
    await this.validatePlugin(pluginPackage);
    
    // 创建沙箱环境
    const sandbox = await this.sandbox.create(pluginPackage);
    
    // 加载插件
    const plugin = await sandbox.load();
    
    // 注册钩子
    this.registerHooks(plugin);
    
    // 保存插件
    this.plugins.set(plugin.id, plugin);
    
    return plugin;
  }

  // 卸载插件
  async uninstallPlugin(pluginId: string): Promise<void> {
    const plugin = this.plugins.get(pluginId);
    if (!plugin) throw new Error('Plugin not found');
    
    // 执行卸载钩子
    await this.executeHook('plugin:uninstall', plugin);
    
    // 清理资源
    await this.sandbox.destroy(pluginId);
    this.plugins.delete(pluginId);
  }

  // 执行钩子
  async executeHook(hookName: string, ...args: any[]): Promise<any[]> {
    const handlers = this.hooks.get(hookName) || [];
    const results = await Promise.all(
      handlers.map(handler => handler(...args))
    );
    return results;
  }

  // 注册钩子
  private registerHooks(plugin: Plugin): void {
    plugin.hooks.forEach(hook => {
      if (!this.hooks.has(hook.name)) {
        this.hooks.set(hook.name, []);
      }
      this.hooks.get(hook.name)!.push(hook.handler);
    });
  }
}
```

### 4.3 插件沙箱

```typescript
// plugin-system/PluginSandbox.ts
export class PluginSandbox {
  private iframes: Map<string, HTMLIFrameElement> = new Map();

  async create(pluginPackage: PluginPackage): Promise<PluginSandbox> {
    const iframe = document.createElement('iframe');
    iframe.sandbox = 'allow-scripts allow-same-origin';
    iframe.style.display = 'none';
    
    // 加载插件代码
    const blob = new Blob([pluginPackage.code], { type: 'text/javascript' });
    iframe.src = URL.createObjectURL(blob);
    
    document.body.appendChild(iframe);
    this.iframes.set(pluginPackage.id, iframe);
    
    return this;
  }

  async load(): Promise<Plugin> {
    // 通过 postMessage 与沙箱通信
    return new Promise((resolve, reject) => {
      window.addEventListener('message', (event) => {
        if (event.data.type === 'plugin:ready') {
          resolve(event.data.plugin);
        }
      });
    });
  }

  async destroy(pluginId: string): Promise<void> {
    const iframe = this.iframes.get(pluginId);
    if (iframe) {
      iframe.remove();
      this.iframes.delete(pluginId);
    }
  }
}
```

### 4.4 插件市场

```typescript
// components/PluginMarketplace.tsx
export function PluginMarketplace() {
  const { plugins, installed, install, uninstall } = usePluginStore();

  return (
    <div className="plugin-marketplace">
      <Tabs>
        <Tabs.TabPane tab="已安装" key="installed">
          <PluginList
            plugins={installed}
            actions={[
              { key: 'uninstall', label: '卸载', danger: true }
            ]}
            onAction={(plugin, action) => {
              if (action === 'uninstall') uninstall(plugin.id);
            }}
          />
        </Tabs.TabPane>
        <Tabs.TabPane tab="发现" key="discover">
          <PluginList
            plugins={plugins}
            actions={[
              { key: 'install', label: '安装', type: 'primary' }
            ]}
            onAction={(plugin, action) => {
              if (action === 'install') install(plugin);
            }}
          />
        </Tabs.TabPane>
        <Tabs.TabPane tab="开发" key="develop">
          <PluginDeveloperTools />
        </Tabs.TabPane>
      </Tabs>
    </div>
  );
}
```

---

## ✅ 五、API 设计

### 5.1 项目 API

```typescript
// API 端点
POST   /api/v1/projects              // 创建项目
GET    /api/v1/projects              // 获取项目列表
GET    /api/v1/projects/:id          // 获取项目详情
PUT    /api/v1/projects/:id          // 更新项目
DELETE /api/v1/projects/:id          // 删除项目
POST   /api/v1/projects/:id/members  // 添加成员
DELETE /api/v1/projects/:id/members/:userId  // 移除成员
```

### 5.2 同步 API

```typescript
// API 端点
POST   /api/v1/sync/libindex         // 启动 LibIndex 同步
GET    /api/v1/sync/status           // 获取同步状态
POST   /api/v1/sync/resolve         // 解决冲突
GET    /api/v1/sync/conflicts       // 获取冲突列表
```

### 5.3 协作 API

```typescript
// API 端点
WS     /ws/collaboration/:documentId // WebSocket 协作会话
POST   /api/v1/comments             // 添加评论
GET    /api/v1/comments             // 获取评论列表
PUT    /api/v1/comments/:id/resolve // 解决评论
GET    /api/v1/activities           // 获取活动日志
```

### 5.4 插件 API

```typescript
// API 端点
GET    /api/v1/plugins              // 获取插件列表
POST   /api/v1/plugins              // 安装插件
DELETE /api/v1/plugins/:id          // 卸载插件
POST   /api/v1/plugins/:id/enable   // 启用插件
POST   /api/v1/plugins/:id/disable  // 禁用插件
```

---

## ✅ 六、数据库模型

### 6.1 项目表

```sql
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  owner_id UUID REFERENCES users(id),
  settings JSONB DEFAULT '{}',
  template_id VARCHAR(50),
  storage_quota BIGINT DEFAULT 1073741824, -- 1GB
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE project_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  role VARCHAR(20) NOT NULL DEFAULT 'viewer',
  permissions JSONB DEFAULT '[]',
  joined_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(project_id, user_id)
);
```

### 6.2 同步表

```sql
CREATE TABLE sync_mappings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  local_document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  remote_document_id VARCHAR(255) NOT NULL,
  remote_service VARCHAR(50) NOT NULL DEFAULT 'libindex',
  last_sync_at TIMESTAMP,
  local_version INTEGER DEFAULT 0,
  remote_version INTEGER DEFAULT 0,
  sync_status VARCHAR(20) DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE sync_conflicts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  local_version JSONB NOT NULL,
  remote_version JSONB NOT NULL,
  detected_at TIMESTAMP DEFAULT NOW(),
  resolution VARCHAR(20),
  resolved_at TIMESTAMP,
  resolved_by UUID REFERENCES users(id)
);
```

### 6.3 评论表

```sql
CREATE TABLE comments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  author_id UUID REFERENCES users(id),
  position JSONB,
  selection JSONB,
  parent_id UUID REFERENCES comments(id) ON DELETE CASCADE,
  resolved BOOLEAN DEFAULT FALSE,
  resolved_by UUID REFERENCES users(id),
  resolved_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE comment_reactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  comment_id UUID REFERENCES comments(id) ON DELETE CASCADE,
  emoji VARCHAR(10) NOT NULL,
  user_id UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(comment_id, emoji, user_id)
);
```

### 6.4 活动日志表

```sql
CREATE TABLE activity_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
  user_id UUID REFERENCES users(id),
  action VARCHAR(50) NOT NULL,
  details JSONB DEFAULT '{}',
  ip_address INET,
  user_agent TEXT,
  timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_activity_logs_project ON activity_logs(project_id, timestamp DESC);
CREATE INDEX idx_activity_logs_user ON activity_logs(user_id, timestamp DESC);
```

### 6.5 插件表

```sql
CREATE TABLE plugins (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  version VARCHAR(50) NOT NULL,
  description TEXT,
  author VARCHAR(255),
  entry VARCHAR(500) NOT NULL,
  permissions JSONB DEFAULT '[]',
  enabled BOOLEAN DEFAULT FALSE,
  settings JSONB DEFAULT '{}',
  installed_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE plugin_hooks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plugin_id UUID REFERENCES plugins(id) ON DELETE CASCADE,
  hook_name VARCHAR(100) NOT NULL,
  handler TEXT NOT NULL,
  priority INTEGER DEFAULT 0
);
```

---

## ✅ 七、下一步计划 (v3.0.13)

- [ ] 移动端适配
- [ ] AI 辅助写作
- [ ] 知识图谱可视化
- [ ] 高级权限管理
- [ ] 数据备份与恢复

---

**更新时间**: 2026-03-29 23:00
