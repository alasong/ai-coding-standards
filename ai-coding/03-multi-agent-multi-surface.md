# AI Coding 规范 v5.0：多 Agent 与多平台

> 版本：v5.0 | 2026-04-14
> 定位：多 Agent 架构与全平台协同的实践指南
> 前置：必须先阅读并理解 [01-core-specification.md](01-core-specification.md) 和 [02-auto-coding-practices.md](02-auto-coding-practices.md)
> 关联：与 04-security-governance、05-tool-reference 共同构成 v5.0 完整体系

---

## 目录

- [第 1 章：Sub-Agents 架构](#第-1-章sub-agents-架构)
- [第 2 章：Agent SDK](#第-2-章agent-sdk)
- [第 3 章：Agent Teams 模式](#第-3-章agent-teams-模式)
- [第 4 章：全平台能力地图](#第-4-章全平台能力地图)
- [第 5 章：多平台协同 Auto-Coding](#第-5-章多平台协同-auto-coding)
- [第 6 章：团队自动化](#第-6-章团队自动化)
- [第 7 章：安全与治理](#第-7-章安全与治理)
- [第 8 章：v4 合规注释](#第-8-章v4-合规注释)

---

## 第 1 章：Sub-Agents 架构

### 1.1 什么是 Sub-Agents

Sub-Agent（子代理）是 Claude Code 在单个会话内启动的**独立 AI 上下文窗口**。它具有以下核心特征：

| 特征 | 说明 |
|------|------|
| **独立上下文** | 每个 Sub-Agent 拥有独立的上下文窗口，中间的工具调用和结果不会污染主会话 |
| **结果摘要化** | 只有 Sub-Agent 的最终消息返回给调用方，保持主会话的上下文清洁 |
| **不可嵌套** | Sub-Agent 不能再次调用 Sub-Agent，防止无限递归和上下文膨胀 |
| **新鲜上下文** | Sub-Agent 每次调用都收到全新的上下文，不继承主会话的历史对话 |
| **自动委派** | Claude 根据 Sub-Agent 的描述自动决定是否委派，无需手动路由逻辑 |

**核心价值**：Sub-Agent 不是简单的"另一个 Claude 实例"，而是一种**上下文隔离机制**。它让主会话保持清洁，同时让专门化的 Agent 在独立的上下文中工作，返回精炼的摘要结果。

### 1.2 Sub-Agent 的三种定义方式

#### 1.2.1 文件定义（推荐：项目级共享）

Sub-Agent 以 Markdown 文件 + YAML frontmatter 的形式存储在作用域特定的目录中：

```
~/.claude/agents/          ← 用户级（所有项目可用）
.claude/agents/            ← 项目级（版本控制，团队共享）
Plugin's agents/ directory ← 插件级（插件自带）
```

**优先级顺序**（名称冲突时高优先级胜出）：

```
Managed settings (组织级)  >  --agents CLI 参数  >  .claude/agents/  >  ~/.claude/agents/  >  Plugin agents/
```

**完整示例：代码审查 Agent**

```markdown
---
name: code-reviewer
description: 代码审查专家，专注于质量、安全和可维护性。在代码变更后主动使用。
tools: Read, Grep, Glob, Bash
model: sonnet
memory: project
permissionMode: acceptEdits
hooks:
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-linter.sh"
---

你是一位高级代码审查专家，确保代码质量、安全性和可维护性。

审查清单：
1. 运行 git diff 查看最近变更
2. 重点关注修改过的文件
3. 检查代码清晰度、错误处理、密钥泄露、输入验证
4. 按优先级组织反馈：Critical（必须修复）→ Warning（应该修复）→ Suggestion（考虑改进）

安全约束：
- 不得修改生产代码，只提供审查意见
- 发现密钥或硬编码凭证时必须标记为 Critical
- 检查 TDD 合规性：测试是否先于实现提交
```

#### 1.2.2 CLI 定义（临时会话级）

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer. Use proactively after code changes.",
    "prompt": "You are a senior code reviewer. Focus on code quality, security, and best practices.",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "sonnet"
  },
  "debugger": {
    "description": "Debugging specialist for errors and test failures.",
    "prompt": "You are an expert debugger. Analyze errors, identify root causes, and provide fixes."
  }
}'
```

#### 1.2.3 SDK 定义（程序化）

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

agents = {
    "code-reviewer": AgentDefinition(
        description="Expert code review specialist.",
        prompt="You are a code review specialist...",
        tools=["Read", "Grep", "Glob"],
        model="sonnet",
    ),
    "test-runner": AgentDefinition(
        description="Runs and analyzes test suites.",
        prompt="You are a test execution specialist...",
        tools=["Bash", "Read", "Grep"],
    ),
}
```

详细 SDK 定义见 [第 2 章](#第-2-章agent-sdk)。

### 1.3 完整的 Frontmatter 字段参考

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `name` | 是 | `string` | 唯一标识符（小写 + 连字符） |
| `description` | 是 | `string` | Claude 何时委派给此 Agent |
| `tools` | 否 | `string` | 工具允许列表（逗号分隔，省略则继承全部） |
| `disallowedTools` | 否 | `string` | 工具禁止列表（逗号分隔） |
| `model` | 否 | `string` | `sonnet`, `opus`, `haiku`, 完整模型 ID, 或 `inherit`（默认继承） |
| `permissionMode` | 否 | `string` | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | 否 | `number` | 停止前的最大交互轮次 |
| `skills` | 否 | `string[]` | 要预加载的技能名称 |
| `mcpServers` | 否 | `array` | MCP 服务器（内联定义或字符串引用） |
| `hooks` | 否 | `object` | 生命周期钩子（仅作用域于此 Sub-Agent） |
| `memory` | 否 | `string` | `user`, `project`, 或 `local` 用于跨会话学习 |
| `background` | 否 | `boolean` | 始终作为后台任务运行（默认 false） |
| `effort` | 否 | `string` | `low`, `medium`, `high`, `max`（覆盖会话级 effort） |
| `isolation` | 否 | `string` | `worktree` 用于 git worktree 隔离 |
| `color` | 否 | `string` | 显示颜色：`red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan` |
| `initialPrompt` | 否 | `string` | 作为主会话 Agent 运行时自动提交的第一个轮次 |

### 1.4 Sub-Agent 的三种调用模式

```
模式 1：自然语言委派（Claude 自主决定）
  用户："Use the test-runner subagent to fix failing tests"
  → Claude 根据 description 决定是否委派

模式 2：@-mention（强制调用）
  用户：@"code-reviewer (agent)" look at the auth changes
  → 保证执行指定的 Sub-Agent

模式 3：会话级 Agent（整个会话变为该 Agent）
  命令：claude --agent code-reviewer
  或 settings.json: { "agent": "code-reviewer" }
  → 整个会话成为该 Agent 角色
```

### 1.5 Sub-Agent 设计指南

#### 职责单一原则

每个 Sub-Agent 应当**只擅长一件事**。设计时遵循以下准则：

| 准则 | 说明 | 反例 |
|------|------|------|
| 描述精确 | description 明确说明何时使用 | "可以做很多事情"的模糊描述 |
| 工具最小化 | 只授予完成任务所需的最少工具 | 给只读 Agent 授予 Edit/Write |
| 模型匹配 | 分析任务用 Haiku，复杂推理用 Opus | 所有任务都用 Sonnet |
| 主动使用 | description 中包含 "Use proactively" | 仅被动等待用户显式调用 |
| 结果精炼 | Agent 输出应是简洁的摘要 | 返回原始工具调用的详细日志 |

#### Sub-Agent 与 v5 核心原则的映射

| v5 原则 | Sub-Agent 中的执行方式 |
|---------|----------------------|
| **P3 TDD 先行** | Sub-Agent 执行 Red→Green→Refactor 时，CI 记录 Red 状态 |
| **P4 人工审查** | Sub-Agent 的结果作为 PR 的一部分，仍需人工审查 |
| **P8 最小批量** | Sub-Agent 一次只实现一个函数/小模块 |
| **P9 Prompt 版本化** | Sub-Agent 的 prompt 在文件中定义，受版本控制 |
| **P10 数据分级** | Sub-Agent 继承主会话的 pre-send 扫描策略 |

### 1.6 常见 Sub-Agent 模式

#### 模式 A：调研 Agent（Read-Only Explore）

```yaml
---
name: researcher
description: 代码库调研专家。快速发现代码结构和模式。只读操作。
tools: Read, Grep, Glob
model: haiku
effort: high
---

你是代码库调研专家。你的目标是快速理解代码结构和关键模式。

调研流程：
1. 使用 Glob 发现相关文件
2. 使用 Grep 搜索关键模式
3. 使用 Read 理解核心逻辑
4. 生成结构化的调研报告

输出格式：
- 模块概览（目录结构、依赖关系）
- 关键发现（值得注意的模式、约定）
- 风险评估（潜在的技术债务、安全问题）
```

**v5 合规要点**：此 Agent 为只读，不违反任何核心原则。调研报告为人工决策提供信息输入。

#### 模式 B：测试 Agent（TDD 执行者）

```yaml
---
name: test-runner
description: 测试执行和分析专家。用于运行测试、分析覆盖率、定位失败原因。
tools: Bash, Read, Grep, Glob
model: sonnet
permissionMode: acceptEdits
---

你是测试执行专家。

执行流程：
1. 运行测试套件并捕获输出
2. 分析失败测试的错误信息
3. 定位根本原因
4. 如果是测试代码本身的问题，直接修复
5. 如果是生产代码问题，报告详细诊断信息

约束：
- 仅修复测试代码中的错误（如断言错误、Mock 配置错误）
- 生产代码的修复建议必须通过报告返回，由其他 Agent 执行
- 记录测试覆盖率数据到 .gate/coverage-report.json
```

**v5 合规要点**：遵循 P3 TDD 先行，测试覆盖率数据作为质量门禁的一部分。

#### 模式 C：代码 Agent（实现者）

```yaml
---
name: implementer
description: 代码实现专家。根据 Spec 和测试生成实现代码。
tools: Read, Edit, Write, Bash, Grep, Glob
model: sonnet
permissionMode: acceptEdits
memory: project
---

你是代码实现专家。

工作流程：
1. 读取 Spec 文件，理解验收标准
2. 读取已有测试，确认测试覆盖范围
3. 使用最小批量原则实现代码
4. 运行测试验证 Green 状态
5. 如果失败，执行 Self-Correction（最多 3 轮）
6. 运行 lint 和类型检查

约束：
- 一次只实现一个函数或小模块
- 超过 50 行的函数或 200 行的文件必须拆分
- 匹配现有代码模式（命名、导入、错误处理）
- 不得留下临时代码、TODO、debugger 语句
- 不得在代码中嵌入密钥或凭证
```

**v5 合规要点**：遵循 P8 最小批量、P3 TDD 先行、P5 密钥不入代码。

#### 模式 D：审查 Agent（AI Reviewer）

```yaml
---
name: ai-reviewer
description: AI 代码审查员。在 PR 创建前执行幻觉检测和安全扫描。
tools: Read, Grep, Glob, Bash
model: opus
---

你是 AI 代码审查专家，专门检测 AI 生成代码的特有问题。

幻觉检测清单：
1. 不存在的 API 或函数调用
2. 虚构的模块路径或导入
3. 错误的参数类型或数量
4. 与项目技术栈不符的代码模式

安全检查：
1. 密钥泄露（硬编码密码、token、API key）
2. SQL 注入风险（字符串拼接 SQL）
3. XSS 风险（未转义的用户输入输出）
4. 路径遍历（未验证的文件路径）

代码质量：
1. 函数长度（超过 50 行需拆分）
2. 圈复杂度（超过 10 需重构）
3. 重复代码（DRY 原则）

输出格式：
- Critical: [必须修复的问题]
- Warning: [应该修复的问题]
- Suggestion: [考虑改进的地方]
- Passed: [无关键问题的确认]
```

**v5 合规要点**：执行 P4 人工审查中的 AI Reviewer 层，检测 AI 特有风险。

### 1.7 Sub-Agent 钩子系统

#### 前置钩子（PreToolUse）

在执行工具前拦截，用于权限校验和参数验证：

```yaml
---
name: db-reader
description: 只读数据库查询专家
tools: Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
---
```

```bash
#!/bin/bash
# validate-readonly-query.sh
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if echo "$COMMAND" | grep -iE '\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b'; then
  echo "Blocked: Write operations not allowed." >&2
  exit 2
fi
exit 0
```

#### 后置钩子（PostToolUse）

在工具执行后触发，用于自动验证和审计日志：

```yaml
---
name: code-reviewer
description: 代码审查专家
hooks:
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-linter.sh"
        - type: command
          command: "./scripts/audit-log.sh"
---
```

#### 项目级钩子（SubagentStart / SubagentStop）

在 settings.json 中定义：

```json
{
  "hooks": {
    "SubagentStart": [
      {
        "matcher": "db-agent",
        "hooks": [
          { "type": "command", "command": "./scripts/setup-db-connection.sh" }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          { "type": "command", "command": "./scripts/cleanup-db-connection.sh" }
        ]
      }
    ]
  }
}
```

### 1.8 持久化记忆

Sub-Agent 可以通过 `memory` 字段跨会话积累知识：

| 范围 | 存储位置 | 适用场景 |
|------|---------|---------|
| `user` | `~/.claude/agent-memory/<name>/` | 跨项目通用知识 |
| `project` | `.claude/agent-memory/<name>/` | 项目特定知识（版本控制） |
| `local` | `.claude/agent-memory-local/<name>/` | 项目特定（不进入 VCS） |

```yaml
---
name: code-reviewer
description: 代码质量审查专家
memory: project
---

你是代码审查专家。在审查过程中，记录你发现的常见模式、约定和重复问题。
这些知识将帮助你在未来的审查中更高效。
```

### 1.9 前台 vs 后台 Sub-Agent

| 类型 | 行为 | 权限传递 | 适用场景 |
|------|------|---------|---------|
| **前台** | 阻塞主会话对话 | 权限请求透传给用户 | 需要用户确认的变更 |
| **后台** | 与主会话并发运行 | 自动拒绝未预先批准的工具 | 长时间运行的只读分析 |

```yaml
---
name: log-analyzer
description: 分析日志文件并在后台运行
background: true
tools: Read, Grep, Glob
---
```

### 1.10 模型解析顺序

Sub-Agent 使用的模型按以下顺序解析：

```
1. CLAUDE_CODE_SUBAGENT_MODEL 环境变量
2. 每次调用的 model 参数
3. Sub-Agent 定义的 model frontmatter
4. 主会话的模型
```

这使得可以在全局、会话、任务三个层级灵活控制模型选择。

### 1.11 限制 Sub-Agent 派生（白名单模式）

通过限制 Agent 可用的子代理类型，可以控制 Agent 的行为范围：

```yaml
---
name: coordinator
description: 协调专家，在 worker 和 researcher 之间委派任务
tools: Agent(worker, researcher), Read, Bash
---
```

只有 `worker` 和 `researcher` 可以被派生。如果完全省略 `Agent`，该 Agent 不能派生任何子代理。

---

## 第 2 章：Agent SDK

### 2.1 Agent SDK 概述

Agent SDK 提供对 Claude Code Agent 能力的**程序化访问**，支持 Python 和 TypeScript 两种语言。它是构建生产级自主编码管道的核心工具。

**安装**：

```bash
# TypeScript
npm install @anthropic-ai/claude-agent-sdk

# Python
pip install claude-agent-sdk
```

**核心架构**：

```
┌─────────────────────────────────────────────────┐
│                自主编码管道                        │
│                                                   │
│  ┌──────────────┐    ┌──────────────────────┐    │
│  │  CI/CD 触发器 │───▶│  Agent SDK 查询      │    │
│  │  (Webhook)   │    │  (query() 函数)       │    │
│  └──────────────┘    └──────────┬───────────┘    │
│                                 │                 │
│                    ┌────────────┼────────────┐    │
│                    ▼            ▼            ▼    │
│              ┌──────────┐ ┌──────────┐ ┌──────┐  │
│              │ Sub-Agent│ │ Sub-Agent│ │ Bash │  │
│              │ (分析)   │ │ (修复)   │ │(测试)│  │
│              └──────────┘ └──────────┘ └──────┘  │
│                                 │                 │
│                                 ▼                 │
│                        ┌──────────────┐          │
│                        │ PR 创建/通知  │          │
│                        └──────────────┘          │
└─────────────────────────────────────────────────┘
```

### 2.2 AgentDefinition 配置

`AgentDefinition` 是 SDK 中定义 Sub-Agent 的核心数据结构：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `description` | `string` | 是 | 何时使用此 Agent |
| `prompt` | `string` | 是 | Agent 的系统提示词 |
| `tools` | `string[]` | 否 | 允许的工具列表（省略则继承全部） |
| `model` | `'sonnet' \| 'opus' \| 'haiku' \| 'inherit'` | 否 | 模型覆盖 |
| `skills` | `string[]` | 否 | 预加载的技能名称 |
| `memory` | `'user' \| 'project' \| 'local'` | 否 | 记忆范围（仅 Python） |
| `mcpServers` | `(string \| object)[]` | 否 | MCP 服务器（按名称或内联配置） |

### 2.3 基础使用模式

#### TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Review the authentication module for security issues",
  options: {
    allowedTools: ["Read", "Grep", "Glob", "Agent"],
    agents: {
      "code-reviewer": {
        description: "Expert code review specialist.",
        prompt: "You are a code review specialist...",
        tools: ["Read", "Grep", "Glob"],
        model: "sonnet"
      }
    }
  }
})) {
  if ("result" in message) console.log(message.result);
}
```

#### Python

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

async def main():
    async for message in query(
        prompt="Review the authentication module for security issues",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Grep", "Glob", "Agent"],
            agents={
                "code-reviewer": AgentDefinition(
                    description="Expert code review specialist.",
                    prompt="You are a code review specialist...",
                    tools=["Read", "Grep", "Glob"],
                    model="sonnet",
                )
            },
        ),
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

### 2.4 工具组合

不同阶段需要的工具组合：

| 阶段 | 工具 | 目的 | v5 合规 |
|------|------|------|---------|
| **分析** | `Read`, `Glob`, `Grep` | 只读代码库理解 | 不违反任何原则 |
| **修改** | `Read`, `Edit`, `Glob` | 分析并修改代码 | 遵循 P8 最小批量 |
| **全自动化** | `Read`, `Edit`, `Bash`, `Glob`, `Grep` | 完整 CI/CD 管道 | 遵循 P3 TDD, P4 审查 |
| **测试** | `Bash`, `Read`, `Grep` | 运行测试并分析 | 遵循 P3 TDD 先行 |
| **Git 操作** | `Bash` (git) | 分支创建、提交、PR | 遵循 P5 密钥不入代码 |

### 2.5 权限策略

SDK 中的权限模式：

| 模式 | 行为 | 适用场景 | 安全级别 |
|------|------|---------|---------|
| `acceptEdits` | 自动批准文件编辑和常见文件系统命令 | 受信任的开发环境 | 中等 |
| `dontAsk` | 拒绝 allowedTools 之外的所有操作 | 锁定的无头 CI Agent | 高 |
| `auto` (仅 TS) | 模型分类器对每个工具调用进行批准/拒绝 | 带安全防护的自主运行 | 中高 |
| `bypassPermissions` | 无需提示运行所有工具（受保护路径除外） | 沙盒 CI、完全受信任环境 | 低（危险） |
| `default` | 需要 `canUseTool` 回调进行审批 | 自定义审批流程 | 最高 |

**v5 合规要点**：
- 在 L2-L3 等级下，推荐使用 `acceptEdits` + 人工 PR 审查
- 在 L4 等级下，可以对 trivial fix 使用 `auto` 模式，但必须通过 CI 门禁
- `bypassPermissions` 在企业管理中可通过 `disableBypassPermissionsMode: "disable"` 禁用

### 2.6 Agent 安全沙箱

#### OS 级沙箱

Claude Code 支持操作系统级别的隔离：

| 平台 | 沙箱技术 | 隔离能力 |
|------|---------|---------|
| **macOS** | Seatbelt (sandbox-exec) | 文件系统 + 网络隔离 |
| **Linux** | bubblewrap | 文件系统 + 网络 + 进程隔离 |

沙箱配置：

```json
{
  "sandbox": {
    "filesystem": {
      "allow": ["./src/**", "./tests/**"],
      "deny": ["./secrets/**", ".env*", "./credentials/**"]
    },
    "network": {
      "allowedDomains": ["*.github.com", "registry.npmjs.org"],
      "blockedDomains": ["*.internal.corp"]
    }
  }
}
```

#### SDK 级沙箱

通过限制工具和权限模式实现逻辑沙箱：

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Grep", "Glob"],  # 仅允许只读工具
    permission_mode="dontAsk",  # 拒绝未允许的工具
    system_prompt="You are a read-only code analyzer. Do not make any changes.",
)
```

#### 企业级沙箱策略

```json
{
  "sandbox": {
    "filesystem": {
      "allow": {
        "managedReadPaths": ["./src/**", "./tests/**"]
      }
    },
    "network": {
      "allow": {
        "managedDomains": ["*.github.com", "registry.npmjs.org"]
      }
    }
  },
  "allowManagedHooksOnly": true,
  "allowManagedMcpServersOnly": true
}
```

### 2.7 编排逻辑

#### Sequential（顺序编排）

每个阶段依赖前一个阶段的输出：

```python
async def sequential_chain():
    """链式 Sub-Agent：调研 -> 设计 -> 实现 -> 测试"""

    # 阶段 1：调研（只读，使用 Haiku 提升速度）
    research_result = ""
    async for message in query(
        prompt="Research the existing authentication patterns in this codebase.",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Grep", "Glob", "Agent"],
            agents={
                "researcher": AgentDefinition(
                    description="Codebase research specialist.",
                    prompt="Explore the codebase thoroughly and produce a detailed report.",
                    tools=["Read", "Grep", "Glob"],
                    model="haiku",
                ),
            },
        ),
    ):
        if hasattr(message, "result"):
            research_result = message.result

    # 阶段 2：设计（使用调研输出）
    async for message in query(
        prompt=f"Based on this research:\n\n{research_result}\n\n"
               "Design a new authentication module that integrates with existing patterns.",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Write", "Grep"],
            agents={
                "architect": AgentDefinition(
                    description="Software architecture and design specialist.",
                    prompt="Create detailed design documents.",
                    tools=["Read", "Write", "Grep"],
                    model="opus",
                ),
            },
        ),
    ):
        pass  # Architect 输出

    # 阶段 3：实现、阶段 4：测试...（类似模式）
```

**适用场景**：Spec 驱动开发、新功能实现、迁移任务。

#### Parallel（并行编排）

多个 Sub-Agent 同时执行独立任务：

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

async def parallel_research():
    """并行调研三个不同的模块"""

    async def research_module(module_name):
        result = ""
        async for message in query(
            prompt=f"Analyze the {module_name} module. Document its structure, "
                   "interfaces, and dependencies.",
            options=ClaudeAgentOptions(
                allowed_tools=["Read", "Grep", "Glob", "Agent"],
                agents={
                    "analyzer": AgentDefinition(
                        description="Code analysis specialist.",
                        tools=["Read", "Grep", "Glob"],
                        model="haiku",
                    )
                },
            ),
        ):
            if hasattr(message, "result"):
                result = message.result
        return {module_name: result}

    # 并行执行
    tasks = [
        research_module("authentication"),
        research_module("database"),
        research_module("api"),
    ]
    results = await asyncio.gather(*tasks)
    return results
```

**适用场景**：并行代码审查、多模块分析、竞品调研。

#### Fan-Out/Fan-In（扇出/扇入）

主 Agent 分发任务到多个 Sub-Agent，然后汇总结果：

```
┌─────────────┐
│  Main Agent │  ← 收到用户请求
│  (Supervisor)│
└──────┬──────┘
       │ Fan-Out
  ┌────┼────┬────────┐
  ▼    ▼     ▼        ▼
┌────┐┌────┐┌────┐┌────┐
│ A1 ││ A2 ││ A3 ││ A4 │  ← Sub-Agent 并行执行
└────┘└────┘└────┘└────┘
       │ Fan-In
       ▼
┌─────────────┐
│  Synthesize │  ← 主 Agent 汇总结果
│  & Report   │
└─────────────┘
```

```text
用户：Run a parallel code review of the auth module.
     Use three sub-agents: one for security, one for performance,
     and one for test coverage. Synthesize their findings.
```

**v5 合规要点**：Fan-In 阶段必须包含 AI Reviewer 幻觉检测（P4），汇总结果必须通过人工审查后才能合并。

### 2.8 动态 Agent 工厂模式

```python
from claude_agent_sdk import AgentDefinition

def create_security_agent(security_level: str) -> AgentDefinition:
    """根据安全级别动态创建安全审查 Agent"""
    is_strict = security_level == "strict"
    return AgentDefinition(
        description="Security code reviewer",
        prompt=f"You are a {'strict' if is_strict else 'balanced'} security reviewer...",
        tools=["Read", "Grep", "Glob"],
        model="opus" if is_strict else "sonnet",
    )
```

### 2.9 Sub-Agent 恢复机制

```python
import re
from claude_agent_sdk import query, ClaudeAgentOptions

def extract_agent_id(text: str) -> str | None:
    match = re.search(r"agentId:\s*([a-f0-9-]+)", text)
    return match.group(1) if match else None

async def main():
    agent_id = None
    session_id = None

    # 第一次调用
    async for message in query(
        prompt="Use the Explore agent to find all API endpoints",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Grep", "Glob", "Agent"]),
    ):
        if hasattr(message, "session_id"):
            session_id = message.session_id
        if hasattr(message, "content"):
            extracted = extract_agent_id(str(message.content))
            if extracted:
                agent_id = extracted

    # 恢复并继续
    if agent_id and session_id:
        async for message in query(
            prompt=f"Resume agent {agent_id} and list the top 3 most complex endpoints",
            options=ClaudeAgentOptions(
                allowed_tools=["Read", "Grep", "Glob", "Agent"],
                resume=session_id
            ),
        ):
            if hasattr(message, "result"):
                print(message.result)
```

**适用场景**：隔夜运行中断恢复、长时间任务的断点续传。

### 2.10 SDK 钩子

| 钩子 | 触发时机 | 用途 |
|------|---------|------|
| `PreToolUse` | 工具执行前 | 参数验证、权限检查 |
| `PostToolUse` | 工具执行后 | 审计日志、自动验证 |
| `Stop` | Agent 完成时 | 清理、报告生成 |
| `SessionStart` | 会话开始时 | 初始化、上下文加载 |
| `SessionEnd` | 会话结束时 | 状态保存、通知 |
| `UserPromptSubmit` | 提交用户提示前 | 提示词注入检测、数据分级扫描 |

```python
from datetime import datetime
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher

async def log_file_change(input_data, tool_use_id, context):
    """文件修改审计日志"""
    file_path = input_data.get("tool_input", {}).get("file_path", "unknown")
    with open("./audit.log", "a") as f:
        f.write(f"{datetime.now()}: modified {file_path}\n")
    return {}

async for message in query(
    prompt="Refactor utils.py to improve readability",
    options=ClaudeAgentOptions(
        permission_mode="acceptEdits",
        hooks={
            "PostToolUse": [
                HookMatcher(matcher="Edit|Write", hooks=[log_file_change])
            ]
        },
    ),
):
    pass
```

### 2.11 MCP 服务器集成

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Bash", "Agent"],
    mcp_servers={
        "github": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"]
        },
        "playwright": {
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest"]
        }
    },
    agents={
        "pr-reviewer": AgentDefinition(
            description="Reviews pull requests on GitHub.",
            prompt="Review PRs and leave constructive feedback.",
            tools=["Read", "Grep", "Glob"],
        ),
    },
    permission_mode="acceptEdits",
)
```

### 2.12 关键环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `ANTHROPIC_API_KEY` | API 认证 | 必须设置 |
| `CLAUDE_CODE_USE_BEDROCK=1` | 使用 Amazon Bedrock | 未设置 |
| `CLAUDE_CODE_USE_VERTEX=1` | 使用 Google Vertex AI | 未设置 |
| `CLAUDE_CODE_USE_FOUNDRY=1` | 使用 Microsoft Foundry | 未设置 |
| `CLAUDE_CODE_SUBAGENT_MODEL` | 覆盖 Sub-Agent 模型 | 继承主会话 |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | 启用 Agent Teams | 未设置（禁用） |
| `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` | 禁用后台 Sub-Agent | 未设置 |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | 覆盖自动压缩阈值 | 95% |

---

## 第 3 章：Agent Teams 模式

### 3.1 Agent Teams 架构

Agent Teams 是 Claude Code 中的**多会话并行协调系统**。与 Sub-Agents 的关键区别：

| 特征 | Sub-Agents | Agent Teams |
|------|-----------|-------------|
| **上下文** | 独立窗口；结果返回给调用方 | 独立窗口；完全独立运行 |
| **通信** | 仅向主 Agent 报告 | 队友之间可直接通信 |
| **协调** | 主 Agent 管理所有工作 | 共享任务列表 + 自我协调 |
| **适合场景** | 聚焦任务、结果导向 | 需要讨论的复杂工作 |
| **Token 成本** | 较低（结果被摘要返回） | 较高（独立的 Claude 实例） |
| **嵌套** | 不能派生 Sub-Agent | 不能嵌套团队 |
| **启用** | 无需环境变量 | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` |

**架构总览**：

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Team                            │
│                                                          │
│  ┌──────────┐                                           │
│  │Team Lead │── 创建团队、派生队友、协调工作、综合结果     │
│  │(Claude)  │                                           │
│  └────┬─────┘                                           │
│       │                                                  │
│       ├─── 共享任务列表（文件级，带锁）                     │
│       │    ┌──────────────┬──────────────┬────────────┐  │
│       │    │ Task 1       │ Task 2       │ Task 3     │  │
│       │    │ [completed]  │ [in-progress]│ [pending]  │  │
│       │    └──────────────┴──────────────┴────────────┘  │
│       │                                                  │
│       ├─── 邮箱（Agent 间消息传递）                        │
│       │    message  → 特定队友                            │
│       │    broadcast → 所有队友                           │
│       │                                                  │
│       ▼                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │Teammate 1│  │Teammate 2│  │Teammate 3│              │
│  │(Session) │  │(Session) │  │(Session) │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

### 3.2 启用 Agent Teams

```json
// settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### 3.3 启动 Agent Team

```text
I'm designing a CLI tool that helps developers track TODO comments across
their codebase. Create an agent team to explore this from different angles: one
teammate on UX, one on technical architecture, one playing devil's advocate.
```

### 3.4 指定队友和模型

```text
Create a team with 4 teammates to refactor these modules in parallel.
Use Sonnet for each teammate.
```

### 3.5 使用 Sub-Agent 定义作为队友

```text
Spawn a teammate using the security-reviewer agent type to audit the auth module.
```

队友将继承 Sub-Agent 定义的 `tools` 允许列表和 `model`，定义体追加到队友的系统提示中。

### 3.6 Plan 审批工作流

```text
Spawn an architect teammate to refactor the authentication module.
Require plan approval before they make any changes.
```

队友在只读计划模式下工作，直到 Lead 批准。Lead 可以设置批准条件："仅批准包含测试覆盖率的计划"。

**审批流程**：

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│Teammate  │───▶│ 创建 Plan │───▶│ Lead 审批 │───▶│ 执行变更 │
│Architect │    │(只读模式) │    │(人工确认) │    │(读写模式) │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                     │                │
                     │ 审批条件：       │ 不满足条件
                     │ - 有测试覆盖率   │ → 返回修改
                     │ - 有回滚方案     │
```

**v5 合规要点**：Plan 审批工作流是 L2/L3 等级下人工审查（P4）的一种轻量形式。在代码变更前确认方案，减少返工风险。

### 3.7 任务管理

任务状态：

| 状态 | 说明 | 转换条件 |
|------|------|---------|
| **pending** | 待执行 | 初始状态 |
| **in-progress** | 执行中 | 队友认领任务 |
| **completed** | 已完成 | 队友标记完成 |

任务依赖：

```
Task 1 (database schema) [completed]
         │
         ▼ (blockedBy)
Task 2 (API endpoints) [in-progress]
         │
         ▼ (blockedBy)
Task 3 (frontend integration) [pending]
```

任务认领使用文件锁防止竞争条件。Lead 显式分配，或队友在完成当前任务后自行认领。

### 3.8 质量门禁钩子

| 钩子 | 触发时机 | 退出码 2 的效果 |
|------|---------|----------------|
| `TeammateIdle` | 队友即将空闲 | 发送反馈，要求继续工作 |
| `TaskCreated` | 任务被创建时 | 通过反馈阻止创建 |
| `TaskCompleted` | 任务被标记完成时 | 通过反馈阻止完成 |

**示例：TDD 合规门禁**

```json
{
  "hooks": {
    "TaskCompleted": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/verify-tdd-compliance.sh"
          }
        ]
      }
    ]
  }
}
```

```bash
#!/bin/bash
# verify-tdd-compliance.sh
# 检查 .gate/tdd-report.json 是否存在
if [[ ! -f ".gate/tdd-report.json" ]]; then
  echo "FAIL: TDD report missing. Task cannot be marked complete." >&2
  exit 2
