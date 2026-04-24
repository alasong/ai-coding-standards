# AI Coding 规范 v5.5：部署与回滚策略

> 版本：v5.5 | 2026-04-24
> 定位：大规模 Auto-Coding 场景下的部署编排与回滚安全 — 定义部署策略、回滚机制、多服务编排、Feature Flag、数据库协调、AI 专属约束
> 前置：[01-core-specification.md](01-core-specification.md) P1-P11、[06-cicd-pipeline.md](06-cicd-pipeline.md) L5 环境晋升、[08-database-migration.md](08-database-migration.md)

---

## 第 1 章：核心原则

### 1.1 为什么需要独立的部署规范

06-cicd-pipeline.md 定义了 Pipeline 分层（L0-L5），但 L5 环境晋升的"金丝雀 → 生产"只是部署流程的入口。大规模 Auto-Coding 场景下：

- **部署密度高**：每天数十至数百个 AI 生成的 PR 合并到 main，如果每个合并都触发完整的 Blue-Green 部署，基础设施成本不可承受
- **回滚复杂度高**：多服务依赖下，单服务回滚可能引发连锁故障
- **AI 代码不确定性**：即使 L0-L4 全部通过，AI 生成的代码在生产环境仍有幻觉逃逸的风险（07-anti-hallucination.md 3.4 目标：逃逸率 0%）
- **数据库协同难**：代码部署和数据库迁移的时序如果不协调，会导致新旧版本同时运行时的数据不一致

**核心原则**：部署是 AI 代码进入生产的最后一道门，必须有与代码生成同等严格的规范约束。

### 1.2 部署策略选型矩阵

| 策略 | 适用场景 | 回滚速度 | 资源成本 | AI 推荐度 |
|------|---------|---------|---------|----------|
| **蓝绿部署** | 核心服务、零停机要求、数据库大变更 | **秒级**（切换路由） | 2x 资源 | L3/L4 核心服务必须 |
| **金丝雀发布** | 日常发布、AI 生成代码验证、风险探索 | 分钟级（流量回收） | 1.1-1.5x | L2-L4 **默认策略** |
| **滚动升级** | 资源受限、非核心服务、大规模部署 | 分钟级（逐实例回退） | 1x + 缓冲 | L3/L4 非核心服务 |

**AI 特有规则**：AI 不得自行选择部署策略。部署策略由 Spec 中的 `deployment_strategy` 字段指定，AI 仅执行。Spec 中必须包含 `deployment_strategy` 字段（canary/blue-green/rolling）。如果缺失，AI 必须阻断并报告，不得使用默认值。CI 在 L3 层验证 Spec 中 deployment_strategy 字段存在。

**术语定义**：本文中所有"健康检查"均指 HTTP GET `/health` 端点返回 200 且 JSON body 中所有 `dependencies` 字段值为 `healthy`。"冒烟测试"指核心用户旅程 E2E 测试子集（由项目根目录 `.smoke-tests.yml` 定义）。

---

## 第 2 章：部署策略详解

### 2.1 蓝绿部署（Blue-Green Deployment）

#### 2.1.1 架构

```
                ┌──────────┐
                │  Router   │
                │ (Switch)  │
                └─────┬────┘
                      │ switch: blue/green
              ┌───────┴────────┐
              ▼                ▼
     ┌─────────────┐   ┌─────────────┐
     │   Blue      │   │   Green     │
     │ (当前生产)   │   │ (新版本)     │
     │ v1.2.3      │   │ v1.2.4      │
     └─────────────┘   └─────────────┘
```

#### 2.1.2 详细步骤

| 步骤 | 动作 | 验证 | 自动/人工 |
|------|------|------|----------|
| **1. 部署 Green** | 将新版本部署到当前未使用的环境 | 健康检查通过 | 自动 |
| **2. Green 冒烟** | 对 Green 环境运行核心 E2E + 冒烟测试 | 冒烟测试 100% 通过 | 自动 |
| **3. 数据同步验证** | 验证 Green 环境的数据库连接、缓存预热完成 | 数据一致性检查 | 自动 |
| **4. 切换路由** | Router 将 100% 流量切换到 Green | 切换后 1 分钟内无错误率增长 | L2 自动，L1 人工 |
| **5. 观察窗口** | Green 作为生产运行观察期 | 错误率 < 1%，P99 < 基线×1.5 | 自动 |
| **6. Blue 保留** | Blue 环境保留（不销毁），作为回滚目标 | Blue 健康检查仍通过 | 自动 |
| **7. Blue 下线** | 观察期（≥24h）结束后下线 Blue | 无回滚发生 | 人工确认 |

