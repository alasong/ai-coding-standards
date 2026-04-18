# AI Coding 规范 v5.4：CI/CD Pipeline

> 版本：v5.4 | 2026-04-18
> 定位：大规模 Auto-Coding 的交付基础设施 — 定义 Pipeline 分层结构、质量门禁、环境晋升
> 前置：[01-core-specification.md](01-core-specification.md) 第 2 章（TDD）、第 3 章（幻觉检测）

---

## 第 1 章：Pipeline 架构总览

### 1.1 为什么需要 Pipeline 规范

大规模 Auto-Coding = 每天数十至数百个 AI 生成的 PR。没有标准化的 Pipeline 意味着：
- 每个 PR 的人工验证成本无法随规模线性下降
- L3/L4 自主编码失去自动化质量门禁
- 无法区分"格式问题"和"安全问题"的严重级别
- 多服务并行部署时缺乏统一的晋升标准

**核心原则**：Pipeline 是 AI 代码进入生产的唯一通道。所有代码——无论人类编写还是 AI 生成——必须通过同一 Pipeline，且 AI 生成的代码有额外的门禁检查。

### 1.2 Pipeline 分层架构

```
┌─────────────────────────────────────────────────────┐
│  L0 — 即时反馈层（<30s）                              │
│  pre-commit hooks · secret scan · format check       │
├─────────────────────────────────────────────────────┤
│  L1 — 编译验证层（<2min）                              │
│  build · type check · import check                   │
├─────────────────────────────────────────────────────┤
│  L2 — 测试验证层（<10min）                             │
│  unit test · integration test · coverage             │
├─────────────────────────────────────────────────────┤
│  L3 — 质量审查层（<15min）                             │
│  lint · SAST · AI Reviewer · API drift check         │
├─────────────────────────────────────────────────────┤
│  L4 — 集成验证层（<30min）                             │
│  E2E test · contract test · performance baseline     │
├─────────────────────────────────────────────────────┤
│  L5 — 环境晋升层（按策略触发）                           │
│  staging deploy · smoke test · canary · production   │
└─────────────────────────────────────────────────────┘
```

### 1.3 层级设计原则

| 原则 | 说明 |
|------|------|
| **速检优先** | 每层必须在时间盒内完成，超时自动阻断并上报 |
| **快速失败** | 低层级的检查先运行，失败则跳过后续所有层级 |
| **分层隔离** | 每层有独立的通过/失败/警告状态，不混为一谈 |
| **AI 增强** | AI 生成的代码在 L3 层有额外的幻觉检测门禁 |
| **可追溯** | 每层结果写入 `.gate/` 目录，形成证据链 |

---

## 第 2 章：各 Layer 详细定义

### 2.1 L0 — 即时反馈层（开发者本地）

**触发时机**：本地 `git commit` 前，pre-commit hook 自动执行。
**目标**：拦截最基础的错误，不浪费 CI 资源。
**时间盒**：30 秒。

| 检查项 | 命令/工具 | 阻断？ | AI 增强 |
|--------|----------|:------:|:-------:|
| 代码格式化 | `gofmt -l` / `prettier --check` | 否→警告 | AI 代码格式不通过=自动修复后重新提交 |
| 密钥扫描 | `gitleaks detect --staged` | **是** | 双向增强：AI 生成密钥=违反 P5 |
| 提交信息规范 | `commitlint` | 否→警告 | 检查是否包含 `ai-generated: true` 标记 |
| 文件大小检查 | 单文件 > 200 行 = 警告 | 否→警告 | 违反 P8 最小批量时警告 |
| 禁止文件检查 | `.env` / `secrets/` 不应被提交 | **是** | 检查 AI 是否生成了敏感文件 |
| pre-send 数据分级扫描 | 检查待提交内容是否含 Restricted 数据 | **是** | P10 数据分级 |

**AI 特有规则**：AI 生成的每次提交必须在 commit message 中包含 `ai-generated: true` 和 `spec: F{NNN}` 引用。

### 2.2 L1 — 编译验证层

**触发时机**：PR 创建或 push 到功能分支时。
**目标**：确保代码可以编译，类型系统完整。
**时间盒**：2 分钟。

