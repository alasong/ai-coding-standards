# AI Coding 规范 v6.0：结构化约束文件系统

> 版本：v6.0 | 2026-05-02
> 定位：多 Agent 编排的结构化约束体系——通过机器可读文件定义任务边界、代理权限和合规验证
> 前置：[01-core.md](01-core.md)（原则）、[02-state-machine.md](02-state-machine.md)（状态机）、[04-multi-agent.md](04-multi-agent.md)（Agent 角色）
>
> **与状态机的关系**：SCFS 微状态机（SCFS_BOOT → SCFS_CONTRACT → SCFS_UPSTREAM → [TDD 循环] → SCFS_GATE_REQUEST → SCFS_WAITING → TASK_GATE）注册为 [02-state-machine.md](02-state-machine.md) 的 PHASE_3 子状态，由 `ipd-sm.py` 统一调度。

---

## 第 1 章：文件体系

### 1.1 核心设计哲学

多 Agent 系统的本质是**隔离上下文间的状态同步**。Agent 之间不共享内存、不直接对话——唯一的通信通道是结构化文件。Director Agent 生成约束文件，Executor Agent 遵守约束，Checker Agent 验证合规。

### 1.2 目录结构

```
.omc/
├── orchestration/orchestration-{session-id}.yaml  # 编排合同（1 个/会话）
├── tasks/{task-id}.yaml                           # 任务合同（1 个/任务）
├── agents/{agent-id}.yaml                         # Agent 清单（1 个/Agent）
├── state/{task-id}.json                           # 状态清单（Agent 执行中更新）
├── escalation/{task-id}.yaml                      # 升级请求（Agent 越界时创建）
└── context/{task-id}-upstream.md                  # 上游上下文摘要（可选）

.gate/
└── gate-{task-id}.json                            # 门禁验证报告（Gate Checker 生成）
```

### 1.3 文件生命周期

```
Director Agent:
  生成编排合同 → 为每个叶子任务生成任务合同 → 为每个 Agent 生成清单 → 启动 Agent

Executor Agent:
  读取 Agent 清单 → 读取任务合同 → 读取上游上下文 → 执行工作，更新状态清单
  → 完成自检 → 标记 requesting_gate → 停止，等待 Gate Checker

Gate Checker:
  读取任务合同 + 状态清单 → 验证合规性 → 生成门禁报告 → 标记 PASS/FAIL

Director Agent（处理升级）:
  接收升级请求 → 决定：扩大边界 / 拆解子任务 / 拒绝 → 更新合同
```

### 1.4 文件所有权矩阵

| 文件类型 | 创建者 | 读取者 | 更新者 | 不得操作 |
|----------|--------|--------|--------|---------|
| 编排合同 | Director | 所有 Agent | Director | Executor 修改 |
| 任务合同 | Director | Executor + Gate Checker | Director（升级时） | Executor 修改 |
| Agent 清单 | Director | Executor | 不得更新 | 任何人修改 |
| 状态清单 | Executor | Director + Gate Checker | Executor | 删除（审计需要）|
| 升级请求 | Executor | Director | 不得更新 | Executor 修改 |
| 门禁报告 | Gate Checker | Director + 所有 Agent | 不得更新 | 删除（审计需要）|

---

## 第 2 章：文件类型定义

### 2.1 编排合同（Orchestration Contract）

**路径**：`.omc/orchestration/orchestration-{session-id}.yaml`
**时机**：Director Agent 接收高层任务后、启动任何 Executor 之前。

**核心字段**：
```yaml
orchestration:
  session_id: "sess-20260502-001"
  spec_reference: "specs/F001-user-authentication.md"
  business_goal: "实现用户认证模块，支持 JWT + OAuth2"
  process_profile: "L"                    # S/M/L/XL，见 01-core §3
  autonomy_level: "L2"                    # L1-L4
  task_tree: [...]                        # 任务分解树（DAG）
  dependency_graph: { nodes: [...], edges: [...] }
  escalation_policy:                      # 升级策略
    max_escalations_per_task: 2
    max_concurrent_escalations: 3
    auto_decompose_threshold: 3
    timeout_minutes: 15
```

