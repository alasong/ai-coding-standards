# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains **AI Coding Standards v5.4/v5.5** — a comprehensive specification for large-scale, high-complexity auto-coding using IPD (Integrated Product Development) methodology. It is a documentation/specification repository, not an application codebase.

All specifications live under `ai-coding-v5.4/`.

## Document Loading Order

When working with this spec, load documents in this priority order:

| Priority | Document | Purpose |
|----------|----------|---------|
| **P0** | `ai-coding-v5.4/01-core-specification.md` | 23 core principles (P1-P23), autonomy levels (L1-L4), IPD six-phase engine, TDD, Spec-driven dev |
| **P1** | `ai-coding-v5.4/07-anti-hallucination.md` | 45 hallucination types, evidence chain methodology |
| **P1** | `ai-coding-v5.4/06-cicd-pipeline.md` | Layered pipeline (L0-L5), quality gates, environment promotion |
| **P2** | `ai-coding-v5.4/03-multi-agent-multi-surface.md` | Sub-agents, consultation mode, multi-agent coordination |
| **P2** | `ai-coding-v5.4/02-auto-coding-practices.md` | Auto-coding patterns, night development, self-healing CI |
| **P2** | `ai-coding-v5.4/05-tool-reference.md` | CLI reference, settings, hooks, skills, review checklists (A01-A09) |
| **P3** | `ai-coding-v5.4/08-18` specialty docs | Load by task type: deploy→13/14, DB→08, API→09, security→04/16 |

Full index: `ai-coding-v5.4/INDEX.md`

## Core Principles Summary

- **P1-P11** (non-negotiable): Business-driven, DCP gates, TDD first, human review, no secrets, single source of truth, spec-driven, small batch, prompt versioning, data classification, evidence chain
- **P12-P22** (engineering): Environment consistency, error handling, tenant isolation, concurrency safety, resource cleanup, input validation, JSON safety, auth on writes, rate limiting, data consistency, no IP exposure
- **P23**: Requirement → Solution → Spec chain (mandatory before any coding)

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

**Non-negotiable at any profile**: P1-P11 core principles, P12-P22 engineering practices, TDD (P3), security baseline (P5/P17/P19).

**Example**: L4 autonomy + S profile = fully automated tiny fix. L4 + XL = fully automated platform refactor.

## TDD Protocol

Red → Green → Refactor. Tests must be written first and must fail before implementation. Test and implementation must be in separate commits.

## Multi-Agent Patterns

- **Consultation mode**: Multiple independent agents review the same deliverable from different perspectives (quality-focused)
- **Pipeline mode**: Relay-style sequential handoff between agents (efficiency-focused)
- Use `.normalized/{role}-rules.md` for agent-specific distilled rules
- Agent registry mapping in `.normalized/agent-registry.yaml`

## Key Directories

| Path | Purpose |
|------|---------|
| `ai-coding-v5.4/.normalized/` | Distilled agent rules per role (tool-agnostic instruction sets) |
| `ai-coding-v5.4/scripts/` | Quality gate scripts and spec validation tools |
| `ai-coding-v5.4/templates/` | Solution design and architecture document templates |

## Quality Gates

- Self-correction loop: max 3 rounds, then escalate to human
- Gate Checker: independent read-only validation agent
- Multi-pass review: 5 passes × 7 gates × 25 checks × 3 rounds = 630 review checks
- Evidence chain: every claim requires ≥2 machine-verifiable evidence items from different sources

## Spec-Driven Development

Every feature requires a Spec file (`specs/F{NNN}-{name}.md`) with YAML frontmatter and Gherkin acceptance criteria. Coding must not begin without a Spec in `ready` or `in-progress` state.
