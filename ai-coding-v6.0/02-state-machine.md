# AI Coding 规范 v6.0：可执行状态机

> 版本：v6.0 | 2026-05-02
> 定位：将声明式规范编译为可执行状态机，解决 AI 在长会话中丢失上下文的问题
> 核心原则：**框架管边界，AI 管内容**
> 关联：[01-core.md](01-core.md)（原则）、[03-structured-constraints.md](03-structured-constraints.md)（SCFS 微状态机约束文件）

---

## 第 1 章：问题定义与设计原则

### 1.1 为什么需要可执行状态机

规范是声明式的（"应该怎样"），AI 是概率式的（长会话中会丢失上下文）。状态机解决的是**上下文丢失**和**进度追踪**问题。

| 规范说 | AI 实际做 | 根因 |
|--------|----------|------|
| P23: 必须完成四阶段链 | "完成了！"（但 Phase 2 没做） | 丢失约束上下文 |
| P3: TDD Red→Green→Refactor | 测试和实现混在一个 commit | 没有明确的状态边界 |
| P7: 编码前必须读 Spec | 直接开始写代码 | 没有阶段入口检查 |

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| **边界硬约束，内容软自由** | 状态转换条件必须通过自动化验证，状态内 AI 可以自由发挥 |
| **不拦截中间操作** | 只在状态边界验证，不实时拦截 AI 的每次写入 |
| **状态原子性** | 状态要么完整转换，要么保持原状 |
| **配置化** | 状态定义在 YAML 中，不在代码中 |
| **渐进增强** | Phase A 只做进度追踪 → 验证有效后 → 再加独立 Agent 验证 |

### 1.3 架构

```
每次会话开始:
  ipd-sm status → 告诉 AI "你现在在哪，能做什么，下一步是什么"
     ↓
  AI 在当前状态的权限窗口内工作
     ↓
AI 声称完成:
  ipd-sm verify → 检查 exit conditions
     ↓
  PASS → 状态转换到下一个
  FAIL → 告诉 AI "缺 X、Y、Z"，状态不变
```

**不做什么**（Phase A）：不实时拦截操作、不用独立 Agent 做深度评分、不 Hook 工具调用。

---

## 第 2 章：主状态流

```
IDLE
 │  [退出] .ipd/requirements/input.md 存在
 ▼
PHASE_0_INSIGHT     市场洞察 — 五看三定 / BLM / 竞品分析
 │  [权限] 写 ipd/phase-0/  [禁止] 代码/测试/Spec
 │  [退出] market-insight.md + DCP checklist 全 PASS
 ▼
PHASE_1_CONCEPT     概念定义 — Kano / QFD / JTBD / 核心竞争力画像
 │  [权限] 写 ipd/phase-1/  [禁止] 代码/测试/Spec
 │  [退出] concept-definition.md + DCP checklist 全 PASS
 ▼
PHASE_2_PLAN        详细规划 — DFX / ATA / WBS / 风险矩阵
 │  [权限] 写 ipd/phase-2/  [禁止] 代码/测试
 │  [退出] solution-design.md + DCP checklist 全 PASS
 ▼
PHASE_2.5_SPEC_GEN  Spec 生成 — 从方案设计生成 Feature Spec
 │  [权限] 写 specs/F{NNN}-*.md  [禁止] 代码/测试
 │  [退出] Spec 存在 + frontmatter 完整 + status = ready
 ▼
PHASE_3_DISPATCH    开发分派 — 按 WBS 拆 Feature → Task 队列
 │  [权限] 写 ipd/phase-3/  [禁止] 代码
 │  [退出] task-queue.json 存在，每个 task 映射到 Spec AC
 ▼
[PHASE_3 子状态循环 — 见 §3]
 ▼ (所有 task 完成)
PHASE_3_COMPLETE    全量验证
 │  [权限] 只读
 │  [退出] 全量测试 PASS + .gate/ 报告存在
 ▼
PR_CREATE           创建 PR
 │  [权限] 写 PR 描述  [禁止] 合并
 │  [退出] PR 文件存在，包含 Spec 引用 + Gate 报告
 ▼
IDLE (等待人类合并)
```

---

## 第 3 章：PHASE_3 子状态

### 3.1 SCFS 任务生命周期（外层包装）