| 检查项 | 命令/工具 | 阻断？ | 说明 |
|--------|----------|:------:|------|
| 编译/构建 | `go build ./...` / `tsc --noEmit` / `python -m py_compile` | **是** | 任何编译错误阻断合并 |
| 类型检查 | 语言特定的类型检查器 | **是** | AI 倾向于生成"看起来正确但类型不匹配"的代码 |
| Import 检查 | `go mod verify` / `npm ls` / `pip check` | **是** | 验证 E01-E03 存在性幻觉 |
| 循环依赖检测 | 架构级别依赖分析工具 | **是** | AI 可能无意中引入循环依赖 |
| 编译警告计数 | 编译警告数量不得超过基线 | 警告 | 警告数增长记录到 PR 描述 |

**AI 特有规则**：编译通过不等于代码正确。L1 通过只是最低门槛，不标记"AI 代码质量合格"。

### 2.3 L2 — 测试验证层

**触发时机**：L1 通过后。
**目标**：验证功能正确性、测试覆盖率。
**时间盒**：10 分钟。

| 检查项 | 命令/工具 | 阻断？ | 说明 |
|--------|----------|:------:|------|
| 单元测试 | `go test ./...` / `jest` / `pytest` | **是** | 全部通过 |
| 集成测试 | `go test -tags=integration` / 数据库集成测试 | **是** | 使用真实数据库容器 |
| TDD 合规检查 | 检查测试 commit 在实现 commit 之前 | **是** | 01-core-specification.md 第 2 章 |
| TDD Red 阶段验证 | 测试提交后、实现提交前必须失败 | **是** | 检测 TDD 造假 |
| 覆盖率检查 | `go test -cover` / `nyc` / `coverage.py` | **是** | 每包 ≥ 80%，AC 覆盖率 100% |
| 分支覆盖率 | 分支覆盖 ≥ 75% | 警告 | AI 倾向于只写正常路径测试 |
| Flaky Test 检测 | 同一 PR 重跑 3 次检测不稳定测试 | 警告 | 02-auto-coding-practices.md 4.3 |

**AI 特有规则**：
- AI 生成测试时，CI 必须检查断言是否"过于宽松"（如 `assert(true)`）
- 覆盖率 80% ≠ AC 覆盖 100%。必须分别报告包覆盖率和 AC 覆盖率
- AI 生成的 Mock 必须审查合理性（禁止为一切写 Mock）

### 2.4 L3 — 质量审查层

**触发时机**：L2 通过后。
**目标**：代码质量、安全、AI 幻觉检测。
**时间盒**：15 分钟。

| 检查项 | 命令/工具 | 阻断？ | 说明 |
|--------|----------|:------:|------|
| Lint | `golangci-lint run` / `eslint` / `flake8` | **是** | 错误级别阻断，警告级别记录 |
| SAST 扫描 | `semgrep` / `gosec` / `bandit` | **是** | 安全漏洞阻断 |
| **AI Reviewer 自动审查** | AI 对代码做 A01-A09 检查 | **是** | 05-tool-reference.md 第 4 章 |
| 幻觉检测扫描 | API 存在性 + 符号解析 + 依赖验证 | **是** | 检测 E/X/V/L/S 系列幻觉 |
| API 漂移检查 | `scripts/check-api-drift.py` | 警告 | 检查实现是否偏离 Spec 中的 API 定义 |
| 技术债扫描 | `sonarqube` / `codeclimate` | 警告 | 代码异味计数，不得增长 |
| 复杂度检查 | 圈复杂度 > 10 = 警告，> 20 = 阻断 | **是** | AI 倾向生成"大函数" |
| 注释-代码一致性 | 检查注释是否描述实际行为 | 警告 | D01 注释幻觉检测 |
| 依赖漏洞扫描 | `trivy` / `npm audit` / `safety` | **是** | 高严重级别漏洞阻断 |

**AI Reviewer 自动审查规则**：
1. AI Reviewer 必须使用与生成代码**不同的模型实例**
2. 审查结果写入 `.gate/ai-review.json`，包含每个 A01-A09 检查项的通过状态
3. 任何 A01-A09 检查项失败 = L3 不通过
4. AI Reviewer 的置信度评分 < 0.7 时，标记 "需人工重点审查"