#### 2.1.3 使用时机

| 场景 | 使用蓝绿 | 原因 |
|------|:--------:|------|
| 核心支付/交易服务 | **必须** | 停机成本 > 资源成本 |
| 数据库结构大变更 | **必须** | 需要新旧 Schema 同时可用 |
| AI 生成的高风险变更 | **必须** | L3/L4 下 AI 代码风险不可完全消除 |
| 内部工具、管理后台 | 不推荐 | 可以接受短暂停机 |

#### 2.1.4 回滚路径

蓝绿部署的回滚是**路由级切换**：

```
Green 出现问题 → Router 切换回 Blue（<30s）→ Blue 恢复服务 → 人工分析 Green 问题
```

回滚不需要重新部署，因此回滚时间 = 路由切换时间（通常 < 30 秒）。

### 2.2 金丝雀发布（Canary Release）

#### 2.2.1 流量分配架构

```
                ┌──────────┐
                │ Gateway   │
                │ (Traffic  │
                │  Split)   │
                └─────┬────┘
                      │
              ┌───────┴──────────┐
              │  95% 流量         │  5% 流量
              ▼                  ▼
     ┌─────────────┐     ┌─────────────┐
     │   Stable     │     │   Canary    │
     │   (旧版本)    │     │   (新版本)   │
     │   18 实例    │     │   1 实例     │
     └─────────────┘     └─────────────┘
```

#### 2.2.2 详细步骤

| 阶段 | 流量比例 | 观察窗口 | 通过标准 | 失败动作 |
|------|---------|---------|---------|---------|
| **Canary-5** | 5% | 10 min | 错误率 < 1%，P99 < 基线×1.5，无 Critical 告警 | 回滚到 0% |
| **Canary-25** | 25% | 15 min | 同上 + 业务指标无异常下降 | 回滚到 5%，再回 0% |
| **Canary-50** | 50% | 20 min | 同上 + 无 Warning 告警 | 回滚到 25% → 5% → 0% |
| **Production** | 100% | 持续监控 | 最终确认 | 触发全量回滚 |

#### 2.2.3 自动回滚触发条件

任一条件满足即触发自动回滚（见第 3 章回滚策略）：

- 错误率 > 5%（5 分钟滑动窗口）
- P99 延迟 > 基线 × 2（5 分钟滑动窗口）
- 健康检查连续 3 次失败
- 关键业务指标下降 > 10%（订单量、注册数、API 调用成功率）
- Critical 级别告警触发

#### 2.2.4 使用时机

| 场景 | 使用金丝雀 | 原因 |
|------|:---------:|------|
| 日常 AI 生成代码发布 | **默认** | 平衡安全性和资源成本 |
| API 行为变更 | **必须** | 验证客户端兼容性 |
| 性能优化变更 | **推荐** | 需要对比性能指标 |
| 紧急 Hotfix | 跳过 → 全量 | 时间敏感，可接受风险 |

### 2.3 滚动升级（Rolling Upgrade）

#### 2.3.1 升级流程

```
实例集：[A, B, C, D, E, F, G, H]

Round 1: [A', B', C, D, E, F, G, H]  替换 2 个（25%）
Round 2: [A', B', C', D', E, F, G, H] 替换 4 个（50%）
Round 3: [A', B', C', D', E', F', G, H] 替换 6 个（75%）
Round 4: [A', B', C', D', E', F', G', H'] 替换 8 个（100%）

每轮之间等待：新实例健康检查通过 + 观察 2 分钟
```

#### 2.3.2 详细步骤

| 步骤 | 动作 | 约束 |
|------|------|------|
| **1. 创建新版本镜像** | 构建、签名、推送到 Registry | 镜像签名验证 |
| **2. 分批替换** | 每批替换 25% 的实例 | 同时不健康的实例不得超过 50% |
| **3. 新实例健康检查** | 每个新实例必须通过 `/health` 检查 | 连续 3 次成功 |
| **4. 等待稳定窗口** | 每批替换后等待 2-5 分钟 | 期间无告警 |
| **5. 下一批** | 重复步骤 2-4 | 直到 100% |
| **6. 最终验证** | 全量 E2E 冒烟测试 | 通过后标记部署完成 |

