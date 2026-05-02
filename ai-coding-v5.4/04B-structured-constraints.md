# AI Coding 规范 v5.6：结构化约束文件系统

> 版本：v5.6 | 2026-05-02
> 定位：多 Agent 编排的结构化约束体系——通过机器可读文件定义任务边界、代理权限和合规验证
> 前置：必须先阅读并理解 [01-core-specification.md](01-core-specification.md)、[03-multi-agent-multi-surface.md](03-multi-agent-multi-surface.md)、[21-executable-state-machine.md](21-executable-state-machine.md)

### 与可执行状态机的关系

[21-executable-state-machine.md](21-executable-state-machine.md) 定义了 IPD 阶段级别的状态转换（Phase 0→1→2→3）。SCFS 的微状态机（SCFS_BOOT → SCFS_CONTRACT → SCFS_UPSTREAM → [TDD 循环] → SCFS_GATE_REQUEST → SCFS_WAITING → TASK_GATE）已注册为状态机的 PHASE_3 子状态，由 `ipd-sm.py` 统一调度和验证。

---

## 文档定位与适用范围

本文档定义**结构化约束文件系统**（Structured Constraint File System，SCFS），解决大规模多 Agent 编排中的核心问题：**如何让多个隔离上下文的 AI Agent 在复杂协作中不"跑飞"**。

### 核心设计哲学

多 Agent 系统的本质是**隔离上下文间的状态同步**。Agent 之间不共享内存、不直接对话——它们唯一的通信通道是结构化文件。Director Agent 生成约束文件，Executor Agent 必须遵守约束，Checker Agent 验证合规性。整个系统通过文件的读写流转实现可追溯、可验证、可审计的编排。

### 与现有原则的映射

| 现有原则 | SCFS 的对应实现 |
|----------|----------------|
| P7 Spec 驱动 | 每个 Task Contract 必须引用 Spec 文件 |
| P8 最小批量 | Atomization Rules 强制拆解粒度 |
| P11 证据链 | State Manifest 记录所有文件变更的 Git SHA |
| P2 DCP 门禁 | Gate Verification Report 是 DCP 的机器化实现 |
| P6 单一信息源 | 每个事实在约束文件中仅定义一次 |
| P23 需求→Spec 链 | Orchestration Contract 承接 Spec，拆解为可执行任务 |

---

## 第 1 章：文件体系总览

### 1.1 目录结构

```
.omc/
├── orchestration/
│   └── orchestration-{session-id}.yaml      # 编排合同（1 个/会话）
├── tasks/
│   └── {task-id}.yaml                        # 任务合同（1 个/任务）
├── agents/
│   └── {agent-id}.yaml                       # Agent 清单（1 个/Agent 实例）
├── state/
│   └── {task-id}.json                        # 状态清单（Agent 执行中更新）
├── escalation/
│   └── {task-id}.yaml                        # 升级请求（Agent 越界时创建）
└── context/
    └── {task-id}-upstream.md                 # 上游上下文摘要（可选）

.gate/
└── gate-{task-id}.json                       # 门禁验证报告（Gate Checker 生成）
```

### 1.2 文件生命周期

```
Director Agent:
  1. 生成 Orchestration Contract（编排合同）
  2. 为每个叶子任务生成 Task Contract（任务合同）
  3. 为每个 Agent 实例生成 Agent Manifest（Agent 清单）
  4. 启动 Agent（传递 Agent Manifest 路径）

Executor Agent:
  1. 读取 Agent Manifest → 知道自己是谁
  2. 读取 Task Contract → 知道自己要做什么、不能做什么
  3. 读取上游上下文 → 知道前置产出
  4. 执行工作，更新 State Manifest
  5. 完成自检，标记 "requesting_gate"
  6. 停止，等待 Gate Checker

Gate Checker:
  1. 读取 Task Contract + State Manifest
  2. 验证合规性
  3. 生成 Gate Verification Report
  4. 标记 PASS / FAIL

Director Agent（处理升级）:
  1. 接收 Escalation Request
  2. 决定：扩大边界 / 拆解子任务 / 拒绝
  3. 更新 Orchestration Contract 和/或 Task Contract
```

### 1.3 文件所有权矩阵

| 文件类型 | 创建者 | 读取者 | 更新者 | 删除者 |
|----------|--------|--------|--------|--------|
| Orchestration Contract | Director | 所有 Agent | Director | Director（会话结束） |
| Task Contract | Director | 对应 Executor + Gate Checker | Director（升级时） | Director（任务归档） |
| Agent Manifest | Director | 对应 Executor | 不得更新 | Director（会话结束） |
| State Manifest | Executor（创建+更新） | Director + Gate Checker | Executor | 不得删除（审计需要） |
| Escalation Request | Executor | Director | 不得更新 | Director（处理完毕） |
| Gate Report | Gate Checker | Director + 所有 Agent | 不得更新 | 不得删除（审计需要） |

**关键约束**：Executor Agent **不得**修改 Task Contract、Agent Manifest 或其他 Agent 的 State Manifest。这是 P17（输入验证）在编排层面的延伸——Agent 只能操作自己被授权的范围。

---

## 第 2 章：文件类型定义

### 2.1 编排合同（Orchestration Contract）

**路径**：`.omc/orchestration/orchestration-{session-id}.yaml`

**生成时机**：Director Agent 接收到高层任务（来自 Spec 或人类）后、启动任何 Executor 之前。

**作用**：定义本次编排的全局约束——任务分解树、Agent-任务映射、依赖图、递归深度限制。

**YAML Schema**：

