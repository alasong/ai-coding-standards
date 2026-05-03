# AI Coding 规范 v6.0：多 Agent 编排

> 版本：v6.0 | 2026-05-02
> 定位：Agent 类型、角色定义、会诊模式、团队管道、冲突解决
> 前置：[01-core.md](01-core.md)（原则）、[02-state-machine.md](02-state-machine.md)（状态机）、[03-structured-constraints.md](03-structured-constraints.md)（约束文件）

---

## 第 1 章：Agent 类型

| 类型 | 能力 | 适用场景 |
|------|------|---------|
| Explore | 只读（Read、Grep、Glob、Bash） | 代码探索、文件搜索 |
| Plan | 只读 + 规划 | 架构设计、实现规划 |
| general-purpose | 全部工具 | 实现、调试、重构 |

安全约束：
- Sub-Agent 继承主 Agent 的权限限制（deny 规则）
- 不得修改安全敏感文件（secrets/、.env）
- 所有输出必须经过主 Agent 验证

---

## 第 2 章：会诊模式（质量导向）

### 2.1 两种多 Agent 模式

| 维度 | 流水线模式 | 会诊模式 |
|------|-----------|---------|
| 目的 | 效率：并行开发不同模块 | 质量：多视角审视同一产出 |
| 结构 | 接力式（A 做完传 B） | 会诊式（A/B/C 独立审视同一对象） |
| 上下文 | 每个 Agent 只看自己那部分 | 每个 Agent 加载不同视角的规范 |
| 产出 | 代码片段拼装 | 单一高质量产出 + 多视角审查报告 |

### 2.2 会诊模式执行规则

| 规则 | 说明 |
|------|------|
| **独立上下文** | 每个 Agent 加载不同视角的规范章节，不共享完整对话 |
| **独立判断** | Agent 之间不看彼此中间结论，只做独立判断 |
| **文件传递** | 通过文件（不是上下文）传递产出物 |
| **Gate 汇总** | 所有 Agent 产出必须有明确 Pass/Fail，Gate Checker 做最终裁定 |
| **动态组建** | 小任务 2-3 个 Agent，大任务 5+ 个 |

### 2.3 任务复杂度与 Agent 数量

| 复杂度 | Agent 数量 | 启用角色 | 示例 |
|--------|-----------|---------|------|
| 简单（≤50 行，单文件） | 1 | 单 Agent | 修复 typo、添加日志 |
| 中等（≤500 行，2-3 文件） | 2-3 | Coder + Gate Checker (+ Security) | 新增 API 端点 |
| 复杂（>500 行，多模块） | 4-5 | Architect + Coder + Test + Gate Checker | 新增认证模块 |
| 关键（安全/资金/核心） | 5+ | Architect + Coder + Test + Security + Gate Checker | 支付流程、权限系统 |

### 2.4 三层执行架构

```
Layer 1: Director Agent（活编译器）
  - 运行时读取规范 Markdown，判断任务复杂度
  - 动态组建会诊团队，为每个 Agent 精确加载规范章节
  - 触发 Gate Checker，收集证据链

Layer 2: Agent 角色定义（上下文隔离）
  - .normalized/ 目录下每个角色的独立规则
  - 每个 Agent 只加载与自己视角相关的规范章节

Layer 3: Hard Enforcement（硬兜底）
  - pre-commit hooks: P5 密钥/P13 错误处理
  - CI gates: P3 TDD/P7 Spec/P8 批量
  - 代码防护兜底
```

---

## 第 3 章：Agent 角色注册表

| 规范角色 | 覆盖 IPD Phase | 职责 |
|---------|--------------|------|
| researcher | Phase 0 | 市场洞察、竞品分析、五看三定 |
| analyst | Phase 1 | 概念定义、需求拆解、Kano/QFD/JTBD |
| architect | Phase 2 | 技术规划、DFX、ATA、WBS、风险矩阵 |
| planner | P23 | 方案设计 → Spec 生成 |
| coder | Phase 3 | 代码实现、调试、重构 |
| reviewer | Phase 3 | 代码审查、质量评分、幻觉检测 |
| tester | Phase 3/4 | 测试策略、E2E、flaky 测试 |
| security | Phase 3/4 | 安全漏洞检测、密钥扫描、注入防护 |
| db-migration | Phase 3 | 数据库迁移审查、数据一致性 |
| performance | Phase 3/4 | 性能基线审查、压力测试 |
| designer | Phase 1/3 | UI/UX 交互审查、可访问性 |
| ops | Phase 4/5 | 部署与可观测性审查、SLO |
| writer | Phase 4/5 | 文档质量、API 文档、CHANGELOG |
| gate-checker | 全阶段 | 证据链验证、Pass/Fail 判定 |
| explorer | 全阶段 | 只读代码搜索、分析 |
| director | 全阶段 | 会诊编排、Gate 调度、报告汇总 |