每个 task 从队列取出后，必须先走 SCFS 生命周期，再进入 TDD 循环：

```
取 task → SCFS_BOOT → SCFS_CONTRACT → SCFS_UPSTREAM → [TDD 循环] → SCFS_GATE_REQUEST → SCFS_WAITING
                                                                        │
                                                                        ▼
                                                              TASK_GATE → 下一个 task
```

| 子状态 | 能写什么 | 不能写什么 | 退出条件 |
|--------|---------|-----------|---------|
| SCFS_BOOT | .omc/state/{task-id}.json | 代码/测试/业务文档 | State Manifest 已创建 |
| SCFS_CONTRACT | .omc/state/{task-id}.json | 代码/测试 | Contract 读取完成 |
| SCFS_UPSTREAM | .omc/state/{task-id}.json | 代码/测试 | Upstream context 加载完成 |
| [TDD 循环] | 见 §3.2 | — | — |
| SCFS_GATE_REQUEST | .omc/state/{task-id}.json | 任何 | gate_status = "requesting_gate" |
| SCFS_WAITING | 无 | 任何 | Gate Report 存在 |

### 3.2 TDD 循环（内层执行）

```
TDD_RED → TDD_GREEN → TDD_REFACTOR → SPEC_ALIGN_CHECK → SCFS_GATE_REQUEST
 │                                        │
 │ FAIL (≤3) ─────────────────────────────┘ (Self-Correction)
 │ FAIL (>3) → BLOCKED → 等待人工
```

| 子状态 | 能写什么 | 不能写什么 | 退出条件 |
|--------|---------|-----------|---------|
| TDD_RED | tests/ | src/ | 测试存在 + 首次 FAIL |
| TDD_GREEN | src/ | tests/ | 测试 PASS |
| TDD_REFACTOR | src/ (重构) | tests/ | 测试 PASS + lint 通过 |
| SPEC_ALIGN_CHECK | 无 | 无 | Spec AC 逐条比对测试通过 |

### 3.3 TASK_GATE

| 检查项 | 验证方式 |
|--------|---------|
| Gate 报告 PASS | .gate/gate-{task-id}.json 存在且包含 "PASS" |
| SCFS 边界验证 | State Manifest files_modified vs Task Contract boundary_constraints |
| Self-Correction ≤ 3 轮 | .gate/self-correction.json 计数 |

FAIL → 回 TDD_GREEN（≤3 轮）→ 仍 FAIL → BLOCKED → 等待人工

---

## 第 4 章：状态定义

### 4.1 YAML 配置

