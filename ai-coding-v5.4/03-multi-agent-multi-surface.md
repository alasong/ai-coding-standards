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

### 5.2 冲突检测机制

**写前检测（Pre-Write Check）：**

```
Agent 编辑文件 F 前：
  1. 读取 F 的当前 Git SHA（SHA_current）
  2. 对比 Agent 启动时记录的 SHA（SHA_base）
  3. 如果 SHA_current != SHA_base：
     → 其他 Agent 已修改 F，触发冲突检测流程
```

**冲突检测算法：**

```python
def detect_conflict(agent_edits, file_path):
    """检测编辑冲突"""
    current = git_read(file_path)
    base = agent_base_snapshot(file_path)

    # 计算三方 diff
    agent_changes = diff3(base, current, agent_edits)

    if agent_changes.has_overlapping_regions():
        conflict_level = classify_conflict(agent_changes)
        return {
            "level": conflict_level,
            "regions": agent_changes.overlap_regions(),
            "action": resolve_strategy(conflict_level)
        }
    return {"level": "none", "action": "apply"}
```

### 5.3 冲突解决策略

| 冲突级别 | 策略 | 执行方 |
|----------|------|--------|
| L1 | 自动合并（行级叠加） | 系统 |
| L2 | 区域排序 + 语义分析合并 | 协调 Agent |
| L3 | 锁定文件 → 排队串行化 → 按依赖顺序合并 | 协调 Agent |

**L2 区域级冲突解决流程：**

1. 识别冲突区域边界（函数/类级别的逻辑单元）
2. 按任务依赖图确定执行优先级（见第 6 章）
3. 优先级高的 Agent 变更先合并
4. 优先级低的 Agent 变更基于新版本重新应用（rebase）
5. 如果 rebase 失败，升级为 L3

**L3 语义级冲突解决流程：**

1. 协调 Agent 冻结两个 Agent 的写权限
2. 拉取两个 Agent 的变更意图（从 Task 描述和 Spec 文件）
3. 分析两个变更是否逻辑兼容
   - 兼容：按依赖序合并
   - 不兼容：回退低优先级 Agent，重新分配任务
4. 生成冲突解决报告，记录到 `.omc/logs/conflict-{timestamp}.md`

### 5.4 冲突预防

- **工作空间隔离**：优先让不同 Agent 操作不同文件集
- **任务依赖驱动**：有依赖关系的任务串行执行（见第 6 章）
- **文件粒度分配**：同一逻辑单元（如同一函数）不分配给多个 Agent

---

## 第 6 章：依赖图自动构建

### 6.1 依赖图数据结构

```json
{
  "nodes": [
    {
      "id": "T001",
      "type": "task",
      "spec": "specs/F001.md",
      "files_touched": ["src/auth.py", "tests/test_auth.py"],
      "status": "pending"
    }
  ],
  "edges": [
    {
      "from": "T001",
      "to": "T002",
      "type": "file_dependency",
      "reason": "T002 imports module defined in T001"
    }
  ]
}
```

### 6.2 自动依赖推断

**推断维度：**

| 维度 | 检测方法 | 示例 |
|------|---------|------|
| 文件级依赖 | import/require 语句分析 | B import A → B 依赖 A |
| 函数级依赖 | 函数调用图 | B calls A.foo() → B 依赖 A |
| Spec 级依赖 | Spec 文件中的依赖声明 | F002.md references F001 |
| 数据流依赖 | 数据库 schema 变更 | Migration A 必须在 Query B 之前 |
| 测试依赖 | 测试文件引用 | test_B tests module_A → test_B 依赖 A |

**自动构建流程：**

```
1. 读取 specs/ 目录下所有 Spec 文件
2. 解析每个 Spec 声明的：
   - 目标文件（target_files）
   - 依赖 Spec（depends_on）
3. 静态分析目标文件：
   - 解析 import/require 语句
   - 构建模块依赖图
4. 合并 Spec 声明依赖和代码分析依赖
5. 检测循环依赖 → 如果存在，报告并请求人工介入
6. 输出 DAG（有向无环图）
7. 根据 DAG 生成任务执行计划
```

