# v4 vs Auto-Coding 冲突解决记录

> 版本：v5.0 | 2026-04-14
> 来源：`ai-coding-specification-v4.md`（25 章，~2197 行）vs `auto-coding/`（5 份文档，~5334 行）
> 状态：全部 12 个冲突已解决（3 BLOCKING + 5 WARNING + 4 MINOR）

---

## 解决原则

1. **v4 是治理标准**，Auto-Coding 是实现能力参考
2. **安全边界不后退**：v4 的 P1-P10 核心原则在任何自治等级下不可违反
3. **自主性在边界内最大化**：通过 L1-L4 等级递进，在安全框架内增加执行灵活性
4. **每份 Auto-Coding 文档末尾添加 "v4 合规注释"**，将能力映射到 v4 条款

---

## BLOCKING 冲突（3 个）

### BLOCKING-1：TDD 强制

| 维度 | v4 立场 | Auto-Coding 立场 |
|------|---------|-----------------|
| 条款 | P3：实现前必须先写测试，Red→Green 强制 | AC-05：[实现]→[测试]→[诊断]→[修复]，测试与实现同时生成 |
| 风险 | 测试先行是质量保障的核心，颠倒后 AI 幻觉无法被捕获 | — |

**解决方案：**
- Auto-coding 循环重排为：`[生成测试] → [验证 Red] → [实现] → [验证 Green] → [Refactor]`
- Auto-coding 流水线中添加 TDD 合规检查 Gate
- 所有自治等级（L1-L4）统一遵守，无例外
- 自修复循环（最多 3 轮）中每轮都必须重新验证 Red→Green

**实施位置：**
- `01-core-specification.md`：第 2 章 TDD Red→Green→Refactor 流程
- `02-auto-coding-practices.md`：第 1 章持续编码循环（TDD 版本）、第 4 章 Self-Correction Loop

---

### BLOCKING-2：人工审查

| 维度 | v4 立场 | Auto-Coding 立场 |
|------|---------|-----------------|
| 条款 | P4：所有 AI 代码合并前必须经过人工 Code Review，两层审查强制 | AC-05：[人工审查（可选）]，"自动合并琐碎修复" |
| 风险 | 自动合并绕过人工审查，AI 幻觉可能引入生产缺陷 | — |

**解决方案：**
- 从所有 Auto-Coding 流水线中移除 `[人工审查（可选）]`
- 明确：**自动合并与 v4 P4 不兼容**
- L1-L3：每次 PR 合并前强制人工审查
- L4：可改为**定期审计**（每周），但仅限 trivial fix（lint 修复、拼写修正）
- AI-as-Reviewer（Layer 1）+ Human Reviewer（Layer 2）两层审查架构不变
- 如团队需要自动合并，必须**显式豁免 P4**（不在本规范范围内）

**实施位置：**
- `01-core-specification.md`：P4 原则说明、L1-L4 约束矩阵
- `02-auto-coding-practices.md`：夜间开发模式（DP3 早晨审查）、自修复 CI（人工升级点）
- `03-multi-agent-multi-surface.md`：Agent Teams 质量门禁
- `04-security-governance.md`：审计链、合规要求

---

### BLOCKING-3：MCP 安全边界

| 维度 | v4 立场 | Auto-Coding 立场 |
|------|---------|-----------------|
| 条款 | P5：密钥不入代码。P10：发送 AI 前必须数据分类，机密数据禁止 | AC-01：数据库分析师 Sub-agent 直连数据库。AC-04：MCP 连接数据库/API/文件系统 |
| 风险 | MCP 直连可能暴露密钥、PII、机密数据到 AI 上下文 | — |

**解决方案：**
- MCP Agent **必须**实现 v4 数据分类过滤层（v4 10.3 节）
- 数据进入 AI 上下文前**必须脱敏**：
  - PII（个人身份信息）：掩码/哈希
  - 密钥/Token：完全过滤
  - 业务机密：聚合/统计后发送
- 数据库 MCP Agent 查询结果自动应用脱敏规则
- 文件系统 MCP Agent 限制可访问路径（白名单模式）
- API MCP Agent 过滤响应头中的敏感信息

**实施位置：**
- `04-security-governance.md`：第 4 章 MCP 安全（数据分类过滤器、数据库脱敏层、API 访问控制、文件系统范围限制）
- `01-core-specification.md`：P5、P10 原则的 Auto-Coding 含义
- `05-tool-reference.md`：MCP 安全配置模板

