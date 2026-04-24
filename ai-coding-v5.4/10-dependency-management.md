# AI Coding 规范 v5.5：依赖与供应链管理

> 版本：v5.5 | 2026-04-24
> 定位：大规模 Auto-Coding 场景下的依赖引入审批、漏洞修复、防膨胀、SBOM 与供应链安全
> 前置：[01-core-specification.md](01-core-specification.md) P11 证据链、[04-security-governance.md](04-security-governance.md) 安全底线、[06-cicd-pipeline.md](06-cicd-pipeline.md) L3 门禁

---

## 第 1 章：依赖引入审批

### 1.1 核心原则

**AI 不得自由添加新依赖。** 每次引入新的第三方库（直接依赖）必须经过审批链，理由：

- 每一个新依赖都是攻击面、维护成本和许可证风险的叠加
- AI 倾向于选择"最知名"的库而非"最适合"的库
- 依赖爆炸（Dependency Explosion）是大规模 Auto-Coding 最常见的退化模式

### 1.2 审批流程

```
AI 识别需要新依赖
        │
        ▼
┌──────────────────────────────────┐
│ 1. AI 编写依赖引入申请（DRF）      │
│    → 存放到 .gate/dep-requests/   │
└──────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────┐
│ 2. 自动审批检查（CI 自动执行）     │
│    · 标准库替代可行性              │
│    · 许可证兼容性                  │
│    · 已知漏洞检查                  │
│    · 包大小与传递依赖数             │
│    · 维护活跃度评分                │
└──────────────────────────────────┘
        │
     ┌──┴──┐
    通过    拒绝 → AI 必须使用替代方案
        │
        ▼
┌──────────────────────────────────┐
│ 3. 人工审批（仅当自动审批通过时）   │
│    · 架构评审：是否符合架构方向      │
│    · 安全评审：供应链风险评估        │
│    → 审批结果记录到 DRF             │
└──────────────────────────────────┘
        │
        ▼
  合并到 allowlist → AI 可自动使用该依赖
```

### 1.3 依赖引入申请表（DRF — Dependency Request Form）

AI 在添加新依赖前，必须在 PR 中填写：

| 字段 | 说明 | 示例 |
|------|------|------|
| `package_name` | 完整包名 | `lodash` |
| `version` | 精确版本或 semver 范围 | `^4.17.21` |
| `purpose` | 为什么需要这个包 | 字符串去抖，用于事件处理 |
| `stdlib_alternative` | 标准库是否可替代 | 否，标准库无 debounce |
| `license` | 许可证类型 | MIT |
| `transitive_deps` | 传递依赖数量 | 0（零依赖） |
| `bundle_size` | 打包后大小估算 | ~16KB（tree-shaken） |
| `maintenance_score` | 最近 6 个月提交活跃度 | 高/中/低 |
| `known_vulnerabilities` | 当前已知漏洞数 | 0 |
| `removal_plan` | 何时/如何移除 | 不再需要时立即移除 |

### 1.4 依赖白名单机制

```yaml
# .omc/dependency-allowlist.yaml
# 只有在此白名单中的直接依赖才可被 AI 引入
version: 1
last_reviewed: 2026-04-18
packages:
  # 格式：包名: 批准原因
  express: "标准 Web 框架，项目核心依赖"
  typescript: "语言层，必须"
  zod: "运行时类型验证，Spec 验证层使用"
  # ...
blocked:
  - request: "AI 尝试引入 axios"
    reason: "项目已有 fetch 封装，无需额外 HTTP 客户端"
    decision: rejected
    reviewed_by: human-reviewer
```

**规则**：
- AI 首次遇到不在白名单中的依赖时，不得自动 `npm install`/`pip install`/`go get`
- AI 必须创建 DRF 并提交 PR，由人类审批
- 已批准的依赖自动加入白名单，后续 AI 可直接使用
- 白名单必须由人类维护，AI 无权直接修改

---

## 第 2 章：漏洞修复 SLA

### 2.1 漏洞分级与修复时间线