与 P23 的关系：编排合同是"方案设计"阶段的产物，把 Spec 验收条件拆解为原子任务。

### 2.2 任务合同（Task Contract）

**路径**：`.omc/tasks/{task-id}.yaml`
**时机**：Director Agent 从编排合同派生，为每个叶子任务生成。

**核心字段**：
```yaml
task:
  task_id: "T002"
  spec_reference: "specs/F001-user-authentication.md"
  spec_acceptance_criteria: ["AC-001", "AC-003"]
  input_files: [...]                      # 必须读取的文件
  output_files: [...]                     # 必须产出的文件
  boundary_constraints:                   # 硬性限制
    max_files_touched: 5
    max_new_code_lines: 500
    max_deleted_lines: 50
    max_new_dependencies: 0
    allowed_file_patterns: ["src/auth/**", "tests/auth/**"]
    forbidden_file_patterns: ["src/db/**", "**/*.env"]
  quality_constraints:                    # 质量要求
    required_tests: [...]
    required_gates: ["L0", "L1", "L2"]
    test_depth_dimensions: [...]
  allowed_operations:                     # 允许的操作
    read: true, write: true, create: true, delete: false, execute: true
  self_check_list: [...]                  # 自检清单
  metadata: { created_at, created_by, status, assigned_to }
```

### 2.3 Agent 清单（Agent Manifest）

**路径**：`.omc/agents/{agent-id}.yaml`
**时机**：Director Agent 为每个启动的 Agent 实例生成。

**核心字段**：
```yaml
agent:
  agent_id: "agent-coder-001"
  agent_role: "coder"                     # 见 .normalized/agent-registry.yaml
  assigned_task_ids: ["T002"]
  spec_rules:                             # 加载的规范
    - path: ".normalized/coder-rules.md", required: true
  tool_permissions:                       # 工具权限
    allowed: ["Read", "Write", "Edit", "Bash"]
    denied: ["Git.push --force", "Bash.rm -rf"]
  context_files: [...]                    # 允许读取的上游产出
  security:
    allowed_network_access: false
    secret_scan_required: true
  resource_quota:
    timeout_minutes: 30
    max_tool_calls: 200
  metadata: { created_at, created_by, model, status }
```

### 2.4 状态清单（State Manifest）

**路径**：`.omc/state/{task-id}.json`
**时机**：Executor Agent 启动时创建，在里程碑节点更新。

**核心字段**：
```json
{
  "state": {
    "task_id": "T002",
    "agent_id": "agent-coder-001",
    "current_phase": "working",
    "phase_transitions": [
      { "from": "pending", "to": "reading_contract", "timestamp": "...", "note": "..." }
    ],
    "files_modified": [
      { "path": "src/auth/jwt_generator.py", "action": "created", "git_sha_after": "...", "lines_added": 120 }
    ],
    "self_check_results": [
      { "check_id": "SC-001", "status": "pass", "evidence": "...", "timestamp": "..." }
    ],
    "escalation_flag": false,
    "gate_status": "requesting_gate",
    "timestamps": { "created_at": "...", "gate_requested_at": "..." }
  }
}
```

**更新规则**：
- `phase_transitions` 只能追加，不得修改已有记录
- `escalation_flag` 一旦为 `true` 不得改回 `false`
- `gate_status` 单向推进：`null` → `requesting_gate` → `gate_passed` / `gate_failed`

### 2.5 升级请求（Escalation Request）

**路径**：`.omc/escalation/{task-id}.yaml`
**时机**：Executor Agent 发现任务超出任务合同边界时**立即**创建。

