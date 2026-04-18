# AI Coding 规范 v5.4：发布管理

> 版本：v5.4 | 2026-04-18
> 定位：大规模 Auto-Coding 场景下的版本控制、发布说明、变更日志、Feature Flag 发布标注、发布节奏、发布检查清单与 Hotfix 流程
> 前置：[01-core-specification.md](01-core-specification.md) P1-P11、[06-cicd-pipeline.md](06-cicd-pipeline.md) L0-L5 Pipeline、[13-deploy-rollback.md](13-deploy-rollback.md) 部署策略与 Feature Flag

---

## 第 1 章：核心原则

### 1.1 为什么需要独立的发布管理规范

大规模 Auto-Coding = 每天数十至数百个 AI 生成的 PR 合并到 main。没有标准化的发布管理意味着：

- **版本混乱**：没有统一的版本编号规则，无法追溯哪个版本包含哪些 AI 生成的变更
- **发布说明手工编写**：在高吞吐场景下人工编写 Release Notes 不可能跟上发布节奏
- **变更日志漂移**：CHANGELOG 与代码实际变更不一致，违反 P11 证据链
- **Feature Flag 堆积**：AI 生成的 Flag 不被及时清理，导致代码中充满死分支
- **Hotfix 与正常发布冲突**：紧急修复和常规发布争夺同一发布窗口，增加回滚风险

**核心原则**：发布是代码交付的最终形态。在 Auto-Coding 场景下，发布管理必须与代码生成同等自动化、同等严格。

### 1.2 发布管理覆盖范围

| 领域 | 本章覆盖内容 | 相关文档 |
|------|------------|---------|
| 版本号 | SemVer + Auto-Coding 后缀，谁决定 bump | 本文档第 2 章 |
| Release Notes | AI 自动生成，从 commit/PR/Spec 聚合 | 本文档第 3 章 |
| Change Log | 结构化 CHANGELOG 格式 | 本文档第 4 章 |
| Feature Flag | Release/CHANGELOG 中的 Flag 标注、清理期限追踪 | 本文档第 5 章 + [13-deploy-rollback.md](13-deploy-rollback.md) 第 5 章 |
| 发布节奏 | Cadence 定义、批量大小规则 | 本文档第 6 章 |
| 发布检查清单 | 发布前必须验证的条目 | 本文档第 7 章 |
| Hotfix | 紧急发布流、Bypass 规则、事后修复 | 本文档第 8 章 |

---

## 第 2 章：版本编号

### 2.1 SemVer 扩展格式

在标准 SemVer（`MAJOR.MINOR.PATCH`）基础上，Auto-Coding 场景追加后缀以支持追溯。

```
完整版本号 = MAJOR.MINOR.PATCH - autocoding.{commit_sha_short}.{batch_id}

示例：
  1.2.4-autocoding.9c3d7e21.batch-042
  1.2.4-autocoding.9c3d7e21.hotfix-001
  2.0.0                           （首次 GA 发布，无后缀）
```

| 段 | 说明 | 示例 |
|---|------|------|
| **MAJOR** | 不兼容的 API 变更 | `2` |
| **MINOR** | 向后兼容的功能新增 | `2.3` |
| **PATCH** | 向后兼容的 Bug 修复 | `2.3.1` |
| **autocoding** | 标识此版本由 Auto-Coding Pipeline 生成 | 固定字符串 |
| **commit_sha_short** | 触发此发布的 main 分支 commit SHA（前 8 位） | `9c3d7e21` |
| **batch_id** | 发布批次编号，格式 `batch-NNN` 或 `hotfix-NNN` | `batch-042` |

### 2.2 版本 Bump 决策规则

| 变更类型 | Bump 级别 | 谁决定 | 决策依据 |
|---------|----------|-------|---------|
| **破坏性 API 变更** | MAJOR | **人工**（架构师/技术负责人） | 09-api-contracts.md 破坏性变更检测 |
| **向后兼容新功能** | MINOR | **AI 建议 + 人工确认** | Spec 中定义的 Feature 完成并通过 L4 验证 |
| **Bug 修复** | PATCH | **AI 自动** | CI 检测到测试失败修复，无新增 Spec |
| **Hotfix** | PATCH + `hotfix-NNN` | **AI 自动 + on-call 确认** | 第 8 章 Hotfix 流程 |
| **仅文档/配置变更** | PATCH（或跳过） | **AI 自动** | 不影响运行时的变更 |

