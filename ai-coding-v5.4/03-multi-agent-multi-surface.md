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

---

## 第 5 章：冲突检测与解决

### 5.1 冲突定义

当多个 Agent 同时修改同一文件或同一代码区域时，产生写冲突。冲突分为三级：

| 级别 | 定义 | 处理方式 |
|------|------|---------|
| L1 行级冲突 | 两个 Agent 修改不同行 | 自动合并 |
| L2 区域级冲突 | 两个 Agent 修改相邻行（±5 行内） | 自动检测 + 策略合并 |
| L3 语义级冲突 | 两个 Agent 修改同一函数/类/逻辑块 | 需要协调解决 |

### 5.2 冲突检测

写前检测：Agent 编辑文件 F 前读取其当前 Git SHA，与启动时记录的 SHA 对比。若不一致，说明其他 Agent 已修改该文件，触发三方 diff（base / current / agent_edits）检测重叠区域并按级别分类。

### 5.3 冲突解决策略

| 冲突级别 | 策略 | 执行方 |
|----------|------|--------|
| L1 | 自动合并（行级叠加） | 系统 |
| L2 | 区域排序 + 语义分析合并 | 协调 Agent |
| L3 | 锁定文件 → 排队串行化 → 按依赖顺序合并 | 协调 Agent |

L2 流程：识别冲突边界 → 按依赖图确定优先级 → 高优先变更先合并 → 低优先变更 rebase → 失败则升级为 L3。

L3 流程：冻结双方写权限 → 提取变更意图（Task/Spec）→ 判断兼容性（兼容则按依赖序合并，不兼容则回退低优先级并重新分配）→ 生成冲突报告到 `.omc/logs/conflict-{timestamp}.md`。

### 5.4 冲突预防

- **工作空间隔离**：优先让不同 Agent 操作不同文件集
- **任务依赖驱动**：有依赖关系的任务串行执行（见第 6 章）
- **文件粒度分配**：同一逻辑单元（如同一函数）不分配给多个 Agent

---

## 第 6 章：依赖图自动构建

### 6.1 依赖图数据结构

依赖图由节点（任务）和边（依赖关系）组成：

```json
{
  "nodes": [{"id": "T001", "type": "task", "spec": "specs/F001.md", "files_touched": ["src/auth.py", "tests/test_auth.py"], "status": "pending"}],
  "edges": [{"from": "T001", "to": "T002", "type": "file_dependency", "reason": "T002 imports module defined in T001"}]
}
```

### 6.2 自动依赖推断

| 维度 | 检测方法 | 示例 |
|------|---------|------|
| 文件级依赖 | import/require 语句分析 | B import A → B 依赖 A |
| 函数级依赖 | 函数调用图 | B calls A.foo() → B 依赖 A |
| Spec 级依赖 | Spec 文件中的依赖声明 | F002.md references F001 |
| 数据流依赖 | 数据库 schema 变更 | Migration A 必须在 Query B 之前 |
| 测试依赖 | 测试文件引用 | test_B tests module_A → test_B 依赖 A |

构建流程：读取所有 Spec 文件 → 解析 target_files / depends_on → 静态分析代码 import 构建模块依赖图 → 合并两类依赖 → 检测循环依赖（存在则报告并请求人工介入）→ 输出 DAG → 生成任务执行计划。

### 6.3 依赖图维护

通过 `TaskUpdate` 对依赖图进行操作：构建（`action="build"`）、查询（`action="query"`）、更新（任务完成后自动检查下游任务是否可解锁）。

### 6.4 循环依赖处理

检测到循环依赖时：标记链路中所有任务为 `[CYCLE-DETECTED]` → 报告循环路径 → 建议破环方案（移除最弱依赖边）→ 等待人工确认后继续。

---

## 第 7 章：合并冲突自动处理

### 7.1 处理策略分层