| 严重级别 | CVSS 评分 | 修复 SLA | 自动修复 | 超时动作 |
|---------|----------|---------|---------|---------|
| **CRITICAL** | ≥ 9.0 | **4 小时** | AI 自动生成修复 PR，标记 `auto-merge-critical` | 阻断 CI，暂停 L3/L4 自主开发 |
| **HIGH** | 7.0–8.9 | **24 小时** | AI 自动生成修复 PR，标记 `auto-merge-high` | 告警到安全通道，降级 L2 |
| **MEDIUM** | 4.0–6.9 | **7 天** | AI 生成修复 PR，人工审查后合并 | 纳入下个迭代修复计划 |
| **LOW** | < 4.0 | **30 天** | 纳入 backlog，定期批量处理 | 无 |

### 2.2 CRITICAL 漏洞应急流程

```
漏洞公告（NVD / GitHub Advisory / 上游通知）
        │
        ▼
┌──────────────────────────────┐
│ 1. 自动识别受影响依赖版本       │
│    → npm audit / pip-audit    │
│    → go list -m -json         │
└──────────────────────────────┘
        │
        ▼
┌──────────────────────────────┐
│ 2. AI 生成修复 PR              │
│    → 升级到安全版本             │
│    → 运行完整回归测试           │
│    → 附加漏洞信息到 PR 描述     │
└──────────────────────────────┘
        │
        ▼
┌──────────────────────────────┐
│ 3. 快速审批通道                │
│    · 仅升级版本 = 自动合并      │
│    · 有 breaking change = 人工│
└──────────────────────────────┘
        │
        ▼
  合并 → L0-L5 Pipeline 全绿 → 部署
```

### 2.3 自动修复规则

| 条件 | 自动合并？ | 说明 |
|------|:---------:|------|
| 仅补丁版本升级（1.2.3 → 1.2.4） | **是** | semver patch 升级，预期向后兼容 |
| 小版本升级（1.2.x → 1.3.x）无 breaking change | **是** | CI 回归全绿后自动合并 |
| 大版本升级（1.x → 2.x） | 否 | 需要人工审查 breaking change |
| 修复引入代码变更 > 20 行 | 否 | 可能引入新问题 |
| 漏洞有已知 PoC 在野利用 | **是** | CRITICAL 级别，加速合并 |

### 2.4 漏洞扫描频率

| 扫描方式 | 触发时机 | 工具 |
|---------|---------|------|
| **每次 PR** | PR 创建 / push | `npm audit` / `pip-audit` / `cargo audit` / `govulncheck` |
| **每日定时** | CI 定时任务（凌晨） | GitHub Dependabot / Renovate |
| **每次构建** | CI Pipeline L3 层 | `osv-scanner`（跨语言统一扫描） |
| **实时订阅** | NVD / 上游安全公告 Webhook | 推送式告警 |

---

## 第 3 章：Typosquatting 自动检测

### 3.1 什么是 Typosquatting

攻击者注册与合法包名极度相似的恶意包（如 `reactt` 替代 `react`、`lodahs` 替代 `lodash`），等待 AI 或开发者拼写错误时自动安装。

### 3.2 检测规则

| 检测类型 | 规则 | 示例 |
|---------|------|------|
| **编辑距离** | 与白名单中包名的 Levenshtein 距离 ≤ 2 | `expresss` vs `express`（距离 1） |
| **字符交换** | 相邻字符交换 | `lodahs` vs `lodash` |
| **重复字符** | 单字符重复 | `reactt` vs `react` |
| **遗漏字符** | 缺少字符 | `expres` vs `express` |
| **替换字符** | 相似字符替换 | `iodash` vs `lodash`（l → i） |
| **命名空间欺骗** | 相似 scope 名 | `@types/expresss` vs `@types/express` |
| **大小写混淆** | 仅大小写不同（部分注册表区分大小写） | `Lodash` vs `lodash` |

### 3.3 防御机制

