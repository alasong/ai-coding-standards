# AI Coding 规范 v5.5：性能基线与回归检测

> 版本：v5.5 | 2026-04-24
> 定位：大规模 Auto-Coding 的性能保障体系 — 性能预算、自动基准测试、CI 门禁、性能剖析、容量规划、压力测试、AI 特定规则
> 前置：[01-core-specification.md](01-core-specification.md) 第 2 章（TDD）、[06-cicd-pipeline.md](06-cicd-pipeline.md) 第 2 章（L4 集成验证层）

---

## 第 1 章：为什么需要性能基线规范

大规模 Auto-Coding = 每天数十至数百个 AI 生成的 PR。没有性能门禁意味着：

- AI 倾向于生成"功能正确但性能差"的代码（N+1 查询、O(n²) 循环、未索引数据库查询）
- 性能退化在 CI 中不可见，只在生产环境爆发
- L3/L4 自主模式下无人逐行审查性能问题
- 无法区分"可接受的性能波动"和"真正的性能退化"

**核心原则**：性能是功能的一部分。没有性能保障的"功能完成"不是真正的完成。每个 PR 必须证明它没有引入性能退化。

---

## 第 2 章：性能预算（Performance Budget）

### 2.1 预算定义

性能预算是对系统各项性能指标设定的上限值。预算不是"目标"，而是"天花板"——任何变更不得突破预算。

| 指标 | 定义 | 预算级别 | 说明 |
|------|------|---------|------|
| **P99 延迟** | 99% 请求的响应时间上限 | 核心 API ≤ 200ms，普通 API ≤ 500ms | 从用户点击到首字节（TTFB） |
| **P95 延迟** | 95% 请求的响应时间上限 | 核心 API ≤ 100ms，普通 API ≤ 250ms | 用于趋势分析和容量规划 |
| **内存占用** | 进程常驻内存（RSS）上限 | 微服务 ≤ 256MB，API Gateway ≤ 512MB | 不含 OS 缓存 |
| **CPU 使用率** | 峰值 CPU 占用率上限 | 常态 ≤ 60%，峰值 ≤ 80% | 1 分钟滑动窗口 |
| **带宽消耗** | 单请求最大响应体大小 | JSON API ≤ 1MB，文件下载按需 | 不含流式传输 |
| **数据库查询时间** | 单条 SQL 执行时间上限 | 查询 ≤ 50ms，写入 ≤ 100ms | 不含网络延迟 |
| **启动时间** | 服务冷启动到就绪的时间上限 | 微服务 ≤ 10s，CLI 工具 ≤ 2s | 用于弹性扩缩容评估 |
| **测试执行时间** | 全量测试套件执行时间上限 | 单元 ≤ 2min，集成 ≤ 10min，E2E ≤ 30min | Pipeline L1-L4 时间盒 |

### 2.2 预算分级

预算按服务关键程度分级，不得跨级降级：

| 级别 | 服务类型 | P99 延迟 | 内存上限 | CPU 峰值 | 适用场景 |
|------|---------|:--------:|:--------:|:--------:|---------|
| **Tier-0** | 认证、支付、核心交易 | ≤ 100ms | 512MB | 70% | 故障直接影响收入 |
| **Tier-1** | 用户管理、搜索、通知 | ≤ 200ms | 256MB | 80% | 故障影响用户体验 |
| **Tier-2** | 管理后台、报表、审计 | ≤ 500ms | 1GB | 90% | 内部工具，可容忍延迟 |
| **Tier-3** | 批处理、数据同步、清理 | ≤ 2s（单次） | 2GB | 95% | 后台任务，异步执行 |

### 2.3 预算分配规则

| 规则 | 说明 |
|------|------|
| **预算不可叠加** | 单个请求链路经过 3 个服务，总 P99 ≤ 300ms，不是每个服务各自 300ms |
| **预留 20% 余量** | 实际运行值不得超过预算的 80%，留 20% 给流量波动 |
| **预算外置** | 性能预算存储在 `.performance-budget.yaml`，不得硬编码在代码中 |
| **预算版本化** | 每次预算变更必须有 ADR（Architecture Decision Record） |
| **预算不可回退** | 预算只能收紧，不能放宽。放宽必须通过 DCP 审批 |

