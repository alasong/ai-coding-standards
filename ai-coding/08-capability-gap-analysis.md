# AI Coding 规范集：能力差距分析与补齐方案

> 版本：v5.2-draft | 日期：2026-04-17
> 基准：技能自创建平台技术方案.md vs ai-coding/ 规范集 v5.1
> 范围：01-core-specification.md 至 07-anti-hallucination.md 共 7 份文档

---

## 1. 根因分析

规范集 v5.1 的设计假设是：**IPD Phase 0-2（市场洞察、概念定义、详细规划）= 人类决策，Phase 3+（开发、验证、生命周期）= AI 编码**。这导致：

- P7 Spec 驱动假设 Spec 已存在，但 Spec 从何而来没有定义
- Prompt Chaining（6.2 节）仅覆盖"已有 Spec 后的代码生成链"，不覆盖"需求→架构→方案→Spec"链
- .gate/ 输出格式全部面向代码验证（编译、测试、lint、SAST），无设计产物格式
- 无领域知识注入机制，AI 在 Phase 0-2 缺乏行业上下文
- 无"方案质量"的门——从需求到 Spec 之间没有验证点
- 无能力泛化机制，解决一个问题后无法沉淀为可复用 skill

**结论**：规范集在"编码执行"侧高度成熟，在"方案设计"侧存在空白。AI 要真正端到端参与 IPD Phase 0-2，必须补齐以下五处能力。

---

## 2. 五处能力差距

### GAP-01：缺少"需求→方案→Spec"Prompt 链

| 维度 | 现状 | 差距 |
|------|------|------|
| Prompt Chaining | 01-core 6.2 节定义了 analyze→design→code→verify→fix 链 | 链的起点是"已有 Spec"，不包含需求分析→架构设计→方案设计→Spec 生成 |
| IPD 映射 | 1.4 节声明 Phase 0-2 = 人类决策 | AI 无法参与需求结构化、方案选型、架构草图 |
| Decision Point | 7.3 节 DP1/DP2 在"AI 分析完代码后"介入 | 无"AI 分析完需求后"的决策点 |

**影响**：从"业务需求"到"可执行的 Spec"这段链路完全依赖人工，Auto-Coding 只能从 Spec ready 之后开始，无法端到端。

### GAP-02：缺少交付物模板

| 维度 | 现状 | 差距 |
|------|------|------|
| 代码产物 | .gate/ 下有完整的编译/测试/覆盖率/SAST 格式 | 无架构文档模板、技术方案模板、解决方案模板 |
| Spec 模板 | 01-core 5.2 节有 Feature Spec 的 YAML frontmatter + Markdown 结构 | 无 Architecture Doc、Solution Design Doc 的结构定义 |
| 验证 Gate | Spec Validation Gate（5.3 节）、Code Review Gate 均有明确检查项 | 设计文档无验证标准，质量靠人感 |

**影响**：AI 生成的设计文档格式不一致、内容不可验证、无法自动检查与 PRD/架构的一致性。

### GAP-03：缺少领域知识预加载机制

| 维度 | 现状 | 差距 |
|------|------|------|
| 上下文加载 | Progressive Disclosure（4.5.3 节）P0/P1/P2 分级 | 分级对象是代码文件和 Spec，无行业/领域知识库的加载入口 |
| Context Manifest | 6.4 节 `required_context` 指定文件+行号 | 无法指定"注入 XX 行业最佳实践"、"加载 XX 技术栈约束" |
| 数据分级 | P10 + pre-send 扫描保护敏感数据 | 领域知识本身可能是受限的（行业机密、客户数据），无加载时的安全策略 |

**影响**：AI 在方案设计阶段缺乏行业上下文，产出的方案可能是通用的但非领域适配的。例如金融行业的合规要求、医疗行业的数据保护规范等无法自动注入。

### GAP-04：缺少方案质量评估 Gate

| 维度 | 现状 | 差距 |
|------|------|------|
| Spec Validation Gate | 01-core 5.3 节：与 PRD 一致性、与架构一致性、AC 可测试性等 6 项 | 验证的是"Spec 格式是否合格"，不验证"方案是否可行" |
| Code Review Gate | 两层审查（AI Reviewer + Human Reviewer）+ CI 全量验证 | 验证的是"代码是否实现 Spec"，不验证"方案本身是否正确" |
| 中间缺失 | — | **Spec 从何而来？Spec 背后的技术方案是否经过质量评估？无 Gate。** |