```
AI 请求安装新包
        │
        ▼
┌──────────────────────────────────┐
│ Typosquatting 检测引擎             │
│                                  │
│ 1. 计算与 allowlist 包的编辑距离   │
│ 2. 检查常见混淆模式                │
│ 3. 验证包注册表元数据              │
│    · 创建时间（新包 = 高风险）      │
│    · 下载量（极低 = 高风险）        │
│    · 发布者历史                   │
│ 4. 与热门包名做模糊匹配            │
└──────────────────────────────────┘
        │
   ┌────┴────┐
  安全      可疑
   │        │
   ▼        ▼
 继续     阻断 → 告警
           │
           ▼
    提示："是否意图安装 X？"
    AI 必须确认或修正
```

### 3.4 实施实现

```bash
# pre-commit hook: typosquatting 检测脚本
# 解析 package.json / requirements.txt / go.mod 中的新增依赖
# 对每个新增依赖执行检测

# 检测命令示例（npm）：
npx package-name-squat-check

# 检测命令示例（Python）：
pip check  # 部分检测
# 自定义脚本比对 PyPI 热门包名

# 检测命令示例（Go）：
# go.mod 解析 + 与标准库/官方库名比对
```

**阻断条件**：当检测到可疑包名时，pre-commit hook 必须阻断提交，并提示：
```
[SQUAT-DETECT] 可疑的包名: "lodahs"
  → 是否与 "lodash" 相似？（编辑距离: 1）
  → 请确认拼写或手动审批：DRF_SQUAT_{timestamp}
```

---

## 第 4 章：依赖升级自动化

### 4.1 自动化升级工具

| 工具 | 适用生态 | 配置方式 |
|------|---------|---------|
| **Renovate** | npm, pip, Go, Docker, GitHub Actions | `renovate.json` |
| **Dependabot** | GitHub 原生支持 | `.github/dependabot.yml` |
| **pip-tools** | Python | `requirements.in` → `requirements.txt` |
| **Go modules** | Go | `go get -u` + `go mod tidy` |

### 4.2 自动合并规则

```yaml
# .github/dependabot.yml 示例
version: 2
updates:
  # 生产依赖：仅安全补丁自动合并
  - package-ecosystem: "npm"
    directory: "/"
    schedule: { interval: "weekly" }
    open-pull-requests-limit: 10
    # 自动合并规则
    automerge: true
    automerge_type: "pr"
    # 语义化版本限制
    versioning-strategy: "increase"
    # 仅允许 patch 和 minor 自动合并
    allowed-updates:
      - update-type: "security"
      - update-type: "version-update:semver-patch"
    # major 版本升级必须人工审查
    reviewers: ["team-lead"]
    labels: ["dependencies"]

  # 开发依赖：可更宽松自动合并
  - package-ecosystem: "npm"
    directory: "/"
    schedule: { interval: "weekly" }
    target-branch: "main"
    # devDependencies 允许 minor 自动合并
    allow:
      - dependency-type: "development"
```

### 4.3 自动合并决策树

```
依赖升级 PR
        │
        ▼
  变更类型？
  ├── 安全补丁（CVE 修复）
  │   └── CI 全绿 → 自动合并（所有级别）
  ├── Patch 版本（1.2.3 → 1.2.4）
  │   └── CI 全绿 → 自动合并
  ├── Minor 版本（1.2.x → 1.3.x）
  │   ├── 生产依赖 → CI 全绿 → 自动合并
  │   └── 开发依赖 → CI 全绿 → 自动合并
  └── Major 版本（1.x → 2.x）
      └── 必须人工审查 → 不自动合并
```

### 4.4 AI 夜间升级任务

在 L3/L4 自治等级下，配置 AI 定时任务：

```yaml
# .omc/automated-tasks.yaml
dependency-upgrade:
  schedule: "0 2 * * 1"  # 每周一凌晨 2:00
  actions:
    - run: "npm outdated --json > /tmp/outdated.json"
    - run: "npm audit --json > /tmp/audit.json"
    - generate_prs: true
    - max_prs_per_run: 5
    - auto_merge_rules:
        patch: true
        minor: true
        security_critical: true
        major: false  # 必须人工
```

---

## 第 5 章：依赖爆炸预防

### 5.1 什么是依赖爆炸

AI 在实现功能时倾向于"每个问题找一个包"，导致项目依赖数量失控增长。典型症状：

