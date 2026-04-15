# AI Coding 规范 v5.1：人工干预 AI 替代方案

> 版本：v5.1 | 2026-04-14
> 基础：v5.0（7 份文档，13,326 行）
> 目标：**激进替代** — 在不破坏 v4 安全边界的前提下，将 24 个人工干预点转为 AI 自动化

---

## 替代原则

1. **安全边界不后退**：P4（人工审查）的"审查权"仍在人类手中，但审查的执行工作可由 AI 完成
2. **AI 执行，人类确认**：AI 完成执行动作，人类从"执行者"变为"确认者"
3. **高风险保留人工**：架构决策（DP2）、需求确认（DP1）、发布决策（DP3）、紧急变更（DP4）保留人工
4. **可回滚**：所有自动化动作必须有可回滚路径

---

## 高可行性替代（14 项）

---

### #1：代码合并操作自动化

**当前位置：**
- `01-core-specification.md` 第 2.3 节：L1 描述中"合并：人工执行 git merge"
- `01-core-specification.md` 第 2.3 节：L2 描述中"合并：人工执行，不得自动合并"
- `01-core-specification.md` 第 2.7 节："合并 | 人工执行 | 人工执行 | 人工执行 | AI 执行（trivial only）"
- `INDEX.md` 约束矩阵："自动合并 | 禁止 | 禁止 | 禁止 | 仅限 trivial fix"

**替代方案详细设计：**

将合并操作从"人工执行"改为"AI 执行，CI Gate 作为安全网"。核心逻辑：

1. AI 完成开发循环（Spec→测试→实现→自修→验证）后，AI 执行 `git merge`
2. 合并前 CI Gate 自动运行：编译检查 → 全量测试 → lint → SAST → 幻觉检测 Gate
3. 全部通过后 AI 自动合并到目标分支
4. 合并失败自动回滚 + 通知人工

```
AI 完成 PR 所有 Gate
       │
       ▼
┌─────────────────────────┐
│   自动合并引擎           │
│ 1. 检查 CI Gate 状态    │
│ 2. 检查两层审查状态     │
│ 3. 检查 DCP 状态        │
│ 4. 所有检查通过 → merge │
│ 5. 任一失败 → 不合并     │
└────────┬────────────────┘
         │
    ┌────┴────┐
    │ 通过     │ 失败
    ▼         ▼
  merge    回滚 + 告警
  通知人工   通知人工
```

**配置示例（CI + Hook）：**

```yaml
# .github/workflows/auto-merge-gate.yml
name: Auto-Merge Gate
on:
  pull_request:
    branches: [main]

jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Compile check
        run: make build
      - name: Full test suite
        run: make test-all
      - name: Lint
        run: make lint
      - name: SAST scan
        run: semgrep --config auto .
      - name: Hallucination Gate
        run: |
          # Check for unresolved symbols — fail gate if any found
          count=$(tsc --noEmit 2>&1 | grep -c "Cannot find" || true)
          if [ "$count" -gt 0 ]; then
            echo "Hallucination Gate: $count unresolved symbols found"
            exit 1
          fi
          echo "Hallucination Gate: passed"
      - name: Verify 2-layer review
        run: |
          # Check all required status checks passed (includes AI + human review)
          gh pr checks ${{ github.event.pull_request.number }} --required
          # Verify human reviewer approval via GitHub API
          reviews=$(gh api repos/${{ github.repository }}/pulls/${{ github.event.pull_request.number }}/reviews --jq '[.[] | select(.state == "APPROVED")] | length')
          if [ "$reviews" -lt 1 ]; then
            echo "Human review approval required"
            exit 1
          fi
```

```jsonc
// .claude/settings.json — L4 启用自动合并（仅限 trivial fix）
// 注意：L1-L3 禁止自动合并，与 v5.0 约束矩阵一致
{
  "permissions": {
    "autoMerge": {
      "enabled": true,
      "conditions": {
        "ciGate": "passed",
        "reviewLayers": 2,
        "dcpStatus": "approved",
        "changeType": "trivial",
        "safetyLevel": "L4"
      },
      "onFailure": "rollback_and_notify"
    }
  }
}
```

**各等级合并策略：**

| 等级 | 合并执行者 | 前置条件 |
|------|-----------|---------|
| L1 | 人工执行 | 所有 Gate 通过后，人工执行 `git merge` |
| L2 | 人工执行，AI 预检 | AI 确认所有 Gate 通过，人工点击合并 |
| L3 | 人工执行，AI 预检 + 异步通知 | AI 确认所有 Gate 通过，人工异步确认后合并 |
| L4 | AI 自动合并（仅限 trivial） | 所有 Gate 通过 + trivial change，AI 自动合并；non-trivial 变更仍需人工 |

**预期效果：**
- 人工时间节省：~5 min/PR（不再需要点击合并按钮）
- 质量影响：无降低，CI Gate 提供比人工更强的安全保障
- 风险评估：极低。合并失败可自动回滚，且两层审查仍在合并前执行

---

### #2：文档一致性维护自动化

**当前位置：**
- `01-core-specification.md` 第 2.4 节约束矩阵："P6 单一信息源 | 人工维护文档一致性 | 人工维护，AI 辅助检测过时文档 | AI 自动检测文档/代码漂移，人工确认 | 同 L3 + 自动漂移检测"

**替代方案详细设计：**

1. 每次代码提交后，AI 自动对比代码与文档的差异
2. 检测以下漂移类型：
   - API 签名变更但文档未更新
   - 环境变量变更但配置文档未更新
   - 新增/删除路由但 API 文档未更新
   - 数据库 schema 变更但文档未更新
3. AI 自动生成功能更新的文档补丁
4. 人工确认补丁（不再从零编写更新）

**配置示例（Drift Detection Hook）：**

```yaml
# .claude/hooks/drift-detection.yaml
type: PostToolUse
match:
  tool: "Write|Edit"
  pattern: "\\.go$|\\.ts$|\\.py$|\\.java$|\\.rs$"
  priority: P1

hooks:
  - command: |
      #!/bin/bash
      # docs-drift-check.sh — 检测代码/文档漂移
      CHANGED_FILE="{{file_path}}"

      # 1. 基于代码文件路径推断对应的文档目录
      #    例如: src/api/users.go → docs/api/users.md
      #    例如: pkg/auth/login.ts → docs/auth/login.md
      SRC_DIR=$(dirname "$CHANGED_FILE" | sed 's|^src/||;s|^pkg/||;s|^lib/||')
      DOC_FILE="docs/${SRC_DIR}/$(basename "$CHANGED_FILE" | sed 's/\\.[^.]*$/.md/')"

      if [ -f "$DOC_FILE" ]; then
        # 2. 根据文件类型选择对应的 API 提取器
        python3 scripts/check-api-drift.py "$CHANGED_FILE" "$DOC_FILE" --auto-fix
      fi

      # 3. 检查 README 中的示例代码是否过时
      if grep -r "example" README.md > /dev/null 2>&1; then
        python3 scripts/check-example-drift.py "$CHANGED_FILE" README.md
      fi
```

**接口：`scripts/check-api-drift.py`**（实现见独立脚本文件）

| 维度 | 说明 |
|------|------|
| 输入 | `src_file`（代码文件路径）, `doc_file`（文档文件路径）, `--auto-fix` |
| 处理 | 按语言提取 API 签名（Python: AST, Go: gofmt+regex, TS: regex），与文档中提到的 API 对比 |
| 输出 | 缺失 API 列表（代码有文档无）、过时 API 列表（文档有代码无） |
| 支持语言 | Python（AST 完整）、Go（regex 提取）、TypeScript（regex 提取）；Java/Rust 返回空（需专用解析器） |

**预期效果：**
- 人工时间节省：~10 min/Feature（从零编写更新变为确认补丁）
- 质量影响：正面。人工维护文档容易遗漏漂移，自动化检测更可靠
- 风险评估：低。AI 生成的是文档补丁，不直接影响运行时代码

---

### #3：Spec 草稿编写自动化

**当前位置：**
- `01-core-specification.md` 第 2.3 节：L1 描述中"Spec 编写：AI 生成草稿，人工审核并修改"
- `01-core-specification.md` 第 2.4 节："P7 Spec 驱动 | 人工编写 Spec | 人工审核 AI 生成的 Spec"

**替代方案详细设计：**