### 2.5 L4 — 集成验证层

**触发时机**：L3 通过后，合并前触发。
**目标**：端到端功能验证、性能基线、契约一致性。
**时间盒**：30 分钟。

| 检查项 | 命令/工具 | 阻断？ | 说明 |
|--------|----------|:------:|------|
| E2E 测试 | `playwright` / `cypress` / HTTP E2E 脚本 | **是** | 覆盖关键用户旅程 |
| API 契约测试 | `pact` / `dredd` / OpenAPI 验证 | **是** | 验证 API 符合 OpenAPI Spec |
| 数据库迁移测试 | 在干净 DB 上执行迁移 + 回滚 + destructive change 检测 | **是** | 见数据库迁移规范 |
| **性能基线检查** | 基准测试 vs 上次基线 | **是** | 见性能基线规范 |
| 安全渗透扫描 | DAST 工具（`owasp-zap`） | **是** | 动态安全测试 |
| AC 映射验证 | 对照 Spec 验证每个验收标准 | **是** | 07-anti-hallucination.md 2.3 |
| 跨服务集成测试 | 多服务联合测试 | **是** | 适用于微服务架构 |

**AC 映射验证详细规则**：
```
For each Acceptance Criteria (AC) in Spec:
  1. 找到对应的测试函数名
  2. 验证测试函数确实调用了被测代码
  3. 检查 .gate/ 中的运行输出（stdout/stderr）
  4. 标记 AC 状态: covered / not_covered / failed
AC 覆盖率 < 100% = L4 不通过
```

### 2.6 L5 — 环境晋升层

**触发时机**：PR 合并到 main 后自动触发。
**目标**：安全地将代码从 main 晋升到生产环境。

**部署策略**：金丝雀发布（5%→25%→50%→100%）为默认策略。金丝雀阶段定义、流量分配、通过标准等详见 [13-deploy-rollback.md](13-deploy-rollback.md) 第 2.2 章。蓝绿部署、滚动升级的策略定义见同文件第 2.1/2.3 章。

**Pipeline 职责**：L5 负责串联各阶段并在每个阶段完成后调用验证逻辑。

| 阶段 | Pipeline 验证项 | 验证执行者 | 自动/人工 |
|------|----------------|-----------|----------|
| **staging deploy** | 构建镜像、部署到 staging | CI Runner | 自动 |
| **smoke test** | 健康检查 + 核心 E2E | 测试脚本 | 自动 |
| **canary stages** | 错误率/延迟/业务指标采集 | 监控系统 | 自动 |
| **production 100%** | 最终检查点确认 | 监控系统 | 按自治等级（见第 5 章） |

**自动回滚触发条件**（任一满足即触发，详细分级见 [13-deploy-rollback.md](13-deploy-rollback.md) 第 3.1 章）：
- 错误率 > 5%（5 分钟窗口）
- P99 延迟 > 基线×2（5 分钟窗口）
- 关键业务指标下降 > 10%
- 健康检查连续 3 次失败
- Critical 级别告警触发

**Pipeline 与回滚的边界**：L5 检测到回滚条件后，执行回滚动作并写入 `.gate/rollback-report.json`。回滚的具体粒度（全量 vs 按服务）、数据一致性保障、LKG 版本选择等机制由 13-deploy-rollback.md 定义。

---

## 第 3 章：Pipeline 并行与加速策略

### 3.1 并行策略

```
L0 (pre-commit) ──串行──→ L1 ──串行──→ L2
                                       ├──→ L3（lint + SAST）── 串行 ──→ L4
                                       └──→ L3'（AI Reviewer）──┘
                                                    ↓
                                             两者都通过 → L4
```

| 层级 | 并行规则 |
|------|---------|
| L0→L1→L2 | 必须串行，快速失败 |
| **L3 内部** | lint、SAST 并行 → AI Reviewer 必须等待 SAST 完成后再执行（需读取 SAST 结果） |
| L4 | E2E 测试可并行拆分（按 feature 分组） |
| L5 | 金丝雀阶段必须串行，等待稳定窗口 |