**核心字段**：
```yaml
escalation:
  task_id: "T002"
  escalation_type: "boundary_exceeded"
  original_contract_summary: { ... }
  boundary_violation:
    type: "new_dependency_required"       # files_touched | code_lines | new_dependency | complexity | unknown
    detail: "..."
    evidence: [{ file: "...", line: 3, import: "...", reason: "..." }]
  proposed_decomposition:
    suggestion: "..."
    sub_tasks: [...]
  director_decision: null                 # Director 填写：approved_expanded_boundary | decomposed | rejected | pending
```

### 2.6 门禁验证报告（Gate Verification Report）

**路径**：`.gate/gate-{task-id}.json`
**时机**：Gate Checker Agent 在 Agent 标记 `requesting_gate` 后执行。

**核心字段**：
```json
{
  "gate_report": {
    "task_id": "T002",
    "gate_checker_id": "gate-checker-001",
    "overall_result": "pass",
    "contract_compliance": {
      "boundary_checks": [{ "check": "...", "expected": 5, "actual": 2, "result": "pass" }],
      "output_file_checks": [{ "file": "...", "required": true, "exists": true, "result": "pass" }],
      "self_check_verification": { "total_items": 8, "passed": 8, "failed": 0, "result": "pass" },
      "escalation_compliance": { "was_escalated": false, "result": "pass" }
    },
    "pipeline_results": { "L0_pre_commit": "pass", "L1_compile": "pass", "L2_tests": "pass" },
    "violations": [],
    "recommendations": []
  }
}
```

---

## 第 3 章：Agent 生命周期协议

### 3.1 严格生命周期

每个 Executor Agent **必须**按以下顺序执行，不得跳过：

```
Phase 1: BOOT（启动）
  ├─ 读取 Agent Manifest
  ├─ 验证 agent_id 与 assigned_task_ids 匹配
  └─ 确认 tool_permissions 和 resource_quota

Phase 2: CONTRACT（合同读取）
  ├─ 读取 Task Contract，解析 input/output files、boundary_constraints、self_check_list
  └─ 更新 State Manifest: pending → reading_contract

Phase 3: UPSTREAM（上游上下文加载）
  ├─ 读取 context_files 中声明的每个文件
  └─ 更新 State Manifest: reading_contract → reading_upstream → working

Phase 4: EXECUTE（执行）
  ├─ 按 input_files → 实现 → output_files 的顺序工作
  ├─ 遵守 boundary_constraints、allowed_operations、tool_permissions
  ├─ 记录 files_modified（含 Git SHA）
  └─ 发现越界 → 立即进入升级协议（§4）

Phase 5: SELF-CHECK（自检）
  ├─ 逐项执行 self_check_list，填写 self_check_results
  └─ 有 fail → 自修复（最多 3 轮）

Phase 6: GATE-REQUEST（请求门禁）
  ├─ 确认所有 self_check_results 为 pass
  └─ 更新 State Manifest: gate_status = "requesting_gate"，停止工作

Phase 7: WAIT（等待门禁结果）
  └─ 不再执行任何操作，等待 Gate Checker 生成报告

Phase 8: RESUME or ROLLBACK（恢复或回滚）
  ├─ Gate PASS → 标记任务完成
  └─ Gate FAIL → 读取 violations → 修正 → 重新自检
```

---

## 第 4 章：升级协议

### 4.1 升级触发

Executor Agent 发现以下任一情况时**必须立即触发升级**：
1. 文件越界：修改文件数 > `max_files_touched`
2. 代码量越界：新增代码行数 > `max_new_code_lines`
3. 依赖越界：需要引入 `max_new_dependencies` 之外的外部依赖
4. 复杂度越界：发现 Task Contract 未预见的关键架构依赖
5. 规范冲突：Task Contract 与现有代码或 Spec 存在不可调和的冲突

### 4.2 升级流程

