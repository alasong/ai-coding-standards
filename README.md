# AI Coding Standards v5.4

> 大规模高复杂度 Auto-Coding 规范集 — IPD 方法引擎 + 全链路交付治理

## Quick Start

1. 阅读 [INDEX](ai-coding-v5.4/INDEX.md) 了解完整文档结构
2. 阅读 [核心规范](ai-coding-v5.4/01-core-specification.md) 理解 23 条原则和 IPD 方法引擎
3. 按需查阅配套文档

## Document Structure

| 类别 | 文档 | 说明 |
|------|------|------|
| **核心** | [01 核心规范](ai-coding-v5.4/01-core-specification.md) | P1-P23、IPD 六阶段、L1-L4、TDD |
| | [02 Auto-Coding 实践](ai-coding-v5.4/02-auto-coding-practices.md) | 自主编码、定时任务、夜间开发 |
| | [03 多 Agent 与多平台](ai-coding-v5.4/03-multi-agent-multi-surface.md) | Sub-Agents、冲突解决、并行度 |
| | [04 安全与治理](ai-coding-v5.4/04-security-governance.md) | 权限、MCP、合规、审计 |
| | [05 工具参考](ai-coding-v5.4/05-tool-reference.md) | CLI、Hooks、Skills、审查清单 |
| **交付** | [06 CI/CD Pipeline](ai-coding-v5.4/06-cicd-pipeline.md) | L0-L5 分层、质量门禁、环境晋升 |
| | [07 可观测性](ai-coding-v5.4/07-observability.md) | 日志、指标、追踪、SLO、告警 |
| | [07 反幻觉方案](ai-coding-v5.4/07-anti-hallucination.md) | 45 种类型、证据链 |
| | [08 数据库迁移](ai-coding-v5.4/08-database-migration.md) | TDD 迁移、蓝绿、Expand-Contract |
| | [09 API 契约](ai-coding-v5.4/09-api-contracts.md) | OpenAPI、契约测试、版本策略 |
| | [10 依赖与供应链](ai-coding-v5.4/10-dependency-management.md) | 依赖审批、SBOM、供应链安全 |
| | [11 性能基线](ai-coding-v5.4/11-performance-baseline.md) | 性能预算、CI 门禁、压力测试 |
| | [12 AI 成本管理](ai-coding-v5.4/12-ai-cost-management.md) | Token 预算、模型路由、ROI |
| | [13 部署与回滚](ai-coding-v5.4/13-deploy-rollback.md) | 蓝绿/金丝雀、回滚、Feature Flag |
| | [14 发布管理](ai-coding-v5.4/14-release-management.md) | 版本编号、Release Notes、Hotfix |
| **运营** | [15 环境/缓存/SLA](ai-coding-v5.4/15-environment-cache-sla.md) | 环境分层、缓存、Review SLA |
| | [16 安全测试与混沌](ai-coding-v5.4/16-security-chaos.md) | DAST、渗透、混沌工程 |
| | [17 数据治理与国际化](ai-coding-v5.4/17-data-governance-i18n.md) | 数据血缘、GDPR、i18n/A11y |
| **配套** | [模板](ai-coding-v5.4/templates/) | 方案设计、架构文档 |
| | [脚本](ai-coding-v5.4/scripts/) | Quality Gate、Spec 验证 |

## Core Principles (摘要)

| # | 原则 | # | 原则 |
|---|------|---|------|
| P1 | 商业驱动 | P12-P22 | 工程实践（环境、错误、租户、并发等） |
| P2 | DCP 门禁 | P23 | 需求→Spec 链 |
| P3 | TDD 先行 | | |
| P4 | 人工审查 | | |
| P5 | 密钥不入代码 | | |
| P6 | 单一信息源 | | |
| P7 | Spec 驱动 | | |
| P8 | 最小批量 | | |
| P9 | Prompt 版本化 | | |
| P10 | 数据分级 | | |
| P11 | 证据链 | | |

## License

MIT