#### 2.3.3 回滚路径

滚动升级的回滚需要**反向操作**：

```
第 3 轮失败（75% 已升级）：
  1. 停止继续替换
  2. 将已升级的 A'-F' 逐批回滚到旧版本
  3. 回滚顺序与升级相反：先回滚最近升级的批次
  4. 每批回滚后等待稳定窗口
```

**注意**：滚动升级的回滚时间长于蓝绿部署（分钟级 vs 秒级）。对于核心服务，不建议使用滚动升级。

#### 2.3.4 使用时机

| 场景 | 使用滚动升级 | 原因 |
|------|:-----------:|------|
| 资源受限环境 | **推荐** | 不需要额外环境 |
| 大规模实例（>20） | **推荐** | 蓝绿成本过高 |
| 非核心服务 | **推荐** | 风险可控 |
| 核心交易服务 | **禁止** | 回滚太慢 |

---

## 第 3 章：回滚策略

### 3.1 回滚触发条件分级

| 级别 | 触发条件 | 响应方式 | 回滚类型 | 时间目标 |
|------|---------|---------|---------|---------|
| **P0 紧急** | 服务完全不可用、数据丢失 | 自动 + 立即通知 on-call | **全量回滚** | < 5 分钟 |
| **P1 严重** | 错误率 > 5%、核心功能不可用 | 自动 | **全量回滚** | < 10 分钟 |
| **P2 警告** | 错误率 2-5%、非核心功能异常 | 自动回滚 + 人工分析 | **按服务回滚** | < 15 分钟 |
| **P3 观察** | 性能下降 > 20%、业务指标微降 | 人工决策 | **按服务回滚或暂停** | < 30 分钟 |

### 3.2 回滚粒度

#### 3.2.1 全量回滚（Full Rollback）

**适用条件**：P0/P1 级别触发。

```
动作：
  1. 停止所有正在进行的部署
  2. 将所有服务回滚到上一个已验证的稳定版本（Last Known Good, LKG）
  3. LKG 版本信息从 .gate/deploy-history.json 中读取
  4. 验证回滚后服务健康
  5. 通知 on-call + 技术负责人
```

**LKG 版本定义**：上一次所有服务通过 L5 完整部署且稳定运行 ≥ 30 分钟的版本。

#### 3.2.2 按服务回滚（Per-Service Rollback）

**适用条件**：P2/P3 级别触发，问题定位到单个或少数服务。

```
动作：
  1. 识别故障服务（通过 .gate/deploy-scope.json）
  2. 仅回滚故障服务到 LKG 版本
  3. 其他服务保持新版本
  4. 验证服务间兼容性（API 契约检查）
  5. 通知相关人员
```

**约束**：按服务回滚的前提是**版本兼容性矩阵**已确认——新版本的其他服务必须能与 LKG 版本的故障服务兼容。如果不兼容，降级为全量回滚。

#### 3.2.3 决策树

```
问题发生
  │
  ├─ 影响核心功能？ ──是──→ 全量回滚
  │
  ├─ 影响 > 50% 服务？ ──是──→ 全量回滚
  │
  ├─ 数据一致性风险？ ──是──→ 全量回滚
  │
  ├─ 能精确定位到单个服务？ ──是──→ 按服务回滚
  │                                   │
  │                                   └─→ 兼容？ ──否──→ 全量回滚
  │
  └─ 影响性能但功能正常？ ──→ 人工决策（暂停/回滚/继续观察）
```

### 3.3 回滚中的数据一致性

#### 3.3.1 数据库向前兼容原则

回滚时数据库**不回滚**，仅回滚代码。这是由 08-database-migration.md 的向前兼容策略保障的：

```
部署流程：
  1. 先执行数据库迁移（新 Schema）
  2. 再部署新代码

回滚流程：
  1. 仅回滚代码到旧版本
  2. 数据库保持新 Schema 不变
  3. 旧代码必须能忽略新列/新表，正常工作
```