### 2.4 `.performance-budget.yaml` 模板

```yaml
# .performance-budget.yaml
# 性能预算定义文件 —— 单一信息源（P6）

version: 1.0
updated: 2026-04-18
approved_by: "@tech-lead"

services:
  auth-service:
    tier: Tier-0
    budget:
      p99_latency_ms: 100
      p95_latency_ms: 50
      memory_rss_mb: 512
      cpu_peak_percent: 70
      db_query_ms: 20

  user-service:
    tier: Tier-1
    budget:
      p99_latency_ms: 200
      p95_latency_ms: 100
      memory_rss_mb: 256
      cpu_peak_percent: 80
      db_query_ms: 50

  admin-portal:
    tier: Tier-2
    budget:
      p99_latency_ms: 500
      p95_latency_ms: 250
      memory_rss_mb: 1024
      cpu_peak_percent: 90

endpoints:
  POST /api/auth/login:
    service: auth-service
    p99_latency_ms: 150
    max_request_body_kb: 4
    max_response_body_kb: 2

  GET /api/users/{id}:
    service: user-service
    p99_latency_ms: 50
    max_response_body_kb: 8
    cache_ttl_s: 300

global:
  max_response_body_kb: 1024        # 1MB 全局上限
  max_startup_time_s: 10            # 冷启动上限
  max_test_duration_unit_s: 120     # 单元测试时间盒
  max_test_duration_integration_s: 600  # 集成测试时间盒
  max_test_duration_e2e_s: 1800     # E2E 测试时间盒
```

---

## 第 3 章：自动化基准测试（Automated Benchmarking）

### 3.1 基准测试类型

| 类型 | 目的 | 触发时机 | 工具 |
|------|------|---------|------|
| **微基准测试** | 单个函数/方法级别性能 | 每次 PR，仅测变更文件 | `go test -bench` / `pytest-benchmark` / `JMH` |
| **宏基准测试** | 端到端 API 级别性能 | L4 集成验证层 | `k6` / `wrk` / `vegeta` |
| **组件基准测试** | 数据库查询、缓存、消息队列 | L4 集成验证层 | `pgbench` / `redis-benchmark` / 自定义 |
| **前端基准测试** | 页面加载、渲染性能 | L4 集成验证层 | `lighthouse-ci` / `web-vitals` |

### 3.2 基准测试生成规则

```
Spec 中的非功能需求 → AI 生成对应的基准测试
```

| 规则 | 说明 |
|------|------|
| **从 Spec 生成** | Spec 中每个量化非功能需求必须有对应基准测试 |
| **先于实现** | 基准测试必须在性能优化实现之前提交（同 TDD 原则） |
| **可复现** | 基准测试必须在相同环境、相同数据量下可复现 |
| **独立运行** | 基准测试可独立运行，不依赖完整系统（微基准） |
| **数据量标注** | 每个基准测试必须标注测试数据量（小/中/大/超大） |

### 3.3 基准测试存储

```
benchmarks/
├── micro/                          # 微基准测试
│   ├── auth/
│   │   ├── password_hash_test.go
│   │   └── token_validate_test.go
│   └── user/
│       ├── profile_lookup_test.go
│       └── search_test.go
├── macro/                          # 宏基准测试
│   ├── login_flow.k6.js
│   ├── user_crud.k6.js
│   └── search_flow.k6.js
├── data/                           # 测试数据集
│   ├── small/                      # 1K 记录
│   ├── medium/                     # 100K 记录
│   └── large/                      # 10M 记录
│       └── generate.sh
└── results/                        # 基准测试结果（自动写入）
    ├── baseline/                   # 基线数据（main 分支）
    │   ├── 2026-04-18_micro.json
    │   └── 2026-04-18_macro.json
    └── pr/                         # PR 运行结果
        └── pr-123_micro.json
```

### 3.4 基准测试执行流程