---

## WARNING 冲突（5 个）

### WARNING-4：DCP 门禁 vs 持续交付

| 维度 | v4 立场 | Auto-Coding 立场 |
|------|---------|-----------------|
| 条款 | P2：每个阶段必须通过决策门 | AC-05：Agent 从 backlog 自主选取任务，无 DCP 门禁 |

**解决方案：**
- L1-L3：持续循环必须在 v4 Phase 3 入口标准约束下运行，循环前加 **Phase Gate Check**
- L4：可简化 DCP（保留核心检查，跳过文档要求），但**不可完全跳过**
- 异步 Decision Points：夜间运行前执行 DP1/DP2，早晨审查执行 DP3

**实施位置：**
- `01-core-specification.md`：P2 原则、Async Decision Points
- `02-auto-coding-practices.md`：夜间开发模式、周末开发模式的前置检查

---

### WARNING-5：Spec 驱动 vs 自主选取

| 维度 | v4 立场 | Auto-Coding 立场 |
|------|---------|-----------------|
| 条款 | P7：AI 生成代码必须有显式 Spec 文件作为输入 | AC-05：Agent 从 backlog 按优先级自主选取，无显式 Spec 验证 |

**解决方案：**
- Agent 必须从 `specs/` 目录读取任务
- 执行前加 **Spec Validation Gate**：检查 Spec 文件存在且状态为 `ready`
- L4 可简化为 backlog item（但 backlog item 必须包含 Spec 引用链接）
- Spec 状态机：`draft → ready → in-progress → done → archived`

**实施位置：**
- `01-core-specification.md`：P7 原则、Spec 状态机（附录 A09）
- `02-auto-coding-practices.md`：Spec-Driven 自主开发模式

---

### WARNING-6：Prompt 版本化

| 维度 | v4 立场 | Auto-Coding 立场 |
|------|---------|-----------------|
| 条款 | P9：所有用于生成代码的 Prompt 必须版本化在 `prompts/` 中 | AC-01：Sub-agents 通过 `--agents` JSON 动态定义，内联 Prompt |

**解决方案：**
- 动态构建的 Prompt 在使用前**必须持久化**到 `prompts/` 并自动递增版本号
- L4 可自动持久化动态 Prompt（无需人工操作），但仍需版本记录
- Prompt 版本格式：`{name}-v{major}.{minor}.md`

**实施位置：**
- `01-core-specification.md`：P9 原则、Prompt 版本管理
- `05-tool-reference.md`：配置模板中的 Prompt 目录结构

---

### WARNING-7：两层 AI 审查

| 维度 | v4 立场 | Auto-Coding 立场 |
|------|---------|-----------------|
| 条款 | 7.5：AI Reviewer + Human Reviewer，两者都阻塞合并 | AC-02："每个 PR 在几分钟内被审查，无人工审查瓶颈" |

**解决方案：**
- Claude 自动审查 = v4 Layer 1（AI Reviewer）
- Layer 2（人工审查）**仍然强制**
- "无人工审查瓶颈"的表述修正为："AI 审查在几分钟内完成，人工审查作为最终门禁"
- 自修复 CI 中的自动批准仅适用于 lint/test fix，不适用于功能变更

**实施位置：**
- `01-core-specification.md`：第 7 章两层审查、AI-as-Reviewer
- `03-multi-agent-multi-surface.md`：Agent Teams 质量门禁

---

### WARNING-8：bypassPermissions

| 维度 | v4 立场 | Auto-Coding 立场 |
|------|---------|-----------------|
| 条款 | P5/S01-S07：安全基线强制。`.aicoding.yaml` 禁止危险操作 | AC-03/AC-04：bypassPermissions 跳过所有权限检查 |

**解决方案：**
- `bypassPermissions` **仅限** v4 定义的完全隔离开发环境（沙箱 CI）
- 生产环境/预发布环境/主分支：**禁止使用**
- 所有使用 bypassPermissions 的场景必须在 `.aicoding.yaml` 中显式标注理由
- 审计日志中必须记录 bypass 事件

**实施位置：**
- `04-security-governance.md`：权限模式、bypass 合规说明
- `05-tool-reference.md`：Settings 配置中的安全警告

---

## MINOR 冲突（4 个）