**AI 生成代码的约束**：
- AI 生成的代码在写入数据库时，不得假设旧列不存在（必须兼容新旧两列同时存在的场景）
- AI 生成的代码在读取数据库时，不得使用新列作为唯一数据源（必须有 fallback 路径）

#### 3.3.2 缓存一致性

| 场景 | 策略 |
|------|------|
| 回滚后缓存中可能有新版本的序列化格式 | 缓存 key 加入版本号，回滚后自动 miss 并重建 |
| 回滚后消息队列中有新版本格式的消息 | 消息 schema 必须向后兼容，旧版本能解析新格式 |
| 回滚后 CDN 中有新版本静态资源 | CDN URL 加入版本 hash，回滚后自动指向旧资源 |

#### 3.3.3 回滚后验证

回滚完成后必须执行以下验证（写入 `.gate/rollback-report.json`）：

```json
{
  "type": "rollback-report",
  "rollback_id": "RB-20260418-001",
  "trigger_level": "P1",
  "trigger_reason": "error_rate > 5% (7.2% in 5min window)",
  "rollback_type": "full | per-service",
  "services_rolled_back": ["api-gateway", "user-service"],
  "lkg_version": "1.2.3-autocoding-48a2f1b0",
  "started_at": "2026-04-18T14:32:00Z",
  "completed_at": "2026-04-18T14:37:00Z",
  "duration_seconds": 300,
  "database_rolled_back": false,
  "post_rollback_checks": {
    "health_check": "passed",
    "error_rate": "0.3% (target: < 1%)",
    "p99_latency": "120ms (baseline: 110ms)",
    "business_metrics": "normal",
    "data_integrity": "verified"
  },
  "evidence": [
    ".gate/rollback-health.json",
    ".gate/rollback-metrics.json"
  ]
}
```

---

## 第 4 章：多服务部署顺序

### 4.1 依赖图驱动排序

多服务部署必须基于服务间的依赖关系计算部署顺序，而非按字母序或随机顺序。

#### 4.1.1 服务依赖声明

每个服务必须在 `.service.yaml` 中声明依赖：

```yaml
service: user-service
version: 1.2.4
deployment_strategy: canary
depends_on:
  - name: auth-service
    version_constraint: ">= 1.1.0"
    reason: "调用 /auth/validate 接口"
  - name: db-proxy
    version_constraint: ">= 2.0.0"
    reason: "使用新的连接池协议"
```

**AI 特有规则**：AI 生成服务代码时，必须同时更新 `.service.yaml` 中的依赖声明。依赖声明缺失 = L3 阻断。

#### 4.1.2 部署顺序计算

```
部署顺序 = 拓扑排序(服务依赖图)

示例依赖图：

  db-proxy ──→ auth-service ──→ api-gateway
     │              │
     │              └──→ user-service ──→ api-gateway
     │
     └──→ notification-service

部署顺序（拓扑排序结果）：
  Round 1: db-proxy                    （无依赖，最先部署）
  Round 2: auth-service, notification-service  （仅依赖 db-proxy，可并行）
  Round 3: user-service                （依赖 auth-service + db-proxy）
  Round 4: api-gateway                 （依赖 auth-service + user-service，最后部署）
```

#### 4.1.3 并行部署规则

同一 Round 内的服务可以并行部署，但必须满足：

| 规则 | 说明 |
|------|------|
| **无相互依赖** | 同一 Round 的服务之间不得有依赖关系 |
| **资源限制** | 并行部署数量受限于 CI Runner 可用资源 |
| **错误隔离** | 一个服务部署失败不影响同 Round 其他服务（继续部署或暂停由配置决定） |
| **数据库隔离** | 同一 Round 内涉及同一张表变更的服务不得并行部署 |

### 4.2 部署批次管理

```
┌─────────────────────────────────────────────┐
│ 部署批次执行器                                 │
│                                               │
│  Round 1 → 部署 → 验证 → 通过 → 继续           │
│                              → 失败 → 暂停     │
│                                               │
│  Round 2 → 部署（并行 N 个服务）→ 验证          │
│                                               │
│  ...                                          │
│                                               │
│  Round N → 全量部署 → 全量验证 → 部署完成       │
└─────────────────────────────────────────────┘
```