```
1. PR 创建 → CI 识别变更文件
2. 查找匹配的基准测试文件（benchmarks/ 中对应路径）
3. 加载 baseline 结果（main 分支最近一次）
4. 执行基准测试（3 次取中位数）
5. 与 baseline 对比，生成差异报告
6. 写入 .gate/performance/pr-{NNN}_benchmark.json
7. 判定通过/失败/警告
```

**数据量分级规则**：

| 级别 | 记录数 | 用途 | 触发条件 |
|------|-------|------|---------|
| **Small** | 1K | 快速验证，每次 PR 必跑 | 所有 PR |
| **Medium** | 100K | 常规性能验证 | 变更涉及数据操作时 |
| **Large** | 10M | 极限性能验证 | 标记 `performance: large-dataset` 的 PR |

---

## 第 4 章：CI 中的性能门禁（Performance Gate）

### 4.1 性能门禁在 Pipeline 中的位置

性能门禁位于 **L4 集成验证层**，是 PR 合并前的最后一道性能关卡。

```
L0 → L1 → L2 → L3 → L4
                       ├── E2E 测试
                       ├── 契约测试
                       ├── 数据库迁移测试
                       ├── 【性能基线检查】← 本节定义
                       ├── 安全渗透扫描
                       └── AC 映射验证
```

### 4.2 性能门禁判定规则

| 检查项 | 通过条件 | 失败条件 | 警告条件 |
|--------|---------|---------|---------|
| **P99 延迟** | ≤ baseline × 1.05（5% 以内） | > baseline × 1.10（10% 以上） | baseline × 1.05 ~ 1.10 |
| **P95 延迟** | ≤ baseline × 1.05 | > baseline × 1.10 | baseline × 1.05 ~ 1.10 |
| **内存占用** | ≤ baseline + 5% | > baseline + 10% | baseline + 5% ~ 10% |
| **CPU 使用率** | ≤ baseline + 5% | > baseline + 15% | baseline + 5% ~ 15% |
| **预算合规** | 所有指标在预算内 | 任一指标超出预算 | — |
| **吞吐量** | ≥ baseline × 0.95 | < baseline × 0.90 | baseline × 0.90 ~ 0.95 |
| **错误率** | ≤ baseline + 0.1% | > baseline + 1% | baseline + 0.1% ~ 1% |

### 4.3 门禁执行策略

| PR 类型 | 基准测试范围 | 数据量级别 |
|---------|-------------|-----------|
| **Trivial**（文档、注释、格式化） | 跳过 | — |
| **Small**（< 5 文件变更，单函数修改） | 微基准测试 | Small |
| **Medium**（5-20 文件变更，模块级修改） | 微基准 + 宏基准 | Small + Medium |
| **Large**（> 20 文件变更，架构级修改） | 微基准 + 宏基准 + 组件基准 | Small + Medium + Large |

**Trivial 判定规则**：PR 标记 `trivial: true` 且满足以下条件之一：仅修改 `.md` 文件、仅修改注释、仅修改变量名、仅格式化。

### 4.4 性能门禁报告格式

```json
{
  "type": "performance-gate",
  "pr": 123,
  "branch": "feature/user-search-optimize",
  "timestamp": "2026-04-18T10:30:00Z",
  "baseline_ref": "main@abc1234",
  "results": {
    "micro": {
      "benchmarks": [
        {
          "name": "BenchmarkUserSearch",
          "baseline_ns_per_op": 15000,
          "current_ns_per_op": 12000,
          "change_percent": -20.0,
          "status": "passed",
          "data_size": "medium"
        }
      ]
    },
    "macro": {
      "benchmarks": [
        {
          "name": "SearchEndpoint",
          "metric": "p99_latency_ms",
          "baseline": 45,
          "current": 48,
          "change_percent": 6.7,
          "status": "warning",
          "budget_limit_ms": 200
        }
      ]
    }
  },
  "gate_decision": "passed_with_warning",
  "warnings": ["SearchEndpoint P99 延迟增长 6.7%，接近 10% 失败阈值"],
  "evidence_files": [".gate/performance/pr-123_benchmark.json"]
}
```

### 4.5 门禁失败处理流程