### 6.3 依赖图维护

```bash
# 依赖图构建命令（概念性）
TaskUpdate(taskId="graph-builder", action="build", source="specs/")

# 依赖图查询
TaskUpdate(taskId="graph-builder", action="query", query="what_blocks_T005")

# 依赖图更新（任务完成后）
TaskUpdate(taskId="T001", status="completed")
# → 自动触发：检查 T001 的下游任务是否可以解锁
```

### 6.4 循环依赖处理

当检测到循环依赖时：

1. 标记循环链路中的所有任务为 `[CYCLE-DETECTED]`
2. 报告循环路径：`T001 → T003 → T007 → T001`
3. 建议破环方案（移除最弱依赖边）
4. 等待人工确认后继续

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

```bash
# 标准三路合并
git merge-base HEAD feature-branch-agent-a
git merge-tree <base> HEAD feature-branch-agent-a

# 如果合并成功且无冲突：
#   → 自动提交合并结果
# 如果有冲突：
#   → 进入语义合并流程
```

### 7.3 语义合并

当三路合并产生冲突时，协调 Agent 执行：

1. **解析冲突标记**：提取 `<<<<<<<`, `=======`, `>>>>>>>` 区域
2. **意图分析**：
   - 读取两个分支对应 Task 的 Spec 文件
   - 理解每个变更的业务意图
3. **兼容性判断**：
   - 两个变更是否修改不同关注点（如一个改样式，一个改逻辑）
   - 是否可以通过代码重组同时保留两者
4. **合并执行**：
   - 保留两个变更的语义完整内容
   - 在必要时插入适配代码（如 import 语句调整）
5. **验证**：运行测试套件确认合并正确

### 7.4 回退重排

当语义合并判断两个变更逻辑不兼容时：

1. 确定优先级（基于依赖图，见第 6 章）
2. 保留高优先级变更
3. 回退低优先级变更：`git checkout <base> -- <conflicted-files>`
4. 提交高优先级版本
5. 重新分配低优先级任务：
   - 更新 Task 状态为 `rebase_needed`
   - 基于新版本代码重新执行该任务
   - 使用 `addBlockedBy` 确保在高优先级任务完成后执行

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

锁状态存储在 `.omc/locks/` 目录下：

```json
// .omc/locks/file-lock-schema.json
{
  "locks": [
    {
      "file": "src/auth.py",
      "locked_by": "worker-backend",
      "task_id": "T003",
      "lock_type": "write",
      "acquired_at": "2026-04-17T10:30:00Z",
      "expires_at": "2026-04-17T11:00:00Z",
      "lock_level": "file"
    }
  ],
  "queue": [
    {
      "file": "src/auth.py",
      "requested_by": "worker-auth-test",
      "task_id": "T012",
      "requested_at": "2026-04-17T10:32:00Z"
    }
  ]
}
```

### 8.3 锁定粒度

| 粒度级别 | 锁定范围 | 适用场景 |
|----------|---------|---------|
| `file` | 整个文件 | 重构、大规模变更 |
| `region` | 文件的逻辑区域（函数/类） | 同一文件不同区域的并行编辑 |
| `line-range` | 指定行范围 | 精确控制的最小锁定 |

### 8.4 锁定生命周期

```
1. 请求锁定（Lock Request）
   → TaskUpdate(action="request_lock", file="src/auth.py", lock_level="function", target="AuthService")

2. 获取锁定（Lock Acquired）
   → 写入 .omc/locks/file-lock-schema.json
   → 设置 expires_at（默认 30 分钟）

3. 持锁编辑（Hold & Edit）
   → Agent 正常编辑
   → 定期心跳（每 5 分钟更新锁状态）

4. 释放锁定（Lock Release）
   → TaskUpdate(action="release_lock", file="src/auth.py")
   → 从锁文件中移除条目
   → 通知队列中的下一个等待者

5. 锁超时（Lock Timeout）
   → 如果 expires_at 到达且无心跳
   → 自动释放锁
   → 通知持锁 Agent 和等待队列
```

