# AI Coding 规范 v6.0：CI/CD Pipeline

> 版本：v6.0 | 2026-05-02
> 定位：分层质量门禁 —— AI 代码进入生产的唯一通道
> 前置：[01-core.md](01-core.md)（TDD、幻觉防护）、[03-structured-constraints.md](03-structured-constraints.md)（SCFS 约束）

---

## 第 1 章：Pipeline 分层架构

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

**设计原则**：
- 速检优先：每层必须在时间盒内完成
- 快速失败：低层级先运行，失败则跳过后续
- 分层隔离：每层有独立的通过/失败/警告状态
- AI 增强：AI 生成代码在 L3 有额外幻觉检测
- 可追溯：每层结果写入 `.gate/` 目录

**Process Profile 集成**：S 档仅执行 L0-L2，M 档 L0-L3，L/XL 档 L0-L5。

---

## 第 2 章：各 Layer 详细定义

### 2.1 L0 — 即时反馈层（<30s）

pre-commit hook 自动执行。

| 检查项 | 阻断？ | AI 增强 |
|--------|:------:|---------|
| 代码格式化 | 警告 | 自动修复后重新提交 |
| 密钥扫描（gitleaks） | **是** | 违反 P5 直接阻断 |
| 提交消息规范 | 警告 | 检查 `ai-generated: true` 标记 |
| 文件大小（>200 行） | 警告 | 违反 P8 |
| 禁止文件（.env、secrets/） | **是** | 检查 AI 是否生成敏感文件 |
| pre-send 数据分级扫描 | **是** | P10 数据分级 |

AI 提交消息必须包含：
```
ai-generated: true
spec: F{NNN}
autonomy-level: L{N}
```

### 2.2 L1 — 编译验证层（<2min）

| 检查项 | 阻断？ | 说明 |
|--------|:------:|------|
| 编译/构建 | **是** | 任何编译错误阻断 |
| 类型检查 | **是** | AI 倾向于生成"看起来正确但类型不匹配"的代码 |
| Import 检查 | **是** | 验证存在性幻觉 |
| 循环依赖检测 | **是** | AI 可能无意中引入循环依赖 |

### 2.3 L2 — 测试验证层（<10min）

| 检查项 | 阻断？ | 说明 |
|--------|:------:|------|
| 单元测试 | **是** | 全部通过 |
| 集成测试 | **是** | 使用真实数据库容器 |
| TDD 合规检查 | **是** | 测试 commit 在实现 commit 之前 |
| TDD Red 阶段验证 | **是** | 检测 TDD 造假 |
| AC 覆盖率 | **是** | 100% 覆盖，否则未完成 |
| 包覆盖率 | 警告 | 不得较基线下降 > 5% |

AI 特有规则：
- 检查断言是否"过于宽松"（如 `assert(true)`）
- AI 生成的 Mock 必须审查合理性

### 2.4 L3 — 质量审查层（<15min）

| 检查项 | 阻断？ | 说明 |
|--------|:------:|------|
| Lint | **是** | 错误级别阻断 |
| SAST 扫描 | **是** | 安全漏洞阻断 |
| AI Reviewer（A01-A09 检查） | **是** | 必须使用不同 API 会话 |
| 幻觉检测扫描 | **是** | API 存在性 + 符号解析 + 依赖验证 |
| 技术债扫描 | 警告 | 代码异味不得增长 |
| 复杂度检查 | **是** | 圈复杂度 > 20 阻断 |
| 依赖漏洞扫描 | **是** | 高严重级别阻断 |

AI Reviewer 规则：必须使用与代码生成**不同的 API 会话**。置信度 < 0.7 标记"需人工重点审查"。

### 2.5 L4 — 集成验证层（<30min）

| 检查项 | 阻断？ | 说明 |
|--------|:------:|------|
| E2E 测试 | **是** | 覆盖关键用户旅程 |
| API 契约测试 | **是** | 验证 API 符合 OpenAPI Spec |
| 数据库迁移测试 | **是** | 干净 DB 上执行迁移 + 回滚 |
| 性能基线检查 | **是** | 回归 >10% 阻断 |
| 安全渗透扫描（DAST） | **是** | 动态安全测试 |
| AC 映射验证 | **是** | 对照 Spec 验证每个验收标准 |

### 2.6 L5 — 环境晋升层

**触发时机**：PR 合并到 main 后自动触发。

**部署策略**：金丝雀发布（5%→25%→50%→100%）为默认。

**自动回滚触发条件**（任一满足）：
- 错误率 > 5%（5 分钟窗口）
- P99 延迟 > 基线×2（5 分钟窗口）
- 关键业务指标下降 > 10%
- 健康检查连续 3 次失败

---

## 第 3 章：Self-Correction 策略