**影响**：一个格式完美但技术不可行的 Spec 可以通过 Spec Validation Gate，驱动 AI 生成错误代码，浪费大量算力。

### GAP-05：缺少能力泛化/演进机制

| 维度 | 现状 | 差距 |
|------|------|------|
| 单次开发 | Spec→Test→Code→Gate→PR 闭环完善 | 闭环结束即终止，无"沉淀为通用 skill"的机制 |
| 技能管理 | 03-multi-agent 定义了 Sub-Agent 文件定义方式 | Sub-Agent 是人工编写的，无"从已验证方案自动泛化为 Sub-Agent"的机制 |
| 知识积累 | Sub-Agent memory 字段支持 project 级持久化 | 仅记录常见模式和约定，不包含"已解决问题的通用解法" |

**影响**：每解决一个问题，系统不会变得更聪明。同一个问题族反复从头开发，无法复用已验证的模式。

---

## 3. 补齐方案

### 3.1 Requirement→Solution→Spec Prompt Chain（新 P23）

**原则定义**：

> **P23 方案设计驱动** | 从需求到 Spec 的转换必须由结构化的 Prompt 链完成，每一步的输出经人工确认后进入下一步。

**链结构**：

```
[Phase 0: 需求分析]              [Phase 1: 架构设计]              [Phase 2: 方案设计]              [Phase 3: Spec 生成]
输入：PRD / 用户故事 / Jira        输入：需求分析报告               输入：架构约束 + 领域知识          输入：方案文档
输出：需求结构文档                  输出：架构适配报告               输出：技术解决方案                 输出：Feature Spec
模型：opus                         模型：opus                       模型：opus                         模型：sonnet
Decision Point: DP0               Decision Point: DP0.5            Decision Point: DP0.7             进入 Spec Validation Gate
```

**每步验证**：

| 步骤 | 验证方式 | 失败处理 |
|------|---------|---------|
| 需求分析 | 人工确认需求覆盖度（对照 PRD 逐条） | 补充缺失需求，重新分析 |
| 架构设计 | 人工确认不违反 ADR（Architecture Decision Record） | 调整架构约束，重新设计 |
| 方案设计 | 进入方案质量 Gate（见 3.4） | Gate 不通过，重新方案 |
| Spec 生成 | 进入 Spec Validation Gate（已有） | Gate 不通过，修正 Spec |

**配置示例**：

```yaml
# .aicoding.yaml
requirement_to_spec_chain:
  enabled: true
  steps:
    - id: analyze
      name: "需求分析"
      prompt_file: "prompts/requirement-analysis.md"
      model: opus
      input: ["prd.md", "user_stories.md"]
      output: "requirement-analysis.md"
      gate: "human_confirm"
    - id: architect
      name: "架构适配"
      prompt_file: "prompts/architecture-adaptation.md"
      model: opus
      input: ["requirement-analysis.md", "architecture.md", "adr/"]
      output: "architecture-adaptation.md"
      gate: "adr_compliance_check"
    - id: design
      name: "方案设计"
      prompt_file: "prompts/solution-design.md"
      model: opus
      input: ["requirement-analysis.md", "architecture-adaptation.md", "domain-knowledge/"]
      output: "solution-design.md"
      gate: "solution_quality_gate"
    - id: spec
      name: "Spec 生成"
      prompt_file: "prompts/spec-generation.md"
      model: sonnet
      input: ["solution-design.md"]
      output: "specs/F{NNN}-{name}.md"
      gate: "spec_validation_gate"
  max_retries_per_step: 3
  fail_action: escalate_to_human
  trace_file: ".gate/requirement-chain-trace.json"
```

**与现有 DP 的关系**：在 DP1 之前新增 DP0（需求理解）、DP0.5（架构方向）、DP0.7（方案可行性），形成完整的 7 个决策点。

### 3.2 交付物模板

#### 3.2.1 架构文档模板（`templates/architecture-doc.md`）