fi

# 检查 Red 状态是否被记录
if ! jq -e '.red_state_verified' .gate/tdd-report.json > /dev/null 2>&1; then
  echo "FAIL: Red state not verified. Task cannot be marked complete." >&2
  exit 2
fi

exit 0
```

### 3.9 显示模式

```json
// ~/.claude.json (全局配置)
{
  "teammateMode": "in-process"
}
```

| 模式 | 说明 | 要求 |
|------|------|------|
| `auto` | tmux 分屏，否则进程内 | tmux 用于分屏 |
| `tmux` | 分屏模式（自动检测 iTerm2/tmux） | tmux 或 iTerm2 + `it2` CLI |
| `in-process` | 所有队友在主终端中 | 任意终端 |

### 3.10 与 Supervisor-Worker 的关系

Supervisor-Worker 是一种**编排模式**，而 Agent Teams 是一种**架构**。两者的关系：

```
Supervisor-Worker 模式可以通过两种方式实现：

方式 1：Sub-Agent 链（Sequential/Fan-Out）
  ┌────────────┐    ┌──────┐    ┌──────┐
  │Supervisor  │───▶│Worker│───▶│Worker│  ← 顺序执行
  │(主会话)     │    │  A   │    │  B   │
  └────────────┘    └──────┘    └──────┘

