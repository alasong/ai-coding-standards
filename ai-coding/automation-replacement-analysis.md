# 中等可行性替代方案详细分析

> 生成时间：2026-04-14 | 分析范围：v5.0 规范中 5 项"部分自动"干预点的完全自动化替代方案

---

## 总览

| 编号 | 替代项 | 当前状态 | 目标状态 | 目标文档 |
|------|--------|---------|---------|---------|
| #20 | 降级判定 | 部分自动，部分人工 | 完全自动化 | `01-core-specification.md` |
| #21 | 幻觉检测结果确认 | L3 人工确认 AI Reviewer | AI 置信度分级 | `01-core-specification.md`, `02-auto-coding-practices.md` |
| #22 | 审计抽样执行 | L4 每周人工审计 >=10% PR | AI 全量审计 + 人工仅审可疑 | `01-core-specification.md`, `04-security-governance.md` |
| #23 | 密钥泄露专项检测 | L4 审计期专项检测 | 持续 CI Gate 扫描 | `02-auto-coding-practices.md`, `04-security-governance.md` |
| #24 | 文档漂移确认 | L3 人工确认漂移检测 | AI 自动修复简单漂移 | `02-auto-coding-practices.md` |

---

## #20 降级判定 — 完全自动化

### 1. 当前位置

**主要定义**：`/home/song/blank/ai-coding/01-core-specification.md`

| 章节 | 行号 | 内容 |
|------|------|------|
| 第 2 章 2.6 节 | L293-L308 | 自治等级降级条件（8 种触发条件） |
| 第 3 章 3.7 节 | L517-L530 | 质量降级与回退机制（Level 0-3） |
| 降级判定说明 | L528 | "降级判定：每周自动统计各 Feature 的 AI 代码一次通过率，自动触发对应级别" |

**辅助定义**：`/home/song/blank/ai-coding/02-auto-coding-practices.md`
- L2493-L2501：`autonomy-degradation` 告警配置示例
- L2551-L2560：降级检查清单示例
- L2723：降级检查日志路径 `.omc/logs/metrics.json`

**当前人工介入点**：规范声明"降级是自动的，不需要审批"（L308），但实际上：
1. 恢复条件中的"技术负责人批准"（L299, L302）需要人工操作
2. 降级报告的生成和分发（附录 G.4, L1846-L1858）依赖人工填写
3. 降级后流程切换（如"改为'人写框架，AI 填充细节'"）需要人工干预

### 2. 替代方案详细设计

#### 2.1 架构：降级控制器（Degradation Controller）

```
┌─────────────────────────────────────────────────────┐
│                Degradation Controller                 │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌───────────┐  │
│  │ Metrics  │───▶│ Rule Engine  │───▶│ Executor  │  │
│  │ Collector│    │ (8 Rules)    │    │           │  │
│  └──────────┘    └──────────────┘    └─────┬─────┘  │
│       │                   │                 │        │
│       ▼                   ▼                 ▼        │
│  .omc/logs/          Decision Log    Slack/CI    │
│  metrics.json         + Audit Trail   Notification │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  Recovery Manager (自动恢复检查)               │   │
│  │  - 轮询恢复条件（每小时）                      │   │
│  │  - 满足条件 → 自动发送升级审批请求              │   │
│  │  - 审批通过 → 自动升级                        │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

#### 2.2 机制设计

**实时监控指标**：

| 指标 | 数据源 | 采集频率 | 阈值 |
|------|--------|---------|------|
| 生产安全事故 | CI/CD pipeline + Sentry | 实时（webhook） | any P0/P1 event |
| 幻觉代码逃逸 | GitHub PR merge events + AI Reviewer report | 每 PR | any merge with hallucination |
| 审计通过率 | `.gate/audit-report.json` | 每周 | < 95% 连续 2 周 |
| 自主成功率 | `.omc/logs/metrics.json` | 每日 | < 70% 连续 2 周 |
| TDD 执行率 | CI TDD Gate report | 每 PR | < 80% |
| 密钥泄露 | gitleaks/trufflehog CI results | 每次 push | any detection |
| AI 提供者通过率 | `.gate/tdd-report.json` | 每日 | < 40% |
| Self-Correction 失败率 | AI execution logs | 每次任务 | 5 次 > 3 轮 |

#### 2.3 AI 能力需求

1. **指标聚合引擎**：从多个数据源实时采集指标，计算滚动窗口统计值
2. **规则评估引擎**：对 8 条降级规则进行实时评估，支持 AND/OR 组合条件
3. **自动执行引擎**：触发降级动作（修改自治等级配置、通知 Slack、创建审计工单）
4. **恢复监控器**：定期检查恢复条件，自动发起升级审批流程

#### 2.4 安全守卫

- **降级操作幂等**：同一条件多次触发只执行一次降级
- **降级操作可回滚**：所有降级动作记录到 `.omc/logs/degradation-audit.jsonl`
- **紧急停止**：人工可通过 `echo "MANUAL_OVERRIDE" > .omc/state/degradation-override` 暂停自动降级
- **防抖动**：连续条件需满足时间窗口（如"连续 2 周"），避免瞬时波动触发

### 3. 配置示例

#### 3.1 降级控制器配置（`.omc/config/degradation-rules.yaml`）

```yaml
# Degradation Rules Configuration
# 对应 01-core-specification.md 第 2 章 2.6 节

version: "v5.0"
evaluation_interval: "1h"
state_file: ".omc/state/autonomy-level.json"
audit_log: ".omc/logs/degradation-audit.jsonl"

rules:
  - id: prod-security-incident
    name: "生产安全事故"
    condition: "metrics.security.p0_events > 0 OR metrics.security.p1_events > 0"
    data_source: "sentry-webhook"
    target_level: "L2"
    recovery:
      conditions:
        - "root_cause_analysis_complete == true"
        - "fix_verified == true"
        - "tech_lead_approval == true"
      auto_request_approval: true
      notify: "tech-lead-slack-channel"

  - id: hallucination-escape
    name: "幻觉代码合并到 main"
    condition: "events.hallucination_merged_to_main > 0"
    data_source: "github-pr-webhook"
    target_level: "L2"
    cooldown: "24h"

  - id: audit-pass-rate-low
    name: "审计通过率连续低于 95%"
    condition: "metrics.audit_pass_rate < 0.95 AND metrics.audit_consecutive_weeks_low >= 2"
    data_source: ".gate/audit-report.json"
    target_level: "L3"
    current_level_required: "L4"

  - id: autonomy-success-rate-low
    name: "自主成功率连续低于 70%"
    condition: "metrics.autonomy_success_rate < 0.70 AND metrics.autonomy_consecutive_weeks_low >= 2"
    data_source: ".omc/logs/metrics.json"
    target_level: "L2"
    current_level_required: "L3"

  - id: tdd-compliance-low
    name: "TDD 执行率低于 80%"
    condition: "metrics.tdd_compliance_rate < 0.80"
    data_source: "ci-tdd-gate"
    target_level: "L1"

  - id: secret-leak
    name: "密钥泄露到代码仓库"
    condition: "events.secret_detected == true"
    data_source: "gitleaks-ci-result"
    target_level: "L1"
    immediate: true

  - id: ai-provider-degradation
    name: "AI 提供者质量严重退化"
    condition: "metrics.ai_first_pass_rate < 0.40"
    data_source: ".gate/tdd-report.json"
    target_level: "L2"

  - id: self-correction-exhausted
    name: "Self-Correction 连续失败"
    condition: "metrics.self_correction_exceeds_3_rounds >= 5"
    data_source: "ai-execution-logs"
    target_level: "L2"