```markdown
# {Project} 架构文档

> 版本：{version} | 日期：{date} | 状态：{draft|reviewed|approved|deprecated}
> 作者：{human|ai-assisted} | 审查人：{name}

## 1. 系统概述
- 系统目标
- 非目标
- 关键约束

## 2. 架构决策记录（ADR）
| # | 决策 | 理由 | 替代方案 | 状态 |
|---|------|------|---------|------|

## 3. 模块划分
### 3.1 模块清单
| 模块 | 职责 | 接口 | 依赖 |
|------|------|------|------|

### 3.2 依赖关系图
（Mermaid 或文本描述）

## 4. 接口契约
### 4.1 API 设计
| 端点 | 方法 | 输入 | 输出 | 错误码 |
|------|------|------|------|--------|

### 4.2 内部接口
| 模块 A | 模块 B | 通信方式 | 数据格式 |

## 5. 数据模型
| 实体 | 字段 | 约束 | 索引 |
|------|------|------|------|

## 6. 安全设计
- 认证方案
- 授权模型
- 数据加密
- 审计日志

## 7. 非功能需求
| 维度 | 指标 | 目标值 | 验证方式 |
|------|------|--------|---------|

## 8. 部署架构
- 环境拓扑
- 容器/服务编排
- 基础设施依赖
```

#### 3.2.2 技术方案模板（`templates/solution-design.md`）

```markdown
# {Feature} 技术方案

> 版本：{version} | 日期：{date} | 关联 Spec：{F{NNN}}
> 输入：{requirement-analysis.md, architecture.md, domain-knowledge}

## 1. 问题定义
- 要解决什么问题
- 为什么不用现有方案
- 成功标准（量化）

## 2. 方案概述
- 核心思路
- 关键设计决策
- 影响范围（文件/模块列表）

## 3. 详细设计
### 3.1 数据流
（输入→处理→输出）

### 3.2 组件设计
| 组件 | 职责 | 输入 | 输出 | 异常处理 |
|------|------|------|------|---------|

### 3.3 接口变更
| 接口 | 变更类型 | 兼容性 | 迁移方案 |
|------|---------|--------|---------|

### 3.4 数据变更
- Schema 变更（如适用）
- 迁移脚本（如适用）
- 回滚方案

## 4. 风险分析
| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|

## 5. 验收标准
- 功能验收（映射到 Spec AC）
- 性能验收
- 安全验收
- 兼容性验收

## 6. 实施计划
- 任务拆分（符合 P8 最小批量）
- 依赖顺序
- 预估工时
```

#### 3.2.3 设计产物 Gate 输出格式

```json
// .gate/design-output.json
{
  "type": "design_deliverable",
  "deliverable_type": "architecture_doc|solution_design|requirement_analysis",
  "timestamp": "2026-04-17T10:00:00Z",
  "source_file": "docs/architecture-v2.md",
  "checklist": {
    "sections_complete": true,
    "adr_references_valid": true,
    "interfaces_defined": true,
    "security_addressed": true,
    "non_functional_specified": true,
    "risk_assessed": true
  },
  "ai_claims": [
    "模块划分覆盖全部 PRD 需求",
    "无循环依赖",
    "接口向后兼容"
  ],
  "evidence": {
    "requirement_coverage": ".gate/requirement-coverage.json",
    "dependency_analysis": ".gate/dependency-graph.json",
    "adr_compliance": ".gate/adr-compliance.json"
  },
  "reviewed_by": "@architect",
  "status": "approved"
}
```

### 3.3 领域知识预加载（Context Loading Gate）

**机制定义**：在需求分析链启动前，必须通过 Context Loading Gate 注入领域知识。

```
Context Loading Gate:
  [ ] 领域知识库存在（domain-knowledge/{industry}/ 目录非空）
  [ ] 知识范围声明明确（覆盖哪些业务规则、法规约束、技术栈特征）
  [ ] 知识来源可信（官方文档、行业标准、已验证项目）
  [ ] 数据分级扫描通过（无 Restricted 数据注入）
  [ ] 知识时效性确认（无过时标准）
```

**知识目录结构**：

```
domain-knowledge/
├── {industry}/                    # 如：finance, healthcare, ecommerce
│   ├── business-rules.md          # 行业业务规则
│   ├── compliance-requirements.md # 法规合规要求
│   ├── security-standards.md      # 安全标准
│   └── common-patterns.md         # 行业通用模式
├── {tech-stack}/                  # 如：go-microservices, react-nextjs
│   ├── best-practices.md          # 最佳实践
│   ├── anti-patterns.md           # 反模式
│   └── architecture-templates.md  # 架构模板
└── {project-specific}/            # 项目特定知识
    ├── domain-glossary.md         # 领域术语表
    └── legacy-constraints.md      # 遗留系统约束
```

**Spec 扩展字段**：