方式 2：Agent Team（并行）
  ┌────────────┐
  │Team Lead   │  ← Supervisor 角色
  │(Supervisor)│
  └─────┬──────┘
        ├─── 共享任务列表
        ▼
  ┌─────┬──────┐
  ▼     ▼      ▼
Worker Worker Worker  ← 并行执行，自我协调
  A      B      C
```

**选择准则**：

| 场景 | 推荐方式 |
|------|---------|
| 顺序依赖的流水线任务 | Sub-Agent 顺序链 |
| 独立可并行的任务 | Agent Teams |
| 需要队友间讨论/辩论 | Agent Teams |
| 只需要结果摘要 | Sub-Agent Fan-Out |
| 需要持续协调的长期工作 | Agent Teams |

### 3.11 Agent Teams 的局限性

| 局限性 | 影响 |
|--------|------|
| 无会话恢复（进程内） | `/resume` 和 `/rewind` 不恢复进程内队友 |
| 任务状态可能滞后 | 队友可能不标记任务完成，阻塞依赖任务 |
| 关闭可能较慢 | 队友在完成当前工具调用前不会停止 |
| 每会话一个团队 | 必须先清理才能启动新团队 |
| 不可嵌套团队 | 队友不能派生自己的团队 |
| Lead 固定 | 不能转移领导权 |
| 分屏支持有限 | VS Code 终端、Windows Terminal、Ghostty 不支持 |

---

## 第 4 章：全平台能力地图

### 4.1 平台概览

Claude Code 已从纯终端工具演进为**多平台自主编码平台**，覆盖六个不同的使用面（Surface）：

```
                    ┌─────────────────────────────────────────┐
                    │          Claude Code 生态系统            │
                    ├─────────────────────────────────────────┤
                    │                                         │
    ┌───────────────┤  核心 Agent 引擎 (LLM + Tools)          ├───────────────┐
    │               │                                         │               │
    ▼               ▼                                         ▼               ▼