# 质量降级规则（对应 01-core-specification.md 第 3 章 3.7 节）
quality_degradation:
  evaluation_window: "7d"
  metrics_source: ".gate/tdd-report.json"

  levels:
    - name: "L0-normal"
      condition: "first_pass_rate >= 0.80"
    - name: "L1-alert"
      condition: "first_pass_rate >= 0.60 AND first_pass_rate < 0.80"
    - name: "L2-degraded"
      condition: "first_pass_rate < 0.60"
      action: "switch_to_human_frame_ai_fill"
    - name: "L3-rollback"
      condition: "first_pass_rate < 0.40"
      action: "manual_coding_ai_assist_only"

notifications:
  on_degradation:
    - type: "slack"
      channel: "#ai-coding-governance"
      template: "AUTONOMY DEGRADED: {level} -> {target} | Reason: {rule_name} | Time: {timestamp}"
    - type: "github-issue"
      repo: "team/ai-governance"
      labels: ["degradation", "auto-created"]
  on_recovery_eligible:
    - type: "slack"
      channel: "#ai-coding-governance"
      template: "RECOVERY ELIGIBLE: {target} -> {current} | Waiting for approval"
```

#### 3.2 CI 集成（`.github/workflows/degradation-monitor.yml`）

```yaml
name: Degradation Monitor
on:
  schedule:
    - cron: "0 * * * *"
  workflow_run:
    workflows: ["PR Quality Gate"]
    types: [completed]

jobs:
  evaluate-degradation:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
    steps:
      - uses: actions/checkout@v4

      - name: Collect Metrics
        run: |
          python .omc/scripts/collect-metrics.py \
            --gate-dir .gate \
            --logs-dir .omc/logs \
            --output .omc/state/metrics-snapshot.json

      - name: Evaluate Degradation Rules
        run: |
          python .omc/scripts/evaluate-rules.py \
            --config .omc/config/degradation-rules.yaml \
            --metrics .omc/state/metrics-snapshot.json \
            --state .omc/state/autonomy-level.json \
            --audit-log .omc/logs/degradation-audit.jsonl

      - name: Execute Actions
        if: steps.evaluate.outputs.degraded == 'true'
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_GOVERNANCE_WEBHOOK }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python .omc/scripts/execute-degradation.py \
            --decision .omc/state/degradation-decision.json \
            --slack-webhook $SLACK_WEBHOOK \
            --github-token $GH_TOKEN
```

### 4. 预期效果

| 指标 | 当前状态 | 替代后 | 改善 |
|------|---------|--------|------|
| 降级检测延迟 | 每周人工检查（最长 7 天） | 每小时自动评估（最长 1 小时） | 168x 更快 |
| 人工时间投入 | 每周 ~30 分钟（检查指标、判断、执行降级） | 每周 ~5 分钟（仅处理审批请求） | 节省 ~83% |
| 降级一致性 | 依赖人工判断，可能不一致 | 规则驱动，100% 一致 | 消除人为偏差 |
| 降级报告生成 | 人工填写 checklist | 自动生成，附带完整审计轨迹 | 100% 覆盖 |

**风险评估**：
- 低风险：规则是规范中已定义的，自动化只是执行速度更快
- 中风险：恢复条件中的"技术负责人批准"仍需人工，但可改为自动发起审批请求
- 缓解措施：提供手动覆盖开关（`degradation-override` 文件），允许人工暂停自动降级

### 5. 前提条件

1. **指标采集基础设施**：所有 8 个降级指标的实时数据采集管道
2. **状态持久化**：`.omc/state/autonomy-level.json` 状态文件的读写机制
3. **规则引擎**：轻量级 YAML 规则解析和评估引擎（Python 或 Node.js）
4. **通知渠道**：Slack webhook、GitHub Issue 创建权限
5. **防抖动逻辑**：连续条件的时间窗口跟踪器
6. **手动覆盖机制**：人工暂停自动降级的能力

---

## #21 幻觉检测结果确认 — AI 置信度分级

### 1. 当前位置

**主要定义**：`/home/song/blank/ai-coding/01-core-specification.md`

| 章节 | 行号 | 内容 |
|------|------|------|
| 第 4 章 4.4 节 | L615-L654 | AI Reviewer Prompt 模板（人工审查指南） |
| 幻觉检测 Gate 汇总表 | L602-L613 | 标注"AI 辅助 + 人工"的检测项 |
| 自治等级 L3 | L253 | "AI Reviewer 自动 + 人工确认" |

**辅助定义**：`/home/song/blank/ai-coding/02-auto-coding-practices.md`
- L135：AI Reviewer 幻觉检测在各等级下的自动化级别对比
- L2611：两层审查 — AI Reviewer（幻觉检测）+ Human Reviewer（业务逻辑）

**当前人工介入点**：
1. L3 下 AI Reviewer 完成扫描后，**所有检测结果都需要人工确认**（即使 AI Reviewer 高置信度标记为"无幻觉"）
2. 注释与代码不符、逻辑错误（边界遗漏）等检测项依赖"AI 辅助 + 人工"（L611-L612）
3. 人工需要阅读 AI Reviewer 报告并判断是否通过

### 2. 替代方案详细设计

#### 2.1 核心思路：置信度分级门

```
AI Reviewer 扫描
    │
    ├── 输出: 幻觉检测报告 + 置信度评分 (0.0-1.0)
    │
    ├── confidence >= 0.85 ──▶ 自动通过（记录审计轨迹）
    │
    ├── 0.60 <= confidence < 0.85 ──▶ 标记 "需要关注" → 转人工快速审查
    │
    └── confidence < 0.60 ──▶ 标记 "高不确定" → 转人工详细审查 + 触发第二 AI Reviewer 交叉验证
