# Automation Replacements Analysis — Items #6 through #11

> Generated: 2026-04-14 | Scope: v5.0 Spec Manual Intervention Points | Source Docs: `01-core-specification.md`, `02-auto-coding-practices.md`, `03-multi-agent-multi-surface.md`, `04-security-governance.md`

---

## #6 — Mock 必要性审查 (Automated Mock Overuse Detection)

### 6.1 当前位置

- **Primary**: `01-core-specification.md` Section 3.2, line 376:
  > "避免过度 Mock — AI 倾向于为一切写 Mock | 人工审查 Mock 必要性"
- **Supporting**: `02-auto-coding-practices.md` Section 4.5.1 (line 1536): "简单的测试失败 | 是（最多 3 轮） | Mock 配置错误、路径错误"
- **Level mapping**: `01-core-specification.md` Section 2.4 (line 254): L1 人工确认每轮自修循环

当前机制：AI 生成测试代码后，由人工 reviewer 在 Code Review 阶段判断 Mock 是否过度使用（例如：Mock 了本可以用真实实现的简单依赖，或 Mock 层数过深导致测试失去意义）。

### 6.2 替代方案详细设计

**机制名称**: Mock Audit Hook (MAH)

**架构**:

```
测试代码生成 → Mock 分析器 (AST + Heuristic) → 评分报告 → 自动修复建议 → CI Gate
```

**三层检测策略**:

1. **AST 静态分析层**（Lint 级）: 解析测试文件，提取所有 `mock.*`、`patch`、`Mock()` 调用，构建 Mock 依赖图
   - 检测：直接依赖被 Mock 的比例、Mock 嵌套深度、纯函数被 Mock 的情况
   - 输出：`mock-audit.json` 包含每个测试文件的 Mock 密度评分

2. **AI 语义分析层**（Reviewer 级）: 当 AST 层发现疑似过度 Mock 时，调用 AI Reviewer 进行上下文分析
   - 分析：Mock 是否替代了本可注入的真实实现？测试是否因为 Mock 而失去了验收价值？
   - 输出：替代方案建议（如 "此处可使用 memory db 替代 mock database"）

3. **自动修复层**（Self-Correct 级）: 对确认为过度 Mock 的测试，尝试生成替代实现
   - 策略：用 in-memory 实现、测试替身（test double）、或简化 fixture 替换 Mock
   - 安全：修复后必须重新运行测试，验证行为不变

**AI 能力需求**:
- AST 解析器（语言特定：Python `ast`、Go `go/parser`、TypeScript `ts-morph`）
- AI Reviewer 技能：理解测试语义、识别可测试边界、推荐替代方案
- Self-Correct：自动替换 Mock 为轻量替代实现

**安全护栏**:
- Mock 审计为 **建议性**（Warning），不阻塞合并（避免误杀合理的 Mock）
- 超过 3 个过度 Mock 标记时升级为 Error 阻塞
- AI Reviewer 给出的替代方案必须通过测试才能自动应用

### 6.3 配置示例

**CI Workflow** (`.github/workflows/mock-audit.yml`):

```yaml
name: Mock Audit
on: [pull_request]

jobs:
  mock-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Mock Static Analysis
        run: |
          python scripts/mock_audit.py \
            --src tests/ \
            --threshold 0.4 \
            --output .gate/mock-audit.json

      - name: AI Review on Findings
        if: steps.audit.outputs.findings > 0
        run: |
          claude -p --max-turns 20 \
            "Review the mock audit findings in .gate/mock-audit.json.
            For each flagged test, determine if the mock is truly excessive
            or justified by the test context. For excessive mocks, suggest
            concrete alternatives (in-memory impl, test fixture, etc.).
            If an alternative exists and passes tests, apply it.

            Rules:
            - Mock is justified if: external service, non-deterministic, slow (>100ms)
            - Mock is excessive if: pure function, in-memory replaceable, simple struct
            - Never modify test assertions
            - Always run tests after changes"

      - name: Fail if >3 Excessive Mocks
        run: |
          excessive=$(jq '[.findings[] | select(.severity=="excessive")] | length' .gate/mock-audit.json)
          if [ "$excessive" -gt 3 ]; then
            echo "::error::Found $excessive excessive mocks. Review required."
            exit 1
          fi

      - name: Upload Mock Audit Report
        uses: actions/upload-artifact@v4
        with:
          name: mock-audit-report
          path: .gate/mock-audit.json
```

**Mock Audit Script** (`scripts/mock_audit.py`) 核心逻辑:

```python
def analyze_mock_density(test_file):
    """返回 Mock 密度评分 (0-1)，越高表示 Mock 越密集"""
    mocks = extract_mock_calls(test_file)
    total_deps = count_testable_dependencies(test_file)
    if total_deps == 0:
        return 0
    density = len(mocks) / total_deps

    findings = []
    for mock in mocks:
        if mock.target_type in ("pure_function", "value_object", "simple_struct"):
            findings.append({
                "file": test_file,
                "line": mock.line,
                "target": mock.target,
                "reason": f"Mocking {mock.target_type} is likely excessive",
                "severity": "excessive",
                "alternative": f"Use in-memory {mock.target_type} or real implementation"
            })
        elif mock.nesting_depth > 2:
            findings.append({
                "file": test_file,
                "line": mock.line,
                "target": mock.target,
                "reason": f"Mock nesting depth {mock.nesting_depth} > 2",
                "severity": "warning",
                "alternative": "Flatten test fixture or use integration test"
            })
    return density, findings
```

**Gate 规则** (`.gate/gate-config.yaml`):

```yaml
mock_audit:
  enabled: true
  thresholds:
    mock_density_warning: 0.3    # 超过 30% 依赖被 Mock → Warning
    mock_density_error: 0.6      # 超过 60% 依赖被 Mock → Error
    max_nesting_depth: 2          # Mock 嵌套超过 2 层 → Warning
    max_excessive_per_pr: 3       # 超过 3 个过度 Mock → Block
  allowed_exceptions:
    - "external_api"              # 外部 API 调用允许 Mock
    - "payment_gateway"           # 支付网关允许 Mock
    - "third_party_sdk"           # 第三方 SDK 允许 Mock
    - "non_deterministic"         # 非确定性操作允许 Mock
```

### 6.4 预期效果