1. 用户输入需求描述（自然语言）
2. AI 自动生成完整 Spec 草稿，包含：
   - 用户故事（As a... I want... So that...）
   - 验收标准（Gherkin Given/When/Then）
   - 技术约束
   - 验收标准映射
3. AI 自动验证 Spec 质量：
   - AC 覆盖率检查（每个用户故事至少 1 个 AC）
   - 可测试性检查（每个 AC 可转换为测试）
   - 无歧义检查（使用模糊词检测：可能、大概、尽量）
4. 人工审核通过（而非从零编写）

**配置示例（Spec Generation Skill）：**

```yaml
# .claude/skills/spec-generator.yaml
name: spec-generator
description: Generate Feature Spec from natural language requirements
version: 1.0.0
```

```markdown
# Spec Generator

## Input
用户提供的需求描述，如："我需要用户注册功能，支持邮箱和手机号"

## Process

1. 提取关键概念：用户、注册、邮箱、手机号
2. 生成用户故事：
   - As a new user, I want to register with email so that I can create an account
   - As a new user, I want to register with phone so that I can create an account
3. 为每个用户故事生成验收标准（Gherkin）：
   ```gherkin
   Scenario: Register with valid email
     Given I am on the registration page
     When I enter a valid email and password
     And I submit the form
     Then I should receive a confirmation email
     And I should be redirected to the dashboard
   ```
4. 检查 Spec 质量：
   - 每个用户故事有 >= 2 个 AC？
   - AC 可测试？
   - 无模糊词？
5. 输出到 `specs/F{NNN}-{name}.md`

## Output Template
见 `templates/spec-template.md`
```

```yaml
# specs/quality-gate.yaml — Spec 质量 Gate
spec_quality_gate:
  min_acceptance_criteria_per_story: 2
  required_sections:
    - user_stories
    - acceptance_criteria
    - technical_constraints
    - out_of_scope
  forbidden_words:
    - "可能"
    - "大概"
    - "尽量"
    - "maybe"
    - "approximately"
  auto_detect:
    - ambiguous_requirements: true
    - missing_error_paths: true
    - missing_boundary_conditions: true
```

**预期效果：**
- 人工时间节省：~30 min/Spec → ~5 min（从零编写变为审核）
- 质量影响：正面。AI 生成的 Spec 更结构化，质量 Gate 确保无遗漏
- 风险评估：低。Spec 审核仍是人工确认，只是大幅减少了工作量

---

### #4：测试断言审核自动化

**当前位置：**
- `01-core-specification.md` 第 3.1 节："Red 阶段人工介入 | L1/L2：人工审核断言正确性"
- `01-core-specification.md` 第 3.2 节："人工审核断言 | AI 生成的断言可能错误"
- `01-core-specification.md` 第 2.4 节："P3 TDD 先行 | 人工确认 Red→Green | AI 执行，人工确认断言"

**替代方案详细设计：**

1. AI 生成测试代码后，自动运行断言验证：
   - **反向验证**：故意破坏实现代码，确认测试能捕获失败（测试真的在测试什么？）
   - **Spec 对照**：每个断言映射到 Spec 中的验收标准
   - **断言类型检查**：检测 `assert true`、`expect(true).toBe(true)` 等无意义断言
2. 自动标记"可疑断言"：
   - 断言与 Spec AC 无映射关系
   - 断言总是通过（可能是假阳性）
   - 断言过于宽松（应检查具体值但只检查了类型）
3. 人工仅审核可疑断言，而非审核所有断言

**配置示例（Assertion Verification Hook）：**

```yaml
# .claude/hooks/assertion-verify.yaml
type: PostToolUse
match:
  tool: "Write|Edit"
  pattern: "test_|_test\\.|spec\\.|\\.spec\\."
  priority: P0

hooks:
  - command: |
      #!/bin/bash
      # verify-assertions.sh — 验证 AI 生成的测试断言
      TEST_FILE="{{file_path}}"

      # 1. 运行测试，确认通过
      echo "=== Running tests ==="
      if ! make test-file FILE="$TEST_FILE"; then
        echo "FAIL: Tests do not pass"
        exit 1
      fi

      # 2. 反向验证：故意破坏实现，确认测试捕获失败
      echo "=== Reverse validation ==="
      python3 scripts/reverse-validate.py "$TEST_FILE"

      # 3. 断言质量扫描
      echo "=== Assertion quality scan ==="
      python3 scripts/scan-assertions.py "$TEST_FILE" \
        --check-empty \
        --check-spec-mapping \
        --check-strictness

      # 4. 生成审核报告
      # 仅标记可疑断言，人工审核这些
```

**接口：`scripts/reverse-validate.py`**（实现见独立脚本文件）

| 维度 | 说明 |
|------|------|
| 输入 | `test_file`（测试文件路径）, `test_cmd`（测试命令，默认 `make test`） |
| 处理 | 找到对应实现文件 → 备份 → 对每个被测试函数注入破坏（return "__MUTATED__"/panic） → 运行测试 → 如测试仍通过则标记可疑 → 恢复原始文件 |
| 输出 | 可疑断言函数列表 |
| 安全保证 | 无论测试结果如何，原始实现文件都会被恢复 |
| 支持语言 | Python、TypeScript、Go |

---

**接口：`scripts/scan-assertions.py`**（实现见独立脚本文件）
| 维度 | 说明 |
|------|------|
| 输入 | `test_file`，可选 `--check-empty`、`--check-spec-mapping`、`--check-strictness` |
| 处理 | 按可疑模式匹配断言（空断言、弱断言、类型断言等），可选映射到 Spec AC |
| 输出 | 可疑断言列表（行号、代码、原因），Spec AC 未引用警告 |
| 检测模式 | `assert True`、`toBeDefined()`、`isinstance(x, type)`、`return True` 等 6 类 |

**预期效果：**
- 人工时间节省：~15 min/Feature → ~3 min（审核所有断言变为仅审核可疑断言）
- 质量影响：正面。反向验证能捕获 AI 生成的"假阳性断言"，人工审核时更易遗漏
- 风险评估：低。反向验证自动运行，人工审核可疑项，安全保障不降低

---

### #5：测试覆盖路径补充自动化

**当前位置：**
- `01-core-specification.md` 第 3.2 节："覆盖异常路径 | AI 倾向于只生成正常路径测试 | 人工补充或 CI 检查分支覆盖率"
- `01-core-specification.md` 第 3.2 节："避免过度 Mock | AI 倾向于为一切写 Mock | 人工审查 Mock 必要性"

**替代方案详细设计：**

1. AI 生成正常路径测试后，自动触发路径补充：
   - **边界值分析**：自动生成分界点测试（0, -1, max, max+1, null, empty）
   - **异常路径生成**：基于函数分支结构和错误处理路径生成错误路径测试
   - **组合测试**：使用 Pairwise 算法生成参数组合测试
2. AI Reviewer 验证覆盖率是否达标（每包 ≥ 80%，分支覆盖率 ≥ 70%）
3. 人工不再需要手动补充异常路径测试

> 注：CFG（控制流图）级别的自动生成需要符号执行引擎（如 angr、Z3），
> 当前版本使用基于函数分支和错误处理的启发式生成。
> 如需完整 CFG 级路径覆盖，应集成专用工具如 `hypothesis`（Python）、
> `fast-check`（TS）或 `go-fuzz`（Go）。

**配置示例（Path Coverage Generator）：**

```yaml
# .claude/hooks/coverage-supplement.yaml
type: PostToolUse
match:
  tool: "Write|Edit"
  pattern: "test_|_test\\.|spec\\."
  priority: P1

hooks:
  - command: |
      #!/bin/bash
      # supplement-coverage.sh — 自动补充测试路径
      TEST_FILE="{{file_path}}"

      # 1. 检查当前覆盖率
      COVERAGE=$(make coverage-file FILE="$TEST_FILE" --json | jq '.coverage.percent')

      if (( $(echo "$COVERAGE < 80" | bc -l) )); then
        echo "[COVERAGE] Current: ${COVERAGE}%. Generating supplements..."

        # 2. 运行边界值生成
        python3 scripts/boundary-generator.py "$TEST_FILE"

        # 3. 运行异常路径生成
        python3 scripts/exception-path-generator.py "$TEST_FILE"

        # 4. 重新检查覆盖率
        NEW_COVERAGE=$(make coverage-file FILE="$TEST_FILE" --json | jq '.coverage.percent')
        echo "[COVERAGE] After supplements: ${NEW_COVERAGE}%"

        if (( $(echo "$NEW_COVERAGE < 80" | bc -l) )); then
          echo "[COVERAGE] Still below 80%. Flagging for human review."
          echo "COVERAGE_SUPPLEMENT_NEEDED=true" >> $GITHUB_ENV
        fi
      else
        echo "[COVERAGE] ${COVERAGE}% ≥ 80%. No supplements needed."
      fi
```