| 步骤 | 动作 | 失败策略 |
|------|------|---------|
| **Round N 部署** | 按拓扑排序结果部署当前 Round 所有服务 | — |
| **Round N 验证** | 所有服务健康检查 + 核心集成测试 | — |
| **验证通过** | 进入 Round N+1 | — |
| **验证失败** | 暂停部署，回滚 Round N 已部署的服务 | 按 3.2 节决策树选择回滚粒度 |
| **修复后重试** | 修复问题后从 Round N 重新开始 | 最多重试 2 次，超过转人工 |

### 4.3 部署范围声明

每次部署前必须生成 `.gate/deploy-scope.json`：

```json
{
  "type": "deploy-scope",
  "deploy_id": "DEP-20260418-001",
  "trigger": "merge-to-main",
  "services": [
    {
      "name": "user-service",
      "from_version": "1.2.3-autocoding-48a2f1b0",
      "to_version": "1.2.4-autocoding-9c3d7e21",
      "strategy": "canary",
      "depends_on": ["auth-service", "db-proxy"],
      "deployment_round": 3
    },
    {
      "name": "api-gateway",
      "from_version": "2.0.1-autocoding-1a2b3c4d",
      "to_version": "2.0.2-autocoding-5e6f7a8b",
      "strategy": "blue-green",
      "depends_on": ["auth-service", "user-service"],
      "deployment_round": 4
    }
  ],
  "total_rounds": 4,
  "rollback_plan": "full-rollback-to-lkg"
}
```

---

## 第 5 章：Feature Flag 管理

### 5.1 Feature Flag 分层

| 层级 | 类型 | 生命周期 | 谁管理 | 示例 |
|------|------|---------|-------|------|
| **L1 发布 Flag** | 控制新功能是否可见 | 短（1-4 周） | 开发团队 | `enable_new_checkout` |
| **L2 实验 Flag** | A/B 测试、流量分配 | 中（2-8 周） | 产品团队 | `checkout_v2_experiment` |
| **L3 运维 Flag** | 系统降级、限流开关 | 中（按需） | 运维团队 | `enable_readonly_mode` |
| **L4 Kill Switch** | 紧急关闭功能 | 永久 | **安全团队** | `disable_ai_generated_feature_x` |

### 5.2 渐进式发布流程

```
代码合并到 main（Flag 关闭）
  │
  ├─→ 部署到生产（Flag 默认关闭，新功能不可见）
  │
  ├─→ 内部测试：Flag 对内部用户开启
  │     验证：内部用户无异常
  │
  ├─→ 1% 用户：Flag 开启，监控指标
  │     验证：错误率、延迟、业务指标正常
  │
  ├─→ 10% → 25% → 50% → 100%
  │     每步等待 ≥ 15 分钟，指标无异常
  │
  └─→ 全量开启后 48 小时无问题
        └─→ 移除 Flag 代码（技术债清理）
```

### 5.3 Kill Switch 规范

Kill Switch 是紧急情况下的一键关闭开关，优先级高于所有其他 Flag。

| 属性 | 要求 |
|------|------|
| **响应时间** | 开启到生效 < 30 秒 |
| **可用性** | 独立于主系统（使用独立的配置中心） |
| **权限** | 仅 on-call + 技术负责人可操作 |
| **审计** | 每次开启/关闭必须记录审计日志 |
| **测试** | 每月至少一次 Kill Switch 演练 |

**AI 特有规则**：AI 生成的涉及新功能/新端点的代码，**必须**附带一个 Kill Switch。没有 Kill Switch 的 AI 生成代码不得进入生产。

### 5.4 AI 生成代码的 Flag 要求

| 约束 | 说明 |
|------|------|
| **强制 Flag** | AI 生成的每个新功能（Feature Spec 中定义的）必须有对应的 Feature Flag |
| **默认关闭** | Flag 默认值必须是 `false` / `off` |
| **Flag 命名** | 格式：`ai.{spec_id}.{feature_name}`，如 `ai.F042.new_recommendation_engine` |
| **Flag 生命周期** | 从代码合并开始计时，统一时间线如下：T+0 代码合并、T+X 渐进 Rollout 至 100%、T+Rollout+48h AI 必须创建清理 PR、T+合并后 30 天 CI 警告、T+合并后 45 天 CI 阻断 |
| **过期检测** | CI 在 L3 层检测存活 > 30 天的 AI Flag，超过 = 警告，> 45 天 = 阻断 |
| **Flag 回滚** | Kill Switch 触发时，自动将所有 `ai.*` Flag 设为 `false` |

