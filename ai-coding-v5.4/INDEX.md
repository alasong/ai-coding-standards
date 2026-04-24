# AI Coding 规范 v5.5：索引

> 版本：v5.5 | 2026-04-24
> 定位：大规模高复杂度 Auto-Coding 规范集 — IPD 方法引擎 + 全链路交付治理

---

## 自治等级模型

| 等级 | 名称 | 人类干预点 | 适用场景 |
|------|------|-----------|---------|
| **L1** | 辅助编码 | 每一步 | 新手团队、安全敏感项目 |
| **L2** | 半自主编码 | 每个 PR 合并前 | **日常开发（推荐默认）** |
| **L3** | 受限自主编码 | PR 合并前 + DCP 门禁 | 夜间/周末开发、成熟团队 |
| **L4** | 完全自主编码 | DCP 门禁 + 定期审计 | 高成熟度团队、低风险变更 |

### 约束矩阵

| 约束 | L1 | L2 | L3 | L4 |
|------|----|----|----|----|
| **P1 商业驱动** | 人工定义目标 | 人工定义，AI 拆解 | AI 按队列执行 | AI 自主按优先级 |
| **P2 DCP 门禁** | 人工同步确认 | 人工同步确认 | 可异步确认 | 自动化+定期审计 |
| **P3 TDD 先行** | 人工确认 Red→Green | AI 执行，人工确认断言 | AI 自动执行，CI 记录 | AI 自动执行，CI 强制验证 |
| **P4 人工审查** | 每次提交前 | 每个 PR 合并前 | 每个 PR 合并前（可批量） | 每周随机抽样 ≥10% |
| **P5 密钥不入代码** | pre-commit 拦截 | pre-commit + SAST | pre-commit + SAST + CI | 同 L3 + 专项密钥检测 |
| **P6 单一信息源** | 人工维护 | 人工维护，AI 辅助检测 | AI 检测漂移，人工确认 | 同 L3 + >20% 触发回归 |
| **P7 Spec 驱动** | 人工编写 | 人工审核 AI 生成 | AI 读取 specs/，Spec 人工验证 | AI 读取 specs/，定期抽检 |
| **P8 最小批量** | 人工控制 | AI 控制，人工审查 | AI 控制，CI 验证 | AI 控制，CI 强制验证 |
| **P9 Prompt 版本化** | 人工记录 | AI 记录到 PR 描述 | AI 持久化到 prompts/ | 同 L3 + 自动回归测试 |
| **P10 数据分级** | 人工判断 | pre-send 自动扫描 | pre-send 扫描 + 审计日志 | 同 L3 + 定期数据安全审计 |
| **P11 证据链** | 人工逐项核对 | AI 收集到 .gate/ | AI 自动收集 + AC 映射验证 | AI 自动收集 + 定期审计 |
| **幻觉检测** | 人工审查 | AI Reviewer + 人工 | AI Reviewer 自动 + 人工 | AI Reviewer 自动 + 抽检 |
| **自修复限制** | 最多 3 轮，人工确认 | 最多 3 轮，自动执行 | 最多 3 轮，超 3 轮转人工 | 最多 3 轮，超 3 轮暂停告警 |
| **MCP 访问** | 只读 | 读写（过滤） | 读写（过滤+脱敏） | 读写（过滤+脱敏+审计） |
| **自动合并** | 禁止 | 禁止 | 禁止 | 仅限 trivial fix |
| **Decision Point** | 全部人工同步 | 人工同步确认 | DP1/DP2 异步，DP3/DP4 同步 | 自动化检查 + 定期抽检 |
| **P23 需求→Spec 链** | **强制** | **强制** | **强制** | **强制** |
| **设计启发式** | **强制** | **强制** | **强制** | **强制** |
| **构造检查清单** | **强制** | **强制** | **强制** | **强制** |

### 原则违反后果矩阵

| 原则 | L1 违规 | L2 违规 | L3 违规 | L4 违规 |
|------|--------|--------|--------|--------|
| P1 商业驱动 | PR 被拒绝 | PR 被拒绝 | PR 被拒绝 + 告警 | PR 被拒绝 + 审计 |
| P2 DCP 门禁 | 阻塞下一阶段 | 阻塞下一阶段 | 阻塞 + 暂停自主开发 | 阻塞 + 降级 L2 |
| P3 TDD 先行 | 阻塞合并 | 阻塞合并 | 阻塞合并 | 阻塞合并 + 审计抽检 |
| P4 人工审查 | 阻塞合并 | 阻塞合并 | 阻塞合并 | 自动回滚 + 降级 L2 |
| P5 密钥不入 | 阻断 + pre-commit | 阻断 + SAST | 阻断 + 安全事件 | 阻断 + 降级 L1 |
| P6 单一信息源 | 人工修正 | 人工修正 | AI 检测漂移 | 漂移检测 + 审计 |
| P7 Spec 驱动 | 不得开始开发 | 不得开始开发 | 不得开始开发 | 不得开始开发 |
| P8 最小批量 | 人工拆分 | CI 阻塞合并 | CI 阻塞合并 | CI 阻塞合并 |
| P9 Prompt 版本化 | 人工记录 | 自动记录到 PR | 持久化到 prompts/ | 同 L3 + 回归测试 |
| P10 数据分级 | 人工判断 | pre-send 扫描 | 扫描 + 审计日志 | 同 L3 + 定期审计 |
| P11 证据链 | 人工逐项核对 | AI 收集到 .gate/ | 自动收集 + AC 映射 | 自动收集 + 审计 |

---

## 文档结构

### 核心规范