**接口：`scripts/boundary-generator.py`**（实现见独立脚本文件）

| 维度 | 说明 |
|------|------|
| 输入 | `test_file`, 自动推导 source_file（去除 test_ 前缀） |
| 处理 | Python AST 分析提取函数签名+类型标注 → 按类型生成边界值（int: 0/-1/1/None, str: 空/超长/None/空格, list/dict: 空/单元素/None） → 追加测试桩到测试文件 |
| 输出 | 生成的边界测试函数（含 TODO 注释待完善断言） |
| 退化行为 | 无类型标注时由 AI 分析函数分支补充边缘用例 |

**预期效果：**
- 人工时间节省：~10 min/Feature → 0 min（完全自动化）
- 质量影响：正面。AI 生成的边界测试比人工更系统、更完整
- 风险评估：低。覆盖率 Gate 确保质量，AI Reviewer 验证

---

### #6：Mock 必要性审查自动化

**当前位置：**
- `01-core-specification.md` 第 3.2 节："避免过度 Mock | AI 倾向于为一切写 Mock | 人工审查 Mock 必要性"

**替代方案详细设计：**

1. AI 生成测试代码后，自动分析 Mock 使用模式
2. 检测过度 Mock 信号：
   - Mock 数量 > 被测试函数的依赖数（不必要的 Mock）
   - Mock 了标准库或不可变依赖
   - Mock 了纯函数（不需要隔离）
   - 所有测试都使用相同的 Mock 配置（可能应该用集成测试）
3. 提供替代方案：
   - "这个 Mock 可以用真实实现替代"
   - "这个 Mock 可以用 Test Double 替代"
   - "建议使用集成测试替代 Mock"

**配置示例：**

**接口：`scripts/mock-analyzer.py`**（实现见独立脚本文件）

| 维度 | 说明 |
|------|------|
| 输入 | `test_file` |
| 处理 | AST 分析检测 Mock 调用（Python ast.NodeVisitor），过度 Mock 检测（mock 数 > 测试数 × 2），标准库/常用库 Mock 警告（os/requests/socket 等 16 个库） |
| 输出 | Mock 数量统计、过度 Mock 警告、不应 Mock 的库告警 |
| 阈值规则 | mock_count > func_count × 2 触发警告 |

**预期效果：**
- 人工时间节省：~5 min/Feature → 0 min
- 质量影响：正面。自动化检测比人工审查更系统
- 风险评估：极低。仅标记可疑项，不阻止任何操作

---

### #7：Prompt 版本记录自动化（扩展到 L1）

**当前位置：**
- `01-core-specification.md` 第 2.4 节："P9 Prompt 版本化 | 人工记录 Prompt 版本 | AI 自动记录到 PR 描述"
- `01-core-specification.md` 第 2.3 节：L1 描述中未明确自动化

**替代方案详细设计：**

1. 将 L2+ 的自动 Prompt 持久化扩展到 L1
2. 每次 AI 生成代码时，自动记录：
   - 使用的 Prompt 内容和版本
   - 使用的模型和参数
   - 生成的代码文件
3. 自动写入 `prompts/` 目录和 PR 描述

**配置示例：**

```jsonc
// .claude/settings.json
{
  "promptVersioning": {
    "enabled": true,
    "autoPersist": true,
    "directory": "prompts/",
    "versionFormat": "{name}-v{major}.{minor}.md",
    "recordInPrDescription": true,
    "includeFields": [
      "prompt_content",
      "model",
      "temperature",
      "max_tokens",
      "timestamp",
      "generated_files"
    ]
  }
}
```

**预期效果：**
- 人工时间节省：~3 min/Feature → 0 min
- 质量影响：正面。自动化记录比人工更准确、更完整
- 风险评估：极低。纯记录操作，不影响代码质量

---

### #8：PR 描述填写自动化

**当前位置：**
- `01-core-specification.md` 第 2.3 节：L3 描述中"PR 创建：AI 自动创建 PR，填入完整的 Spec/Prompt/Model 追溯信息"
- 隐含：L1/L2 中 PR 描述需要人工填写

**替代方案详细设计：**

1. AI 完成开发循环后，自动生成 PR 描述，包含：
   - Spec 文件链接和内容摘要
   - 使用的 Prompt 版本
   - 模型和参数
   - 测试结果摘要
   - 覆盖率数据
   - Self-Correction 记录
   - 变更文件列表
2. 人工确认描述（而非从零编写）

**配置示例：**

```yaml
# .github/workflows/auto-pr-description.yml
name: Auto PR Description
on:
  pull_request:
    types: [opened]

jobs:
  generate-description:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate PR description
        run: |
          # Extract spec info — find the most recently modified spec file
          SPEC_FILE=$(find specs/ -name "*.md" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | awk '{print $2}' | xargs basename)
          if [ -z "$SPEC_FILE" ]; then
            SPEC_FILE="no spec linked"
          fi
          PROMPT_VERSION=$(cat .claude/prompt-version 2>/dev/null || echo "unknown")
          COVERAGE=$(cat .gate/coverage.json 2>/dev/null | jq '.percent' || echo "N/A")

          # Generate description
          cat <<EOF > /tmp/pr-desc.md
          ## Spec
          - **Spec**: \`${SPEC_FILE}\`
          - **验收标准**: $(grep -c "Scenario:" specs/$SPEC_FILE) scenarios

          ## AI Generation
          - **Prompt**: \`${PROMPT_VERSION}\`
          - **Model**: $(cat .claude/model-info 2>/dev/null)
          - **Self-Correction**: $(cat .claude/self-correction-log 2>/dev/null | wc -l) rounds

          ## Quality Gates
          - **Coverage**: ${COVERAGE}%
          - **Tests**: $(make test-count --silent)
          - **Lint**: $(make lint --silent)
          EOF

          # Update PR description
          gh pr edit ${{ github.event.pull_request.number }} --body-file /tmp/pr-desc.md
```

**预期效果：**
- 人工时间节省：~5 min/PR → 0 min
- 质量影响：正面。自动化描述更完整、更一致
- 风险评估：极低

---

### #9：Lint 修复审核自动化

**当前位置：**
- `02-auto-coding-practices.md` 第 4 章 Self-Correction Loop 中 lint 修复
- 隐含：lint 修复结果需要人工确认

**替代方案详细设计：**

1. AI 检测到 lint 错误后，自动修复
2. 自动重新运行 lint，确认修复通过
3. 如果修复通过 → 自动提交，不通知人工
4. 如果修复失败或引入了新问题 → 通知人工

**配置示例：**

```yaml
# .claude/hooks/lint-auto-fix.yaml
type: PostToolUse
match:
  tool: "Bash"
  pattern: "lint|make lint"
  priority: P2

hooks:
  - command: |
      #!/bin/bash
      # lint-auto-fix.sh — 自动修复 lint 错误
      COMMAND="{{tool_input}}"
      EXIT_CODE="{{tool_exit_code}}"

      # 仅在 lint 失败时尝试自动修复
      if [ "$EXIT_CODE" -eq 0 ]; then
        echo "[LINT] No errors to fix"
        exit 0
      fi

      # 1. 记录修复前的 lint 输出用于对比
      make lint 2>&1 > /tmp/lint-before.txt || true

      # 2. 检测项目类型并应用自动修复
      #    注意：不同 linter 的 auto-fix 能力不同
      if [ -f "go.mod" ] && command -v golangci-lint > /dev/null; then
        # Go: golangci-lint 本身无 --fix，需用 gci + gofumpt 单独修复
        echo "[LINT] Go project: applying gofumpt and gci"
        command -v gofumpt > /dev/null && gofumpt -w . 2>/dev/null || true
        command -v gci > /dev/null && gci write . 2>/dev/null || true
      elif [ -f "package.json" ] && command -v eslint > /dev/null; then
        npx eslint --fix . 2>/dev/null || true
      elif command -v ruff > /dev/null; then
        ruff check --fix . 2>/dev/null || true
      fi

      # 3. 重新运行 lint，确认修复通过
      if make lint 2>/dev/null; then
        echo "[LINT] Auto-fix successful"
      else
        echo "[LINT] Auto-fix failed or introduced new issues"
        make lint 2>&1 > /tmp/lint-after.txt || true
        # 对比修复前后的差异，便于人工审查
        diff /tmp/lint-before.txt /tmp/lint-after.txt > /tmp/lint-diff.txt 2>&1 || true
        echo "LINT_FIX_FAILED=true" >> $GITHUB_ENV
      fi
```

