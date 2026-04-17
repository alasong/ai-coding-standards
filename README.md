# AI Coding Standards v5.3

> 方案设计驱动的 Auto-Coding 规范 — 消除文档间冗余、统一术语、规范化结构

## Quick Start

1. 阅读 [INDEX](ai-coding-v5.3/INDEX.md) 了解文档结构和自治等级
2. 阅读 [核心规范](ai-coding-v5.3/01-core-specification.md) 理解 23 条原则和 P23 需求→Spec 链
3. 按需查阅配套文档

## Document Structure

| # | 文档 | 说明 |
|---|------|------|
| 01 | [核心规范](ai-coding-v5.3/01-core-specification.md) | P1-P23 原则、L1-L4 自治等级、TDD、Spec 驱动、幻觉检测 |
| 02 | [Auto-Coding 实践](ai-coding-v5.3/02-auto-coding-practices.md) | 自主编码模式、定时任务、夜间开发、自修复 CI |
| 03 | [多 Agent 与多平台](ai-coding-v5.3/03-multi-agent-multi-surface.md) | Sub-Agents、Agent SDK、多平台协同 |
| 04 | [安全与治理](ai-coding-v5.3/04-security-governance.md) | 企业部署、权限管理、MCP 安全、合规审计 |
| 05 | [工具参考](ai-coding-v5.3/05-tool-reference.md) | CLI、配置模板、Hooks、P23 模板、Quality Gate 脚本 |
| 07 | [反幻觉方案](ai-coding-v5.3/07-anti-hallucination.md) | 45 种幻觉类型、证据链方法论、检测与防护 |
| - | [模板](ai-coding-v5.3/templates/) | 方案设计模板、架构文档模板 |
| - | [脚本](ai-coding-v5.3/scripts/) | Quality Gate 脚本、Spec 验证工具 |

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
