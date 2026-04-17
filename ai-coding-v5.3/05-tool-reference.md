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
