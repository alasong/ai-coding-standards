# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains **AI Coding Standards v6.0** — a comprehensive specification for large-scale, high-complexity auto-coding using IPD (Integrated Product Development) methodology. It is a documentation/specification repository, not an application codebase.

All specifications live under `ai-coding-v6.0/`.

## Document Loading Order

Load documents in this priority order:

| Priority | Document | Purpose |
|----------|----------|---------|
| **P0** | `ai-coding-v6.0/01-core.md` | P1-P24, L1-L4, IPD 六阶段, TDD, Spec 驱动, 幻觉防护 |
| **P0** | `ai-coding-v6.0/02-state-machine.md` | IPD 宏状态 + SCFS 微状态, YAML 配置, CLI |
| **P1** | `ai-coding-v6.0/03-structured-constraints.md` | 6 种约束文件, Agent 生命周期 |
| **P1** | `ai-coding-v6.0/04-multi-agent.md` | Agent 角色, 会诊模式, 团队矩阵 |
| **P2** | `ai-coding-v6.0/05-cicd-pipeline.md` | L0-L5 分层门禁, Kill Switch, 自修复 CI |
| **P2** | `ai-coding-v6.0/06-security-governance.md` | 安全基线, 依赖治理, 混沌工程 |
| **P2** | `ai-coding-v6.0/07-specialized.md` | DB 迁移, API 契约, 性能, 部署, 发布 |
| **P3** | `ai-coding-v6.0/08-operations.md` | 可观测性, 环境, 缓存, 数据治理, i18n |
| **P3** | `ai-coding-v6.0/09-cost-management.md` | Token 预算, 模型路由 |
| **P3** | `ai-coding-v6.0/10-spec-evolution.md` | Spec 生命周期, 版本管理 |

Full index: `ai-coding-v6.0/INDEX.md`

## Core Principles Summary

- **P1-P11** (non-negotiable): Business-driven, DCP gates, TDD first, human review, no secrets, single source of truth, spec-driven, small batch, prompt versioning, data classification, evidence chain
- **P12-P22** (engineering): Environment consistency, error handling, tenant isolation, concurrency safety, resource cleanup, input validation, JSON safety, auth on writes, rate limiting, data consistency, no IP exposure
- **P23**: Requirement → Solution → Spec chain
- **P24**: Standard library first

## Autonomy Levels

| Level | Name | Human Intervention |
|-------|------|-------------------|
| L1 | Assisted | Every step |
| **L2** | **Semi-autonomous (default)** | Before each PR merge |
| L3 | Restricted autonomous | PR merge + DCP gates |
| L4 | Full autonomous | DCP gates + periodic audit |

## Autonomy Levels vs Process Profiles

Two orthogonal dimensions control execution:

| Dimension | Controls | Values |
|-----------|----------|--------|
| **Autonomy Level (L1-L4)** | Who does the work | L1 assisted → L4 fully autonomous |
| **Process Profile (S-XL)** | How heavy the process is | S (trivial) → XL (platform-level) |

### Process Profiles

| Profile | Phases | DCPs | Use Case |
|---------|--------|------|---------|
| **S** | Phase 3 only | 0 | Single file ≤50 lines, no API/arch changes |
| **M** | Phase 1→3 | 1 | 1-3 Specs |
| **L** | Phase 0→3 | 2 | 3-10 Specs / architecture changes |
| **XL** | Phase 0→4 + Phase 5 | 3+ | 10+ Specs / platform-level / production release |

**Non-negotiable at any profile**: P1-P11, P12-P22, TDD (P3), security baseline (P5/P17/P19).

## TDD Protocol

Red → Green → Refactor. Tests must be written first and must fail before implementation. Test and implementation must be in separate commits.

## Multi-Agent Patterns

- **Consultation mode**: Multiple independent agents review the same deliverable from different perspectives (quality-focused)
- **Pipeline mode**: Relay-style sequential handoff between agents (efficiency-focused)
- Use `.normalized/{role}-rules.md` for agent-specific distilled rules
- Agent registry mapping in `.normalized/agent-registry.yaml`

## State Machine

IPD macro states + SCFS micro states control all agent permissions via `ai-coding-v6.0/scripts/ipd-sm.py`:
- 18 states total: IDLE → PHASE_0 → PHASE_1 → PHASE_2 → PHASE_2.5 → PHASE_3_DISPATCH → SCFS_BOOT → [TDD loop] → TASK_GATE → PR_CREATE → IDLE
- Each state has explicit permissions (allow/deny/scope) and exit conditions

## Key Directories

| Path | Purpose |
|------|---------|
| `ai-coding-v6.0/.normalized/` | Distilled agent rules per role (16 roles) |
| `ai-coding-v6.0/scripts/` | Quality gate scripts and state machine CLI |
| `ai-coding-v6.0/templates/` | Solution design and architecture document templates |
| `ai-coding-v6.0/lessons/` | Lessons learned registry |

## Quality Gates

- Self-correction loop: max 3 rounds, then escalate to human
- Gate Checker: independent read-only validation agent
- Multi-pass review: 6 Pass × 7 Gate × 3 rounds = 630 review checks
- Evidence chain: every claim requires ≥2 machine-verifiable evidence items from different sources

## Spec-Driven Development

Every feature requires a Spec file (`specs/F{NNN}-{name}.md`) with YAML frontmatter and Gherkin acceptance criteria. Coding must not begin without a Spec in `ready` or `in-progress` state.