| 指标 | 当前 (人工) | 自动化后 |
|------|-----------|---------|
| 单 PR 审查时间 | 5-10 min (Mock 专项) | 0 min (自动分析) |
| 误杀率 | 低 (人工判断准确) | ~5% (AI Reviewer 可能有误判) |
| 覆盖度 | 抽样审查 (大项目只能抽 20%) | 100% 全量 |
| 反馈速度 | Code Review 时才知道 | 提交后 30s 内 |
| 质量影响 | 取决于 reviewer 经验 | 标准化检测，一致性高 |

**风险评估**:
- **低 Mock 质量下降**: AI Reviewer 可能将合理的 Mock 标记为过度。缓解：配置 allowed_exceptions 白名单，标记为 Warning 而非 Error
- **性能开销**: AST 分析极快，AI Reviewer 仅在发现疑似问题时调用，额外耗时 <30s
- **误修复**: 自动替换 Mock 后测试通过但语义改变。缓解：修复后强制运行全量测试套件

---

## #7 — Prompt 版本记录 (Automated Prompt Versioning & Persistence)

### 7.1 当前位置

- **Primary**: `01-core-specification.md` Section 2.4 (line 251):
  > "P9 Prompt 版本化 | L1: 人工记录 Prompt 版本 | L2: AI 自动记录到 PR 描述 | L3: AI 自动持久化到 prompts/ 目录 | L4: 同 L3 + 自动回归测试"
- **Detailed**: `01-core-specification.md` Section 6.1 (lines 998-1058): Prompt 版本化原则、文件结构、PR 追溯
- **Auto-coding**: `02-auto-coding-practices.md` Section 2.3 (lines 2649-2656): Prompt 版本化在 Auto-Coding 下的含义
- **Multi-agent**: `03-multi-agent-multi-surface.md` line 187: "Sub-Agent 的 prompt 在文件中定义，受版本控制"

当前机制（L1）：开发者手动记录每次使用的 Prompt 版本（版本号、模型、参数）到 PR 描述或单独的记录文件。容易遗漏、容易出错、无法审计。

### 7.2 替代方案详细设计

**机制名称**: Prompt Auto-Persist Hook (PAPH)

**架构**:

```
AI 生成代码 → Post-Hook 拦截 → 提取 Prompt → 计算 Hash → 版本递增 → 保存到 prompts/ → 关联 PR → 生成追溯记录
```

**自动化流程**:

1. **Prompt 捕获**: 每次 AI 调用（通过 MCP 或 Claude Code harness）后，post-hook 自动捕获实际使用的 Prompt 内容、模型、参数
2. **去重检查**: 对 Prompt 内容计算 SHA-256 hash，检查是否与已有版本相同
3. **版本递增**: 若内容变更，自动递增 minor version；若结构变更（新增 input_context 等），递增 major version
4. **持久化**: 保存到 `prompts/{id}-{name}-v{version}.md`，包含 YAML frontmatter
5. **PR 关联**: 在 PR 描述中自动添加/更新 Prompt 版本声明区块
6. **追溯链**: 写入 `.gate/prompt-chain-trace.json` 记录完整的 Prompt 使用链

**动态 Prompt 处理**: 对于 L3/L4 下由 Spec 解析动态构建的 Prompt（非静态文件），同样执行持久化：
- 动态 Prompt 在使用前写入 `prompts/dynamic/{spec-id}-{timestamp}.md`
- 自动关联到原始 Spec 文件
- 版本号使用 `D-{seq}` 前缀标识为动态生成

**AI 能力需求**:
- Prompt 模板解析与 diff 能力（判断版本号递增幅度）
- YAML frontmatter 自动生成
- PR 描述自动编辑（GitHub API / GitLab API）

**安全护栏**:
- Prompt 必须来自本地仓库，禁止外部 URL 加载（`01-core-specification.md` line 1173）
- 敏感信息（密钥、token）不得出现在 Prompt 中，pre-send 扫描拦截
- 版本号递增遵循 semver 规则，防止版本冲突

### 7.3 配置示例

**Claude Code Hook** (`settings.json`):

```json
{
  "hooks": {
    "afterPrompt": {
      "command": "node .omc/hooks/prompt-persist.js",
      "env": {
        "PROMPT_DIR": "prompts/",
        "TRACE_FILE": ".gate/prompt-chain-trace.json",
        "AUTO_VERSION": "true"
      }
    }
  }
}
```

**Prompt Persist Hook** (`.omc/hooks/prompt-persist.js`):

```javascript
const fs = require('fs');
const crypto = require('crypto');
const path = require('path');

module.exports = async function promptPersist(context) {
  const { prompt, model, params, sessionId, featureId } = context;

  // 1. 计算 Prompt hash
  const hash = crypto.createHash('sha256').update(prompt).digest('hex').slice(0, 12);

  // 2. 检查是否已有相同 hash 的版本
  const existing = findPromptByHash(hash);
  if (existing) {
    // 已存在，复用版本号
    return { promptId: existing.id, version: existing.version, reused: true };
  }

  // 3. 查找该 feature 的最新版本号
  const latest = findLatestPromptVersion(featureId);
  const newVersion = incrementVersion(latest.version, prompt, latest.content);

  // 4. 生成 Prompt 文件
  const promptFile = generatePromptFile({
    id: `P${String(featureId).padStart(3, '0')}`,
    name: deriveName(prompt),
    version: newVersion,
    model,
    params,
    hash,
    content: prompt,
    featureId,
    sessionId,
  });

  // 5. 保存到 prompts/ 目录
  const filePath = path.join('prompts', promptFile.filename);
  fs.writeFileSync(filePath, promptFile.content);

  // 6. 更新追溯链
  appendToTrace({
    timestamp: new Date().toISOString(),
    promptId: promptFile.id,
    version: newVersion,
    file: filePath,
    hash,
    model,
    featureId,
    sessionId,
  });

  return { promptId: promptFile.id, version: newVersion, reused: false };
};
```

**PR Description Template** (自动生成的 PR 描述区块):