### 8.5 死锁预防

- **有序请求**：Agent 按文件路径字典序请求锁，避免循环等待
- **超时释放**：所有锁都有最大持有时间（默认 30 分钟）
- **心跳机制**：活跃 Agent 每 5 分钟发送心跳，续期锁
- **无嵌套锁**：一个 Agent 同一时间只持有一个文件的写锁
- **死锁检测**：协调 Agent 定期扫描锁等待图，检测循环等待

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

```python
def calculate_optimal_parallelism(tasks, resource_limits):
    """计算最优并行度"""
    # 1. 基于 DAG 的最大可并行集
    ready_tasks = [t for t in tasks if t.blocked_by == [] or all_deps_done(t)]

    # 2. 资源上限
    max_by_resources = min(
        resource_limits.api_calls_per_minute / avg_api_per_task,
        resource_limits.max_concurrent_agents
    )

    # 3. 冲突因子衰减
    file_groups = group_tasks_by_files(ready_tasks)
    conflict_penalty = sum(
        max(0, len(group) - 1) * CONFLICT_COST
        for group in file_groups.values()
    )

    # 4. 最终并行度
    optimal = min(
        len(ready_tasks),
        max(1, int(max_by_resources - conflict_penalty)),
        HARD_CAP  # 绝对上限，默认 8
    )

    return optimal
```

### 9.3 动态并行度调整

```
初始并行度：min(ready_tasks, 4)  # 保守启动

运行时调整：
  - 如果连续 2 轮无冲突 → parallelism += 1
  - 如果检测到冲突 → parallelism -= 1
  - 如果 API 速率限制触发 → parallelism = max(1, parallelism - 2)
  - 范围：[1, 8]

任务类型差异化：
  - Explore 类：不受限（只读，不会冲突）
  - general-purpose：受并行度限制
  - Plan 类：最多 2 个并行
```

### 9.4 并行执行编排

```bash
# Team Lead 根据依赖图和并行度启动任务

# 第一批：无依赖任务（可全并行）
Agent(name="worker-auth", subagent_type="general-purpose", team_name="feature-team")
Agent(name="worker-models", subagent_type="general-purpose", team_name="feature-team")
Agent(name="worker-explore", subagent_type="Explore", team_name="feature-team")

TaskUpdate(taskId="T001", owner="worker-auth")
TaskUpdate(taskId="T002", owner="worker-models")
TaskUpdate(taskId="T003", owner="worker-explore")

# 等待第一批完成 → 第二批解锁
# （自动通过 TaskList 检测 T001/T002/T003 状态）

# 第二批：依赖第一批的任务
Agent(name="worker-api", subagent_type="general-purpose", team_name="feature-team")
TaskUpdate(taskId="T004", owner="worker-api")  # T004 blockedBy: [T001, T002]
```

---

## 第 10 章：Agent 协调协议

### 10.1 状态报告协议

每个 Agent 按以下频率和格式报告状态：

```json
{
  "agent_name": "worker-backend",
  "task_id": "T003",
  "status": "in_progress",
  "progress": {
    "phase": "implementation",
    "completed_steps": 3,
    "total_steps": 5,
    "current_file": "src/auth.py"
  },
  "blockers": [],
  "estimated_completion": "2026-04-17T11:15:00Z",
  "timestamp": "2026-04-17T11:00:00Z"
}
```

**状态机：**

```
pending → in_progress → [self-correction (max 3 rounds)] → completed
                        → blocked → unblocked → in_progress
                        → failed → [escalation] → human-review
```

### 10.2 工作交接协议

当 Agent A 需要将工作交接给 Agent B 时：

```
1. Agent A 完成当前工作阶段
2. Agent A 生成交接报告（Handoff Report）：
   ├── 已完成内容
   ├── 当前状态（Git SHA、分支）
   ├── 遗留问题/TODO
   ├── 下一步建议
   └── 关键文件列表
3. Agent A 更新 Task 状态为 `handoff_ready`
4. Team Lead 通知 Agent B
5. Agent B 读取交接报告，理解上下文
6. Agent B 更新 Task 状态为 `in_progress`，继续工作
```

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

