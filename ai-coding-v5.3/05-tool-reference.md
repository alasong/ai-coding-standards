# AI Coding 规范 v5.3：工具参考

> 版本：v5.3 | 2026-04-17
> 定位：CLI 命令、Settings、Hooks、Skills、配置模板

---

## 第 1 章：CLI 快速参考

| 命令 | 说明 |
|------|------|
| `claude -p "prompt"` | 执行单次 Prompt |
| `claude -p --max-turns 100 --permission-mode auto` | Auto-Coding 模式 |
| `/schedule create --cron "..." --prompt "..."` | 创建定时任务 |
| `/loop 30m "prompt"` | 会话内轮询 |
| `TeamCreate(...)` | 创建 Agent 团队 |
| `TaskCreate(subject="...", description="...")` | 创建任务 |
| `TaskUpdate(taskId="...", status="completed")` | 更新任务 |

---

## 第 2 章：配置模板

### 2.1 .aicoding.yaml

```yaml
gate:
  verify_gate:
    enabled: true
    steps:
      - compile: "go build ./..."
      - test: "go test ./... -cover"
      - lint: "golangci-lint run"
    coverage_threshold: 80
    fail_action: self-correct

  self_correction:
    max_rounds: 3
    fail_action: escalate_to_human

  tdd_gate:
    check_commit_order: true
    verify_red_phase: true

requirement_to_spec_chain:
  phases:
    - name: requirement_analysis
      decision_point: DP0
    - name: architecture_adaptation
      decision_point: DP0.5
    - name: solution_design
      decision_point: DP0.7
      quality_gate: solution-quality-gate
    - name: spec_generation
      decision_point: DP1
  max_retries_per_phase: 3
  fail_action: escalate_to_human
```

### 2.2 pre-commit hook

```bash
#!/bin/sh
echo "Running secret scan..."
if command -v gitleaks &>/dev/null; then
  if ! gitleaks detect --source . --no-banner --redact --staged; then
    echo "COMMIT BLOCKED: Secret detected"
    exit 1
  fi
fi
echo "Pre-commit checks passed"
exit 0
```

---

## 第 3 章：P23 相关模板

### 3.1 方案设计模板

见 `templates/solution-design.md`。

### 3.2 领域知识目录

```
domain-knowledge/
├── industry/
│   ├── fintech.md
│   ├── healthcare.md
│   └── e-commerce.md
├── tech-stack/
│   ├── go-gin.md
│   ├── python-fastapi.md
│   └── react-typescript.md
└── project-specific/
    ├── architecture-decisions.md
    ├── naming-conventions.md
    └── historical-lessons.md
```

### 3.3 Solution Quality Gate 脚本

见 `scripts/solution-quality-gate.sh`。

### 3.4 `.gate/design-output.json` 格式

方案设计通过 Solution Quality Gate 后，AI 必须生成设计输出证据文件：

```json
{
  "type": "design-output",
  "deliverable_type": "solution-design",
  "design_file": "docs/solutions/{feature-id}-design.md",
  "checklist": {
    "需求覆盖": true,
    "架构一致性": true,
    "接口完整性": true,
    "数据模型正确": true,
    "异常处理": true,
    "可测试性": true,
    "依赖明确": true,
    "风险评估": true
  },
  "ai_claims": [
    "与现有架构无冲突",
    "不违反任何 ADR"
  ],
  "evidence": [
    {
      "claim": "与现有架构无冲突",
      "sources": ["docs/architecture.md#L50", "ADR-003"]
    }
  ],
  "reviewed_by": "@reviewer",
  "status": "approved"
}
```

### 3.5 `.aicoding.yaml` 完整链配置

带 prompt_file、model、input/output 声明的完整 Requirement→Spec 链配置：

```yaml
requirement_to_spec_chain:
  phases:
    - name: requirement_analysis
      decision_point: DP0
      prompt_file: prompts/requirement-analysis-v1.md
      model: high
      input:
        - user_raw_requirement
        - domain-knowledge/industry/{domain}.md
      output:
        - structured_requirement.md
      gate:
        - human_review: DP0

    - name: architecture_adaptation
      decision_point: DP0.5
      prompt_file: prompts/architecture-adaptation-v1.md
      model: high
      input:
        - structured_requirement.md
        - docs/architecture.md
      output:
        - architecture-adaptation-analysis.md
      gate:
        - human_review: DP0.5

    - name: solution_design
      decision_point: DP0.7
      prompt_file: prompts/solution-design-v1.md
      model: medium
      input:
        - architecture-adaptation-analysis.md
        - templates/solution-design.md
      output:
        - docs/solutions/{feature-id}-design.md
      gate:
        - quality_gate: solution-quality-gate
        - human_review: DP0.7

    - name: spec_generation
      decision_point: DP1
      prompt_file: prompts/spec-generation-v1.md
      model: medium
      input:
        - docs/solutions/{feature-id}-design.md
        - templates/spec-template.md
      output:
        - specs/{feature-id}-spec.md
      gate:
        - spec_validation: spec-validate.py
        - human_review: DP1

  max_retries_per_phase: 3
  fail_action: escalate_to_human
```