┌────────┐    ┌──────────┐                              ┌──────────┐   ┌──────────┐
│Desktop │    │   Web    │                              │  Slack   │   │ Channels │
│  App   │    │(claude.ai│                              │Integration│   │(Telegram │
│        │    │  /code)  │                              │          │   │/Discord/ │
└────┬───┘    └────┬─────┘                              └────┬─────┘   │iMessage/ │
     │             │                                        │         │Webhooks) │
     └──────┬──────┘                                        └────┬────┘│          │
            │                                                     │     └────┬─────┘
            │                    ┌──────────┐                    │          │
            └────────────────────│ Remote   │────────────────────┘          │
                                 │ Control  │                              │
                                 │ (Phone/  │                              │
                                 │  Tablet) │                              │
                                 └──────────┘                              │
                                                                           │
                                                                    ┌──────▼──────┐
                                                                    │   Chrome    │
                                                                    │  Extension  │
                                                                    │  (Browser)  │
                                                                    └─────────────┘
```

### 4.2 平台比较矩阵

| 平台 | 主要用途 | 自主级别 | 会话持久化 | 最佳场景 | v5 适配等级 |
|------|---------|---------|-----------|---------|------------|
| **Desktop App** | 全功能自主编码 | 高（本地运行，无超时） | 磁盘持久化 | 长时间任务、定时任务 | L2-L4 |
| **Web (claude.ai/code)** | 浏览器编码 | 中（会话绑定） | 云端持久化 | 快速会话、随时随地访问 | L2-L3 |
| **VS Code 插件** | IDE 内编码 | 中（内联 diff） | 项目持久化 | 开发中即时辅助 | L1-L2 |
| **JetBrains 插件** | IDE 内编码 | 中（内联 diff） | 项目持久化 | 开发中即时辅助 | L1-L2 |
| **Remote Control** | 监控/重定向 | 中（镜像本地会话） | 镜像源会话 | 手机监控运行中的任务 | 监控层 |
| **Slack 集成** | 团队触发行动 | 高（消息触发任务） | 云端持久化 | 团队自动化、PR 工作流 | L2-L4 |
| **Channels** | 事件驱动输入 | 高（推送到运行会话） | 镜像源会话 | CI/CD 告警、事件响应 | L3-L4 |
| **Chrome 插件** | Web 应用调试 | 低（辅助，非自主） | 会话绑定 | 前端调试、实时检查 | 辅助层 |

### 4.3 Terminal CLI：核心能力

#### 核心能力

| 能力 | 说明 |
|------|------|
| 文件读写 | Read/Write/Edit 工具，完整文件系统访问 |
| 终端执行 | Bash 工具，运行构建、测试、Git 操作 |
| 多文件感知 | 理解项目结构，协调跨文件变更 |
| Hook 系统 | PreToolUse/PostToolUse/SubagentStart 等生命周期钩子 |
| 管道集成 | 与 shell 管道、CI/CD 工具链无缝集成 |
| Sub-Agent | 单会话内的独立上下文委托 |
| Agent Teams | 多会话并行协调（需实验性标志） |

#### 配置示例

```json
// .claude/settings.json
{
  "permissions": {
    "allow": ["Read(**)", "Bash(git *)", "Bash(npm run *)", "Edit(**)"],
    "deny": ["Read(./.env*)", "Bash(curl *)", "Bash(rm -rf *)"]
  },
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          { "type": "command", "command": "git diff --stat" }
        ]
      }
    ]
  }
}
```

### 4.4 Desktop App：可视化能力

#### 核心能力

| 能力 | 说明 |
|------|------|
| 完整本地工具链 | npm, pip, cargo, make, Docker 及所有本地安装的工具 |
| 定时任务 | 内置调度器，用于自主编码任务 |
| 持久会话 | 会话在应用重启后存活，基于磁盘持久化 |
| 原生性能 | 直接文件系统和进程访问 |
| Remote Control 集成 | Desktop 会话可被远程设备监控 |
| 可视化 Diff | 图形化的变更查看和审批 |

#### 定时任务配置

```json
// Desktop 定时任务
{
  "schedule": [
    {
      "name": "nightly-dependency-updates",
      "cron": "0 2 * * 1-5",
      "prompt": "Check all dependencies for updates. Update minor and patch versions. Run tests. Create PRs for any breaking changes.",
      "repository": "github.com/acme-corp/my-app",
      "branch": "auto/dep-updates",
      "permissionPolicy": "auto-approve-safe"
    },
    {
      "name": "weekly-code-review",
      "cron": "0 10 * * 1",
      "prompt": "Review all PRs created this week. Check for security issues, code quality, and test coverage.",
      "repository": "github.com/acme-corp/my-app",
      "output": "slack:#code-reviews"
    }
  ]
}
```

### 4.5 Web 浏览器：零配置编码

#### 核心能力

| 能力 | 说明 |
|------|------|
| 零配置访问 | 打开浏览器、认证、立即开始编码 |
| 云端会话 | 会话在浏览器关闭和设备切换后存活 |
| GitHub 集成 | 连接 GitHub 仓库进行代码访问 |
| 完整功能集 | 与 Desktop 相同的 Agent 能力 |
| iOS 支持 | 通过 Safari 在 iPhone/iPad 上使用 |

#### Desktop vs Web 决策指南

| 因素 | 选 Desktop | 选 Web |
|------|-----------|--------|
| 任务时长 | 数小时到数天 | 数分钟到数小时 |
| 本地工具访问 | 完整本地工具链 | 仅云端工具 |
| 隐私需求 | 代码留在本地 | 代码在云端 |
| 网络依赖 | 可离线工作 | 需要网络连接 |
| 会话持久化 | 基于磁盘 | 基于云端 |
| 安装开销 | 需要安装 | 零安装 |

#### v5 合规要点

Web 平台使用云端基础设施，发送的代码受 **P10 数据分级** 约束。在发送前必须确认不包含 Restricted 级别数据。HIPAA 合规组织应仅使用 Desktop。

### 4.6 VS Code：内联 Diff 能力

#### 核心能力

| 能力 | 说明 |
|------|------|
| 内联 Diff | 直接在编辑器中查看和审批 AI 建议的变更 |
| @-mentions | 在聊天中 @mention Sub-Agent 触发专业任务 |
| 终端集成 | 在 VS Code 终端中运行 Claude Code |
| 上下文感知 | 自动读取当前文件、选中代码、打开的标签页 |
| 快速操作 | 右键菜单中的 Code Actions 触发 AI 重构 |

#### 配置

```json
// VS Code settings.json
{
  "claude.code.autoApproveReads": true,
  "claude.code.inlineDiffMode": true,
  "claude.code.subagent.quickReview": {
    "model": "haiku",
    "tools": ["Read", "Grep"]
  }
}
```

### 4.7 JetBrains：IDE 内集成

#### 核心能力

| 能力 | 说明 |
|------|------|
| IDE 内终端 | 在 JetBrains 终端中运行 Claude Code |
| 项目上下文 | 自动检测项目结构、运行配置 |
| 文件导航 | 通过 IDE 的文件树快速定位代码 |
| 运行配置 | 与 JetBrains 运行/调试配置集成 |

### 4.8 Slack：@Claude 触发自动化

#### 核心能力

| 能力 | 说明 |
|------|------|
| @Claude 提及 | 在任意 Slack 频道提及 Claude 触发行动 |
| PR 创建 | 直接从 Slack 对话创建和管理 PR |
| 代码审查请求 | 提及 Claude + PR 链接触发自动审查 |
| 任务委派 | 从 Slack 线程分配编码任务给 Claude |
| 状态更新 | Claude 在 Slack 线程中报告进度和结果 |

#### 团队自动化工作流

```
开发者："@Claude create a PR for the auth branch with title 'Add OAuth2 support'"
Claude Code: 分析分支，创建 PR，在频道中发布链接