```
性能门禁失败 → 分析差异报告
                 ├── 可解释（数据量变化、新依赖）→ 人工确认 → 标记豁免
                 ├── 不可解释 → 人工分析根因 → 制定修复方案 → 重跑
                 └─ 持续失败 → 阻塞合并，通知人工分析根因
```

**豁免规则**：

| 豁免条件 | 说明 | 审批 |
|---------|------|------|
| **已知退化 + 功能必要** | 性能退化是为了修复严重 Bug 或实现必要功能 | Tech Lead 审批 |
| **基准不准确** | Baseline 本身有问题（运行环境不稳定） | 重新建立基线 |
| **短期过渡** | 临时退化，已在计划中优化（关联优化任务 ID） | Tech Lead 审批 + 7 天内优化 |

**注意**：性能退化不得由 AI 自行"优化"后重新提交——必须人工分析根因（见 06-cicd-pipeline.md 4.1）。

---

## 第 5 章：性能剖析（Performance Profiling）

### 5.1 何时触发性能剖析

| 触发条件 | 优先级 | 执行者 |
|---------|:------:|--------|
| 性能门禁失败（退化 > 10%） | P0 | AI + 人工 |
| 生产环境 P99 延迟超预算 | P0 | 人工 + AI 辅助 |
| 内存持续增长（疑似泄漏） | P0 | 人工 + AI 辅助 |
| CI 中基准测试持续退化（3 次以上） | P1 | AI 自动 |
| 新服务上线前的性能评估 | P1 | 人工 + AI 辅助 |
| 季度性性能健康检查 | P2 | AI 自动 |

### 5.2 剖析工具链

| 语言 | CPU 剖析 | 内存剖析 | 阻塞/锁剖析 | 工具 |
|------|---------|---------|------------|------|
| **Go** | `pprof cpu` | `pprof heap` | `pprof mutex` | `go tool pprof` |
| **Python** | `cProfile` / `py-spy` | `tracemalloc` / `objgraph` | — | `pyinstrument` |
| **TypeScript/Node** | `--prof` / `clinic` | `--inspect` / `heapdump` | — | `0x` / `clinic` |
| **Java** | `async-profiler` | `jmap` / `MAT` | `jstack` | `JFR` / `VisualVM` |

### 5.3 剖析标准流程

```
1. 复现问题
   ├── 在测试环境复现（非生产）
   ├── 使用相同数据量（或同比例缩放）
   └── 运行 3 次确认非偶发

2. 收集剖析数据
   ├── CPU Profile：30 秒采样
   ├── Heap Profile：前后对比（内存泄漏场景）
   ├── Goroutine/Thread 快照（阻塞场景）
   └── Flame Graph：可视化热点路径

3. 分析热点
   ├── Top 5 耗时函数（按自身时间排序，非累计时间）
   ├── 调用链分析：哪个上游函数触发了热点
   └── 与 baseline 对比：哪些函数新增/变慢

4. 制定优化方案
   ├── 算法优化：O(n²) → O(n log n)
   ├── 数据结构：map → slice（或反之）
   ├── 缓存策略：计算结果缓存
   ├── 并发优化：串行 → 并行
   └── 数据库优化：添加索引、避免 N+1

5. 实施优化并验证
   ├── 实施最小优化（一次只改一处）
   ├── 运行基准测试验证效果
   └── 确认无功能退化（测试全绿）

6. 记录剖析结果
   └── 写入 `.gate/performance/profile-{date}.md`
```

### 5.4 剖析报告模板

```markdown
# 性能剖析报告：[问题简述]

> 日期：[日期] | 触发原因：[门禁失败/生产告警/定期健康检查]
> 服务：[服务名] | 分支：[分支名] | PR：[PR 编号]

## 问题描述
[描述性能问题现象，包括指标数值和影响范围]

## 剖析数据
- CPU Profile：[火焰图链接]
- Heap Profile：[快照链接]
- 测试环境：[环境配置说明]

## 根因分析
[定位到具体函数/SQL/算法，解释为什么慢]

## 优化方案
| 方案 | 预期效果 | 风险 | 推荐？ |
|------|---------|------|--------|
| [方案 1] | [预期降低 X%] | [风险说明] | [是/否] |

## 验证结果
[优化后基准测试结果对比]
```