角色映射通过 `.normalized/agent-registry.yaml` 维护，将抽象角色映射到具体工具中的 Agent 类型。

### 清洗后规范

每个角色在 `.normalized/{role}-rules.md` 中有对应的工具无关指令集：
- 只提取与该角色相关的规范章节
- 治理语言翻译为指令语言
- 交叉引用展开为实际内容
- 每条规则对照原文验证，确保语义不变

---

## 第 4 章：IPD Phase 团队矩阵

| Phase | 核心角色 | 可选角色 | Gate Checker | 产出交付件 |
|-------|---------|---------|-------------|-----------|
| **Phase 0** | Researcher | Analyst、Explorer | 独立 | 五看三定报告、竞品分析 |
| **Phase 1** | Analyst | Researcher、Designer | 独立 | Kano 分类、QFD 矩阵、JTBD 场景 |
| **Phase 2** | Architect | Analyst、Performance | 独立 | ADR、WBS、风险矩阵、DFX 评估 |
| **P23** | Planner | Architect、Gate Checker | 独立 | 方案设计文档、Spec 文件 |
| **Phase 3** | Coder、Reviewer、Tester | Security、DB-Migration、Performance | 独立（每次迭代） | 代码、测试、Gate Report |
| **Phase 4** | Tester、Ops、Security | Performance、Writer | 独立 | E2E 报告、部署报告 |
| **Phase 5** | Ops、Writer | Researcher、Analyst | 定期审计 | SLO 报告、技术债清单 |

### Phase 间交接协议

| 上游 → 下游 | 交接文件 | 验证者 |
|------------|---------|--------|
| Phase 0 → Phase 1 | 五看三定报告、差异化定位 | Gate Checker |
| Phase 1 → Phase 2 | Kano 分类、QFD 矩阵、JTBD | Gate Checker |
| Phase 2 → P23 | ADR、WBS、风险矩阵 | Gate Checker + Architect |
| P23 → Phase 3 | Spec 文件、方案设计文档 | Gate Checker + Planner |
| Phase 3 → Phase 4 | 代码、测试报告 | Gate Checker |
| Phase 4 → Phase 5 | 发布版本、用户反馈 | Ops + Gate Checker |

---

## 第 5 章：冲突检测与解决

| 级别 | 定义 | 处理方式 |
|------|------|---------|
| L1 行级冲突 | 两个 Agent 修改不同行 | 自动合并 |
| L2 区域级冲突 | 两个 Agent 修改相邻行（±5 行内） | 自动检测 + 策略合并 |
| L3 语义级冲突 | 两个 Agent 修改同一函数/类/逻辑块 | 锁定文件 → 排队串行化 |

L3 流程：冻结双方写权限 → 提取变更意图（Task/Spec）→ 判断兼容性 → 不兼容则回退低优先级 → 生成冲突报告到 `.omc/logs/conflict-{timestamp}.md`。

### 文件锁定协议

- 乐观锁为主、悲观锁为辅
- 锁状态存储在 `.omc/locks/` 目录
- 锁粒度：file / region / line-range
- 死锁预防：有序请求 + 超时释放（30 分钟）+ 心跳续期（5 分钟）

---

## 第 6 章：依赖图与并行度

### 6.1 依赖推断

| 维度 | 检测方法 |
|------|---------|
| 文件级 | import/require 语句分析 |
| 函数级 | 函数调用图 |
| Spec 级 | Spec 文件中的 depends_on 声明 |
| 数据流 | 数据库 schema 变更顺序 |

检测到循环依赖时：标记 `[CYCLE-DETECTED]` → 报告循环路径 → 建议破环方案 → 等待人工确认。

### 6.2 并行度控制

保守启动 `min(ready_tasks, 4)`，运行时调整：
- 连续 2 轮无冲突 → +1
- 检测到冲突 → -1
- API 限流 → -2
- 绝对上限：8

差异化：Explore 不受限，general-purpose 受限制，Plan 最多 2 个并行。

---

## 第 7 章：协调协议

### 7.1 Agent 状态机

`pending → in_progress → [self-correction (max 3 rounds)] → completed | blocked → unblocked → in_progress | failed → [escalation] → human-review`

### 7.2 心跳与保活

心跳间隔 5 分钟。超时阈值 15 分钟：第一次超时发探测 → 第二次标记 suspect → 第三次标记 failed 并触发恢复。