开发者："@Claude review this PR https://github.com/org/repo/pull/123"
Claude Code: 审查 PR，在线程中发布分析结果和建议
```

### 4.9 Chrome：Web 应用调试

#### 核心能力

| 能力 | 说明 |
|------|------|
| DOM 检查 | Claude Code 可读取当前页面结构 |
| 控制台访问 | 读取控制台日志、错误和警告 |
| 网络监控 | 查看 API 调用、响应和失败情况 |
| 实时调试 | Claude Code 可在实际运行页面上诊断问题 |
| 视觉上下文 | 理解用户实际看到的内容 |

#### 调试工作流

```
用户报告 Bug ──Chrome 插件──> Claude Code 检查实时页面 ──定位根因──> 建议修复
                                                         │
                                                         ▼
                                                  Desktop 会话实现修复
```

### 4.10 平台能力汇总

```
                    能力级别
                    │
        最高自主     │  Desktop, Slack, Channels
                    │  (L3-L4 自主编码)
                    │
        中等自主     │  Web, VS Code, JetBrains
                    │  (L2-L3 半自主)
                    │
        辅助级       │  Chrome Extension
                    │  (L1 辅助编码)
                    │
        监控/审批   │  Remote Control (手机)
                    │  (人类审批点)
                    │
                    └──────────────────────────▶
                           使用场景复杂度