```yaml
version: "2.0"
states:
  IDLE:
    description: "空闲 — 等待新需求输入"
    permissions: { allow: [read], deny: [write_docs, write_code, edit_tests], scope: [] }
    exit_conditions: [{ type: file_exists, path: ".ipd/requirements/input.md" }]
    next_states: [PHASE_0_INSIGHT]

  PHASE_0_INSIGHT:
    description: "市场洞察 — 五看三定 / BLM / 竞品分析"
    permissions: { allow: [read, write_docs], deny: [write_code, edit_tests], scope: ["ipd/phase-0/"] }
    exit_conditions: [{ type: file_exists, path: "ipd/phase-0/market-insight.md" }, { type: dcp_checklist, phase: 0 }]
    next_states: [PHASE_1_CONCEPT]

  PHASE_1_CONCEPT:
    description: "概念定义 — Kano / QFD / JTBD / 核心竞争力画像"
    permissions: { allow: [read, write_docs], deny: [write_code, edit_tests], scope: ["ipd/phase-1/"] }
    exit_conditions: [{ type: file_exists, path: "ipd/phase-1/concept-definition.md" }, { type: dcp_checklist, phase: 1 }]
    next_states: [PHASE_2_PLAN]

  PHASE_2_PLAN:
    description: "详细规划 — DFX / ATA / WBS / 风险矩阵"
    permissions: { allow: [read, write_docs], deny: [write_code, edit_tests], scope: ["ipd/phase-2/"] }
    exit_conditions: [{ type: file_exists, path: "ipd/phase-2/solution-design.md" }, { type: dcp_checklist, phase: 2 }]
    next_states: [PHASE_2.5_SPEC_GEN]

  PHASE_2.5_SPEC_GEN:
    description: "Spec 生成 — 从方案设计生成 Feature Spec"
    permissions: { allow: [read, write_docs], deny: [write_code, edit_tests], scope: ["specs/"] }
    exit_conditions: [{ type: file_exists, path: "specs/", min_files: 1, pattern: "^specs/F\\d+-.*\\.md$" }, { type: spec_validated }]
    next_states: [PHASE_3_DISPATCH]

  PHASE_3_DISPATCH:
    description: "开发分派 — 按 WBS 拆 Feature → Task 队列"
    permissions: { allow: [read, write_docs], deny: [write_code], scope: ["ipd/phase-3/"] }
    exit_conditions: [{ type: file_exists, path: "ipd/phase-3/task-queue.json" }]
    next_states: [SCFS_BOOT]

  SCFS_BOOT:
    description: "SCFS 启动 — 创建 State Manifest"
    permissions: { allow: [read, write_docs], deny: [write_code, edit_tests], scope: [".omc/state/"] }
    exit_conditions: [{ type: scfs_state_file_exists }]
    next_states: [SCFS_CONTRACT]

  SCFS_CONTRACT:
    description: "SCFS 合同读取 — 读取 Task Contract"
    permissions: { allow: [read, write_docs], deny: [write_code, edit_tests], scope: [".omc/state/", ".omc/tasks/"] }
    exit_conditions: [{ type: scfs_contract_read }]
    next_states: [SCFS_UPSTREAM]

  SCFS_UPSTREAM:
    description: "SCFS 上游上下文加载"
    permissions: { allow: [read, write_docs], deny: [write_code, edit_tests], scope: [".omc/state/", ".omc/context/"] }
    exit_conditions: [{ type: scfs_upstream_loaded }]
    next_states: [TDD_RED]

  TDD_RED:
    description: "TDD Red — 编写测试并确认首次失败"
    permissions: { allow: [read, edit_tests], deny: [write_code], scope: ["tests/"] }
    exit_conditions: [{ type: test_fail }]
    next_states: [TDD_GREEN]

  TDD_GREEN:
    description: "TDD Green — 编写实现使测试通过"
    permissions: { allow: [read, write_code], deny: [edit_tests], scope: ["src/"] }
    exit_conditions: [{ type: test_pass }]
    next_states: [TDD_REFACTOR]

  TDD_REFACTOR:
    description: "TDD Refactor — 重构代码，保持测试通过"
    permissions: { allow: [read, write_code], deny: [edit_tests], scope: ["src/"] }
    exit_conditions: [{ type: test_pass }, { type: lint_pass }]
    next_states: [SPEC_ALIGN_CHECK]

  SPEC_ALIGN_CHECK:
    description: "Spec-Test 对齐验证 — 对照者角色切换"
    permissions: { allow: [read], deny: [write_code, edit_tests, write_docs], scope: [] }
    exit_conditions: [{ type: spec_align_pass }]
    next_states: [SCFS_GATE_REQUEST]

  SCFS_GATE_REQUEST:
    description: "SCFS 请求门禁 — 标记请求门禁"
    permissions: { allow: [read, write_docs], deny: [write_code, edit_tests], scope: [".omc/state/"] }
    exit_conditions: [{ type: scfs_gate_requested }]
    next_states: [SCFS_WAITING]

  SCFS_WAITING:
    description: "SCFS 等待门禁结果"
    permissions: { allow: [read], deny: [write_code, edit_tests, write_docs], scope: [] }
    exit_conditions: [{ type: scfs_gate_report_exists }]
    next_states: [TASK_GATE]

  TASK_GATE:
    description: "任务 Gate — 幻觉检测 + 安全检查 + SCFS 边界验证"
    permissions: { allow: [read], deny: [write_code, edit_tests, write_docs], scope: [] }
    exit_conditions: [{ type: gate_report_pass }, { type: scfs_boundary_check }]
    next_states: [NEXT_TASK_OR_PHASE_3_COMPLETE]

  PHASE_3_COMPLETE:
    description: "全量验证"
    permissions: { allow: [read], deny: [write_code, edit_tests, write_docs], scope: [] }
    exit_conditions: [{ type: all_tests_pass }, { type: gate_report_exists, path: ".gate/gate-report.md" }]
    next_states: [PR_CREATE]

  PR_CREATE:
    description: "创建 PR"
    permissions: { allow: [read, write_docs], deny: [write_code, edit_tests], scope: ["specs/", ".gate/"] }
    exit_conditions: [{ type: file_exists, path: ".ipd/pr/", min_files: 1 }]
    next_states: [IDLE]
```