| 策略 | 适用场景 | 成功率 | 回退 |
|------|---------|--------|------|
| 自动三路合并 | 无重叠编辑 | ~95% | → 语义合并 |
| 语义合并 | 重叠但逻辑兼容 | ~70% | → 回退重排 |
| 回退重排 | 逻辑不兼容 | ~90% | → 上报人工 |
| 人工介入 | 以上全部失败 | 100% | — |

### 7.2 自动三路合并

使用 `git merge-tree <base> HEAD feature-branch-agent-a` 进行标准三路合并。成功则自动提交，有冲突则进入语义合并。

### 7.3 语义合并

三路合并冲突时协调 Agent 执行：解析冲突标记 → 读取双方 Spec 理解变更意图 → 判断兼容性（不同关注点可重组保留，不兼容则进入回退重排）→ 合并后运行测试套件验证。

### 7.4 回退重排

逻辑不兼容时：按依赖图确定优先级 → 保留高优先级变更 → `git checkout <base> -- <conflicted-files>` 回退低优先级变更 → 将其任务状态设为 `rebase_needed` 并通过 `addBlockedBy` 确保在高优先级任务完成后重新执行。

### 7.5 合并冲突报告格式

```markdown
# 合并冲突报告 - {timestamp}

## 冲突摘要
- 涉及文件：src/auth.py, src/models/user.py
- 冲突 Agent：worker-backend (T003), worker-frontend (T007)
- 冲突级别：L3 语义级

## 冲突详情
### src/auth.py:45-62
- Agent A (T003): 添加 JWT token 刷新逻辑
- Agent B (T007): 修改认证中间件签名

## 解决方案
- 策略：回退重排
- 优先级：T003 > T007（T007 依赖 T003 的模块）
- 操作：保留 T003，T007 标记为 rebase_needed

## 验证
- 合并后测试：PASS (42/42)
- T007 重排状态：等待 T003 完成
```

---

## 第 8 章：文件锁定机制

### 8.1 锁定协议

采用乐观锁为主、悲观锁为辅的策略：

| 锁类型 | 场景 | 行为 |
|--------|------|------|
| 乐观读锁 | 大多数编辑场景 | 允许并发读取，写前检测冲突 |
| 悲观写锁 | L3 冲突场景、关键文件 | 独占访问，其他 Agent 排队 |

### 8.2 锁状态管理

锁状态存储在 `.omc/locks/` 目录下，每个条目包含：file、locked_by、task_id、lock_type、acquired_at、expires_at（默认 30 分钟）、lock_level。等待队列记录请求文件、请求者、task_id 和时间戳。

### 8.3 锁定粒度

| 粒度级别 | 锁定范围 | 适用场景 |
|----------|---------|---------|
| `file` | 整个文件 | 重构、大规模变更 |
| `region` | 文件的逻辑区域（函数/类） | 同一文件不同区域的并行编辑 |
| `line-range` | 指定行范围 | 精确控制的最小锁定 |

### 8.4 锁定生命周期

请求锁定（`TaskUpdate action="request_lock"`）→ 写入锁文件并设置 expires_at → 持锁编辑（每 5 分钟心跳续期）→ 释放锁定（`action="release_lock"`，从锁文件移除并通知队列下一个等待者）。锁超时（expires_at 到达且无心跳）时自动释放。

### 8.5 死锁预防

有序请求（按文件路径字典序）→ 超时释放（默认 30 分钟）→ 心跳续期（每 5 分钟）→ 无嵌套锁（同时只持有一个写锁）→ 定期扫描等待图检测循环。

---

## 第 9 章：并行度控制

### 9.1 并行度决策因素

| 因素 | 权重 | 说明 |
|------|------|------|
| 任务独立性 | 高 | DAG 中无依赖的节点可并行 |
| 资源约束 | 高 | API 配额、内存、CPU 限制 |
| 冲突概率 | 中 | 同文件操作数越多，冲突概率越高 |
| 任务类型 | 中 | 只读任务（Explore）可高度并行 |
| 代码库规模 | 低 | 大项目适合更多并行 |

