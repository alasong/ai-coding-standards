# AI Coding Standards v6.0

> IPD 方法引擎 + 全链路交付治理 — 从 25 份文档压缩为 12 份核心文档

## Quick Start

1. 阅读 [INDEX](ai-coding-v6.0/INDEX.md) 了解文档结构
2. 阅读 [00-philosophy](ai-coding-v6.0/00-philosophy.md) 了解元规则
3. 阅读 [01-core](ai-coding-v6.0/01-core.md) 理解 24 条原则和 IPD 方法引擎
4. 按需查阅配套文档

## 使用方法

### 场景 1：新项目从零开始（完整 IPD 流程）

```bash
# 第一步：初始化 .ipd/ 状态机目录
python3 ai-coding-v6.0/scripts/ipd-sm.py init

# 第二步：进入 Phase 0 市场洞察
# 填写 ipd/phase-0/01-market-insight.md（五看三定）
# 运行 Phase 0 会诊模式（需要 SILICONFLOW_API_KEY）
export SILICONFLOW_API_KEY="your-key"
python3 ai-coding-v6.0/scripts/phase0-consultation.py

# 第三步：状态机推进
python3 ai-coding-v6.0/scripts/ipd-sm.py next

# 第四步：Phase 1 概念定义
python3 ai-coding-v6.0/scripts/phase1-consultation.py

# 第五步：继续推进到 Phase 3 开发
# 创建 Spec 文件 → TDD 开发 → Gate 检查 → PR
```

### 场景 2：现有项目中的功能开发（跳过 Phase 0/1）

```bash
# 直接初始化状态机并跳转到 Phase 3
python3 ai-coding-v6.0/scripts/ipd-sm.py init
python3 ai-coding-v6.0/scripts/ipd-sm.py reset PHASE_3_DEVELOP

# 创建 Feature Spec
# specs/F001-feature-name.md
# 包含：YAML frontmatter + 用户故事 + Gherkin 验收标准

# 开发前做 Gate 检查
python3 ai-coding-v6.0/scripts/gate-check.py

# 完成开发后创建 PR
python3 ai-coding-v6.0/scripts/ipd-sm.py next  # → PR_CREATE
```

### 状态机命令（ipd-sm.py）

| 命令 | 作用 |
|------|------|
| `python3 ai-coding-v6.0/scripts/ipd-sm.py init` | 初始化 .ipd/ 目录和初始文件 |
| `python3 ai-coding-v6.0/scripts/ipd-sm.py status` | 查看当前状态 |
| `python3 ai-coding-v6.0/scripts/ipd-sm.py verify` | 验证 exit conditions |
| `python3 ai-coding-v6.0/scripts/ipd-sm.py next` | 转换到下一个状态 |
| `python3 ai-coding-v6.0/scripts/ipd-sm.py reset STATE` | 重置到指定状态 |
| `python3 ai-coding-v6.0/scripts/ipd-sm.py history` | 查看状态历史 |

### 会诊脚本

| 脚本 | 场景 | 依赖 |
|------|------|------|
| `phase0-consultation.py` | Phase 0 三角色并行 + Gate Checker | `SILICONFLOW_API_KEY` |
| `phase1-consultation.py` | Phase 1 三角色并行 + Gate Checker | `SILICONFLOW_API_KEY` |
| `gate-check.py` | Gate 门禁检查 | 无 |

### 在 Claude Code 中使用

1. 将此仓库 clone 到你的项目同级目录
2. 复制 `ai-coding-v6.0/.normalized/{role}-rules.md` 到你的项目的 `.claude/agents/` 目录
3. 按照场景 1 或场景 2 的流程开始开发
4. 所有原则（P1-P24）在编码时自动生效，通过 CLAUDE.md 加载

## Document Structure

| 优先级 | 文档 | 说明 |
|--------|------|------|
| **P0** | [00-philosophy](ai-coding-v6.0/00-philosophy.md) | 元规则：为什么存在、追求什么 |
| **P0** | [01-core](ai-coding-v6.0/01-core.md) | P1-P24、IPD 六阶段、L1-L4、TDD、Spec 驱动 |
| **P0** | [02-state-machine](ai-coding-v6.0/02-state-machine.md) | IPD 宏状态 + SCFS 微状态、YAML 配置、CLI |
| **P1** | [03-structured-constraints](ai-coding-v6.0/03-structured-constraints.md) | 6 种约束文件、Agent 生命周期 |
| **P1** | [04-multi-agent](ai-coding-v6.0/04-multi-agent.md) | Agent 角色、会诊模式、团队矩阵 |
| **P2** | [05-cicd-pipeline](ai-coding-v6.0/05-cicd-pipeline.md) | L0-L5 分层门禁、Kill Switch |
| **P2** | [06-security-governance](ai-coding-v6.0/06-security-governance.md) | 安全基线、依赖治理、混沌工程 |
| **P2** | [07-specialized](ai-coding-v6.0/07-specialized.md) | DB 迁移、API 契约、性能、部署、发布 |
| **P3** | [08-operations](ai-coding-v6.0/08-operations.md) | 可观测性、环境、缓存、数据治理、i18n |
| **P3** | [09-cost-management](ai-coding-v6.0/09-cost-management.md) | Token 预算、模型路由 |
| **P3** | [10-spec-evolution](ai-coding-v6.0/10-spec-evolution.md) | Spec 生命周期、版本管理 |

## Core Principles (摘要)

| # | 原则 | # | 原则 |
|---|------|---|------|
| P1 | 商业驱动 | P12-P22 | 工程实践 |
| P2 | DCP 门禁 | P23 | 需求→Spec 链 |
| P3 | TDD 先行 | P24 | 标准库优先 |
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