```
Executor 检测到越界
  → 立即停止所有修改操作（已修改文件提交到临时分支）
  → 创建 Escalation Request（填写 type、detail、evidence、proposed_decomposition）
  → 更新 State Manifest: escalation_flag = true, current_phase = "escalating"
  → 停止所有工作

Director 接收升级请求
  → 读取 Escalation Request + Task Contract + Orchestration Contract + evidence
  → 决策（三选一）：
    (a) 批准扩大边界：更新 Task Contract boundary_constraints，Executor 恢复工作
    (b) 拆解为子任务：在 Orchestration Contract 新增子任务，生成新 Task Contract
    (c) 拒绝为超范围：标记 failed，通知人类（达到 auto_decompose_threshold）
```

### 4.3 升级超时

| 场景 | 超时时间 | 超时动作 |
|------|---------|---------|
| Director 未处理升级请求 | 15 分钟 | 发送告警 |
| 升级请求 > 30 分钟未处理 | 30 分钟 | 标记 escalation_timeout，通知人类 |
| 同一任务第 3 次升级 | 立即 | 必须人工介入 |

---

## 第 5 章：违规与后果

### 5.1 违规类型矩阵

| 违规类型 | 检测方法 | 后果 | 对应原则 |
|----------|---------|------|---------|
| 修改边界外文件 | files_modified vs allowed_file_patterns | Gate FAIL → 回滚 | P17 |
| 超代码行数未升级 | git diff vs max_new_code_lines | Gate FAIL → 补升级 | P8 |
| 跳过自检项 | self_check_results 含 skipped | Gate FAIL → 补做 | P3 |
| 未声明新增依赖 | import 分析 vs allowed_dependencies | Gate FAIL → 补升级或移除 | P24 |
| 产出文件缺失 | output_files vs 磁盘实际 | Gate FAIL → 补全 | P7 |
| TDD 顺序错误 | git log 测试在实现之后 | Gate FAIL → 拆分 commit | P3 |
| 密钥出现在代码中 | gitleaks 扫描 | Gate FAIL + 安全事件 | P5 |

### 5.2 违规严重级别

| 级别 | 定义 | 处理 |
|------|------|------|
| P0（阻断） | 安全违规（密钥泄漏、越权操作） | 立即回滚 + 安全审计 + 降级 L1 |
| P1（阻塞） | 边界违规（越界文件、越界代码量） | Gate FAIL + 必须修正 |
| P2（警告） | 流程违规（跳过自检、TDD 顺序错误） | Gate FAIL + 补做 |
| P3（建议） | 代码质量问题 | Gate PASS + 建议记录 |

---

## 第 6 章：Director Agent 协议

### 6.1 工作流程

```
1. 接收高层任务 → 解析 Spec acceptance criteria → 确定 process_profile + autonomy_level
2. 任务拆解 → 遵守原子化规则（§6.2）→ 建立依赖关系（DAG）
3. 生成编排合同 → 定义 task_tree + dependency_graph + escalation_policy
4. 生成任务合同 → 为每个叶子任务填写 input/output/boundary/quality/self_check
5. 生成 Agent 清单 → 分配任务 + 配置 tool_permissions + 填写 context_files
6. 启动 Agent → 按 DAG 拓扑顺序启动
7. 监控执行 → 轮询 State Manifest → 检测 escalation_flag → 处理升级请求
8. 触发门禁 → 当 gate_status = "requesting_gate" → 启动 Gate Checker
9. 汇总与归档 → 所有任务完成后汇总 Gate Report → 归档约束文件
```

### 6.2 原子化规则（Atomization Rules）

| 规则 | 阈值 | 违反后果 |
|------|------|---------|
| 文件限制 | 单个任务 ≤ 5 个文件 | 必须进一步拆解 |
| 代码量限制 | 单个任务 ≤ 500 行 | 必须进一步拆解 |
| 依赖限制 | 不得引入未声明的外部依赖 | 必须声明或拆解 |
| 时间限制 | 单个任务 ≤ 30 分钟 | 预估超时必须拆解 |
| Spec 覆盖限制 | 单个任务负责 ≤ 3 个 AC | 超过必须拆解 |