### 9.2 并行度计算

基于 DAG 最大可并行集、资源上限（API 速率 / 最大 Agent 数）、冲突因子衰减（同文件任务数 * CONFLICT_COST）计算最小值，绝对上限默认为 8。

### 9.3 动态并行度调整

保守启动 `min(ready_tasks, 4)`，运行时调整：连续 2 轮无冲突则 +1，检测到冲突则 -1，API 限流则 -2（范围 [1, 8]）。差异化：Explore 不受限，general-purpose 受限制，Plan 最多 2 个并行。

### 9.4 并行执行编排

Team Lead 根据依赖图按批次启动：无依赖任务全并行 → 通过 TaskList 检测完成 → 解锁依赖前序任务的下一批。

---

## 第 10 章：Agent 协调协议

### 10.1 状态报告协议

每个 Agent 定期报告状态（agent_name、task_id、status、progress、blockers、estimated_completion）。状态机：`pending → in_progress → [self-correction (max 3 rounds)] → completed | blocked → unblocked → in_progress | failed → [escalation] → human-review`。

### 10.2 工作交接协议

交接流程：Agent A 完成当前阶段 → 生成交接报告（已完成内容 / Git SHA / 遗留问题 / 下一步 / 关键文件列表）→ 更新状态为 `handoff_ready` → Team Lead 通知 Agent B → Agent B 读取报告后继续。

**交接报告模板：**

```markdown
# 交接报告 - T003

## 交接方：worker-backend → 接收方：worker-backend-test

## 已完成
- [x] 实现 JWT token 生成逻辑 (src/auth.py:120-185)
- [x] 添加 token 验证中间件 (src/middleware/auth.py)
- [x] 编写单元测试 12 个 (tests/test_auth.py)

## 当前状态
- 分支：feature/auth-backend
- 最后提交：a1b2c3d - "add token validation"
- 测试状态：12/12 PASS

## 遗留问题
- 需要集成 Redis 黑名单（依赖 T005 的 Redis 配置）
- refresh_token 存储方案待确认

## 下一步
1. 等待 T005 完成后集成 Redis 黑名单
2. 补充集成测试
3. 性能测试（token 验证 < 5ms）
```

### 10.3 故障恢复协议

| 故障类型 | 检测方式 | 恢复策略 |
|----------|---------|---------|
| Agent 崩溃 | 心跳超时（5 分钟无活动） | 重新分配任务给新 Agent |
| 自修循环耗尽 | 3 轮自修后仍失败 | 标记 `[SELF-CORRECTION-EXHAUSTED]`，上报人工 |
| 依赖不可满足 | 依赖任务失败 | 阻塞链中所有下游任务标记 `blocked_upstream_failure` |
| 资源耗尽 | API 配额用尽 | 暂停非关键 Agent，保留核心任务 |
| 合并不可解决 | 多次合并失败 | 上报人工审查 |

恢复流程：检测故障 → 分类 → 执行恢复（崩溃则保留工作区并创建新 Agent；自修耗尽则收集日志并标记 `needs_human_review`；依赖断裂则标记下游并尝试替代路径）→ 记录事件到 `.omc/logs/failure-{timestamp}.md`。

### 10.4 心跳与保活

心跳间隔 5 分钟（任何 TaskUpdate / SendMessage 即视为心跳）。超时阈值 15 分钟：第一次超时发探测 → 第二次标记 suspect → 第三次标记 failed 并触发恢复流程。

---

## 第 11 章：Spec 驱动的 Agent 分配

### 11.1 Spec 文件规范

每个任务必须有对应的 Spec 文件，存放在 `specs/` 目录，包含：元信息（ID、Title、Priority、Depends On、Agent Type）、目标、输入、输出、验收标准、约束。