```

#### 2.2 置信度评分模型

置信度由以下子维度加权计算：

| 维度 | 权重 | 评分方法 | 高分条件 |
|------|------|---------|---------|
| **编译/类型检查** | 30% | 编译器/类型检查器结果 | 全部通过 = 1.0，任何失败 = 0.0 |
| **符号解析** | 25% | AST 符号对照覆盖率 | 100% 符号已定义 = 1.0 |
| **依赖验证** | 20% | 依赖存在性 + 版本匹配 | 所有依赖已验证 = 1.0 |
| **SAST 扫描** | 15% | 静态安全分析结果 | 0 CRITICAL/HIGH = 1.0 |
| **语义一致性** | 10% | AI 二次审查（cross-check prompt） | 二次审查一致 = 1.0 |

```python
confidence_score = (
    0.30 * compile_check_score +
    0.25 * symbol_resolution_score +
    0.20 * dependency_verification_score +
    0.15 * sast_scan_score +
    0.10 * semantic_consistency_score
)
```

#### 2.3 安全守卫

- **自动通过的最低要求**：编译检查 + 符号解析 + 依赖验证 必须全部满分（任何一项失败直接阻断）
- **逃逸率监控**：持续追踪自动通过的 PR 中幻觉逃逸率，> 0% 时降低置信度阈值
- **随机抽检**：即使自动通过，每周仍随机抽取 5% 进行人工复核（验证置信度模型准确性）

#### 2.4 AI 能力需求

1. **多工具结果聚合**：整合编译器、符号解析器、依赖检查器、SAST 的结果
2. **置信度计算引擎**：加权评分模型，支持动态阈值调整
3. **交叉验证 AI Reviewer**：对低置信度代码启动第二轮独立 AI 审查
4. **阈值自适应**：根据逃逸率数据自动调整置信度阈值

### 3. 配置示例

#### 3.1 置信度门配置（`.omc/config/hallucination-confidence.yaml`）

```yaml
version: "v5.0"

# 置信度分级阈值
thresholds:
  auto_pass: 0.85          # >= 此值自动通过
  needs_review: 0.60       # >= 此值转快速审查
  deep_review: 0.00        # < 此值转详细审查 + 交叉验证

# 子维度权重和评分方法
scoring:
  dimensions:
    - name: "compile_check"
      weight: 0.30
      method: "compiler_result"

    - name: "symbol_resolution"
      weight: 0.25
      method: "ast_symbol_check"

    - name: "dependency_verification"
      weight: 0.20
      method: "dep_exists_and_version"

    - name: "sast_scan"
      weight: 0.15
      method: "static_analysis"

    - name: "semantic_consistency"
      weight: 0.10
      method: "cross_check_ai"

  # 硬性约束（任何一项不满足则无论总分如何都阻断）
  hard_requirements:
    - compile_check == 1.0
    - symbol_resolution >= 0.80
    - dependency_verification == 1.0

# 随机抽检
random_audit:
  enabled: true
  sampling_rate: 0.05   # 5% 自动通过的 PR 随机人工复核
  schedule: "weekly"

# 阈值自适应
adaptive_thresholds:
  enabled: true
  adjustment_rules:
    - condition: "hallucination_escape_rate > 0"
      action: "auto_pass_threshold += 0.05"
      max_threshold: 0.95
    - condition: "hallucination_escape_rate == 0 FOR 4 weeks"
      action: "auto_pass_threshold -= 0.02"
      min_threshold: 0.75

# 通知配置
notifications:
  on_auto_pass:
    type: "silent"
  on_needs_review:
    type: "pr-comment"
    template: "AI Reviewer 置信度 {confidence:.2f}，标记为「需要关注」，请人工审查"
  on_deep_review:
    type: "pr-comment+slack"
    template: "AI Reviewer 置信度 {confidence:.2f}（低），已启动交叉验证，请人工详细审查"
    second_reviewer: "auto"
```

#### 3.2 AI Reviewer Prompt 增强（含置信度输出格式）

```markdown
请审查以下 AI 生成的代码，检查以下 AI 特有问题：

## 审查清单
1. 幻觉检测：是否存在不存在的 API/函数调用？
2. 架构约束：是否遵循了架构约束？
3. 安全漏洞：是否存在注入、XSS、CSRF？
4. 边界条件：异常路径是否处理？
5. 注释一致性：注释是否描述实际代码行为？

## 输出格式（必须严格遵循）