**AI 特有规则**：
- AI 在 PR 描述中必须**建议**版本 bump 级别，但 MAJOR bump 必须人工确认
- AI 不得自行决定 MAJOR bump。MAJOR bump 必须由人类在 DCP 门禁中批准
- 同一批次内的多个 PR，取最高的 bump 级别

### 2.3 版本标签与 Git Tag

```
Git Tag 格式 = v{MAJOR}.{MINOR}.{PATCH}[-autocoding.{sha}.{batch_id}]

示例：
  v1.2.4-autocoding.9c3d7e21.batch-042
  v1.2.5-autocoding.3f8a1b2c.hotfix-001
  v2.0.0
```

**规则**：
- 每次发布**必须**在 Git 上创建对应 Tag
- Tag 必须由 CI Pipeline（L5 层）自动创建，AI 不得直接执行 `git tag`
- Tag 创建后必须附带签名（`git tag -s`），签名为 CI 系统的 GPG 密钥

### 2.4 版本追溯文件

每次发布后，CI 自动在仓库根目录生成 `.gate/release-version.json`：

```json
{
  "type": "release-version",
  "version": "1.2.4-autocoding.9c3d7e21.batch-042",
  "semver": { "major": 1, "minor": 2, "patch": 4 },
  "bump_level": "MINOR",
  "bump_decided_by": "ai-suggestion + human-approval",
  "bump_reason": "New feature: AI recommendation engine (Spec F042)",
  "git_tag": "v1.2.4-autocoding.9c3d7e21.batch-042",
  "main_branch_commit": "9c3d7e21f3a8b1c4d5e6f7a8b9c0d1e2f3a4b5c6",
  "batch_id": "batch-042",
  "pr_count": 7,
  "specs_completed": ["F042", "F039"],
  "released_at": "2026-04-18T16:00:00Z",
  "released_by": "ci-pipeline",
  "artifacts": [
    ".gate/release-notes.md",
    ".gate/changelog-diff.md",
    ".gate/release-checklist.json"
  ]
}
```

---

## 第 3 章：Release Notes 自动生成

### 3.1 生成流程

```
PR 合并到 main
  │
  ├─→ CI 聚合数据源：
  │     1. 本批次所有 PR 的 commit messages
  │     2. 本批次所有 PR 的描述（含 Spec 引用、部署信息）
  │     3. specs/ 中已完成的 Spec 文件
  │     4. .gate/ 中的验证结果（Pipeline L0-L4 状态）
  │     5. CHANGELOG.md 的上次发布点
  │
  ├─→ AI 生成 Release Notes 草稿
  │     按类别分组：Breaking / Features / Fixes / Internal
  │
  ├─→ 模板渲染 → .gate/release-notes.md
  │
  ├─→ L3 层验证：Release Notes 与变更的一致性检查
  │
  └─→ 发布时附加到 Git Tag + 发布系统
```

### 3.2 数据源优先级

| 数据源 | 优先级 | 用途 |
|-------|:------:|------|
| **PR 描述** | 1 | 主要信息源，含 Spec 引用、部署信息、Feature Flag 声明 |
| **Spec 文件** | 2 | 功能验收条件、用户故事、商业目标 |
| **Commit messages** | 3 | 补充细节，但不得与 PR 描述冲突 |
| **Pipeline 结果** | 4 | 性能指标、测试覆盖率、安全评分 |
| **CHANGELOG 差异** | 5 | 自上次发布以来的变更汇总 |

**冲突解决**：PR 描述与 commit message 冲突时，以 PR 描述为准。Spec 与 PR 描述冲突时，以 Spec 为准（Spec 是单一信息源）。

### 3.3 Release Notes 模板