```yaml
# Orchestration Contract Schema
orchestration:
  session_id: "sess-20260502-001"
  spec_reference: "specs/F001-user-authentication.md"
  business_goal: "实现用户认证模块，支持 JWT + OAuth2"
  process_profile: "L"                    # S / M / L / XL，见 01-core §1.6.9
  autonomy_level: "L2"                    # L1 / L2 / L3 / L4

  # 任务分解树（DAG）
  task_tree:
    - task_id: "T001"
      name: "认证模块设计"
      parent_task_id: null                # 根任务
      phase: "design"
      process_profile: "M"
      recursion_depth_limit: 1            # 该任务最多可拆解 1 层子任务
      dependencies: []                    # 无前置依赖
      agent_assignment: "agent-arch-001"
      escalation_triggers:                # 满足任一条件时 Agent 必须停止并升级
        - "files_touched > 5"
        - "new_code_lines > 500"
        - "new_external_dependency required"
        - "estimated_time > 30min"

    - task_id: "T002"
      name: "JWT Token 生成器实现"
      parent_task_id: "T001"
      phase: "implementation"
      process_profile: "S"
      recursion_depth_limit: 0            # 叶子任务，不得进一步拆解
      dependencies: ["T001"]
      agent_assignment: "agent-coder-001"
      escalation_triggers:
        - "files_touched > 5"
        - "new_code_lines > 500"
        - "new_external_dependency required"
        - "estimated_time > 30min"

    - task_id: "T003"
      name: "JWT Token 验证器实现"
      parent_task_id: "T001"
      phase: "implementation"
      process_profile: "S"
      recursion_depth_limit: 0
      dependencies: ["T001"]
      agent_assignment: "agent-coder-002"
      escalation_triggers:
        - "files_touched > 5"
        - "new_code_lines > 500"
        - "new_external_dependency required"
        - "estimated_time > 30min"

    - task_id: "T004"
      name: "认证集成测试"
      parent_task_id: "T001"
      phase: "testing"
      process_profile: "S"
      recursion_depth_limit: 0
      dependencies: ["T002", "T003"]     # 必须等 T002 和 T003 完成
      agent_assignment: "agent-tester-001"
      escalation_triggers:
        - "files_touched > 5"
        - "new_code_lines > 500"
        - "estimated_time > 30min"

  # 依赖图（DAG）—— 从 task_tree 自动派生，供调度器使用
  dependency_graph:
    nodes: ["T001", "T002", "T003", "T004"]
    edges:
      - from: "T001"
        to: "T002"
      - from: "T001"
        to: "T003"
      - from: "T002"
        to: "T004"
      - from: "T003"
        to: "T004"

  # 升级策略
  escalation_policy:
    max_escalations_per_task: 2           # 同一任务最多升级 2 次
    max_concurrent_escalations: 3         # 同时处理中的升级不超过 3 个
    auto_decompose_threshold: 3           # 超过 3 次升级后 Director 必须手动介入
    timeout_minutes: 15                   # 升级请求 15 分钟未处理则告警
```

**与 P23 的关系**：Orchestration Contract 是 P23（需求→Spec 链）中"方案设计"阶段的产物。它把 Spec 中的验收条件拆解为可执行的原子任务。

### 2.2 任务合同（Task Contract）

**路径**：`.omc/tasks/{task-id}.yaml`

**生成时机**：Director Agent 从 Orchestration Contract 派生，为每个叶子任务生成一个 Task Contract。

**作用**：单个 Agent 执行的完整约束——输入、输出、边界、质量要求、允许的操作。

**YAML Schema**：

```yaml
# Task Contract Schema
task:
  task_id: "T002"
  parent_task_id: "T001"
  session_id: "sess-20260502-001"
  spec_reference: "specs/F001-user-authentication.md"
  spec_acceptance_criteria: ["AC-001", "AC-003"]  # 该任务负责的验收条件

  # 输入文件（Agent 必须读取的文件）
  input_files:
    - path: "ipd/phase-2/design-doc.md"
      purpose: "架构设计文档"
      required: true
    - path: "src/auth/interfaces.py"
      purpose: "现有接口定义"
      required: true
    - path: ".omc/context/T002-upstream.md"
      purpose: "T001 设计阶段的产出摘要"
      required: true

  # 输出文件（Agent 必须产出的文件）
  output_files:
    - path: "src/auth/jwt_generator.py"
      description: "JWT Token 生成器实现"
      required: true
    - path: "tests/auth/test_jwt_generator.py"
      description: "JWT 生成器单元测试"
      required: true

  # 边界约束（硬性限制，违反则 Gate FAIL）
  boundary_constraints:
    max_files_touched: 5                  # 最多修改/创建 5 个文件
    max_new_code_lines: 500               # 最多新增 500 行代码
    max_deleted_lines: 50                 # 最多删除 50 行代码
    max_new_dependencies: 0               # 不允许新增外部依赖
    allowed_file_patterns:                # 允许操作的文件路径模式
      - "src/auth/**"
      - "tests/auth/**"
    forbidden_file_patterns:              # 禁止操作的文件路径模式
      - "src/db/**"
      - "src/api/**"
      - "**/*.env"
      - "**/secrets/**"

  # 质量约束
  quality_constraints:
    required_tests:
      - type: "unit"
        target: "src/auth/jwt_generator.py"
        min_test_functions: 3
    required_gates: ["L0", "L1", "L2"]   # 必须通过的 Pipeline 层级，见 06-cicd-pipeline.md
    depth_tier: 3                         # 测试深度评分维度要求，见 01-core §2.3
    test_depth_dimensions:                # 必须评分 ≥ 3 的维度
      - "boundary_conditions"
      - "exception_paths"
      - "business_behavior_correctness"

  # 允许的操作
  allowed_operations:
    read: true
    write: true                           # 可以写入文件
    create: true                          # 可以创建新文件
    delete: false                         # 不得删除文件
    execute: true                         # 可以运行测试
    git_commit: true                      # 可以提交 git

  # 自检清单（Agent 必须在 claiming done 前完成）
  self_check_list:
    - id: "SC-001"
      check: "所有 output_files 已创建且非空"
      method: "file_exists_and_not_empty"
    - id: "SC-002"
      check: "所有 required_tests 已编写且通过"
      method: "run_tests_and_verify_pass"
    - id: "SC-003"
      check: "files_touched ≤ max_files_touched"
      method: "count_modified_files"
    - id: "SC-004"
      check: "new_code_lines ≤ max_new_code_lines"
      method: "git_diff_line_count"
    - id: "SC-005"
      check: "无新增外部依赖"
      method: "diff_requirements_txt"
    - id: "SC-006"
      check: "未操作 forbidden_file_patterns"
      method: "check_modified_files_against_patterns"
    - id: "SC-007"
      check: "TDD Red 阶段已记录"
      method: "verify_git_log_test_before_impl"
    - id: "SC-008"
      check: "Spec 验收条件 AC-001 和 AC-003 的测试已覆盖"
      method: "map_tests_to_ac"

  # 元数据
  metadata:
    created_at: "2026-05-02T10:00:00Z"
    created_by: "director-agent-001"
    status: "pending"                     # pending | assigned | in_progress | completed | escalated | failed
    assigned_to: "agent-coder-001"
    estimated_duration_minutes: 20
```

### 2.3 Agent 清单（Agent Manifest）

**路径**：`.omc/agents/{agent-id}.yaml`

**生成时机**：Director Agent 为每个启动的 Agent 实例生成。

**作用**：Agent 的身份凭证——知道自己是谁、能做什么工具、该读哪些上下文。

**YAML Schema**：