```markdown
# specs/F001-auth-module.md

## 元信息
- ID: F001
- Title: 用户认证模块
- Priority: P0
- Depends On: [F000]
- Agent Type: general-purpose

## 目标
实现 JWT 认证模块，包括 token 生成、验证、刷新。

## 输出
- src/auth.py - 认证核心逻辑
- src/middleware/auth.py - 认证中间件
- tests/test_auth.py - 单元测试

## 验收标准
1. token 生成 < 10ms
2. token 验证 < 5ms
3. AC 覆盖率 100%
4. 通过安全审查（04-security-governance.md）

## 约束
- 使用 PyJWT 库
- 密钥从环境变量读取（禁止硬编码）
```

### 11.2 Agent 自动分配流程

Team Lead 扫描 specs/ → 解析每个 Spec 的元信息 → 查询依赖图（依赖满足则标记 ready，否则标记 blocked 并设置 blockedBy）→ 对 ready 的 Spec 按 Agent Type 分配 → 创建 Task 并关联 Spec 路径 → 持续监控（完成则解锁下游，失败则触发故障恢复）。

### 11.3 Spec → Task 映射

一个 Spec 可映射多个 Task（实现、测试、审查），通过 `blockedBy` 表达 Task 间的执行顺序。

```json
{
  "spec_file": "specs/F001-auth-module.md",
  "tasks": [
    {"id": "T001", "subject": "实现 JWT token 生成", "files": ["src/auth.py"], "agent_type": "general-purpose", "status": "pending"},
    {"id": "T002", "subject": "编写认证单元测试", "files": ["tests/test_auth.py"], "agent_type": "general-purpose", "status": "pending", "blockedBy": ["T001"]},
    {"id": "T003", "subject": "安全审查 - 认证模块", "files": ["src/auth.py", "src/middleware/auth.py"], "agent_type": "Plan", "status": "pending", "blockedBy": ["T001", "T002"]}
  ]
}
```

### 11.4 Agent 任务领取协议

**Pull 模式**：空闲 Agent 查询 TaskList → 筛选 `status=="pending"` 且未分配且无阻塞且类型匹配的任务 → `TaskUpdate(taskId, owner, status="in_progress")` 认领。

**Push 模式**：Team Lead 根据依赖图和 Agent 空闲状态主动分配 → `TaskUpdate(taskId, owner)` → `SendMessage` 通知。

### 11.5 Spec 版本与追溯

Spec 文件纳入 Git 版本控制，包含变更记录表。Agent 生成代码时在注释中记录 `# Spec: F001 v1.1`。变更 Spec 后相关任务需要重新评估。

---

## 第 12 章：上下文共享与传播

### 12.1 上下文传播机制

多 Agent 场景下每个 Agent 有独立上下文窗口。上游 Agent 完成后写入 `.omc/context/{task_id}.md`（包含变更文件列表、新增 API 签名、关键设计决策、已知限制、Git commit SHA），下游 Agent 启动前自动读取并注入上下文。

### 12.2 上下文摘要格式

```markdown
# 上下文摘要 - T001

## 基本信息
- Task: T001 | Agent: worker-auth | Completed: 2026-04-18T11:30:00Z
- Branch: feature/auth-backend | Commit: a1b2c3d

## 变更文件
| 文件 | 行数 | 说明 |
|------|------|------|
| src/auth.py | 185 | JWT 认证核心逻辑 |
| src/middleware/auth.py | 62 | 认证中间件 |
| tests/test_auth.py | 245 | 单元测试 12 个 |

## 新增 API
```python
def generate_token(user_id: str, role: str) -> str: ...
def verify_token(token: str) -> dict: ...
def refresh_token(old_token: str) -> str: ...
```

## 设计决策
- 使用 HS256 算法（项目规模不需要 RSA）
- token 有效期 15 分钟，refresh_token 7 天

## 已知限制
- 不支持多租户隔离
- token 撤销后黑名单最长 15 分钟生效
```

### 12.3 上下文传播规则