### 5.5 Flag 配置模板

```yaml
# feature-flags/ai-F042-new-recommendation-engine.yaml
flag: ai.F042.new_recommendation_engine
type: boolean
default: false
owner: "@team-ai-coding"
created_at: "2026-04-18"
expiry_date: "2026-05-18"  # 30 天自动清理
kill_switch: true
description: "AI 生成的推荐引擎 V2（Spec F042）"
rollout_stages:
  - percentage: 0
    condition: "default"
  - percentage: 1
    condition: "internal_users"
  - percentage: 10
    condition: "after_48h_no_incident"
  - percentage: 50
    condition: "after_7d_no_incident"
  - percentage: 100
    condition: "after_14d_no_incident"
```

---

## 第 6 章：数据库与代码部署协调

### 6.1 部署时序规则

```
正确的部署时序：

  Phase 1: 数据库迁移（Safe/Caution 级别）
    │  先执行，因为新 Schema 必须对旧代码可用
    │  使用 08-database-migration.md 的 Expand 阶段
    │
    ▼
  Phase 2: 部署新代码（使用第 2 章的部署策略）
    │  新代码读写新列，旧代码读写旧列
    │  新代码兼容新旧两列同时存在的场景
    │
    ▼
  Phase 3: 数据回填（Expand-Contract 的 Migrate 阶段）
    │  新代码部署后、旧代码完全下线前
    │
    ▼
  Phase 4: 旧代码完全下线
    │
    ▼
  Phase 5: 收缩数据库（Contract 阶段，人工确认）
     删除旧列/旧表
```

**关键原则**：数据库迁移**永远先于**代码部署。不存在"先部署代码再执行迁移"的场景。

### 6.2 部署过程中的数据库兼容性

| 场景 | 兼容策略 |
|------|---------|
| **新增列（允许 NULL）** | 旧代码忽略新列，新代码写入新列 → 天然兼容 |
| **新增列（NOT NULL）** | 必须先添加允许 NULL 的列 → 回填默认值 → 加 NOT NULL 约束（分 3 步） |
| **新增表** | 旧代码不访问新表 → 天然兼容 |
| **新增索引** | 不影响代码逻辑 → 天然兼容 |
| **列类型变更** | 必须使用蓝绿迁移（08-database-migration.md 第 4 章），禁止简单 ALTER |
| **列删除** | 必须在旧代码完全下线后执行（Contract 阶段） |

### 6.3 迁移与部署的原子性

```
部署事务 = [数据库迁移, 代码部署, 验证] 整体成功或整体回滚

如果数据库迁移成功但代码部署失败：
  → 数据库迁移不回滚（向前兼容原则）
  → 代码部署重试或回滚到 LKG
  → 记录到 .gate/deploy-incident.json

如果代码部署成功但验证失败：
  → 触发代码回滚（第 3 章）
  → 数据库保持不变
  → 旧代码 + 新 Schema = 向前兼容
```

### 6.4 多服务数据库协调

多个服务操作同一数据库时的协调规则：

| 规则 | 说明 |
|------|------|
| **迁移顺序** | 按服务依赖图排序，底层服务的迁移先执行 |
| **并发控制** | 同一数据库的迁移必须串行执行（使用数据库级别的锁） |
| **迁移窗口** | 所有迁移必须在同一个部署窗口内完成，不得跨窗口 |
| **回滚协调** | 一个服务的迁移失败，所有后续服务的迁移不得执行 |

---

## 第 7 章：零停机部署模式

### 7.1 零停机的必要条件

| 条件 | 检查方式 | 不满足的后果 |
|------|---------|-------------|
| 健康检查端点 | `/health` 返回 200 + 依赖状态 | 无法判断实例是否就绪 |
| 优雅关闭 | 进程收到 SIGTERM 后完成在飞请求再退出 | 在飞请求被丢弃 |
| 连接排空 | 实例下线时等待连接数降至 0 | 数据库连接被强制断开 |
| 向前兼容数据库 | 新旧代码都能读写当前 Schema | 回滚时旧代码读取失败 |
| 会话兼容 | 新版本不破坏现有用户会话 | 用户被迫重新登录 |