**拆解启发式**：
- 按功能模块：`"实现用户认证"` → `"JWT Token 生成"` + `"JWT Token 验证"` + `"OAuth2 回调"`
- 按数据流：`"实现 API 端点"` → `"定义数据模型"` → `"实现业务逻辑"` → `"实现 HTTP 路由"` → `"编写集成测试"`
- 按 Spec 验收条件：`"AC-001: 用户可以登录"` → `"实现登录接口"` + `"实现登录测试"`

---

## 第 7 章：与现有体系的映射

### 7.1 与核心原则的映射

| 原则 | SCFS 实现 |
|------|----------|
| P7 Spec 驱动 | 每个 Task Contract 必须引用 Spec 文件 |
| P8 最小批量 | 原子化规则强制拆解粒度 |
| P11 证据链 | State Manifest 记录所有文件变更的 Git SHA |
| P2 DCP 门禁 | Gate Report 是 DCP 的机器化实现 |
| P6 单一信息源 | 每个事实在约束文件中仅定义一次 |
| P23 需求→Spec 链 | 编排合同承接 Spec，拆解为可执行任务 |

### 7.2 与 TDD 的集成

Task Contract 的 `self_check_list` 必须包含 TDD 验证项：
```yaml
self_check_list:
  - id: "SC-TDD-001", check: "测试 commit 在实现 commit 之前", method: "verify_git_log_test_before_impl"
  - id: "SC-TDD-002", check: "Red 阶段已记录", method: "check_test_commit_message_contains_red_phase"
  - id: "SC-TDD-003", check: "测试和实现不在同一 commit", method: "verify_separate_commits"
```

### 7.3 与状态机的映射

| 层级 | 状态机（02-state-machine.md） | SCFS 微状态机 |
|------|------------------------------|--------------|
| 范围 | IPD 阶段（Phase 0-3） | 阶段内的任务执行 |
| 粒度 | 项目级 | 任务级 |
| 状态 | PHASE_0_INSIGHT → PHASE_1_CONCEPT → ... | SCFS_BOOT → SCFS_CONTRACT → SCFS_UPSTREAM → [TDD 循环] → SCFS_GATE_REQUEST → SCFS_WAITING → TASK_GATE |
| 验证 | `ipd-sm verify` 检查 exit conditions | `ipd-sm verify` 检查 scfs_* 条件 + boundary_constraints |

---

## 附录 A：约束文件校验清单

Director 生成约束文件后、启动 Agent 前必须运行：

**编排合同**：session_id 全局唯一 + spec_reference 指向存在的 Spec + business_goal 非空 + task_tree 无循环依赖 + dependency_graph 是有效 DAG。

**任务合同**：task_id 在编排合同中存在 + input_files 中所有文件存在 + output_files 路径不冲突 + self_check_list 覆盖所有约束。

**Agent 清单**：agent_id 全局唯一 + assigned_task_ids 在编排合同中存在 + spec_rules 中所有文件存在 + tool_permissions 不冲突。

### Contract Validation Gate（独立 Agent 验证）

> 01-core.md §12 通用独立验证原则的应用。

约束文件校验清单是**自动化检查**。Contract Validation Gate 是**独立 Agent 的结构化验证**。两者互补：自动化检查查格式，独立 Agent 查语义。

**执行时机**：Director 生成所有约束文件后、启动 Executor 之前。

**执行者**：与 Director 不同的 Agent 会话（不得共享对话上下文）。

**检查项**：