```markdown
# Release v{VERSION}

> 发布日期：{DATE} | 批次：{BATCH_ID} | 触发：{TRIGGER}

## 概要

{AI 生成的 2-3 句发布摘要}

## Breaking Changes

> {若无，标注 "None"}

- **{组件}**: {变更描述}
  - 迁移路径：{说明}
  - 影响范围：{哪些用户/系统受影响}

## New Features

- **{Spec ID}**: {功能描述}
  - 验收条件：{来自 Spec 的 Acceptance Criteria}
  - Feature Flag: `{flag_name}`（默认关闭）
  - Kill Switch: `{kill_switch_name}`

## Bug Fixes

- **#{issue}**: {修复描述}
  - 根因：{5 Whys 分析结果}
  - 验证：{如何确认修复有效}

## Performance

- {性能指标变化，来自 .gate/performance-report.json}

## Security

- {SAST 结果摘要，来自 .gate/security-report.json}

## Internal Changes

- {基础设施、工具链、CI 变更}

## 证据链

- Pipeline 报告: `.gate/pipeline-report-{BATCH_ID}.json`
- 版本追溯: `.gate/release-version.json`
- 发布检查清单: `.gate/release-checklist.json`
```

### 3.4 AI 生成质量要求

| 要求 | 说明 | 验证方式 |
|------|------|---------|
| **不得编造** | Release Notes 中每个声明必须有对应的 commit/PR/Spec 证据 | L3 层交叉引用检查 |
| **不得遗漏** | 本批次所有 MAJOR/MINOR 级别变更必须出现在 Release Notes 中 | 版本追溯对比 |
| **Breaking Changes 置顶** | 破坏性变更必须在最前面，且用红色/警告标记 | 模板检查 |
| **Spec 引用** | 每个 Feature 必须引用 Spec ID | PR 描述解析 |
| **Flag 标注** | 涉及 Feature Flag 的功能必须标注 Flag 名称和默认状态 | Flag 配置解析 |
| **人类可读** | 技术术语必须有简短解释 | AI Reviewer 可读性检查 |

### 3.5 审核与发布

| 自治等级 | Release Notes 审核方式 |
|---------|---------------------|
| **L1** | AI 生成草稿 → 人工逐条审核 → 人工发布 |
| **L2** | AI 生成草稿 → 人工审核概要 → 人工发布 |
| **L3** | AI 生成 → L3 自动验证 → 人工抽样审核（≥10%）→ CI 发布 |
| **L4** | AI 生成 → L3/L4 自动验证 → 定期人工审计 → CI 自动发布 |

---

## 第 4 章：Change Log 管理

### 4.1 CHANGELOG 格式（Keep a Changelog 扩展）