### 7.2 优雅关闭（Graceful Shutdown）

```
实例收到 SIGTERM
  │
  ├─→ 停止接收新请求（从负载均衡移除）
  │
  ├─→ 等待在飞请求完成（最长等待 30 秒）
  │
  ├─→ 关闭数据库连接池（等待在飞事务完成）
  │
  ├─→ 关闭缓存连接、消息队列消费者
  │
  └─→ 进程退出
```

| 配置 | 推荐值 | 说明 |
|------|-------|------|
| `shutdown_timeout` | 30s | 在飞请求最长等待时间 |
| `drain_connections` | true | 是否等待连接排空 |
| `health_check_interval` | 5s | 健康检查间隔（部署期间缩短） |
| `pre_stop_hook` | 执行清理脚本 | 可选的预停止钩子 |

### 7.3 会话兼容策略

| 策略 | 适用场景 | 实现方式 |
|------|---------|---------|
| **会话外部化** | 分布式部署 | 会话存储在 Redis，代码版本变更不影响 |
| **会话版本化** | 会话格式变更 | 会话 key 加入版本，旧版本会话自动失效并重建 |
| **无会话设计** | API 服务 | JWT/无状态认证，天然兼容 |

**AI 特有规则**：AI 生成代码不得引入新的本地会话存储（如内存中的 session map）。所有会话状态必须外部化到 Redis 或数据库。

### 7.4 零停机检查清单

部署前必须逐项确认：

- [ ] 数据库迁移已完成且向前兼容（08-database-migration.md 验证）
- [ ] 健康检查端点返回正确状态
- [ ] 优雅关闭已配置且测试通过
- [ ] 新版本的向后兼容性已验证（API 契约测试通过）
- [ ] 回滚方案已定义并测试（`.gate/rollback-plan.json` 存在）
- [ ] Feature Flag 已配置且默认关闭
- [ ] Kill Switch 已配置（AI 生成代码）
- [ ] 监控告警已就绪（错误率、延迟、业务指标）
- [ ] 部署范围已声明（`.gate/deploy-scope.json`）
- [ ] 不在维护窗口内（第 8 章）

---

## 第 8 章：AI 专属部署规则

### 8.1 AI 部署权限

| 规则 | 说明 | 违反后果 |
|------|------|---------|
| **自动化 Pipeline 唯一通道** | AI 只能通过 CI/CD Pipeline 部署，不得直接操作生产环境 | L4 降级 |
| **禁止手动部署** | AI 不得执行 `kubectl apply`、`docker run` 等直接部署命令 | 审计告警 |
| **禁止绕过 L0-L4** | AI 不得跳过任何 Pipeline 层级直接到 L5 | 部署拒绝 |
| **禁止维护窗口部署** | AI 不得在维护窗口期间触发部署（维护窗口是人工操作时间） | 部署延迟 |
| **必须定义回滚计划** | AI 提交部署前必须在 PR 中声明回滚计划 | L3 阻断 |
| **必须通过 Feature Flag** | AI 生成的新功能必须通过 Flag 控制可见性 | L3 阻断 |
| **必须有 Kill Switch** | AI 生成的每个新端点必须有 Kill Switch | L3 阻断 |

### 8.2 部署前声明

AI 在 PR 中必须声明以下部署信息（由 CI 自动验证，但 AI 生成的 PR 描述中必须包含）：

```markdown
## 部署信息

- **部署策略**: canary（由 Spec F042 指定）
- **影响服务**: user-service, recommendation-service
- **数据库变更**: Safe - 新增 recommendations 表
- **回滚计划**: 自动回滚至 LKG 版本 1.2.3-autocoding-48a2f1b0
  - 回滚触发条件: error_rate > 5%, p99 > baseline*2
  - 回滚预计时间: < 10 分钟（canary 回收流量）
  - 数据库回滚: 不回滚（向前兼容）
- **Feature Flag**: ai.F042.new_recommendation_engine (默认关闭)
- **Kill Switch**: ai.F042.kill_switch (独立配置)
- **维护窗口检查**: 不在维护窗口内 ✅
- **部署依赖顺序**: db-proxy → auth-service → user-service → recommendation-service
```