| # | 检查项 | 方法 | 失败标记 |
|---|--------|------|---------|
| 1 | 任务合同是否完整覆盖 Spec 验收标准 | 逐项对比 `spec_acceptance_criteria` 与 Spec 的 AC | `[CONTRACT-AC-MISSING]` |
| 2 | dependency_graph 的依赖关系是否合理 | 检查 input_files 是否真的是 output_files 的前置依赖 | `[CONTRACT-DEP-INVALID]` |
| 3 | 边界约束是否覆盖所有可能的修改路径 | 检查 `boundary_constraints` 是否遗漏了 Spec 要求的修改范围 | `[CONTRACT-BOUNDARY-GAP]` |
| 4 | 任务合同之间是否存在隐性冲突 | 检查多个任务的 output_files 是否有重叠 | `[CONTRACT-CONFLICT]` |
| 5 | Agent 能力是否与任务匹配 | 检查 Agent Manifest 的 `capabilities` 是否覆盖任务要求 | `[CONTRACT-CAPABILITY-MISMATCH]` |
| 6 | 编排合同的历史失败模式是否被考虑 | 读取 `.gate/learning/` 中的历史模式，检查是否注入约束 | `[CONTRACT-LEARNING-MISSING]` |

**输出**：`.gate/contract-validation-{session-id}.json`

```json
{
  "session_id": "sess-20260502-001",
  "validated_by": "independent validator",
  "status": "pass" | "fail",
  "findings": [
    {
      "check_id": 1,
      "status": "fail",
      "finding": "AC-003 没有对应的任务合同",
      "severity": "critical"
    }
  ]
}
```

**裁决**：
- 所有检查 PASS → 启动 Executor
- 存在 `critical` 级发现 → Director 必须修复后重新验证
- 存在 `warning` 级发现 → 记录到 Gate 报告，允许启动

**不可裁剪**：Contract Validation Gate 在任何流程档位（S/M/L/XL）都必须执行。S 档可跳过第 2/4 项（简单任务无复杂依赖），但第 1/3/5/6 项必须执行。

---

## 附录 B：自动学习机制

> 从 Gate 失败中自动学习，避免重复犯错。01-core.md P11（证据链）原则的执行。

### B.1 失败模式分类

Gate Checker 在每个 `gate-{task-id}.json` 中增加 `failure_patterns` 字段：

```json
{
  "task_id": "T002",
  "status": "fail",
  "failure_patterns": {
    "category": "boundary_violation",
    "subcategory": "file_outside_scope",
    "severity": "critical",
    "detail": "修改了 internal/config/ 下的文件，但该文件不在 boundary_constraints 中",
    "root_cause_hypothesis": "任务合同未声明 config 文件需要修改",
    "spec_id": "F001",
    "task_type": "auth_implementation",
    "module": "payment-service"
  }
}
```

失败类别：

| 类别 | 说明 | 自动修正动作 |
|------|------|------------|
| `boundary_violation` | Executor 修改了边界外文件 | 注入到 Director 约束：下次同类任务必须包含此文件 |
| `ac_not_covered` | 验收标准未被测试覆盖 | 注入到 Director 约束：下次必须为 AC 生成对应测试 |
| `spec_misunderstood` | Executor 误解了 Spec 意图 | 注入到 Spec 质量审查队列 |
| `dependency_missing` | 遗漏了必要的依赖文件 | 注入到 Director 约束：下次必须读取此文件 |
| `nfr_violated` | 非功能需求未满足 | 注入到任务合同的 nfr 检查清单 |
| `contract_ambiguous` | 任务合同描述有歧义 | 注入到 Director 的模板改进记录 |

### B.2 学习触发规则

| 触发条件 | 动作 | 影响范围 |
|---------|------|---------|
| 相同 `failure_pattern.category` + `task_type` 出现 ≥ 2 次 | 自动注入到下一次同类型任务的编排合同约束中 | 同任务类型 |
| 相同 `spec_id` 连续 ≥ 2 次 Gate 失败 | 触发 Spec 质量审查（可能 Spec 本身有问题） | 该 Spec |
| 相同 `module` 连续 ≥ 3 次 Gate 失败 | 触发模块级架构审查 | 该模块 |
| 全局 Gate 失败率 > 30%（滚动 10 个任务） | 触发流程健康度审查（可能是流程档位选择不当） | 全局 |