```

---

## 第 5 章：多平台协同 Auto-Coding

### 5.1 跨平台协同架构

```
┌─────────────────────────────────────────────────────────┐
│                    团队层                                 │
│                                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────────────┐         │
│  │  Slack  │  │  GitHub │  │  CI/CD Pipeline │         │
│  │ Channel │  │  Events │  │  Webhooks       │         │
│  └────┬────┘  └────┬────┘  └────────┬────────┘         │
│       │            │                 │                  │
└───────┼────────────┼─────────────────┼──────────────────┘
        │            │                 │
┌───────▼────────────▼─────────────────▼──────────────────┐
│                    Claude Code Hub                       │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │  Desktop     │  │  Web/Cloud   │                     │
│  │  Sessions    │  │  Sessions    │                     │
│  └──────┬───────┘  └──────┬───────┘                     │
│         │                  │                             │
└─────────┼──────────────────┼─────────────────────────────┘
          │                  │
┌─────────▼──────────────────▼─────────────────────────────┐
│                    个人层                                 │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐        │
│  │  Remote  │  │ Channels │  │  Chrome Extension│        │
│  │  Control │  │(Telegram)│  │  (Live Debug)    │        │
│  └──────────┘  └──────────┘  └──────────────────┘        │
└──────────────────────────────────────────────────────────┘
```

### 5.2 场景 1：终端启动 → Desktop 审查 → 手机审批

这是最常见的个人开发者工作流。

```
时间线：
18:00  [Desktop]  启动 Claude Code：
                   "Refactor the auth module to use the new middleware pattern.
                    Scope: src/auth/, tests/auth/. Do not change the public API."
18:30  [Phone]    通过 Remote Control 检查：
                   Agent 已完成 8 个文件中的 3 个，进度正常
19:00  [Phone]    检查 Remote Control：
                   Agent 遇到权限门，从手机批准
20:00  [Phone]    检查 Remote Control：
                   重构完成，测试全部通过
21:00  [Desktop]  返回：审查完成的工作，确认测试通过
         [Desktop]  创建 PR，等待人工审查合并（v5 P4）
```

**v5 合规检查**：
- [ ] P3 TDD：Agent 执行了 Red→Green→Refactor
- [ ] P4 人工审查：人工在 PR 合并前审查
- [ ] P8 最小批量：Agent 按模块拆分变更
- [ ] P9 Prompt 版本化：Prompt 存储在 `.claude/prompts/` 中

### 5.3 场景 2：Web 创建定时任务 → 云端执行 → Slack 通知

适用于定期维护任务的云端工作流。

```
周一 09:00  [Web]    创建定时任务：
                     "每周依赖更新：检查 package.json，更新 minor/patch 版本，
                      运行测试，修复破坏性变更，创建 PR"
                     调度：`0 9 * * 1-5`

周一 09:00  [Cloud]  云端调度器触发任务
周一 09:05  [Cloud]  Agent 分析 package.json，识别过期依赖
周一 09:10  [Cloud]  Agent 更新依赖，运行测试，修复 breaking changes
周一 09:30  [Cloud]  Agent 创建 PR：`auto/dep-updates-2026-04-14`
周一 09:31  [Slack]  团队通知："Weekly dependency update PR created: #456"
周一 10:00  [Phone]  开发者通过 GitHub App 审查并合并 PR
```

**配置示例**：

```json
{
  "scheduledTasks": [
    {
      "name": "weekly-dependency-updates",
      "cron": "0 9 * * 1-5",
      "repository": "github.com/acme-corp/my-app",
      "branch_prefix": "auto/dep-updates",
      "prompt": "Check all dependencies in package.json. Update minor and patch versions. Run `npm test`. If tests fail due to breaking API changes, update the code accordingly. Create a PR with all updates.",
      "permissionMode": "auto",
      "notificationChannel": "slack:#engineering"
    }
  ]
}
```

**v5 合规检查**：
- [ ] P3 TDD：Agent 在更新依赖后运行测试验证
- [ ] P4 人工审查：PR 需人工审查后才能合并
- [ ] P5 密钥不入代码：依赖更新不引入密钥
- [ ] P8 最小批量：所有依赖更新合并在一个 PR 中（trivial fix）

### 5.4 场景 3：Slack 触发 → Agent 执行 → 自动 PR

团队通过 Slack 协作触发编码任务的场景。

```
[GitHub]      新 PR 创建，Slack #code-reviews 频道收到通知
[Team Lead]   "@Claude review this PR and check for security issues"
[Claude Code] 分析 diff，检查：SQL 注入、认证绕过、数据暴露
[Claude Code] 在线程中发布结构化审查报告：
              - 发现 2 个次要问题（无安全影响）
              - 1 个建议（可使用更具体的错误消息）
              - 总体：批准，附带次要意见
[Author]      处理意见，推送更新
[Claude Code] 重新审查更新的 diff，确认问题已解决
[Team Lead]   合并 PR
```

**Slack 触发配置**：

```json
{
  "slack": {
    "channel": "#code-reviews",
    "triggers": [
      {
        "pattern": "@Claude review.*PR.*https://github.com/([^/]+)/([^/]+)/pull/(\\d+)",
        "action": "code_review",
        "agents": ["security-reviewer", "quality-reviewer"],
        "output": "thread"
      },
      {
        "pattern": "@Claude create.*PR.*branch\\s+(\\S+).*title\\s+[\"'](.+?)[\"']",
        "action": "create_pr",
        "output": "channel"
      }
    ]
  }
}
```

**v5 合规检查**：
- [ ] P4 人工审查：AI Reviewer 执行第一层审查，Human Reviewer 执行第二层
- [ ] P9 Prompt 版本化：审查使用的 Prompt 版本可追溯

### 5.5 场景 4：Channels 监控 → 自动修复

CI/CD 失败时自动修复的场景。

```
[CI System]   主分支构建失败
[Webhook]     POST 到 Claude Code Channel，附带失败日志
[Agent]       分析日志，识别根因："TypeScript 类型错误 in auth.ts:42"
[Agent]       在新分支中实现修复
[Agent]       本地运行测试，全部通过
[Agent]       创建 PR，发布到 Slack："Auto-fixed CI failure: #456"
[Developer]   审查自动修复，批准合并
```

**Channel Webhook 配置**：

```json
{
  "channels": {
    "webhook": {
      "endpoint": "/webhook/ci-failure",
      "authentication": "bearer:$CI_WEBHOOK_TOKEN",
      "session": "ci-auto-fix",
      "prompt_template": "CI build failed. Analyze the following logs and create a fix:\n\n{{logs}}",
      "permissionMode": "acceptEdits",
      "output": {
        "on_success": "slack:#ci-status: Auto-fixed CI failure, PR created",
        "on_failure": "slack:#ci-status: CI failure requires human attention: {{summary}}"
      }
    }
  }
}
```

**CI Pipeline 配置（GitHub Actions）**：

```yaml
name: CI
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install && npm test

  ai-fix:
    needs: build
    if: failure()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Trigger Claude Code Auto-Fix
        run: |
          curl -X POST "${CLAUDE_WEBHOOK_URL}/webhook/ci-failure" \
            -H "Authorization: Bearer $CI_WEBHOOK_TOKEN" \
            -H "Content-Type: application/json" \
            -d '{
              "repository": "${{ github.repository }}",
              "branch": "${{ github.ref_name }}",
              "commit": "${{ github.sha }}",
              "logs": ${{ toJson(steps.build.outputs.logs) }}
            }'
```

**v5 合规检查**：
- [ ] P3 TDD：Agent 在修复后运行测试验证
- [ ] P4 人工审查：自动修复通过 PR 提交，需人工审查
- [ ] P2 DCP 门禁：夜间/周末自动修复需前置 DCP 确认
- [ ] 自修复限制：Agent 最多尝试 3 轮 Self-Correction

### 5.6 跨平台会话管理

#### 会话持久化策略

| 平台 | 持久化机制 | 恢复能力 |
|------|-----------|---------|
| Desktop | 磁盘持久化 | 完整恢复（包括 Sub-Agent 状态） |
| Web | 云端持久化 | 完整恢复（跨设备） |
| CLI + tmux | 终端多路复用 | 会话级恢复 |
| VS Code | 项目级存储 | 有限恢复 |

#### 跨平台消息传递

```
Desktop Session ──── Remote Control ──── Phone Browser
       │                                      │
       │  Slack Notification                   │
       ▼                                      ▼
  ┌─────────┐    ┌──────────┐    ┌──────────────┐
  │ Desktop │◄──►│  Slack   │◄──►│  Phone/App   │
  │ Session │    │  Bot     │    │  Remote Ctrl │
  └─────────┘    └──────────┘    └──────────────┘
       │
       │  Channel Webhook
       ▼
  ┌──────────┐
  │ CI/CD    │
  │ Webhook  │
  └──────────┘