**故障分类：**

| 故障类型 | 检测方式 | 恢复策略 |
|----------|---------|---------|
| Agent 崩溃 | 心跳超时（5 分钟无活动） | 重新分配任务给新 Agent |
| 自修循环耗尽 | 3 轮自修后仍失败 | 标记 `[SELF-CORRECTION-EXHAUSTED]`，上报人工 |
| 依赖不可满足 | 依赖任务失败 | 阻塞链中所有下游任务标记 `blocked_upstream_failure` |
| 资源耗尽 | API 配额用尽 | 暂停非关键 Agent，保留核心任务 |
| 合并不可解决 | 多次合并失败 | 上报人工审查 |

**故障恢复流程：**

```
1. 检测故障（心跳超时 / 异常退出 / 错误报告）
2. 分类故障类型
3. 执行恢复策略：

   3a. Agent 崩溃：
       - 保留 Agent 的 Git 工作区（不丢弃部分进度）
       - 创建新 Agent，加载相同上下文
       - 新 Agent 从最后已知状态继续

   3b. 自修循环耗尽：
       - 收集所有失败日志到 .omc/logs/self-correction-{task_id}.md
       - 标记任务状态为 needs_human_review
       - 通知 Team Lead 和上游/下游任务

   3c. 依赖链断裂：
       - 标记所有下游任务为 blocked_upstream_failure
       - 尝试找到替代路径（是否可不依赖该任务）
       - 如果无替代路径，整体上报

4. 记录故障事件到 .omc/logs/failure-{timestamp}.md
```

### 10.4 心跳与保活

```
心跳间隔：5 分钟
心跳内容：TaskUpdate 或 SendMessage（任何活动即视为心跳）
超时阈值：15 分钟（3 个心跳周期无活动）
超时处理：
  1. 第一次超时：发送探测消息
  2. 第二次超时：标记 Agent 为 suspect
  3. 第三次超时：标记 Agent 为 failed，触发恢复流程
```

---

## 第 11 章：Spec 驱动的 Agent 分配

### 11.1 Spec 文件规范

每个任务必须有对应的 Spec 文件，存放在 `specs/` 目录：

```markdown
# specs/F001-auth-module.md

## 元信息
- ID: F001
- Title: 用户认证模块
- Priority: P0
- Depends On: [F000]  # 依赖的其他 Spec
- Agent Type: general-purpose

## 目标
实现 JWT 认证模块，包括 token 生成、验证、刷新。

## 输入
- 用户数据库模型（已由 F000 定义）
- 应用配置文件

## 输出
- src/auth.py - 认证核心逻辑
- src/middleware/auth.py - 认证中间件
- tests/test_auth.py - 单元测试

## 验收标准
1. token 生成 < 10ms
2. token 验证 < 5ms
3. 测试覆盖率 > 80%
4. 通过安全审查（04-security-governance.md）

## 约束
- 使用 PyJWT 库
- 密钥从环境变量读取（禁止硬编码）
- 遵循 01-core-specification.md 中的 P5、P8 原则
```

### 11.2 Agent 自动分配流程

```
1. Team Lead 扫描 specs/ 目录
2. 为每个 Spec 文件：
   a. 解析元信息（ID、依赖、Agent 类型）
   b. 查询依赖图，确认依赖状态
   c. 如果依赖已满足 → 标记为 ready
   d. 如果依赖未满足 → 标记为 blocked，设置 blockedBy
3. 对所有 ready 的 Spec：
   a. 根据 Agent Type 选择合适的 Agent
   b. 创建 Task 并关联 Spec 路径
   c. 分配 Agent 作为 Task owner
   d. Agent 读取 Spec，开始工作
4. 持续监控：
   a. Task 完成 → 解锁下游 Spec
   b. Task 失败 → 触发故障恢复（见第 10 章）
```

### 11.3 Spec → Task 映射