---

## 第 6 章：容量规划（Capacity Planning）

### 6.1 容量指标

| 指标 | 定义 | 告警阈值 | 扩容阈值 |
|------|------|---------|---------|
| **QPS 容量** | 单实例最大可持续 QPS | > 70% 容量 | > 80% 容量 |
| **连接池容量** | 数据库连接池使用率 | > 70% | > 85% |
| **存储容量** | 磁盘/数据库存储使用率 | > 60% | > 80% |
| **内存容量** | 可用内存百分比 | < 30% 可用 | < 20% 可用 |
| **并发用户容量** | 系统最大并发用户数 | > 60% | > 75% |

### 6.2 容量预测模型

```
当前容量 = 单实例 QPS × 实例数
预测容量 = 当前容量 × (1 + 月增长率)^N
```

| 参数 | 来源 | 更新频率 |
|------|------|---------|
| 单实例 QPS | 基准测试结果（Large 数据量） | 每次基准测试变更时 |
| 实例数 | 基础设施实际值 | 实时 |
| 月增长率 | 历史流量趋势分析 | 每月 |
| 安全系数 | 0.8（预留 20% 余量） | 固定 |

### 6.3 容量规划报告

每月自动生成，包含：

```yaml
capacity_report:
  month: "2026-04"
  services:
    auth-service:
      current_qps: 1200
      max_qps_per_instance: 500
      instances: 3
      total_capacity: 1500
      utilization_percent: 80
      growth_rate_monthly: 15
      months_to_capacity: 2          # 2 个月后达到容量上限
      recommendation: "建议在 2026-05-15 前扩容至 4 实例"
      confidence: "high"             # high / medium / low
```

### 6.4 容量告警分级

| 级别 | 条件 | 动作 |
|------|------|------|
| **Green** | 利用率 < 60% | 无需动作 |
| **Yellow** | 利用率 60-75% | 纳入下月扩容计划 |
| **Orange** | 利用率 75-85% | 本周内启动扩容 |
| **Red** | 利用率 > 85% | 立即扩容 + 限流保护 |

---

## 第 7 章：负载/压力/耐久测试

### 7.1 测试类型定义

| 测试类型 | 目的 | 负载模式 | 持续时间 | 触发时机 |
|---------|------|---------|---------|---------|
| **负载测试** | 验证预期负载下的性能 | 正常 QPS ± 20% | 30 分钟 | 每次大版本发布前 |
| **压力测试** | 找到系统崩溃点 | 递增 QPS 直至失败 | 至崩溃 | 季度性 / 架构变更时 |
| **耐久测试** | 检测内存泄漏和资源耗尽 | 正常 QPS 持续运行 | 24-72 小时 | 季度性 / 新服务上线 |
| **峰值测试** | 验证突发流量下的行为 | 瞬时 10× 正常 QPS | 5 分钟 | 大促/活动前 |
| **浸泡测试** | 检测长时间运行的退化 | 80% 最大 QPS | 12 小时 | 关键服务版本更新 |

### 7.2 测试阈值

| 测试类型 | 通过条件 | 失败条件 |
|---------|---------|---------|
| **负载测试** | P99 ≤ 预算 × 1.05，错误率 ≤ 0.1% | P99 > 预算 × 1.10，错误率 > 1% |
| **压力测试** | 找到明确的崩溃点，崩溃点 QPS ≥ 预期容量 × 1.2 | 崩溃点 QPS < 预期容量 |
| **耐久测试** | 内存稳定（增长 ≤ 5%），无 goroutine 泄漏 | 内存持续增长，goroutine 泄漏 |
| **峰值测试** | 降级但不崩溃，恢复后指标正常 | 系统崩溃或数据丢失 |
| **浸泡测试** | 性能退化 ≤ 5%（vs 初始值） | 性能退化 > 10% |

### 7.3 自动化执行