### 7.3 故障恢复

| 故障类型 | 恢复策略 |
|---------|---------|
| Agent 崩溃（心跳超时 5 分钟） | 重新分配任务给新 Agent，保留工作区 |
| 自修循环耗尽（3 轮） | 标记 `[SELF-CORRECTION-EXHAUSTED]`，上报人工 |
| 依赖断裂 | 阻塞链中所有下游任务标记 `blocked_upstream_failure` |
| 资源耗尽（API 配额） | 暂停非关键 Agent，保留核心任务 |

---

## 第 8 章：Spec 驱动的 Agent 分配

一个 Spec 可映射多个 Task：

```
specs/F001-auth-module.md
  ├── T001: 实现 JWT token 生成（general-purpose）
  ├── T002: 编写认证单元测试（general-purpose，blockedBy T001）
  └── T003: 安全审查 - 认证模块（Plan，blockedBy T001, T002）
```

### 任务领取协议

- **Pull 模式**：空闲 Agent 查询 TaskList → 筛选 pending、无阻塞、类型匹配的任务 → 认领
- **Push 模式**：Team Lead 根据依赖图和 Agent 空闲状态主动分配

### 上下文传播

上游 Agent 完成后写入 `.omc/context/{task_id}.md`（变更文件列表、新增 API 签名、关键设计决策、已知限制、Git commit SHA），下游 Agent 启动前自动读取。

规则：下游必读 + 变更通知 + 版本匹配 + 过期清理（30 天）。

### 8.3 Supervisor-Worker 编排

| 角色 | 模型 | 职责 |
|------|------|------|
| Supervisor | 强 | 需求分析、任务拆分、分发、仲裁 |
| Worker | 中 | TDD 循环执行 |

流程：读取 ready Spec → 构建依赖图 → 拆分原子任务 → 按依赖分发 → 并行执行无依赖任务 → 汇总 PR → 全量测试 + 幻觉扫描 + 安全检查。

转人工：安全漏洞、架构问题、DB 迁移、性能问题、业务逻辑错误、>3 轮自修、>50 文件、密钥配置。

### 8.4 Agent SDK（Team 模式）

Agent SDK 用于多 Agent 协作的团队编排：

```
TeamCreate → TaskCreate → TaskUpdate(addBlockedBy) → Agent(team_name=...) → TaskList 监控
```

- Team Lead 通过 SendMessage 向 Worker 分配任务
- Worker 通过 TaskUpdate 更新任务状态
- Worker 完成后自动发送消息给 Team Lead
- Team Lead 通过 TaskList 查看整体进度

详见 `.normalized/agent-registry.yaml`。

### 8.5 多平台协同

| 平台 | 能力 |
|------|------|
| CLI | 完整工具集，会话级运行 |
| Desktop App | 定时任务、Remote Control |
| Cloud | 云端定时任务，关机也可运行 |

阻塞事件通过 Slack/Telegram/webhook 发送告警。完成报告自动生成。

### 8.6 分层 Agent 调度（S3/S4 专用）

S3/S4 级别下，扁平的多 Agent 并行会导致上下文爆炸和语义冲突。改用分层调度：

```
Architecture Agent (强能力模型)
  └── 职责：维护模块间接口契约，不关心模块内部实现
        │
        ├── Domain Agent A (中能力模型) ── payment 模块，负责该模块内所有 Feature
        ├── Domain Agent B (中能力模型) ── order 模块
        └── Domain Agent C (中能力模型) ── notification 模块
```

**分层规则**：
1. **Architecture Agent**：只读取和修改 `.contracts/` 目录下的 Contract 文件，不得读取模块实现代码
2. **Domain Agent**：只读取和修改自己负责的模块代码，通过 Contract 文件了解上游/下游接口约束
3. **跨模块变更**：Domain Agent 发现需要修改其他模块时，通过 Escalation Protocol（见 [03-structured-constraints.md](03-structured-constraints.md) §4）请求 Architecture Agent 协调
4. **Gate Checker**：分层架构下，每个 Domain Agent 有独立的 Gate Checker，Architecture Agent 有全局 Gate Checker

**对比会诊模式**：

| 维度 | 会诊模式（S1/S2） | 分层调度（S3/S4） |
|------|-----------------|-----------------|
| Agent 数量 | 3-5 个/Feature | N 个 Domain Agent + 1 个 Architecture Agent |
| 上下文范围 | 全部代码 | 单个模块 |
| 冲突检测 | Gate Checker 人工判断 | Contract 文件自动验证接口兼容性 |
| 适用场景 | 单 Feature 开发 | 多 Feature 并行开发 |
