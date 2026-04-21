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

### Step 2：组建会诊团队

每个 Phase 不是单个 Agent 独立完成，而是多角色协作。Director 根据变更类型动态组队：

| Phase | 核心团队 | 产出件 |
|-------|---------|-------|
| Phase 0 市场洞察 | Researcher + Analyst（按需） | 五看三定、竞品分析、差异化定位 |
| Phase 1 概念定义 | Analyst + Designer（按需） | Kano 分类、QFD 矩阵、JTBD 场景 |
| Phase 2 技术规划 | Architect + Performance（按需） | ADR、WBS、风险矩阵、DFX |
| 方案设计+Spec | Planner + Architect（架构适配） | 方案设计文档、Spec 文件 |
| Phase 3 开发 | Coder + Reviewer + Tester | 代码、测试、审查报告 |
| Phase 3 + 安全/资金模块 | + Security | 安全审查报告 |
| Phase 3 + 数据库变更 | + DB-Migration | 迁移脚本 + 回滚策略 |
| Phase 3 + 性能敏感 | + Performance | 性能基准报告 |
| Phase 3 + UI 变更 | + Designer | 交互审查报告 |
| Phase 4 验证发布 | Tester + Ops + Security | E2E、部署、渗透报告 |

### Step 3：需求 → Spec 链（编码前必须完成）

```
需求输入 → [需求分析] → [架构适配] → [方案设计] → [Spec 生成] → 编码执行
            DP0            DP0.5         DP0.7          DP1
```

1. 加载上下文：`domain-knowledge/` + `docs/architecture/` + `docs/domain-model/`
2. 完成四阶段，每阶段过 DCP 门禁（独立 Agent 验证，非作者自评）
3. 方案通过 8 项 Quality Gate（Planner + Architect 联合，Gate Checker 裁定）
4. Spec 状态变为 `ready`，产出 `specs/F{NNN}-{name}.md`

### Step 4：开发（TDD 先行 + 团队协作）

```
读 Spec → 写测试 → 提交测试(CI 记录 Red) → 写实现 → 测试通过(Green) → 重构 → 全量验证
```

- 单函数 ≤50 行，单文件 ≤200 行
- Coder 实现 → Reviewer 幻觉检测 → Tester AC 覆盖 → Security（安全模块） → DB-Migration（DB变更）
- 自修复最多 3 轮，第 3 轮失败转人工
- 编码完成后执行 Skill Generalization（经验沉淀到知识库）

### Step 5：代码审查（协作会诊模式）

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

16 个角色覆盖 IPD Phase 0 → Phase 5 全链路：

| 规范角色 | Claude Code Agent | 覆盖 Phase |
|----------|------------------|-----------|
| Researcher | `WebSearch` + `Explore` | Phase 0 市场洞察 |
| Analyst | `critic` | Phase 1 概念定义 |
| Architect | `architect` | Phase 2 技术规划 |
| Planner | `Plan` | P23 方案设计+Spec |
| Coder | `general-purpose` | Phase 3 开发 |
| Reviewer | `code-reviewer` | Phase 3 审查 |
| Tester | `test-engineer` | Phase 3/4 测试 |
| Security | `security-reviewer` | Phase 3/4 安全 |
| DB-Migration | `debugger` | Phase 3 DB变更 |
| Performance | `general-purpose` | Phase 3/4 性能 |
| Designer | `designer` | Phase 1/3 UI/UX |
| Ops | `general-purpose` | Phase 4/5 部署运维 |
| Writer | `writer` | Phase 4/5 文档 |
| Gate Checker | `verifier` | 全阶段 |
| Explorer | `Explore` | 全阶段 |
| Director | `critic` | 全阶段编排 |

完整映射见 `.normalized/agent-registry.yaml`。

### 角色专属规则

每个角色有独立的清洗后规则文件（紧凑格式，逐条验证）：

| 规则文件 | 适用角色 |
|----------|---------|
| `.normalized/researcher-rules.md` | 市场洞察、竞品分析、伪需求检测 |
| `.normalized/analyst-rules.md` | 概念定义、Kano、QFD、JTBD |
| `.normalized/architect-rules.md` | Phase 2 技术规划、DFX、ATA、WBS |
| `.normalized/planner-rules.md` | 方案设计 → Spec 生成 |
| `.normalized/coder-rules.md` | 代码实现、TDD、工程实践 |
| `.normalized/reviewer-rules.md` | 代码审查、幻觉检测 |
| `.normalized/security-rules.md` | 安全扫描、密钥检测、注入防护 |
| `.normalized/tester-rules.md` | 测试策略、AC 覆盖率、Flaky Test |
| `.normalized/db-migration-rules.md` | DB 迁移审查、数据一致性、回滚策略 |
| `.normalized/performance-rules.md` | 性能基线、预算、N+1 检测 |
| `.normalized/designer-rules.md` | UI/UX 交互审查、A11y |
| `.normalized/ops-rules.md` | 部署与可观测性、SLO、回滚策略 |
| `.normalized/writer-rules.md` | 文档质量、API 文档、CHANGELOG |
| `.normalized/gate-checker-rules.md` | Gate 验证、证据链检查 |
| `.normalized/explorer-rules.md` | 只读代码探索 |
| `.normalized/director-rules.md` | 会诊编排、Gate 调度、团队组建 |
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
