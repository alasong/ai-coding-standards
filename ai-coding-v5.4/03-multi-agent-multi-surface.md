# AI Coding 规范 v5.4：多 Agent 与多平台

> 版本：v5.4 | 2026-04-17
> 定位：Sub-Agents、Agent SDK、多平台协同的实践指南
> 前置：必须先阅读并理解 [01-core-specification.md](01-core-specification.md)

---

## 第 1 章：Sub-Agents

### 1.1 什么是 Sub-Agent

Sub-Agent 是主 Agent 启动的独立执行单元，每个 Sub-Agent 有独立的上下文窗口和工具集。

### 1.2 Sub-Agent 类型

| 类型 | 能力 | 适用场景 |
|------|------|---------|
| Explore | 只读（Read、Grep、Glob、Bash） | 代码探索、文件搜索 |
| Plan | 只读 + 规划 | 架构设计、实现规划 |
| general-purpose | 全部工具 | 实现、调试、重构 |

### 1.3 安全约束

- Sub-Agent 继承主 Agent 的权限限制（deny 规则）
- Sub-Agent 不得修改安全敏感文件（secrets/、.env）
- Sub-Agent 的所有输出必须经过主 Agent 验证
- 安全相关变更必须在主 Agent 上下文中审查

---

## 第 2 章：Agent SDK

### 2.1 Agent Teams 模式

```bash
# 创建团队
TeamCreate(team_name="feature-team", description="Implement feature set")

# 创建任务
TaskCreate(subject="Implement F001", description="Spec at specs/F001.md")

# 设置依赖
TaskUpdate(taskId="2", addBlockedBy=["1"])

# 启动成员
Agent(name="worker-frontend", subagent_type="general-purpose", team_name="feature-team")
Agent(name="worker-backend", subagent_type="general-purpose", team_name="feature-team")
```

### 2.2 通信机制

- Team Lead 通过 SendMessage 向 Worker 分配任务
- Worker 通过 TaskUpdate 更新任务状态
- Worker 完成后自动发送消息给 Team Lead
- Team Lead 通过 TaskList 查看整体进度

---

## 第 3 章：多平台协同

### 3.1 平台支持

| 平台 | 能力 |
|------|------|
| CLI | 完整工具集，会话级运行 |
| Desktop App | 定时任务、Remote Control |
| Cloud | 云端定时任务，关机也可运行 |

### 3.2 通知与监控

- 阻塞事件：通过 Slack/Telegram/webhook 发送告警
- 进度通知：Remote Control 查看仪表板
- 完成报告：自动生成并发送到 Channel

---

## 第 4 章：与配套文档的关系

| 文档 | 关系 |
|------|------|
| 01 核心规范 | 定义了分工原则，本文档定义多 Agent 协调实现 |
| 02 Auto-Coding 实践 | 定义了 Supervisor-Worker 模式，本文档定义具体 Agent 类型 |
| 04 安全与治理 | 定义了 Sub-Agent 安全约束，本文档引用 |
| 05 工具参考 | 定义了 CLI 命令，本文档定义使用模式 |