```markdown
## Prompt Trace

| Item | Value |
|------|-------|
| **Feature** | F001 - 用户注册 |
| **Spec** | `specs/F001-user-registration.md` |
| **Prompts Used** | `prompts/P001-user-reg-test.md` v1.2, `prompts/P002-user-reg-impl.md` v1.1 |
| **Model** | qwen3.5-plus |
| **Temperature** | 0.0 |
| **Prompt Hash** | `a3f8c2d1e5b7` |
| **Generated At** | 2026-04-14T10:30:00Z |
| **Gate Result** | All gates passed |
```

**Prompt Chain Trace** (`.gate/prompt-chain-trace.json`):

```json
{
  "feature": "F001",
  "pr": 123,
  "prompt_chain": [
    {
      "phase": "test-generation",
      "prompt_id": "P001",
      "version": "1.2",
      "file": "prompts/P001-user-reg-test.md",
      "hash": "a3f8c2d1e5b7",
      "model": "qwen3.5-plus",
      "temperature": 0.0,
      "timestamp": "2026-04-14T10:30:00Z",
      "output_file": "tests/test_user_registration.py",
      "result": "success"
    },
    {
      "phase": "implementation",
      "prompt_id": "P002",
      "version": "1.1",
      "file": "prompts/P002-user-reg-impl.md",
      "hash": "b7e4d3c8a1f2",
      "model": "qwen3.5-plus",
      "temperature": 0.0,
      "timestamp": "2026-04-14T10:35:00Z",
      "output_file": "src/user/registration.py",
      "result": "success"
    }
  ]
}
```

### 7.4 预期效果

| 指标 | 当前 (L1 人工) | 自动化后 (L3/L4) |
|------|--------------|----------------|
| 记录准确率 | ~60% (常遗漏) | 100% |
| 单 PR 记录时间 | 2-5 min | 0 min (自动) |
| 版本冲突 | 偶尔发生 (手动递增) | 0 (自动 semver) |
| 审计可追溯性 | 需要人工翻找 | 一键查询 `.gate/prompt-chain-trace.json` |
| 动态 Prompt 覆盖 | 无法记录 | 完全覆盖 |
| 质量影响 | 无直接影响 | Prompt 回归测试可检测质量退化 |

**风险评估**:
- **Prompt 泄漏风险**: 自动持久化可能意外保存含敏感信息的 Prompt。缓解：pre-send 扫描 + 持久化前二次脱敏
- **存储膨胀**: 大量动态 Prompt 可能占用空间。缓解：相同 hash 去重 + 定期清理 deprecated 版本
- **版本冲突**: 多人同时修改同一 Prompt。缓解：Git 锁机制 + 自动 rebase

---

## #8 — PR 描述填写 (Automated PR Description with Traceability)

### 8.1 当前位置

- **Primary**: `01-core-specification.md` Section 6.1.2 (lines 1042-1058): "每个 PR 必须在描述中声明使用的 Prompt 版本"
- **Gate rules**: `01-core-specification.md` Section 6.2 (lines 988-992): "PR 描述中必须引用 Spec 文件"
- **Compliance**: `02-auto-coding-practices.md` Section 6.7 (lines 2710-2721): 多个 Checkpoint 要求 PR 描述包含追溯信息
  - P1 商业驱动 → PR 描述: Spec 路径 + 商业目标摘要
  - P7 Spec 驱动 → PR 描述: Spec 文件路径和版本
  - P9 Prompt 版本化 → `.gate/prompt-chain-trace.json`
  - 自修复限制 → PR 描述: Self-Correction 轮次
- **CI Auto-fix**: `02-auto-coding-practices.md` (lines 1285-1286): "Include a diagnostic report in the PR description"
- **Security governance**: `04-security-governance.md` (line 143): "Prompt 持久化 + 审计追溯"

当前机制：开发者手动填写 PR 标题、描述、关联 Spec、商业目标、Prompt 版本等信息。信息常常不完整、格式不统一、难以审计。

### 8.2 替代方案详细设计

**机制名称**: PR Auto-Description Hook (PRADH)

**架构**:

```
PR 创建事件 → 信息收集器 (Spec/Prompt/Gate/Commit) → AI 生成描述 → 更新 PR → Gate 验证完整性
```

**自动收集的信息源**:

| 信息源 | 获取方式 | 内容 |
|--------|---------|------|
| **Spec 文件** | 解析分支中 `specs/` 的变更 | Spec ID、标题、验收标准、优先级 |
| **Prompt 追溯** | 读取 `.gate/prompt-chain-trace.json` | 使用的 Prompt 版本、模型、参数 |
| **Gate 结果** | 读取 `.gate/` 目录下的报告 | TDD 合规、SAST、lint、测试覆盖率 |
| **Commit 历史** | `git log` 分析 | 提交信息、Self-Correction 轮次、文件变更统计 |
| **商业目标** | 解析 Spec frontmatter 中的 `business_goal` 字段 | 商业目标 ID、描述、预期影响 |
| **AI 摘要** | AI 分析代码 diff | 变更摘要、影响范围、风险提示 |

**生成流程**:

1. PR 创建时（或 force-push 后），触发 hook
2. 从上述信息源收集数据
3. AI 生成结构化的 PR 描述（使用预定义模板）
4. 通过 GitHub/GitLab API 更新 PR 描述
5. Gate 验证描述完整性，缺失则自动补全

**AI 能力需求**:
- diff 理解：读取代码变更，生成准确的变更摘要
- 模板填充：将结构化数据填入 PR 描述模板
- 自然语言生成：将技术信息转化为可读的描述文本

**安全护栏**:
- 描述中不得包含敏感信息（密钥、内部 URL）
- 商业目标摘要必须来自 Spec frontmatter，不得 AI 编造
- Gate 结果必须如实报告，不得美化

### 8.3 配置示例

**GitHub Workflow** (`.github/workflows/pr-description.yml`):