**预期效果：**
- 人工时间节省：~3 min/PR → 0 min
- 质量影响：正面。自动化修复比人工更快速、更一致
- 风险评估：低。lint 修复不影响运行时行为

---

### #10：商业目标拆解自动化

**当前位置：**
- `01-core-specification.md` 第 2.4 节："P1 商业驱动 | 人工定义每个商业目标 | 人工定义，AI 辅助拆解"
- `01-core-specification.md` 第 1 章：P1 商业驱动原则

**替代方案详细设计：**

1. 用户输入商业目标（如"提升用户注册转化率 30%"）
2. AI 自动拆解为可执行的 Spec 队列：
   - 注册页面优化
   - 社交登录集成
   - 注册流程简化
   - 邮件验证优化
3. 每个 Spec 自动估算影响力和工作量
4. 人工审核优先级排序

**配置示例：**

```yaml
# scripts/goal-decomposer.yaml — 示例配置数据（非可执行 Hook）
# 展示 Goal Decomposer 的输入输出结构
goal_decomposition:
  input: "提升用户注册转化率 30%"
  output_format: "specs/"
  analysis:
    - metric: "当前注册转化率"
      source: "analytics dashboard"
    - baseline: "查看近 30 天数据"
    - decomposition:
        - spec: "F001-注册页面优化"
          impact: "高"
          effort: "中"
          description: "优化注册页面 UI/UX，减少跳出率"
        - spec: "F002-社交登录集成"
          impact: "高"
          effort: "高"
          description: "集成 Google/GitHub 登录，降低注册门槛"
        - spec: "F003-注册流程简化"
          impact: "中"
          effort: "中"
          description: "减少注册步骤，从 5 步减少到 3 步"
  priority_suggestion:
    - "F001（高影响，中工作量）→ 优先"
    - "F002（高影响，高工作量）→ 第二阶段"
    - "F003（中影响，中工作量）→ 第三阶段"
```

**预期效果：**
- 人工时间节省：~20 min/Feature → ~5 min
- 质量影响：中性。AI 拆解可能不完整，人工审核弥补
- 风险评估：低。人工审核优先级，不自动执行

---

### #11：自修循环每轮确认自动化

**当前位置：**
- `01-core-specification.md` 第 2.3 节：L1 描述中"自修循环：AI 修复 lint/test 错误，人工确认修复结果"
- `01-core-specification.md` 第 2.4 节："自修复限制 | 最多 3 轮，人工确认每轮 | 最多 3 轮，自动执行"

**替代方案详细设计：**

1. L1 的自修循环每轮确认改为自动化
2. AI 修复后，自动运行 lint/test 验证
3. 验证通过 → 自动进入下一轮（或完成）
4. 验证失败 → 自动进入下一轮（最多 3 轮）
5. 3 轮全部失败 → 通知人工

**配置示例：**

```yaml
# .claude/hooks/self-correction-auto-verify.yaml
type: PostToolUse
match:
  tool: "Bash"
  pattern: "^(make\\s+)?(lint|test|pytest|jest|go\\s+test)"
  priority: P0

hooks:
  - command: |
      #!/bin/bash
      # auto-verify-fix.sh — 自动验证自修结果
      COMMAND="{{tool_input}}"
      EXIT_CODE="{{tool_exit_code}}"

      # 初始化计数器（首次运行时从文件读取或初始化为 0）
      ROUND_FILE=".gate/self-correction-round"
      if [ -f "$ROUND_FILE" ]; then
        SELF_CORRECTION_ROUND=$(cat "$ROUND_FILE")
      else
        SELF_CORRECTION_ROUND=0
      fi

      if [ "$EXIT_CODE" -eq 0 ]; then
        echo "[AUTO-VERIFY] Fix passed: $COMMAND"
        # 重置计数器（修复成功）
        echo "0" > "$ROUND_FILE"
      else
        echo "[AUTO-VERIFY] Fix failed: $COMMAND (exit code: $EXIT_CODE)"
        SELF_CORRECTION_ROUND=$((SELF_CORRECTION_ROUND + 1))
        echo "$SELF_CORRECTION_ROUND" > "$ROUND_FILE"
        echo "SELF_CORRECTION_ROUND=$SELF_CORRECTION_ROUND" >> $GITHUB_ENV

        if [ "$SELF_CORRECTION_ROUND" -ge 3 ]; then
          echo "[AUTO-VERIFY] 3 rounds exhausted. Escalating to human."
          echo "SELF_CORRECTION_EXHAUSTED=true" >> $GITHUB_ENV
        fi
      fi
```

**预期效果：**
- 人工时间节省：~10 min/Feature → ~1 min
- 质量影响：无降低。自动化验证比人工更可靠
- 风险评估：极低。CI Gate 作为额外安全保障

---

### #12：数据级别判断自动化（扩展到 L1）

**当前位置：**
- `01-core-specification.md` 第 2.4 节："P10 数据分级 | 人工判断数据级别 | pre-send 自动扫描"

**替代方案详细设计：**

1. 将 L2+ 的 pre-send 自动扫描扩展到 L1
2. 每次数据发送到 AI 前，自动扫描：
   - 密钥/Token 检测
   - PII 检测
   - 机密数据标记
3. 自动拦截或脱敏

**配置示例：**

```yaml
# .claude/hooks/pre-send-scan.yaml
type: PreToolUse
match:
  tool: "WebFetch|Agent"
  priority: P0

hooks:
  - command: |
      #!/bin/bash
      # pre-send-scan.sh — 发送 AI 前扫描数据
      INPUT="{{tool_input}}"

      # 1. 密钥检测 — 使用结构化检测而非简单 grep
      #    推荐：使用 gitleaks detect --stdin 或 trufflehog filesystem
      if echo "$INPUT" | grep -iE "(api_key|apikey|secret_key|access_token|private_key)\s*[:=]\s*['\"][A-Za-z0-9]+['\"]"; then
        echo "[PRE-SEND] WARNING: Possible secret detected"
        python3 scripts/redact-secrets.py "$INPUT"
      fi

      # 2. PII 检测 — 使用真实格式匹配
      if echo "$INPUT" | grep -E "([0-9]{3}-[0-9]{2}-[0-9]{4}|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\b\d{11}\b)"; then
        echo "[PRE-SEND] WARNING: Possible PII detected"
        python3 scripts/redact-pii.py "$INPUT"
      fi

      # 3. 机密数据检测
      if echo "$INPUT" | grep -iE "(confidential|proprietary|internal only)"; then
        echo "[PRE-SEND] BLOCKED: Confidential data detected"
        exit 1
      fi
```

**预期效果：**
- 人工时间节省：~3 min/请求 → 0 min
- 质量影响：正面。自动化扫描比人工判断更可靠
- 风险评估：极低。安全增强操作

---

### #13：批量 PR 审查排序自动化

**当前位置：**
- `01-core-specification.md` 第 2.3 节：L3 描述中"合并：人工审查 PR 后合并（可以批量审查多个 PR）"
- `02-auto-coding-practices.md` 第 7 章夜间开发模式："09:00 早晨审查"

**替代方案详细设计：**

1. 早晨审查前，AI 自动按风险等级排序 PR
2. 风险评分算法：
   - 变更行数（越多风险越高）
   - 变更文件类型（核心文件风险高）
   - 自修轮数（3 轮通过的风险高）
   - 测试覆盖率变化（覆盖率下降风险高）
   - 幻觉检测标记
3. 人工优先审查高风险 PR

**配置示例：**

