# AI Coding 规范 v5.2：Auto-Coding 实践

> 版本：v5.2 | 2026-04-17
> 定位：在安全边界内最大化自主性的实践指南
> 前置：必须先阅读并理解 [01-core-specification.md](01-core-specification.md)
> 关联：与 03-multi-agent-multi-surface、04-security-governance、05-tool-reference 共同构成 v5.2 完整体系
> 变更：基于 v5.1 引入 P23 需求→Spec 链引用、Skill Generalization、Self-Correction/Prompt Chaining 归一化

---

## 目录

- [第 1 章：Auto-Coding 场景总览](#第-1-章auto-coding-场景总览)
- [第 2 章：自主编码模式](#第-2-章自主编码模式)
- [第 3 章：定时任务与持续自主执行](#第-3-章定时任务与持续自主执行)
- [第 4 章：自修复 CI](#第-4-章自修复-ci)
- [第 5 章：夜间/周末自主开发](#第-5-章夜间周末自主开发)
- [第 6 章：Supervisor-Worker 自动编排](#第-6-章supervisor-worker-自动编排)
- [第 7 章：Auto-Coding 度量](#第-7-章auto-coding-度量)
- [第 8 章：v4 合规注释](#第-8-章v4-合规注释)

---

## 第 1 章：Auto-Coding 场景总览

### 1.1 什么是 Auto-Coding

Auto-Coding（自主编码）是指 AI Agent 在最小化或零人工干预的情况下，独立完成软件开发生命周期中的编码活动。与 AI 辅助编码（AI-Assisted Coding）的本质区别：

| 维度 | AI 辅助编码 | Auto-Coding |
|------|------------|-------------|
| 执行模式 | 人在编辑器中，AI 逐行补全 | AI 独立执行完整开发循环 |
| 干预频率 | 每次编辑都需要人参与 | 仅在里程碑/审查点介入 |
| 工具使用 | IDE 内联补全 | 终端、文件系统、Git、CI/CD 全栈 |
| 持续时间 | 分钟级 | 小时级到数天（夜间/周末） |
| 适用自治等级 | L1 | L2-L4 |

**核心定义**：Auto-Coding 是 AI 作为执行者而非助手，能够在给定 Spec 和约束条件下，独立完成"理解需求 -> 生成测试 -> 实现代码 -> 自修验证 -> 创建 PR"的完整开发循环。

### 1.2 Auto-Coding vs AI 辅助编码的区别

```
AI 辅助编码（L1）：
  人：写 Spec -> 写测试 -> AI 补全实现 -> 人审查 -> 人合并

Auto-Coding（L2+）：
  人：写 Spec -> 审核 Spec
  AI：生成测试 -> 验证 Red -> 生成实现 -> 验证 Green -> 自修 -> 创建 PR
  人：审查 PR -> 合并（或拒绝）
```

**关键区别**：
1. **开发循环的所有权**：辅助编码中，人驱动每一步；Auto-Coding 中，AI 驱动开发循环，人只在审查点介入
2. **时间窗口**：辅助编码是同步的；Auto-Coding 可以是异步的（夜间/周末）
3. **错误处理**：辅助编码中，人即时纠正；Auto-Coding 中，AI 通过 Self-Correction Loop 自主修复
4. **规模**：辅助编码适合单文件/小改动；Auto-Coding 适合多文件/完整特性

### 1.3 L1-L4 各等级的 Auto-Coding 能力

#### L1（辅助编码）：Auto-Coding 不适用

L1 下 AI 仅作为助手，人在每一步都参与。严格来说，L1 不是 Auto-Coding。

**适用场景**：
- 团队刚开始使用 AI Coding，尚未积累信任
- 安全敏感项目（金融、医疗、政府）
- 法规要求人工逐行审查的场景

**Auto-Coding 能力**：无。AI 只响应单次指令，不独立运行开发循环。

#### L2（半自主编码）：基础 Auto-Coding

AI 独立完成单个特性的完整开发循环，人工在每个 PR 合并前审查。

**能力范围**：
- 读取 Spec 并生成测试（基于 Gherkin 验收标准）
- 执行 TDD Red -> Green -> Refactor 完整循环
- 运行 Self-Correction Loop（最多 3 轮）
- 自动创建 PR 并填入追溯信息（Spec/Prompt/Model）
- 执行 AI Reviewer 幻觉检测

**约束**：
- 每个 PR 必须经过人工审查后才能合并（v5 P4）
- 禁止自动合并到任何受保护分支
- 两层审查：AI Reviewer + Human Reviewer

**推荐场景**：**日常开发的默认等级**

#### L3（受限自主编码）：进阶 Auto-Coding

AI 作为"夜班开发者"，可以在无人值守时持续工作。

**新增能力**（相比 L2）：
- 从 `specs/` 目录读取状态为 `ready` 的 Spec 自动开始开发
- 夜间/周末持续运行，无需人工实时监督
- 异步 Decision Point 确认（DP1-DP2 通过消息通知）
- 可批量审查多个 PR（早晨统一审查）
- CI Gate 全量执行（含幻觉检测）

**约束**：
- 夜间/周末开发前必须通过 DCP Go 决策
- 每个 PR 仍须人工审查后才能合并
- 发现安全问题立即暂停自主开发并降级到 L2
- Self-Correction 超过 3 轮必须转人工

**推荐场景**：夜间特性工厂、自修复 CI、成熟团队的常规开发

#### L4（完全自主编码）：高级 Auto-Coding

AI 作为"独立开发者"，人作为"审计者"。

**新增能力**（相比 L3）：
- 自动合并 trivial fix（lint 修复、格式修复、注释更新）到 main
- 定期审计替代逐 PR 审查（每周随机抽样 >= 10%）
- DCP 门禁简化为自动化检查清单
- 自动化回滚机制

**严格约束**：
- 自动合并仅限：lint fix、format、typo fix in comments、dependency version patch update
- 任何涉及业务逻辑、架构变更、API 变更的代码不得自动合并
- 每周审计报告必须公开，团队可见
- 安全扫描 CRITICAL 级别问题必须立即阻断
- 审计通过率 < 95% 自动降级到 L3

**推荐场景**：高成熟度团队、低风险变更、长期运维环境

### 1.4 Auto-Coding 能力矩阵

| 能力 | L1 | L2 | L3 | L4 |
|------|----|----|----|----|
| 独立 TDD 循环 | 否 | 是 | 是 | 是 |
| 自修循环（3 轮） | 人工确认每轮 | 自动执行 | 自动执行 | 自动执行 |
| 从 specs/ 自动获取任务 | 否 | 否 | 是 | 是 |
| 夜间/周末持续运行 | 否 | 否 | 是 | 是 |
| 自动创建 PR | 否 | 是 | 是 | 是 |
| AI Reviewer 幻觉检测 | 人工 | 自动 | 自动 | 自动 |
| 自动合并到 main | 禁止 | 禁止 | 禁止 | 仅限 trivial |
| 异步 DCP 确认 | 否 | 否 | 是 | 是（自动化） |
| 自动降级 | 否 | 否 | 是 | 是 |

### 1.5 Auto-Coding 的价值与风险

**最高 ROI 的 Auto-Coding 场景**（按价值排序）：
1. 依赖更新与 CI 自修复（低风险、高频次）
2. 夜间特性工厂（给定 Spec，早晨审查）
3. 机械性重构（重命名、提取方法、类型标注）
4. 测试生成（基于 Spec 自动生成测试代码）
5. 文档同步（代码变更后自动更新文档）

**最高风险的 Auto-Coding 场景**：
1. 安全相关代码（认证、授权、加密）
2. 数据库迁移（不可逆的 schema 变更）
3. 架构级重构（影响多个模块的依赖关系）
4. 性能关键路径（延迟敏感、资源密集）

**黄金法则**：Auto-Coding 的质量与测试覆盖率成正比。测试基础设施薄弱的团队应先投资 TDD，再提升自治等级。

---

## 第 2 章：自主编码模式

### 2.1 持续编码循环（TDD-first 版本）

v5.0 要求所有 Auto-Coding 模式必须遵循 TDD-first 顺序。这是 v4 核心原则 P3 的强制性执行。

#### 2.1.1 TDD-first 循环流程

```
┌─────────────────────────────────────────────────────────────┐
│                    TDD-First 持续编码循环                     │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ [生成测试] │───▶│ [验证 Red]│───▶│ [生成实现]│              │
│  │ 从 Spec   │    │ 测试必须  │    │ 最小实现  │              │
│  │ AC 生成   │    │ 失败      │    │ 让测试通过│              │
│  └──────────┘    └──────────┘    └────┬─────┘              │
│       ▲                               │                     │
│       │                               ▼                     │
│  ┌────┴─────┐    ┌──────────┐    ┌──────────┐              │
│  │ [Refactor]│◀───│ [验证 Green]│◀───│ [Self-Correct]│     │
│  │ 重构代码  │    │ 测试全部  │    │ 最多 3 轮  │              │
│  │ 测试仍通过│    │ 通过      │    │ 修复失败  │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │                               ▲                     │
│       ▼                               │                     │
│  ┌──────────┐    ┌──────────┐         │                     │
│  │ [提交 PR] │◀───│ [AI Review]│        │                     │
│  │ 追溯信息  │    │ 幻觉检测  │         │                     │
│  └──────────┘    └──────────┘         │                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 2.1.2 循环步骤详解

**步骤 1：生成测试**
```
输入：specs/F{NNN}-{name}.md（包含 Gherkin 验收标准）
输出：test/ 目录下的测试文件
约束：
  - 每个 AC（Acceptance Criteria）至少对应一个测试
  - 测试先于实现提交（git commit 时间戳验证）
  - L1/L2：人工审核断言正确性
  - L3/L4：AI 自主生成，CI 抽检
```

**步骤 2：验证 Red**
```
操作：运行测试，确认全部失败
验证：CI 记录 Red 状态到 .gate/tdd-report.json
失败处理：
  - 如果测试意外通过 -> 断言可能错误 -> 进入自修
  - 如果测试无法运行 -> 测试代码有语法错误 -> 进入自修
```

**步骤 3：生成实现**
```
约束：
  - 最小批量（P8）：一次只实现一个函数/小模块
  - 超过 50 行的函数或 200 行的文件必须拆分
  - 匹配现有代码模式（命名、导入、错误处理）
```

**步骤 4：验证 Green**
```
操作：运行全部测试，确认通过
失败处理：进入 Self-Correction Loop
成功条件：
  - 全部测试通过
  - lint 无新增警告
  - 类型检查通过
```

**步骤 5：Self-Correction Loop（最多 3 轮）**
```
轮次 1：AI 读取错误输出，诊断根因，修复代码
轮次 2：AI 重新运行，如果仍失败，读取更广泛上下文
轮次 3：AI 最后一次尝试
超过 3 轮：
  - L2：暂停，通知人工介入
  - L3：暂停，发送异步告警，降级当前任务
  - L4：暂停，创建 Issue 并标记 needs-human
```

**步骤 6：Refactor**
```
约束：
  - 重构后测试必须全部通过
  - 不改变外部行为
  - CI 验证无回归
```

**步骤 7：AI Review + PR 创建**
```
AI Reviewer 检查清单：
  - 幻觉代码检测（不存在的 API、虚构的函数名）
  - 密钥泄露检测（硬编码密码、token）
  - 安全漏洞检测（SQL 注入、XSS、路径遍历）
  - 代码质量（函数长度、圈复杂度、重复代码）

PR 必须包含的追溯信息：
  - Spec 文件路径和版本
  - 使用的 Prompt 版本（P9）
  - 使用的模型和参数
  - TDD 合规报告（Red -> Green 时间戳）
  - Self-Correction 轮次
  - AI Review 结果
```

#### 2.1.3 TDD 造假检测

AI 可能在一次提交中同时提交测试和实现，使 TDD 流程看起来被执行但实际没有。CI 必须：

```bash
# CI Gate 脚本示例：检查 TDD 合规
#!/bin/bash

# 1. 检查提交顺序：测试文件必须先于实现文件提交
TEST_COMMITS=$(git log --oneline --diff-filter=A -- '*_test.*' | head -1)
IMPL_COMMITS=$(git log --oneline --diff-filter=A -- 'src/**' | head -1)

if [[ "$TEST_COMMITS" > "$IMPL_COMMITS" ]]; then
  echo "FAIL: TDD order violation - test commit must precede implementation"
  exit 1
fi

# 2. 检查测试和实现不得在同一 commit 中
SAME_COMMIT=$(git log --oneline -n 100 -- '*_test.*' 'src/**' | \
  awk '{print $1}' | sort | uniq -d)
if [[ -n "$SAME_COMMIT" ]]; then
  echo "FAIL: Test and implementation in same commit(s): $SAME_COMMIT"
  exit 1
fi

# 3. 验证 Red 状态记录
if [[ ! -f ".gate/tdd-report.json" ]]; then
  echo "FAIL: TDD report missing"
  exit 1
fi

echo "PASS: TDD compliance verified"
```

### 2.2 Spec-Driven 自主编码

#### 2.2.1 架构概览

```
┌──────────────────────────────────────────────────────────┐
│                    Spec-Driven 自主编码                     │
│                                                          │
│  specs/                                                  │
│  ├── F001-user-registration.md    [ready]               │
│  ├── F002-user-login.md           [ready]               │
│  ├── F003-password-reset.md       [in-progress]         │
│  └── F004-permission-system.md    [backlog]             │
│       │                                                  │
│       ▼                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │ Spec 解析器   │───▶│ 任务队列     │───▶│ 执行引擎    │  │
│  │ 读取 Gherkin  │    │ 按优先级排序  │    │ 选择 ready  │  │
│  │ 生成测试骨架  │    │ 检查依赖关系  │    │ 的 Spec    │  │
│  └──────────────┘    └──────────────┘    └─────┬──────┘  │
│                                                │          │
│                                    ┌───────────┴───────┐  │
│                                    ▼                    ▼  │
│                              ┌──────────┐        ┌──────┐  │
│                              │ 开发循环  │        │ 暂停  │  │
│                              │ TDD-first │        │ 等待  │  │
│                              └────┬─────┘        │ 人工  │  │
│                                   │              └──────┘  │
│                                   ▼                         │
│                              ┌──────────┐                  │
│                              │ 创建 PR   │                  │
│                              │ 等待审查  │                  │
│                              └──────────┘                  │
└──────────────────────────────────────────────────────────┘
```

#### 2.2.2 Spec 文件格式

```markdown
# F001: User Registration

## Status
ready

## Priority
high

## Description
Allow users to register with email and password.

## Acceptance Criteria

### AC-1: Successful Registration
**Given** a user provides a valid email and password
**When** they submit the registration form
**Then** a new user record is created in the database
**And** a verification email is sent
**And** the response contains the user ID (excluding password)

### AC-2: Duplicate Email
**Given** a user provides an email that already exists
**When** they submit the registration form
**Then** the response returns 409 Conflict
**And** the error message indicates the email is already registered

### AC-3: Weak Password
**Given** a user provides a password shorter than 8 characters
**When** they submit the registration form
**Then** the response returns 400 Bad Request
**And** the error message indicates minimum password length

## Technical Constraints
- Use bcrypt for password hashing
- Email verification via JWT token (24h expiry)
- Rate limit: 5 registrations per IP per hour

## Dependencies
- F000: Database schema (completed)
```

#### 2.2.3 Spec 验证 Gate

在 AI 开始开发前，必须通过 Spec 验证 Gate：

```
Spec Validation Gate:
  [ ] Spec 文件格式正确（包含 required 字段）
  [ ] Gherkin AC 可解析为测试用例
  [ ] 依赖的 Spec 已完成（status = completed）
  [ ] 技术约束可执行（非模糊描述）
  [ ] L1/L2：人工审核 Spec 通过
  [ ] L3/L4：自动验证通过，定期人工抽检
```

#### 2.2.4 实现示例：Spec 队列处理器

```bash
#!/bin/bash
# spec-runner.sh — Spec-Driven 自主编码的入口脚本
# 用法：./spec-runner.sh --max-tasks 5 --timeout 3600

set -euo pipefail

SPECS_DIR="specs"
GATE_DIR=".gate"
MAX_TASKS="${1:-5}"
TIMEOUT="${2:-3600}"
START_TIME=$(date +%s)

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# Pre-flight: DCP Check (required for L3/L4)
if [[ "${AUTONOMY_LEVEL:-L2}" == "L3" || "${AUTONOMY_LEVEL:-L2}" == "L4" ]]; then
  if [[ ! -f "${GATE_DIR}/dcp-go.confirmed" ]]; then
    log "ERROR: DCP Go not confirmed. Cannot start autonomous run."
    log "Run DCP checklist and confirm before starting."
    exit 1
  fi
fi

completed=0
for spec_file in $(ls "${SPECS_DIR}"/F*.md | sort); do
  spec_name=$(basename "$spec_file" .md)
  status=$(grep -m1 '^status:' "$spec_file" | awk '{print $2}')

  # Only process ready specs
  if [[ "$status" != "ready" ]]; then
    log "SKIP: $spec_name (status=$status)"
    continue
  fi

  # Check timeout
  elapsed=$(( $(date +%s) - START_TIME ))
  if [[ $elapsed -gt $TIMEOUT ]]; then
    log "TIMEOUT: Reached ${TIMEOUT}s limit. Stopping."
    break
  fi

  # Check max tasks
  if [[ $completed -ge $MAX_TASKS ]]; then
    log "LIMIT: Reached ${MAX_TASKS} tasks. Stopping."
    break
  fi

  log "START: Processing $spec_name"

  # Run Claude Code with the spec
  claude -p --max-turns 100 \
    "Execute the spec at ${spec_file}. Follow TDD-first: generate tests, verify Red, implement, verify Green. Create a PR when done." \
    --permission-mode auto \
    --max-budget-usd 10.00

  # Verify PR was created
  pr_url=$(git log --oneline -5 | grep -o 'https://github.com/[^ ]*' || true)
  if [[ -n "$pr_url" ]]; then
    log "SUCCESS: $spec_name -> PR created"
    # Update spec status
    sed -i "s/^status: ready/status: in-progress/" "$spec_file"
    ((completed++))
  else
    log "WARN: $spec_name — no PR detected, checking for blockers"
    # Update spec status to indicate issue
    sed -i "s/^status: ready/status: blocked/" "$spec_file"
  fi
done

log "COMPLETE: Processed $completed specs in $(( $(date +%s) - START_TIME ))s"
```

### 2.3 Prompt Chaining 自主执行链

> **说明**：Prompt Chaining 的详细定义已在 [01-core-specification.md](01-core-specification.md) 第 6.2 节中统一定义。在执行 Prompt Chaining 之前，必须先完成 P23 的 Requirement→Solution→Spec 链（见 01-core-specification.md 1.6.2）。本节补充 Auto-Coding 场景下的具体执行细节。

#### 2.3.1 链式架构

Prompt Chaining 将复杂任务拆分为多个阶段，每个阶段的输出作为下一阶段的输入：

```
[Phase 1: 需求分析]
  输入：用户描述 / Jira Ticket
  输出：结构化的 Spec 文件
  模型：opus（需要理解力）

       │
       ▼

[Phase 2: 测试生成]
  输入：Spec 文件（Gherkin AC）
  输出：测试代码
  模型：sonnet（执行任务）

       │
       ▼

[Phase 3: 实现生成]
  输入：Spec + 测试代码
  输出：实现代码
  模型：sonnet

       │
       ▼

[Phase 4: 代码审查]
  输入：Spec + 测试 + 实现 diff
  输出：审查报告 + 修复建议
  模型：opus（需要判断力）

       │
       ▼

[Phase 5: 最终验证]
  输入：修复后的代码
  输出：验证通过 / 转人工
  模型：sonnet
```

#### 2.3.2 Prompt Chain 配置

```json
{
  "prompt_chain": {
    "name": "feature-implementation",
    "phases": [
      {
        "id": "analyze",
        "prompt_file": "prompts/analyze.md",
        "model": "opus",
        "input": "user_description",
        "output": "spec_file",
        "timeout_seconds": 300,
        "max_cost_usd": 2.00
      },
      {
        "id": "test",
        "prompt_file": "prompts/generate-tests.md",
        "model": "sonnet",
        "input": "spec_file",
        "output": "test_files",
        "timeout_seconds": 600,
        "max_cost_usd": 3.00,
        "gate": "tests_must_fail_without_implementation"
      },
      {
        "id": "implement",
        "prompt_file": "prompts/implement.md",
        "model": "sonnet",
        "input": ["spec_file", "test_files"],
        "output": "implementation_files",
        "timeout_seconds": 900,
        "max_cost_usd": 5.00,
        "gate": "all_tests_must_pass"
      },
      {
        "id": "review",
        "prompt_file": "prompts/review.md",
        "model": "opus",
        "input": ["spec_file", "test_files", "implementation_files"],
        "output": "review_report",
        "timeout_seconds": 300,
        "max_cost_usd": 2.00,
        "gate": "no_critical_issues"
      }
    ],
    "on_failure": "notify_human",
    "max_retries_per_phase": 2,
    "trace_file": ".gate/prompt-chain-trace.json"
  }
}
```

#### 2.3.3 版本化与追溯

每个 Prompt 文件必须版本化（P9）：

```
prompts/
├── v1.0.0/
│   ├── analyze.md
│   ├── generate-tests.md
│   ├── implement.md
│   └── review.md
├── v1.1.0/
│   ├── analyze.md          # 添加了数据分级检查
│   ├── generate-tests.md
│   ├── implement.md
│   └── review.md           # 添加了幻觉检测规则
└── current -> v1.1.0       # 符号链接指向当前版本
```

每个 PR 必须声明使用的 Prompt 版本：

```markdown
## AI Coding Trace
- Prompt Version: v1.1.0
- Model: sonnet (implement), opus (analyze, review)
- Spec: specs/F001-user-registration.md
- TDD: Red at 14:23:01, Green at 14:25:47
- Self-Correction: 1 round (fixed import path)
- AI Review: Passed (0 critical, 1 warning)
```

### 2.4 Self-Correction Loop 自主修复

> **说明**：Self-Correction Loop 的详细定义、规则和上限已在 [01-core-specification.md](01-core-specification.md) 第 1.7 节中统一定义。本节补充 Auto-Coding 场景下的具体执行细节。

#### 2.4.1 修复策略

```
┌───────────────────────────────────────────────────────────┐
│                  Self-Correction Loop                       │
│                                                           │
│  [测试/构建失败]                                           │
│       │                                                    │
│       ▼                                                    │
│  ┌─────────────────┐                                      │
│  │ Round 1: 快速修复 │                                      │
│  │ - 读取错误输出   │                                      │
│  │ - 定位失败行     │                                      │
│  │ - 应用最小修复   │                                      │
│  │ - 重新运行验证   │                                      │
│  └────────┬────────┘                                      │
│           │ 成功 -> [退出循环]                              │
│           │ 失败 -> ▼                                      │
│  ┌─────────────────┐                                      │
│  │ Round 2: 上下文扩展│                                      │
│  │ - 读取相关文件   │                                      │
│  │ - 检查依赖关系   │                                      │
│  │ - 分析根因       │                                      │
│  │ - 应用修正       │                                      │
│  │ - 重新运行验证   │                                      │
│  └────────┬────────┘                                      │
│           │ 成功 -> [退出循环]                              │
│           │ 失败 -> ▼                                      │
│  ┌─────────────────┐                                      │
│  │ Round 3: 最后尝试 │                                      │
│  │ - 全面探索代码库  │                                      │
│  │ - 尝试替代方案    │                                      │
│  │ - 应用修正       │                                      │
│  │ - 重新运行验证   │                                      │
│  └────────┬────────┘                                      │
│           │ 成功 -> [退出循环]                              │
│           │ 失败 -> ▼                                      │
│  ┌─────────────────┐                                      │
│  │ 转人工            │                                      │
│  │ - 创建 Issue     │                                      │
│  │ - 附诊断报告     │                                      │
│  │ - 标记 needs-human│                                      │
│  └─────────────────┘                                      │
└───────────────────────────────────────────────────────────┘
```

#### 2.4.2 修复禁忌清单

Self-Correction 中 AI **不得**执行以下操作：

| 禁忌 | 原因 | 检测方式 |
|------|------|---------|
| 修改测试断言使其"通过" | 可能掩盖真实 bug | 对比测试文件 diff |
| 删除失败的测试 | 降低覆盖率 | CI 检查覆盖率变化 |
| 添加 `@skip` / `@ignore` | 绕过而非修复 | lint 规则 |
| 放宽类型检查 | 降低安全性 | 类型检查输出 |
| 添加 `try/catch` 吞掉异常 | 隐藏错误 | 代码审查 |
| 修改生产代码以适配错误测试 | 本末倒置 | 人工审查 |

#### 2.4.3 诊断报告模板

当 Self-Correction 超过 3 轮仍失败时，AI 必须生成诊断报告：

```markdown
# Self-Correction Failure Report

## Spec
F003: Password Reset

## Failed Test
`test_password_reset_expired_token` — Expected 401, got 200

## Root Cause Analysis
经过 3 轮尝试，无法确定根因。可能原因：
1. Token 过期逻辑未正确实现（JWT exp 字段检查缺失）
2. 测试中的时间模拟方式与实现代码不兼容
3. 边界条件：token 恰好在前一秒过期

## Attempts Made
1. **Round 1**: 添加了 `exp` 字段检查 -> 仍失败（测试使用了过期 token 但实现未检查）
2. **Round 2**: 修改了实现中的时间比较逻辑 -> 仍失败（引入了新的类型错误）
3. **Round 3**: 尝试使用 mock clock -> 仍失败（mock clock 与 JWT 库不兼容）

## Recommendation for Human
- 检查 JWT 库的过期验证行为是否与预期一致
- 可能需要修改测试的时间模拟策略
- 涉及认证逻辑，建议人工介入

## Files Modified
- src/auth/token.go (3 edits, all reverted)
- tests/auth/token_test.go (no changes — correctly preserved)
```

### 2.4.5 Skill Generalization 技能泛化

> **说明**：Skill Generalization 的详细定义见 [01-core-specification.md](01-core-specification.md) 2.24.5。本节补充 Auto-Coding 场景下的执行细节。

在 Auto-Coding 模式下，每次需求→Spec 链完成后，Supervisor Agent 应自动执行技能泛化：

```
编码完成 → [Skill Generalization] → 模式提取 → 知识库更新
              ├─ 成功模式 → domain-knowledge/tech-stack/{stack}.md
              ├─ 失败模式 → domain-knowledge/project-specific/historical-lessons.md
              └─ 设计模式 → domain-knowledge/project-specific/architecture-decisions.md
```

**执行时机**：每个 Feature 的需求→Spec 链完成、Spec 生成后、进入编码执行前。

**输出示例**：

```yaml
# domain-knowledge/project-specific/historical-lessons.md 新增条目
## [2026-04-17] F001 用户注册 - 密码验证模式
- 问题: bcrypt 版本兼容性导致验证失败
- 方案: 固定 bcrypt@5.0.1，不升级到 5.1.x
- 可复用: 所有需要密码哈希的场景
```

### 2.5 Supervisor-Worker 自主编排

详见 [第 6 章](#第-6-章supervisor-worker-自动编排)。

---

## 第 3 章：定时任务与持续自主执行

### 3.1 定时任务概述

定时任务是 Auto-Coding 的基础设施，使 AI 能够在预定时间自动启动、执行任务、产出结果。v5.0 支持三种定时任务模式：

| 模式 | 执行环境 | 关机后运行 | 适用场景 | 权限模式 |
|------|---------|-----------|---------|---------|
| Cloud Scheduled Tasks | Anthropic 云端 | 是 | 依赖更新、文档生成、代码审查 | dontAsk |
| Desktop Scheduled Tasks | 本地 Desktop App | 否（需 Desktop 运行） | 构建、测试、Docker 操作 | auto |
| CLI /loop | 会话级 | 否（需会话活跃） | 轮询、持续监控、交互式 | 继承会话 |

### 3.2 Cloud Scheduled Tasks（Anthropic 云端）

#### 3.2.1 架构

```
┌─────────────────────────────────────────────────────────┐
│               Cloud Scheduled Tasks                      │
│                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │ Cron Scheduler│──▶│ Cloud Runner │──▶│ GitHub PR  │  │
│  │ (Anthropic   │    │ (Cloud VM)   │    │ API        │  │
│  │  云端)       │    │              │    │            │  │
│  └─────────────┘    │ - 克隆 repo   │    └────────────┘  │
│                     │ - 运行 Prompt  │                    │
│                     │ - 创建分支/PR  │                    │
│                     └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

**关键特性**：
- 关机也运行：不依赖本地机器
- GitHub 集成：直接操作仓库
- 适合：不需要本地工具链的任务

**局限**：
- 无法访问本地工具（Docker、本地数据库）
- 受限于云端可用的工具集
- 不适用于需要本地构建环境的任务

#### 3.2.2 配置示例

```bash
# 每日依赖更新检查
/schedule create \
  --cron "0 9 * * 1-5" \
  --prompt "Check all dependencies for outdated versions. Update any that have minor or patch updates. Run tests. If tests pass, create a PR. If tests fail, note the incompatibility and skip that update." \
  --repo "my-org/my-repo" \
  --branch "auto/dependency-updates" \
  --permission-mode dontAsk \
  --max-turns 50

# 每周代码审查
/schedule create \
  --cron "0 10 * * 1" \
  --prompt "Review all PRs merged this week. Check for: security issues, code quality, test coverage. Post a summary report." \
  --repo "my-org/my-repo" \
  --permission-mode dontAsk \
  --max-turns 30
```

### 3.3 Desktop Scheduled Tasks（本地）

#### 3.3.1 架构

```
┌─────────────────────────────────────────────────────────┐
│              Desktop Scheduled Tasks                      │
│                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │ Cron Scheduler│──▶│ Desktop App  │──▶│ Full Local │  │
│  │ (Desktop App │    │ (Running     │    │ Toolchain  │  │
│  │  内置)       │    │  Locally)    │    │ Access     │  │
│  └─────────────┘    │              │    └────────────┘  │
│                     │ - 克隆 repo   │                    │
│                     │ - npm/pip/go  │                    │
│                     │ - Docker      │                    │
│                     │ - Full Bash   │                    │
│                     └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

**关键特性**：
- 完整本地工具链访问
- 适合：需要构建、测试、Docker 的任务

**要求**：
- Desktop App 必须在任务执行时保持运行
- 本地机器不能关机

#### 3.3.2 配置示例

```bash
# 夜间测试生成
/schedule create \
  --cron "0 2 * * *" \
  --prompt "Generate tests for all code changed today. Follow TDD: tests first, verify they fail without implementation, then note what implementation is needed." \
  --permission-mode auto \
  --max-turns 100 \
  --max-budget-usd 10.00

# CI 自修复
/schedule create \
  --cron "*/30 * * * *" \
  --prompt "Check if the main branch CI is failing. If so, analyze the failure logs and attempt to fix. Create a PR if successful." \
  --permission-mode auto \
  --max-turns 50
```

### 3.4 CLI /loop 命令（会话级轮询）

#### 3.4.1 用法

```bash
# 在 Claude Code 会话中
/loop 30m "Check if any new specs have been added to specs/ with status=ready. If so, process them."

# 持续监控 CI 状态
/loop 5m "Check CI status for the main branch. If failing, analyze and attempt fix."
```

**限制**：
- 仅在当前会话活跃时运行
- 适合：短时间内的轮询任务
- 不适合：长时间无人值守的任务

#### 3.4.2 /loop 与定时任务的选择指南

| 需求 | 推荐方案 | 原因 |
|------|---------|------|
| 每天固定时间运行 | Cloud/Desktop Scheduled | 精确调度，会话无关 |
| 关机后也要运行 | Cloud Scheduled | 云端执行 |
| 需要本地工具链 | Desktop Scheduled | 访问本地环境 |
| 会话内的短期轮询 | /loop | 会话级，灵活 |
| 事件驱动（非定时） | Channels + Webhook | 实时触发 |

### 3.5 周末自主开发完整模式

#### 3.5.1 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    周末自主开发模式                            │
│                                                             │
│  Friday 17:00  [Developer]                                   │
│    │                                                         │
│    ├── 1. 检查 specs/ 目录中的 ready 任务                     │
│    ├── 2. 确认 DCP Go（v5 P2）                               │
│    ├── 3. 配置定时任务（见 3.5.3）                            │
│    ├── 4. 设置 Kill Switch 参数                              │
│    ├── 5. 启用 Remote Control（手机监控）                     │
│    └── 6. 启动 Desktop Scheduled Tasks                       │
│                                                             │
│  Saturday 00:00 ── Sunday 23:59  [Agent]                     │
│    │                                                         │
│    ├── 持续 TDD-first 循环                                    │
│    ├── 每完成一个 Spec 创建 PR                                │
│    ├── 遇到阻塞发送告警到 Channel                             │
│    ├── Kill Switch 触发时停止                                 │
│    └── 状态持久化到 .omc/state/                              │
│                                                             │
│  Monday 09:00  [Developer]                                   │
│    │                                                         │
│    ├── 1. 审查所有生成的 PR                                   │
│    ├── 2. 运行手动测试                                        │
│    ├── 3. 合并通过的 PR                                      │
│    ├── 4. 更新 Spec 状态                                     │
│    └── 5. 记录本周自主开发度量数据                            │
└─────────────────────────────────────────────────────────────┘
```

#### 3.5.2 前置检查清单

```markdown
## 周末自主开发前置检查清单

### DCP 确认（v5 P2，必须完成）
- [ ] 商业目标已定义（P1：本周末要完成哪些有价值的需求）
- [ ] Spec 文件已准备好（P7：specs/ 中 status=ready 的任务已审核）
- [ ] Prompt 版本已确认（P9：使用最新的 prompt 版本）
- [ ] 数据分级检查已配置（P10：无 Restricted 数据会被发送）

### 技术准备
- [ ] 测试覆盖率 >= 80%（自修复依赖测试）
- [ ] CI Gate 已配置（编译 + 测试 + lint + SAST）
- [ ] pre-commit hook 已启用（密钥扫描、lint）
- [ ] 分支保护规则已设置（main 不可直接推送）

### 安全准备
- [ ] Kill Switch 参数已设置（最大时间、最大成本、最大文件数）
- [ ] 告警 Channel 已配置（Slack / Telegram / webhook）
- [ ] Remote Control 已启用
- [ ] 紧急联系人已指定（遇到安全事件时通知谁）

### 度量基准
- [ ] 当前自主成功率已记录
- [ ] 当前幻觉率已记录
- [ ] 当前 TDD 执行率已记录
```

#### 3.5.3 定时任务配置示例

```json
{
  "weekend_auto": {
    "name": "Weekend Hack — Sprint 12",
    "start": "2026-04-18T00:00:00+08:00",
    "end": "2026-04-20T00:00:00+08:00",
    "tasks": [
      {
        "name": "Feature Factory",
        "schedule": "*/2 * * * *",
        "prompt": "Check specs/ for tasks with status=ready. Pick the highest priority one. Execute TDD-first development cycle. Create PR when done. Update spec status to in-progress.",
        "max_turns": 200,
        "max_budget_usd": 15.00,
        "timeout_seconds": 7200,
        "branch_prefix": "auto/weekend/"
      },
      {
        "name": "CI Monitor",
        "schedule": "*/15 * * * *",
        "prompt": "Check CI status. If main branch is failing, analyze and attempt fix. Create PR if successful.",
        "max_turns": 50,
        "max_budget_usd": 3.00,
        "timeout_seconds": 1800
      },
      {
        "name": "Quality Check",
        "schedule": "0 */6 * * *",
        "prompt": "Run full test suite, lint, type check. Report results. Flag any new warnings.",
        "max_turns": 20,
        "max_budget_usd": 1.00,
        "timeout_seconds": 600
      }
    ],
    "kill_switch": {
      "max_total_budget_usd": 50.00,
      "max_wall_clock_hours": 48,
      "max_files_per_pr": 50,
      "forbidden_dirs": ["database/migrations", "secrets", ".env"],
      "alert_channel": "slack:#auto-coding-alerts"
    },
    "notification": {
      "on_completion": true,
      "on_blocker": true,
      "on_kill_switch": true,
      "on_cost_threshold_usd": 25.00,
      "channel": "telegram"
    }
  }
}
```

### 3.6 夜间自主开发模式

#### 3.6.1 架构

```
┌─────────────────────────────────────────────────────────┐
│                  夜间自主开发模式                          │
│                                                         │
│  18:00  [Developer] 下班前                                │
│    │                                                     │
│    ├── 检查 specs/ 中的 ready 任务                        │
│    ├── 运行 DCP 快速确认（异步，5 分钟）                   │
│    ├── 启动 Desktop Scheduled Task                       │
│    │   cron: "0 20 * * *" (8PM start)                   │
│    │   timeout: 10 hours (until 6AM)                    │
│    └── 启用 Remote Control 到手机                        │
│                                                         │
│  20:00 - 06:00  [Agent] 夜间运行                          │
│    │                                                     │
│    ├── 20:00  开始处理第一个 ready Spec                   │
│    ├── 21:30  PR #1 创建（Feature A）                     │
│    ├── 21:35  开始处理第二个 ready Spec                   │
│    ├── 23:00  PR #2 创建（Feature B）                     │
│    ├── 23:05  CI 失败 — 进入自修复循环                    │
│    ├── 23:15  自修复成功，PR #3 创建                      │
│    ├── 02:00  遇到阻塞（依赖外部 API）— 发送告警           │
│    │         暂停当前任务，继续下一个                      │
│    ├── 04:00  第三个 Spec 完成                            │
│    ├── 05:30  质量检查运行（全量测试 + lint）             │
│    └── 06:00  超时到达，停止运行                          │
│                                                         │
│  09:00  [Developer] 早晨审查                              │
│    │                                                     │
│    ├── 检查 Remote Control 通知（是否有告警）              │
│    ├── 审查 PR #1, #2, #3                                │
│    ├── 合并通过的 PR                                     │
│    └── 处理阻塞任务（外部 API 依赖）                       │
└─────────────────────────────────────────────────────────┘
```

#### 3.6.2 夜间任务配置

```bash
# 夜间特性工厂 — Desktop Scheduled Task
/schedule create \
  --name "nightly-feature-factory" \
  --cron "0 20 * * 1-5" \
  --permission-mode auto \
  --max-turns 300 \
  --max-budget-usd 20.00 \
  --prompt "$(cat <<'EOF'
Nightly Feature Factory — L3 Autonomous Run

Rules:
1. Read specs/ directory and find tasks with status=ready
2. For each task (max 3 per night):
   a. Read the spec file
   b. Generate tests from Gherkin AC
   c. Verify tests fail (Red)
   d. Implement the feature (Green)
   e. Self-correct if tests fail (max 3 rounds)
   f. Refactor
   g. Create PR with full trace info
3. If blocked for >30 min, send alert and skip to next task
4. At 05:30, run full quality check
5. Stop at 06:00 regardless of progress

Constraints:
- Do NOT modify files in database/migrations/
- Do NOT send any Restricted data
- Do NOT auto-merge any PR
- Follow TDD strictly (tests before implementation)
- Max 50 files per PR
EOF
)"
```

### 3.7 Kill Switch 和超时机制

#### 3.7.1 Kill Switch 层级

```
┌─────────────────────────────────────────────────────────┐
│                  Kill Switch 层级                        │
│                                                         │
│  L1 — Soft Warning（通知但不中断）                        │
│  ├── 运行时间 > 4 小时                                   │
│  ├── 成本 > $10                                         │
│  ├── 自修复轮次 > 2（接近上限）                           │
│  └── 修改文件数 > 30                                     │
│                                                         │
│  L2 — Hard Stop（立即中断并通知）                         │
│  ├── 运行时间 > 8 小时                                   │
│  ├── 成本 > $30                                         │
│  ├── 修改文件数 > 50                                    │
│  ├── 修改了 forbidden_dirs 中的文件                      │
│  ├── 检测到密钥泄露                                      │
│  └── 检测到 Restricted 数据发送                          │
│                                                         │
│  L3 — Emergency Shutdown（中断 + 回滚 + 告警）             │
│  ├── 安全事件（密钥提交到仓库）                            │
│  ├── 数据泄露（Restricted 数据被发送）                     │
│  └── 未经授权的分支操作（直接推送到 main）                 │
└─────────────────────────────────────────────────────────┘
```

#### 3.7.2 实现示例

```bash
#!/bin/bash
# kill-switch.sh — 自主运行的 Kill Switch 监控脚本
# 用法：./kill-switch.sh --max-hours 8 --max-cost 30.00 --pid $AGENT_PID

set -euo pipefail

MAX_HOURS="${1:-8}"
MAX_COST="${2:-30.00}"
AGENT_PID="${3:-0}"
FORBIDDEN_DIRS="database/migrations secrets .env"
START_TIME=$(date +%s)

check_cost() {
  # 通过 API 或日志文件检查当前成本
  local current_cost
  current_cost=$(grep -o 'cost_usd":[0-9.]*' .omc/state/session.json 2>/dev/null | \
    grep -o '[0-9.]*' || echo "0")
  if (( $(echo "$current_cost > $MAX_COST" | bc -l) )); then
    echo "KILL: Cost limit exceeded ($current_cost > $MAX_COST)"
    return 0
  fi
  return 1
}

check_time() {
  local elapsed=$(( $(date +%s) - START_TIME ))
  local max_seconds=$(( MAX_HOURS * 3600 ))
  if [[ $elapsed -gt $max_seconds ]]; then
    echo "KILL: Time limit exceeded (${elapsed}s > ${max_seconds}s)"
    return 0
  fi
  return 1
}

check_forbidden_changes() {
  local changes
  changes=$(git diff --name-only HEAD 2>/dev/null || true)
  for dir in $FORBIDDEN_DIRS; do
    if echo "$changes" | grep -q "^${dir}/"; then
      echo "KILL: Forbidden directory modified: $dir"
      return 0
    fi
  done
  return 1
}

check_secrets() {
  # 使用 gitleaks 或类似工具扫描
  if command -v gitleaks &>/dev/null; then
    if gitleaks detect --source . --no-banner --redact 2>/dev/null; then
      echo "KILL: Secret detected in code"
      return 0
    fi
  fi
  return 1
}

# Main monitoring loop
while kill -0 "$AGENT_PID" 2>/dev/null; do
  sleep 60  # Check every minute

  if check_cost; then
    kill -SIGTERM "$AGENT_PID"
    echo "$(date): Kill switch triggered — cost limit" | \
      tee -a .omc/logs/kill-switch.log
    # Emergency rollback
    git reset --hard HEAD~1 2>/dev/null || true
    exit 1
  fi

  if check_time; then
    kill -SIGTERM "$AGENT_PID"
    echo "$(date): Kill switch triggered — time limit" | \
      tee -a .omc/logs/kill-switch.log
    exit 0  # Normal stop
  fi

  if check_forbidden_changes; then
    kill -SIGTERM "$AGENT_PID"
    echo "$(date): Kill switch triggered — forbidden directory" | \
      tee -a .omc/logs/kill-switch.log
    exit 2
  fi

  if check_secrets; then
    kill -SIGTERM "$AGENT_PID"
    echo "$(date): Kill switch triggered — secret detected" | \
      tee -a .omc/logs/kill-switch.log
    exit 3
  fi
done
```

#### 3.7.3 超时恢复策略

```
超时触发后的行为：
  1. 保存当前状态到 .omc/state/（断点续传支持）
  2. 提交当前工作到临时分支（不创建 PR）
  3. 发送通知（Channel / Slack / Telegram）
  4. 清理临时资源
  5. 退出

状态文件格式：
  {
    "task_id": "F003",
    "spec_file": "specs/F003-password-reset.md",
    "phase": "implement",
    "iteration": 12,
    "last_successful_step": "tests_generated_and_red_verified",
    "files_modified": ["src/auth/reset.go", "tests/auth/reset_test.go"],
    "timestamp": "2026-04-14T23:45:00Z",
    "can_resume": true
  }
```

---

## 第 4 章：自修复 CI

### 4.1 CI 构建失败的自动分析和修复

#### 4.1.1 架构

```
┌────────────────────────────────────────────────────────────┐
│                     自修复 CI 流程                           │
│                                                            │
│  [Push to branch] ──▶ [CI Pipeline]                       │
│                            │                                │
│                    ┌───────┴───────┐                        │
│                    ▼               ▼                        │
│              [CI Passes]      [CI Fails]                    │
│                    │               │                        │
│                    ▼               ▼                        │
│            [Deploy/Merge]   [AI Agent Activated]            │
│                                   │                          │
│                          ┌────────┴────────┐                │
│                          ▼                 ▼                │
│                  [分析失败日志]    [获取 git diff]           │
│                          │                 │                │
│                          └────────┬────────┘                │
│                                   ▼                          │
│                          [诊断根因]                          │
│                                   │                          │
│                    ┌──────────────┼──────────────┐          │
│                    ▼              ▼              ▼          │
│              [Lint 错误]    [测试失败]    [构建错误]          │
│                    │              │              │          │
│                    ▼              ▼              ▼          │
│              [自动修复]    [Self-Correct]  [自动修复]        │
│              (成功率 >90%)  (最多 3 轮)    (成功率 >80%)     │
│                          │                                 │
│                    ┌─────┴─────┐                           │
│                    ▼           ▼                           │
│              [修复成功]    [修复失败]                       │
│                    │           │                           │
│                    ▼           ▼                           │
│              [创建 PR]    [通知人工]                        │
│              (trivial:    (附诊断报告)                      │
│               自动合并)                                    │
└────────────────────────────────────────────────────────────┘
```

#### 4.1.2 GitHub Actions 集成

```yaml
# .github/workflows/self-healing-ci.yml
name: Self-Healing CI

on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]

jobs:
  analyze-failure:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ github.event.workflow_run.head_branch }}

      - name: Download failure logs
        uses: actions/download-artifact@v4
        with:
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          path: ./ci-logs

      - name: Setup Claude Code
        run: |
          curl -fsSL https://claude.ai/install.sh | bash
          claude auth login --token ${{ secrets.CLAUDE_API_KEY }}

      - name: Analyze and Fix
        run: |
          claude -p --max-turns 50 --max-budget-usd 5.00 \
            --permission-mode auto \
            "CI has failed on branch ${{ github.event.workflow_run.head_branch }}.
            Analyze the failure logs in ./ci-logs/ and identify the root cause.
            Attempt to fix the issue following these rules:

            1. If it's a lint/style error -> fix it directly
            2. If it's a type error -> fix it with minimal change
            3. If it's a test failure -> diagnose and fix (max 3 self-correction rounds)
            4. If it's a build/dependency error -> fix config or update imports

            DO NOT:
            - Modify test assertions to make them pass
            - Add @skip or @ignore annotations
            - Change production code to match incorrect tests

            Create a PR with branch name: auto/ci-fix-$(date +%Y%m%d-%H%M%S)
            Include a diagnostic report in the PR description."

      - name: Notify on Slack
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          channel-id: '#ci-alerts'
          payload: |
            {
              "text": "CI self-healing: ${{ job.status == 'success' && 'PR created' || 'failed to fix' }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*CI Self-Healing Result*\nBranch: ${{ github.event.workflow_run.head_branch }}\nStatus: ${{ job.status }}"
                  }
                }
              ]
            }
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
```

#### 4.1.3 GitLab CI/CD 集成

```yaml
# .gitlab-ci.yml — 自修复 CI 配置
stages:
  - build
  - test
  - self-heal

variables:
  CLAUDE_AUTO_HEAL: "true"

build:
  stage: build
  script:
    - go build ./...
  allow_failure: false

test:
  stage: test
  script:
    - go test ./... -cover
  allow_failure: true  # Allow failure so self-heal can trigger

self-heal:
  stage: self-heal
  script:
    - |
      if [[ "$CI_JOB_STATUS" != "success" ]]; then
        echo "CI failed, attempting self-healing..."

        # Install Claude Code
        curl -fsSL https://claude.ai/install.sh | bash

        # Analyze and fix
        claude -p --max-turns 50 --max-budget-usd 5.00 \
          --permission-mode auto \
          "Build or test failed. Analyze and fix."

        # Create merge request
        git checkout -b "auto/ci-fix-$(date +%Y%m%d-%H%M%S)"
        git add -A
        git commit -m "Auto-fix CI failure"
        git push -o merge_request.create -o merge_request.target=main
      fi
  rules:
    - when: on_failure
  allow_failure: true
```

### 4.2 依赖更新的自动测试和 PR

#### 4.2.1 AI 增强的依赖更新流程

```
[扫描依赖清单]
   │
   ▼
[对比已安装版本与 Registry]
   │
   ▼
[分类更新类型]
   ├── Patch 更新（x.x.0 -> x.x.1）
   │     └── 自动创建 PR + 自动合并（L4，测试通过即可）
   │
   ├── Minor 更新（x.0.0 -> x.1.0）
   │     └── 创建 PR + AI 读取 Changelog + 适配代码
   │
   └── Major 更新（0.0.0 -> 1.0.0）
         └── 创建 PR + AI 读取 Changelog + 适配代码 + 必须人工审查
   │
   ▼
[运行全量测试]
   │
   ├── 测试通过 -> 创建 PR
   │     ├── Trivial (patch): L4 可自动合并
   │     └── Non-trivial (minor/major): 必须人工审查
   │
   └── 测试失败 -> 记录不兼容性，跳过该更新
```

#### 4.2.2 配置示例

```yaml
# .github/workflows/dependency-updates.yml
name: AI-Enhanced Dependency Updates

on:
  schedule:
    - cron: "0 9 * * 1-5"  # Weekdays at 9 AM
  workflow_dispatch:

jobs:
  dependency-update:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Run AI Dependency Update Agent
        run: |
          claude -p --max-turns 100 --max-budget-usd 15.00 \
            --permission-mode auto \
            "Check all dependencies for outdated versions.
            For each outdated dependency:
            1. Check if it's a patch, minor, or major update
            2. For patch updates: update version and test
            3. For minor/major updates: read the changelog, update code for breaking changes, then test
            4. Create a separate PR for each update with the changelog summary

            Rules:
            - Patch updates can be auto-merged if tests pass (L4 only)
            - Minor/major updates MUST require human review
            - Security patches are highest priority
            - If a dependency update breaks the build, skip it and note why"
```

### 4.3 代码质量问题的自动修复

#### 4.3.1 可自动修复的质量问题

| 问题类型 | 自动修复成功率 | 是否需要人工审查 |
|---------|-------------|---------------|
| Lint 警告（格式、命名） | > 95% | 否（L4 可自动合并） |
| 未使用的导入 | > 99% | 否 |
| 类型推断缺失 | > 90% | 否 |
| 过时的 API 调用 | > 80% | 是（需确认行为不变） |
| 缺失错误处理 | > 60% | 是（需确认错误处理正确） |
| 圈复杂度过高 | > 50% | 是（需确认逻辑不变） |
| 代码重复 | > 40% | 是（需确认提取的函数合理） |

#### 4.3.2 自动修复工作流

```bash
#!/bin/bash
# quality-fix.sh — 代码质量自动修复脚本

set -euo pipefail

echo "=== Code Quality Auto-Fix ==="

# Step 1: Run linter and capture output
echo "Running linter..."
golangci-lint run --output=json > /tmp/lint-report.json 2>/dev/null || true

# Step 2: Run type checker
echo "Running type check..."
go build ./... 2> /tmp/type-errors.txt || true

# Step 3: Analyze and fix with Claude Code
claude -p --max-turns 50 --max-budget-usd 5.00 \
  --permission-mode auto \
  "Fix code quality issues based on the following reports:
  - Lint report: /tmp/lint-report.json
  - Type errors: /tmp/type-errors.txt

  Rules:
  1. Fix lint warnings automatically (formatting, naming, unused imports)
  2. For type errors, diagnose and fix with minimal changes
  3. For complexity warnings, suggest refactoring but do not auto-fix
  4. Do NOT change test assertions
  5. Create a PR with all fixes

  Branch name: auto/quality-fix-$(date +%Y%m%d)"
```

### 4.4 Flaky Test 的自动识别和隔离

#### 4.4.1 Flaky Test 数据库

```yaml
# .flaky-tests.yml — Flaky Test 数据库
# AI 自修复时读取此文件，跳过已知的不稳定测试

flaky_tests:
  - name: TestConcurrentAccess
    package: pkg/lock
    reason: "Race condition with system time"
    flake_rate: 0.05  # 5% flake rate
    last_flaked: "2026-04-10"
    skip_until: "2026-05-01"  # Auto-skip until this date
    investigation_status: "scheduled"  # scheduled | in-progress | resolved

  - name: TestNetworkTimeout
    package: pkg/http
    reason: "External service latency variance"
    flake_rate: 0.03
    last_flaked: "2026-04-12"
    skip_until: null  # Do not skip, just flag
    investigation_status: "in-progress"

# Auto-coding rules:
# - If a test is in flaky_tests with skip_until in future, skip it
# - If a failing test matches a flaky entry, flag it but don't count as failure
# - AI must not modify flaky tests to "fix" flakiness
```

#### 4.4.2 Flaky Test 识别算法

```
Flaky Test 识别：
  1. 同一测试在连续 3 次 CI 运行中：通过 -> 失败 -> 通过
  2. 失败消息包含时序相关关键词（timeout, deadline, race, concurrent）
  3. 失败仅在特定环境下复现（本地通过，CI 失败）
  4. AI 修复尝试 3 轮后仍失败，且失败原因不确定

识别后的动作：
  1. 记录到 .flaky-tests.yml
  2. 在 CI 中标记但不阻塞合并（如果仅在 flaky 列表中出现）
  3. 创建 Issue 跟踪修复进度
  4. 通知人工安排根因分析
```

### 4.5 自修复的边界

#### 4.5.1 什么能修

| 类别 | 自动修复 | 示例 |
|------|---------|------|
| 格式问题 | 是 | 缩进、换行、空格 |
| 命名问题 | 是 | 未导出的变量名不符合规范 |
| 导入问题 | 是 | 缺失 import、未使用的 import |
| 类型错误 | 是（最小修改） | 缺少类型标注、类型不匹配 |
| Lint 警告 | 是 | 代码风格、未使用的变量 |
| 简单的测试失败 | 是（最多 3 轮） | Mock 配置错误、路径错误 |
| 依赖版本不兼容 | 是 | 更新 import path 适配新版本 |

#### 4.5.2 什么必须转人工

| 类别 | 原因 | 示例 |
|------|------|------|
| 安全漏洞 | 需要专业判断 | SQL 注入修复方案选择 |
| 架构问题 | 影响范围大 | 模块间循环依赖 |
| 数据迁移 | 不可逆操作 | 数据库 schema 变更 |
| 性能问题 | 需要基准测试 | 算法优化、索引调整 |
| 业务逻辑错误 | 需要产品确认 | 计费规则错误、权限逻辑 |
| Self-Correction > 3 轮 | AI 无法自主解决 | 复杂依赖的兼容性问题 |
| 影响 > 50 个文件 | 超出最小批量 | 全局重构 |
| 涉及密钥配置 | 安全敏感 | 认证配置修改 |

#### 4.5.3 边界检查实现

```bash
#!/bin/bash
# boundary-check.sh — 检查修复是否在自动修复边界内

set -euo pipefail

check_file_count() {
  local changed_files
  changed_files=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | wc -l)
  if [[ $changed_files -gt 50 ]]; then
    echo "BOUNDARY: Too many files changed ($changed_files > 50)"
    return 1
  fi
  return 0
}

check_forbidden_dirs() {
  local forbidden="database/migrations secrets config/production"
  for dir in $forbidden; do
    if git diff --name-only HEAD~1 HEAD | grep -q "^${dir}/"; then
      echo "BOUNDARY: Forbidden directory modified: $dir"
      return 1
    fi
  done
  return 0
}

check_security_changes() {
  # Check for authentication, authorization, encryption changes
  local diff_content
  diff_content=$(git diff HEAD~1 HEAD)
  if echo "$diff_content" | grep -qiE '(auth|permission|encrypt|decrypt|cipher|secret)'; then
    echo "BOUNDARY: Security-related change detected, requires human review"
    return 1
  fi
  return 0
}

# Run all checks
check_file_count && check_forbidden_dirs && check_security_changes
echo "PASS: Auto-fix within boundaries"
```

---

## 第 5 章：夜间/周末自主开发

### 5.1 模式 1：夜间特性工厂（给定 Spec -> 自主开发 -> 早晨审查）

#### 5.1.1 详细流程

```
┌──────────────────────────────────────────────────────────────┐
│                    夜间特性工厂 — 详细流程                     │
│                                                              │
│  [17:00 — 下班前]                                             │
│  Developer:                                                   │
│    1. 检查 specs/ 目录，确认哪些 Spec 标记为 ready            │
│    2. 按业务优先级排序（P1：商业驱动）                         │
│    3. 执行 DCP 快速确认（5 分钟，异步）                        │
│       - 商业目标是否明确？                                     │
│       - Spec 是否经过审核？                                   │
│       - 数据分级是否安全？                                    │
│    4. 启动夜间 Scheduled Task                                 │
│    5. 启用 Remote Control 到手机                              │
│    6. 设置 Kill Switch 参数                                   │
│                                                              │
│  [20:00 — 夜间运行开始]                                        │
│  Agent:                                                       │
│    循环执行（最多 3 个 Spec 或直到 06:00）：                   │
│      1. 从 specs/ 读取下一个 ready Spec                       │
│      2. 更新 Spec status 为 in-progress                       │
│      3. 执行 TDD-first 循环                                   │
│         a. 从 Gherkin AC 生成测试                             │
│         b. 验证测试失败（Red）                                │
│         c. 生成最小实现                                       │
│         d. 验证测试通过（Green）                              │
│         e. Self-Correct（如果失败，最多 3 轮）                │
│         f. 重构                                               │
│      4. AI Reviewer 幻觉检测                                  │
│      5. 创建 PR（包含完整追溯信息）                            │
│      6. 更新 Spec status 为 review-ready                      │
│                                                              │
│  [06:00 — 夜间运行结束]                                        │
│  Agent:                                                       │
│    - 停止运行                                                 │
│    - 发送完成通知到 Channel                                   │
│    - 保存状态到 .omc/state/                                   │
│                                                              │
│  [09:00 — 早晨审查]                                           │
│  Developer:                                                   │
│    1. 检查通知（是否有告警）                                   │
│    2. 逐条审查 PR                                             │
│       - AI Reviewer 报告                                     │
│       - 代码 diff                                             │
│       - 测试结果                                              │
│       - Spec 覆盖度                                           │
│    3. 合并通过的 PR                                           │
│    4. 对需要修改的 PR 给出反馈                                │
│    5. 更新 Spec status（completed / needs-revision）          │
│    6. 记录度量数据                                            │
└──────────────────────────────────────────────────────────────┘
```

#### 5.1.2 夜间运行配置

```json
{
  "nightly_feature_factory": {
    "schedule": "0 20 * * 1-5",
    "autonomy_level": "L3",
    "max_specs_per_night": 3,
    "max_hours": 10,
    "max_budget_usd": 25.00,
    "tdd_enforcement": true,
    "self_correction_max_rounds": 3,
    "auto_merge": false,
    "branch_prefix": "nightly/",
    "dcp_required": true,
    "notification": {
      "channel": "slack:#nightly-build",
      "on_start": true,
      "on_pr_created": true,
      "on_blocker": true,
      "on_complete": true
    },
    "kill_switch": {
      "max_files_per_pr": 50,
      "forbidden_dirs": ["database/migrations", "secrets"],
      "emergency_contact": "@tech-lead"
    }
  }
}
```

### 5.2 模式 2：周末 Hack 模式（多个 Spec -> 自主编排 -> 周一 Review）

#### 5.2.1 与夜间模式的区别

| 维度 | 夜间模式 | 周末 Hack 模式 |
|------|---------|---------------|
| 持续时间 | 10 小时（晚间到早晨） | 48 小时（周五到周一） |
| Spec 数量 | 1-3 个 | 3-10 个 |
| 任务类型 | 单一特性开发 | 特性 + 重构 + 修复 混合 |
| 编排方式 | 顺序执行 | Supervisor-Worker 并行 |
| 风险等级 | 中等 | 较高（长时间无人监督） |
| 适用自治等级 | L3 | L3+（要求更高的成熟度） |

#### 5.2.2 周末 Hack 详细流程

```
┌────────────────────────────────────────────────────────────────┐
│                     周末 Hack 模式 — 详细流程                    │
│                                                                │
│  [Friday 17:00 — 启动]                                          │
│  Developer:                                                     │
│    1. 编写 Project Brief（本周末要完成的目标）                   │
│    2. 确认 specs/ 中的任务队列                                   │
│       ├── F010: User profile page        [ready]               │
│       ├── F011: Notification system       [ready]               │
│       ├── F012: Search optimization       [ready]               │
│       ├── F013: Admin dashboard           [ready]               │
│       └── F014: Export to PDF             [backlog]             │
│    3. 执行完整 DCP 确认（15 分钟）                              │
│    4. 配置 Supervisor-Worker 编排（见第 6 章）                  │
│    5. 设置 Kill Switch 参数                                    │
│       ├── max_total_budget: $100.00                           │
│       ├── max_wall_clock: 48 hours                            │
│       ├── max_files_per_pr: 50                                │
│       └── forbidden_dirs: [migrations, secrets, production]    │
│    6. 启动周末自主开发                                          │
│                                                                │
│  [Saturday - Sunday — Agent 运行]                               │
│                                                                │
│  Saturday Morning:                                              │
│    Supervisor: 分析任务依赖关系                                 │
│      ├── F010 无依赖 -> Worker A 开始                         │
│      ├── F011 依赖 F010 -> 等待                               │
│      ├── F012 无依赖 -> Worker B 开始                         │
│      └── F013 依赖 F011 -> 等待                               │
│                                                                │
│  Saturday Afternoon:                                            │
│    Worker A: F010 完成 -> PR #101 创建                         │
│    Worker B: F012 完成 -> PR #102 创建                         │
│    Supervisor: 启动 F011 -> Worker A                          │
│                                                                │
│  Saturday Evening:                                              │
│    Worker A: F011 完成 -> PR #103 创建                         │
│    Supervisor: 启动 F013 -> Worker B                          │
│                                                                │
│  Sunday:                                                        │
│    Worker B: F013 完成 -> PR #104 创建                         │
│    Supervisor: 运行全量回归测试                                 │
│    Quality Check: 扫描全部 PR 的幻觉/安全问题                    │
│                                                                │
│  [Monday 09:00 — 审查]                                          │
│  Developer:                                                     │
│    1. 审查 4 个 PR（批量审查，约 2 小时）                        │
│    2. 合并通过的 PR                                             │
│    3. 对需要修改的 PR 给出反馈                                   │
│    4. 记录周末自主开发度量数据                                   │
└────────────────────────────────────────────────────────────────┘
```

### 5.3 模式 3：自修复 + 特性开发混合

#### 5.3.1 架构

```
┌─────────────────────────────────────────────────────────────┐
│              自修复 + 特性开发混合模式                         │
│                                                             │
│  ┌──────────────────┐      ┌──────────────────┐             │
│  │   CI 监控 Agent   │      │  特性开发 Agent   │             │
│  │   (每 15 分钟)    │      │  (持续运行)       │             │
│  └────────┬─────────┘      └────────┬─────────┘             │
│           │                          │                       │
│           ▼                          ▼                       │
│  ┌──────────────────┐      ┌──────────────────┐             │
│  │ CI 状态检查       │      │ Spec 队列处理     │             │
│  │                   │      │                  │             │
│  │ 失败? ──▶ 自修复  │      │ ready? ──▶ 开发  │             │
│  │ 成功? ──▶ 继续    │      │ blocked? ──▶ 跳过│             │
│  └──────────────────┘      └──────────────────┘             │
│           │                          │                       │
│           └──────────┬───────────────┘                       │
│                      ▼                                       │
│              ┌───────────────┐                               │
│              │ 冲突仲裁       │                               │
│              │ (两个 Agent    │                               │
│              │  可能修改同一  │                               │
│              │   个文件)      │                               │
│              └───────────────┘                               │
│                      │                                       │
│                      ▼                                       │
│              ┌───────────────┐                               │
│              │ PR 队列        │                               │
│              │ (等待早晨审查)  │                               │
│              └───────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

**冲突仲裁策略**：
1. 自修复 Agent 优先（CI 失败阻塞特性开发）
2. 特性开发 Agent 在自修复完成后继续
3. 如果修改同一文件，后运行的 Agent 必须在 PR 中合并冲突

### 5.4 前置条件检查清单

```markdown
## 夜间/周末自主开发 — 完整前置检查清单

### 必须项（不满足则不得启动）

#### DCP 门禁（v5 P2）
- [ ] P1 商业驱动：本批次的商业目标已定义并文档化
- [ ] P2 DCP Go：决策门检查通过（Phase 3 入口标准满足）
- [ ] P7 Spec 驱动：所有待开发任务有明确的 Spec 文件
- [ ] P9 Prompt 版本化：使用的 Prompt 版本已记录

#### 安全保障
- [ ] P5 密钥不入代码：pre-commit hook 已启用
- [ ] P10 数据分级：pre-send 扫描已配置，Restricted 数据拦截
- [ ] 分支保护：main 分支不可直接推送
- [ ] Kill Switch：参数已设置（时间、成本、文件数）

#### 质量保障
- [ ] P3 TDD 先行：CI Gate 已配置 TDD 合规检查
- [ ] P4 人工审查：审查人/流程已指定（早晨审查计划）
- [ ] P8 最小批量：CI 强制验证函数/文件大小
- [ ] 测试覆盖率 >= 80%

#### 基础设施
- [ ] 通知 Channel 已配置并测试
- [ ] Remote Control 已启用
- [ ] 状态持久化路径已验证（.omc/state/ 可写）
- [ ] 定时任务已测试（运行一个空跑验证配置）

### 推荐项（建议满足）

- [ ] L2 稳定运行 >= 1 个月
- [ ] 自主成功率 >= 70%
- [ ] 幻觉发生率 < 5%
- [ ] Self-Correction 成功率 >= 60%
- [ ] Flaky Test 数据库已更新
- [ ] 紧急联系人已指定
```

### 5.5 执行过程监控

#### 5.5.1 监控仪表板

```
┌─────────────────────────────────────────────────────────────┐
│               自主开发监控仪表板（Remote Control 查看）         │
│                                                             │
│  当前状态: 运行中                                             │
│  已运行时间: 4h 23m                                          │
│  已处理 Spec: 2/5                                            │
│  已创建 PR: 2                                                │
│  当前成本: $12.45 / $25.00 (49.8%)                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Spec 进度                                            │    │
│  │ F001: ✅ completed -> PR #101                        │    │
│  │ F002: ✅ completed -> PR #102                        │    │
│  │ F003: 🔄 in-progress (implementing, iteration 8)     │    │
│  │ F004: ⏳ waiting                                     │    │
│  │ F005: ⏳ waiting                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 质量指标                                             │    │
│  │ TDD Compliance: ✅ Red->Green verified               │    │
│  │ Test Coverage: 84.2%                                │    │
│  │ Lint Warnings: 0 new                                │    │
│  │ AI Review: ✅ passed (0 critical, 2 warnings)        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Kill Switch 状态                                      │    │
│  │ Time: 4h23m / 10h (43.8%)     ✅ OK                 │    │
│  │ Cost: $12.45 / $25.00 (49.8%)  ✅ OK                │    │
│  │ Files: 23 / 50 per PR         ✅ OK                 │    │
│  │ Forbidden Dirs: 0 violations  ✅ OK                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  [干预按钮] [发送消息] [暂停] [紧急停止]                      │
└─────────────────────────────────────────────────────────────┘
```

### 5.6 结果审查指南

#### 5.6.1 PR 审查清单

```markdown
## 自主开发 PR 审查清单

### 基础检查
- [ ] CI 全部通过（构建、测试、lint、SAST）
- [ ] TDD 合规（测试先于实现，Red -> Green 记录）
- [ ] 分支从正确的基准创建

### Spec 覆盖度
- [ ] 所有 AC（Acceptance Criteria）都有对应测试
- [ ] 异常路径测试已覆盖（不仅是正常路径）
- [ ] 技术约束已满足（Spec 中的技术要求）

### 代码质量
- [ ] 无幻觉代码（不存在的 API、虚构的函数名）
- [ ] 无密钥泄露（硬编码密码、token）
- [ ] 函数长度符合 P8（单函数 <= 50 行）
- [ ] 匹配现有代码模式（命名、导入、错误处理）
- [ ] 无临时/调试代码（console.log、TODO、HACK、debugger）

### 安全
- [ ] 无 SQL 注入风险
- [ ] 无 XSS 风险
- [ ] 无路径遍历风险
- [ ] 认证/授权逻辑正确

### 合并决策
- [ ] 通过 -> 合并
- [ ] 需要小修 -> 评论并要求修改
- [ ] 需要大修 -> 拒绝 PR，转人工开发
```

#### 5.6.2 审查反馈模板

```markdown
## PR Review — {PR Number}: {Title}

### Reviewer: {Name}
### Date: {Date}
### Autonomy Level: L3

### Verdict: [APPROVE | REQUEST CHANGES | REJECT]

### Summary
{简要描述审查结果}

### Findings
| # | Severity | File:Line | Description | Action |
|---|----------|-----------|-------------|--------|
| 1 | Critical | src/auth.go:42 | Potential SQL injection | Must fix |
| 2 | Warning | tests/user_test.go:15 | Missing edge case test | Should fix |
| 3 | Info | src/user.go:88 | Could use early return | Suggestion |

### TDD Verification
- Red phase: ✅ confirmed (commit abc1234)
- Green phase: ✅ confirmed (commit def5678)
- Self-Correction rounds: 1

### AI Review Cross-Check
- Hallucination check: ✅ passed
- Secret scan: ✅ passed
- Security scan: ❌ 1 critical finding (see #1)

### Notes for Autonomous Process Improvement
{反馈给自主编码流程的改进建议}
```

---

## 第 6 章：Supervisor-Worker 自动编排

### 6.1 Supervisor 角色定义

#### 6.1.1 职责

Supervisor 是自动编排的核心，负责：
1. **需求分析**：理解 Spec 集合，识别依赖关系
2. **任务拆分**：将大任务拆分为可并行执行的子任务
3. **任务分发**：将子任务分配给合适的 Worker
4. **进度跟踪**：监控每个 Worker 的执行状态
5. **冲突仲裁**：处理多 Worker 修改同一文件的情况
6. **质量判断**：在汇总阶段判断整体质量是否达标
7. **异常处理**：Worker 失败时的重试或转人工

#### 6.1.2 模型要求

| 属性 | 要求 | 原因 |
|------|------|------|
| 模型 | Opus（或等效强模型） | 需要理解力、判断力、规划能力 |
| 上下文窗口 | 大（>= 200K tokens） | 需要同时理解多个 Spec 和整个代码库 |
| 工具访问 | 全部（读、写、执行、Git） | 需要全面的项目掌控能力 |
| 权限模式 | auto | 需要自动执行编排决策 |

#### 6.1.3 Supervisor Agent 配置

```markdown
---
name: supervisor
description: Orchestrates multi-agent coding tasks. Analyzes dependencies, splits work, assigns to workers, and validates results.
tools: Read, Grep, Glob, Bash, Edit, Write
model: opus
permissionMode: auto
maxTurns: 500
memory: project
---

You are a Supervisor Agent responsible for orchestrating autonomous coding tasks.

## Responsibilities
1. Analyze specs/ directory to understand the task queue
2. Build a dependency graph between tasks
3. Split tasks into atomic sub-tasks suitable for parallel execution
4. Assign sub-tasks to Worker agents based on complexity
5. Monitor Worker progress and handle failures
6. Merge results and resolve conflicts
7. Run final quality validation before creating PRs

## Decision Rules
- If a task depends on another, wait for the dependency to complete
- If a Worker fails after 3 retries, mark the task as blocked and continue
- If a conflict occurs (two Workers modify same file), resolve it in the merge step
- If cost exceeds budget, stop and report

## Quality Gates
Before marking a task as complete:
- All tests pass
- No new lint warnings
- TDD compliance verified
- AI Review passed (no critical hallucinations)
```

### 6.2 Worker 角色定义

#### 6.2.1 职责

Worker 是执行具体编码任务的 Agent：
1. **理解分配的任务**：读取 Spec 和上下文
2. **执行 TDD-first 循环**：生成测试 -> Red -> 实现 -> Green
3. **Self-Correction**：修复失败（最多 3 轮）
4. **报告进度**：向 Supervisor 汇报状态
5. **产出 PR**：完成任务后创建 PR

#### 6.2.2 模型要求

| 属性 | 要求 | 原因 |
|------|------|------|
| 模型 | Sonnet（或等效中等模型） | 执行具体任务，性价比高 |
| 上下文窗口 | 中等（>= 128K tokens） | 需要理解任务涉及的文件 |
| 工具访问 | 全部（读、写、执行、Git） | 需要完整的编码能力 |
| 权限模式 | auto | 需要自主执行 |

#### 6.2.3 Worker Agent 配置模板

```markdown
---
name: worker-frontend
description: Implements frontend coding tasks. Creates React components, styles, and tests.
tools: Read, Grep, Glob, Bash, Edit, Write
model: sonnet
permissionMode: auto
maxTurns: 100
---

You are a Frontend Worker Agent.

When assigned a task:
1. Read the spec file to understand requirements
2. Explore existing components to match patterns
3. Generate tests first (TDD)
4. Implement the component
5. Run tests and fix failures (max 3 self-correction rounds)
6. Create a PR with the changes

Coding conventions:
- Follow existing patterns in the codebase
- Use TypeScript strictly
- Write unit tests for each component
- Keep components under 200 lines
```

```markdown
---
name: worker-backend
description: Implements backend coding tasks. Creates API endpoints, services, and tests.
tools: Read, Grep, Glob, Bash, Edit, Write
model: sonnet
permissionMode: auto
maxTurns: 100
---

You are a Backend Worker Agent.

When assigned a task:
1. Read the spec file to understand requirements
2. Explore existing API patterns and service layers
3. Generate tests first (TDD)
4. Implement the endpoint/service
5. Run tests and fix failures (max 3 self-correction rounds)
6. Create a PR with the changes

Coding conventions:
- Follow existing patterns in the codebase
- Use proper error handling
- Write integration tests for each endpoint
- Keep functions under 50 lines
```

### 6.3 编排流程

#### 6.3.1 完整编排流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    Supervisor-Worker 编排流程                     │
│                                                                 │
│  Phase 1: 需求分析                                               │
│  ┌─────────────┐                                                │
│  │ Supervisor  │                                                │
│  │ - 读取全部   │                                                │
│  │   ready Spec │                                                │
│  │ - 理解业务    │                                                │
│  │   目标       │                                                │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  Phase 2: 任务拆分                                               │
│  ┌─────────────┐                                                │
│  │ Supervisor  │                                                │
│  │ - 构建依赖   │                                                │
│  │   关系图     │                                                │
│  │ - 拆分为      │                                                │
│  │   原子任务    │                                                │
│  │ - 标注       │                                                │
│  │   复杂度      │                                                │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  Phase 3: 分发                                                   │
│  ┌─────────────┐    ┌─────────┐   ┌─────────┐   ┌─────────┐    │
│  │ Supervisor  │───▶│ Worker A│   │ Worker B│   │ Worker C│    │
│  │ - 按依赖    │    │ Task 1  │   │ Task 2  │   │ Task 3  │    │
│  │   顺序分发   │    │ (无依赖) │   │ (无依赖) │   │ (依赖1) │    │
│  └─────────────┘    └────┬────┘   └────┬────┘   └────┬────┘    │
│                          │             │             │          │
│                          ▼             ▼             ▼          │
│  Phase 4: 并行执行                                                │
│  ┌─────────────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐  │
│  │ 时间线           │ │ Worker A│ │ Worker B│ │ 等待依赖解决  │  │
│  │                 │ │ TDD 循环│ │ TDD 循环│ │               │  │
│  │ t=0 ───▶        │ │ PR #1   │ │ PR #2   │ │               │  │
│  │ t=1 ───▶        │ │ 完成    │ │ 完成    │ │ Worker C 启动 │  │
│  │ t=2 ───▶        │ │         │ │         │ │ TDD 循环     │  │
│  │                 │ │         │ │         │ │ PR #3        │  │
│  └─────────────────┘ └─────────┘ └─────────┘ └──────────────┘  │
│                          │             │             │          │
│                          └─────────────┴─────────────┘          │
│                                    │                             │
│                                    ▼                             │
│  Phase 5: 汇总                                                   │
│  ┌─────────────┐                                                │
│  │ Supervisor  │                                                │
│  │ - 收集所有   │                                                │
│  │   PR         │                                                │
│  │ - 运行       │                                                │
│  │   集成测试    │                                                │
│  │ - 检查       │                                                │
│  │   冲突        │                                                │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  Phase 6: 质量判断                                               │
│  ┌─────────────┐                                                │
│  │ Supervisor  │                                                │
│  │ - 全量测试   │                                                │
│  │   通过？     │                                                │
│  │ - 幻觉扫描    │                                                │
│  │ - 安全检查    │                                                │
│  │ - 生成       │                                                │
│  │   汇总报告    │                                                │
│  └─────────────┘                                                │
└─────────────────────────────────────────────────────────────────┘
```

#### 6.3.2 依赖关系图构建

```
Supervisor 构建依赖关系图的算法：

1. 读取所有 ready Spec
2. 对每个 Spec，解析其 Dependencies 字段
3. 构建有向图：Spec A -> Spec B 表示 A 依赖 B
4. 检测循环依赖 -> 报错并转人工
5. 拓扑排序 -> 得到执行顺序
6. 识别可并行的任务组（同层无依赖关系的任务）

示例：
  F001 (user registration) -> 无依赖 -> Layer 0
  F002 (user login) -> 依赖 F001 -> Layer 1
  F003 (password reset) -> 依赖 F001 -> Layer 1
  F004 (user profile) -> 依赖 F001, F002 -> Layer 2
  F005 (notification) -> 依赖 F004 -> Layer 3

执行顺序：
  Layer 0: [F001] — Worker A
  Layer 1: [F002, F003] — Worker A, Worker B (并行)
  Layer 2: [F004] — Worker A (等待 Layer 1 完成)
  Layer 3: [F005] — Worker B (等待 Layer 2 完成)
```

### 6.4 Agent Teams 模式

#### 6.4.1 使用 Claude Code Agent Teams

```bash
# 创建团队
TeamCreate(team_name="weekend-hack-sprint12", description="Weekend autonomous development sprint")

# 创建任务列表
TaskCreate(subject="Implement F001: User Registration", description="Spec at specs/F001-user-registration.md")
TaskCreate(subject="Implement F002: User Login", description="Spec at specs/F002-user-login.md")
TaskCreate(subject="Implement F003: Password Reset", description="Spec at specs/F003-password-reset.md")

# 设置依赖关系
TaskUpdate(taskId="2", addBlockedBy=["1"])  # F002 depends on F001
TaskUpdate(taskId="3", addBlockedBy=["1"])  # F003 depends on F001

# 启动团队成员
Agent(name="worker-auth-frontend", subagent_type="general-purpose", team_name="weekend-hack-sprint12")
Agent(name="worker-auth-backend", subagent_type="general-purpose", team_name="weekend-hack-sprint12")
Agent(name="worker-tester", subagent_type="general-purpose", team_name="weekend-hack-sprint12")

# Supervisor 分配任务
TaskUpdate(taskId="1", owner="worker-auth-backend")
```

#### 6.4.2 团队成员通信

```
Team Lead (Supervisor) ──Message──> Worker
  "开始实现 F001，注意使用现有的 middleware 模式"

Worker ──Message──> Team Lead
  "F001 完成，PR #101 已创建。发现一个模式不一致的地方，已修复。"

Team Lead ──Message──> Team Lead
  （内部决策）"F002 和 F003 现在可以并行启动了"

Team Lead ──Message──> Worker A
  "开始实现 F002"

Team Lead ──Message──> Worker B
  "开始实现 F003"
```

### 6.5 超时和失败处理

#### 6.5.1 超时策略

```
超时处理层级：

Worker 级别：
  - 单任务 max_turns: 100
  - 单任务 max_budget: $5.00
  - 单任务 timeout: 2 小时
  - 达到限制 -> 标记为 blocked，通知 Supervisor

Supervisor 级别：
  - 总任务 max_turns: 500
  - 总预算 max_budget: $50.00
  - 总 timeout: 10 小时
  - 达到限制 -> 停止编排，保存状态，发送告警

Kill Switch 级别：
  - 检测到安全事件 -> 立即终止全部 Agent
  - 检测到密钥泄露 -> 立即终止 + 回滚
  - 检测到 Forbidden 目录修改 -> 立即终止
```

#### 6.5.2 失败重试策略

```
Worker 失败处理：

1. 首次失败：
   - Self-Correction Round 1
   - AI 自行诊断并修复

2. 第二次失败：
   - Self-Correction Round 2
   - 扩大上下文，读取更多相关文件

3. 第三次失败：
   - Self-Correction Round 3
   - 尝试替代方案

4. 超过 3 轮仍失败：
   - Worker 向 Supervisor 报告失败
   - Supervisor 尝试以下策略：
     a. 重试一次（使用不同的 Worker 模型，如 haiku -> sonnet）
     b. 重新拆分任务（拆分为更小的子任务）
     c. 标记为 blocked，跳过该任务
   - 全部重试失败 -> 创建 Issue，通知人工
```

#### 6.5.3 冲突解决

```
多 Worker 修改同一文件的冲突解决：

1. 预防策略：
   - Supervisor 在任务拆分时避免分配重叠的文件范围
   - 每个 Worker 声明其将要修改的文件列表
   - Supervisor 检查冲突并重新分配

2. 检测策略：
   - 在汇总阶段，Supervisor 检查所有 Worker 的 git diff
   - 识别被多个 Worker 修改的文件

3. 解决策略：
   - 自动合并（如果修改在不同行，git merge 无冲突）
   - 手动解决（Supervisor 尝试 git merge，解决冲突）
   - 转人工（Supervisor 无法解决时，创建 Issue 并通知）
```

---

## 第 7 章：Auto-Coding 度量

### 7.1 自主成功率计算

#### 7.1.1 定义

自主成功率 = 无需人工干预即通过审查的 PR 数 / 总 PR 数

```
自主成功率 = (PRs passed on first review) / (Total PRs created) × 100%
```

#### 7.1.2 计算示例

```
本周数据：
  - AI 创建 PR 总数：20
  - 第一次审查即通过的 PR：14
  - 需要修改后通过的 PR：5
  - 被拒绝的 PR：1

自主成功率 = 14 / 20 × 100% = 70%

解读：
  - 70% = L3 升级阈值（>= 70%）— 处于临界状态
  - 5 个需要修改的 PR 表明自修循环或 AI Reviewer 需要优化
  - 1 个被拒绝的 PR 需要根因分析
```

#### 7.1.3 按任务类型细分

| 任务类型 | PR 数 | 一次通过 | 成功率 | 趋势 |
|---------|-------|---------|--------|------|
| CRUD 端点 | 8 | 7 | 87.5% | ↑ |
| UI 组件 | 5 | 3 | 60.0% | ↓ |
| 测试生成 | 4 | 4 | 100% | — |
| 重构 | 2 | 0 | 0% | ↓ |
| CI 修复 | 1 | 0 | 0% | — |

**洞察**：UI 组件和重构的成功率较低，说明 AI 在视觉/架构理解方面需要加强。

### 7.2 人工干预率

#### 7.2.1 定义

人工干预率 = 需要人工介入的任务数 / 总任务数

```
人工干预率 = (Tasks requiring human intervention) / (Total tasks) × 100%
```

#### 7.2.2 干预原因分类

| 原因 | 次数 | 占比 | 改进方向 |
|------|------|------|---------|
| Self-Correction > 3 轮 | 5 | 35.7% | 增强诊断能力 |
| 架构决策需要判断 | 3 | 21.4% | 丰富架构知识库 |
| 安全相关变更 | 2 | 14.3% | 增加安全模式检查 |
| Spec 不清晰 | 2 | 14.3% | 改进 Spec 模板 |
| 依赖冲突 | 1 | 7.1% | 优化依赖解析 |
| 工具不可用 | 1 | 7.1% | 检查环境配置 |

### 7.3 质量指标

#### 7.3.1 Lint 通过率

```
Lint 通过率 = (无新增 lint 警告的 PR 数) / (总 PR 数) × 100%

目标：>= 95%
当前：92%（2 个 PR 引入了新警告）
```

#### 7.3.2 测试覆盖率

```
测试覆盖率 = (被测试覆盖的代码行) / (总代码行) × 100%

目标：>= 80%
当前：84.2%

覆盖率趋势：
  Week 12: 84.2% ↑
  Week 11: 82.1% ↑
  Week 10: 79.8% ↑
  Week 9:  78.5%
```

#### 7.3.3 幻觉率

```
幻觉率 = (包含幻觉代码的 PR 数) / (总 PR 数) × 100%

幻觉代码定义：
  - 调用了不存在的 API 或函数
  - 虚构的第三方库方法
  - 错误的参数签名
  - 不符合项目约定的模式

目标：< 5%
当前：3.2%

幻觉类型分布：
  - 虚构 API 调用：60%
  - 错误参数签名：25%
  - 不符合项目约定：15%
```

#### 7.3.4 TDD 合规率

```
TDD 合规率 = (遵循 TDD 流程的 PR 数) / (总 PR 数) × 100%

目标：>= 80%（L2 升级条件）
当前：88%

TDD 违规类型：
  - 测试和实现在同一 commit：8%
  - 缺少 Red 阶段记录：3%
  - 测试覆盖率不足：1%
```

### 7.4 成本指标

#### 7.4.1 单次 PR 成本

```
平均单次 PR 成本 = 总 API 成本 / PR 总数

本周：
  总 API 成本：$127.50
  PR 总数：20
  平均单次 PR 成本：$6.38

按任务类型：
  CRUD 端点：$4.20/PR
  UI 组件：$8.90/PR
  测试生成：$3.10/PR
  重构：$12.50/PR
  CI 修复：$2.80/PR
```

#### 7.4.2 成本趋势

```
每周 AI 编码成本趋势：

  Week 12: $127.50 ↑ (20 PRs)
  Week 11: $98.20  ↑ (15 PRs)
  Week 10: $85.00  ↑ (12 PRs)
  Week 9:  $72.40  — (12 PRs)
  Week 8:  $68.10  — (11 PRs)

解读：成本随 PR 数量增长，但单次 PR 成本在下降（$6.38 vs $8.05），
说明效率在提升。
```

#### 7.4.3 成本效率比

```
成本效率比 = 人工时间节省 / AI 成本

本周：
  人工时间节省：约 45 小时（vs 纯人工开发）
  人工时薪：$75/小时
  节省价值：45 × $75 = $3,375
  AI 成本：$127.50
  ROI：$3,375 / $127.50 = 26.5x
```

### 7.5 趋势分析和预警

#### 7.5.1 自动预警规则

```yaml
# auto-coding-alerts.yml — 自动预警配置
alerts:
  - name: autonomy-degradation
    condition: "autonomy_success_rate < 70% for 2 consecutive weeks"
    action: "downgrade L3 -> L2"
    notify: ["tech-lead", "architect"]

  - name: hallucination-spike
    condition: "hallucination_rate > 10% in any week"
    action: "pause autonomous runs, investigate"
    notify: ["tech-lead", "security"]

  - name: cost-overrun
    condition: "weekly_cost > budget * 1.5"
    action: "reduce max_budget_usd for next week"
    notify: ["tech-lead", "finance"]

  - name: tdd-violation
    condition: "tdd_compliance_rate < 80%"
    action: "downgrade to L1 until recovery"
    notify: ["tech-lead"]

  - name: security-breach
    condition: "any secret detected in code"
    action: "emergency shutdown, rollback, incident response"
    notify: ["tech-lead", "security", "ciso"]

  - name: self-healing-failure
    condition: "self_correction_success_rate < 30% for 3 consecutive runs"
    action: "pause auto-correction, notify human"
    notify: ["tech-lead"]
```

#### 7.5.2 度量报告模板

```markdown
# Auto-Coding 周报 — Week 12 (2026-04-07 to 2026-04-13)

## 执行摘要
- 自主成功率：70%（↑ 2% vs 上周）
- 人工干预率：30%（↓ 2%）
- 幻觉率：3.2%（↓ 0.8%）
- TDD 合规率：88%（↑ 3%）
- 总成本：$127.50（ROI 26.5x）

## PR 统计
| 状态 | 数量 | 占比 |
|------|------|------|
| 一次通过 | 14 | 70% |
| 修改后通过 | 5 | 25% |
| 被拒绝 | 1 | 5% |

## 自治等级状态
- 当前等级：L3
- 升级条件（L3 -> L4）：
  - 自主成功率：70% < 85% ❌
  - 审计通过率：N/A（尚未运行 3 个月）
  - 零安全事故：✅
  - 结论：暂不满足升级条件

## 降级检查
- 生产安全事故：无 ✅
- 幻觉代码合并：无 ✅
- 审计通过率：N/A ✅
- 自主成功率连续低于 70%：否 ✅
- TDD 执行率：88% >= 80% ✅
- 密钥泄露：无 ✅
- 结论：无需降级

## 改进建议
1. UI 组件成功率低（60%），建议添加前端模式示例到 CLAUDE.md
2. 重构成功率低（0%），建议限制自主重构的范围
3. Self-Correction > 3 轮是最多的人工干预原因，建议增强诊断能力

## 下周计划
- 继续 L3 自主开发
- 重点优化 UI 组件的 Prompt 模板
- 目标：自主成功率 >= 75%
```

---

## 第 8 章：v4 合规注释

### 8.1 每条 v4 核心原则在本实践中的执行方式

#### P1 — 商业驱动

| 维度 | v4 要求 | 本实践中的执行方式 |
|------|---------|-------------------|
| **定义** | 所有开发活动必须有明确的商业目标 | 夜间/周末开发前，DCP 确认商业目标已定义并文档化 |
| **Auto-Coding 含义** | AI 可以 24/7 编码，但必须有人定义"值得做什么" | Spec 文件中的 Priority 字段由人工设置，AI 仅按优先级执行，不自定义优先级 |
| **检查点** | PR 被拒绝 | CI 检查 PR 是否关联了有商业目标的 Spec（通过 label 或 metadata） |
| **合规证据** | PR 描述中包含 Spec 路径和商业目标摘要 | |

#### P2 — DCP 门禁

| 维度 | v4 要求 | 本实践中的执行方式 |
|------|---------|-------------------|
| **定义** | 每个阶段必须通过决策门才能进入下一阶段 | L3/L4 夜间开发前，必须完成 DCP Go 确认（异步执行） |
| **Auto-Coding 含义** | Auto-Coding 模式下，DCP 可以异步执行但不得跳过 | `.gate/dcp-go.confirmed` 文件存在是启动自主运行的前置条件 |
| **检查点** | 阻塞进入下一阶段 | `spec-runner.sh` 脚本在启动前检查 DCP 确认文件 |
| **合规证据** | `.gate/dcp-checklist.json` 中记录了 DCP 确认的时间和确认人 | |

#### P3 — TDD 先行

| 维度 | v4 要求 | 本实践中的执行方式 |
|------|---------|-------------------|
| **定义** | AI 生成实现前必须先有测试，且测试必须先失败 | 所有 Auto-Coding 模式严格遵循 TDD-first：生成测试 -> 验证 Red -> 实现 -> 验证 Green |
| **Auto-Coding 含义** | L3/L4 下 AI 自动执行完整 TDD 循环，CI 必须记录 Red 状态 | CI Gate 强制检查提交顺序、Red 状态、Red->Green 转换；禁止 TDD 造假 |
| **检查点** | 阻塞合并 | CI 自动检测：git log 提交顺序、`.gate/tdd-report.json` 存在、Red 状态记录 |
| **合规证据** | TDD 造假检测：测试和实现不得在同一 commit 中 | |

#### P4 — 人工审查

| 维度 | v4 要求 | 本实践中的执行方式 |
|------|---------|-------------------|
| **定义** | 所有 AI 生成的代码必须经过人工 Code Review 才能合并 | L1-L3：每个 PR 合并前必须有人工审查；L4：定期审计替代逐 PR 审查 |
| **Auto-Coding 含义** | L4 仅 trivial fix 可自动合并，其他仍需人工审查 | 自动合并严格限制为：lint fix、format、typo in comments、dependency patch update |
| **检查点** | 阻塞合并 | 分支保护规则：main 需要 PR review 才能合并；L4 下 trivial fix 除外 |
| **合规证据** | 两层审查：AI Reviewer（幻觉检测）+ Human Reviewer（业务逻辑） | |

#### P5 — 密钥不入代码

| 维度 | v4 要求 | 本实践中的执行方式 |
|------|---------|-------------------|
| **定义** | 任何密钥、密码、token 不得出现在代码或配置文件中 | pre-commit hook（gitleaks）+ SAST + CI 自动扫描三重拦截 |
| **Auto-Coding 含义** | AI 倾向于从上下文复制密钥到代码中，必须自动化拦截 | Kill Switch 检测到密钥提交时立即停止 + 回滚 + 告警 |
| **检查点** | 阻断 + pre-commit 拦截（L1）/ SAST 拦截（L2）/ 自动安全事件（L3）/ 降级到 L1（L4） | |
| **合规证据** | pre-commit hook 日志、SAST 报告、Kill Switch 日志 | |

#### P6 — 单一信息源

| 维度 | v4 要求 | 本实践中的执行方式 |
|------|---------|-------------------|
| **定义** | 每个事实只在一个地方定义，其他地方引用 | L3/L4：AI 自动检测文档/代码漂移 |
| **Auto-Coding 含义** | 过时的文档 = AI 按旧信息编码 | 定期运行文档一致性检查（AI Reviewer 比对代码与文档） |
| **检查点** | L3：AI 自动检测漂移，人工确认；L4：自动漂移检测（>20% 触发回归） | |
| **合规证据** | `.gate/doc-drift-report.json` 记录漂移检测时间和漂移内容 | |

#### P7 — Spec 驱动

| 维度 | v4 要求 | 本实践中的执行方式 |
|------|---------|-------------------|
| **定义** | AI 生成代码必须有明确的 Spec 文件作为输入 | 所有 Auto-Coding 模式从 `specs/` 目录读取任务 |
| **Auto-Coding 含义** | L3/L4 下 Agent 直接从 specs/ 读取任务队列自动执行 | Spec Validation Gate 在执行前验证 Spec 格式、AC 可解析性、依赖关系 |
| **检查点** | 不得开始开发（无 Spec 时） | `spec-runner.sh` 仅处理 `status: ready` 的 Spec |
| **合规证据** | 每个 PR 描述中包含 Spec 文件路径和版本 | |

#### P8 — 最小批量

| 维度 | v4 要求 | 本实践中的执行方式 |
|------|---------|-------------------|
| **定义** | AI 一次只生成一个函数或小模块的代码 | 超过 50 行的函数或 200 行的文件必须拆分 |
| **Auto-Coding 含义** | 批量越大，幻觉概率越高 | CI 验证函数/文件大小；Supervisor 在任务拆分时确保原子粒度 |
| **检查点** | CI 阻塞合并 | CI 检查：单函数行数 <= 50，单文件行数 <= 200（可配置） |
| **合规证据** | 圈复杂度报告、函数长度统计 | |

#### P9 — Prompt 版本化

| 维度 | v4 要求 | 本实践中的执行方式 |
|------|---------|-------------------|
| **定义** | 用于生成代码的 Prompt 必须版本化并可追溯 | Prompt 文件存放在 `prompts/v{version}/` 目录，符号链接指向当前版本 |
| **Auto-Coding 含义** | L3/L4 下 Prompt 必须自动持久化到 prompts/，每个 PR 声明版本 | 动态构建的 Prompt（如 Spec 解析生成的 Prompt）在使用前持久化并自动递增版本号 |
| **检查点** | 自动持久化 | PR 描述中必须包含使用的 Prompt 版本、模型、参数 |
| **合规证据** | `.gate/prompt-chain-trace.json` 记录每个阶段的 Prompt 版本 | |

#### P10 — 数据分级

| 维度 | v4 要求 | 本实践中的执行方式 |
|------|---------|-------------------|
| **定义** | 发送给 AI 的数据必须经过分类，敏感数据禁止发送 | pre-send 扫描自动拦截 Restricted 级别数据 |
| **Auto-Coding 含义** | AI 不知情 = 人不负责 = 泄露发生 | Kill Switch 检测到 Restricted 数据发送时立即停止 + 回滚 |
| **检查点** | pre-send 扫描 + 审计日志（L3）/ 定期数据安全审计（L4） | |
| **合规证据** | pre-send 扫描日志、审计报告中记录 | |

### 8.2 与 v4 的冲突已解决说明

以下冲突基于 [conflict-analysis-v4-vs-auto-coding.md](../auto-coding/conflict-analysis-v4-vs-auto-coding.md) 的分析结果，全部已在本实践中解决：

#### BLOCKING 冲突（3 个，全部已解决）

**冲突 1 — TDD 强制**
- **问题**：v4 P3 要求 Red->Green 强制，但 auto-coding 知识库中持续循环为"实现->测试->诊断->修复"
- **解决**：本实践第 2 章所有 Auto-Coding 模式重排为 TDD-first 顺序：`[生成测试] -> [验证 Red] -> [实现] -> [验证 Green]`。CI Gate 强制验证。

**冲突 2 — 人工审查**
- **问题**：v4 P4 要求人工审查强制，但 auto-coding 知识库中 PR 审查为"可选"
- **解决**：本实践中 L1-L3 每个 PR 合并前必须有人工审查。L4 仅 trivial fix 可自动合并（严格定义），其他变更仍需人工审查。移除"可选"概念。

**冲突 3 — MCP 安全边界**
- **问题**：v4 P5/P10 要求数据分类过滤，但 MCP Agent 直连数据库可能暴露敏感数据
- **解决**：本实践第 3 章定时任务配置中包含数据分级检查。MCP Agent 访问数据库前必须经过脱敏过滤层。

#### WARNING 冲突（5 个，全部已解决）

| # | 冲突 | 解决方式 |
|---|------|---------|
| 4 | DCP 门禁 vs 持续交付 | 持续循环前加 Phase Gate Verification（第 5 章前置检查清单） |
| 5 | Spec 驱动 vs 自主选取 | Agent 必须从 `specs/` 读取任务，执行前加 Spec Validation Gate（第 2.2 节） |
| 6 | Prompt 版本化 | 动态构建的 Prompt 在使用前持久化到 `prompts/` 并自动递增版本号（第 2.3 节） |
| 7 | 两层 AI 审查 | 明确 Claude 自动审查 = Layer 1（AI Reviewer），Layer 2（人工）仍然强制（第 2.1 节） |
| 8 | bypassPermissions | 仅在沙箱/隔离 CI 环境中有效，生产环境禁用（第 3 章 Kill Switch） |

#### MINOR 冲突（4 个，全部已澄清）

| # | 冲突 | 澄清 |
|---|------|------|
| 9 | 最小批量 vs 多特性 | P8 是每次生成的粒度（单函数 <= 50 行），不是总范围。一个周末完成多个特性是兼容的，只要每个子任务遵循 P8 |
| 10 | 自修复循环次数 | v4 的 3 轮 = 每轮任务内的自修复次数；auto-coding 的 50-200 轮 = 总任务循环数。两者是不同粒度 |
| 11 | Decision Point vs 夜间运行 | DP1/DP2 在夜间运行前执行（异步确认），DP3 在早晨审查时执行（同步确认） |
| 12 | AI 质量降级 | 本实践第 7 章添加了基于质量指标的自动降级机制，与 v4 阈值对齐 |

### 8.3 审计检查点

以下是 v4/v5 审计时需要检查的证据点：

| 审计项 | 检查位置 | 证据格式 | 频率 |
|--------|---------|---------|------|
| P1 商业驱动 | PR 描述 | Spec 路径 + 商业目标摘要 | 每个 PR |
| P2 DCP 门禁 | `.gate/dcp-checklist.json` | 确认时间 + 确认人 | 每次自主运行前 |
| P3 TDD 先行 | `.gate/tdd-report.json` + git log | Red/Green 时间戳 + 提交顺序 | 每个 PR |
| P4 人工审查 | GitHub/GitLab PR review | 审查人签名 + 审查时间 | 每个 PR（L1-L3）/ 抽样（L4） |
| P5 密钥不入代码 | pre-commit hook 日志 + SAST 报告 | 扫描结果 | 每次 commit |
| P6 单一信息源 | `.gate/doc-drift-report.json` | 漂移检测记录 | 每周 |
| P7 Spec 驱动 | PR 描述 | Spec 文件路径和版本 | 每个 PR |
| P8 最小批量 | CI 输出 | 函数/文件大小统计 | 每个 PR |
| P9 Prompt 版本化 | `.gate/prompt-chain-trace.json` | Prompt 版本记录 | 每个 PR |
| P10 数据分级 | pre-send 扫描日志 | 扫描结果 + 拦截记录 | 每次 AI 调用 |
| 幻觉检测 | AI Reviewer 报告 | 幻觉类型和数量 | 每个 PR |
| 自修复限制 | PR 描述 | Self-Correction 轮次 | 每个 PR |
| 自主成功率 | `.omc/logs/metrics.json` | 每周统计 | 每周 |
| 降级检查 | `.omc/logs/metrics.json` | 降级条件评估 | 每周 |
| Kill Switch | `.omc/logs/kill-switch.log` | 触发记录 | 实时 |

### 8.4 审计流程图

```
┌──────────────────────────────────────────────────────────────┐
│                    v5 Auto-Coding 审计流程                     │
│                                                              │
│  审计开始                                                     │
│    │                                                         │
│    ▼                                                         │
│  [Step 1: 检查自治等级]                                      │
│    │ 当前等级 = ?                                             │
│    │ 是否满足升级条件？                                       │
│    │ 是否触发降级条件？                                       │
│    ▼                                                         │
│  [Step 2: 抽查 PR 样本]                                      │
│    │ L1-L3：全部 PR                                          │
│    │ L4：随机抽样 >= 10%                                     │
│    ▼                                                         │
│  [Step 3: 逐 PR 检查 10 条核心原则]                           │
│    │ P1-P10 各检查点是否通过？                                 │
│    │ AI Reviewer 报告是否完整？                               │
│    │ Human Review 签名是否存在？                              │
│    ▼                                                         │
│  [Step 4: 检查安全事件]                                      │
│    │ 密钥泄露？                                               │
│    │ Restricted 数据发送？                                    │
│    │ Kill Switch 触发记录？                                   │
│    ▼                                                         │
│  [Step 5: 检查度量数据]                                      │
│    │ 自主成功率趋势                                           │
│    │ 幻觉率趋势                                               │
│    │ TDD 合规率趋势                                           │
│    │ 成本趋势                                                 │
│    ▼                                                         │
│  [Step 6: 出具审计报告]                                      │
│    │ 通过 -> 继续当前自治等级                                 │
│    │ 有条件通过 -> 要求改进（设定改进期限）                   │
│    │ 不通过 -> 降级到下一等级                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## 附录 A：配置模板汇总

### A.1 .claude/settings.json（项目级）

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run test)",
      "Bash(npm run lint)",
      "Bash(npm run build)",
      "Bash(go test ./...)",
      "Bash(golangci-lint run)"
    ],
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./credentials/**)"
    ]
  },
  "env": {
    "AUTONOMY_LEVEL": "L3",
    "SPECS_DIR": "specs",
    "GATE_DIR": ".gate",
    "PROMPTS_DIR": "prompts"
  }
}
```

### A.2 pre-commit hook（密钥扫描）

```bash
#!/bin/sh
# .git/hooks/pre-commit
# Scans for secrets before each commit

echo "Running secret scan..."
if command -v gitleaks &>/dev/null; then
  if ! gitleaks detect --source . --no-banner --redact --staged; then
    echo "COMMIT BLOCKED: Secret detected in staged changes"
    echo "Remove the secret and try again."
    exit 1
  fi
fi

echo "Running TDD compliance check..."
if [ -f ".gate/tdd-check.sh" ]; then
  if ! bash .gate/tdd-check.sh; then
    echo "COMMIT BLOCKED: TDD compliance failed"
    exit 1
  fi
fi

echo "Pre-commit checks passed"
exit 0
```

### A.3 CI Gate 配置

```yaml
# .gate/ci-gate.yml
gates:
  tdd:
    enabled: true
    checks:
      - name: commit_order
        description: "Test files committed before implementation"
        command: "bash .gate/check-tdd-order.sh"
      - name: red_phase
        description: "Tests must fail before implementation"
        command: "bash .gate/check-red-phase.sh"
      - name: green_conversion
        description: "Tests must pass after implementation"
        command: "bash .gate/check-green.sh"
      - name: coverage_threshold
        description: "Coverage >= 80%"
        command: "go test ./... -cover | grep 'total:' | awk '{print $NF}' | sed 's/%//' | awk '{if ($1 < 80) exit 1}'"

  quality:
    enabled: true
    checks:
      - name: lint
        command: "golangci-lint run --max-issues-per-linter=0 --max-same-issues=0"
      - name: type_check
        command: "go build ./..."
      - name: function_length
        description: "No function > 50 lines"
        command: "bash .gate/check-function-length.sh --max 50"

  security:
    enabled: true
    checks:
      - name: secret_scan
        command: "gitleaks detect --source . --no-banner"
      - name: sast
        command: "gosec ./..."
```

---

## 附录 B：术语表

| 术语 | 定义 |
|------|------|
| Auto-Coding | 自主编码，AI 在最小化人工干预下独立完成开发循环 |
| TDD-first | 测试驱动开发的优先顺序：测试先于实现 |
| Red Phase | 测试已编写但尚未实现，测试必须失败 |
| Green Phase | 实现已编写，所有测试必须通过 |
| Self-Correction Loop | AI 自主修复失败的循环，最多 3 轮 |
| Spec-Driven | 由 Spec 文件驱动的开发，Spec 是 AI 的唯一输入来源 |
| DCP | Decision Check Point，决策门 |
| AI Reviewer | AI 自动代码审查，专注于检测 AI 特有问题（幻觉） |
| Human Reviewer | 人工代码审查，专注于业务逻辑和架构 |
| Kill Switch | 紧急停止机制，在安全/成本超限时中断自主运行 |
| Hallucination | 幻觉代码，AI 生成的不存在的 API、函数或模式 |
| Autonomy Level | 自治等级（L1-L4） |
| Trivial Fix | 琐碎修复，仅包括 lint fix、format、注释 typo、依赖 patch |
| Pre-Send Scan | 发送 AI 前的数据分类扫描，拦截 Restricted 数据 |

---

## 附录 C：快速参考卡片

### Auto-Coding 启动检查（5 分钟）

```
[ ] Spec 文件 ready（specs/ 中 status=ready）
[ ] DCP Go confirmed（.gate/dcp-go.confirmed 存在）
[ ] Kill Switch 参数已设置
[ ] 通知 Channel 已测试
[ ] Remote Control 已启用
[ ] 开始自主运行
```

### PR 审查检查（每个 PR）

```
[ ] CI 全部通过
[ ] TDD 合规（Red -> Green 记录）
[ ] AI Reviewer 通过（无 critical 幻觉）
[ ] 人工审查签名
[ ] Spec 覆盖度完整
[ ] 无密钥泄露
[ ] 函数/文件尺寸合规
```

### 每周审计检查

```
[ ] 自主成功率 >= 目标值
[ ] 幻觉率 < 5%
[ ] TDD 合规率 >= 80%
[ ] 无安全事件
[ ] 成本在预算内
[ ] 降级条件未触发
[ ] 审计报告已发布
```

---

*本文档是 AI Coding 规范 v5.0 系列的 02 号文档，与 01-core-specification.md 配合使用。*
*所有 Auto-Coding 模式必须严格遵守 v5 核心规范中定义的 10 条核心原则（P1-P10）。*
*任何偏离核心原则的行为都被视为违规，必须记录在审计报告中。*