```yaml
# .performance-tests.yaml
# 性能测试自动化配置

load_test:
  schedule: "0 2 * * 0"           # 每周日凌晨 2 点
  tool: k6
  script: benchmarks/macro/load_test.k6.js
  duration: 30m
  vus: 100                         # 虚拟用户数
  thresholds:
    - http_req_duration:p(99) < 200
    - http_req_failed < 0.001

stress_test:
  schedule: "0 2 1 * *"            # 每月 1 日凌晨 2 点
  tool: k6
  script: benchmarks/macro/stress_test.k6.js
  ramp_duration: 10m               # 10 分钟内从 0 递增至最大
  thresholds:
    - system_capacity_reached = true

endurance_test:
  schedule: "0 0 1 */3 *"          # 每季度 1 日零点
  tool: k6
  script: benchmarks/macro/endurance_test.k6.js
  duration: 24h
  vus: 50
  thresholds:
    - memory_growth_percent < 5
    - goroutine_leak = 0
```

### 7.4 性能测试结果存储

```
.gate/performance/
├── load/                           # 负载测试结果
│   ├── 2026-04-18_load.json
│   └── trend.csv                   # 趋势数据
├── stress/                         # 压力测试结果
│   ├── 2026-04-01_stress.json
│   └── breaking_point.json         # 崩溃点记录
├── endurance/                      # 耐久测试结果
│   ├── 2026-04-01_endurance.json
│   └── memory_leak_report.md       # 内存泄漏分析
└── summary/                        # 汇总报告
    ├── latest.json                 # 最新一次结果
    └── trend.json                  # 30 天趋势
```

---

## 第 8 章：AI 特定性能规则

### 8.1 绝对禁止（Zero Tolerance）

AI 生成的代码不得包含以下模式，CI 必须自动检测并阻断：

| # | 规则 | 检测方法 | 违反后果 |
|---|------|---------|---------|
| **PF-01** | **N+1 查询** | 循环内的数据库查询调用 | CI 阻断合并 |
| **PF-02** | **循环内 HTTP 请求** | 循环内的 `http.Get` / `fetch` / `requests.get` | CI 阻断合并 |
| **PF-03** | **未索引数据库查询** | EXPLAIN 分析 + 全表扫描检测 | CI 阻断合并 |
| **PF-04** | **SELECT \* 查询** | SQL 解析检测 `SELECT *` | CI 阻断合并 |
| **PF-05** | **字符串拼接 SQL** | 正则检测 SQL 字符串拼接 | CI 阻断合并（同时违反 P5） |
| **PF-06** | **同步阻塞主线程** | UI/前端代码中的同步 I/O | CI 阻断合并 |
| **PF-07** | **无限循环无退出条件** | 静态分析检测 `for/while` 无 break | CI 阻断合并 |

### 8.2 需要证明（Require Justification）

以下模式可以存在，但必须有性能分析证明其必要性：

| # | 规则 | 证明要求 |
|---|------|---------|
| **PF-08** | **O(n²) 或更高复杂度算法** | 说明 n 的上限 + 基准测试证明在此范围内可接受 |
| **PF-09** | **全量数据加载到内存** | 说明数据量上限 + 内存预算合规证明 |
| **PF-10** | **全局可变状态** | 说明并发安全机制（锁/原子操作） |
| **PF-11** | **递归无尾递归优化** | 说明递归深度上限 + 栈溢出防护 |
| **PF-12** | **同步串行处理可并行请求** | 说明为什么不能并行（依赖关系证明） |

### 8.3 性能审查检查清单（AI Reviewer 必须执行）

AI Reviewer 在 L3 质量审查层中，必须对每个 PR 执行以下性能检查：