**接口：`scripts/pr-risk-scorer.py`**（实现见独立脚本文件）
| 维度 | 说明 |
|------|------|
| 输入 | PR 列表（JSON 格式，含 additions/deletions/changed_files/self_correction_rounds/coverage_delta/hallucination_flag） |
| 处理 | 加权评分：变更行数 >500 (+30)/>100 (+15)，核心文件 (+20)，自修轮数 (×15)，覆盖率下降 (+25)，幻觉标记 (+50) |
| 输出 | 按风险分数降序排列的 PR 列表 |
| 核心文件 | auth/, config/, db/, api/ |

**预期效果：**
- 人工时间节省：~10 min/早晨 → ~3 min
- 质量影响：正面。优先审查高风险 PR 提高问题发现率
- 风险评估：极低

---

### #14：异步 Decision Point 通知自动化

**当前位置：**
- `01-core-specification.md` 第 2.3 节：L3 描述中"决策点：DP1/DP2 通过异步消息通知人工确认"
- `01-core-specification.md` 第 2.4 节："Decision Point | DP1-DP2 异步确认，DP3-DP4 人工同步"

**替代方案详细设计：**

1. AI 自动检测 Decision Point 条件
2. 自动填充确认上下文（需求分析结果、架构方案对比）
3. 发送通知到人工（Slack/邮件/消息）
4. 人工一键确认（而非逐项检查）

**配置示例：**

```yaml
# .claude/hooks/decision-point-notify.yaml
type: PostToolUse
match:
  tool: "Write"
  pattern: "specs/.*\\.md"
  priority: P1

hooks:
  - command: |
      #!/bin/bash
      # dp-notify.sh — Decision Point 通知
      SPEC_FILE="{{file_path}}"

      # 检测 DP1：需求理解
      if grep -q "## 需求分析" "$SPEC_FILE"; then
        python3 scripts/dp-notify.py \
          --type "DP1" \
          --title "需求理解确认" \
          --context "$(python3 scripts/dp-context.py dp1 $SPEC_FILE 2>/dev/null || echo 'Context unavailable')" \
          --channel "night-dev-reviews"
      fi

      # 检测 DP2：架构方案
      if grep -q "## 架构方案" "$SPEC_FILE"; then
        python3 scripts/dp-notify.py \
          --type "DP2" \
          --title "架构方案确认" \
          --context "$(python3 scripts/dp-context.py dp2 $SPEC_FILE 2>/dev/null || echo 'Context unavailable')" \
          --channel "night-dev-reviews"
      fi
```

**预期效果：**
- 人工时间节省：~5 min/DP → ~1 min
- 质量影响：中性。通知自动化不影响决策质量
- 风险评估：极低

---

## 中等可行性替代（10 项）

---

### #15：Code Review - 业务逻辑审查自动化

**当前位置：**
- `01-core-specification.md` 第 2.3 节：L2 描述中"Human Reviewer 专注于业务逻辑和架构约束"
- `04-security-governance.md` 第 1 章：6 层防御架构，第 4 层"人工抽检"

**替代方案详细设计：**

1. 增强 AI Reviewer，注入业务规则上下文
2. 业务规则结构化表达：
   - 业务规则文件：`rules/business-rules.yaml`
   - 规则类型：权限、状态机、数据约束、计算逻辑
3. AI Reviewer 对照业务规则检查代码
4. 标记可疑项：
   - 违反业务规则
   - 缺少业务规则覆盖
   - 边界条件处理不当
5. 人工仅审查 AI 标记的可疑项

**配置示例：**

```yaml
# rules/business-rules.yaml
business_rules:
  - id: "BR-001"
    name: "用户注册必须验证邮箱或手机号"
    type: "validation"
    check:
      - type: "code_pattern"
        description: "registration endpoint must call email verification or phone verification"
        grep: "verify_email|verify_phone|send_verification"

  - id: "BR-002"
    name: "订单金额不能为负"
    type: "constraint"
    check:
      - type: "code_pattern"
        description: "order.amount >= 0"
        grep: "amount.*<.*0|amount.*>=.*0"

  - id: "BR-003"
    name: "用户状态机：pending → active → suspended → deleted"
    type: "state_machine"
    valid_transitions:
      - ["pending", "active"]
      - ["active", "suspended"]
      - ["suspended", "active"]
      - ["active", "deleted"]
    invalid_transitions:
      - ["pending", "deleted"]
      - ["suspended", "deleted"]
    check:
      - type: "state_transition_scan"
        description: "scan for invalid state transitions in code"

  - id: "BR-004"
    name: "管理员权限不能直接分配"
    type: "permission"
    check:
      - type: "code_pattern"
        description: "no direct role update to admin without approval"
        grep: "role.*=.*admin|role.*admin.*update"
```

```yaml
# .github/workflows/ai-reviewer-business-rules.yml
name: AI Reviewer - Business Rules
on:
  pull_request:
    branches: [main]

jobs:
  business-rules-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Load business rules
        run: |
          # AI Reviewer loads business rules and checks code against them
          claude --agent business-rules-reviewer \
            --context "$(cat rules/business-rules.yaml)" \
            --prompt "Review the changes in this PR against the business rules. Flag any violations or suspicious patterns."
      - name: Generate report
        run: |
          # Output structured review report
          cat <<EOF > business-rules-report.json
          {
            "violations": [...],
            "suspicious": [...],
            "passed": true/false
          }
          EOF
```

**前提条件：**
- 业务规则可结构化表达（yaml/json 格式）
- AI Reviewer 能够理解业务规则上下文
- 规则覆盖率达到 80%+

**预期效果：**
- 人工时间节省：~15 min/PR → ~5 min（审查所有业务逻辑变为仅审查可疑项）
- 质量影响：正面。结构化业务规则比人工记忆更可靠
- 风险评估：中。需要业务规则结构化，初期投入较大

---

### #16：Code Review - 架构约束审查自动化

**当前位置：**
- `01-core-specification.md` 第 2.3 节：L2 描述中"Human Reviewer 专注于业务逻辑和架构约束"
- `01-core-specification.md` 第 21 章（v4）：架构设计 DNA

**替代方案详细设计：**

1. 定义架构约束规则：
   - 循环依赖检测
   - 分层违规检测（如表现层直接访问数据层）
   - 模块大小检测（单模块 ≤ 200 行）
   - 依赖方向检测
2. AI 自动检查架构约束
3. 标记违规项，人工审查是否真的违规

**配置示例：**

```yaml
# rules/architecture-rules.yaml
architecture_rules:
  - id: "AR-001"
    name: "无循环依赖"
    type: "circular_dependency"
    severity: "error"
    check: "madge --circular src/"

  - id: "AR-002"
    name: "分层约束：表现层不得直接访问数据层"
    type: "layer_violation"
    severity: "error"
    layers:
      presentation: ["controllers/", "views/"]
      business: ["services/", "usecases/"]
      data: ["repositories/", "models/"]
    allowed:
      - presentation -> business
      - business -> data
    forbidden:
      - presentation -> data

  - id: "AR-003"
    name: "模块大小限制：单文件 ≤ 200 行"
    type: "file_size"
    severity: "warning"
    max_lines: 200
    exclude: ["test/", "vendor/"]

  - id: "AR-004"
    name: "公共 API 稳定性：已发布的接口不得破坏性变更"
    type: "api_breaking_change"
    severity: "error"
    check: "api-extractor run --local"
```

```yaml
# .github/workflows/architecture-review.yml
name: Architecture Review
on:
  pull_request:
    branches: [main]

jobs:
  architecture-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check circular dependencies
        run: npx madge --circular src/ || exit 1
      - name: Check layer violations
        run: python3 scripts/check-layer-violations.py rules/architecture-rules.yaml
      - name: Check file sizes
        run: find src/ -name "*.go" -o -name "*.ts" | xargs wc -l | sort -rn | head -20
      - name: AI Architecture Reviewer
        run: |
          claude --agent architecture-reviewer \
            --context "$(cat rules/architecture-rules.yaml)" \
            --prompt "Review the changes in this PR against the architecture rules. Flag any violations."
```

**前提条件：**
- 架构规则可配置化（yaml 格式）
- 依赖分析工具可用（madge、depcheck 等）
- 模块大小规则与团队共识一致

**预期效果：**
- 人工时间节省：~10 min/PR → ~3 min
- 质量影响：正面。自动化检测比人工更系统
- 风险评估：低。架构规则明确后可完全自动化

---

### #17：Spec 审核自动化