```yaml
# Agent Manifest Schema
agent:
  agent_id: "agent-coder-001"
  agent_role: "coder"                     # 见 .normalized/agent-registry.yaml
  agent_type: "general-purpose"           # Explore / Plan / general-purpose
  session_id: "sess-20260502-001"

  # 分配的任务
  assigned_task_ids:
    - "T002"

  # 加载的规范规则
  spec_rules:
    - path: ".normalized/coder-rules.md"
      required: true
    - path: "ai-coding-v5.4/01-core-specification.md"
      sections: ["P1-P11", "P12-P22"]
      required: true

  # 工具权限
  tool_permissions:
    allowed:
      - "Read"
      - "Write"
      - "Edit"
      - "Bash"                             # 受限：只能运行测试和 lint
      - "Bash.args": "pytest*, make*, tsc*"
    denied:
      - "Git.push --force"
      - "Bash.rm -rf"
      - "Write" to: ["**/.env", "**/secrets/**", "**/config.py"]
      - "Bash.sudo*"

  # 上下文文件（允许读取的上游产出）
  context_files:
    - path: ".omc/context/T002-upstream.md"
      purpose: "T001 设计阶段产出摘要"
    - path: "specs/F001-user-authentication.md"
      purpose: "Feature Spec"

  # 安全约束
  security:
    allowed_network_access: false          # 不得访问外部网络
    allowed_filesystem: "project_root"     # 仅限项目目录
    secret_scan_required: true             # 提交前必须通过密钥扫描

  # 超时和资源配额
  resource_quota:
    timeout_minutes: 30
    max_tool_calls: 200
    max_context_tokens: 100000
    max_output_tokens: 8000

  # 元数据
  metadata:
    created_at: "2026-05-02T10:00:00Z"
    created_by: "director-agent-001"
    model: "sonnet"                        # 使用的模型
    status: "pending"                      # pending | running | idle | completed | failed | escalated
```

**安全约束说明**：Agent Manifest 中的 `tool_permissions.denied` 是 P5（密钥不入代码）和 P17（输入验证）的编排层实现。通过文件声明而非运行时判断，使得 Gate Checker 可以事后验证。

### 2.4 状态清单（State Manifest）

**路径**：`.omc/state/{task-id}.json`

**生成时机**：Executor Agent 启动时创建初始状态，在里程碑节点更新。

**作用**：Agent 执行进度的实时快照。Director 通过读取 State Manifest 监控进度，Gate Checker 通过对比 State Manifest 和 Task Contract 验证合规性。

**JSON Schema**：

```json
{
  "state": {
    "task_id": "T002",
    "agent_id": "agent-coder-001",
    "session_id": "sess-20260502-001",

    "current_phase": "working",

    "phase_transitions": [
      {
        "from": "pending",
        "to": "reading_contract",
        "timestamp": "2026-05-02T10:05:00Z",
        "note": "Agent started, reading task contract"
      },
      {
        "from": "reading_contract",
        "to": "reading_upstream",
        "timestamp": "2026-05-02T10:05:30Z",
        "note": "Contract read complete, loading upstream context"
      },
      {
        "from": "reading_upstream",
        "to": "working",
        "timestamp": "2026-05-02T10:06:00Z",
        "note": "All context loaded, starting work"
      }
    ],

    "files_modified": [
      {
        "path": "src/auth/jwt_generator.py",
        "action": "created",
        "git_sha_before": null,
        "git_sha_after": "a1b2c3d4e5f6...",
        "lines_added": 120,
        "lines_deleted": 0
      },
      {
        "path": "tests/auth/test_jwt_generator.py",
        "action": "created",
        "git_sha_before": null,
        "git_sha_after": "f6e5d4c3b2a1...",
        "lines_added": 85,
        "lines_deleted": 0
      }
    ],

    "self_check_results": [
      {
        "check_id": "SC-001",
        "status": "pass",
        "evidence": "All 2 output files exist and are non-empty",
        "timestamp": "2026-05-02T10:25:00Z"
      },
      {
        "check_id": "SC-002",
        "status": "pass",
        "evidence": "5 test functions, all passing",
        "timestamp": "2026-05-02T10:25:30Z"
      },
      {
        "check_id": "SC-003",
        "status": "pass",
        "evidence": "files_touched=2, max=5",
        "timestamp": "2026-05-02T10:26:00Z"
      },
      {
        "check_id": "SC-004",
        "status": "pass",
        "evidence": "new_code_lines=205, max=500",
        "timestamp": "2026-05-02T10:26:00Z"
      },
      {
        "check_id": "SC-005",
        "status": "pass",
        "evidence": "No new dependencies in requirements.txt",
        "timestamp": "2026-05-02T10:26:00Z"
      },
      {
        "check_id": "SC-006",
        "status": "pass",
        "evidence": "All modified files match allowed patterns",
        "timestamp": "2026-05-02T10:26:00Z"
      },
      {
        "check_id": "SC-007",
        "status": "pass",
        "evidence": "git log shows test commit before impl commit",
        "timestamp": "2026-05-02T10:26:30Z"
      },
      {
        "check_id": "SC-008",
        "status": "pass",
        "evidence": "AC-001 covered by test_token_generation, AC-003 covered by test_token_expiry",
        "timestamp": "2026-05-02T10:26:30Z"
      }
    ],

    "escalation_flag": false,

    "gate_status": "requesting_gate",

    "timestamps": {
      "created_at": "2026-05-02T10:05:00Z",
      "working_started_at": "2026-05-02T10:06:00Z",
      "self_check_started_at": "2026-05-02T10:25:00Z",
      "self_check_completed_at": "2026-05-02T10:26:30Z",
      "gate_requested_at": "2026-05-02T10:27:00Z"
    }
  }
}
```

**State Manifest 更新规则**：
- Agent 每次状态转换必须追加一条 `phase_transitions` 记录（不得修改已有记录）
- `files_modified` 必须在 Agent 声称完成前更新完毕
- `self_check_results` 必须在 Agent 声称完成前填写完毕
- `escalation_flag` 一旦设为 `true` 不得再改回 `false`（升级不可撤销）
- `gate_status` 只能单向推进：`null` → `requesting_gate` → `gate_passed` / `gate_failed`

### 2.5 升级请求（Escalation Request）

**路径**：`.omc/escalation/{task-id}.yaml`

**生成时机**：Executor Agent 发现任务超出 Task Contract 定义的边界时，**立即**创建。

**作用**：通知 Director 任务需要重新评估——扩大边界、拆解子任务、或拒绝为超范围。

**YAML Schema**：