```yaml
# Spec frontmatter 新增
required_domain_knowledge:
  - industry: "finance"
    scope: ["compliance-requirements", "security-standards"]
  - tech_stack: "go-microservices"
    scope: ["best-practices"]
  - project: "payment-gateway"
    scope: ["domain-glossary"]
```

**Prompt 注入方式**：在 Requirement→Solution→Spec 链的每个 Prompt 中，按 `required_domain_knowledge` 声明自动注入对应知识文件的内容（受 P10 数据分级约束）。

### 3.4 方案质量评估 Gate（Solution Quality Gate）

**位置**：在方案设计完成后、Spec 生成之前。位于 Requirement→Solution→Spec 链的 Phase 2 和 Phase 3 之间。

```
需求分析 ──(DP0)──▶ 架构设计 ──(DP0.5)──▶ 方案设计 ──▶ [Solution Quality Gate] ──▶ Spec 生成 ──▶ [Spec Validation Gate]
```

**检查项**：

| # | 检查项 | 验证方式 | 不通过后果 |
|---|--------|---------|-----------|
| 1 | **技术可行性** | 方案中的关键技术点是否有可行实现路径（非虚构 API/库） | 阻塞，标记技术幻觉 |
| 2 | **架构一致性** | 不违反任何已存在的 ADR | 阻塞，列出冲突 ADR |
| 3 | **影响分析完整** | 影响范围声明 vs 实际代码依赖图是否一致 | 标记范围幻觉 |
| 4 | **风险已识别** | 风险清单中无遗漏的高概率/高影响项 | 标记风险遗漏 |
| 5 | **回滚方案存在** | 每个破坏性变更是否有回滚路径 | 阻塞 |
| 6 | **验收标准可量化** | 成功标准必须是数值化指标 | 标记模糊描述 |
| 7 | **资源评估合理** | 预估工时/成本是否在合理范围内 | 标记成本幻觉 |
| 8 | **依赖链完整** | 方案依赖的外部组件是否可用 | 阻塞，列出缺失依赖 |

**自动化检查脚本**：

```bash
#!/bin/bash
# scripts/solution-quality-gate.sh
# 运行在方案设计完成后，Spec 生成前

GATE_DIR=".gate"
SOLUTION_FILE="$1"  # solution-design.md

echo "=== Solution Quality Gate ==="

# 1. 技术方案可行性 — 检查方案中引用的 API/库是否真实存在
python scripts/verify-tech-claims.py "$SOLUTION_FILE" > "$GATE_DIR/tech-verification.json"

# 2. 架构一致性 — 对照 ADR 检查
python scripts/check-adr-compliance.py "$SOLUTION_FILE" "adr/" > "$GATE_DIR/adr-compliance.json"

# 3. 影响分析 — 对照实际依赖图
python scripts/verify-impact-analysis.py "$SOLUTION_FILE" > "$GATE_DIR/impact-analysis.json"

# 4. 风险清单完整性
python scripts/check-risk-assessment.py "$SOLUTION_FILE" > "$GATE_DIR/risk-check.json"

# 5. 汇总报告
jq -s '{
  gate: "solution_quality",
  timestamp: now,
  tech_feasible: .[0].all_valid,
  adr_compliant: .[1].compliant,
  impact_complete: .[2].complete,
  risks_identified: .[3].complete,
  overall: (.[0].all_valid and .[1].compliant and .[2].complete and .[3].complete)
}' "$GATE_DIR/tech-verification.json" \
   "$GATE_DIR/adr-compliance.json" \
   "$GATE_DIR/impact-analysis.json" \
   "$GATE_DIR/risk-check.json" \
   > "$GATE_DIR/solution-gate-result.json"
```

**Gate 输出**：

```json
{
  "gate": "solution_quality",
  "timestamp": "2026-04-17T12:00:00Z",
  "solution_file": "docs/solution-F001.md",
  "checks": {
    "tech_feasibility": { "passed": true, "issues": [] },
    "architecture_consistency": { "passed": true, "adr_conflicts": [] },
    "impact_analysis": { "passed": true, "orphan_claims": [] },
    "risk_assessment": { "passed": true, "missing_risks": [] },
    "rollback_plan": { "passed": true },
    "quantifiable_acceptance": { "passed": true, "vague_items": [] },
    "resource_estimate": { "passed": true, "anomalies": [] },
    "dependency_chain": { "passed": true, "missing_deps": [] }
  },
  "overall_passed": true,
  "reviewed_by": "@architect"
}
```