**当前位置：**
- `01-core-specification.md` 第 2.4 节："P7 Spec 驱动 | 人工审核 AI 生成的 Spec"
- `01-core-specification.md` 第 2.3 节：L2 描述中"Spec 编写：AI 生成，人工审核"

**替代方案详细设计：**

1. AI 生成 Spec 后，自动运行质量评估：
   - **完整性检查**：所有必填字段存在
   - **AC 覆盖率**：每个用户故事有 >= 2 个验收标准
   - **可测试性**：每个 AC 包含 Given/When/Then，可转换为测试
   - **无歧义**：无模糊词
   - **边界覆盖**：包含异常路径
2. 评分系统：
   - 90-100 分：自动通过，人工确认
   - 70-89 分：标记为"中等质量"，人工审核
   - < 70 分：标记为"低质量"，人工重点审核
3. 人工仅审核低/中等质量 Spec，高质量 Spec 快速确认

**配置示例：**

**接口：`scripts/spec-quality.py`**（实现见独立脚本文件）

| 维度 | 说明 |
|------|------|
| 输入 | `spec_file`（Markdown 格式） |
| 处理 | 解析 Markdown 结构，5 维度评分：完整性（必填章节）、AC 覆盖率（每故事 ≥2 AC）、歧义检测（模糊词）、边界覆盖（异常路径 AC）、可测试性（Given/When/Then） |
| 输出 | 总分（100 起扣）+ 等级（HIGH ≥90 / MEDIUM ≥70 / LOW <70）+ 问题列表 + action 建议（auto_pass / human_review） |
| 必填章节 | title, user_stories, acceptance_criteria, technical_constraints, out_of_scope |

**前提条件：**
- Spec 质量评估模型成熟
- 评分系统经人工验证有效
- 团队对评分标准达成共识

**预期效果：**
- 人工时间节省：~10 min/Spec → ~3 min（审核所有 Spec 变为仅审核低质量 Spec）
- 质量影响：正面。自动化评估更系统，评分系统发现人工容易遗漏的问题
- 风险评估：低。人工确认仍在

---

### #18：DCP 门禁自动化

**当前位置：**
- `01-core-specification.md` 第 2.4 节："P2 DCP 门禁 | 人工执行，同步确认 | 人工执行，同步确认 | 人工执行，可异步确认 | 自动化检查清单"
- `01-core-specification.md` 第 1 章：P2 DCP 原则

**替代方案详细设计：**

1. L1-L3 的 DCP 改为自动化检查清单 + AI 生成报告
2. DCP 指标自动采集：
   - 上一阶段完成状态
   - 测试覆盖率
   - 缺陷数量
   - 风险项
3. AI 生成 DCP 报告，包含：
   - Go/No-Go/Re-work 建议
   - 风险项列表
   - 缓解措施
4. 人工确认建议（而非逐项检查）

**配置示例：**

```yaml
# .gate/dcp-checklist.yaml
dcp_gate:
  phase: 3  # entering Phase 3
  auto_checks:
    - id: "DCP-001"
      name: "Phase 2 completion"
      check: "grep -q 'status: done' .gate/phase-2-status.yaml"
      severity: "block"

    - id: "DCP-002"
      name: "Test coverage >= 80%"
      check: "jq '.coverage.percent >= 80' .gate/coverage.json"
      severity: "block"

    - id: "DCP-003"
      name: "No critical bugs open"
      check: "gh issue list --label 'bug,critical' --json count | jq '.count == 0'"
      severity: "block"

    - id: "DCP-004"
      name: "Security scan passed"
      check: "semgrep --config auto . --exit-code 0"
      severity: "block"

    - id: "DCP-005"
      name: "Specs ready"
      check: "find specs/ -name '*.md' -exec grep -l 'status: ready' {} \; | wc -l"
      severity: "warn"

  ai_report:
    enabled: true
    template: "templates/dcp-report.md"
    output: ".gate/dcp-report.md"
```

```markdown
# templates/dcp-report.md — DCP 报告模板

# DCP Report: Phase {{phase}} Gate

## Auto Check Results
{{auto_checks}}

## AI Assessment
{{ai_assessment}}

## Risk Items
{{risk_items}}

## Recommendation
{{recommendation}}  <!-- Go / No-Go / Re-work -->
```

**前提条件：**
- DCP 指标可自动化采集
- AI 能够生成有意义的 DCP 评估
- 团队对 DCP 标准有共识

**预期效果：**
- 人工时间节省：~15 min/DCP → ~3 min
- 质量影响：正面。自动化采集比人工更完整、更准确
- 风险评估：低。人工确认仍在

---

### #19：升级审批自动化

**当前位置：**
- `01-core-specification.md` 第 2.5 节：所有升级条件中"技术负责人批准"、"架构师批准"
- `01-core-specification.md` 第 2.5 节：L3→L4"技术负责人 + 架构师 + 产品负责人三方批准"

**替代方案详细设计：**

1. AI 自动收集升级条件证据：
   - PR 无事故数量：`gh pr list` + 过滤
   - TDD 执行率：CI 统计数据
   - 自主成功率：PR 一次通过率
   - 幻觉发生率：AI Reviewer 统计
   - Self-Correction 成功率：自修日志统计
2. AI 生成升级建议报告
3. 人工确认（而非人工收集证据）

**配置示例：**

```yaml
# .gate/upgrade-checker.yaml
upgrade_checker:
  l1_to_l2:
    checks:
      - metric: "pr_no_incidents"
        threshold: 20
        query: "gh pr list --state merged --json number,labels | jq '[.[] | select(.labels | map(.name) | index(\"incident\") | not)] | length'"
      - metric: "tdd_execution_rate"
        threshold: 0.80
        query: "jq '.tdd.rate' .gate/metrics.json"
      - metric: "prompt_first_pass_rate"
        threshold: 0.50
        query: "jq '.prompt.first_pass_rate' .gate/metrics.json"
      - metric: "two_layer_review"
        threshold: true
        query: "test -f .gate/two-layer-review-enabled"

  l2_to_l3:
    checks:
      - metric: "l2_stable_months"
        threshold: 1
        query: "python3 -c \"from datetime import date; d=date.fromisoformat('$(jq -r '.l2.start_date' .gate/metrics.json)'); print((date.today()-d).days>=30)\""
      - metric: "autonomy_success_rate"
        threshold: 0.70
        query: "jq '.autonomy.success_rate' .gate/metrics.json"
      - metric: "hallucination_rate"
        threshold: 0.05
        query: "jq '.hallucination.rate' .gate/metrics.json"
      - metric: "self_correction_success_rate"
        threshold: 0.60
        query: "jq '.self_correction.success_rate' .gate/metrics.json"
```

**接口：`scripts/upgrade-advisor.py`**（实现见独立脚本文件）

| 维度 | 说明 |
|------|------|
| 输入 | 升级检查配置（JSON，含 query/threshold），目标等级 |
| 处理 | 执行每个检查的 shell 查询，对比阈值，生成通过/失败判定 |
| 输出 | 升级报告（目标等级、全部通过状态、详情、APPROVE/REVIEW_NEEDED 建议） |

**前提条件：**
- 升级指标可自动化追踪
- CI 统计系统完整运行一段时间
- 团队对升级标准有共识

**预期效果：**
- 人工时间节省：~30 min/升级（收集证据 + 审核）→ ~5 min（仅确认报告）
- 质量影响：正面。自动化证据比人工收集更完整
- 风险评估：低。最终审批权仍在人

---

### #20：降级判定自动化

**当前位置：**
- `01-core-specification.md` 第 2.6 节：降级条件表中部分自动、部分人工
- `01-core-specification.md` 第 2.6 节："降级是自动的，不需要审批"（但部分降级触发需要人工判定）

**替代方案详细设计：**

1. 所有降级触发条件改为 AI 实时监控
2. AI 自动执行降级动作：
   - 更新 `.gate/autonomy-level` 文件
   - 更新 CI Gate 配置
   - 发送通知到人工
3. 人工收到通知后可确认（但降级已经执行）

**配置示例：**