```

#### 会话安全准则

- **不要**在多个平台同时编辑同一文件
- **始终**使用 Remote Control 而非独立会话来从手机访问
- **配置**重要会话的通知，确保及时收到权限请求
- **限制**手机端的 Diff 审查大小（小屏幕难以审查大变更）

---

## 第 6 章：团队自动化

### 6.1 Slack 集成模式

#### 6.1.1 PR 审查机器人

一个 Claude Code 实例监控 Slack 频道，自动审查每个发布的 PR 链接：

```
配置：
  - Slack 频道：#code-reviews
  - 触发器：包含 GitHub PR URL 的任意消息
  - 行动：完整的代码审查 + 安全检查
  - 输出：结构化审查结果作为线程回复

结果：每个 PR 在几分钟内得到审查，无人工审查瓶颈
```

#### 6.1.2 事件响应管道

CI 失败自动触发调查和修复：

```
配置：
  - CI Webhook → Channel → Claude Code 会话
  - 会话可访问：仓库、测试套件、部署配置
  - 自动批准：只读操作、测试运行
  - 需要批准：代码修改、部署

结果：70% 的 CI 失败在无人工干预下自动修复
```

#### 6.1.3 文档同步

代码变更自动触发文档更新：

```
配置：
  - GitHub merge to main 的 Webhook → Channel
  - Claude Code："更新 API 文档和 README 以匹配合并的变更"
  - 创建包含文档更新的 PR
  - 团队通过 Slack 收到通知

结果：文档永远不过时
```

### 6.2 Channels 模式（Telegram/Discord/iMessage/Webhook）

#### 6.2.1 CI/CD 管道集成

```
GitHub Actions (CI fails) ──Webhook──> Claude Code Session ──Auto-fix──> Push PR
```

- CI 失败 webhook 触发 Claude Code 分析失败
- Agent 读取日志、识别根因、实现修复
- Agent 创建修复 PR
- 成功/失败状态发回到 Channel

#### 6.2.2 事件响应

```
PagerDuty Alert ──Webhook──> Claude Code Session ──Analyze──> Telegram notification
```

- 生产告警触发 Claude Code 调查
- Agent 检查日志、指标、最近部署
- 通过 Telegram 发送发现和建议的修复

#### 6.2.3 开发团队聊天

```
Discord #dev channel ──Bot──> Claude Code Session ──Execute──> Discord reply
```

- 团队成员在 Discord 中说 "fix the failing tests"
- Claude Code 分析并修复测试
- 在 Discord 中报告变更内容

#### 6.2.4 Channel + Remote Control 组合模式

最强大的模式结合 Channels 和 Remote Control：

```
1. CI 失败推送告警到 Telegram (Channel)
2. 在手机上阅读告警，通过 Telegram 批准修复 (Channel 输入)
3. Claude Code 在本地会话中开始修复
4. 通过 Remote Control 从手机监控进度
5. 修复部署，确认信息发送回 Telegram (Channel 输出)
```

### 6.3 GitHub Code Review 自动化

#### 6.3.1 自动 PR 审查

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

async def github_pr_review(pr_url: str):
    """自动 GitHub PR 审查"""
    async for message in query(
        prompt=f"Review this PR: {pr_url}\n\n"
               "Check for:\n"
               "1. Security vulnerabilities (SQL injection, XSS, auth bypass)\n"
               "2. Code quality (function length, complexity, DRY)\n"
               "3. Test coverage (are new features tested?)\n"
               "4. Breaking changes (API compatibility)\n"
               "5. TDD compliance (were tests written before implementation?)\n\n"
               "Post a structured review with Critical/Warning/Suggestion categories.",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Grep", "Glob", "Bash", "Agent"],
            agents={
                "security-reviewer": AgentDefinition(
                    description="Security code reviewer.",
                    prompt="Review for security vulnerabilities...",
                    tools=["Read", "Grep", "Glob"],
                    model="opus",
                ),
                "test-analyzer": AgentDefinition(
                    description="Test coverage analyzer.",
                    prompt="Analyze test coverage for the changes...",
                    tools=["Read", "Bash", "Grep"],
                    model="haiku",
                ),
            },
            mcp_servers={
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"]
                }
            },
        ),
    ):
        if hasattr(message, "result"):
            print(message.result)
```

#### 6.3.2 PR 创建自动化

```bash
#!/bin/bash
# create-ai-pr.sh — AI 生成的 PR 创建脚本
# 确保 PR 包含完整的 v5 追溯信息

PR_TITLE="${1:-Auto: Feature implementation}"
PR_BODY=$(cat <<EOF
## AI Coding Trace (v5.0)

- **Spec**: specs/F001-user-registration.md
- **Prompt Version**: v1.1.0
- **Model**: sonnet (implement), opus (review)
- **Autonomy Level**: L3
- **TDD**: Red at 14:23:01, Green at 14:25:47
- **Self-Correction**: 1 round (fixed import path)
- **AI Review**: Passed (0 critical, 1 warning)
- **DCP**: Go decision confirmed at 14:20:00

## Changes

- Implemented user registration endpoint
- Added validation for email and password
- Created integration and unit tests
- Updated API documentation

## Checklist

- [x] TDD compliance verified
- [x] AI Review passed
- [x] No secrets in code
- [x] Tests passing
EOF
)

gh pr create \
  --title "$PR_TITLE" \
  --body "$PR_BODY" \
  --base main \
  --label "ai-generated" \
  --reviewer "security-team"
```

### 6.4 团队 Skill 共享

通过项目级 `.claude/` 目录共享 Sub-Agent 定义和 Skills：

```
.claude/
├── agents/
│   ├── code-reviewer.md        # 团队共享的代码审查 Agent
│   ├── test-runner.md          # 测试执行 Agent
│   ├── security-scanner.md     # 安全扫描 Agent
│   └── doc-sync.md             # 文档同步 Agent
├── skills/
│   ├── api-conventions/        # API 约定技能
│   ├── error-handling-patterns/ # 错误处理模式
│   └── testing-strategy/       # 测试策略
├── settings.json               # 项目级设置
└── CLAUDE.md                   # 项目指令
```

**好处**：
- 新团队成员立即可用相同的 Agent 配置
- Agent 定义通过 Git 版本化，变更可追溯
- 技能（Skills）共享确保团队使用一致的编码模式

---

## 第 7 章：安全与治理

### 7.1 多平台下的权限管理

#### 权限层级

```
┌─────────────────────────────────────────────────┐
│            Managed Settings (组织级)              │
│  - 服务器下发 / 端点管理                            │
│  - 不可被用户覆盖                                  │
│  - 支持 fail-closed（强制远程刷新）                 │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│            CLI 参数 (会话级)                      │
│  - 临时覆盖                                      │
│  - 仅在会话期间有效                               │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│            项目设置 (.claude/settings.json)       │
│  - 团队共享                                      │
│  - 版本控制                                      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│            用户设置 (~/.claude/settings.json)     │
│  - 个人偏好                                      │
│  - 跨项目生效                                     │
└─────────────────────────────────────────────────┘

关键规则：如果某工具在任一层级被拒绝，其他层级无法允许它。
```

#### 企业策略配置示例

```json
{
  "permissions": {
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./credentials/**)"
    ],
    "disableBypassPermissionsMode": "disable",
    "disableAutoMode": "disable"
  },
  "allowManagedPermissionRulesOnly": true,
  "allowManagedHooksOnly": true,
  "forceRemoteSettingsRefresh": true
}
```

#### 跨平台权限一致性

| 平台 | 权限执行 | 说明 |
|------|---------|------|
| Desktop | 本地 settings.json + Managed Settings | 完整执行 |
| Web | 云端 Managed Settings | 受组织策略控制 |
| Slack | 云端 Managed Settings | 继承组织策略 |
| VS Code | 项目 settings.json | 受限于项目配置 |
| Channels | 会话级权限 | 继承源会话权限 |

### 7.2 跨平台审计追踪

#### 审计日志架构

```
┌─────────────────────────────────────────────────────┐
│                  审计日志系统                          │
│                                                      │
│  Desktop Session ──┐                                 │
│  Web Session     ──┼──▶ 审计日志收集 ──▶ 集中存储     │
│  Slack Actions   ──┤                  (audit.log)     │
│  Channel Events  ──┤                    │             │
│  CLI Sessions    ──┘                    ▼             │
│                                    SIEM / 监控        │
└─────────────────────────────────────────────────────┘
```

#### 审计日志格式