遵循 [Keep a Changelog](https://keepachangelog.com/) 格式，追加 Auto-Coding 扩展字段。

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- ai.F042: AI recommendation engine with kill switch (`ai.F042.new_recommendation_engine`)
  [PR #142](link) | [Spec F042](specs/F042.md)

### Changed
- Upgraded auth-service dependency to >= 1.1.0
  [PR #145](link)

### Fixed
- ai.F039: Fixed race condition in user session cleanup
  [PR #138](link) | [Spec F039](specs/F039.md)
  Root cause: Missing lock in concurrent goroutine access (5-Whys: Why 3)

## [1.2.4-autocoding.9c3d7e21.batch-042] - 2026-04-18

### Added
- ...

### Security
- Patched CVE-2026-XXXX in dependency `openssl`
  [PR #150](link) | SBOM updated

### Internal
- CI pipeline L3 layer added AI hallucination detection
  [PR #135](link)
```

### 4.2 Auto-Coding 扩展字段

| 字段 | 格式 | 说明 |
|------|------|------|
| **ai.{Spec ID}** | 前缀 | 标注此变更由哪个 Spec 驱动 |
| **Root cause** | 附录 | Bug 修复条目附带 5 Whys 根因（来自 01-core-specification.md T4） |
| **Feature Flag** | 括号标注 | 标注关联的 Flag 名称 |
| **PR / Spec 链接** | 后缀 | 可追溯证据 |

### 4.3 更新时机与责任

| 事件 | 谁更新 | 更新内容 |
|------|-------|---------|
| **PR 合并到 main** | **AI 自动** | 在 `## [Unreleased]` 段添加条目 |
| **发布时** | **CI 自动** | 将 `## [Unreleased]` 重命名为 `## [{VERSION}] - {DATE}` |
| **Hotfix 合并** | **AI 自动** | 在 `## [Unreleased]` 段添加 `[HOTFIX]` 标记条目 |

**规则**：
- CHANGELOG 更新是 CI Pipeline L1 层的一部分，PR 合并后自动触发
- AI 更新 CHANGELOG 时必须保持现有条目不变，仅追加新条目
- CHANGELOG 文件格式错误 = L1 阻断

### 4.4 CHANGELOG 一致性验证

CI 在 L3 层执行以下检查：

| 检查项 | 规则 | 失败策略 |
|-------|------|---------|
| **完整性** | 每个合并的 PR 必须有对应的 CHANGELOG 条目 | L3 阻断 |
| **Spec 引用** | ai.* 变更必须引用 Spec ID | L3 警告 |
| **格式** | 符合 Keep a Changelog 格式 | L1 阻断 |
| **重复** | 同一变更不得出现多条不同描述 | L3 警告 |
| **Unreleased 清洁度** | 发布后 Unreleased 段必须为空 | L3 警告 |

---

## 第 5 章：Feature Flag 发布标注

> 注：Feature Flag 的详细技术规范（分层、Kill Switch、配置模板、渐进 Rollout 步骤、AI 生成 Flag 强制要求、清理流程）在 [13-deploy-rollback.md](13-deploy-rollback.md) 第 5 章定义。本章仅覆盖**发布管理层面的 Flag 标注**要求。

### 5.1 发布层面的 Flag 标注

每次发布时，Release Notes 和 CHANGELOG 必须标注本批次涉及的 Feature Flag 状态。这些标注从 PR 描述和 Flag 配置文件中自动提取，由 CI L3 层验证。

| 标注项 | Release Notes | CHANGELOG | 来源 |
|-------|:------------:|:---------:|------|
| **Flag 名称** | 每个新 Feature 条目后标注 | `## [Unreleased]` 段括号内标注 | PR 描述 / `feature-flags/*.yaml` |
| **默认状态** | 标注 `(default: off)` 或 `(default: on)` | 同 Release Notes | Flag 配置 `default` 字段 |
| **Kill Switch** | 标注 Kill Switch 名称 | 不标注 | Flag 配置 `kill_switch` 字段 |
| **清理截止日期** | 标注 `(cleanup deadline: {date})` | 不标注 | 13-deploy-rollback.md 5.4 节（4 周上限） |
| **Rollout 状态** | 已全量开启的标注 `(rollout: 100%)` | 标注 `retired` 若 Flag 已清理 | CI 从配置中心读取 |

### 5.2 CHANGELOG 中的 Flag 追踪

CHANGELOG 条目中的 Flag 标注格式（见第 4.2 节扩展字段）：

```markdown
### Added
- ai.F042: AI recommendation engine (`ai.F042.new_recommendation_engine`, default: off)
  [PR #142](link) | [Spec F042](specs/F042.md)
  Cleanup deadline: 2026-05-18
```

Flag 清理后的 CHANGELOG 条目：

```markdown
### Internal
- Retired flag `ai.F031.old_search_engine` (previously F031)
  [PR #155](link)
```

### 5.3 清理期限追踪

CI 在发布检查清单（第 7 章）中增加以下 Flag 清理期限检查：

| 检查项 | 规则 | 失败策略 |
|-------|------|---------|
| **过期 Flag 未清理** | 存在 > 45 天的 `ai.*` Flag | L3 阻断（见 13-deploy-rollback.md 5.4） |
| **清理 PR 未合并** | 过期 Flag 的清理 PR 已创建但未合并 | L3 警告 |
| **清理 Deadline 临近** | Flag 清理截止日期 ≤ 7 天 | Release Notes 中标注警告 |
| **无清理计划** | Flag 创建时未定义清理截止日期 | L3 警告 |

Flag 健康报告（`.gate/flag-health-report.json`）由 13-deploy-rollback.md 第 5 章定义的流程生成，发布管理仅消费该报告用于清理期限检查。

---

## 第 6 章：发布节奏

### 6.1 发布 Cadence 定义

| 发布类型 | 节奏 | 触发条件 | 适用场景 |
|---------|------|---------|---------|
| **常规发布** | 每周 2 次（周二、周四 14:00 UTC） | main 有已合并且通过 Pipeline 的变更 | L2-L4 日常开发 |
| **按需发布** | 随时（受限于批量规则） | 单次 PR 包含 P0/P1 修复或独立 Feature | 紧急但非 Hotfix |
| **Hotfix** | 即时 | P0/P1 生产事故（见第 8 章） | 紧急修复 |
| **大版本发布** | 按需（人工决定） | MAJOR bump | 架构级变更 |

**AI 特有规则**：
- L3/L4 下 AI 自动在常规发布窗口触发发布
- AI 不得在维护窗口（13-deploy-rollback.md 第 8 章）触发发布
- 两次常规发布间隔不得 < 4 小时

### 6.2 批量大小规则

| 规则 | 说明 | 例外 |
|------|------|------|
| **最大批量** | 单次发布最多包含 **20 个 PR** | 大版本发布除外 |
| **最小批量** | 单次发布至少包含 **1 个 PR** | — |
| **混合限制** | 同一发布中，AI 生成的 PR 不得超过总数的 **80%** | L4 全自主模式 |
| **Spec 覆盖** | 同一 Spec 的多个 PR 必须在同一批次中发布 | 保持 Spec 原子性 |
| **依赖约束** | 有依赖关系的 PR 必须在同一批次中，或已在上一个批次中发布 | — |

### 6.3 批次聚合策略

```
PR 合并到 main
  │
  ├─→ 加入 Unreleased Pool
  │
  ├─→ 发布窗口到达 或  Pool 达到阈值（15 PR / 24h）
  │     │
  │     ├─→ 检查批量规则（≤20 PR）
  │     │     超过 20 PR → 拆分为多个批次
  │     │
  │     ├─→ 检查依赖约束（同一 Spec 的 PR 不拆分）
  │     │
  │     ├─→ 检查混合限制（AI PR ≤ 80%）
  │     │
  │     └─→ 生成批次
  │           │
  │           ├─→ 运行发布检查清单（第 7 章）
  │           ├─→ 决定版本号（第 2 章）
  │           ├─→ 生成 Release Notes（第 3 章）
  │           └─→ 执行部署（06-cicd-pipeline.md L5）
```

### 6.4 发布窗口冲突解决

| 冲突场景 | 解决策略 |
|---------|---------|
| 两个发布窗口同时到达 | 串行执行，间隔 ≥ 30 分钟 |
| 发布窗口与 Hotfix 冲突 | 暂停常规发布，优先 Hotfix |
| 发布窗口与维护窗口冲突 | 推迟到维护窗口结束后 |
| 发布窗口与业务高峰期冲突 | 推迟到下一个窗口 |

---

## 第 7 章：发布检查清单

### 7.1 发布前检查清单

每次发布前，CI 必须自动验证以下所有条目。任一项目失败 = 发布阻断。

```
## 发布检查清单 v5.4

### 版本控制
- [ ] 版本号符合 SemVer 扩展格式（第 2 章）
- [ ] Git Tag 已创建并签名
- [ ] MAJOR bump 已获人工批准（如适用）
- [ ] .gate/release-version.json 已生成

### Pipeline 状态
- [ ] 本批次所有 PR 的 L0-L4 全部通过
- [ ] 无 SAST 高危/危急漏洞
- [ ] 测试覆盖率 >= 项目基线（不得下降）
- [ ] 性能基线检查通过（11-performance-baseline.md）

### 代码质量
- [ ] 无未解决的 lint 错误
- [ ] CHANGELOG 已更新且格式正确（第 4 章）
- [ ] Release Notes 已生成且通过一致性检查（第 3 章）
- [ ] 所有 Spec 的 Acceptance Criteria 已验证

### Feature Flag
- [ ] 所有新 Feature 已配置 Flag 且默认关闭（第 5 章）
- [ ] 所有 AI 生成 Feature 已配置 Kill Switch
- [ ] 无过期 Flag（> 45 天）未处理

### 安全与合规
- [ ] 无硬编码密钥（P5 验证）
- [ ] 依赖无已知高危 CVE（10-dependency-management.md）
- [ ] SBOM 已更新
- [ ] 数据分级扫描通过（P10 验证）

### 部署就绪
- [ ] 部署策略已定义（canary / blue-green / rolling）
- [ ] 回滚计划已定义且可执行（.gate/rollback-plan.json）
- [ ] LKG 版本已记录
- [ ] 不在维护窗口内
- [ ] 不在业务高峰期
- [ ] 监控告警已就绪

### 证据链（P11）
- [ ] .gate/pipeline-report-{BATCH_ID}.json 存在
- [ ] .gate/release-checklist.json 存在
- [ ] 所有证据跨引用 ≥ 2 条
```

### 7.2 检查清单输出

```json
{
  "type": "release-checklist",
  "batch_id": "batch-042",
  "version": "1.2.4-autocoding.9c3d7e21.batch-042",
  "checked_at": "2026-04-18T15:55:00Z",
  "result": "passed",
  "checks": {
    "version_control": { "status": "passed", "details": "..." },
    "pipeline_status": { "status": "passed", "details": "..." },
    "code_quality": { "status": "passed", "details": "..." },
    "feature_flag": { "status": "passed", "details": "..." },
    "security_compliance": { "status": "passed", "details": "..." },
    "deployment_ready": { "status": "passed", "details": "..." },
    "evidence_chain": { "status": "passed", "details": "..." }
  },
  "blockers": [],
  "warnings": [
    "Flag ai.F031.old_search_engine 已过期，清理 PR #155 待合并"
  ],
  "approved_by": "ci-pipeline",
  "approved_at": "2026-04-18T15:55:30Z"
}
```

### 7.3 各自治等级的检查清单执行

| 检查类别 | L1 | L2 | L3 | L4 |
|---------|----|----|----|----|
| 版本控制 | 人工确认 | 人工确认 | AI 检查 + 人工抽检 | AI 自动 |
| Pipeline 状态 | 人工确认 | 人工确认 | AI 自动 | AI 自动 |
| 代码质量 | 人工确认 | 人工确认 | AI 自动 + 人工抽检 | AI 自动 + 定期审计 |
| Feature Flag | 人工确认 | 人工确认 | AI 自动 | AI 自动 |
| 安全与合规 | 人工确认 | 人工确认 | AI 自动 + 安全团队审批 | AI 自动 + 定期审计 |
| 部署就绪 | 人工确认 | 人工确认 | AI 自动 | AI 自动 |
| 证据链 | 人工逐项核对 | AI 收集 + 人工确认 | AI 自动 | AI 自动 + 定期审计 |

---

## 第 8 章：Hotfix 流程

### 8.1 Hotfix 定义与触发条件

| 触发条件 | 严重级别 | 响应 SLA |
|---------|---------|---------|
| **生产 P0 事故**（核心功能不可用、数据丢失） | P0 | 15 分钟内发布 |
| **生产 P1 事故**（部分功能不可用、性能严重退化） | P1 | 1 小时内发布 |
| **安全漏洞**（CVE 高危、密钥泄漏） | P0 | 30 分钟内发布 |
| **P2 缺陷** | P2 | 走常规发布流程 |

### 8.2 Hotfix 流程

```
生产事故检测
  │
  ├─→ 触发告警（监控/用户报告）
  │
  ├─→ 定级：P0/P1 → 启动 Hotfix 流程
  │
  ├─→ 创建 hotfix 分支
  │     分支名：hotfix/{issue_id}-{YYYYMMDD}
  │     例如：hotfix/INC-2026-0418-20260418
  │
  ├─→ AI 生成修复代码（基于事故根因分析）
  │     约束：最小修复范围，仅修改与事故直接相关的代码
  │
  ├─→ 精简 Pipeline 执行（第 8.3 节）
  │
  ├─→ on-call 确认（P0 必须，P1 可跳过）
  │
  ├─→ 部署 Hotfix 版本
  │     版本格式：{VERSION}-hotfix-NNN
  │     策略：加速金丝雀（5% → 50% → 100%，每步 5 分钟）
  │
  ├─→ 验证 Hotfix 效果
  │     核心指标恢复正常 = Hotfix 成功
  │
  └─→ 事后修复（第 8.5 节）
```

### 8.3 精简 Pipeline（Hotfix 专用）

Hotfix 可以绕过部分 Pipeline 层级，但**安全门禁不可绕过**。

| Pipeline 层 | Hotfix 处理 | 说明 |
|:-----------:|:----------:|------|
| **L0** | **执行** | pre-commit hook 必须运行，但失败不阻断（仅警告） |
| **L1** | **执行** | 编译验证不可跳过 |
| **L2** | **执行** | 仅运行与修复范围相关的测试（选择性测试） |
| **L3 lint** | **跳过** | 格式/lint 问题不得阻断 Hotfix |
| **L3 SAST** | **执行** | 安全扫描**不可跳过**，高危漏洞必须修复 |
| **L3 幻觉** | **执行** | AI 生成修复代码必须通过幻觉检测 |
| **L4 E2E** | **跳过** | 端到端测试不得阻断 Hotfix，事后补测 |
| **L4 性能** | **跳过** | 性能基线检查不得阻断 Hotfix |
| **L5 部署** | **加速执行** | 金丝雀窗口缩短（每步 5 分钟） |

**安全底线**：L3 SAST（安全扫描）是 Hotfix 流程中**唯一不可跳过的质量门禁**。L1 编译验证、L2 选择性测试、L3 幻觉检测同样不可跳过。Hotfix 不得引入新的安全漏洞。

### 8.4 Hotfix 版本规则

| 规则 | 说明 |
|------|------|
| **PATCH bump** | Hotfix 永远只 bump PATCH 级别 |
| **Hotfix 后缀** | 版本号追加 `-hotfix-NNN`，NNN 从 001 开始递增 |
| **Git Tag** | `v{MAJOR}.{MINOR}.{PATCH}-hotfix-{NNN}` |
| **独立批次** | Hotfix 发布**不计入**常规发布的批量限制 |
| **常规发布合并** | 下一个常规发布必须包含所有未合并的 Hotfix 变更 |

### 8.5 事后修复（Post-Hotfix Reconciliation）

Hotfix 完成后 **24 小时内**必须完成以下事后修复动作：

| 动作 | 执行者 | 时限 |
|------|-------|------|
| **补测 L4 E2E** | AI 自动 | 24h |
| **补测性能基线** | AI 自动 | 24h |
| **补全 CHANGELOG** | AI 自动 | 12h |
| **生成 Hotfix 报告** | AI 自动 | 12h |
| **根因分析（5 Whys）** | AI 生成 + 人工确认 | 24h |
| **预防回归测试** | AI 自动 | 24h |
| **Hotfix 代码 Review** | 人工 | 24h |
| **合并到 main** | AI 创建 PR + 人工合并 | 48h |

### 8.6 Hotfix 报告模板

```json
{
  "type": "hotfix-report",
  "hotfix_id": "hotfix-001",
  "incident_id": "INC-2026-0418",
  "severity": "P0",
  "version": "1.2.5-autocoding.3f8a1b2c.hotfix-001",
  "created_at": "2026-04-18T10:00:00Z",
  "resolved_at": "2026-04-18T10:12:00Z",
  "resolution_time": "12 minutes",
  "root_cause": {
    "summary": "Database connection pool exhaustion due to missing timeout",
    "five_whys": [
      "Why 1: API returned 500 for all requests",
      "Why 2: Database connection pool was exhausted",
      "Why 3: Connection timeout was not configured",
      "Why 4: Default config omitted timeout parameter",
      "Why 5: [Root cause] Config template missing timeout default"
    ]
  },
  "fix": {
    "description": "Added default connection timeout (30s) to database config",
    "files_changed": ["config/database.yaml", "src/db/pool.go"],
    "pr": "#160"
  },
  "pipeline_bypassed": ["L3-lint", "L4-e2e", "L4-performance"],
  "pipeline_executed": ["L0", "L1", "L2-selective", "L3-SAST", "L3-hallucination", "L5-accelerated"],
  "sast_result": "clean",
  "reconciliation": {
    "e2e_test": "pending",
    "performance_test": "pending",
    "changelog_updated": true,
    "root_cause_analysis": true,
    "regression_test_added": true,
    "code_reviewed_by": "@reviewer-zhang",
    "merged_to_main": false
  }
}
```

### 8.7 Hotfix 与常规发布的冲突处理

| 场景 | 处理策略 |
|------|---------|
| Hotfix 发布中，常规发布窗口到达 | **暂停常规发布**，等待 Hotfix 完成后继续 |
| Hotfix 分支与 main 分叉 > 24h | Hotfix 完成后必须执行 `git rebase main` 并解决冲突 |
| Hotfix 与常规发布修改同一文件 | Hotfix 优先。常规发布的对应 PR 必须重新适配 |
| Hotfix 后下一个常规发布 | 常规发布必须包含 Hotfix 的所有变更，且 Release Notes 中单独标注 |

---

## 附录 A：发布管理 Artifact 清单

| 文件 | 生成时机 | 内容 |
|------|---------|------|
| `.gate/release-version.json` | 每次发布后 | 版本号、bump 级别、批次信息 |
| `.gate/release-notes.md` | 每次发布前 | AI 生成的 Release Notes |
| `.gate/release-checklist.json` | 发布前验证后 | 发布检查清单结果 |
| `.gate/pipeline-report-{BATCH_ID}.json` | Pipeline 完成后 | L0-L5 各层执行结果 |
| `.gate/flag-health-report.json` | 每周自动生成 | Feature Flag 健康状态 |
| `.gate/hotfix-report-{NNN}.json` | Hotfix 完成后 | Hotfix 详情、根因分析、事后修复状态 |
| `CHANGELOG.md` | PR 合并时更新 | 结构化变更日志 |

## 附录 B：版本号决策补充

以下为 2.2 节未覆盖的额外 bump 规则（基础规则见第 2.2 节）：

| 变更场景 | Bump 级别 | 决定者 | 是否需要人工 |
|---------|:--------:|-------|:-----------:|
| 仅文档变更 | PATCH（或跳过） | AI 自动 | 否 |
| 仅配置变更 | PATCH（或跳过） | AI 自动 | 否 |
| 依赖升级（非安全） | PATCH | AI 自动 | 否 |
| 依赖升级（CVE 修复） | PATCH | AI 自动 | 否（但需安全团队通知） |

## 附录 C：与其他文档的交叉引用

| 引用文档 | 关联章节 | 关联内容 |
|---------|---------|---------|
| [01-core-specification.md](01-core-specification.md) | P1-P11, T4 | 核心原则、5 Whys 根因分析 |
| [06-cicd-pipeline.md](06-cicd-pipeline.md) | L0-L5 | Pipeline 分层结构、Self-Correction |
| [07-anti-hallucination.md](07-anti-hallucination.md) | 3.4 | AI 幻觉检测 |
| [08-database-migration.md](08-database-migration.md) | 6.1 | 数据库部署协调 |
| [09-api-contracts.md](09-api-contracts.md) | 2.2 | API 破坏性变更检测 |
| [10-dependency-management.md](10-dependency-management.md) | 7.1 | CVE 检查、SBOM |
| [11-performance-baseline.md](11-performance-baseline.md) | 7.1 | 性能基线检查 |
| [13-deploy-rollback.md](13-deploy-rollback.md) | 第 5 章 | Feature Flag 技术规范、Kill Switch |