| 症状 | 阈值 |
|------|------|
| 直接依赖数量 | > 30 个 |
| 总依赖树（含传递） | > 500 个（Node.js）/ > 100 个（Go） |
| `node_modules` / `.cache` 大小 | > 500MB |
| 单一功能引入整个框架 | 如为 1 个函数引入 50MB 框架 |

### 5.2 依赖预算

每个项目在架构设计阶段必须定义**依赖预算**：

```yaml
# .omc/dependency-budget.yaml
budget:
  max_direct_dependencies: 30       # 直接依赖上限
  max_total_tree_size: 500          # 传递依赖总数上限
  max_bundle_size_increase: "50KB"  # 每次引入的包大小增量上限
  max_install_size: "500MB"         # 安装后目录大小上限

  # 按类别细分预算
  categories:
    web-framework: 2                # Web 框架最多 2 个
    testing: 5                      # 测试工具最多 5 个
    utilities: 10                   # 工具库最多 10 个
    database: 3                     # 数据库驱动最多 3 个
    security: 3                     # 安全库最多 3 个

  # 硬限制
  hard_limits:
    - no_duplicate_functionality: true   # 禁止功能重叠的包（如 lodash + underscore）
    - prefer_stdlib: true                # 优先使用标准库
    - max_transitive_depth: 10           # 传递依赖深度上限
```

### 5.3 AI 依赖选择优先级

```
AI 需要实现某功能
        │
        ▼
  ┌─────────────────────────────┐
  │ 1. 标准库能否实现？            │  ✅ 必须优先
  │    YES → 使用标准库           │
  │    NO  → 继续                │
  └─────────────────────────────┘
        │
        ▼
  ┌─────────────────────────────┐
  │ 2. 已引入的依赖能否实现？       │  ✅ 复用已有
  │    YES → 使用已有依赖         │
  │    NO  → 继续                │
  └─────────────────────────────┘
        │
        ▼
  ┌─────────────────────────────┐
  │ 3. 轻量替代（< 50 行自行实现） │  ✅ 自己写更轻
  │    YES → 自行实现             │
  │    NO  → 继续                │
  └─────────────────────────────┘
        │
        ▼
  ┌─────────────────────────────┐
  │ 4. 提交 DRF 申请新依赖         │  ⚠️  最后选项
  │    → 走 1.2 审批流程          │
  └─────────────────────────────┘
```

### 5.4 依赖膨胀 CI 门禁

在 CI Pipeline L3 层添加依赖检查：

```yaml
# CI 配置示例
dependency-budget-check:
  stage: L3
  steps:
    # 检查直接依赖数量
    - name: "Check dependency count"
      run: |
        DIRECT=$(npm ls --depth=0 --prod | grep -c '@')
        if [ "$DIRECT" -gt 30 ]; then
          echo "::error::直接依赖数量 $DIRECT 超过预算上限 30"
          exit 1
        fi

    # 检查总依赖树大小
    - name: "Check total tree size"
      run: |
        TOTAL=$(npm ls --prod --json | jq '.dependencies | keys | length')
        if [ "$TOTAL" -gt 500 ]; then
          echo "::error::总依赖树大小 $TOTAL 超过预算上限 500"
          exit 1
        fi

    # 检查功能重叠
    - name: "Check duplicate functionality"
      run: |
        # 检查是否存在功能重叠的包
        if npm ls lodash > /dev/null 2>&1 && npm ls underscore > /dev/null 2>&1; then
          echo "::error::lodash 和 underscore 功能重叠，请移除其一"
          exit 1
        fi

    # 检查 node_modules 大小
    - name: "Check install size"
      run: |
        SIZE=$(du -sm node_modules | cut -f1)
        if [ "$SIZE" -gt 500 ]; then
          echo "::warning::node_modules 大小 ${SIZE}MB 接近预算上限 500MB"
        fi
```

---

## 第 6 章：SBOM（软件物料清单）

### 6.1 为什么要 SBOM

- 每个 AI 生成的 PR 都可能引入新的依赖版本
- 没有 SBOM，无法回答"我们到底用了什么"这个基本问题
- 安全审计、许可证合规、漏洞影响分析都依赖 SBOM