```yaml
# .gate/monitor.yaml
degradation_monitor:
  check_interval: "5m"
  triggers:
    - id: "D-001"
      name: "Production incident from AI code"
      check: "gh issue list --label 'production-incident,ai-generated' | jq '.count > 0'"
      action: "degrade_to_L2"
      severity: "P1"

    - id: "D-002"
      name: "Hallucinated code merged undetected"
      check: "grep -q 'hallucination_detected' .gate/review-log.json"
      action: "degrade_to_L2"
      severity: "P1"

    - id: "D-003"
      name: "Audit pass rate < 95% for 2 weeks (L4)"
      check: "jq '.audit.pass_rate_2weeks < 0.95' .gate/metrics.json"
      action: "degrade_to_L3"
      severity: "P2"

    - id: "D-004"
      name: "Autonomy success rate < 70% for 2 weeks (L3)"
      check: "jq '.autonomy.success_rate_2weeks < 0.70' .gate/metrics.json"
      action: "degrade_to_L2"
      severity: "P2"

    - id: "D-005"
      name: "TDD execution rate < 80%"
      check: "jq '.tdd.rate < 0.80' .gate/metrics.json"
      action: "degrade_to_L1"
      severity: "P1"

    - id: "D-006"
      name: "Secret leaked to repo"
      check: |
        gitleaks detect --report-format json --report-path /tmp/gitleaks.json 2>/dev/null || true
        jq 'length > 0' /tmp/gitleaks.json 2>/dev/null || echo "false"
      action: "degrade_to_L1"
      severity: "P1"

    - id: "D-007"
      name: "Self-correction fails 5 consecutive times"
      check: "jq '.self_correction.consecutive_failures >= 5' .gate/metrics.json"
      action: "degrade_to_L2"
      severity: "P2"

  actions:
    degrade_to_L2:
      - |
        printf 'L2\nhuman_review_required\n' > .gate/autonomy-level
      - "python3 scripts/notify-degradation.py L2"
    degrade_to_L3:
      - "echo 'L3' > .gate/autonomy-level"
      - "python3 scripts/notify-degradation.py L3"
    degrade_to_L1:
      - |
        printf 'L1\nfull_human_review\n' > .gate/autonomy-level
      - "python3 scripts/notify-degradation.py L1"
```

**前提条件：**
- 降级指标可实时监控
- 监控系统稳定运行
- 降级动作可回滚

**预期效果：**
- 人工时间节省：~10 min/降级事件 → 0 min（完全自动化）
- 质量影响：正面。自动化降级更快，减少风险窗口
- 风险评估：极低。降级是安全保护操作，自动化更安全

---

### #21：幻觉检测结果置信度分级

**当前位置：**
- `01-core-specification.md` 第 4 章：幻觉检测
- `01-core-specification.md` 第 2.3 节：L3 描述中"幻觉检测 Gate 必须自动通过 CI 执行"
- `01-core-specification.md` 第 2.4 节："幻觉检测 | AI Reviewer 自动 + 人工确认 | AI Reviewer 自动 + 定期审计抽检"

**替代方案详细设计：**

1. AI Reviewer 对每个幻觉检测结果标记置信度（0-100）
2. 分级处理：
   - 高置信度（80-100）：自动通过/拦截，无需人工确认
   - 中置信度（50-79）：标记为"需确认"，人工审核
   - 低置信度（0-49）：必须人工审核
3. 置信度评分维度：
   - 符号解析成功率
   - 依赖验证结果
   - API 存在性验证
   - 编译检查结果

**配置示例：**

**接口：`scripts/hallucination-confidence-scorer.py`**（实现见独立脚本文件）

| 维度 | 说明 |
|------|------|
| 输入 | 检测结果 JSON（hallucination, compiles, unresolved_symbols, dependencies_verified, api_exists, semantic_consistent） |
| 处理 | 加权评分：compiles 25 + symbols_resolved 25（每未解析符号扣 5 分）+ dependencies_verified 20 + api_exists 15 + semantic_consistent 15 |
| 输出 | confidence 分数（0-100）+ action 分类：auto_pass（≥80 无幻觉）、auto_block（≥80 有幻觉）、human_review（50-79）、human_review_required（0-49） |
| 评分公式 | `score = Σ(通过维度权重) - min(未解析符号×5, symbols_resolved权重)` |

**前提条件：**
- 幻觉检测置信度评分模型成熟
- 评分标准经人工验证有效
- 高置信度自动拦截的错误率 < 1%

**预期效果：**
- 人工时间节省：~5 min/PR → ~2 min（确认所有结果变为仅确认中低置信度结果）
- 质量影响：正面。置信度分级让 AI 更高效地处理高置信度结果
- 风险评估：中。需要验证置信度评分的准确性

---

### #22：审计全量替代抽样

**当前位置：**
- `01-core-specification.md` 第 2.3 节：L4 描述中"每周人工审计随机抽样的 PR（至少 10%）"
- `04-security-governance.md` 第 6 章：合规审计

**替代方案详细设计：**

1. AI 自动全量审计所有 PR（100%，而非 10% 抽样）
2. 审计维度：
   - 代码质量（lint、复杂度、重复代码）
   - 安全性（SAST、密钥检测、依赖漏洞）
   - 规范合规（TDD、Spec 驱动、Prompt 版本化）
   - 幻觉检测
3. 人工仅审查：
   - AI 标记的"可疑 PR"
   - 随机抽检（5%，确保 AI 审计质量）

**配置示例：**

```yaml
# .gate/full-audit.yaml
full_audit:
  schedule: "weekly"
  scope: "all_merged_prs"
  checks:
    - id: "AU-001"
      name: "Code quality"
      tool: "sonarqube"
      threshold: "quality_gate == passed"

    - id: "AU-002"
      name: "Security scan"
      tool: "semgrep"
      threshold: "no_critical_findings"

    - id: "AU-003"
      name: "TDD compliance"
      tool: "git-log"
      threshold: "test_commit_before_impl_commit"
      # 注意：squash merge 会破坏 commit 时间戳，需配合 --no-ff merge 或
      # 使用 git log --all --diff-filter=A -- <test_file> 判断文件创建时间

    - id: "AU-004"
      name: "Spec compliance"
      tool: "spec-verifier"
      threshold: "all_acceptance_criteria_met"

    - id: "AU-005"
      name: "Prompt versioning"
      tool: "prompt-tracker"
      threshold: "prompt_version_recorded"

    - id: "AU-006"
      name: "Hallucination detection"
      tool: "ai-reviewer"
      threshold: "no_unresolved_hallucinations"

  human_review:
    - "all_prs_flagged_as_suspicious"
    - "random_sample_5_percent"
```

**前提条件：**
- 全量 AI 审计模型成熟
- 审计工具集成完整
- AI 审计的准确率 > 95%

**预期效果：**
- 人工时间节省：~60 min/周（审计 10% PR）→ ~15 min/周（审查可疑 + 5% 随机抽检）
- 质量影响：正面。全量审计比抽样审计更完整
- 风险评估：低。随机抽检确保 AI 审计质量

---

### #23：密钥泄露持续检测

**当前位置：**
- `01-core-specification.md` 第 2.4 节："P5 密钥不入代码 | 同 L3 + 审计期专项密钥检测"
- `04-security-governance.md`：密钥安全管理

**替代方案详细设计：**

1. CI 中集成持续密钥扫描（trufflehog/gitleaks）
2. 每次提交自动扫描，发现即阻断
3. 不再需要等待"审计期专项检测"
4. 扫描范围：代码、配置文件、提交历史、PR 描述

**配置示例：**

```yaml
# .github/workflows/secret-scan.yml
name: Secret Scan
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  secret-detection:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for secret scanning
      - name: Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: TruffleHog
        uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --only-verified

  block-on-secret:
    needs: secret-detection
    if: failure()
    runs-on: ubuntu-latest
    steps:
      - name: Block merge
        run: |
          echo "## Secret Detected" >> $GITHUB_STEP_SUMMARY
          echo "Secret detected in code. Please remove and rotate." >> $GITHUB_STEP_SUMMARY
          exit 1
```

**前提条件：**
- CI 密钥扫描集成
- 密钥扫描规则库完整
- 误报率 < 5%

**预期效果：**
- 人工时间节省：~30 min/审计期 → 0 min（持续自动化）
- 质量影响：正面。持续检测比周期性检测更安全
- 风险评估：极低。安全增强操作

---

### #24：文档漂移自动修复

**当前位置：**
- `01-core-specification.md` 第 2.4 节："P6 单一信息源 | AI 自动检测文档/代码漂移，人工确认 | 同 L3 + 自动漂移检测（>20% 触发回归）"