```
Performance Review Checklist（AI Reviewer）
═══════════════════════════════════════════

[ ] PF-01: 无循环内数据库查询（N+1）
[ ] PF-02: 无循环内 HTTP 请求
[ ] PF-03: 数据库查询使用索引（EXPLAIN 验证）
[ ] PF-04: 无 SELECT * 查询
[ ] PF-05: SQL 使用参数化查询（非字符串拼接）
[ ] PF-06: 前端代码无同步阻塞
[ ] PF-07: 所有循环有明确退出条件
[ ] PF-08: 如有 O(n²) 算法，有 n 上限证明
[ ] PF-09: 如无全量加载到内存，有数据量证明
[ ] PF-10: 全局可变状态有并发保护
[ ] PF-11: 递归有深度限制
[ ] PF-12: 可并行请求已并行化（或说明原因）
[ ] PF-13: 无多余序列化/反序列化
[ ] PF-14: 大对象传递使用引用而非值拷贝
[ ] PF-15: 文件/连接/流有正确关闭（defer 或 finally）
[ ] PF-16: 无不必要的 deeply nested 循环（> 3 层）
```

### 8.4 AI 生成代码的性能反模式检测

| 反模式 | 描述 | 检测方式 | 替代方案 |
|--------|------|---------|---------|
| **Chatty API** | 多次小请求替代一次大请求 | 同一端点短时间多次调用 | 批量 API |
| **Over-fetching** | 查询返回远多于需要的数据 | 响应体大小 / 实际使用大小 > 5× | 字段裁剪 / GraphQL |
| **Eager Loading Abuse** | 关联数据全部预加载 | SQL JOIN 数 > 5 或返回行数异常 | Lazy loading / DataLoader |
| **Cache Missing** | 热点数据未缓存 | 重复查询相同 key | 添加缓存层 |
| **Missing Pagination** | 列表查询无分页 | SQL 无 LIMIT/OFFSET | 强制分页 |
| **Sync in Hot Path** | 热路径上的同步 I/O | CPU Profile 中 I/O wait 占比 > 20% | 异步化 |

### 8.5 AI 必须考虑的性能影响

AI 在生成代码时，必须对以下决策显式说明性能考量：

| 决策点 | 必须说明 |
|--------|---------|
| 选择排序/搜索算法 | 时间复杂度 + n 的预估范围 |
| 选择数据结构 | 为什么选这个结构（map vs slice vs tree） |
| 数据库查询设计 | 预期查询计划 + 是否使用索引 |
| 缓存策略 | 缓存什么、TTL 多久、缓存命中率预期 |
| 并发模型 | 为什么选择串行/并行/goroutine 池 |
| 序列化格式 | JSON vs Protocol Buffers vs 其他 |

---

## 第 9 章：性能指标与持续改进

### 9.1 性能核心指标

| 指标 | 计算方式 | 目标 | 告警阈值 |
|------|---------|:----:|---------|
| **性能门禁通过率** | 性能检查通过的 PR 数 / 总 PR 数 | ≥ 95% | < 85% |
| **性能退化检出时间** | 从退化引入到检出的时间 | < 1 个 PR 周期 | > 3 个 PR 周期 |
| **基准测试覆盖率** | 有基准测试的函数数 / 总函数数 | ≥ 80%（核心路径 100%） | < 60% |
| **性能回归修复时间** | 从性能退化检出到修复完成的平均时间 | < 24 小时 | > 72 小时 |
| **容量预测准确率** | 预测容量 vs 实际容量的误差 | < 15% | > 30% |
| **压力测试执行率** | 按计划执行的压力测试数 / 计划总数 | 100% | < 80% |

### 9.2 性能趋势分析

CI 必须维护性能趋势数据，用于识别慢性退化：

```
趋势分析规则：
1. 每次基准测试结果追加到趋势数据
2. 计算 30 天移动平均
3. 移动平均持续增长 = 慢性退化（即使每次 < 5%）
4. 慢性退化累计 > 20% = 触发专项优化任务
```

### 9.3 性能改进规则

| 触发条件 | 动作 |
|---------|------|
| 性能门禁通过率 < 85% 连续 1 周 | 分析 Top 3 退化原因，针对性修复 |
| 同一服务连续 3 个 PR 性能退化 | 触发专项性能剖析任务 |
| 慢性退化累计 > 20% | 创建性能优化 Epic，优先级 P1 |
| 压力测试崩溃点下降 | 架构评审，分析容量退化原因 |
| 耐久测试发现内存泄漏 | P0 Bug，24 小时内修复 |