### 6.2 SBOM 生成规范

| 属性 | 要求 |
|------|------|
| **格式** | CycloneDX（推荐）或 SPDX |
| **生成时机** | 每次构建（CI Pipeline L1 层） |
| **存储位置** | `.gate/sbom/{build-id}.json` |
| **版本** | 随每次发布版本递增 |
| **范围** | 生产依赖 + 传递依赖 |

### 6.3 生成命令

```bash
# Node.js — CycloneDX
npx @cyclonedx/cyclonedx-npm --output-file .gate/sbom/sbom-cdx.json

# Python — CycloneDX
cyclonedx-py -i -o .gate/sbom/sbom-cdx.json

# Go — CycloneDX
cyclonedx-gomod -output .gate/sbom/sbom-cdx.json

# 多语言统一 — syft（生成 SPDX）
syft . --output spdx-json=.gate/sbom/sbom-spdx.json
```

### 6.4 SBOM 内容要求

生成的 SBOM 必须包含：

| 字段 | 说明 |
|------|------|
| `metadata.timestamp` | 生成时间 |
| `metadata.component` | 项目名称和版本 |
| `components[].name` | 每个依赖包名 |
| `components[].version` | 精确版本号 |
| `components[].purl` | Package URL（标准化标识） |
| `components[].licenses[]` | 许可证列表 |
| `components[].hashes[]` | 文件完整性校验值 |
| `dependencies` | 依赖关系图 |
| `vulnerabilities[]` | 已知漏洞引用 |

### 6.5 SBOM 消费场景

| 场景 | SBOM 用途 |
|------|----------|
| **漏洞影响分析** | 新 CVE 发布时，快速查询是否受影响 |
| **许可证审计** | 检查是否存在 GPL 等传染性许可证 |
| **合规报告** | 向客户/监管提供供应链透明度 |
| **依赖升级决策** | 了解当前版本与目标版本的差距 |
| **事故响应** | 供应链攻击时快速定位受影响组件 |

### 6.6 SBOM CI 集成

```yaml
# CI Pipeline L1 层
sbom-generation:
  stage: L1
  steps:
    - name: "Generate SBOM"
      run: "syft . --output spdx-json=.gate/sbom/sbom-spdx.json"
    - name: "Validate SBOM"
      run: "cat .gate/sbom/sbom-spdx.json | jq '.spdxVersion' | grep -q 'SPDX'"
    - name: "Upload SBOM as artifact"
      uses: actions/upload-artifact
      with: { name: "sbom", path: ".gate/sbom/" }
    - name: "Diff against previous SBOM"
      run: |
        if [ -f .gate/sbom/previous-sbom.json ]; then
          diff <(jq '.packages[].name' .gate/sbom/previous-sbom.json | sort) \
               <(jq '.packages[].name' .gate/sbom/sbom-spdx.json | sort) || true
        fi
```

---

## 第 7 章：供应链安全

### 7.1 威胁模型

| 威胁 | 攻击向量 | 影响 |
|------|---------|------|
| **恶意包注入** | Typosquatting、依赖混淆（dependency confusion） | 代码执行、数据外泄 |
| **上游仓库劫持** | 维护者账号被盗、DNS 劫持 | 全量用户受影响 |
| **供应链攻击** | 流行库被植入后门（如 event-stream 事件） | 下游全部感染 |
| **CI/CD 注入** | 恶意 GitHub Actions workflow、恶意的 build script | 构建过程被篡改 |
| **签名伪造** | 伪造的发布签名 | 绕过完整性检查 |
| **生命周期脚本攻击** | `preinstall`/`postinstall` 脚本执行恶意代码 | 安装即感染 |

### 7.2 包完整性验证

#### 7.2.1 锁文件强制要求

| 生态 | 锁文件 | 强制要求 |
|------|--------|---------|
| Node.js | `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` | **必须提交到 Git** |
| Python | `requirements.txt`（精确版本）/ `Pipfile.lock` / `poetry.lock` | **必须提交到 Git** |
| Go | `go.sum` | **必须提交到 Git** |
| Rust | `Cargo.lock` | **必须提交到 Git**（binary 项目） |