### 3.2 缓存策略

| 可缓存项 | 缓存键 | 缓存失效条件 |
|---------|--------|-------------|
| 依赖下载 | `go.sum` / `package-lock.json` hash | 依赖变更 |
| 编译产物 | 源码文件 hash | 源码变更 |
| 测试产物 | 测试文件 + 实现文件 hash | 测试或实现变更 |
| Lint 结果 | 源码文件 hash | 源码变更 |

**AI 特有规则**：AI 生成的代码修改范围较大时（> 50 文件），不启用测试缓存，全量运行。

### 3.3 Pipeline 状态通知

| 事件 | 通知方式 | 通知对象 |
|------|---------|---------|
| L0 阻断 | 本地输出（不通知） | 开发者本地 |
| L1 阻断 | PR comment + Slack | PR 作者 + Slack channel |
| L2 阻断 | PR comment + Slack | PR 作者 + Slack channel |
| L3 阻断（安全） | Slack + email + PagerDuty | 安全团队 + PR 作者 |
| L3 阻断（幻觉） | PR comment + Slack | PR 作者 + AI 审核者 |
| L4 阻断 | PR comment + Slack | PR 作者 + 人工审查者 |
| L5 回滚 | Slack + PagerDuty | on-call + 技术负责人 |

---

## 第 4 章：Pipeline Self-Correction 策略

Pipeline 各层失败后，AI 必须按以下策略自动修复，而非直接转人工。

### 4.1 各层 Self-Correction 规则

| 层级 | AI 可自动修复？ | 最大轮次 | 修复范围 | 转人工条件 |
|------|:---:|:--------:|---------|-----------|
| **L0** | **是** | 1 轮（自动修复后重新 commit） | 格式化、密钥移除、文件删除 | 修复后仍失败 |
| **L1** | **是** | 2 轮 | 类型标注、import 修正、编译错误 | 架构级编译错误 |
| **L2** | **是** | 3 轮（沿用 Self-Correction Loop） | 测试失败、Mock 配置 | 测试逻辑错误、AC 无法映射 |
| **L3 lint** | **是** | 2 轮 | 代码风格、未使用变量 | 架构级 lint（循环依赖） |
| **L3 SAST** | **否** | — | — | 安全漏洞必须人工确认修复方案 |
| **L3 幻觉** | **是** | 3 轮 | API 修正、依赖版本修正 | 核心逻辑幻觉 |
| **L4 E2E** | **是** | 3 轮 | E2E 脚本修复、测试数据修正 | 端到端功能缺失 |
| **L4 性能** | **否** | — | — | 性能退化需要架构级分析 |
| **L4 AC 未覆盖** | **是** | 3 轮 | 补充缺失测试 | AC 需求理解错误 |
| **L5 回滚** | **否** | — | — | 自动回滚，通知人工分析 |

### 4.2 Self-Correction 约束

| 规则 | 说明 |
|------|------|
| **禁止修改测试断言** | 不得为了让测试通过而修改断言（违反 P3 TDD 先行） |
| **禁止删除失败测试** | 不得删除失败的测试用例 |
| **禁止添加 @skip** | 不得跳过失败的测试 |
| **最小修改原则** | 每次修复只修改与失败直接相关的代码 |
| **修复痕迹记录** | 每次 Self-Correction 必须写入 `.gate/self-correction.json` |
| **安全漏洞不可自修** | SAST 检测的安全漏洞不得由 AI 自行"修复"，必须人工确认 |
| **性能退化不可自修** | 性能基线检查失败不得由 AI 自行"优化"，必须人工分析根因 |

### 4.3 Self-Correction 证据文件

```json
{
  "type": "pipeline-self-correction",
  "layer": "L2",
  "check": "unit-test",
  "attempt": 1,
  "max_attempts": 3,
  "error": "expected 200 but got 500",
  "fix_description": "Added missing error handling in handler.go:42",
  "files_changed": ["src/handler.go"],
  "result": "passed"
}
```

---

## 第 5 章：Pipeline 与自治等级的关系

### 4.1 不同等级的 Pipeline 差异