```yaml
# Escalation Request Schema
escalation:
  task_id: "T002"
  agent_id: "agent-coder-001"
  session_id: "sess-20260502-001"
  escalation_type: "boundary_exceeded"

  # 原任务合同摘要
  original_contract_summary:
    task_name: "JWT Token 生成器实现"
    max_files_touched: 5
    max_new_code_lines: 500
    max_new_dependencies: 0

  # 越界详情
  boundary_violation:
    type: "new_dependency_required"       # files_touched | code_lines | new_dependency | complexity | unknown
    detail: "实现 JWT RS256 签名需要 cryptography 库，但 Task Contract 声明 max_new_dependencies=0"
    evidence:
      - file: "src/auth/jwt_generator.py"
        line: 3
        import: "from cryptography.hazmat.primitives import hashes"
        reason: "RS256 签名算法依赖，Python 标准库无法实现"

  # Agent 建议的拆解方案
  proposed_decomposition:
    suggestion: "将 T002 拆分为两个子任务"
    sub_tasks:
      - name: "JWT 核心逻辑（HS256）"
        description: "使用 Python 标准库 hashlib 实现 HS256 签名"
        estimated_files: 1
        estimated_lines: 80
        new_dependencies: 0
      - name: "JWT RS256 签名支持"
        description: "引入 cryptography 库实现 RS256 签名"
        estimated_files: 2
        estimated_lines: 120
        new_dependencies: 1
        justification: "Spec AC-002 明确要求支持 RS256"

  # 时间信息
  timestamps:
    task_started_at: "2026-05-02T10:06:00Z"
    escalation_at: "2026-05-02T10:12:00Z"
    work_done_before_escalation: "已完成接口设计和部分 HS256 实现"

  # Director 决策（由 Director 填写，Agent 留空）
  director_decision: null                # approved_expanded_boundary | decomposed | rejected | pending
  director_decision_at: null
  director_notes: null
```

**升级类型定义**：

| 类型 | 触发条件 | 示例 |
|------|---------|------|
| `files_touched` | 修改文件数 > `max_files_touched` | 需要改 8 个文件但限制是 5 |
| `code_lines` | 新增代码行数 > `max_new_code_lines` | 需要 800 行但限制是 500 |
| `new_dependency` | 需要新的外部依赖 | 需要 `cryptography` 库 |
| `complexity` | 发现隐含的架构复杂度 | "本以为改一个函数，发现需要重构整个模块" |
| `unknown` | 遇到 Task Contract 未覆盖的场景 | 发现了 Spec 中未定义的技术约束 |

### 2.6 门禁验证报告（Gate Verification Report）

**路径**：`.gate/gate-{task-id}.json`

**生成时机**：Gate Checker Agent 在 Agent 标记 `requesting_gate` 后执行。

**作用**：独立验证 Agent 是否遵守了 Task Contract 的所有约束。这是 P2（DCP 门禁）的机器化实现。

**JSON Schema**：

```json
{
  "gate_report": {
    "task_id": "T002",
    "agent_id": "agent-coder-001",
    "session_id": "sess-20260502-001",
    "gate_checker_id": "gate-checker-001",

    "overall_result": "pass",

    "contract_compliance": {
      "boundary_checks": [
        {
          "check": "files_touched ≤ max_files_touched",
          "expected": 5,
          "actual": 2,
          "result": "pass"
        },
        {
          "check": "new_code_lines ≤ max_new_code_lines",
          "expected": 500,
          "actual": 205,
          "result": "pass"
        },
        {
          "check": "new_dependencies ≤ max_new_dependencies",
          "expected": 0,
          "actual": 0,
          "result": "pass"
        },
        {
          "check": "no forbidden files modified",
          "forbidden_patterns": ["src/db/**", "src/api/**", "**/*.env", "**/secrets/**"],
          "modified_files": ["src/auth/jwt_generator.py", "tests/auth/test_jwt_generator.py"],
          "result": "pass"
        }
      ],
      "output_file_checks": [
        {
          "file": "src/auth/jwt_generator.py",
          "required": true,
          "exists": true,
          "non_empty": true,
          "result": "pass"
        },
        {
          "file": "tests/auth/test_jwt_generator.py",
          "required": true,
          "exists": true,
          "non_empty": true,
          "result": "pass"
        }
      ],
      "self_check_verification": {
        "total_items": 8,
        "passed": 8,
        "failed": 0,
        "skipped": 0,
        "skipped_items": [],
        "result": "pass"
      },
      "escalation_compliance": {
        "was_escalated": false,
        "escalation_handled_correctly": null,
        "result": "pass"
      }
    },

    "pipeline_results": {
      "L0_pre_commit": "pass",
      "L1_compile": "pass",
      "L2_tests": "pass"
    },

    "test_coverage": {
      "functions_with_tests": 5,
      "total_functions": 5,
      "coverage_ratio": 1.0,
      "depth_tier": {
        "boundary_conditions": 4,
        "exception_paths": 3,
        "business_behavior_correctness": 4,
        "overall_tier": 3,
        "result": "pass"
      }
    },

    "violations": [],

    "recommendations": [],

    "timestamps": {
      "gate_started_at": "2026-05-02T10:28:00Z",
      "gate_completed_at": "2026-05-02T10:32:00Z"
    }
  }
}
```

---

## 第 3 章：Agent 生命周期协议

### 3.1 严格生命周期

每个 Executor Agent **必须**按以下顺序执行，不得跳过、不得乱序：

```
┌──────────────────────────────────────────────────────┐
│  Phase 1: BOOT（启动）                                │
│  ├─ 读取 Agent Manifest                               │
│  ├─ 验证 agent_id 与 assigned_task_ids 匹配          │
│  ├─ 加载 spec_rules 中声明的规范文件                  │
│  └─ 确认 tool_permissions 和 resource_quota          │
│                                                      │
│  Phase 2: CONTRACT（合同读取）                        │
│  ├─ 读取自己的 Task Contract（通过 assigned_task_ids）│
│  ├─ 解析 input_files → 建立待读文件列表               │
│  ├─ 解析 output_files → 建立待产出文件列表            │
│  ├─ 解析 boundary_constraints → 建立"不得触碰"清单   │
│  ├─ 解析 self_check_list → 建立自检清单               │
│  └─ 更新 State Manifest: pending → reading_contract  │
│                                                      │
│  Phase 3: UPSTREAM（上游上下文读取）                  │
│  ├─ 读取 context_files 中声明的每个文件               │
│  ├─ 注意：不得读取 context_files 之外的任何上游产出    │
│  └─ 更新 State Manifest: reading_contract → reading_upstream → working │
│                                                      │
│  Phase 4: EXECUTE（执行）                             │
│  ├─ 按 input_files → 实现 → output_files 的顺序工作  │
│  ├─ 遵守 boundary_constraints 的所有限制             │
│  ├─ 遵守 allowed_operations 的操作权限               │
│  ├─ 遵守 tool_permissions 的工具限制                 │
│  ├─ 每完成一个里程碑更新 State Manifest               │
│  ├─ 记录 files_modified（含 Git SHA）                │
│  └─ 如发现越界 → 立即进入 Escalation Protocol（§4）  │
│                                                      │
│  Phase 5: SELF-CHECK（自检）                          │
│  ├─ 逐项执行 self_check_list                          │
│  ├─ 填写 self_check_results（每项必须 pass/fail）     │
│  ├─ 不得跳过任何自检项                                │
│  └─ 如有 fail → 自修复（最多 3 轮，见 01-core §2.2） │
│                                                      │
│  Phase 6: GATE-REQUEST（请求门禁）                    │
│  ├─ 确认所有 self_check_results 为 pass              │
│  ├─ 更新 State Manifest.gate_status = "requesting_gate" │
│  └─ 停止所有工作                                      │
│                                                      │
│  Phase 7: WAIT（等待门禁结果）                        │
│  ├─ 不再执行任何操作                                  │
│  ├─ 不再修改任何文件                                  │
│  └─ 等待 Gate Checker 生成 Gate Report               │
│                                                      │
│  Phase 8: RESUME or ROLLBACK（恢复或回滚）            │
│  ├─ Gate PASS → 标记任务完成                          │
│  └─ Gate FAIL → 读取 violations → 修正 → 重新自检    │
└──────────────────────────────────────────────────────┘
```

