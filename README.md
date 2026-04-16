# AI Coding Standards v5.1

> Evidence-driven, safety-first AI-assisted coding standards for 1-3 person teams.

## What This Is

A comprehensive specification for AI-assisted and autonomous software development. Covers core principles, autonomy levels, hallucination detection, security governance, and multi-agent orchestration.

## Core Principles (P1-P11)

| # | Principle | Essence |
|---|-----------|---------|
| P1 | Business-Driven | Every development activity must trace to a business goal |
| P2 | DCP Gate | Decision checkpoints between phases, never skip |
| P3 | TDD First | Tests before implementation, Red must fail before Green |
| P4 | Human Review | All AI-generated code requires human review before merge |
| P5 | No Secrets in Code | Keys, passwords, tokens never appear in code or config |
| P6 | Single Source of Truth | Each fact defined once, everywhere else references it |
| P7 | Spec-Driven | AI coding requires explicit Spec files as input |
| P8 | Minimum Batch | One function or small module at a time |
| P9 | Prompt Versioning | Prompts used for generation must be versioned and traceable |
| P10 | Data Classification | Data sent to AI must be classified, sensitive data blocked |
| P11 | **Evidence Chain** | Every AI claim must have independently verifiable evidence |

## Autonomy Levels

| Level | Name | Human Intervention | When |
|-------|------|-------------------|------|
| L1 | Assisted Coding | Every step | New teams, safety-critical |
| L2 | Semi-Autonomous | Before each PR merge | **Recommended default** |
| L3 | Constrained Autonomous | Before PR merge + DCP gate | Night/weekend dev, self-healing CI |
| L4 | Fully Autonomous | DCP gate + periodic audit | Mature teams, low-risk changes |

## Document Structure

| # | Document | Description |
|---|----------|-------------|
| 00 | [INDEX](ai-coding/INDEX.md) | Navigation and overview |
| 01 | [Core Specification](ai-coding/01-core-specification.md) | Core principles, autonomy levels, TDD, Spec-driven, hallucination detection |
| 02 | [Auto-Coding Practices](ai-coding/02-auto-coding-practices.md) | Autonomous modes, scheduled tasks, self-healing CI, night development |
| 03 | [Multi-Agent & Multi-Surface](ai-coding/03-multi-agent-multi-surface.md) | Sub-agents, Agent SDK, multi-platform collaboration |
| 04 | [Security & Governance](ai-coding/04-security-governance.md) | Enterprise deployment, permission management, MCP security, compliance |
| 05 | [Tool Reference](ai-coding/05-tool-reference.md) | CLI reference, settings, hooks, skills, configuration templates |
| 06 | [Automation Replacements](ai-coding/06-automation-replacements-analysis.md) | Automation analysis for manual intervention points |
| 07 | [Anti-Hallucination](ai-coding/07-anti-hallucination.md) | 40 hallucination types, evidence chain methodology, detection strategies |

## Anti-Hallucination System (v5.1)

**40 hallucination types** across 7 categories:

| Category | Count | Examples |
|----------|-------|---------|
| Existence | 6 | Non-existent APIs, files, variables |
| Execution | 5 | Claimed but unexecuted operations |
| Verification | 6 | Fake test passes, selective validation |
| Logic | 7 | Reversed conditions, missing boundaries, race conditions |
| Description | 5 | Comment-code mismatch, PR description lies |
| Cognition | 6 | False completion, misunderstood context |
| Security | 5 | Fake parameterization, encoding vs encryption |

**Evidence Chain Architecture:**

```
L1 Intent Evidence → L2 Plan Evidence → L3 Action Evidence → L4 Verification Evidence → L5 Review Evidence
```

**5 Core Methods:**
1. Evidence Chain (Chain of Evidence)
2. Multi-dimensional Cross-validation
3. Counterfactual Testing
4. Claim-Evidence-Verify (CEV) Protocol
5. Statistical Anomaly Detection

## Quick Start

1. Read [INDEX.md](ai-coding/INDEX.md) for navigation
2. Start with [Core Specification](ai-coding/01-core-specification.md) for principles and autonomy model
3. For auto-coding setup, read [Auto-Coding Practices](ai-coding/02-auto-coding-practices.md)
4. For security, read [Security & Governance](ai-coding/04-security-governance.md)
5. For hallucination mitigation, read [Anti-Hallucination](ai-coding/07-anti-hallucination.md)

## License

MIT