```json
{
  "review_id": "review-{timestamp}",
  "pr_number": 123,
  "hallucinations_found": [
    {
      "type": "api_hallucination",
      "file": "src/auth.ts",
      "line": 42,
      "description": "调用了不存在的 `authenticateWithBiometric()`",
      "severity": "CRITICAL"
    }
  ],
  "confidence_scores": {
    "compile_check": 1.0,
    "symbol_resolution": 0.95,
    "dependency_verification": 1.0,
    "sast_scan": 1.0,
    "semantic_consistency": 0.80
  },
  "overall_confidence": 0.955,
  "recommendation": "auto_pass",
  "comments": "所有编译和符号检查通过，1个注释不一致但非关键"
}
```
```

### 4. 预期效果

| 指标 | 当前状态 | 替代后 | 改善 |
|------|---------|--------|------|
| 人工审查量 | 100% AI Reviewer 结果需人工确认 | 仅 ~15% 转人工（低置信度部分） | 节省 ~85% |
| 审查延迟 | 人工确认后合并（平均 2-4 小时） | 高置信度自动通过（< 5 分钟） | 8-48x 更快 |
| 幻觉逃逸率 | < 5%（人工确认保障） | 目标 < 5%（置信度门 + 随机抽检） | 持平或更好 |
| AI Reviewer 利用率 | 单一审查 | 低置信度触发交叉验证 | 双重保障 |

**风险评估**：
- 中风险：置信度模型可能不够准确，导致误判
- 缓解措施：随机抽检 5% 自动通过的 PR，持续校准阈值；逃逸率监控自动收紧阈值
- 硬性约束兜底：编译和符号解析不过则无论如何都阻断

### 5. 前提条件

1. **置信度评分模型**：各维度的量化评分方法需经过历史数据校准
2. **AST 符号解析工具**：支持项目主要语言的符号解析（tsc, go vet, mypy）
3. **第二 AI Reviewer**：独立运行的交叉验证 AI 实例
4. **逃逸率追踪**：自动通过的 PR 后续发现幻觉的追踪机制
5. **阈值校准数据**：至少 100+ PR 的历史审查数据用于初始阈值设定

---

## #22 审计抽样执行 — AI 全量审计

### 1. 当前位置

**主要定义**：`/home/song/blank/ai-coding/01-core-specification.md`

| 章节 | 行号 | 内容 |
|------|------|------|
| L4 自治等级定义 | L220 | "定期审计：每周人工审计随机抽样的 PR（至少 10%）" |
| L3 自治等级约束 | L220 | "审计通过率 < 95% 或出现安全事件立即降级到 L2" |

**辅助定义**：`/home/song/blank/ai-coding/04-security-governance.md`
- L82："第 4 层：人工抽检... L4：抽样 >=10%"
- L2173：审计通过率指标定义
- L2188-L2195：审计周报示例

**当前人工介入点**：
1. 每周人工从 L4 已合并的 PR 中随机抽样 >=10%
2. 人工逐 PR 审查代码质量、安全合规、架构约束
3. 人工计算审计通过率并判断是否触发降级

### 2. 替代方案详细设计

#### 2.1 架构：全量 AI 审计引擎

```
┌───────────────────────────────────────────────────────┐
│                AI Audit Engine                          │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Phase 1: 全量扫描（每个 PR 自动执行）            │  │
│  │                                                 │  │
│  │  For each merged PR in last 7 days:              │  │
│  │    ├── Code Quality Score (SonarQube/Codemetric) │  │
│  │    ├── Security Scan (SAST + Secret Scan)        │  │
│  │    ├── Architecture Constraint Check              │  │
│  │    ├── TDD Compliance Check                       │  │
│  │    ├── Spec Alignment Check                       │  │
│  │    └── Doc Drift Check                            │  │
│  └─────────────────────────────────────────────────┘  │
│                         │                               │
│                         ▼                               │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Phase 2: 风险评分与分类                          │  │
│  │                                                 │  │
│  │  Risk Score = f(quality, security, constraints)  │  │
│  │                                                 │  │
│  │  GREEN  (score >= 0.90) → 自动通过                │  │
│  │  YELLOW (0.70-0.90)    → AI 标记 + 人工快速审查   │  │
│  │  RED    (< 0.70)       → AI 标记 + 人工详细审查   │  │
│  │                                                 │  │
│  │  同时随机抽取 5% GREEN 进行人工复核                │  │
│  └─────────────────────────────────────────────────┘  │
│                         │                               │
│                         ▼                               │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Phase 3: 周报生成                                │  │
│  │                                                 │  │
│  │  自动生成 .gate/audit-report-weekly.json          │  │
│  │  含：全量审计结果、风险分布、趋势分析、降级建议    │  │
│  └─────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────┘
```

#### 2.2 AI 审计能力矩阵

| 审计维度 | AI 能力 | 检测方式 | 评分标准 |
|---------|---------|---------|---------|
| **代码质量** | SonarQube/CodeClimate 集成 | 圈复杂度、重复率、代码异味 | 100 - 异味数 * 5 |
| **安全合规** | SAST + 密钥扫描 | CRITICAL/HIGH 漏洞数 | 100 - CRIT*20 - HIGH*5 |
| **架构约束** | AI Reviewer + 规则引擎 | 违反 ADR 数量 | 100 - 违反数 * 10 |
| **TDD 合规** | CI Gate 结果分析 | 测试缺失、TDD 造假 | 100 - 违规数 * 15 |
| **Spec 对齐** | AI 语义对比 | Spec AC 与实现差异 | AI 评分 0-100 |
| **文档漂移** | doc-diff 工具 | 文档/代码不一致度 | 100 - 漂移百分比 |

#### 2.3 安全守卫

- **随机抽检保底**：自动通过的 PR 中 5% 随机人工复核
- **降级建议自动触发**：审计通过率 < 95% 时自动关联降级控制器（#20）
- **人工最终裁决权**：AI 标记为 RED 的 PR 人工审查后，可推翻 AI 判定

#### 2.4 AI 能力需求

1. **全量审计模型**：能同时执行代码质量、安全、架构、TDD、Spec、文档六维审计
2. **风险评分引擎**：多维度评分聚合，输出统一的 0-100 风险分
3. **周报自动生成**：生成结构化的审计报告，含趋势分析和降级建议
4. **Spec 语义对齐检查**：用 AI 理解 Spec AC 并与实际实现对齐

### 3. 配置示例

#### 3.1 全量审计配置（`.omc/config/audit-rules.yaml`）

```yaml
version: "v5.0"

scope:
  pr_status: "merged"
  time_window: "7d"
  exclude_labels: ["chore", "ci-only"]

dimensions:
  code_quality:
    weight: 0.20
    tool: "sonarqube"
    metrics:
      - name: "bugs"
        threshold: 0
      - name: "code_smells"
        threshold: 5
      - name: "cognitive_complexity"
        threshold: 15

  security:
    weight: 0.30
    tools: ["semgrep", "gitleaks", "trufflehog"]
    fail_on:
      - severity: "CRITICAL"
        count: 0
      - severity: "HIGH"
        count: 0

  architecture:
    weight: 0.15
    method: "ai_reviewer_adr_check"
    adr_files: "docs/adr/**/*.md"

  tdd_compliance:
    weight: 0.15
    checks:
      - "test_file_exists"
      - "red_state_recorded"
      - "no_tdd_fraud"
      - "coverage_threshold"
    min_coverage: 0.80

  spec_alignment:
    weight: 0.10
    method: "ai_semantic_compare"
    spec_dir: "specs/"

  doc_drift:
    weight: 0.10
    method: "doc_diff"
    drift_threshold: 0.20

risk_classification:
  green: { min_score: 0.90, action: "auto_pass" }
  yellow: { min_score: 0.70, action: "quick_review" }
  red: { min_score: 0.00, action: "deep_review" }

random_audit:
  green_prs_sampling_rate: 0.05

report:
  output: ".gate/audit-report-weekly.json"
  format: "json"
  include:
    - "total_prs_audited"
    - "pass_fail_counts"
    - "risk_distribution"
    - "top_issues"
    - "trend_vs_previous_week"
    - "degradation_recommendation"
```

#### 3.2 GitHub Action 自动审计（`.github/workflows/weekly-audit.yml`）

```yaml
name: Weekly AI Full Audit
on:
  schedule:
    - cron: "0 6 * * 1"

jobs:
  full-audit:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: read
      issues: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Fetch Merged PRs (Last 7 Days)
        run: |
          gh pr list --state merged --json number,title,mergedAt,headRefName \
            --jq '.[] | select(.mergedAt > "'$(date -d '7 days ago' -u +%Y-%m-%dT%H:%M:%SZ)'")"' \
            > .omc/state/merged-prs.json

      - name: Run AI Audit Engine
        run: |
          python .omc/scripts/audit-engine.py \
            --config .omc/config/audit-rules.yaml \
            --prs .omc/state/merged-prs.json \
            --output .gate/audit-report-weekly.json

      - name: Create Review Issues for Yellow/Red PRs
        if: steps.audit.outputs.issues_created > 0
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python .omc/scripts/create-review-issues.py \
            --report .gate/audit-report-weekly.json

      - name: Post Audit Summary to Slack
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_GOVERNANCE_WEBHOOK }}
        run: |
          python .omc/scripts/audit-summary-slack.py \
            --report .gate/audit-report-weekly.json \
            --webhook $SLACK_WEBHOOK

      - name: Check Degradation Threshold
        run: |
          PASS_RATE=$(jq '.audit_pass_rate' .gate/audit-report-weekly.json)
          if (( $(echo "$PASS_RATE < 0.95" | bc -l) )); then
            echo "AUDIT_PASS_RATE_LOW=true" >> $GITHUB_ENV
            echo "Audit pass rate $PASS_RATE < 95%, triggering degradation check"
          fi