### MINOR-9：最小批量 vs 多特性

| 维度 | v4 立场 | Auto-Coding 立场 |
|------|---------|-----------------|
| 条款 | P8：AI 一次只生成一个函数/小模块 | AC-05：周末完成 3-5 个特性 PR |

**解决方案：**
- P8 约束的是**单次生成的粒度**，不是总范围
- Assembly Line 中每个 Worker 的工作仍遵循 P8
- 周末完成 3-5 个特性 = 3-5 个独立的 Spec，每个 Spec 内部遵循 P8
- **结论：不冲突，需文档澄清**

---

### MINOR-10：自修复循环次数

| 维度 | v4 立场 | Auto-Coding 立场 |
|------|---------|-----------------|
| 条款 | 4B：自修复最多 3 轮，超过转人工 | AC-05：最大迭代次数 "50-200 轮" |

**解决方案：**
- **粒度不同**：
  - 3 轮 = 每轮内的自修复次数（Self-Correction Loop 内部）
  - 50-200 轮 = 总任务循环数（整个 backlog 的处理轮次）
- 每个任务循环内部的自修复仍然限制为最多 3 轮
- **结论：不冲突，需文档澄清**

---

### MINOR-11：Decision Point vs 夜间运行

| 维度 | v4 立场 | Auto-Coding 立场 |
|------|---------|-----------------|
| 条款 | 3D：DP1-DP4 要求在里程碑处人工确认 | AC-05：夜间运行从傍晚到早晨自主执行 |

**解决方案：**
- DP1（需求理解）/ DP2（架构方案）在夜间运行**前**执行
- DP3（发布决策）在早晨审查**时**执行
- DP4（紧急变更）按需执行，夜间触发时暂停并告警
- 文档化为 **异步 Decision Points**

**实施位置：**
- `01-core-specification.md`：第 6 章 Async Decision Points
- `02-auto-coding-practices.md`：夜间开发模式的 DP 时间线

---

### MINOR-12：AI 质量降级

| 维度 | v4 立场 | Auto-Coding 立场 |
|------|---------|-----------------|
| 条款 | 3.4：通过率低于 60% 自动降级 | AC-05：分层自治但无基于质量的自动降级 |

**解决方案：**
- Auto-coding 流水线中添加**通过率追踪**
- v4 阈值 breached 时**自动降低自治等级**：
  - 通过率 < 60%：立即降级一级
  - 通过率 < 40%：降至 L1（完全人工辅助）
  - 连续 3 天通过率 > 90%：可申请升级
- **实施位置：**
  - `01-core-specification.md`：第 8 章质量降级、降级检查清单（附录 A06）
  - `02-auto-coding-practices.md`：Auto-Coding 指标（成功率、干预率）

---

## 协同清单（10 项）

| # | 领域 | 联合价值 |
|---|------|---------|
| 1 | 多 Agent 协同 | Auto-coding SDK 实现 v4 的概念模式；v4 提供治理框架 |
| 2 | 定时自动化 | 定时任务在排定时间执行 v4 Phase 3 开发循环 |
| 3 | 安全治理 | 企业控制强化 v4 基线；v4 数据分类指导 MCP 访问 |
| 4 | 自修复循环 | Auto-coding 在规模上实现 v4 概念；v4 的 3 轮限制提供安全边界 |
| 5 | 代码审查自动化 | Auto-coding 管理审查 = v4 Layer 1 的技术实现 |
| 6 | 上下文管理 | 跨会话的有界上下文，Progressive Disclosure + Memory 系统 |
| 7 | CI/CD 集成 | Auto-coding 提供执行 v4 门禁的流水线实现 |
| 8 | 夜间开发 | 夜间运行与 v4 AI-First 对齐；早晨审查满足 P4 |
| 9 | 成本控制 | CLI 标志实现 v4 成本控制机制（预算、熔断） |
| 10 | 状态持久化 | 结构化记忆补充文件级状态持久化 |

---

## 解决状态总览

| 严重度 | 总数 | 已解决 | 状态 |
|--------|------|--------|------|
| **BLOCKING** | 3 | 3 | ✅ 全部解决 |
| **WARNING** | 5 | 5 | ✅ 全部解决 |
| **MINOR** | 4 | 4 | ✅ 全部解决 |
| **合计** | 12 | 12 | ✅ 全部解决 |