```json
{
  "timestamp": "2026-04-14T14:23:01Z",
  "session_id": "abc-123-def",
  "platform": "desktop",
  "agent_type": "implementer",
  "action": "Edit",
  "file": "src/auth/login.ts",
  "line_range": [42, 55],
  "result": "success",
  "tdd_state": "green",
  "prompt_version": "v1.1.0",
  "model": "sonnet"
}
```

#### SDK 级审计钩子

```python
from datetime import datetime
from claude_agent_sdk import HookMatcher

async def audit_log(input_data, tool_use_id, context):
    """通用审计日志钩"""
    tool_name = input_data.get("tool_name", "unknown")
    file_path = input_data.get("tool_input", {}).get("file_path", "N/A")

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "file": file_path,
        "session": getattr(context, "session_id", "unknown"),
    }

    with open("./audit.log", "a") as f:
        f.write(f"{log_entry}\n")

    return {}

# 在 ClaudeAgentOptions 中使用：
# hooks={"PostToolUse": [HookMatcher(matcher="Edit|Write", hooks=[audit_log])]}
```

### 7.3 敏感操作的多平台确认

#### 敏感操作分类

| 操作 | 风险级别 | 确认要求 |
|------|---------|---------|
| 修改数据库 schema | Critical | 必须人工确认（任意平台） |
| 修改认证/授权逻辑 | Critical | 必须人工确认 + Security Review |
| 合并到 main 分支 | High | 必须人工 PR 审查（P4） |
| 修改环境变量/密钥配置 | Critical | 必须人工确认 + P5 检查 |
| 删除文件或目录 | High | 必须人工确认 |
| 部署到生产环境 | Critical | DCP Go 决策 + 人工确认 |
| 修改依赖版本（major） | Medium | 人工审查 PR |

#### 多平台确认流程

```
敏感操作触发
     │
     ├── Desktop:  弹窗确认对话框
     ├── Web:      浏览器中显示确认提示
     ├── Slack:    @user 需要确认，点击 ✅/❌ 按钮
     ├── Channels: 发送确认消息到 Telegram/Discord
     └── Remote Control: 手机上显示确认请求

任一平台确认后，操作继续执行
```

### 7.4 远程访问的安全边界

#### Remote Control 安全约束

| 约束 | 说明 |
|------|------|
| 认证 | 只有认证用户才能访问会话 |
| 加密 | 所有通信端到端加密 |
| 超时 | 可配置会话超时，超时后自动断开 |
| 权限 | 远程控制继承源会话的权限模式 |
| 审计 | 所有远程操作记录到审计日志 |

#### Web 平台安全注意事项

| 风险 | 缓解措施 |
|------|---------|
| 代码在云端 | 使用 Desktop 处理敏感代码 |
| 会话劫持 | 启用 SSO + MFA |
| 数据泄露 | P10 数据分级：pre-send 扫描 |
| 浏览器扩展冲突 | 仅使用官方 Chrome Extension |

#### Channels 安全

```json
{
  "allowedChannelPlugins": ["telegram", "discord", "webhook"],
  "channels": {
    "webhook": {
      "authentication": "bearer",
      "allowedIPs": ["10.0.0.0/8", "172.16.0.0/12"],
      "rateLimit": "10/minute"
    }
  }
}
```

### 7.5 合规要求映射

| 合规框架 | 要求 | Claude Code 实现 |
|---------|------|-----------------|
| **SOC 2** | 变更管理流程 | 自主编码变更通过标准 PR 审查流程 |
| **GDPR** | 个人数据处理 | 确保 Claude Code 会话 Prompt 不包含 PII |
| **HIPAA** | 受保护健康信息 | 避免将 PHI 发送到云端会话；仅使用 Desktop |
| **ISO 27001** | 访问控制 + 审计 | Managed Settings + 审计钩子 + 权限系统 |

### 7.6 风险缓解矩阵

| 风险 | 缓解措施 | v5 原则 |
|------|---------|---------|
| Agent 引入 Bug | 合并前要求测试通过；人工审查 | P3, P4 |
| Agent 修改错误文件 | Prompt 中的作用域约束；文件模式限制 | P8 |
| Agent 暴露密钥 | CI 中的密钥扫描；合并前审查 diff | P5 |
| 定时任务无限运行 | 设置超时限制；监控任务完成 | 自修复限制 |
| 未授权访问会话 | 强认证；会话超时 | P10 |
| Agent 创建无限循环 | 会话超时；迭代限制 | 自修复限制 |
| 依赖更新破坏构建 | 运行完整测试套件；准备回滚分支 | P3 |

---

## 第 8 章：v4 合规注释

### 8.1 与 v4 核心原则的映射

本文档中的所有实践均建立在 v4.0 核心原则之上。以下是本文档涉及的 v4 原则映射：

| v4 原则 | 本文档中的体现 |
|---------|---------------|
| **P1 商业驱动** | 所有自主编码任务必须有明确的业务目标。Agent 不应在无商业价值的方向上消耗资源 |
| **P2 DCP 门禁** | L3/L4 自主编码前必须完成 DCP Go 决策。夜间/周末开发尤其需要 DCP 前置 |
| **P3 TDD 先行** | Sub-Agent 和 Agent SDK 执行 Red→Green→Refactor 时，CI 必须记录 Red 状态 |
| **P4 人工审查** | 所有 AI 生成代码必须经过人工 Code Review。L1-L3 逐 PR 审查，L4 定期审计 |
| **P5 密钥不入代码** | pre-commit hook + SAST 双重拦截，Sub-Agent 的审计钩子自动扫描 |
| **P6 单一信息源** | Agent 读取的上下文文件（AGENTS.md、CLAUDE.md）是事实唯一来源 |
| **P7 Spec 驱动** | L3/L4 下 Agent 直接从 `specs/` 目录读取任务队列自动执行 |
| **P8 最小批量** | Agent 一次只生成一个函数或小模块的代码。超过 50 行函数或 200 行文件必须拆分 |
| **P9 Prompt 版本化** | Sub-Agent prompt 在文件中定义，受版本控制。PR 必须声明使用的 Prompt 版本 |
| **P10 数据分级** | 发送到 AI 的数据必须经过分类。Web/云端平台需特别注意 pre-send 扫描 |

### 8.2 安全边界说明

#### 本文档中不可违反的安全边界

1. **Sub-Agent 工具最小化**：永远不要给 Sub-Agent 超过其任务所需的工具权限
2. **禁止自动合并到受保护分支**：L1-L3 禁止自动合并；L4 仅限 trivial fix
3. **人工审查不可跳过**：即使在 L4 定期审计模式下，非 trivial 变更仍需人工审查
4. **密钥检测自动化**：不依赖 AI 自觉，必须配置 pre-commit hook + SAST
5. **DCP 门禁不可绕过**：自主编码前必须完成 DCP 确认
6. **TDD 不可造假**：AI 不得在同一 commit 中同时提交测试和实现
7. **Self-Correction 最多 3 轮**：超过 3 轮必须转人工
8. **数据分级扫描**：发送到云端 AI 的数据必须经过 pre-send 分类

#### 本文档引入的 v5 新增安全机制

| 机制 | 说明 | 适用等级 |
|------|------|---------|
| **幻觉检测** | AI Reviewer 检查不存在的 API、虚构的函数名等 | L1-L4 |
| **TDD 造假检测** | CI 检查测试和实现不在同一 commit | L2-L4 |
| **Agent 审计钩子** | PostToolUse 钩子自动记录文件修改 | L2-L4 |
| **计划审批工作流** | Agent Teams 中的 Plan Approval 机制 | L2-L3 |
| **质量门禁钩子** | TeammateIdle/TaskCompleted 钩子阻止不合规操作 | L3-L4 |
| **多平台权限一致性** | Managed Settings 确保跨平台策略一致 | L3-L4 |

### 8.3 自治等级与平台选择

| 等级 | 推荐平台 | 自主能力 | 人工干预点 |
|------|---------|---------|-----------|
| **L1** | Desktop, VS Code | 无自主编码 | 每一步 |
| **L2** | Desktop, Web, VS Code | 单特性完整开发循环 | PR 合并前 |
| **L3** | Desktop + Slack + Channels | 夜间/周末自主开发 | PR 合并前 + DCP |
| **L4** | Desktop + Slack + Channels + Web | 完全自主（trivial fix 自动合并） | 定期审计 |

### 8.4 本文档与配套文档的关系

| 文档 | 关系 |
|------|------|
| [01-core-specification.md](01-core-specification.md) | 核心原则定义，本文档的实践必须遵守 |
| [02-auto-coding-practices.md](02-auto-coding-practices.md) | 自主编码场景定义，本文档提供多 Agent/多平台实现 |
| [04-security-governance.md](04-security-governance.md) | 企业安全与治理详情，本文档第 7 章为其摘要 |
| [05-tool-reference.md](05-tool-reference.md) | CLI 参考、Settings、Hooks、Skills 配置模板 |

---

*本文档是 AI Coding 规范 v5.0 系列的第 03 篇，与 01-02 核心规范和 04-05 支持文档共同构成完整的 v5.0 体系。*
*所有实践必须在 v5 核心原则定义的安全边界内执行。*
*功能和安全能力可能随产品迭代变化，请以官方最新文档为准。*