**替代方案详细设计：**

1. AI 检测到文档漂移后，自动分类：
   - **简单漂移**：版本号变更、路径变更、函数签名变更 → AI 自动修复，CI 格式验证后直接提交
   - **中等漂移**：API 行为变更、配置格式变更 → AI 生成修复补丁，人工确认后提交
   - **复杂漂移**：架构变更、业务流程变更 → 人工修复
2. 自动修复的文档变更必须经过 CI 验证（链接检查、格式检查、API 签名一致性检查）
3. 简单漂移自动修复与 #2 的关系：
   - #2 侧重"检测 + 生成补丁 + 人工确认"（通用流程）
   - #24 在 #2 基础上增加"简单漂移免确认"（L4 专属优化）
   - L1-L3 中简单漂移仍需人工确认，L4 中可免确认

**配置示例：**

```yaml
# .claude/hooks/drift-auto-fix.yaml
type: PostToolUse
match:
  tool: "Write|Edit"
  pattern: "\\.go$|\\.ts$|\\.py$"
  priority: P1

hooks:
  - command: |
      #!/bin/bash
      # drift-auto-fix.sh — 自动修复文档漂移
      # 注意：L1-L3 所有修复均需人工确认；L4 中简单漂移可免确认
      CHANGED_FILE="{{file_path}}"
      AUTONOMY_LEVEL=$(cat .gate/autonomy-level 2>/dev/null || echo "L1")

      # 1. 检测文档漂移（复用 #2 的 check-api-drift.py）
      python3 scripts/check-api-drift.py "$CHANGED_FILE" docs/ 2>/dev/null || true

      # 2. 分类漂移并应用对应修复策略
      python3 scripts/classify-drift.py "$CHANGED_FILE" --categories simple,medium,complex

      # 3. L4 自动修复简单漂移，L1-L3 仅生成补丁
      if [ "$AUTONOMY_LEVEL" = "L4" ]; then
        python3 scripts/classify-drift.py "$CHANGED_FILE" --type simple --apply
      else
        python3 scripts/classify-drift.py "$CHANGED_FILE" --type simple --generate-patch
      fi

      # 4. 中等漂移：始终生成补丁，人工确认
      python3 scripts/classify-drift.py "$CHANGED_FILE" --type medium --generate-patch

      # 5. 复杂漂移：报告人工修复
      python3 scripts/classify-drift.py "$CHANGED_FILE" --type complex --report
```

**前提条件：**
- 文档自动修复能力成熟
- 简单漂移检测准确率高（> 95%）
- 修复后的文档通过验证

**预期效果：**
- 人工时间节省：~5 min/漂移 → ~1 min（仅确认中等和复杂漂移）
- 质量影响：正面。自动化修复比人工更快速、更一致
- 风险评估：低。CI 验证确保修复质量

---

## 总结

### 替代效果总览

| 类型 | 数量 | 当前人工时间/Feature | 替代后人工时间/Feature | 节省比例 |
|------|------|-------------------|---------------------|---------|
| 高可行性 | 14 | ~110 min | ~20 min | **82% 减少** |
| 中等可行性 | 10 | ~80 min | ~25 min | **69% 减少** |
| 保留人工 | 8 | ~50 min | ~50 min | 0% |
| **替代项合计** | 24 | ~190 min | ~45 min | **76% 总减少** |
| **总计（含保留人工）** | 32 | ~240 min | ~95 min | **60% 总减少** |

### 保留人工的 8 个干预点

| # | 干预点 | 理由 |
|---|--------|------|
| 25 | P4 最终合并放行（L1-L3） | v4 安全边界的最后防线 |
| 26 | 架构方案决策（DP2） | 架构决策影响深远，AI 缺乏全局上下文 |
| 27 | 需求理解确认（DP1） | 需求误解是最高风险的错误来源 |
| 28 | 生产发布决策（DP3） | 发布决策涉及商业风险 |
| 29 | 紧急变更方向（DP4） | 紧急场景更需要人类判断 |
| 30 | 升级最终审批 | 升级是不可逆的信任跃迁 |
| 31 | 生产安全事故响应 | 安全事故需要人类判断影响范围 |
| 32 | 业务逻辑正确性最终判断 | AI 无法理解"用户真正需要什么" |

### 实施建议

1. **Phase 1（立即执行）**：实施高可行性替代 #1-#14，无需改变安全边界
2. **Phase 2（1-2 个月）**：实施中等可行性替代 #15-#24，需要完善前置条件
3. **Phase 3（持续）**：保留人工的 8 个干预点不替代，定期评估是否有新的自动化机会

---

## 附录 A：脚本实现状态清单

> 本文档中引用的脚本分为两类：
> - **[DONE]** 已有完整实现逻辑，可直接用于实施
> - **[STUB]** 核心框架已定义，需按注释中的 TODO 补充实现逻辑

| 脚本文件 | 所属项目 | 状态 | 说明 |
|----------|---------|------|------|
| `scripts/check-api-drift.py` | #2, #24 | **DONE** | 支持 Python/Go/TS，Java/Rust 待扩展 |
| `scripts/reverse-validate.py` | #4 | **DONE** | 完整实现：备份→注入→测试→恢复 |
| `scripts/scan-assertions.py` | #4 | **DONE** | 含空断言检测、Spec AC 映射、严格度检查 |
| `scripts/boundary-generator.py` | #5 | **DONE** | Python AST 解析生成边界测试 |
| `scripts/exception-path-generator.py` | #5 | **STUB** | 需用 Hypothesis/fast-check 实现 |
| `scripts/mock-analyzer.py` | #6 | **DONE** | Python AST Mock 分析 |
| `scripts/pr-risk-scorer.py` | #13 | **DONE** | 完整风险评分实现 |
| `scripts/spec-quality.py` | #17 | **DONE** | Markdown 格式 Spec 质量评估 |
| `scripts/hallucination-confidence-scorer.py` | #21 | **DONE** | 完整置信度评分 |
| `scripts/upgrade-advisor.py` | #19 | **DONE** | 完整证据收集+报告生成 |
| `scripts/check-layer-violations.py` | #16 | **STUB** | 需按语言实现 import 方向分析 |
| `scripts/classify-drift.py` | #24 | **STUB** | 需实现简单/中等/复杂漂移分类逻辑 |
| `scripts/dp-notify.py` | #14 | **STUB** | 需实现 Slack/邮件通知发送 |
| `scripts/dp-context.py` | #14 | **STUB** | 需实现 DP 上下文提取 |
| `scripts/redact-secrets.py` | #12 | **STUB** | 需用正则+结构化检测脱敏 |
| `scripts/redact-pii.py` | #12 | **STUB** | 需用正则匹配+掩码脱敏 |
| `scripts/notify-degradation.py` | #20 | **STUB** | 需实现降级通知发送 |
| `scripts/check-example-drift.py` | #2 | **STUB** | 需实现示例代码一致性检查 |

> 注：[STUB] 脚本在 Phase 1 中不需要实现，其对应的替代项在 Phase 2 才执行。

---

## 附录 B：v5.0 合规性说明

| v5.0 原则 | 本文档变更 | 合规性 |
|-----------|-----------|--------|
| P1 商业驱动 | #10 AI 辅助拆解，人工审核优先级 | ✅ 人类最终判断权保留 |
| P2 DCP 门禁 | #18 AI 采集指标+生成报告，人工确认 | ✅ 人类确认保留 |
| P3 TDD 先行 | #4, #5 AI 辅助断言验证和覆盖补充 | ✅ TDD Red→Green 不变 |
| P4 人工审查 | #1 自动合并仅限 L4 trivial；#13, #15, #16, #22 辅助审查 | ✅ 审查权在人类手中 |
| P5 密钥不入代码 | #12, #23 增强检测，不改变密钥管理方式 | ✅ 安全增强 |
| P6 单一信息源 | #2, #24 自动化文档漂移检测和修复 | ✅ 一致性增强 |
| P7 Spec 驱动 | #3, #17 AI 生成+质量评估，人工审核 | ✅ 人类审核保留 |
| P8 最小批量 | 无变更 | ✅ |
| P9 Prompt 版本化 | #7 自动化记录 | ✅ 增强追溯能力 |
| P10 数据分级 | #12 扩展到 L1 自动扫描 | ✅ 安全增强 |