```yaml
name: Auto PR Description
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  auto-description:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Collect PR Metadata
        id: collect
        run: |
          # Extract Spec info
          spec_file=$(find specs/ -name "*.md" -newer .git/HEAD 2>/dev/null | head -1)
          if [ -n "$spec_file" ]; then
            spec_id=$(grep -m1 '^id:' "$spec_file" | cut -d' ' -f2)
            spec_title=$(grep -m1 '^title:' "$spec_file" | cut -d' ' -f2-)
            business_goal=$(grep -m1 '^business_goal:' "$spec_file" | cut -d' ' -f2-)
          fi

          # Extract Prompt trace
          prompt_trace="N/A"
          if [ -f ".gate/prompt-chain-trace.json" ]; then
            prompt_trace=$(jq -r '.prompt_chain[] | "\(.prompt_id) v\(.version)"' .gate/prompt-chain-trace.json | tr '\n' ', ')
          fi

          # Extract Gate results
          tdd_status=$(jq -r '.tdd.status // "not_run"' .gate/tdd-report.json 2>/dev/null || echo "not_run")
          lint_status=$(jq -r '.lint.passed' .gate/lint-report.json 2>/dev/null || echo "unknown")
          test_count=$(jq -r '.tests.total' .gate/test-report.json 2>/dev/null || echo "0")

          # Self-Correction rounds
          self_correct=$(jq -r '.self_correction.rounds // 0' .gate/self-correct-report.json 2>/dev/null || echo "0")

          # Commit stats
          commit_count=$(git log --oneline origin/main..HEAD | wc -l)
          files_changed=$(git diff --name-only origin/main..HEAD | wc -l)

          echo "spec_id=${spec_id:-unknown}" >> $GITHUB_OUTPUT
          echo "spec_title=${spec_title:-unknown}" >> $GITHUB_OUTPUT
          echo "business_goal=${business_goal:-not_specified}" >> $GITHUB_OUTPUT
          echo "prompt_trace=${prompt_trace}" >> $GITHUB_OUTPUT
          echo "tdd_status=${tdd_status}" >> $GITHUB_OUTPUT
          echo "lint_status=${lint_status}" >> $GITHUB_OUTPUT
          echo "test_count=${test_count}" >> $GITHUB_OUTPUT
          echo "self_correct=${self_correct}" >> $GITHUB_OUTPUT
          echo "commit_count=${commit_count}" >> $GITHUB_OUTPUT
          echo "files_changed=${files_changed}" >> $GITHUB_OUTPUT

      - name: Generate AI Summary
        id: summary
        run: |
          git diff origin/main..HEAD > /tmp/pr.diff
          claude -p --max-turns 10 \
            "Analyze this code diff and generate a PR description section.
            Focus on: what changed, why, and any risks.
            Keep it under 200 words. Be specific about the changes.

            Diff:
            $(cat /tmp/pr.diff)" > /tmp/ai-summary.md

      - name: Update PR Description
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            const fs = require('fs');
            const pr = context.payload.pull_request;
            const s = ${{ toJSON(steps.collect.outputs) }};
            const aiSummary = fs.readFileSync('/tmp/ai-summary.md', 'utf8');

            const body = `## Change Summary

            ${aiSummary}

            ## Traceability

            | Item | Value |
            |------|-------|
            | **FeatureSpec** | \`${s.spec_id}\` - ${s.spec_title} |
            | **SpecFile** | \`specs/${s.spec_id}-*.md\` |
            | **BusinessGoal** | ${s.business_goal} |
            | **PromptVersions** | ${s.prompt_trace} |
            | **TDD** | ${s.tdd_status} |
            | **Lint** | ${s.lint_status} |
            | **Tests** | ${s.test_count} tests run |
            | **Self-Correction** | ${s.self_correct} rounds |
            | **Changes** | ${s.commit_count} commits, ${s.files_changed} files |

            ## GateReports

            - TDD: \`.gate/tdd-report.json\`
            - Lint: \`.gate/lint-report.json\`
            - Test: \`.gate/test-report.json\`
            - PromptChain: \`.gate/prompt-chain-trace.json\`

            ---
            *This description was auto-generated by PR Auto-Description Hook.*
            `;

            github.rest.pulls.update({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: pr.number,
              body: body,
            });
```

**PR Description Gate** (`.github/workflows/pr-gate.yml`):

```yaml
name: PR Description Gate
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  pr-desc-check:
    runs-on: ubuntu-latest
    steps:
      - name: Check Required Sections
        uses: actions/github-script@v7
        with:
          script: |
            const pr = context.payload.pull_request;
            const body = pr.body || '';
            const required = [
              'FeatureSpec',
              'BusinessGoal',
              'PromptVersion',
              'TDD',
              'Gate',
            ];
            const missing = required.filter(r => !body.includes(r));
            if (missing.length > 0) {
              core.setFailed(`PR description missing required sections: ${missing.join(', ')}`);
            }