### 4.2 状态数据

```json
{
  "current_state": "IDLE",
  "state_history": [],
  "task_queue": [],
  "current_task_index": -1,
  "self_correction_count": 0,
  "blocked": null
}
```

### 4.3 条件类型

| 类型 | Phase A 验证 | Phase B+ |
|------|-------------|---------|
| `file_exists` | `os.path.exists()` | 同 |
| `dcp_checklist` | 读文件，检查全 PASS | + 独立 Agent 评分 |
| `spec_validated` | Spec frontmatter + status | + spec-validate.py |
| `spec_align_pass` | .gate/spec-align-*.json status=pass | + 独立 Agent 对照 |
| `test_fail` / `test_pass` | 运行测试，检查 exit code | + 覆盖率 |
| `lint_pass` | 运行 lint 工具 | 同 |
| `gate_report_pass` | .gate/ 报告包含 "PASS" | + 独立 Agent |
| `scfs_state_file_exists` | .omc/state/{task-id}.json 存在 | 同 |
| `scfs_contract_read` | phase_transitions 含 reading_contract | + YAML 校验 |
| `scfs_upstream_loaded` | phase_transitions 含 reading_upstream | + context_files 校验 |
| `scfs_gate_requested` | gate_status = "requesting_gate" | 同 |
| `scfs_gate_report_exists` | .gate/gate-{task-id}.json 存在 | + Gate Checker 验证 |
| `scfs_boundary_check` | files_modified vs boundary_constraints | + SCFS 全量校验 |

---

## 第 5 章：异常路径

| 场景 | 状态机行为 |
|------|-----------|
| 验证失败 | 状态不变，返回具体失败项 |
| Self-Correction > 3 轮 | 挂起，写入 .ipd/blocked.json |
| 要求跳过状态 | 拒绝，状态不变 |
| 紧急 hotfix | `ipd-sm reset PHASE_3_DISPATCH` |

---

## 第 6 章：CLI 接口

```bash
python scripts/ipd-sm.py status          # 查看当前状态
python scripts/ipd-sm.py verify          # 验证 exit conditions
python scripts/ipd-sm.py next            # 转换到下一个状态
python scripts/ipd-sm.py reset STATE     # 重置状态（人工）
python scripts/ipd-sm.py history         # 查看历史
python scripts/ipd-sm.py init            # 初始化 .ipd/ 目录
```

---

## 第 7 章：与现有体系的映射

| 规范概念 | 定义位置 | 状态机实现 |
|---------|---------|-----------|
| P23 需求→Spec 链 | [01-core.md](01-core.md) §1 | PHASE_1 → PHASE_2 → PHASE_2.5 |
| DCP Gate | [01-core.md](01-core.md) §4 | exit_condition: dcp_checklist |
| P3 TDD | [01-core.md](01-core.md) §5 | TDD_RED → TDD_GREEN → TDD_REFACTOR |
| P7 Spec 驱动 | [01-core.md](01-core.md) §6 | PHASE_3_DISPATCH enter 需 Spec ready |
| Self-Correction ≤ 3 | [01-core.md](01-core.md) §5 | TASK_GATE 计数器 |
| SCFS 结构化约束 | [03-structured-constraints.md](03-structured-constraints.md) | SCFS_BOOT → ... → SCFS_WAITING |
| SCFS 边界验证 | [03-structured-constraints.md](03-structured-constraints.md) §5 | TASK_GATE: scfs_boundary_check |

---

## 附录：决策记录

### 为什么不做实时拦截

Claude Code hooks 只拦截 shell 命令，不拦截 Read/Edit/Write 工具。方案：AI 在状态内可以"犯错"，但 exit conditions 不满足时状态不会转换——误操作在边界被发现。

### 为什么定位为"进度追踪器"

核心价值不是"强制 AI"，而是"在每次会话开始时给 AI 一个明确的、不可跳过的起点"。质量判断交给审查机制和独立 Agent。
