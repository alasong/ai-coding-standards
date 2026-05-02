# AI Coding 规范 v5.6：IPD 可执行状态机

> 版本：v5.6 | 2026-05-02
> 定位：将声明式规范编译为可执行状态机，解决 AI 在长会话中丢失上下文的问题
> 核心原则：**框架管边界，AI 管内容**
> 实现策略：先做进度追踪器，再做硬验证器

---

## 第 1 章：问题定义与设计原则

### 1.1 为什么需要可执行状态机

现有规范体系（P1-P24、IPD 六阶段、15 个 Gate）是**声明式**的——描述了"应该怎样"。但 AI 执行器是**概率式**的——在长会话中会丢失上下文，忘记自己该做什么。

**典型失败模式**：

| 规范说 | AI 实际做 | 根因 |
|--------|----------|------|
| P23: 必须完成四阶段链 | "完成了！"（但 Phase 2 没做） | 长会话中丢失约束上下文 |
| P3: TDD Red→Green→Refactor | 测试和实现混在一个 commit | 没有明确的状态边界 |
| P7: 编码前必须读 Spec | 直接开始写代码 | 没有阶段入口检查 |

**结论**：问题不是"AI 故意违反规范"，而是"AI 在长会话中忘记了规范约束"。状态机解决的是**上下文丢失**和**进度追踪**问题。

### 1.2 设计原则（简化版）

| 原则 | 说明 |
|------|------|
| **边界硬约束，内容软自由** | 状态转换条件必须通过自动化验证，状态内 AI 可以自由发挥 |
| **不拦截中间操作** | 只在状态边界验证，不实时拦截 AI 的每次写入 |
| **状态原子性** | 状态要么完整转换，要么保持原状 |
| **配置化** | 状态定义在 YAML 中，不在代码中 |
| **渐进增强** | Phase A 只做进度追踪 → 验证有效后 → 再加独立 Agent 验证 |

### 1.3 架构简化

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

**不做什么**（Phase A）：
- 不实时拦截 AI 的每次操作
- 不用独立 Agent 做深度评分
- 不 Hook 工具调用

---

## 第 2 章：状态图

### 2.1 主状态流

```
IDLE
 │
 ├─ [权限] 只读项目结构
 ├─ [退出] 需求输入存在 (.ipd/requirements/input.md)
 │
 ▼
PHASE_0_INSIGHT     市场洞察 — 五看三定 / BLM / 竞品分析
 ├─ [权限] 写 ipd/phase-0/
 ├─ [禁止] 代码、测试、Spec
 ├─ [退出] market-insight.md 存在 + DCP checklist 存在且全 PASS
 │
 ▼
PHASE_1_CONCEPT     概念定义 — Kano / QFD / JTBD / 核心竞争力画像
 ├─ [权限] 写 ipd/phase-1/
 ├─ [禁止] 代码、测试、Spec
 ├─ [退出] concept-definition.md 存在 + DCP checklist 存在且全 PASS
 │
 ▼
PHASE_2_PLAN        详细规划 — DFX / ATA / WBS / 风险矩阵
 ├─ [权限] 写 ipd/phase-2/
 ├─ [禁止] 代码、测试
 ├─ [退出] solution-design.md 存在 + DCP checklist 存在且全 PASS
 │
 ▼
PHASE_2.5_SPEC_GEN  Spec 生成 — 从方案设计生成 Feature Spec
 ├─ [权限] 写 specs/F{NNN}-*.md
 ├─ [禁止] 代码、测试
 ├─ [退出] Spec 文件存在 + frontmatter 完整 + 状态 = ready
 │
 ▼
PHASE_3_DISPATCH    开发分派 — 按 WBS 拆 Feature → Task 队列
 ├─ [权限] 写 ipd/phase-3/task-queue.json
 ├─ [禁止] 代码
 ├─ [退出] task-queue.json 存在，每个 task 映射到 Spec AC
 │
 ▼
[PHASE_3 子状态循环 — 见 §2.2]
 │
 ▼ (所有 task 完成)
PHASE_3_COMPLETE    全量验证
 ├─ [权限] 只读
 ├─ [退出] 全量测试 PASS + .gate/ 报告存在
 │
 ▼
PR_CREATE           创建 PR
 ├─ [权限] 写 PR 描述
 ├─ [禁止] 合并
 ├─ [退出] PR 文件已创建，包含 Spec 引用 + Gate 报告
 │
 ▼
IDLE (等待人类合并)
```