```

### 8.4 预期效果

| 指标 | 当前 (人工) | 自动化后 |
|------|-----------|---------|
| PR 描述完整率 | ~40% (常见遗漏) | 100% |
| 填写时间 | 3-10 min/PR | 0 min (自动，<15s 延迟) |
| 格式一致性 | 低 (每人风格不同) | 高 (标准化模板) |
| 追溯可审计性 | 需要人工核对 | 所有追溯信息自动关联 |
| 商业目标关联 | 常被遗漏 | 自动从 Spec 提取 |

**风险评估**:
- **信息不准确**: AI 生成的变更摘要可能有误。缓解：AI 摘要仅作为补充，关键追溯信息从结构化数据源直接读取
- **敏感信息泄漏**: diff 中可能包含敏感信息。缓解：diff 发送给 AI 前执行 pre-send 脱敏扫描
- **API 限流**: 频繁更新 PR 描述可能触发 GitHub API 限流。缓解：合并更新操作，仅在有变化时更新

---

## #9 — Lint 修复审核 (Automated Lint Fix + Verification)

### 9.1 当前位置

- **Primary**: `01-core-specification.md` Section 2.4 (line 256): "自动合并 | L4: 仅限 trivial fix"
- **Trivial fix 定义**: `02-auto-coding-practices.md` Section 6.6 (line 2888): "Trivial Fix — 琐碎修复，仅包括 lint fix、format、注释 typo、依赖 patch"
- **Auto-merge 限制**: `02-auto-coding-practices.md` Section 2.3 (line 118): "自动合并仅限：lint fix、format、typo fix in comments、dependency version patch update"
- **Self-Correction 中的 lint**: `01-core-specification.md` Section 5.1 (line 441): "Lint 错误 | AI 能理解 lint 规则并修复 | 80%"
- **CI auto-fix**: `02-auto-coding-practices.md` Section 4.4 (lines 1275-1286): CI 失败时 AI 自动修复流程

当前机制：Lint 错误由 AI 在 Self-Correction Loop 中自动修复，但修复结果需要人工审核确认（L1）或至少需要人工审查 PR（L2/L3）。只有 L4 下 trivial fix 才能自动合并。

### 9.2 替代方案详细设计

**机制名称**: Lint Auto-Heal Pipeline (LAHP)

**架构**:

```
Lint 失败 → AI 解析错误 → 自动修复 → 验证修复 → (成功 → 自动提交) / (失败 → 报告人工)
```

**两阶段流水线**:

**阶段 1: 自动修复 + 自动验证**

1. Lint 工具运行，收集错误列表
2. AI 分析每个错误，分类为：
   - **Auto-fixable**: 格式问题、import 顺序、未使用变量、简单类型标注
   - **Human-required**: 需要架构判断的 lint 问题（如复杂度警告、设计模式建议）
3. 对 Auto-fixable 错误，AI 直接修复
4. 修复后重新运行 lint 工具验证
5. 验证通过 → 自动提交到当前分支
6. 验证失败 → 进入阶段 2

**阶段 2: 失败转人工**

1. AI 生成诊断报告：哪些 lint 错误未能修复、为什么
2. 创建 issue 或通知人工
3. 阻塞合并（lint 错误不得被忽略）

**自动合并策略**（仅 L4）:

| 条件 | 动作 |
|------|------|
| 仅含 lint fix + format，无其他变更 | 自动合并，跳过人工审查 |
| 包含功能变更 | 正常 PR 流程 |
| lint 修复失败 > 1 次 | 转人工 |
| 修复后引入新的 lint 错误 | 转人工（防止无限循环） |

**AI 能力需求**:
- Lint 输出解析：理解各 lint 工具的错误格式（ESLint、golangci-lint、ruff 等）
- 代码修复：针对具体 lint 规则生成修复代码
- 循环检测：防止 AI 修复引入新错误导致无限循环

**安全护栏**:
- 修复仅限于 **最小修改**：不改变代码语义，仅修复格式/风格
- 禁止修改测试断言来通过 lint
- 循环保护：最多 3 轮自动修复，超过后强制转人工
- 自动合并仅限于纯 lint/format 变更，通过 diff 语义分析验证无功能变更

### 9.3 配置示例

**Claude Code Hook** (`settings.json`):

```json
{
  "hooks": {
    "afterCommand": {
      "command": "node .omc/hooks/lint-auto-heal.js",
      "conditions": {
        "onlyIfCommandFailed": true,
        "matchPatterns": ["lint", "format", "build"]
      }
    }
  }
}
```

**Lint Auto-Heal Script** (`.omc/hooks/lint-auto-heal.js`):

```javascript
const { execSync } = require('child_process');

const AUTO_FIXABLE = [
  'indent', 'semi', 'quotes', 'comma-dangle',
  'no-unused-vars', 'import/order', 'eol-last',
  'trailing-spaces', 'keyword-spacing', 'space-infix-ops',
  'gofmt', 'goimports', 'ruff-format', 'ruff-lint',
];

const MAX_ROUNDS = 3;

async function lintAutoHeal() {
  let round = 0;
  let previousErrors = new Set();

  while (round < MAX_ROUNDS) {
    round++;
    console.log(`[Lint Auto-Heal] Round ${round}/${MAX_ROUNDS}`);

    const { stdout, stderr, status } = runLinter();
    const errors = parseLintErrors(stdout + stderr);

    if (errors.length === 0) {
      console.log('[Lint Auto-Heal] All lint errors fixed!');
      if (isOnlyLintChanges()) {
        execSync('git add -A && git commit -m "chore: auto-fix lint errors [auto-heal]"');
      }
      return { success: true, rounds: round };
    }

    const fixable = errors.filter(e => AUTO_FIXABLE.includes(e.rule));
    const manual = errors.filter(e => !AUTO_FIXABLE.includes(e.rule));

    if (manual.length > 0) {
      console.log(`[Lint Auto-Heal] ${manual.length} errors require manual attention:`);
      manual.forEach(e => console.log(`  - ${e.rule}: ${e.message} at ${e.file}:${e.line}`));
    }

    if (fixable.length === 0) {
      break;
    }

    const currentErrorKeys = new Set(fixable.map(e => `${e.rule}:${e.file}:${e.line}`));
    const persistent = [...currentErrorKeys].filter(k => previousErrors.has(k));
    if (persistent.length >= fixable.length * 0.8) {
      console.log(`[Lint Auto-Heal] Stuck in loop: ${persistent.length}/${fixable.length} errors persist`);
      break;
    }
    previousErrors = currentErrorKeys;

    const fixPrompt = `Fix the following lint errors. Make minimal changes:
${fixable.map(e => `${e.file}:${e.line} [${e.rule}] ${e.message}`).join('\n')}

Rules:
- Do NOT modify test assertions
- Do NOT change code logic
- Do NOT add @skip/@ignore`;

    await runClaudeFix(fixPrompt);
  }

  if (round >= MAX_ROUNDS) {
    console.log('[Lint Auto-Heal] Max rounds reached. Notifying human.');
    notifyHuman({ remainingErrors: parseLintErrors(runLinter().stdout + runLinter().stderr) });
  }

  return { success: false, rounds: round };
}
```

**GitHub Workflow** (`.github/workflows/lint-auto-fix.yml`):

```yaml
name: Lint Auto-Fix
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  lint-and-fix:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.head_ref }}
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Run Linter
        id: lint
        run: |
          npm run lint -- --format json > lint-results.json || true
          if [ -s lint-results.json ] && jq -e '.[] | select(.severity == 2)' lint-results.json > /dev/null 2>&1; then
            echo "has_errors=true" >> $GITHUB_OUTPUT
          fi

      - name: Auto-Fix Lint Errors
        if: steps.lint.outputs.has_errors == 'true'
        run: |
          claude -p --max-turns 30 --max-budget-usd 2.00 \
            --permission-mode auto \
            "Lint errors detected. Fix all auto-fixable lint errors.
            Rules:
            - Only fix style/format issues
            - Do NOT change code logic or test assertions
            - Run linter after each fix batch to verify
            - Max 3 rounds of fix attempts"

      - name: Verify Fix
        run: npm run lint

      - name: Auto-Commit Fix (L4 Only)
        if: env.AUTO_LEVEL == 'L4' && success()
        run: |
          git config user.name "ci-bot"
          git config user.email "ci-bot@example.com"
          git add -A
          git commit -m "chore: auto-fix lint errors"
          git push