### 3.2 生命周期状态机

```
pending
  │
  ▼
reading_contract ──────┐
  │                    │
  ▼                    │
reading_upstream ──────┤
  │                    │
  ▼                    │ (escalation detected)
working ───────────────┼──→ escalating ──→ (等待 Director 决策)
  │                    │                      │
  │ (boundary OK)       │                      ▼
  ▼                    │               resumed / decomposed
self_check ────────────┤
  │                    │
  ▼                    │
requesting_gate ───────┤
  │                    │
  ▼                    │
waiting_gate ──────────┤
  │                    │
  ├─ gate_pass ───→ completed
  │
  └─ gate_fail ───→ fixing ───→ self_check ───→ ...（最多 3 轮）
                                    │
                                    └─ 3 轮后仍 fail → failed
```

### 3.3 Agent 启动检查清单

Director 在启动 Agent 前必须验证：

- [ ] Agent Manifest 已生成且包含所有必填字段
- [ ] Task Contract 已生成且状态为 `pending`
- [ ] 依赖的前置任务状态为 `completed`
- [ ] 上游上下文摘要文件已生成
- [ ] 当前并发 Agent 数未超过 `max_concurrent_escalations`

---

## 第 4 章：升级协议

### 4.1 升级触发

Executor Agent 在执行过程中发现以下任一情况时，**必须立即触发升级**：

1. **文件越界**：需要修改的文件数超过 `max_files_touched`
2. **代码量越界**：预估新增代码行数超过 `max_new_code_lines`
3. **依赖越界**：需要引入 `max_new_dependencies` 之外的外部依赖
4. **复杂度越界**：发现 Task Contract 未预见的关键架构依赖
5. **规范冲突**：发现 Task Contract 与现有代码或 Spec 存在不可调和的冲突

### 4.2 升级流程

```
Executor 检测到越界
  │
  ├─ Step 1: 立即停止当前所有修改操作
  │   ├─ 如果已修改文件 → 提交当前进度到临时分支（不得污染主分支）
  │   └─ 如果未修改文件 → 无需操作
  │
  ├─ Step 2: 创建 Escalation Request
  │   ├─ 写入 .omc/escalation/{task-id}.yaml
  │   ├─ 填写 escalation_type、detail、evidence
  │   └─ 填写 proposed_decomposition（Agent 的建议方案）
  │
  ├─ Step 3: 更新 State Manifest
  │   ├─ escalation_flag = true
  │   ├─ current_phase = "escalating"
  │   └─ gate_status = null（取消门禁请求，如果有）
  │
  ├─ Step 4: 停止所有工作
  │   └─ 不再执行任何工具调用或文件修改
  │
  ▼
Director 接收升级请求
  │
  ├─ 读取 Escalation Request
  ├─ 读取对应的 Task Contract 和 Orchestration Contract
  ├─ 读取 Agent 提供的 evidence 文件
  │
  ├─ 决策（三选一）：
  │
  │  (a) 批准扩大边界（approved_expanded_boundary）
  │      ├─ 更新 Task Contract 的 boundary_constraints
  │      ├─ 更新 Orchestration Contract 中对应任务的 escalation_triggers
  │      ├─ 在 Escalation Request 中填写 director_decision
  │      └─ Executor 恢复工作（使用新边界）
  │
  │  (b) 拆解为子任务（decomposed）
  │      ├─ 在 Orchestration Contract 中新增子任务
  │      ├─ 为每个子任务生成新的 Task Contract
  │      ├─ 将当前任务标记为 "decomposed"
  │      ├─ 在 Escalation Request 中填写 director_decision
  │      └─ Executor 领取第一个子任务（或分配给新 Agent）
  │
  │  (c) 拒绝为超范围（rejected）
  │      ├─ 在 Escalation Request 中填写 director_decision + 拒绝原因
  │      ├─ 将任务标记为 "failed"
  │      └─ 通知人类介入（如果达到 auto_decompose_threshold）
  │
  ▼
后续处理
  ├─ 如果 (a) → Executor 继续执行，使用扩大后的边界
  ├─ 如果 (b) → 新的 Executor（或原 Executor）按新 Task Contract 执行
  └─ 如果 (c) → 任务挂起，等待人类决策
```

### 4.3 升级超时

| 场景 | 超时时间 | 超时动作 |
|------|---------|---------|
| Director 未处理升级请求 | 15 分钟 | 发送告警通知 |
| 升级请求超过 30 分钟未处理 | 30 分钟 | 标记为 "escalation_timeout"，通知人类 |
| 同一任务第 3 次升级 | 立即 | 必须人工介入（auto_decompose_threshold 触发） |

---

## 第 5 章：违规与后果

### 5.1 违规类型矩阵

| 违规类型 | 检测方法 | 后果 | 对应原则 |
|----------|---------|------|---------|
| **修改了边界外的文件** | State Manifest `files_modified` vs Task Contract `allowed_file_patterns` | Gate FAIL → Agent 必须回滚越界文件 → 重新提交 | P17 |
| **超出最大代码行数且未升级** | Git diff 行数 vs Task Contract `max_new_code_lines` | Gate FAIL → 必须补充升级流程（追溯性） | P8 |
| **跳过自检项** | Gate Checker 读取 `self_check_results`，发现 `skipped` 项 | Gate FAIL → 必须补做自检 | P3 |
| **未声明的新增依赖** | 输出文件的 import 分析 vs Task Contract `allowed_dependencies` | Gate FAIL → 必须补充升级或移除依赖 | P24 |
| **产出文件缺失** | 输出文件列表 vs 磁盘实际文件 | Gate FAIL → 必须补全产出 | P7 |
| **读取了未授权的上游上下文** | 实际读取文件 vs Agent Manifest `context_files` | Gate FAIL（安全/隔离违规）→ 必须报告 | P10 |
| **使用了未授权的工具** | 工具调用日志 vs Agent Manifest `tool_permissions` | Gate FAIL（安全违规）→ 必须报告 + 审计 | P5 |
| **在 gate_fail 后继续修改** | State Manifest `gate_status` vs 文件修改时间戳 | Gate FAIL → 所有修改视为无效 → 回滚 | P2 |
| **TDD 顺序错误** | Git log 中测试 commit 在实现 commit 之后 | Gate FAIL → 必须拆分 commit | P3 |
| **密钥出现在代码中** | pre-commit gitleaks 扫描 | Gate FAIL + 安全事件 | P5 |

