# AI Coding 规范 v5.4：方案设计驱动的 Auto-Coding

> IPD 方法引擎 + 协作会诊式多 Agent + 全链路交付治理

---

## 快速开始：如何使用本规范

### Step 0：选择自治等级

| 等级 | 场景 | 人类干预 |
|------|------|---------|
| **L2（推荐默认）** | 日常开发 | 每个 PR 合并前审核 |
| L1 | 新手团队/安全敏感 | 每一步都要确认 |
| L3 | 夜间开发/成熟团队 | PR + DCP 门禁，可异步 |
| L4 | 高成熟度/低风险 | DCP + 定期审计 |

### Step 1：加载核心规范

按顺序读取（上游先于下游）：

| 优先级 | 文档 | 说明 |
|--------|------|------|
| **必读** | `01-core-specification.md` | 23 条原则（P1-P23）、自治等级、TDD、IPD 六阶段、质量响应机制 |
| **必选** | `00-philosophy.md` | 规范哲学——理解规范的设计意图 |
| 按需 | `INDEX.md` | 完整文档索引与阅读指南 |

### Step 2：需求 → Spec 链（编码前必须完成）

```
需求输入 → [需求分析] → [架构适配] → [方案设计] → [Spec 生成] → 编码执行
            DP0            DP0.5         DP0.7          DP1
```

1. 加载上下文：`domain-knowledge/` + `docs/architecture/` + `docs/domain-model/`
2. 完成四阶段，每阶段过 DCP 门禁
3. 方案通过 8 项 Quality Gate（独立 Agent 验证，非作者自评）
4. Spec 状态变为 `ready`，产出 `specs/F{NNN}-{name}.md`

### Step 3：开发（TDD 先行）

```
读 Spec → 写测试 → 提交测试(CI 记录 Red) → 写实现 → 测试通过(Green) → 重构 → 全量验证
```

- 单函数 ≤50 行，单文件 ≤200 行
- 自修复最多 3 轮，第 3 轮失败转人工
- 编码完成后执行 Skill Generalization（经验沉淀到知识库）

### Step 4：代码审查（协作会诊模式）

**5 轮独立审查**，每个 Agent 独立视角：

| Pass | 执行者 | 视角 |
|------|--------|------|
| P1 | 作者/Executor | 完整性 |
| P2 | 独立 Agent | 上下游一致性 |
| P3 | 独立 Agent | 竞品/审计/攻击者视角 |
| P4 | Gate Checker | 规范合规（只读） |
| P5 | 人类 | 战略对齐 + 风险接受度 |

### Step 5：Gate 验证（独立 Gate Checker）

| Gate | 检查内容 |
|------|---------|
| TDD | 提交顺序、Red→Green、AC 覆盖 |
| Spec | Spec 存在、状态正确、API 对齐 |
| 安全 | 密钥、SQL 拼接、eval/exec、Protected Paths |
| 质量 | 编译、test、lint、覆盖率基线 |
| 幻觉 | API 存在性、依赖、符号解析 |
| DCP | Phase checklist、深度评分独立性 |

任一 Gate FAIL → 返回修复；全部 PASS → 创建 PR

### Step 6：质量响应

| 级别 | 触发 | 动作 |
|------|------|------|
| L0 | 通过率>80% | 正常推进，成功模式入知识库 |
| L1 | 60-80% | 诊断根因，修复后重试 |
| L2 | <60% | 增强上下文，多 Agent 会诊 |
| L3 | 严重退化 | 人做决策，AI 继续编码 |

---

## 多 Agent 协作

本规范采用**协作会诊模式**（质量导向，非效率导向）——多个 Agent 独立检查同一产出，各自不同视角，交叉验证。

### Agent 角色与动态映射

| 规范角色 | Claude Code Agent |
|----------|------------------|
| Architect | `architect` |
| Coder | `general-purpose` |
| Reviewer | `code-reviewer` |
| Security | `security-reviewer` |
| Tester | `test-engineer` |
| Gate Checker | `verifier` |
| Explorer | `Explore` |
| Planner | `Plan` |
| Debugger | `debugger` |
| Simplifier | `code-simplifier` |

完整映射见 `.normalized/agent-registry.yaml`。

### 角色专属规则

每个角色有独立的清洗后规则文件（紧凑格式，逐条验证）：

| 规则文件 | 适用角色 |
|----------|---------|
| `.normalized/architect-rules.md` | 架构设计、IPD 六阶段、深度评分 |
| `.normalized/coder-rules.md` | 代码实现、TDD、工程实践 |
| `.normalized/reviewer-rules.md` | 代码审查、幻觉检测 |
| `.normalized/security-rules.md` | 安全扫描、密钥检测、Prompt 注入 |
| `.normalized/tester-rules.md` | 测试策略、AC 覆盖率、Flaky Test |
| `.normalized/gate-checker-rules.md` | Gate 验证、证据链检查 |
| `.normalized/explorer-rules.md` | 只读代码探索 |
| `.normalized/planner-rules.md` | 需求分析、方案设计、Spec 生成 |

---

## 核心原则速查

```
底线（P1-P11）：
P1 商业驱动 ── P2 DCP 门禁 ── P3 TDD 先行 ── P4 人工审查 ── P5 密钥不入
P6 单一信息 ── P7 Spec 驱动 ── P8 最小批量 ── P9 Prompt 版 ── P10 数据分级 ── P11 证据链

工程实践（P12-P22）：
P12 环境 ── P13 错误 ── P14 租户 ── P15 并发 ── P16 资源 ── P17 输入
P18 JSON ── P19 认证 ── P20 速率 ── P21 数据 ── P22 IP

链路（P23）：
需求分析 → 架构适配 → 方案设计 → Spec 生成
```

## 文档结构

| # | 文档 | 说明 |
|---|------|------|
| 00 | [规范哲学](00-philosophy.md) | 元规则、设计意图 |
| 01 | [核心规范](01-core-specification.md) | 原则、IPD 六阶段、自治等级、TDD、Spec、幻觉检测 |
| 02 | [Auto-Coding 实践](02-auto-coding-practices.md) | 自主编码、夜间开发、自修复 CI |
| 03 | [多 Agent 与多平台](03-multi-agent-multi-surface.md) | 协作会诊、Sub-Agents、多平台协同 |
| 04 | [安全与治理](04-security-governance.md) | 企业部署、权限、MCP 安全 |
| 05 | [工具参考](05-tool-reference.md) | CLI、Hooks、Skills、审查清单 |
| 06 | [CI/CD Pipeline](06-cicd-pipeline.md) | L0-L5 分层、质量门禁 |
| 07 | [反幻觉方案](07-anti-hallucination.md) | 45 种幻觉、证据链方法论 |
| 08-18 | 专项文档 | 数据库、API、部署、发布、安全等 |
| - | [完整索引](INDEX.md) | 全部文档导航 |

## 版本

| 版本 | 日期 | 变更 |
|------|------|------|
| v4.0 | 2026-04-13 | 基线版本 |
| v5.4 | 2026-04-18 | IPD 六阶段方法引擎 |
| **v5.5** | **2026-04-21** | **协作会诊式多 Agent + 质量响应机制** |