**AI 规则**：AI 修改依赖时，锁文件必须同步更新。锁文件变更必须由 CI 验证完整性。

#### 7.2.2 校验和验证

```bash
# Node.js — 验证锁文件完整性
npm ci --ignore-scripts    # 使用锁文件，不执行安装脚本

# Python — 验证哈希
pip install --require-hashes -r requirements.txt

# Go — 验证 go.sum
go mod verify
```

#### 7.2.3 安装脚本防护

```yaml
# .npmrc — 禁止执行安装脚本
ignore-scripts=true

# 或选择性允许
scripts-allowed=
```

**规则**：生产环境默认禁止执行 `preinstall`/`postinstall`/`prepublish` 脚本。如需执行，必须经过人工审批并审查脚本内容。

### 7.3 签名验证

| 机制 | 说明 | 实施方式 |
|------|------|---------|
| **NPM provenance** | 验证包由声明的 CI 构建 | `npm install` 自动验证 |
| **Sigstore/cosign** | 容器镜像和发布签名 | `cosign verify` |
| **GPG 发布签名** | Go/Rust 等生态的标签签名 | `git tag -v` |
| **SLSA 框架** | 供应链级别的安全等级 | 构建系统生成 attestation |

### 7.4 依赖混淆防御

**内部包命名规范**：

```yaml
# .npmrc — 作用域路由
@mycompany:registry=https://npm.mycompany.com/
# 所有 @mycompany/* 包只从内部注册表拉取
# 防止攻击者在公共 npm 发布同名包
```

**规则**：
- 所有内部包必须使用作用域前缀（如 `@mycompany/`）
- 配置包管理器优先从内部注册表拉取作用域包
- CI 验证内部包不存在于公共注册表

### 7.5 供应链 CI 门禁

在 CI Pipeline L3 层集成供应链安全检查：

```yaml
supply-chain-security:
  stage: L3
  steps:
    # 1. 依赖完整性
    - name: "Lock file integrity"
      run: "npm ci --ignore-scripts"

    # 2. 漏洞扫描
    - name: "Vulnerability scan"
      run: "osv-scanner --lockfile=package-lock.json"

    # 3. 许可证检查
    - name: "License compliance"
      run: "npx license-checker --failOn 'GPL;AGPL;SSPL'"

    # 4. 安装脚本检查
    - name: "Install script audit"
      run: |
        SCRIPTS=$(node -e "
          const pkg = require('./package.json');
          const scripts = Object.keys(pkg.scripts || {})
            .filter(s => s.includes('install') || s.includes('post'));
          if (scripts.length > 0) {
            console.error('WARNING: install scripts found:', scripts.join(', '));
            process.exit(1);
          }
        ")

    # 5. SBOM 生成与比对
    - name: "Generate and diff SBOM"
      run: |
        syft . --output spdx-json=.gate/sbom/sbom-current.json
        # 比对上一次，检测依赖变更

    # 6. Typosquatting 检查
    - name: "Typosquatting check"
      run: "./scripts/check-typosquatting.sh"

    # 7. 依赖预算检查
    - name: "Dependency budget check"
      run: "./scripts/check-dep-budget.sh"
```

---

## 第 8 章：AI 专属规则

### 8.1 依赖选择优先级（AI 必须遵守）

```
P24 — 标准库优先（新增原则）

当 AI 实现功能时，必须按以下顺序选择实现方式：

1. 标准库（stdlib）  → 零依赖、零风险、零维护成本
2. 已有依赖         → 不增加依赖数量
3. 轻量自研（< 50 行）→ 可控、可审查
4. 新依赖（走 DRF）  → 最后选项，需审批
```

### 8.2 AI 依赖引入禁止项