```json
{
  "spec_file": "specs/F001-auth-module.md",
  "tasks": [
    {
      "id": "T001",
      "subject": "实现 JWT token 生成",
      "description": "根据 specs/F001-auth-module.md 实现 token 生成逻辑",
      "files": ["src/auth.py"],
      "agent_type": "general-purpose",
      "status": "pending"
    },
    {
      "id": "T002",
      "subject": "编写认证单元测试",
      "description": "为 src/auth.py 编写测试，遵循 TDD 原则",
      "files": ["tests/test_auth.py"],
      "agent_type": "general-purpose",
      "status": "pending",
      "blockedBy": ["T001"]
    },
    {
      "id": "T003",
      "subject": "安全审查 - 认证模块",
      "description": "审查认证模块是否符合 04-security-governance.md",
      "files": ["src/auth.py", "src/middleware/auth.py"],
      "agent_type": "Plan",
      "status": "pending",
      "blockedBy": ["T001", "T002"]
    }
  ]
}
```

### 11.4 Agent 任务领取协议

**主动领取模式（Pull）：**

```
1. 空闲 Agent 定期查询 TaskList
2. 筛选条件：
   - status == "pending"
   - owner == "" (未分配)
   - blockedBy == [] 或所有 blockedBy 已完成
   - agent_type 匹配 Agent 自身能力
3. Agent 通过 TaskUpdate 认领任务：
   TaskUpdate(taskId="T001", owner="worker-auth", status="in_progress")
4. 开始执行
```

**分配模式（Push）：**

```
1. Team Lead 根据 Spec 依赖图和 Agent 空闲状态
2. 主动分配：TaskUpdate(taskId="T001", owner="worker-auth")
3. 通知 Agent（SendMessage）
4. Agent 接收任务，更新状态为 in_progress
```

### 11.5 Spec 版本与追溯

每个 Spec 文件的变更必须可追溯：

```markdown
## Spec 变更记录
| 版本 | 日期 | 变更内容 | 变更人 |
|------|------|---------|--------|
| v1.0 | 2026-04-17 | 初始版本 | admin |
| v1.1 | 2026-04-18 | 增加 refresh_token 要求 | admin |
```

- Spec 文件纳入 Git 版本控制
- Agent 生成代码时记录使用的 Spec 版本
- 代码注释中包含 Spec 引用：`# Spec: F001 v1.1`
- 变更 Spec 后，相关 Agent 任务需要重新评估

---

## 第 12 章：上下文共享与传播

### 12.1 上下文传播问题

多 Agent 场景下，每个 Agent 有独立的上下文窗口。当 Agent A 完成的工作不被 Agent B 知晓时，产生信息孤岛。

### 12.2 上下文传播机制

```
Agent A 完成 T001（实现认证模块）
        │
        ▼
┌──────────────────────────────────┐
│ 1. Agent A 生成上下文摘要          │
│    → 写入 .omc/context/T001.md    │
│    包含：                         │
│    · 变更文件列表                  │
│    · 新增 API 签名                  │
│    · 关键设计决策                  │
│    · 已知限制                      │
│    · Git commit SHA               │
└──────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────┐
│ 2. Agent B 启动 T007 时            │
│    → 自动读取 .omc/context/T001.md│
│    → 注入上下文窗口               │
│    → 基于最新状态工作              │
└──────────────────────────────────┘
```

### 12.3 上下文摘要格式

```markdown
# 上下文摘要 - T001

## 基本信息
- Task: T001
- Agent: worker-auth
- Completed: 2026-04-18T11:30:00Z
- Branch: feature/auth-backend
- Commit: a1b2c3d

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
- 黑名单存储在内存中（后续迁移到 Redis）

## 已知限制
- 不支持多租户隔离
- token 撤销后黑名单最长 15 分钟生效
```

### 12.4 上下文传播规则

| 规则 | 说明 |
|------|------|
| **下游必读** | 下游 Agent 启动前必须读取所有上游依赖的上下文摘要 |
| **变更通知** | 上游 Agent 完成工作后自动通知下游等待的 Agent |
| **版本匹配** | 下游 Agent 使用上游 Agent 提交的 commit SHA 作为基准 |
| **过期清理** | 上下文摘要保留 30 天，过期自动清理 |