### 5.2 违规处理流程

```
Gate Checker 检测到违规
  │
  ├─ 记录违规到 Gate Report 的 violations 数组
  ├─ overall_result = "fail"
  │
  ├─ 更新 State Manifest.gate_status = "gate_failed"
  │
  ▼
Director 接收失败通知
  │
  ├─ 读取 Gate Report，分析 violations
  │
  ├─ 判断违规类型：
  │   ├─ 可修复违规（边界、代码量、自检遗漏）
  │   │   └─ 通知 Agent 修正，重新进入 self_check 阶段
  │   │
  │   ├─ 需升级违规（复杂度超出预期、隐含架构依赖）
  │   │   └─ 触发升级协议（§4），Director 重新决策
  │   │
  │   └─ 安全违规（密钥泄漏、越权访问）
  │       └─ 立即回滚所有修改 → 标记任务 failed → 通知人类
  │
  └─ 如果同一 Agent 连续 3 次 Gate FAIL
      └─ 标记 Agent 为 "unreliable"，后续任务分配不同 Agent
```

### 5.3 违规严重级别

| 级别 | 定义 | 处理 |
|------|------|------|
| **P0（阻断）** | 安全违规（密钥泄漏、越权操作、数据泄漏） | 立即回滚 + 安全审计 + 降级 L1 |
| **P1（阻塞）** | 边界违规（越界文件、越界代码量、缺失产出） | Gate FAIL + 必须修正 |
| **P2（警告）** | 流程违规（跳过自检、TDD 顺序错误） | Gate FAIL + 补做 |
| **P3（建议）** | 代码质量问题（命名不规范、缺少注释） | Gate PASS + 建议记录到 Gate Report |

---

## 第 6 章：Director Agent 协议

### 6.1 Director 工作流程

```
Director Agent 工作流
  │
  ├─ Step 1: 接收高层任务
  │   ├─ 来源：Spec 文件 或 人类直接输入
  │   ├─ 解析 Spec 中的 acceptance criteria
  │   └─ 确定 process_profile（S/M/L/XL）和 autonomy_level
  │
  ├─ Step 2: 任务拆解
  │   ├─ 将 Spec 拆解为可执行的原子任务
  │   ├─ 遵守 Atomization Rules（§6.2）
  │   ├─ 建立任务间的依赖关系（DAG）
  │   └─ 为每个任务分配 process_profile
  │
  ├─ Step 3: 生成编排合同
  │   ├─ 填写 Orchestration Contract（§2.1）
  │   ├─ 定义 task_tree 和 dependency_graph
  │   ├─ 定义 escalation_triggers 和 escalation_policy
  │   └─ 写入 .omc/orchestration/orchestration-{session-id}.yaml
  │
  ├─ Step 4: 生成任务合同
  │   ├─ 为每个叶子任务生成 Task Contract（§2.2）
  │   ├─ 填写 input_files、output_files、boundary_constraints
  │   ├─ 填写 quality_constraints、self_check_list
  │   └─ 写入 .omc/tasks/{task-id}.yaml
  │
  ├─ Step 5: 生成 Agent 清单
  │   ├─ 为每个 Agent 实例生成 Agent Manifest（§2.3）
  │   ├─ 分配任务（agent_assignment）
  │   ├─ 配置 tool_permissions
  │   ├─ 填写 context_files
  │   └─ 写入 .omc/agents/{agent-id}.yaml
  │
  ├─ Step 6: 启动 Agent
  │   ├─ 按 DAG 拓扑顺序启动（无依赖的任务优先）
  │   ├─ 传递 Agent Manifest 路径
  │   └─ 创建 State Manifest 初始状态（pending）
  │
  ├─ Step 7: 监控执行
  │   ├─ 轮询 State Manifest 状态
  │   ├─ 检测 escalation_flag
  │   ├─ 检测超时（resource_quota.timeout_minutes）
  │   └─ 处理 Escalation Request（§4.2）
  │
  ├─ Step 8: 触发门禁
  │   ├─ 当 State Manifest.gate_status = "requesting_gate"
  │   ├─ 启动 Gate Checker Agent
  │   ├─ 传递 Task Contract + State Manifest 路径
  │   └─ 等待 Gate Report
  │
  └─ Step 9: 汇总与归档
      ├─ 所有任务完成后汇总 Gate Report
      ├─ 更新 Orchestration Contract 状态
      ├─ 生成会话摘要报告
      └─ 归档约束文件（保留用于审计）
```

### 6.2 原子化规则（Atomization Rules）

Director 拆解任务时**必须**遵守以下规则。违反任一规则意味着拆解粒度不够，必须进一步分解。

| 规则 | 阈值 | 违反后果 |
|------|------|---------|
| **文件限制** | 单个任务不得修改超过 **5 个文件** | 必须进一步拆解 |
| **代码量限制** | 单个任务不得新增超过 **500 行代码** | 必须进一步拆解 |
| **依赖限制** | 单个任务不得引入未声明的外部依赖 | 必须声明或拆解 |
| **时间限制** | 单个任务必须在 **30 分钟**内完成 | 预估超时必须拆解 |
| **Spec 覆盖限制** | 单个任务负责的验收条件不超过 **3 个** | 超过必须拆解 |

**拆解启发式**：

```
按功能模块拆解：
  "实现用户认证"
    → "实现 JWT Token 生成"（T002）
    → "实现 JWT Token 验证"（T003）
    → "实现 OAuth2 回调"（T004）

按数据流拆解：
  "实现 API 端点"
    → "定义数据模型和接口"（T005）
    → "实现业务逻辑"（T006）
    → "实现 HTTP 路由和序列化"（T007）
    → "编写集成测试"（T008）

按 Spec 验收条件拆解：
  "AC-001: 用户可以登录"
    → "实现登录接口"（T009）
    → "实现登录测试"（T010）

按层级拆解（P8 最小批量的编排层实现）：
  "重构数据库模块"
    → "重构 Schema 定义"（T011，2 个文件）
    → "重构 Migration 脚本"（T012，3 个文件）
    → "重构 Repository 层"（T013，4 个文件）
```

### 6.3 Director 的决策矩阵