---

## 附录 A：性能测试脚本模板

### A.1 k6 宏基准测试模板

```javascript
// benchmarks/macro/search_flow.k6.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  thresholds: {
    http_req_duration: ['p(99)<200'],
    errors: ['rate<0.01'],
  },
  stages: [
    { duration: '2m', target: 50 },   // ramp up
    { duration: '5m', target: 50 },   // steady state
    { duration: '2m', target: 100 },  // peak load
    { duration: '1m', target: 0 },    // ramp down
  ],
};

export default function () {
  const res = http.get(`${__ENV.BASE_URL}/api/users/search?q=test`);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'p99 latency < 200ms': (r) => r.timings.duration < 200,
    'response size < 8KB': (r) => r.body.length < 8192,
  }) || errorRate.add(1);

  sleep(1);
}
```

### A.2 Go 微基准测试模板

```go
// benchmarks/micro/user/search_test.go

func BenchmarkUserSearch(b *testing.B) {
    db := setupTestDB(b, "medium") // 100K records
    svc := NewUserService(db)

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        b.StopTimer()
        query := generateRandomQuery()
        b.StartTimer()

        results, err := svc.Search(b.Context(), query)
        if err != nil {
            b.Fatalf("search failed: %v", err)
        }
        _ = results
    }
}
```

### A.3 `.gate/performance/` 证据文件格式

```json
{
  "type": "performance-evidence",
  "version": "1.0",
  "timestamp": "2026-04-18T10:30:00Z",
  "test_type": "micro | macro | component",
  "test_name": "BenchmarkUserSearch",
  "environment": {
    "cpu": "8 cores",
    "memory": "16GB",
    "os": "linux",
    "go_version": "1.22"
  },
  "data_size": {
    "level": "medium",
    "records": 100000,
    "size_mb": 50
  },
  "iterations": 3,
  "results": {
    "mean_ns_per_op": 12500,
    "median_ns_per_op": 12000,
    "p95_ns_per_op": 18000,
    "p99_ns_per_op": 22000,
    "std_dev": 3000
  },
  "baseline_comparison": {
    "baseline_ref": "main@abc1234",
    "baseline_mean_ns": 15000,
    "change_percent": -16.7,
    "status": "improved"
  },
  "budget_check": {
    "p99_budget_ms": 50,
    "within_budget": true
  }
}
```

---

## 附录 B：术语表

| 术语 | 定义 |
|------|------|
| **Performance Budget** | 对系统各项性能指标设定的上限值，不可突破 |
| **Baseline** | 基准性能数据，用于与 PR 变更对比 |
| **Micro Benchmark** | 单个函数/方法级别的性能测试 |
| **Macro Benchmark** | 端到端 API 级别的性能测试 |
| **Performance Gate** | CI 中的性能门禁，位于 L4 层 |
| **Capacity Planning** | 预测系统容量、规划扩容的流程 |
| **Load Test** | 验证预期负载下的系统性能 |
| **Stress Test** | 找到系统崩溃点的测试 |
| **Endurance Test** | 长时间运行检测内存泄漏和资源耗尽 |
| **N+1 Query** | 循环中逐条查询数据库的反模式 |
| **Over-fetching** | 查询返回远多于实际需要的数据 |
| **Chronic Degradation** | 每次小幅退化累积成显著性能下降 |

---

## 附录 C：与其他规范的关联

| 关联文档 | 关联章节 | 说明 |
|---------|---------|------|
| 01-core-specification.md | 第 2 章 TDD | 基准测试遵循 TDD 原则（先于实现） |
| 01-core-specification.md | 1.5.4 构造检查清单 | 并发安全、资源清理与性能直接相关 |
| 06-cicd-pipeline.md | 2.5 L4 集成验证层 | 性能基线检查是 L4 的检查项之一 |
| 06-cicd-pipeline.md | 4.1 Self-Correction 策略 | 性能退化不可由 AI 自修 |
| 04-security-governance.md | — | 安全扫描与性能门禁并行执行 |
| 07-observability.md | — | 生产性能数据反馈至基线系统 |