---

## 第 13 章：多 Agent 测试协调

### 13.1 测试并行策略

```
┌──────────────────────────────────────┐
│ Test Agent 集群                        │
│                                      │
│  Agent T1: 单元测试（按模块分区）       │
│  Agent T2: 集成测试（按服务分区）       │
│  Agent T3: E2E 测试（按场景分区）       │
│  Agent T4: 安全测试（SAST + 渗透）     │
│                                      │
│  协调器：汇总结果 → 生成测试报告        │
└──────────────────────────────────────┘
```

### 13.2 测试数据隔离

| 测试类型 | 数据隔离方式 |
|---------|-------------|
| 单元测试 | Mock 所有外部依赖，无需隔离 |
| 集成测试 | 独立测试数据库（每个 Agent 用不同 schema） |
| E2E 测试 | 容器化测试环境，测试后销毁 |
| 性能测试 | 独占环境，避免与其他测试互相干扰 |

### 13.3 测试结果汇总

```yaml
# .omc/test-results/aggregate.yaml
timestamp: 2026-04-18T12:00:00Z
agents:
  worker-auth:
    unit_tests: { passed: 12, failed: 0, skipped: 0 }
  worker-api:
    unit_tests: { passed: 24, failed: 1, skipped: 2 }
    integration_tests: { passed: 8, failed: 0, skipped: 0 }
  worker-e2e:
    e2e_tests: { passed: 15, failed: 0, skipped: 1 }
summary:
  total_passed: 59
  total_failed: 1
  total_skipped: 3
  overall: FAILED  # 有失败即整体失败
```

---

## 第 14 章：Agent 资源配额

### 14.1 配额定义

每个 Agent 在启动时被分配资源配额：

| 资源类型 | 配额示例 | 超限行为 |
|---------|---------|---------|
| API 调用次数 | 50 次/任务 | 停止执行，上报 Team Lead |
| 上下文窗口使用 | 80% | 触发上下文压缩 |
| 文件写入数 | 10 个文件/任务 | 警告，超过 15 个阻断 |
| 执行时间 | 30 分钟/任务 | 超时终止 |
| 自修轮次 | 3 轮 | 超限转人工 |

### 14.2 配额配置

```yaml
# .omc/agent-quota.yaml
defaults:
  max_api_calls: 50
  max_file_writes: 10
  max_execution_minutes: 30
  max_self_correction_rounds: 3

by_agent_type:
  Explore:
    max_api_calls: 30
    max_file_writes: 0  # 只读
    max_execution_minutes: 15
  Plan:
    max_api_calls: 40
    max_file_writes: 0  # 不写代码
    max_execution_minutes: 20
  general-purpose:
    max_api_calls: 50
    max_file_writes: 15
    max_execution_minutes: 45
```

---

## 第 15 章：Agent 生命周期管理

### 15.1 生命周期状态

```
created → warming → idle → in_progress → [completed | failed | cancelled]
                                        → handoff → in_progress (next agent)
```

### 15.2 生命周期事件处理

| 事件 | 触发动作 |
|------|---------|
| Agent 创建 | 加载团队配置、权限策略、上下文模板 |
| Agent 空闲 | 等待 TaskList 分配、超时 15 分钟自动休眠 |
| Agent 完成 | 生成总结、释放资源、通知 Team Lead |
| Agent 失败 | 收集日志、标记任务、触发恢复协议（第 10 章） |
| Agent 取消 | 保留 Git 工作区、释放锁、记录取消原因 |

### 15.3 团队清理

所有 Agent 完成任务后，Team Lead 执行清理：

```bash
# Team Lead 完成所有任务后
TeamDelete  # 清理团队目录和任务列表
# 关闭所有 Worker Agent
SendMessage(to="worker-auth", message="shutdown")
SendMessage(to="worker-api", message="shutdown")
```

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