| 场景 | Director 动作 |
|------|--------------|
| 所有任务正常完成 | 触发 Gate Checker → 汇总 → 归档 |
| 单个任务升级（边界超出） | 评估：扩大边界 / 拆解 / 拒绝 |
| 单个任务升级（复杂度超出） | 必须拆解，扩大边界无效 |
| 同一任务第 2 次升级 | 拆解为子任务（不得再扩大边界） |
| 同一任务第 3 次升级 | 标记 failed → 通知人类 |
| Agent 连续 3 次 Gate FAIL | 标记 Agent unreliable → 后续任务分配不同 Agent |
| 多个任务同时升级（> max_concurrent_escalations） | 排队处理，超过 30 分钟通知人类 |
| Spec 变更（人类修改了 Spec） | 重新生成 Orchestration Contract → 更新未完成的任务 |

---

## 第 7 章：与现有规范的集成

### 7.1 与 P7（Spec 驱动）的集成

```
Spec 文件（specs/F{NNN}-{name}.md）
  │
  ▼
Director 读取 Spec，解析 acceptance criteria
  │
  ▼
生成 Orchestration Contract（spec_reference 字段指向 Spec 路径）
  │
  ▼
生成 Task Contract（spec_acceptance_criteria 字段列出负责的 AC）
  │
  ▼
Executor 读取 Spec（通过 input_files）和 Task Contract
  │
  ▼
Gate Checker 验证测试是否覆盖了对应的 AC
```

**验证链**：Spec AC → Task Contract `spec_acceptance_criteria` → 测试文件 → Gate Report `test_coverage`。这条链中任何一环断裂都导致 Gate FAIL。

### 7.2 与 P3（TDD 先行）的集成

Task Contract 的 `self_check_list` 必须包含 TDD 验证项：

```yaml
self_check_list:
  - id: "SC-TDD-001"
    check: "测试 commit 在实现 commit 之前"
    method: "verify_git_log_test_before_impl"
  - id: "SC-TDD-002"
    check: "Red 阶段已记录（测试先失败）"
    method: "check_test_commit_message_contains_red_phase"
  - id: "SC-TDD-003"
    check: "测试和实现不在同一 commit"
    method: "verify_separate_commits"
```

### 7.3 与 P2（DCP 门禁）的集成

Gate Verification Report 是 DCP 门禁的机器化实现。DCP checklist 的深度评分（depth score）由 Gate Checker 在生成 Gate Report 时附加：

```json
{
  "dcp_depth_scores": {
    "code_quality": 3,
    "test_coverage": 4,
    "architecture_compliance": 3,
    "security": 4,
    "overall": 3.5
  }
}
```

### 7.4 与 CI/CD Pipeline 的集成

Task Contract 中的 `required_gates` 字段直接映射到 [06-cicd-pipeline.md](06-cicd-pipeline.md) 定义的 Pipeline 层级：

| Task Contract `required_gates` | 执行的 Pipeline 层级 |
|-------------------------------|---------------------|
| `["L0"]` | pre-commit hooks、secret scan、format check |
| `["L0", "L1"]` | + build、type check、import check |
| `["L0", "L1", "L2"]` | + unit test、integration test、coverage |
| `["L0", "L1", "L2", "L3"]` | + lint、SAST、AI Reviewer |
| `["L0", "L1", "L2", "L3", "L4"]` | + E2E test、contract test、performance |
| `["L0", "L1", "L2", "L3", "L4", "L5"]` | + staging deploy、canary、production |

### 7.5 与可执行状态机的集成

SCFS 的微状态机已注册为 [21-executable-state-machine.md](21-executable-state-machine.md) 的 PHASE_3 子状态。`ipd-sm.py` 统一调度两个层级：

| 层级 | 状态机 | SCFS 微状态机 |
|------|--------|--------------|
| **范围** | IPD 阶段（Phase 0-3） | 阶段内的任务执行 |
| **粒度** | 项目级 | 任务级 |
| **状态** | PHASE_0_INSIGHT → PHASE_1_CONCEPT → ... | SCFS_BOOT → SCFS_CONTRACT → SCFS_UPSTREAM → [TDD 循环] → SCFS_GATE_REQUEST → SCFS_WAITING → TASK_GATE |
| **验证** | ipd-sm verify 检查 exit conditions | ipd-sm verify 检查 scfs_* 条件 + boundary_constraints |
| **新增条件类型** | — | scfs_state_file_exists, scfs_contract_read, scfs_upstream_loaded, scfs_gate_requested, scfs_gate_report_exists, scfs_boundary_check |

---

## 第 8 章：审计与追溯

### 8.1 审计日志

所有约束文件和状态文件构成完整的审计轨迹。对于任何会话，可以重建以下信息：

- **谁做了什么**：Agent Manifest → 任务分配 → State Manifest → 文件修改
- **为什么这样做**：Task Contract → 边界约束 → Spec 验收条件
- **是否合规**：Gate Report → 违规记录 → 深度评分
- **遇到问题如何处理**：Escalation Request → Director 决策 → 后续状态

### 8.2 追溯查询示例

```
# 查找某个文件变更的来源
git log -- src/auth/jwt_generator.py
  → commit a1b2c3d by agent-coder-001
  → 对应 task T002
  → 读取 .omc/tasks/T002.yaml
  → 对应 spec specs/F001-user-authentication.md

# 查找某个 Gate FAIL 的原因
cat .gate/gate-T002.json | jq '.gate_report.violations'
  → 列出所有违规项

# 查找升级历史
find .omc/escalation/ -name "*.yaml" | xargs grep -l "task_id: T002"
  → 列出 T002 的所有升级请求
```

### 8.3 文件保留策略

| 文件类型 | 保留时间 | 保留位置 |
|----------|---------|---------|
| Orchestration Contract | 永久 | Git 仓库（归档分支） |
| Task Contract | 永久 | Git 仓库（归档分支） |
| Agent Manifest | 永久 | Git 仓库（归档分支） |
| State Manifest | 永久 | Git 仓库（归档分支） |
| Escalation Request | 永久 | Git 仓库（归档分支） |
| Gate Report | 永久 | Git 仓库（.gate/ 目录） |

**重要**：约束文件是审计证据（P11 证据链），不得删除。建议在每次会话结束后将 `.omc/` 和 `.gate/` 目录提交到 `ipd-audit/` 分支。

---

## 第 9 章：实施指南

### 9.1 渐进式采用

| 阶段 | 采用内容 | 验证方式 |
|------|---------|---------|
| **Phase 1（最小可用）** | Task Contract + State Manifest | Agent 能读取合同并遵守边界 |
| **Phase 2（编排完整）** | + Orchestration Contract + Agent Manifest | Director 能正确拆解和调度 |
| **Phase 3（质量保障）** | + Gate Report + Self-Check | Gate Checker 能独立验证 |
| **Phase 4（升级处理）** | + Escalation Request | 升级流程端到端可用 |
| **Phase 5（全面集成）** | 与 CI/CD Pipeline + 状态机集成 | 全链路自动化 |

### 9.2 工具支持