### 3.5 能力泛化机制（Skill Generalization）

**核心思路**：Feature 完成并合并后，系统自动分析该 Feature 的解决方案是否可泛化为通用 skill。

**触发时机**：Spec 状态变更为 `done` 且 PR 合并到 main 后。

**泛化流程**：

```
Spec done + PR merged
    │
    ▼
┌───────────────────────────────┐
│  Generalization Analyzer      │
│                               │
│  1. 分析已实现的代码模式       │
│  2. 识别可泛化的核心逻辑       │
│  3. 提取参数化变量             │
│  4. 生成 skill 草案            │
│  5. 人工审查 + 确认            │
│  6. skill 入库                 │
└───────────────────────────────┘
```

**泛化评估标准**：

| 标准 | 说明 | 判定方式 |
|------|------|---------|
| **复用潜力** | 该方案是否适用于 >1 个场景 | 人工评估 + AI 建议 |
| **参数化可行** | 是否可通过参数配置适配不同场景 | 变量提取检查 |
| **质量达标** | 已实现代码的测试覆盖率和 Gate 结果 | 读取 .gate/ 证据 |
| **无硬编码** | 无实例化值（地名、客户名、特定 ID） | 代码扫描 |

**Skill 生成模板**：

```markdown
---
name: {skill-name}
description: {泛化后的描述}
source_feature: F{NNN}
source_pr: #{NNN}
generalization_level: high|medium|low
parameters:
  - name: {param}
    type: string
    description: {用途}
    default: {默认值}
version: 1.0
created: {date}
verified: false  # 待人工确认
---

## 适用场景
- {场景 1}
- {场景 2}

## 核心逻辑
（从已验证代码中提取的通用模式）

## 参数说明
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|

## 使用示例
```yaml
# 使用此 skill 生成代码的配置
skill: {skill-name}
parameters:
  {param}: {value}
```

## 验证记录
| Feature | PR | 验证结果 |
|---------|----|---------|
```

**Skill 入库流程**：

```
skill 草案 → 人工审查（验证泛化正确性）
    │
    ├── 通过 → 存入 .claude/agents/ 或 skills/ 目录
    │         状态：verified
    │         可用于后续 Feature
    │
    └── 不通过 → 标记为 draft
                记录改进建议
                等待后续 Feature 验证
```

---

## 4. 规范集精简审查

对 7 份文档进行 MECE 分析，识别以下问题：

### 4.1 重复内容

| 重复项 | 出现位置 | 建议 |
|--------|---------|------|
| Prompt Chaining 描述 | 01-core 6.2 节 + 02-auto-coding 2.3 节 | 01-core 保留定义，02 改为引用 |
| Self-Correction Loop 流程 | 01-core 3.4 节 + 02-auto-coding 2.4 节 | 01-core 保留定义，02 改为引用 + 补充 Auto-Coding 特定场景 |
| Example-Driven Prompting | 01-core 4.5.1 节 + 01-core 6.3 节 | 合并为单一章节（6.3），4.5.1 改为引用 |
| Progressive Disclosure | 01-core 4.5.3 节 + 01-core 6.4 节 | 同上，合并为 6.4 |
| Sub-Agent 安全约束 | 03-multi-agent 1.5 节 + 04-security 7.4 节 | 04-security 保留安全视角，03 改为引用 |
| v4 合规注释（每文档第 8 章） | 02、03、04 均含 v4 合规注释 | 合并为独立文档 `09-v4-compliance-mapping.md`，各文档保留简要引用 |

### 4.2 矛盾点

| 矛盾 | 涉及文档 | 说明 | 建议修正 |
|------|---------|------|---------|
| 幻觉类型数量 | 01-core 列出 ~10 种，07-anti-hallucination 列出 40 种 | 01-core 数字过时 | 01-core 更新为 40 种 + 引用 07 |
| 原则数量表述 | 01-core 正文写"11 条核心原则"但实际有 P1-P11（11 条）+ P12-P22（11 条）| 核心 vs 工程实践应明确区分 | 已明确但表述需统一（核心 11 条 + 工程 11 条 = 22 条） |
| Agent Teams 状态 | 03-multi-agent 描述为实验性（需环境变量） | 02-auto-coding 6.4 节当作成熟功能使用 | 02 节标注实验性限制 |
| TDD 描述 | 01-core 写"AI 生成测试→人工审核断言"，02 写"AI 自主生成测试" | L2+ 下 AI 可自主生成但需 CI 抽检，两者不矛盾但表述易混淆 | 01-core 补充等级差异说明 |