```

### 9.4 预期效果

| 指标 | 当前 (人工审核) | 自动化后 |
|------|--------------|---------|
| lint fix 修复率 | 人工审核每个修复 | 80% 自动修复 + 自动验证 |
| 修复时间 | 5-15 min/次 | <2 min (自动) |
| 人工介入率 | 100% | <20% (仅修复失败时) |
| 无限循环风险 | 无 (人工控制) | 已防护 (3 轮上限 + 循环检测) |
| 语义变更风险 | 低 (人工审核) | 极低 (AST diff 验证) |

**风险评估**:
- **修复循环**: AI 修复 A 错误引入 B 错误。缓解：循环检测（80% 相同错误持续 → 停止）+ 3 轮硬上限
- **语义漂移**: lint 修复意外改变代码行为。缓解：修复后运行全量测试 + AST diff 验证
- **误判 auto-fixable**: 某些 lint 规则需要架构判断。缓解：保守分类，仅纯格式类标记为 auto-fixable

---

## #10 — 商业目标拆解 (AI-Assisted Business Goal Decomposition)

### 10.1 当前位置

- **Primary**: `01-core-specification.md` Section 2.1 (line 60):
  > "P1 商业驱动 — 所有开发活动必须有明确的商业目标支撑"
- **Level mapping**: `01-core-specification.md` Section 2.4 (line 243):
  > "P1 商业驱动 | L1: 人工定义每个商业目标 | L2: 人工定义，AI 辅助拆解 | L3: 人工定期定义，AI 按 Spec 队列执行 | L4: 人工定期审查，AI 自主按优先级执行"
- **Work distribution**: `01-core-specification.md` Section 7.2 (lines 1241-1250): L4 下 "人（周审计者）定义商业目标，AI（独立开发者）从 specs/ 读取任务"
- **Compliance**: `02-auto-coding-practices.md` Section 6.1 (lines 2581-2584): "所有开发活动必须有明确的商业目标 | PR 描述中包含 Spec 路径和商业目标摘要"
- **Pre-flight**: `02-auto-coding-practices.md` Section 3.1 (lines 881, 1809): 开发前检查 "商业目标已定义"

当前机制：产品负责人或技术负责人人工定义商业目标，然后人工拆解为 Feature Spec。在 L2 下 AI 辅助拆解，但拆解结果需要人工审核。

### 10.2 替代方案详细设计

**机制名称**: Business Goal Decomposition Engine (BGDE)

**架构**:

```
商业目标声明 → AI 拆解分析 → 生成 Spec 候选队列 → 优先级评分 → 人工审核 + 调整 → 确认执行
```

**三阶段流程**:

**阶段 1: 商业目标输入**

产品负责人输入商业目标（自然语言），例如：
> "Q2 目标：将用户注册转化率从 15% 提升到 25%，主要通过简化注册流程和优化移动端体验。"

**阶段 2: AI 拆解**

AI 分析商业目标，拆解为：
1. **价值流分析**: 识别影响转化率的关键路径
2. **Spec 候选生成**: 为每个可实施的改进点生成 Spec 草案
3. **依赖分析**: 识别 Spec 间的依赖关系
4. **影响评分**: 对每个 Spec 预估商业影响（基于历史数据或启发式）

**阶段 3: 人工审核 + 队列确认**

1. AI 展示拆解结果：Spec 队列、依赖图、优先级排序
2. 人工审核：调整优先级、合并/拆分 Spec、删除不需要的
3. 确认后进入执行队列

**Spec 生成格式**:

```yaml
---
id: F0XX
title: "..."
business_goal: "BG-001: 提升注册转化率"
priority: P1
estimated_impact: "high"
depends_on: []
parent_goal: "BG-001"
---
```

**AI 能力需求**:
- 商业目标理解：解析自然语言商业目标，识别关键指标和约束
- 价值流拆解：将高层目标拆解为可执行的技术任务
- Spec 生成：按照 Spec 模板格式生成 Feature Spec
- 优先级评估：基于影响/成本比进行优先级排序

**安全护栏**:
- AI 只做 **建议**，不做 **决策**：优先级、范围、取舍最终由人工决定
- 拆解结果必须可追溯回原始商业目标（`parent_goal` 字段）
- 防止过度拆解：Spec 粒度受 P8 最小批量原则约束
- 商业目标变更时，关联的 Spec 需要重新评估

### 10.3 配置示例

**Business Goals Definition** (`business-goals/BG-001-q2-conversion.md`):

```markdown
---
id: BG-001
title: "Q2 注册转化率提升"
owner: "@product-lead"
period: Q2-2026
current_metric: "注册转化率 15%"
target_metric: "注册转化率 25%"
deadline: 2026-06-30
status: active
---

# 商业目标：Q2 注册转化率提升

## 背景
当前注册转化率 15%，目标提升到 25%。

## 关键举措
1. 简化注册流程（当前 5 步 → 目标 2 步）
2. 优化移动端体验（移动端转化率仅 8%）
3. 增加社交登录选项
```

**Decomposition Command**:

```bash
claude -p --max-turns 50 \
  "You are a technical architect. Decompose this business goal into executable Feature Specs.

  Business Goal: $(cat business-goals/BG-001-q2-conversion.md)

  Rules:
  1. Generate Feature Specs in the standard v5.0 format
  2. Each Spec must be independently implementable (P8 minimum batch)
  3. Analyze dependencies between Specs
  4. Estimate priority based on impact/effort ratio
  5. Each Spec must reference the parent business goal

  Output:
  - List of Spec files to create in specs/
  - Dependency graph (JSON)
  - Priority-ordered execution queue
  - Risk assessment"