| 禁止行为 | 原因 |
|---------|------|
| 引入功能重叠的包（如 `moment` + `dayjs`） | 增加包体积和复杂度 |
| 引入已废弃的包（> 12 个月无更新） | 安全风险、无维护 |
| 引入许可证不兼容的包（GPL 在 MIT 项目中） | 法律风险 |
| 引入有未修复 CRITICAL/HIGH 漏洞的包 | 直接安全风险 |
| 引入传递依赖 > 50 个的包 | 供应链风险失控 |
| 为简单功能引入重量级框架 | 违反 P8 最小批量精神 |
| 使用 `*` 或 `latest` 作为版本号 | 构建不可重现 |
| 修改锁文件但不修改依赖声明文件 | 锁文件与声明不一致 |

### 8.3 AI 依赖自审清单

每次 AI 涉及依赖变更时，必须自审并记录到 PR 描述：

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | 标准库能否实现？ | [ ] |
| 2 | 已有依赖能否复用？ | [ ] |
| 3 | 自行实现是否更轻量（< 50 行）？ | [ ] |
| 4 | 许可证与项目兼容？ | [ ] |
| 5 | 无 CRITICAL/HIGH 漏洞？ | [ ] |
| 6 | 传递依赖数量合理（< 50）？ | [ ] |
| 7 | 包维护活跃度正常（6 月内有提交）？ | [ ] |
| 8 | 版本号使用精确范围（非 `*`/`latest`）？ | [ ] |
| 9 | 锁文件已同步更新？ | [ ] |
| 10 | DRF 已填写（仅新增依赖时）？ | [ ] |

### 8.4 AI 依赖使用日志

AI 每次引入、升级或移除依赖时，必须记录到 `.gate/dep-log.md`：

```markdown
# Dependency Change Log

## 2026-04-18

| 时间 | 操作 | 包名 | 版本 | 原因 | PR |
|------|------|------|------|------|----|
| 14:30 | ADD | zod | 3.22.4 | Spec 验证层需要运行时类型检查 | #1234 |
| 14:35 | UPD | express | 4.18.2→4.19.0 | 安全补丁（CVE-2024-XXXX） | #1235 |
| 15:00 | REM | moment | 2.30.1 | 已迁移到 dayjs，消除冗余 | #1236 |
```

---

## 附录 A：原则编号

本规范引入新原则 **P24**，补充到 `01-core-specification.md` 的原则体系中：

| # | 原则 | 说明 |
|---|------|------|
| **P24** | **标准库优先** | AI 引入新依赖前必须证明标准库无法实现，且已有依赖无法复用 |

**P24 违反后果**：

| 自治等级 | 后果 |
|---------|------|
| L1 | 人工审查时直接驳回 |
| L2 | CI 阻断 + 要求补充 DRF |
| L3 | CI 阻断 + 告警 |
| L4 | CI 阻断 + 自动回滚 |

---

## 附录 B：工具速查

| 用途 | Node.js | Python | Go | Rust | 跨语言 |
|------|---------|--------|----|----|--------|
| 漏洞扫描 | `npm audit` | `pip-audit` | `govulncheck` | `cargo audit` | `osv-scanner` |
| 锁文件 | `package-lock.json` | `poetry.lock` | `go.sum` | `Cargo.lock` | — |
| SBOM | `cyclonedx-npm` | `cyclonedx-py` | `cyclonedx-gomod` | `cyclonedx-rust` | `syft` |
| 许可证 | `license-checker` | `pip-licenses` | — | `cargo-deny` | `license_finder` |
| Typosquatting | `npm-audit` + 自定义 | `safety` + 自定义 | 自定义 | — | 自定义脚本 |
| 升级自动化 | Renovate / Dependabot | Renovate / pip-tools | `go get -u` | `cargo update` | Renovate |

---

## 附录 C：与其他文档的交叉引用

| 交叉引用 | 关联内容 |
|---------|---------|
| [01-core-specification.md](01-core-specification.md) | P5（密钥不入代码）、P8（最小批量）、P11（证据链）、P24（标准库优先） |
| [04-security-governance.md](04-security-governance.md) | 安全底线、应急响应、审计检查点 |
| [06-cicd-pipeline.md](06-cicd-pipeline.md) | L3 质量审查层（依赖检查、SBOM 生成、漏洞扫描） |
| [07-anti-hallucination.md](07-anti-hallucination.md) | E01-E06（存在性幻觉：AI 虚构的依赖/包名/版本） |