### 4.3 冗余内容

| 冗余项 | 位置 | 建议 |
|--------|------|------|
| 各文档的术语表（附录 B） | 01、02、03 各有术语表 | 合并为独立文档 `10-glossary.md` |
| 快速参考卡片 | 01 附录 B + 02 附录 C | 合并为独立文档 `11-quick-reference.md` |
| CI Gate 配置模板 | 01 附录 F + 04 第 5 章 | 04 保留企业级模板，01 附录 F 精简为引用 |
| 升级/降级 Checklist | 01 附录 G + 04 第 8 章 | 04 保留，01 改为引用 |

### 4.4 精简建议

```
精简前：7 份文档，约 12 万字，多处重复
精简后：10 份文档（7 核心 + 3 支撑），消除重复约 15%

新增：
  08-capability-gap-analysis.md（本文档）
  09-v4-compliance-mapping.md（合并各文档第 8 章）
  10-glossary.md（合并术语表）

精简：
  01-core-specification.md：移除重复的 Prompt Chaining/Progressive Disclosure 正文，改为引用
  02-auto-coding-practices.md：移除 Self-Correction 正文重复，改为引用 + Auto-Coding 补充
  03/04：交叉引用替代重复的安全描述
```

---

## 5. 新版本变更摘要（v5.1 → v5.2）

### 5.1 新增内容

| 变更 | 类型 | 说明 |
|------|------|------|
| **P23 方案设计驱动** | 新原则 | 需求→Spec 的结构化 Prompt 链 |
| **DP0/DP0.5/DP0.7** | 新决策点 | 需求理解、架构方向、方案可行性 |
| **交付物模板** | 新资源 | 架构文档模板 + 技术方案模板 |
| **Context Loading Gate** | 新 Gate | 领域知识预加载机制 |
| **Solution Quality Gate** | 新 Gate | 方案质量评估（Spec 生成前） |
| **Skill Generalization** | 新机制 | 从已验证方案泛化为通用 skill |
| **design-output.json** | 新证据格式 | 设计产物 Gate 输出格式 |
| **domain-knowledge/** | 新目录 | 领域知识库标准结构 |

### 5.2 变更内容

| 变更 | 位置 | 说明 |
|------|------|------|
| IPD 映射更新 | 01-core 1.4 | Phase 0-2 从"无影响"改为"AI 参与方案设计" |
| Prompt Chaining 扩展 | 01-core 6.2 | 链起点从"已有 Spec"扩展到"原始需求" |
| 决策点扩展 | 01-core 7.3 | 从 4 个扩展到 7 个（DP0-DP4） |
| Spec 扩展字段 | 01-core 5.2 | 新增 `required_domain_knowledge` 字段 |
| .gate/ 扩展 | 01-core 附录 F | 新增 design-output.json、solution-gate-result.json |

### 5.3 清理内容

| 变更 | 说明 |
|------|------|
| 重复章节合并 | Prompt Chaining、Self-Correction、Progressive Disclosure、Example-Driven 去除重复 |
| 术语表独立 | 从各文档附录合并为 10-glossary.md |
| v4 合规注释独立 | 从各文档第 8 章合并为 09-v4-compliance-mapping.md |
| 幻觉类型统一 | 01-core 更新为 40 种（引用 07-anti-hallucination） |

### 5.4 版本影响矩阵

| 文档 | 变更量 | 主要变更 |
|------|--------|---------|
| 01-core-specification.md | 中 | P23、DP0-0.7、IPD 映射更新、Spec 字段扩展 |
| 02-auto-coding-practices.md | 小 | 引用新的 Requirement→Spec 链入口 |
| 03-multi-agent-multi-surface.md | 小 | 新增 Generalization Agent 模式 |
| 04-security-governance.md | 小 | Context Loading Gate 安全检查项 |
| 05-tool-reference.md | 中 | 新模板、新 Gate 脚本、新目录结构 |
| 06-automation-replacements-analysis.md | 无 | 不受影响 |
| 07-anti-hallucination.md | 小 | 方案设计中新增幻觉类型检查（技术幻觉、成本幻觉） |

---

*本文档是 AI Coding 规范 v5.2 的差距分析与补齐方案。后续需将 3.1-3.5 的补齐方案落实到具体文档中，形成 v5.2 正式版。*