### 8.3 AI 部署禁止时段

| 时段 | 说明 | 例外 |
|------|------|------|
| **维护窗口** | 每周六 02:00-06:00 UTC | 无例外 |
| **业务高峰期** | 工作日 09:00-11:00 本地时间 | P0 Hotfix |
| **月末/季末** | 财务系统月结/季结期间 | P0 Hotfix |
| **已知不稳定期** | 基础设施变更后的 24 小时内 | 无例外 |

### 8.4 AI 回滚计划模板

每个 AI 生成的 PR 在部署前必须包含回滚计划，格式如下：

```json
{
  "type": "rollback-plan",
  "spec_id": "F042",
  "deploy_strategy": "canary",
  "lkg_version": "1.2.3-autocoding-48a2f1b0",
  "rollback_triggers": [
    { "metric": "error_rate", "threshold": "5%", "window": "5min" },
    { "metric": "p99_latency", "threshold": "baseline * 2", "window": "5min" },
    { "metric": "health_check", "threshold": "3 consecutive failures" }
  ],
  "rollback_type": "per-service",
  "rollback_steps": [
    "1. Stop canary traffic → 0%",
    "2. Scale up stable version to full capacity",
    "3. Verify health check on all instances",
    "4. Run post-rollback smoke tests",
    "5. Write .gate/rollback-report.json"
  ],
  "database_rollback": false,
  "database_reason": "Forward-compatible migration (Safe level, new table only)",
  "estimated_rollback_time": "< 10 minutes"
}
```

### 8.5 AI 部署审计

所有 AI 触发的部署必须记录到审计日志：

**原则：审计日志由部署 Agent 生成，但审计日志的完整性必须由 Gate Checker Agent 独立验证（不得由部署 Agent 自评 PASS/FAIL）。**

```json
{
  "type": "deploy-audit",
  "deploy_id": "DEP-20260418-001",
  "triggered_by": "ai-agent",
  "agent_id": "agent-worker-042",
  "spec_id": "F042",
  "pipeline_results": {
    "L0": "passed", "L1": "passed", "L2": "passed",
    "L3": "passed", "L4": "passed"
  },
  "human_reviewer": "@reviewer-zhang",
  "human_approval_at": "2026-04-18T14:00:00Z",
  "rollback_plan_defined": true,
  "feature_flag_configured": true,
  "kill_switch_configured": true,
  "not_in_maintenance_window": true,
  "deployment_completed_at": "2026-04-18T14:45:00Z",
  "final_status": "success | rolled_back | partial_failure",
  "gate_checker_verified": true
}
```

---

### 附录 A：部署决策速查表

| 场景 | 部署策略 | 回滚类型 | 需要人工？ |
|------|---------|---------|:---------:|
| 核心服务 + AI 代码 | 蓝绿 | 全量路由切换 | L2: 否, L1: 是 |
| 日常服务 + AI 代码 | 金丝雀 5→25→50→100 | 自动流量回收 | L2: 否, L1: 是 |
| 非核心服务 + AI 代码 | 滚动升级 | 反向逐批回退 | L2/L3: 否 |
| 紧急 Hotfix | 金丝雀 → 加速全量 | 全量回滚 | 否 |
| 数据库大变更 | 蓝绿 + 蓝绿 DB 迁移 | 全量路由切换 | 是 |
| 多服务协同部署 | 依赖排序 + 分批 | 按决策树选择 | L2: 否, L1: 是 |

### 附录 B：部署相关 Artifact 清单

| 文件 | 生成时机 | 内容 |
|------|---------|------|
| `.gate/deploy-scope.json` | 部署前 | 部署范围、策略、依赖顺序 |
| `.gate/rollback-plan.json` | PR 创建时 | 回滚触发条件、步骤、估计时间 |
| `.gate/deploy-history.json` | 每次部署后 | LKG 版本记录、部署结果 |
| `.gate/rollback-report.json` | 回滚后 | 回滚执行详情、验证结果 |
| `.gate/deploy-audit.json` | 部署完成后 | AI 部署审计记录 |
| `.gate/deploy-incident.json` | 部署异常时 | 异常描述、影响范围、处理动作 |