### 2.2 PHASE_3 子状态（TDD 循环 + Spec-to-Test 验证）

PHASE_3 是状态机中最关键的部分——这里是 AI 写代码的地方。拆成子状态确保 TDD 流程不被跳过，并加入 **Spec-to-Test 对齐验证**：

```
取 task → TDD_RED → TDD_GREEN → TDD_REFACTOR → SPEC_ALIGN_CHECK → TASK_GATE
 │                                                                    │
 │ PASS → 下一个 task                                                 │
 │ FAIL (≤3) → 回 TDD_GREEN (Self-Correction)                         │
 │ FAIL (>3) → BLOCKED → 等待人工                                     │
```

| 子状态 | 能写什么 | 不能写什么 | 退出条件 |
|--------|---------|-----------|---------|
| TDD_RED | tests/ | src/ | 测试存在 + 首次运行 FAIL |
| TDD_GREEN | src/ | tests/ | 测试全部 PASS |
| TDD_REFACTOR | src/ (重构) | tests/ | 测试仍 PASS + lint 通过 |
| **SPEC_ALIGN_CHECK** | 无 | 无 | Spec AC 逐条比对测试断言通过 |
| TASK_GATE | 无 | 任何 | Gate 报告存在且 PASS |

### 2.3 Spec-to-Test 对齐验证（微观质量保障）

**核心问题**：TDD 保障"代码和测试一致"，不保障"代码和需求一致"。AI 可能误解 Spec，然后写了一个匹配错误理解的测试——测试通过但代码是错的。

**解决思路**：在 TDD_REFACTOR 之后、TASK_GATE 之前，插入**角色切换**步骤——同一个 AI，切换到"对照者"视角，逐条比对 Spec AC 和测试断言。

```
角色切换流程:
  1. AI 完成 TDD_REFACTOR（测试通过）
  2. 注入角色切换提示:
     "你现在是【对照者】，不是【实现者】。
      任务: 逐条检查 Spec 中的每个 AC，确认测试是否覆盖。
      注意: 只看 Spec 和测试，不看实现代码。"
  3. AI 逐项输出比对结果:
     AC1 "Given-When-Then..." → 测试 test_foo 覆盖 ✅
     AC2 "Given-When-Then..." → 无对应测试 ❌
  4. 如果有 ❌ → AI 补测试 → 回到 TDD_RED
  5. 全部 ✅ → 进入 TASK_GATE
```

**角色切换不是独立 Agent**，是同一个对话中强制切换视角：

| 角色 | 任务 | 视角 |
|------|------|------|
| 实现者（TDD_RED/GREEN/REFACTOR） | 写测试、写实现 | "怎么让 AC 通过？" |
| 破坏者（TDD_RED 隐含） | 写边界条件测试 | "怎么让实现出错？" |
| **对照者（SPEC_ALIGN_CHECK）** | 比对 Spec AC 和测试 | "AC 说的和测试写的是同一件事吗？" |

**和独立 Agent 的关系**：SPEC_ALIGN_CHECK 是同一个 AI 的视角切换（轻量）。如果需要更强的验证（D1 核心特性），可在 TASK_GATE 阶段引入独立 Agent 做第二轮对照。

**硬性规则**：SPEC_ALIGN_CHECK 不通过（有 AC 遗漏），不得进入 TASK_GATE。

---

## 第 3 章：Phase A 最小实现

### 3.1 状态定义（YAML）

所有状态定义存在 `.ipd/state-machine.yaml` 中：