```

**Decomposition Output** (`.decomposition/BG-001-queue.json`):

```json
{
  "business_goal": "BG-001",
  "decomposed_at": "2026-04-14T14:00:00Z",
  "specs": [
    {
      "id": "F010",
      "title": "简化注册流程 - 合并姓名和邮箱步骤",
      "file": "specs/F010-simplify-registration-step1.md",
      "priority": "P1",
      "estimated_impact": "high",
      "estimated_effort": "medium",
      "impact_score": 9,
      "depends_on": [],
      "rationale": "直接减少注册步骤，预期提升转化率 5-8%"
    },
    {
      "id": "F011",
      "title": "移动端注册页面响应式优化",
      "file": "specs/F011-mobile-registration-responsive.md",
      "priority": "P1",
      "estimated_impact": "high",
      "estimated_effort": "large",
      "impact_score": 8,
      "depends_on": [],
      "rationale": "移动端转化率仅 8%，优化空间最大"
    },
    {
      "id": "F012",
      "title": "社交登录集成 (Google, WeChat)",
      "file": "specs/F012-social-login-integration.md",
      "priority": "P2",
      "estimated_impact": "medium",
      "estimated_effort": "medium",
      "impact_score": 6,
      "depends_on": ["F010"],
      "rationale": "社交登录可降低注册门槛，但依赖流程简化"
    }
  ],
  "execution_queue": ["F010", "F011", "F012"],
  "parallel_groups": [["F010", "F011"], ["F012"]],
  "risk_notes": "F011 工作量较大，建议拆分为独立 PR"
}
```

**CI Gate** (`.github/workflows/business-goal-gate.yml`):

```yaml
name: Business Goal Gate
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  bg-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Verify Business Goal Linkage
        run: |
          spec_ids=$(git diff --name-only origin/main..HEAD | grep "^specs/" | sed 's/specs\/\(F[0-9]*\).*/\1/')
          for spec_id in $spec_ids; do
            spec_file="specs/${spec_id}-"*.md
            bg=$(grep -m1 '^business_goal:' "$spec_file" | cut -d' ' -f2-)
            if [ -z "$bg" ]; then
              echo "::error::Spec $spec_id has no business_goal declared"
              exit 1
            fi
            bg_id=$(echo "$bg" | cut -d' ' -f1)
            bg_file="business-goals/${bg_id}-"*.md
            if [ ! -f "$bg_file" ]; then
              echo "::error::Business goal file not found: $bg_file"
              exit 1
            fi
            echo "OK: $spec_id -> $bg"
          done
```

### 10.4 预期效果

| 指标 | 当前 (人工拆解) | 自动化后 |
|------|--------------|---------|
| 拆解时间 | 1-4 小时/目标 | 15-30 min (AI 生成 + 人工审核) |
| 拆解完整性 | 取决于经验 | 系统化分析，覆盖更广 |
| Spec 生成质量 | 人工编写，一致性参差 | 模板化生成，格式统一 |
| 商业-技术追溯 | 手动维护，常断裂 | 自动关联，完整追溯 |
| 优先级合理性 | 主观判断 | 数据辅助 (影响评分) |

**风险评估**:
- **AI 误解商业目标**: AI 可能误解优先级或遗漏关键约束。缓解：人工审核阶段必须确认
- **过度拆解**: AI 可能生成过多细碎 Spec。缓解：P8 最小批量原则约束
- **优先级偏差**: AI 的 impact 评分可能不准确。缓解：标注为 "AI 预估"，人工可调整
- **商业目标漂移**: 执行期间商业目标变更。缓解：每周检查活跃商业目标状态

---

## #11 — 自修循环每轮确认 (Automated Self-Correction Verification)

### 11.1 当前位置

- **Primary**: `01-core-specification.md` Section 2.4 (line 254):
  > "自修复限制 | L1: 最多 3 轮，人工确认每轮 | L2: 最多 3 轮，自动执行 | L3: 最多 3 轮，自动执行，超 3 轮转人工 | L4: 最多 3 轮，自动执行，超 3 轮暂停并告警"
- **L1 detail**: `01-core-specification.md` Section 2.3 (line 163): "自修循环：AI 修复 lint/test 错误，人工确认修复结果"
- **Cycle comparison**: `01-core-specification.md` Section 2.7 (line 317): "自修循环 | L1: 人确认每轮，10min | L2+: AI 自主 3 轮，5min"
- **Auto-coding**: `02-auto-coding-practices.md` Section 3.1 (line 131): "自修循环（3 轮） | L1: 人工确认每轮"
- **Security**: `04-security-governance.md` Section 2.1 (line 79): "L1：人工确认每轮；L2-L4：自动执行"

当前机制（L1）：Self-Correction Loop 的每一轮修复后，都需要人工确认修复结果（运行测试、检查 lint）才能进入下一轮。L1 下自修循环耗时长（10min vs L2+ 的 5min）。

### 11.2 替代方案详细设计

**机制名称**: Self-Correction Auto-Verify Loop (SCAVL)

**架构**:

```
CI 失败 → AI 诊断 → 修复 → 自动验证 (CI re-run) → {通过 → 完成} / {失败 → 下一轮} → {3 轮全败 → 转人工}
```

**核心改进**: 用 **自动 CI 验证** 替代 **人工确认每轮**

**轮次管理**:

| 轮次 | 动作 | 验证方式 | 失败后 |
|------|------|---------|--------|
| **Round 1** | AI 诊断根因 + 最小修复 | 自动 CI re-run | 进入 Round 2 |
| **Round 2** | AI 分析 Round 1 失败日志 + 修复 | 自动 CI re-run | 进入 Round 3 |
| **Round 3** | AI 分析 Round 2 失败日志 + 尝试替代方案 | 自动 CI re-run | **转人工** (3 轮全败) |
| **>3 轮** | 暂停，生成诊断报告 | 人工介入 | 人工修复后重置计数器 |

**自动验证机制**:

1. AI 修复代码后，自动提交到分支
2. 触发 CI pipeline（lint + test + build）
3. 自动收集 CI 结果：
   - 全部通过 → 本轮修复成功，跳出循环
   - 仍有失败 → 提取失败日志，作为下一轮修复的输入
4. 3 轮全部失败 → 自动创建 issue，通知人工，附带诊断报告

**诊断报告内容**:
- 原始错误
- 每轮的修复尝试和结果
- 最终失败状态和日志
- AI 建议的人工处理方向

**AI 能力需求**:
- 失败日志理解：解析 CI 输出、编译器错误、测试失败信息
- 根因分析：区分表面错误和根因
- 替代策略：当直接修复无效时，尝试不同的修复路径
- 进度感知：知道当前是第几轮，避免重复之前的失败方案

**安全护栏**:
- 每轮修复必须是最小变更（不得大规模重写）
- 禁止修改测试断言来 "通过" 测试
- 禁止添加 @skip/@ignore 来绕过失败
- 修复后必须重新运行完整 CI（不得只运行部分测试）
- 3 轮全败后 **必须** 转人工，不得自动继续
- AI 不得自动合并修复后的代码（即使测试通过），必须走 PR 流程

### 11.3 配置示例

**GitHub Workflow** (`.github/workflows/self-correct.yml`):

```yaml
name: Self-Correction Loop
on:
  workflow_call:
    inputs:
      branch:
        required: true
        type: string
      max_rounds:
        default: 3
        type: number

