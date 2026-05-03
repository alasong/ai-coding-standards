# AI Coding 规范 v6.0：索引

> 版本：v6.0 | 2026-05-02
> 变更：从 v5.4 的 25 份文档压缩为 10 份核心文档 + `.normalized/` + `scripts/` + `templates/`

---

## 加载顺序

按优先级从高到低加载：

| 优先级 | 文档 | 内容 |
|--------|------|------|
| **P0** | [00-philosophy.md](00-philosophy.md) | 元规则：为什么存在、追求什么 |
| **P0** | [01-core.md](01-core.md) | P1-P24 原则、L1-L4 自治等级、流程裁剪、Scale 适配、TDD、Spec 驱动、幻觉防护 |
| **P0** | [02-state-machine.md](02-state-machine.md) | IPD 宏状态 + SCFS 微状态、YAML 配置、CLI |
| **P1** | [03-structured-constraints.md](03-structured-constraints.md) | 6 种约束文件、Agent 生命周期、升级协议 |
| **P1** | [04-multi-agent.md](04-multi-agent.md) | Agent 角色、会诊模式、团队矩阵、冲突解决 |
| **P2** | [05-cicd-pipeline.md](05-cicd-pipeline.md) | L0-L5 分层门禁、Self-Correction、Kill Switch |
| **P2** | [06-security-governance.md](06-security-governance.md) | 安全底线、权限、依赖治理、混沌测试 |
| **P2** | [07-specialized.md](07-specialized.md) | 数据库迁移、API 契约、性能、部署、发布 |
| **P3** | [08-operations.md](08-operations.md) | 可观测性、环境、缓存、数据治理、i18n |
| **P3** | [09-cost-management.md](09-cost-management.md) | Token 预算、模型路由、成本优化 |
| **P3** | [10-spec-evolution.md](10-spec-evolution.md) | Spec 生命周期、版本管理、变更传播 |

## 配套目录

| 目录 | 内容 |
|------|------|
| `.normalized/` | Agent 角色规则（工具无关指令集） |
| `scripts/` | 质量门禁脚本（ipd-sm.py、spec-validate.py 等） |
| `templates/` | 方案设计模板 |
| `lessons/` | 教训注册表 |

## v6.0 变更摘要

| 变更 | 说明 |
|------|------|
| **文档压缩** | 25 份 → 10 份（68% 行减少） |
| **状态机核心** | 独立文档，宏状态 + 微状态统一定义 |
| **SCFS 整合** | 结构化约束文件体系提升为 P1 优先级 |
| **去冗余** | 每条原则只在一处定义，其他处通过引用 |
| **可执行化** | 每条规则必须可被脚本、状态条件或门禁检查 |

## 快速参考

```
原则：P1 商业驱动 → P2 DCP → P3 TDD → P4 人工审查 → P5 密钥不入
     P6 单一信息 → P7 Spec 驱动 → P8 最小批量 → P9 Prompt 版
     P10 数据分级 → P11 证据链 → P12-P22 工程实践 → P23 需求链 → P24 标准库优先

自治等级：L1 辅助 → L2 半自主（默认）→ L3 受限自主 → L4 完全自主
流程裁剪：S（单文件）→ M（1-3 Spec）→ L（3-10 Spec）→ XL（10+ Spec）
状态机：IDLE → PHASE_0 → PHASE_1 → PHASE_2 → PHASE_2.5 → PHASE_3_DISPATCH → [SCFS 循环] → PHASE_3_COMPLETE → PR_CREATE → IDLE
SCFS：BOOT → CONTRACT → UPSTREAM → [TDD_RED → TDD_GREEN → TDD_REFACTOR → SPEC_ALIGN_CHECK] → GATE_REQUEST → WAITING → TASK_GATE
TDD：Red → Green → Refactor
多 Agent：会诊模式（质量）+ 流水线模式（效率）
CI/CD：L0 预提交 → L1 编译 → L2 测试 → L3 质量 → L4 集成 → L5 晋升
安全：P5 密钥 → P10 分级 → P17 输入 → P19 认证
幻觉：Example-Driven + Prompt Chaining + Progressive Disclosure + 两层审查
```