```yaml
version: "1.0"
states:
  IDLE:
    description: "空闲 — 等待新需求输入"
    permissions:
      allow: [read]
      deny: [write_docs, write_code, edit_tests]
      scope: []
    exit_conditions:
      - type: file_exists
        path: .ipd/requirements/input.md
    next_states: [PHASE_0_INSIGHT]

  PHASE_0_INSIGHT:
    description: "市场洞察 — 五看三定 / BLM / 竞品分析"
    permissions:
      allow: [read, write_docs]
      deny: [write_code, edit_tests]
      scope: [ipd/phase-0/]
    exit_conditions:
      - type: file_exists
        path: ipd/phase-0/market-insight.md
      - type: dcp_checklist
        phase: 0
    next_states: [PHASE_1_CONCEPT]

  PHASE_1_CONCEPT:
    description: "概念定义 — Kano / QFD / JTBD / 核心竞争力画像"
    permissions:
      allow: [read, write_docs]
      deny: [write_code, edit_tests]
      scope: [ipd/phase-1/]
    exit_conditions:
      - type: file_exists
        path: ipd/phase-1/concept-definition.md
      - type: dcp_checklist
        phase: 1
    next_states: [PHASE_2_PLAN]

  PHASE_2_PLAN:
    description: "详细规划 — DFX / ATA / WBS / 风险矩阵"
    permissions:
      allow: [read, write_docs]
      deny: [write_code, edit_tests]
      scope: [ipd/phase-2/]
    exit_conditions:
      - type: file_exists
        path: ipd/phase-2/solution-design.md
      - type: dcp_checklist
        phase: 2
    next_states: [PHASE_2.5_SPEC_GEN]

  PHASE_2.5_SPEC_GEN:
    description: "Spec 生成 — 从方案设计生成 Feature Spec"
    permissions:
      allow: [read, write_docs]
      deny: [write_code, edit_tests]
      scope: [specs/]
    exit_conditions:
      - type: file_exists
        path: specs/
        min_files: 1
        pattern: "^specs/F\\d+-.*\\.md$"
      - type: spec_validated
    next_states: [PHASE_3_DISPATCH]

  PHASE_3_DISPATCH:
    description: "开发分派 — 按 WBS 拆 Feature → Task 队列"
    permissions:
      allow: [read, write_docs]
      deny: [write_code]
      scope: [ipd/phase-3/]
    exit_conditions:
      - type: file_exists
        path: ipd/phase-3/task-queue.json
    next_states: [TDD_RED]

  TDD_RED:
    description: "TDD Red — 编写测试并确认首次失败"
    permissions:
      allow: [read, edit_tests]
      deny: [write_code]
      scope: [tests/]
    exit_conditions:
      - type: test_fail
    next_states: [TDD_GREEN]

  TDD_GREEN:
    description: "TDD Green — 编写实现使测试通过"
    permissions:
      allow: [read, write_code]
      deny: [edit_tests]
      scope: [src/]
    exit_conditions:
      - type: test_pass
    next_states: [TDD_REFACTOR]

  TDD_REFACTOR:
    description: "TDD Refactor — 重构代码，保持测试通过"
    permissions:
      allow: [read, write_code]
      deny: [edit_tests]
      scope: [src/]
    exit_conditions:
      - type: test_pass
      - type: lint_pass
    next_states: [SPEC_ALIGN_CHECK]

  SPEC_ALIGN_CHECK:
    description: "Spec-Test 对齐验证 — 对照者角色切换"
    permissions:
      allow: [read]
      deny: [write_code, edit_tests, write_docs]
      scope: []
    exit_conditions:
      - type: spec_align_pass
    next_states: [TASK_GATE]

  TASK_GATE:
    description: "任务 Gate — 幻觉检测 + 安全检查"
    permissions:
      allow: [read]
      deny: [write_code, edit_tests, write_docs]
      scope: []
    exit_conditions:
      - type: gate_report_pass
    next_states: [NEXT_TASK_OR_PHASE_3_COMPLETE]

  PHASE_3_COMPLETE:
    description: "全量验证"
    permissions:
      allow: [read]
      deny: [write_code, edit_tests, write_docs]
      scope: []
    exit_conditions:
      - type: all_tests_pass
      - type: gate_report_exists
        path: .gate/gate-report.md
    next_states: [PR_CREATE]

  PR_CREATE:
    description: "创建 PR"
    permissions:
      allow: [read, write_docs]
      deny: [write_code, edit_tests]
      scope: [specs/, .gate/]
    exit_conditions:
      - type: file_exists
        path: .ipd/pr/
        min_files: 1
    next_states: [IDLE]
```

### 3.2 状态数据（JSON）

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