### B.3 学习存储

失败模式存储到 `.gate/learning/` 目录：

```
.gate/learning/
├── failure-log.json           # 所有失败记录
├── pattern-index.json         # 按 task_type 索引的失败模式
└── injected-constraints.json  # 已注入到编排合同的约束
```

`pattern-index.json` 格式：

```json
{
  "auth_implementation": {
    "count": 5,
    "patterns": {
      "boundary_violation": {
        "count": 3,
        "last_seen": "2026-05-02",
        "injected_constraint": "必须包含 internal/config/ 下的配置文件"
      }
    }
  }
}
```

### B.4 Director 启动时的学习注入

Director 生成编排合同前必须读取 `.gate/learning/pattern-index.json`：

1. 匹配本次任务的 `task_type` 和 `module`
2. 提取该类型的高频失败模式（出现 ≥ 2 次）
3. 将对应的 `injected_constraint` 写入编排合同的 `learning_constraints` 字段
4. 记录到 `.gate/learning/injected-constraints.json`

```yaml
# 编排合同中新增字段
orchestration:
  learning_constraints:
    - source_pattern: "boundary_violation in auth_implementation"
      constraint: "任务合同必须显式声明 internal/config/ 下的文件是否需要修改"
      severity: critical
```

### B.5 学习的生命周期

| 事件 | 动作 |
|------|------|
| 约束注入后，同类型任务连续 5 次未触发相同失败 | 标记约束为 `satisfied`（保留但不强制） |
| 约束注入后，同类型任务仍然失败 | 升级为 `critical`，触发人工审查 |
| 约束超过 30 天未被触发 | 归档到历史，不再注入 |

---

## 第 8 章：Contract 文件（S3/S4 结构化契约）

> S3（100-1000 万行）和 S4（>1000 万行）级别下，Contract 文件替代 markdown Spec 作为 P7 的执行载体。

详见 [01-core.md §4.4](01-core.md#44-结构化契约contract-file)

### 5.1 Contract 文件结构

```yaml
# .contracts/payment-service/F042-refund.yaml
contract:
  id: F042
  module: payment-service
  change_type: api_addition          # api_addition | api_modification | internal_change
  api: POST /v2/refund
  backward_compatible: true
  input_schema:
    order_id: string
    reason: string
  output_schema:
    refund_id: string
    status: string
  affected_modules: [order-service, notification-service]
  test_scope:
    - payment/refund_test.go
    - order/refund_integration_test.go
  nfr:
    latency_p99: 200ms
    error_budget: 0.01%
  dcp_phase: M
  status: ready
```

### 5.2 Contract 与 Spec 的关系

| 维度 | Spec 文件（S1/S2） | Contract 文件（S3/S4） |
|------|-------------------|----------------------|
| 格式 | markdown | YAML |
| 可读性 | 人类友好 | 机器友好 |
| 位置 | `specs/F{NNN}-{name}.md` | `.contracts/{module}/F{NNN}.yaml` |
| 验证 | Spec Validation Gate | 自动化契约验证 |
| 依赖追踪 | 手动 | 依赖图谱自动构建 |

### 5.3 Contract 验证规则

Contract 文件在 Phase 2→3 转换时生成，必须通过以下验证：
1. `id` 在 Spec 列表中存在对应的 Spec 文件
2. `module` 是已定义的模块名
3. `affected_modules` 中的每个模块存在对应的 Contract 目录
4. `input_schema` 和 `output_schema` 是有效的 JSON Schema 子集
5. `test_scope` 中至少有一个文件路径（不要求文件已存在，但路径必须合理）