| 检查项 | L1 | L2 | L3 | L4 |
|--------|----|----|----|----|
| L0-L4 | 全部运行 | 全部运行 | 全部运行 | 全部运行 |
| L3 AI Reviewer | 阻断合并 | 阻断合并 | 阻断合并 | 阻断合并 |
| L4 AC 映射验证 | 阻断合并 | 阻断合并 | 阻断合并 | 阻断合并 |
| 人工审查 | **必须** | **必须** | **必须** | 抽样 ≥10% |
| L5 金丝雀 | 人工审批每阶段 | 人工审批 100% | 自动到 50% | 全自动 |
| 自动回滚 | 人工决策 | 人工决策 | 自动 | 自动 |

### 4.2 Pipeline 作为 P2 DCP 门禁的执行载体

```
Phase N 完成 → DCP 决策 → [Go/No-Go]
                              ↓ Go
                    Pipeline L1→L2→L3→L4→L5
                              ↓ 全部通过
                    生产环境部署完成
                              ↓
                    Phase N+1 开始
```

**DCP 与 Pipeline 的关系**：DCP 是"能不能做"的决策点，Pipeline 是"做得对不对"的验证链。DCP 通过后代码进入 Pipeline，Pipeline 全部通过才算 Phase 完成。

---

## 第 5 章：Artifact 与构建产物管理

### 5.1 Artifact 定义

| 类型 | 内容 | 存储位置 | 保留策略 |
|------|------|---------|---------|
| **构建产物** | 二进制、Docker 镜像 | Container Registry | 最近 20 个版本 |
| **测试报告** | JUnit XML、覆盖率报告 | `.gate/` + CI 存储 | 90 天 |
| **AI 证据链** | `.gate/*.json` | Git（小文件）+ CI 存储 | 永久 |
| **安全报告** | SAST、DAST、依赖扫描 | CI 存储 | 1 年 |
| **性能基线** | 基准测试结果 | `.gate/performance/` | 永久，用于趋势分析 |

### 5.2 镜像构建规范

| 规则 | 说明 |
|------|------|
| 多阶段构建 | 构建层和运行层分离，最终镜像不含构建工具 |
| 非 root 运行 | 容器内进程以非 root 用户运行 |
| 最小基础镜像 | 优先使用 `distroless` / `alpine` |
| SBOM 生成 | 每个镜像生成 Software Bill of Materials |
| 镜像签名 | 使用 cosign 签名，验证签名后部署 |

### 5.3 版本号规范

```
{major}.{minor}.{patch}-{autocoding}-{commit_sha_short}
```

| 组件 | 说明 |
|------|------|
| major | 不兼容 API 变更 |
| minor | 向后兼容的功能新增 |
| patch | 向后兼容的 Bug 修复 |
| autocoding | AI 生成的构建编号（自增） |
| commit_sha_short | Git commit 短 hash（8 位） |

**AI 特有规则**：AI 生成的 PR 不得自行决定 major/minor 版本变更，必须由人类在 DCP 决策时确定版本号变更类型。

---

## 第 6 章：Pipeline 配置模板

### 6.1 GitHub Actions 模板

```yaml
name: AI-Coding Pipeline
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  # L0: pre-commit (local, not CI)

  # L1: 编译验证
  compile:
    runs-on: ubuntu-latest
    timeout-minutes: 2
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: go build ./...
      - name: Type check
        run: go vet ./...

  # L2: 测试验证
  test:
    needs: compile
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - name: Unit tests
        run: go test ./... -coverprofile=coverage.out -covermode=atomic
      - name: Coverage check
        run: go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//' | awk '{if ($1 < 80) exit 1}'

  # L3: 质量审查
  quality:
    needs: compile
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - name: Lint
        run: golangci-lint run
      - name: SAST
        run: gosec ./...
      - name: AI Reviewer
        run: claude -p "Review this PR against A01-A09 checklist" --max-turns 10
      - name: Hallucination scan
        run: python ai-coding-v5.4/scripts/check-api-drift.py

  # L4: 集成验证
  integration:
    needs: [test, quality]
    runs-on: ubuntu-latest
    timeout-minutes: 30
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - name: E2E tests
        run: go test -tags=e2e ./...
      - name: AC mapping verification
        run: python ai-coding-v5.4/scripts/spec-validate.py

  # L5: 部署（仅 main 分支）
  deploy:
    needs: integration
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: ./scripts/deploy.sh staging
      - name: Smoke test
        run: ./scripts/smoke-test.sh
      - name: Canary 5%
        run: ./scripts/canary.sh 5
      - name: Canary 100%
        run: ./scripts/canary.sh 100
```