| 规则 | 说明 |
|------|------|
| **下游必读** | 下游 Agent 启动前必须读取所有上游依赖的上下文摘要 |
| **变更通知** | 上游完成后自动通知下游等待的 Agent |
| **版本匹配** | 下游使用上游提交的 commit SHA 作为基准 |
| **过期清理** | 上下文摘要保留 30 天 |

---

## 第 13 章：多 Agent 测试协调

### 13.1 测试并行策略

测试按类型分区并行执行：单元测试（按模块分区）、集成测试（按服务分区）、E2E 测试（按场景分区）、安全测试（SAST + 渗透）。协调器汇总所有结果生成测试报告。

### 13.2 测试数据隔离

| 测试类型 | 数据隔离方式 |
|---------|-------------|
| 单元测试 | Mock 所有外部依赖，无需隔离 |
| 集成测试 | 独立测试数据库（每个 Agent 用不同 schema） |
| E2E 测试 | 容器化测试环境，测试后销毁 |
| 性能测试 | 独占环境，避免与其他测试互相干扰 |

### 13.3 测试结果汇总

协调器汇总各 Agent 测试结果到 `.omc/test-results/aggregate.yaml`，格式包含各 Agent 各类型的 passed/failed/skipped 计数，有失败即整体失败。

---

## 第 14 章：Agent 资源配额

### 14.1 配额定义

| 资源类型 | 配额示例 | 超限行为 |
|---------|---------|---------|
| API 调用次数 | 50 次/任务 | 停止执行，上报 Team Lead |
| 上下文窗口使用 | 80% | 触发上下文压缩 |
| 文件写入数 | 10 个文件/任务 | 警告，超过 15 个阻断 |
| 执行时间 | 30 分钟/任务 | 超时终止 |
| 自修轮次 | 3 轮 | 超限转人工（见 01-core-specification.md） |

### 14.2 配额配置

按 Agent 类型差异化配置（`.omc/agent-quota.yaml`）：Explore 只读（max_file_writes=0，15 分钟）、Plan 不写代码（max_file_writes=0，20 分钟）、general-purpose 标准配额（max_api_calls=50，max_file_writes=15，45 分钟）。

---

## 第 15 章：Agent 生命周期管理

### 15.1 生命周期状态

`created → warming → idle → in_progress → [completed | failed | cancelled] → handoff → in_progress (next agent)`

### 15.2 生命周期事件

| 事件 | 触发动作 |
|------|---------|
| Agent 创建 | 加载团队配置、权限策略、上下文模板 |
| Agent 空闲 | 等待 TaskList 分配、超时 15 分钟自动休眠 |
| Agent 完成 | 生成总结、释放资源、通知 Team Lead |
| Agent 失败 | 收集日志、标记任务、触发恢复协议（第 10 章） |
| Agent 取消 | 保留 Git 工作区、释放锁、记录取消原因 |

### 15.3 团队清理

所有 Agent 完成任务后，Team Lead 执行 `TeamDelete` 清理团队目录和任务列表，并发送 shutdown 消息关闭所有 Worker。

---

## 附录：与其他文档的交叉引用

| 交叉引用 | 关联内容 |
|---------|---------|
| [01-core-specification.md](01-core-specification.md) | 分工原则、P8 最小批量、自修循环限制 |
| [02-auto-coding-practices.md](02-auto-coding-practices.md) | Supervisor-Worker 模式、自主编码模式 |
| [04-security-governance.md](04-security-governance.md) | Sub-Agent 安全约束、权限模型 |
| [05-tool-reference.md](05-tool-reference.md) | CLI 命令参考、TeamCreate/TaskCreate 等 |
| [06-cicd-pipeline.md](06-cicd-pipeline.md) | 多 Agent 生成的代码通过同一 Pipeline |
| [10-dependency-management.md](10-dependency-management.md) | 多 Agent 引入依赖的审批协调 |