### 3.3 条件类型（Phase A 实现）

| 类型 | Phase A 验证方式 | Phase B+ |
|------|-----------------|---------|
| `file_exists` | `os.path.exists()` | 同 |
| `dcp_checklist` | 读 checklist 文件，检查全为 PASS | + 独立 Agent 评分 |
| `spec_validated` | Spec frontmatter 存在 + status 字段 | + spec-validate.py |
| `spec_align_pass` | 读取 `.gate/spec-align-{task}.json`，检查 `status: pass` | + 独立 Agent 对照 |
| `test_fail` | 运行测试，检查 exit code ≠ 0 | 同 |
| `test_pass` | 运行测试，检查 exit code = 0 | + 覆盖率检查 |
| `lint_pass` | 运行 lint 工具，检查 exit code = 0 | 同 |
| `gate_report_pass` | .gate/ 报告存在且包含 "PASS" | + 独立 Agent 验证 |
| `all_tests_pass` | 运行全量测试套件 | + 性能基准 |

**Phase A 跳过的条件**：`depth_score`（独立 Agent）、`independent_review`。这些在 Phase B 中加入。

---

## 第 4 章：异常路径

### 4.1 Self-Correction 上限

```
TASK_GATE FAIL → 回 TDD_GREEN
  → Round 1 FAIL → Round 2 FAIL → Round 3 FAIL → STOP

STOP 后:
  - 标记 [SELF-CORRECTION-EXHAUSTED]
  - 写入 .ipd/blocked.json
  - 状态挂起，等待人工输入
```

### 4.2 异常场景

| 场景 | 状态机行为 |
|------|-----------|
| AI 声称完成但验证失败 | 状态不变，返回具体失败项 |
| Self-Correction 超过 3 轮 | 状态挂起，写入 blocked.json |
| AI 要求跳过状态 | 状态不变，无法获得下一状态权限 |
| 紧急 hotfix | 人工 `ipd-sm reset PHASE_3_DISPATCH` 直接跳到开发 |

---

## 第 5 章：与现有体系的映射

| 规范概念 | 定义位置 | 状态机实现 |
|---------|---------|-----------|
| P23 需求→Spec 链 | 01-core-specification.md §1.3 | PHASE_1 → PHASE_2 → PHASE_2.5 |
| DCP Gate | 01-core-specification.md §1.6 | Phase exit_condition: dcp_checklist |
| P3 TDD Red→Green→Refactor | 01-core-specification.md §2.1 | TDD_RED → TDD_GREEN → TDD_REFACTOR |
| P7 Spec 驱动 | 01-core-specification.md §1.1 | PHASE_3_DISPATCH enter 需 Spec ready |
| Self-Correction ≤ 3 轮 | 01-core-specification.md §2.2 | TASK_GATE 中计数器 |

---

## 第 6 章：CLI 接口

```bash
# 查看当前状态（每次会话开头运行）
python ai-coding-v5.4/scripts/ipd-sm.py status

# 验证当前状态是否可以退出
python ai-coding-v5.4/scripts/ipd-sm.py verify

# 转换到下一个状态
python ai-coding-v5.4/scripts/ipd-sm.py next

# 重置状态（人工操作）
python ai-coding-v5.4/scripts/ipd-sm.py reset PHASE_0_INSIGHT

# 查看历史
python ai-coding-v5.4/scripts/ipd-sm.py history
```

---

## 附录：决策记录

### 为什么不做实时拦截

Claude Code hooks 只拦截 shell 命令，不拦截 Read/Edit/Write 工具。实时拦截不可行。边界验证的方案是：AI 在状态内可以"犯错"，但 exit conditions 不满足时状态不会转——误操作在边界被发现并要求修复。

### 为什么 Phase A 跳过独立 Agent 验证

独立 Agent 验证需要基础设施来调度，这本身就是要建的系统的一部分。先验证"边界检查"这个思路本身是否有效，再逐步增强验证能力。

### 为什么定位为"进度追踪器"而非"强制执行器"

状态机的核心价值不是"强制 AI"，而是"在每次会话开始时给 AI 一个明确的、不可跳过的起点"。它解决的是上下文丢失和进度追踪问题。质量判断交给审查机制和独立 Agent。