### 6.2 `.aicoding.yaml` Pipeline 扩展配置

```yaml
pipeline:
  layers:
    L0:
      name: "即时反馈"
      timeout: 30s
      trigger: pre-commit
      steps:
        - secret-scan
        - format-check
        - data-classification-scan

    L1:
      name: "编译验证"
      timeout: 2m
      trigger: pr-create | push
      steps:
        - compile
        - type-check
        - import-verify
      on_failure: block

    L2:
      name: "测试验证"
      timeout: 10m
      trigger: L1-pass
      steps:
        - unit-test
        - integration-test
        - tdd-compliance
        - coverage-check
      on_failure: block

    L3:
      name: "质量审查"
      timeout: 15m
      trigger: L2-pass
      parallel:
        - lint
        - sast
        - ai-reviewer
        - hallucination-scan
        - dependency-audit
      on_failure: block

    L4:
      name: "集成验证"
      timeout: 30m
      trigger: L3-pass
      steps:
        - e2e-test
        - contract-test
        - performance-baseline
        - ac-mapping
      on_failure: block

    L5:
      name: "环境晋升"
      trigger: merge-to-main
      steps:
        - staging-deploy
        - smoke-test
        - canary:
            - 5%
            - 25%
            - 50%
            - 100%
      on_failure: rollback

  auto_rollback:
    conditions:
      - error_rate > 5%   # 5 分钟窗口
      - p99_latency > baseline * 2
      - health_check_failures >= 3
      - business_metric_drop > 10%
```

---

## 第 7 章：Pipeline 度量与持续改进

### 7.1 Pipeline 核心指标

| 指标 | 计算方式 | 目标 | 告警阈值 |
|------|---------|:----:|---------|
| **Pipeline 通过率** | 全绿运行次数 / 总运行次数 | ≥ 70% | < 50% |
| **平均 Pipeline 时长** | 从 L1 到 L5 完成的总时长 | < 45min | > 60min |
| **L1 失败率** | L1 阻断次数 / 总运行次数 | < 10% | > 20% |
| **L2 失败率** | L2 阻断次数 / 总运行次数 | < 15% | > 25% |
| **L3 幻觉检出率** | L3 检出幻觉 PR 数 / AI PR 总数 | 2-5% | > 10% |
| **L4 AC 覆盖率** | AC 覆盖率 100% 的 PR 数 / 总 PR 数 | ≥ 95% | < 85% |
| **L5 回滚率** | 触发回滚次数 / 部署次数 | < 5% | > 10% |
| **Flaky Test 率** | 不稳定测试数 / 总测试数 | < 1% | > 3% |

### 7.2 Pipeline 改进规则

| 触发条件 | 动作 |
|---------|------|
| Pipeline 通过率 < 50% 连续 1 周 | 分析 Top 3 失败原因，针对性修复 |
| 同一检查项连续失败 3 次 | 检查项本身可能有问题，需要审查 |
| L3 幻觉检出率 > 10% | 触发 AI 质量降级（01-core-specification.md 2.5） |
| L5 回滚率 > 10% | 降低自治等级，增加人工审批 |
| Pipeline 时长 > 60min | 分析最慢阶段，优化或并行化 |

---

## 附录：Pipeline 状态与 Spec 状态联动

| Pipeline 结果 | Spec 状态变更 |
|--------------|--------------|
| 全绿通过 | `in-progress` → `done` |
| L1-L2 阻断 | `in-progress` → 不变，通知 AI 修复 |
| L3 幻觉阻断 | `in-progress` → 不变，标记 `hallucination_detected` |
| L4 AC 未覆盖 | `in-progress` → 不变，标记 `ac_not_covered` |
| L5 回滚 | `done` → `in-progress`，重新进入修复循环 |