```

### 4. 预期效果

| 指标 | 当前状态 | 替代后 | 改善 |
|------|---------|--------|------|
| 审计覆盖率 | 10% 抽样 | 100% 全量 | 10x 覆盖 |
| 人工审计时间 | 每周 ~1 小时（10% PR 手工审） | 每周 ~15 分钟（仅审 Yellow/Red + 5% 随机） | 节省 ~75% |
| 问题发现率 | 仅发现抽样中的问题 | 全量发现，包括抽样遗漏的 | 显著提升 |
| 审计一致性 | 依赖人工，不同人标准不同 | AI 一致评分，人类仅裁决边界 | 消除偏差 |
| 审计延迟 | 每周一次 | PR 合并后即时扫描 | 从 7 天 → 即时 |

**风险评估**：
- 中风险：AI 审计可能遗漏深层逻辑问题
- 缓解措施：5% 随机人工复核 + Red 级别强制人工详细审查
- 低风险：审计覆盖率从 10% 提升到 100%，风险净降低

### 5. 前提条件

1. **全量 AI 审计模型**：训练/配置一个能执行六维审计的 AI Agent
2. **SonarQube 或等效工具**：代码质量扫描基础设施
3. **ADR 文档可机器读取**：架构决策文档需结构化为 AI 可检查的格式
4. **Spec 文件标准化**：Spec 必须有结构化的 AC（Acceptance Criteria）供 AI 对比
5. **历史审计数据**：至少 4 周的人工审计数据用于校准 AI 审计评分

---

## #23 密钥泄露专项检测 — 持续 CI Gate 扫描

### 1. 当前位置

**主要定义**：`/home/song/blank/ai-coding/02-auto-coding-practices.md`

| 章节 | 行号 | 内容 |
|------|------|------|
| P5 — 密钥不入代码 | L2613-L2620 | pre-commit hook + SAST + CI 三重拦截 |
| 密钥扫描函数 | L1112-L1118 | `check_secrets()` 使用 gitleaks |
| pre-commit 示例 | L2806-L2814 | gitleaks pre-commit 扫描 |
| CI Gate 示例 | L2864-L2865 | `secret_scan` CI job |

**辅助定义**：`/home/song/blank/ai-coding/04-security-governance.md`
- L1380-L1383：GitHub gitleaks action 配置
- L1461：CI Gate 中 gitleaks 执行
- L2005：密钥泄露风险矩阵（pre-commit Hook + SAST | gitleaks + trufflehog）
- L2116：pre-commit gitleaks 配置

**当前问题**：
1. 规范中虽然定义了 CI Gate，但**专项检测**仍然依赖"审计期"的周期性执行（L4 模式下）
2. 现有配置偏向 pre-commit 拦截，但缺少持续的全仓库历史扫描
3. AI 生成的代码可能通过不同路径绕过 pre-commit（如直接 push 到分支再合并）
4. 缺乏密钥检测的**响应自动化**（发现后需要人工确认和修复）

### 2. 替代方案详细设计

#### 2.1 三层持续扫描架构

```
┌──────────────────────────────────────────────────────────┐
│               Continuous Secret Detection                   │
│                                                            │
│  Layer 1: pre-commit (拦截在 commit 前)                     │
│  ┌────────────────────────────────────────────────────┐   │
│  │  gitleaks pre-commit hook                         │   │
│  │  - 扫描暂存区                                      │   │
│  │  - 本地执行，< 1 秒                                │   │
│  │  - 失败 → 拒绝 commit                             │   │
│  └────────────────────────────────────────────────────┘   │
│                           │                                │
│  Layer 2: CI Gate (拦截在 merge 前)                        │
│  ┌────────────────────────────────────────────────────┐   │
│  │  gitleaks + trufflehog CI Job                     │   │
│  │  - 扫描 PR diff                                   │   │
│  │  - 扫描新增 commit 历史                            │   │
│  │  - 失败 → 阻塞 merge + 自动创建安全 issue          │   │
│  └────────────────────────────────────────────────────┘   │
│                           │                                │
│  Layer 3: Continuous Full-Scan (持续全仓库扫描)             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  trufflehog filesystem --daily                     │   │
│  │  - 扫描整个仓库历史                                 │   │
│  │  - 每日执行（夜间）                                  │   │
│  │  - 发现 → 立即阻断 + 告警 + 自动创建修复 PR          │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  Response Automation:                                      │
│  ┌────────────────────────────────────────────────────┐   │
│  │  On detection:                                     │   │
│  │  1. Block merge (Layer 1/2) or flag (Layer 3)     │   │
│  │  2. Create security issue (auto)                   │   │
│  │  3. Notify #security-alerts Slack                  │   │
│  │  4. Auto-create rotation PR (for Layer 3)          │   │
│  │  5. Trigger degradation to L1 (via #20)            │   │
│  └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

#### 2.2 允许列表管理

密钥检测需要支持"合法密钥"的 allowlist（如测试用假密钥、公开的示例 key）：

```yaml
# .gitleaks.toml - allowlist 配置
[allowlist]
description = "Global Allowlist"
paths = [
  '''test/fixtures/.*''',
  '''docs/examples/.*''',
]
regexes = [
  '''AKIAIOSFODNN7EXAMPLE''',
  '''ghp_xxxxxxxxxxxxxxxxxxxx''',
]
```

#### 2.3 安全守卫

- **双层扫描**：gitleaks（规则匹配）+ trufflehog（熵分析 + Git 历史扫描），互补覆盖
- **allowlist 审计**：allowlist 变更需要人工审批（防止通过 allowlist 绕过检测）
- **Kill Switch 联动**：检测到密钥提交时，触发 02-auto-coding-practices.md 中定义的 Kill Switch

#### 2.4 AI 能力需求

1. **gitleaks/trufflehog 集成**：CI pipeline 中配置密钥扫描 job
2. **自动响应脚本**：发现密钥后自动创建 issue、通知、触发降级
3. **Git 历史扫描**：trufflehog 全仓库历史扫描（每日 cron）
4. **密钥轮换建议**：检测到泄露后自动生成密钥轮换 PR

### 3. 配置示例

#### 3.1 pre-commit Hook（`.pre-commit-config.yaml`）

```yaml
# Secret Detection - Layer 1 (pre-commit)
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
        name: "Secret Scan (pre-commit)"
        stages: [pre-commit]
        args: ["detect", "--staged", "--no-banner", "--redact"]
        fail_fast: true
```

#### 3.2 CI Gate（`.github/workflows/secret-scan.yml`）

```yaml
name: Secret Scan Gate
on:
  pull_request:
    branches: [main, develop, "release/**"]
  push:
    branches: [main]

permissions:
  contents: read
  security-events: write
  issues: write

jobs:
  gitleaks-scan:
    name: "Layer 2: gitleaks (PR diff + new commits)"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}

  trufflehog-scan:
    name: "Layer 2: trufflehog (Git history)"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ github.event.pull_request.head.sha }}

      - name: Trufflehog scan
        uses: trufflesecurity/trufflehog@v3.50.0
        with:
          extra_args: "--since-commit HEAD~50 --only-verified --fail"

  auto-respond:
    name: "Auto-Response on Detection"
    needs: [gitleaks-scan, trufflehog-scan]
    if: failure()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Create Security Issue
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh issue create \
            --title "[SECURITY] Potential Secret Detected in PR #${{ github.event.pull_request.number }}" \
            --label "security,secret-leak,P0" \
            --body "Automated secret scan detected potential leaked secret.
            PR: #${{ github.event.pull_request.number }}
            Branch: ${{ github.head_ref }}
            Action required: 1. Verify if real secret 2. Remove and rotate if real 3. Add to allowlist if false positive"

      - name: Notify Slack
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_SECURITY_WEBHOOK }}
        run: |
          curl -X POST $SLACK_WEBHOOK \
            -H 'Content-Type: application/json' \
            -d '{
              "text": "SECRET SCAN ALERT",
              "blocks": [
                {"type": "header", "text": {"type": "plain_text", "text": "Potential Secret Leak Detected"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": "*PR:* <${{ github.event.pull_request.html_url }}|#${{ github.event.pull_request.number }}>\n*Action:* Verify, remove, and rotate if real"}}
              ]
            }'

  full-repo-scan:
    name: "Layer 3: Daily Full History Scan"
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Trufflehog full scan
        run: |
          trufflehog git https://github.com/${{ github.repository }} \
            --only-verified \
            --json \
            > trufflehog-results.json \
            || true

      - name: Process Results
        run: |
          FINDINGS=$(jq 'length' trufflehog-results.json)
          if [ "$FINDINGS" -gt 0 ]; then
            python .omc/scripts/process-full-scan-results.py \
              --results trufflehog-results.json \
              --create-issues --notify-slack
          fi
```

#### 3.3 gitleaks 规则配置（`.gitleaks.toml`）

```toml
title = "AI Coding Secret Detection Rules"

[extend]
useDefault = true

[[rules]]
id = "aws-access-key"
description = "AWS Access Key"
regex = '''AKIA[0-9A-Z]{16}'''
tags = ["key", "AWS"]

[[rules]]
id = "generic-api-key"
description = "Generic API Key"
regex = '''(?i)(api[_-]?key|apikey|access[_-]?token)\s*[:=]\s*['"]?[a-zA-Z0-9]{20,}['"]?'''
tags = ["key", "API"]

[[rules]]
id = "private-key"
description = "Private Key"
regex = '''-----BEGIN (?:RSA|EC|DSA|OPENSSH) PRIVATE KEY-----'''
tags = ["key", "crypto"]

[[rules]]
id = "ai-coding-specific"
description = "AI provider API key pattern"
regex = '''(?i)(anthropic|openai|cohere|dashscope)[_-]?(api[_-]?)?key\s*[:=]\s*['"]?[a-zA-Z0-9]{20,}['"]?'''
tags = ["key", "ai-provider"]

[allowlist]
description = "Allowed patterns"
paths = [
  '''test/fixtures/.*''',
  '''docs/examples/.*''',
  '''\.gitleaks\.toml''',
]
regexes = [
  '''AKIAIOSFODNN7EXAMPLE''',
  '''your-api-key-here''',
  '''<API_KEY>''',
]
```

### 4. 预期效果

| 指标 | 当前状态 | 替代后 | 改善 |
|------|---------|--------|------|
| 检测延迟 | 审计期周期性执行（最长 7 天） | pre-commit（即时）+ CI（分钟级）+ 全仓库扫描（24h） | 从 7 天 → < 1 分钟 |
| 覆盖范围 | 仅新提交 | 全仓库历史 + 新提交 | 100% 覆盖 |
| 人工响应时间 | 审计期发现后人工修复 | 自动创建 issue + 通知 + 触发降级 | 零人工启动延迟 |
| 密钥泄露窗口 | 最长 7 天 | 最长 1 分钟（pre-commit 拦截） | 10080x 缩短 |

**风险评估**：
- 低风险：gitleaks 和 trufflehog 是成熟工具，误报率低
- 中风险：allowlist 管理不当可能导致漏报
- 缓解措施：allowlist 变更需人工审批；trufflehog 作为第二层补充 gitleaks 规则未覆盖的密钥

### 5. 前提条件

1. **gitleaks 和 trufflehog 安装**：CI 环境中安装密钥扫描工具
2. **gitleaks.toml 配置**：项目定制的密钥检测规则 + allowlist
3. **Slack 安全告警通道**：`#security-alerts` 或等效的 webhook
4. **密钥轮换流程**：检测到泄露后自动触发密钥轮换的 SOP
5. **与降级控制器集成**：密钥泄露事件能自动触发 #20 的降级规则
6. **历史扫描基线**：首次全仓库扫描建立基线（处理遗留的假密钥）

---

## #24 文档漂移确认 — AI 自动修复简单漂移

### 1. 当前位置

**主要定义**：`/home/song/blank/ai-coding/02-auto-coding-practices.md`

| 章节 | 行号 | 内容 |
|------|------|------|
| P6 — 单一信息源 | L2622-L2629 | L3：AI 自动检测漂移，人工确认 |
| 漂移检测 | L2628 | "检查点：L3：AI 自动检测漂移，人工确认；L4：自动漂移检测（>20% 触发回归）" |
| 合规证据 | L2629 | `.gate/doc-drift-report.json` 记录漂移检测时间和内容 |

**辅助定义**：`/home/song/blank/ai-coding/04-security-governance.md`
- L128：P3 一般违规 — "文档漂移 > 20%"
- L140：P6 单一信息源 — "文档漂移检测 + 定期一致性审计"
- L1569：文档漂移 Gate — "文档/代码一致性 > 80%，标记为 Important"

**当前人工介入点**：
1. L3 下 AI 检测出文档漂身后，**人工需要确认漂移是否真实**并决定是否修复
2. 简单漂移（如版本号变更、路径变更、函数签名更新）目前也需人工确认后修复
3. 复杂漂移（如架构变更、API 语义变更）需要人工判断和修复

### 2. 替代方案详细设计

#### 2.1 漂移分类与自动修复策略

```
文档漂移检测
    │
    ├── 分析漂移类型
    │
    ├── Type A: 简单漂移（可自动修复）
    │   ├── 版本号更新（如 "v1.2.3" → "v1.2.4"）
    │   ├── 文件路径变更（如 "src/old.ts" → "src/new.ts"）
    │   ├── 函数签名更新（参数增删、返回类型变更）
    │   ├── 环境变量名变更
    │   └── 依赖版本号更新
    │   │
    │   └── Action: AI 自动修复 → 创建 PR → CI 验证 → 自动合并
    │
    ├── Type B: 中等漂移（AI 修复 + 人工审批）
    │   ├── API 端点变更（URL、方法、参数）
    │   ├── 数据结构字段增删
    │   ├── 配置项变更
    │   └── 错误码更新
    │   │
    │   └── Action: AI 自动修复 → 创建 PR → 人工审查 → 合并
    │
    └── Type C: 复杂漂移（仅人工）
        ├── 架构决策变更
        ├── 业务流程变更
        ├── 语义级描述不符
        └── 多文档一致性冲突
        │
        └── Action: AI 生成修复建议 → 人工审查 → 人工修复
```

#### 2.2 AI 自动修复机制

**Type A 自动修复流程**：

```
1. 检测漂移 → 分类为 Type A
2. AI 生成修复 patch
3. 本地验证：
   - 修复后的文档语法检查（markdownlint / yaml lint）
   - 交叉引用检查（引用路径是否仍然有效）
   - 一致性检查（修复后文档与代码的一致性评分 > 95%）
4. 创建 PR：
   - 标题：[doc-drift-auto-fix] Update {field} in {document}
   - 标签：automated, doc-fix, auto-merge
   - 描述：漂移检测结果 + 修复内容 diff
5. CI 验证通过 → 自动合并
6. 更新 .gate/doc-drift-report.json 记录自动修复
```

**安全守卫**：
- 单次 PR 仅修复一个漂移点（原子性）
- 自动修复 PR 数量限制：每天最多 5 个（防止漂移风暴）
- 自动合并仅当 CI 全通过且一致性评分 > 95%
- 超过阈值自动停止并转人工

#### 2.3 AI 能力需求

1. **文档解析引擎**：解析 Markdown、YAML、JSON 等文档格式，提取结构化信息
2. **代码-文档比对引擎**：对比代码实际行为与文档描述，识别差异
3. **自动修复生成器**：针对简单漂移类型，生成正确的文档修复 patch
4. **漂移分类器**：将检测到的漂移分为 A/B/C 三类
5. **交叉引用解析器**：确保文档内部引用路径的一致性

### 3. 配置示例

#### 3.1 文档漂移检测与修复配置（`.omc/config/doc-drift.yaml`）

```yaml
version: "v5.0"

scope:
  doc_patterns:
    - "**/*.md"
    - "**/*.yaml"
    - "**/*.json"
  code_patterns:
    - "src/**/*.ts"
    - "src/**/*.py"
    - "src/**/*.go"
  exclude:
    - "node_modules/**"
    - "vendor/**"
    - "dist/**"

drift_types:
  type_a_auto_fix:
    description: "简单漂移，AI 自动修复"
    patterns:
      - type: "version_number"
        detection: "doc mentions version X.Y.Z, code/package.json shows X'.Y'.Z'"
        fix_method: "update_version_in_doc"
      - type: "file_path"
        detection: "doc references path that no longer exists"
        fix_method: "update_path_in_doc"
      - type: "function_signature"
        detection: "doc describes function params that differ from actual"
        fix_method: "update_signature_in_doc"
      - type: "env_var_name"
        detection: "doc references env var not found in codebase"
        fix_method: "update_env_var_in_doc"
      - type: "dependency_version"
        detection: "doc mentions dependency version that differs from lockfile"
        fix_method: "update_dep_version_in_doc"

    auto_merge:
      ci_must_pass: true
      min_consistency_score: 0.95
      max_fixes_per_day: 5
      pr_labels: ["automated", "doc-fix", "auto-merge"]
      auto_merge_after: "ci-passed"

  type_b_ai_fix_human_review:
    description: "中等漂移，AI 修复 + 人工审批"
    patterns:
      - type: "api_endpoint"
        detection: "doc describes API endpoint that differs from actual routes"
      - type: "data_structure"
        detection: "doc describes data fields that differ from actual types"
      - type: "configuration"
        detection: "doc describes config items that differ from actual schema"
      - type: "error_codes"
        detection: "doc lists error codes that differ from actual definitions"

    pr_labels: ["automated", "doc-fix", "needs-review"]

  type_c_human_only:
    description: "复杂漂移，仅人工修复"
    patterns:
      - type: "architecture_change"
        detection: "doc describes architecture that differs from actual"
      - type: "business_logic"
        detection: "doc describes process that differs from actual implementation"
      - type: "semantic_mismatch"
        detection: "doc and code have fundamental semantic disagreement"
      - type: "cross_doc_conflict"
        detection: "multiple docs describe the same thing differently"

schedule:
  full_scan: "daily"
  incremental: "on-pr"

report:
  output: ".gate/doc-drift-report.json"
  include:
    - "drift_count_by_type"
    - "auto_fixed_count"
    - "pending_human_review"
    - "consistency_score"
    - "trend"

thresholds:
  consistency_warning: 0.90
  consistency_block: 0.80
  auto_fix_stop: 10
```

#### 3.2 CI 文档漂移检查（`.github/workflows/doc-drift.yml`）

```yaml
name: Document Drift Check
on:
  pull_request:
    branches: [main, develop]
    paths:
      - "src/**"
      - "docs/**"
      - "*.md"
  schedule:
    - cron: "0 3 * * *"

jobs:
  detect-drift:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run Doc Drift Detection
        run: |
          python .omc/scripts/doc-drift-detect.py \
            --config .omc/config/doc-drift.yaml \
            --output .gate/doc-drift-report.json

      - name: Auto-Fix Type A Drifts
        if: github.event_name == 'schedule'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python .omc/scripts/doc-drift-autofix.py \
            --report .gate/doc-drift-report.json \
            --type "type_a" \
            --create-prs \
            --max-prs 5

      - name: Check Consistency Threshold
        run: |
          SCORE=$(jq '.overall_consistency_score' .gate/doc-drift-report.json)
          if (( $(echo "$SCORE < 0.80" | bc -l) )); then
            gh issue create \
              --title "[P3] Document consistency below threshold: $SCORE" \
              --label "doc-drift,P3" \
              --body "Overall document consistency score: $SCORE\nThreshold: 80%"

      - name: Upload Drift Report
        uses: actions/upload-artifact@v4
        with:
          name: doc-drift-report
          path: .gate/doc-drift-report.json
```

#### 3.3 自动修复 PR 示例

```markdown
## [doc-drift-auto-fix] Update function signature in API reference

### Drift Detection
- **Document**: `docs/api-reference.md` line 42
- **Issue**: Function signature mismatch
  - Document says: `authenticate(username: string, password: string): Promise<User>`
  - Code says: `authenticate(credentials: AuthCredentials): Promise<User | AuthError>`

### Auto-Fix
Updated the function signature in the document to match the actual code.

### Consistency Check
- Pre-fix consistency: 87%
- Post-fix consistency: 96%
- Markdown syntax: valid
- Cross-references: all valid

---
*Auto-generated by AI Doc Drift Detector*
```

### 4. 预期效果

| 指标 | 当前状态 | 替代后 | 改善 |
|------|---------|--------|------|
| 人工确认量 | 100% 漂移需人工确认 | 仅 Type B/C 需人工（Type A 自动修复） | 节省 ~60% |
| 修复延迟 | 人工确认后修复（平均 1-2 天） | Type A 自动修复（< 10 分钟） | 144-288x 更快 |
| 文档一致性 | 人工确认滞后导致持续漂移 | 自动修复保持实时一致 | 从 80% → 95%+ |
| 漂移检测覆盖 | 定期扫描（每周） | 每次 PR + 每日全量 | 从每周 → 持续 |

**风险评估**：
- 低风险：Type A 自动修复模式非常确定（版本号、路径等），误修复概率极低
- 中风险：自动修复 PR 过多可能淹没人工审查队列
- 缓解措施：每天最多 5 个自动修复 PR；超过 10 个漂移时停止自动修复转人工
- 安全守卫：自动合并要求一致性评分 > 95%，CI 全通过

### 5. 前提条件

1. **文档解析工具**：能解析 Markdown/JSON/YAML 文档，提取可比对的结构化信息
2. **代码-文档比对引擎**：能将代码中的函数签名、类型定义、API 路由与文档描述对比
3. **漂移分类模型**：能准确将漂移分类为 A/B/C 三类
4. **自动修复 PR 创建能力**：Git 操作 + GitHub API 集成
5. **交叉引用解析器**：确保文档内部链接和引用的有效性
6. **漂移检测基准**：首次运行建立当前文档一致性基线

---

## 综合影响分析

### 五项替代的相互依赖关系

```
                    ┌─────────────┐
                    │   #20 降级   │
                    │   控制器     │
                    └──────┬──────┘
                           │
              接收降级事件  │
                     ┌─────┴─────┐
                     │           │
            ┌────────▼──┐  ┌────▼────────┐
            │ #23 密钥   │  │ #22 全量审计│
            │ 持续扫描   │  │ 引擎        │
            └───────────┘  └──────┬──────┘
                                  │
                           需要审计结果
                                  │
                     ┌────────────▼───────────┐
                     │                         │
              ┌──────▼──────┐          ┌──────▼──────┐
              │ #21 置信度   │          │ #24 文档    │
              │ 分级门       │          │ 漂移修复    │
              └─────────────┘          └─────────────┘
```

| 依赖关系 | 说明 |
|---------|------|
| #23 → #20 | 密钥泄露事件自动触发降级控制器 |
| #22 → #20 | 审计通过率低于阈值时自动触发降级控制器 |
| #21 → #22 | 幻觉检测置信度模型为全量审计引擎提供幻觉扫描能力 |
| #24 → #22 | 文档漂移检测作为全量审计的六个维度之一 |

### 总体预期收益

| 维度 | 当前（部分自动） | 替代后（完全自动） | 总体改善 |
|------|----------------|-------------------|---------|
| **人工时间** | ~3.5 小时/周（5 项合计） | ~0.5 小时/周（仅审批和边界审查） | **节省 ~86%** |
| **检测延迟** | 最长 7 天（审计周期） | 最长 1 小时（降级评估间隔） | **168x 更快** |
| **覆盖率** | 10-20%（抽样） | 100%（全量） | **5-10x 提升** |
| **一致性** | 依赖人工判断 | 规则 + AI 驱动 | **消除人为偏差** |

### 实施建议顺序

1. **Phase 1（基础）**：先实施 #23（密钥扫描）— 工具成熟，风险最低，立竿见影
2. **Phase 2（核心）**：实施 #20（降级控制器）— 为其他自动化提供执行框架
3. **Phase 3（质量）**：实施 #21（置信度分级）— 减少人工审查量，需要校准数据
4. **Phase 4（覆盖）**：实施 #22（全量审计）— 依赖 #21 的幻觉检测能力
5. **Phase 5（文档）**：实施 #24（文档漂移自动修复）— 工具复杂度最高，但收益稳定

---

## 附录：规范变更清单

以下文档需要更新以反映这些自动化替代：

| 文件 | 需要更新的章节 | 变更内容 |
|------|--------------|---------|
| `01-core-specification.md` | 第 2 章 2.6 节（L293-L308） | 更新降级执行方式：从"自动统计+人工执行"改为"Degradation Controller 全自动" |
| `01-core-specification.md` | 第 4 章 4.4 节（L615-L654） | 更新 AI Reviewer 流程：增加置信度分级和自动通过逻辑 |
| `01-core-specification.md` | 第 4 章 4.3.4 节（L602-L613） | 更新自动化级别列：将"AI 辅助 + 人工"改为"AI 置信度分级" |
| `01-core-specification.md` | L220（L4 审计） | 更新审计描述：从"每周人工抽样 10%"改为"AI 全量审计 + 人工仅审可疑" |
| `02-auto-coding-practices.md` | P6 单一信息源（L2622-L2629） | 更新检查点：L3 改为"AI 检测 + 自动修复简单漂移 + 人工确认复杂漂移" |
| `02-auto-coding-practices.md` | P5 密钥不入代码（L2613-L2620） | 更新检查点：强调持续 CI Gate 扫描，不再依赖"审计期专项检测" |
| `04-security-governance.md` | L82（第 4 层描述） | 更新人工抽检描述：从"L4：抽样 >=10%"改为"AI 全量审计 + 人工抽检 5%" |
| `CHANGELOG.md` | 新增条目 | 记录 v5.1 新增的自动化替代能力 |