| # | 文档 | 说明 |
|---|------|------|
| 00 | [规范哲学](00-philosophy.md) | 元规则：规范解决什么、准入标准、冲突裁决、写作规范、演进原则 |
| 01 | [核心规范](01-core-specification.md) | 核心原则（P1-P23）、IPD 六阶段方法引擎、自治等级、TDD、Spec 驱动 |
| 02 | [Auto-Coding 实践](02-auto-coding-practices.md) | 自主编码模式、定时任务、夜间开发、自修复 CI、Supervisor-Worker |
| 03 | [多 Agent 与多平台](03-multi-agent-multi-surface.md) | Sub-Agents、Agent SDK、多平台协同、冲突解决、并行度控制 |
| 04 | [安全与治理](04-security-governance.md) | 企业部署、权限管理、MCP 安全、合规、审计 |
| 05 | [工具参考](05-tool-reference.md) | CLI 参考、Settings、Hooks、Skills、配置模板、审查清单 |
| 06 | [CI/CD Pipeline](06-cicd-pipeline.md) | L0-L5 分层结构、质量门禁、Self-Correction、环境晋升、Artifact 管理 |
| 07 | [反幻觉方案](07-anti-hallucination.md) | 45 种幻觉类型、证据链方法论、检测与防护 |

### 交付基础设施

| # | 文档 | 说明 |
|---|------|------|
| 07B | [可观测性](07-observability.md) | 结构化日志、RED 指标、分布式追踪、SLO/SLA、告警、Dashboard |
| 08 | [数据库迁移](08-database-migration.md) | TDD 迁移、destructive change 检测、蓝绿迁移、Expand-Contract |
| 09 | [API 契约与版本](09-api-contracts.md) | OpenAPI 管理、契约测试、向后兼容、破坏性变更通知、版本策略 |
| 10 | [依赖与供应链](10-dependency-management.md) | 依赖审批、漏洞 SLA、Typosquatting 检测、SBOM、供应链安全 |
| 11 | [性能基线](11-performance-baseline.md) | 性能预算、自动基准测试、CI 门禁、性能剖析、压力测试 |
| 12 | [AI 成本管理](12-ai-cost-management.md) | Token 预算、模型路由、Prompt 优化、上下文复用、ROI 度量 |
| 13 | [部署与回滚](13-deploy-rollback.md) | 蓝绿/金丝雀/滚动、回滚机制、多服务编排、Feature Flag |
| 14 | [发布管理](14-release-management.md) | 版本编号、Release Notes、CHANGELOG、发布节奏、Hotfix |

### 运营与治理

| # | 文档 | 说明 |
|---|------|------|
| 15 | [环境、缓存与 Review SLA](15-environment-cache-sla.md) | 环境分层、测试数据脱敏、缓存架构、Code Review SLA |
| 16 | [安全测试与混沌工程](16-security-chaos.md) | DAST、渗透测试、混沌工程、AI 安全测试、合规验证 |
| 17 | [数据治理与国际化](17-data-governance-i18n.md) | 数据血缘、PII、GDPR、备份恢复、i18n/A11y、数据生命周期 |
| 18 | [规范演进治理](18-spec-evolution-governance.md) | 规范生命周期、变更请求、审批矩阵、过渡期、版本管理 |
| 19 | [Multi-Pass Review Protocol](19-multi-pass-review.md) | 每阶段 7 Gate × 5 检查项 × 3 轮验证 × 6 Pass = 630 次验证 |
| 20 | [Lessons Learned Protocol](20-lessons-learned.md) | 教训链：L1-L4 分级、结构化沉淀、48h 注入、深度评分联动 |
| - | [教训库](lessons/) | 已沉淀的教训索引与详情（lessons-registry.yaml + LL-NNN.md） |
| - | [脚本](scripts/) | Quality Gate 脚本、Spec 验证工具 |

---

## AI 阅读顺序指南

> **重要**：本文档是导航索引，不是规范本体。AI 应按以下顺序加载规范文档，确保上游依赖先于下游加载。

| 优先级 | 加载顺序 | 文档 | 说明 |
|--------|---------|------|------|
| **P0** | 首先加载 | 01-core-specification.md | 核心原则（P1-P24）、自治等级、TDD、Spec 驱动、IPD 六阶段、全机制目录（附录 D）。所有其他文档依赖本文档的定义 |
| **P1** | 其次加载 | 07-anti-hallucination.md | 证据链定义（P11 执行细则）、45 种幻觉类型。L2+ 审查和 Gate 依赖此文档 |
| **P1** | 其次加载 | 06-cicd-pipeline.md | Pipeline 层级、各层 Gate 定义。L2+ 自动化执行依赖此文档 |
| **P2** | 按需加载 | 02-auto-coding-practices.md | 自主编码模式、Prompt Chaining 等。执行阶段需要时加载 |
| **P2** | 按需加载 | 05-tool-reference.md | 工具参考、AI 审查清单（A01-A09）。审查阶段需要时加载 |
| **P2** | 按需加载 | 03-multi-agent-multi-surface.md | 多 Agent 协调。团队协作场景需要时加载 |
| **P3** | 专项加载 | 08-18 专项文档 | 按任务类型加载：部署→13/14、数据库→08、API→09、安全→04/16 等 |

**跨文档引用约定**：所有文档间引用使用 `[文件名](文件名.md)` 格式，不得使用"见XX规范"等模糊引用。

---

## 原则速查

```
P1 商业驱动 ── P2 DCP 门禁 ── P3 TDD 先行 ── P4 人工审查 ── P5 密钥不入
P6 单一信息 ── P7 Spec 驱动 ── P8 最小批量 ── P9 Prompt 版 ── P10 数据分级
P11 证据链
P12-P22 工程实践（环境、错误、租户、并发、资源、输入、JSON、认证、速率、数据、IP）
P23 需求→Spec 链（需求分析→架构适配→方案设计→Spec 生成）
```