| 层级 | AI 可自动修复？ | 最大轮次 | 转人工条件 |
|------|:---:|:--------:|-----------|
| L0 | **是** | 1 轮 | 修复后仍失败 |
| L1 | **是** | 2 轮 | 架构级编译错误 |
| L2 | **是** | 3 轮 | 测试逻辑错误、AC 无法映射 |
| L3 lint | **是** | 2 轮 | 架构级 lint |
| L3 SAST | **否** | — | 安全漏洞必须人工确认 |
| L3 幻觉 | **是** | 3 轮 | 核心逻辑幻觉 |
| L4 E2E | **是** | 3 轮 | 端到端功能缺失 |
| L4 性能 | **否** | — | 需要架构级分析 |

**约束**：
- 禁止修改测试断言让测试通过
- 禁止删除失败测试或添加 @skip
- 安全漏洞不可自修（AI 只生成修复建议）
- 性能退化不可自修（必须人工分析）

---

## 第 4 章：Pipeline 与自治等级

| 检查项 | L1 | L2 | L3 | L4 |
|--------|----|----|----|----|
| L0-L4 | 全部运行 | 全部运行 | 全部运行 | 全部运行 |
| 人工审查 | **必须** | **必须** | **必须** | 抽样 ≥10% |
| L5 金丝雀 | 人工审批每阶段 | 人工审批 100% | 自动到 50% | 全自动 |
| 自动回滚 | 人工决策 | 人工决策 | 自动 | 自动 |

DCP 与 Pipeline 的关系：DCP 是"能不能做"的决策点，Pipeline 是"做得对不对"的验证链。

---

## 第 5 章：Kill Switch 与自修复 CI

### 5.1 Kill Switch

每个端点必须有 Kill Switch。当检测到异常时自动关闭：

```yaml
kill-switch:
  conditions:
    - error_rate > 10%       # 5 分钟窗口
    - p99_latency > 5s       # 持续 3 分钟
    - data_corruption: true   # 数据完整性检测失败
  actions:
    - disable_endpoint       # 禁用该端点
    - route_to_fallback      # 路由到降级版本
    - alert_oncall           # 通知值班
```

### 5.2 自修复 CI

CI Pipeline 在检测到可预测的失败模式时自动修复：
- L0 格式化失败 → 自动修复后重新提交
- L1 import 缺失 → 自动添加 import
- L2 flaky test → 标记 flaky 并重跑

自修复记录写入 `.gate/ci-self-heal.json`。

---

## 第 6 章：增量验证（S3/S4 专用）

> S3/S4 级别下，全量测试成本过高。增量测试由依赖图谱驱动，只运行受影响的测试。

详见 [01-core.md §4.2](01-core.md#42-核心原则在不同-scale-下的执行机制)

### 7.1 测试范围计算

```
变更文件 → 依赖图谱 → {
  直接受影响测试: import 变更文件的测试
  契约测试: affected_modules 的接口测试
  冒烟测试: 核心路径测试集（S4 强制）
}
```

### 7.2 增量测试规则

| 变更类型 | 测试范围 | 说明 |
|---------|---------|------|
| 函数内部逻辑修改 | 该函数的直接测试 | 最小范围 |
| 函数签名修改 | 直接测试 + 调用方测试 | 中范围 |
| API 端点修改 | 接口测试 + E2E 测试子集 | 中范围 |
| 数据库迁移 | 全量集成测试 | 不可增量 |
| 基础设施变更 | 全量冒烟测试 | 不可增量 |

### 7.3 与 L2 测试层的集成

CI Pipeline 的 L2 测试层支持两种模式：

```yaml
test_layer:
  mode: incremental    # full（默认）或 incremental
  smoke_tests:         # S4 强制执行的冒烟测试集
    - tests/smoke/
  contract_tests:      # 契约测试，跨模块变更时执行
    - tests/contracts/
  fallback:            # 增量测试失败后的回退策略
    - run_full_suite   # 跑全量
    - block_merge      # 阻断合并
```

### 7.4 不可妥协项

以下场景**必须跑全量测试**，不得增量：
- 数据库迁移（schema 变更影响全局）
- 认证/授权逻辑变更
- 核心基础设施变更（网络、存储、并发模型）
- S3/S4 中 `test_scope` 标记为 `full` 的 Contract

---

## 第 7 章：Pipeline 配置模板

```yaml
pipeline:
  layers:
    L0:
      timeout: 30s
      steps: [secret-scan, format-check]
    L1:
      timeout: 2m
      steps: [compile, type-check, import-verify]
    L2:
      timeout: 10m
      steps: [unit-test, integration-test, tdd-compliance]
    L3:
      timeout: 15m
      steps: [lint, sast, ai-reviewer, hallucination-scan]
    L4:
      timeout: 30m
      steps: [e2e-test, contract-test, performance-baseline]
    L5:
      steps: [staging-deploy, smoke-test, canary: [5%, 25%, 50%, 100%]]
  auto_rollback:
    conditions:
      - error_rate > 5%
      - p99_latency > baseline * 2
      - health_check_failures >= 3
```