| 工具 | 用途 | 实现状态 |
|------|------|---------|
| YAML Schema 验证 | 验证约束文件格式正确性 | 待实现 |
| DAG 拓扑排序 | 确定任务启动顺序 | 待实现 |
| 文件变更检测 | 对比实际变更与边界约束 | 待实现 |
| 升级超时监控 | 监控升级请求是否超时 | 待实现 |
| 审计日志聚合 | 汇总约束文件为审计报告 | 待实现 |

### 9.3 与 OMC 工具的映射

| SCFS 文件 | 对应的 OMC 路径 |
|-----------|----------------|
| Orchestration Contract | `.omc/orchestration/`（新目录） |
| Task Contract | `.omc/tasks/`（新目录） |
| Agent Manifest | `.omc/agents/`（新目录） |
| State Manifest | `.omc/state/{task-id}.json`（扩展现有结构） |
| Escalation Request | `.omc/escalation/`（新目录） |
| Gate Report | `.gate/gate-{task-id}.json`（扩展现有 .gate/ 目录） |
| Context 摘要 | `.omc/context/`（新目录） |

---

## 附录 A：完整 YAML Schema 速查

### A.1 Orchestration Contract 必填字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `orchestration.session_id` | string | 是 | 唯一会话标识 |
| `orchestration.spec_reference` | string | 是 | 来源 Spec 文件路径 |
| `orchestration.business_goal` | string | 是 | 商业目标描述（P1） |
| `orchestration.process_profile` | enum | 是 | S/M/L/XL |
| `orchestration.task_tree` | array | 是 | 任务分解树 |
| `orchestration.dependency_graph` | object | 是 | DAG 依赖图 |
| `orchestration.escalation_policy` | object | 是 | 升级策略配置 |

### A.2 Task Contract 必填字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task.task_id` | string | 是 | 唯一任务标识 |
| `task.spec_reference` | string | 是 | 来源 Spec 文件路径（P7） |
| `task.input_files` | array | 是 | 必须读取的输入文件 |
| `task.output_files` | array | 是 | 必须产出的输出文件 |
| `task.boundary_constraints` | object | 是 | 边界约束 |
| `task.quality_constraints` | object | 是 | 质量约束 |
| `task.allowed_operations` | object | 是 | 允许的操作 |
| `task.self_check_list` | array | 是 | 自检清单 |

### A.3 Agent Manifest 必填字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agent.agent_id` | string | 是 | 唯一 Agent 标识 |
| `agent.agent_role` | string | 是 | Agent 角色（见 agent-registry.yaml） |
| `agent.assigned_task_ids` | array | 是 | 分配的任务列表 |
| `agent.spec_rules` | array | 是 | 加载的规范规则 |
| `agent.tool_permissions` | object | 是 | 工具权限 |
| `agent.context_files` | array | 是 | 允许读取的上下文文件 |
| `agent.resource_quota` | object | 是 | 超时和资源配额 |

### A.4 State Manifest 必填字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `state.task_id` | string | 是 | 对应任务标识 |
| `state.agent_id` | string | 是 | 执行 Agent 标识 |
| `state.current_phase` | enum | 是 | 当前执行阶段 |
| `state.files_modified` | array | 是 | 修改的文件列表（含 SHA） |
| `state.escalation_flag` | boolean | 是 | 升级标志 |
| `state.gate_status` | enum | 是 | 门禁状态 |

### A.5 Escalation Request 必填字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `escalation.task_id` | string | 是 | 对应任务标识 |
| `escalation.escalation_type` | enum | 是 | 越界类型 |
| `escalation.boundary_violation` | object | 是 | 越界详情 |
| `escalation.proposed_decomposition` | object | 否 | Agent 建议的拆解方案 |

### A.6 Gate Report 必填字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `gate_report.task_id` | string | 是 | 对应任务标识 |
| `gate_report.overall_result` | enum | 是 | pass / fail |
| `gate_report.contract_compliance` | object | 是 | 合同合规检查 |
| `gate_report.violations` | array | 是 | 违规列表（可为空数组） |

---

## 附录 B：约束文件校验清单

Director 在生成约束文件后、启动 Agent 前，必须运行以下校验：

### B.1 Orchestration Contract 校验

- [ ] `session_id` 全局唯一
- [ ] `spec_reference` 指向存在的 Spec 文件
- [ ] `business_goal` 非空（P1 合规）
- [ ] `task_tree` 中每个任务有唯一的 `task_id`
- [ ] `task_tree` 中不存在循环依赖
- [ ] `dependency_graph` 是有效的 DAG（无环）
- [ ] 所有 `agent_assignment` 引用了存在的 Agent ID
- [ ] 每个叶子任务（`recursion_depth_limit = 0`）有明确的 `output_files`

### B.2 Task Contract 校验

- [ ] `task_id` 在 Orchestration Contract 中存在
- [ ] `spec_reference` 与 Orchestration Contract 一致
- [ ] `input_files` 中所有文件存在
- [ ] `output_files` 路径不与现有文件冲突（除非 `allowed_operations.delete = true`）
- [ ] `max_files_touched` ≥ `output_files.length` + 预计读取的现有文件数
- [ ] `self_check_list` 覆盖所有 `boundary_constraints` 和 `quality_constraints`
- [ ] `allowed_operations` 与 Agent Manifest 的 `tool_permissions` 一致

### B.3 Agent Manifest 校验

- [ ] `agent_id` 全局唯一
- [ ] `assigned_task_ids` 中所有任务在 Orchestration Contract 中存在
- [ ] `spec_rules` 中所有文件存在
- [ ] `context_files` 中所有文件存在
- [ ] `tool_permissions` 不冲突（allowed 和 denied 无重叠）
- [ ] `timeout_minutes` ≥ 预估任务执行时间

---

## 附录 C：与 IPD 流程的映射

SCFS 文件体系与 IPD 六阶段方法引擎的对应关系：

| IPD 阶段 | SCFS 文件 | 说明 |
|----------|----------|------|
| **Phase 0（市场洞察）** | Orchestration Contract | Director 将洞察拆解为分析任务 |
| **Phase 1（概念定义）** | Orchestration Contract + Task Contract | 概念定义任务化 |
| **Phase 2（技术规划）** | Orchestration Contract + Task Contract + Agent Manifest（architect） | 架构设计任务化 |
| **Phase 3（开发）** | Task Contract + Agent Manifest（coder） + State Manifest + Escalation Request | 核心开发执行层 |
| **Phase 4（测试验证）** | Task Contract（tester） + Gate Report | 测试任务化 + 门禁验证 |
| **Phase 5（发布）** | Gate Report + Orchestration Contract（最终状态） | 发布前门禁汇总 |

**关键对应**：Phase 3 开发阶段是 SCFS 最密集的使用场景。每个开发任务对应一个 Task Contract，每个开发 Agent 对应一个 Agent Manifest，执行过程通过 State Manifest 追踪，遇到越界通过 Escalation Request 升级，最终通过 Gate Report 验证。