jobs:
  self-correct:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    strategy:
      matrix:
        round: [1, 2, 3]
      max-parallel: 1
    outputs:
      success: ${{ steps.verify.outputs.success }}

    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.branch }}

      - name: Run CI Validation
        id: validate
        run: |
          npm run lint && npm run build && npm test > ci-output.txt 2>&1
          if [ $? -eq 0 ]; then
            echo "status=pass" >> $GITHUB_OUTPUT
          else
            echo "status=fail" >> $GITHUB_OUTPUT
          fi

      - name: AI Fix (Round ${{ matrix.round }})
        if: steps.validate.outputs.status == 'fail'
        run: |
          PREV_LOG=""
          if [ -f ".self-correct/round-${{ matrix.round - 1 }}-log.txt" ]; then
            PREV_LOG=$(cat ".self-correct/round-${{ matrix.round - 1 }}-log.txt")
          fi

          claude -p --max-turns 40 --max-budget-usd 3.00 \
            --permission-mode auto \
            "Self-Correction Round ${{ matrix.round }} of ${{ inputs.max_rounds }}.

            CI Failure Log:
            ${{ steps.validate.outputs.ci_log }}

            Previous Round Failure (if any): ${PREV_LOG}

            Diagnose the root cause and fix it.

            Rules:
            1. Make the MINIMAL change needed
            2. Do NOT modify test assertions
            3. Do NOT add @skip or @ignore
            4. If round > 1, try a different approach than previous rounds"

      - name: Verify Fix
        id: verify
        run: |
          npm run lint && npm run build && npm test
          if [ $? -eq 0 ]; then
            echo "success=true" >> $GITHUB_OUTPUT
          else
            echo "success=false" >> $GITHUB_OUTPUT
          fi

      - name: Early Exit on Success
        if: steps.verify.outputs.success == 'true'
        run: echo "Fixed in round ${{ matrix.round }}!" && exit 0

  notify-on-failure:
    needs: self-correct
    if: failure()
    runs-on: ubuntu-latest
    steps:
      - name: Generate Diagnostic Report
        run: |
          cat << EOF > .self-correct/diagnostic-report.md
          # Self-Correction Failed - Diagnostic Report

          **Branch**: ${{ inputs.branch }}
          **Rounds Attempted**: ${{ inputs.max_rounds }}
          **Status**: All rounds failed

          ## AI Recommendation
          Manual intervention is required. Likely root causes:
          - Complex dependency conflict
          - Architecture-level issue
          - Missing prerequisite setup
          EOF

      - name: Create Issue
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('.self-correct/diagnostic-report.md', 'utf8');
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `Self-Correction Failed - Manual Intervention Required`,
              body: report,
              labels: ['self-correct-failed', 'needs-human-attention'],
            });
```

**Self-Correction State Tracking** (`.gate/self-correct-report.json`):

```json
{
  "feature": "F001",
  "branch": "feature/F001-user-registration",
  "trigger": "CI failure on build step",
  "rounds": [
    {
      "round": 1,
      "timestamp": "2026-04-14T10:40:00Z",
      "error_category": "lint",
      "error_summary": "Unused variable 'tempResult' in registration.py:45",
      "fix_applied": "Removed unused variable",
      "verification": "pass",
      "ci_duration": "45s"
    }
  ],
  "total_rounds": 1,
  "final_status": "pass",
  "time_saved": "8min"
}
```

### 11.4 预期效果

| 指标 | L1 (人工每轮确认) | 自动化后 (L2+) |
|------|-----------------|--------------|
| 单轮确认时间 | 3-5 min (人工检查) | 0 min (CI 自动) |
| 3 轮总耗时 | ~10 min | ~5 min |
| 人工介入率 | 100% (每轮) | <10% (仅 3 轮全败时) |
| 修复成功率 | 取决于人工经验 | 80% (Round 1) → 70% (Round 2) → 60% (Round 3) |
| 诊断质量 | 取决于人工技术水平 | AI 根因分析 + 完整日志 |
| 夜间/自主开发可行性 | 不可行 (需要人在场) | 完全可行 (自主运行) |

**风险评估**:
- **假阳性通过**: AI 修复后测试通过但修复方式不正确。缓解：CI 中包含断言完整性检查
- **无限重试**: 3 轮上限已防护。缓解：硬性计数器 + 每轮不同修复策略
- **修复污染**: AI 修复引入隐蔽 bug。缓解：全量测试 + AST diff 检查变更范围
- **夜间通知不及时**: 人工无法立即响应。缓解：Slack/邮件通知，不阻塞其他独立 Spec

---

## 汇总对比

| # | 自动化项 | 当前人工耗时 | 自动化后人工耗时 | 节省比例 | 风险等级 |
|---|---------|------------|---------------|---------|---------|
| 6 | Mock 必要性审查 | 5-10 min/PR | 0 min | 100% | 低 |
| 7 | Prompt 版本记录 | 2-5 min/PR | 0 min | 100% | 低 |
| 8 | PR 描述填写 | 3-10 min/PR | 0 min | 100% | 低 |
| 9 | Lint 修复审核 | 5-15 min/次 | 0 min (80% case) | 80% | 中 |
| 10 | 商业目标拆解 | 1-4 小时/目标 | 15-30 min | 85% | 中 |
| 11 | 自修循环确认 | 3-5 min/轮 | 0 min | 100% | 中 |

**总体影响**：这 6 项自动化可将 L1 下单 Feature 的人工时间从 ~150 min 降至 ~60 min（节省 60%），同时为 L2 → L3 → L4 的升级路径铺平道路。所有自动化项都保留了人工介入的逃生通道，确保在 AI 无法处理的情况下 gracefully degrade 到人工处理。
