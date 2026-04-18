# AI Coding 规范 v5.4：环境管理、缓存策略与 Code Review SLA

> 版本：v5.4 | 2026-04-18
> 前置：[01-core-specification.md](01-core-specification.md) P1-P11、[06-cicd-pipeline.md](06-cicd-pipeline.md) L0-L5 Pipeline、[13-deploy-rollback.md](13-deploy-rollback.md) 部署策略

---

## 第 1 章：环境管理

### 1.1 环境定义与能力矩阵

> Pipeline L5 环境晋升流程定义见 [06-cicd-pipeline.md](06-cicd-pipeline.md) 第 2.6 章。本章补充环境本身的能力边界、数据隔离与 AI 约束。

| 环境 | 用途 | 数据源 | 部署频率 | 部署方式 | 回滚策略 |
|------|------|--------|---------|---------|---------|
| **dev** | 开发验证、单元测试、集成测试 | 合成数据 / 脱敏快照 | 每次 PR 创建 | CI 自动 | 重建容器 |
| **staging** | 预生产验证、E2E 测试、性能基线 | 生产脱敏快照（T-7d） | 每次 main merge | CI + 金丝雀 | 蓝绿切换 |
| **prod** | 生产服务、真实用户 | 真实数据 | 金丝雀渐进 | 金丝雀 + 监控 | 自动回滚 |
| **sandbox** | AI 实验、原型验证、Poc | 完全合成数据 | 按需 | AI 自助 | 销毁重建 |

### 1.2 环境隔离规则

```
sandbox ──→ dev ──→ staging ──→ prod (单向流，禁止反向)
```

| 隔离维度 | dev | staging | prod | sandbox |
|---------|-----|---------|------|---------|
| **网络** | 内部 VPC | 隔离 VPC，仅通 CI | 生产 VPC，WAF | 独立 VPC，出口白名单 |
| **数据库** | 独立实例 / Docker | 独立实例，脱敏数据 | 生产实例，多可用区 | 独立实例，频繁重建 |
| **缓存** | 独立 Redis / 内存 | 独立 Redis，预热数据 | 生产 Redis 集群 | 独立 Redis |
| **配置管理** | `.env.dev` | `.env.staging` | KMS | `.env.sandbox` |
| **日志保留** | 7 天 | 30 天 | 1 年 | 24 小时 |

**P22 IP 不暴露**：所有环境的 IP、域名、端点必须通过环境变量或配置中心获取，禁止硬编码。

### 1.3 环境配置管理

```yaml
# .omc/environments.yaml
apiVersion: ai-coding/v5.4
kind: EnvironmentConfig
environments:
  sandbox:
    purpose: "AI 实验与原型验证"
    data_policy: synthetic_only
    ai_constraints:
      max_api_calls_per_day: 1000
      model_tier_limit: tier-3
      auto_cleanup_hours: 24
  dev:
    purpose: "开发验证、单元/集成测试"
    data_policy: synthetic_or_masked
    ai_constraints:
      max_api_calls_per_day: 5000
      model_tier_limit: tier-2
  staging:
    purpose: "预生产验证、E2E、性能基线"
    data_policy: masked_production_snapshot
    ai_constraints:
      max_api_calls_per_day: 2000
      model_tier_limit: tier-2
      write_restricted: true
  prod:
    purpose: "生产服务"
    data_policy: real_data
    ai_constraints:
      max_api_calls_per_day: 0
      write_restricted: true
      direct_access: false
```

### 1.4 环境晋升规则（索引）

环境晋升的 Pipeline 串联（staging deploy → smoke test → canary → production）定义在 [06-cicd-pipeline.md](06-cicd-pipeline.md) 第 2.6 章。部署策略（金丝雀、蓝绿、滚动升级）定义在 [13-deploy-rollback.md](13-deploy-rollback.md)。本章仅补充晋升失败处理与紧急通道：

**晋升失败处理**：
| 失败阶段 | 自动动作 | 恢复方式 |
|---------|---------|---------|
| L0 阻断 | 拒绝 commit | 修正后重新 commit |
| L1-L2 阻断 | 标记 PR failed | AI 自修 ≤3 轮 → 转人工 |
| L3 阻断 | 标记 PR blocked | 安全漏洞=人工修复；幻觉=AI 自修 |
| L4 阻断 | 拒绝合并 | AI 自修 ≤3 轮 → 转人工 |
| staging 冒烟失败 | 自动回滚 staging | 分析根因，修复后重新部署 |
| 金丝雀失败 | 自动回收流量 | 自动回滚，记录事故报告 |

**紧急晋升通道（Hotfix）**：
| 条件 | 流程 | 事后要求 |
|------|------|---------|
| **P0 生产事故** | 跳过 dev/staging，直接金丝雀 5%→验证→100% | 24h 内补齐 L0-L4 + 复盘 |
| **安全漏洞修复** | L0-L3 必须在 hotfix 分支运行，L4 可异步 | 48h 内完成 E2E 验证 |

**核心规则**：紧急通道 ≠ 无验证通道。L0 密钥扫描、L3 SAST 不得跳过。

---

## 第 2 章：测试数据管理

### 2.1 测试数据生成策略

| 策略 | 适用场景 | 生成方式 | 质量要求 |
|------|---------|---------|---------|
| **Factory Pattern** | 单元测试、集成测试 | 代码层数据工厂 | 类型正确、约束满足 |
| **Faker 生成** | E2E 测试、性能测试 | `faker` 库生成仿真数据 | 格式真实、语义无关 |
| **生产快照脱敏** | Staging 环境 | ETL 管道从 prod 抽取 → 脱敏 → 导入 | 数据分布一致、敏感字段不可逆 |
| **AI 生成测试数据** | 复杂场景数据 | AI 基于 Schema 生成 | 通过 Schema 校验、满足业务规则 |

### 2.2 数据脱敏规则（P10 数据分级对齐）

| 数据分类 | 脱敏级别 | 脱敏方法 | 可用环境 |
|---------|---------|---------|---------|
| **公开（Public）** | 无需脱敏 | — | 全部 |
| **内部（Internal）** | 低 | 部分遮蔽（如邮箱前缀脱敏） | dev, staging |
| **机密（Confidential）** | 高 | 不可逆替换（hash / 随机值） | dev, staging |
| **限制（Restricted）** | 极高 | 完全移除或使用合成替代 | 仅 sandbox（合成） |

```yaml
# .omc/data-masking-rules.yaml
apiVersion: ai-coding/v5.4
kind: DataMaskingRules

rules:
  - field_pattern: "email"
    classification: confidential
    masking_method: "hash_with_salt"
    example: "a1b2c3d4@example.com"  # 原始值不可恢复

  - field_pattern: "phone"
    classification: confidential
    masking_method: "partial_mask"
    example: "***-****-1234"  # 保留格式，隐藏内容

  - field_pattern: "id_number|ssn"
    classification: restricted
    masking_method: "replace_synthetic"
    example: "000-00-0000"  # 完全替换

  - field_pattern: "password|token|secret|key"
    classification: restricted
    masking_method: "remove"
    example: "[REDACTED]"  # 完全移除

  - field_pattern: "ip_address|hostname"
    classification: internal
    masking_method: "range_shift"
    example: "10.0.0.1"  # 映射到私有范围
```

### 2.3 测试数据生命周期

```
数据需求识别 → [AI 生成 / Faker / Factory] → 数据验证 → 注入测试环境
                                                      │
                                          测试完成 ───┘
                                                      │
                                          数据清理 ←──┘
```

| 阶段 | 规则 | 执行者 |
|------|------|-------|
| **生成** | 数据必须符合目标 Schema 和业务规则 | AI / CI |
| **验证** | 生成后运行 Schema 校验，不合法数据丢弃 | CI Gate |
| **注入** | 通过环境变量或测试 fixture 注入，禁止硬编码 | AI / CI |
| **隔离** | 每个测试运行使用独立数据集，防止交叉污染 | 测试框架 |
| **清理** | 测试完成后清理临时数据，防止数据泄漏 | CI / AI |

### 2.4 AI 生成测试数据特殊规则

| 规则 | 说明 | 验证方式 |
|------|------|---------|
| **禁止使用真实数据** | AI 不得从生产数据库复制数据到测试 | pre-send 扫描拦截 |
| **必须声明数据来源** | 测试数据生成脚本必须注明使用了哪种策略 | 代码审查 |
| **可重现性** | 使用固定 seed 的 Faker 确保测试可重现 | CI 重跑验证 |
| **边界覆盖** | 必须包含正常值、边界值、异常值三类 | 测试覆盖率检查 |
| **大小合理** | 单测试数据集不超过 100MB，超出使用流式生成 | CI 文件大小检查 |

---

## 第 3 章：缓存策略

### 3.1 缓存分层与 AI 要求

| 层级 | 实现 | AI 生成代码强制要求 |
|------|------|-------------------|
| **L1 本地** | sync.Map / LRU | 必须声明一致性级别，默认最终一致 |
| **L2 分布式** | Redis Cluster | 必须有 TTL、空值处理、随机偏移 |
| **L3 CDN** | CloudFront/Cloudflare | 禁止缓存动态内容/敏感数据 |
| **L4 DB** | 内置缓存 | AI 不直接配置，了解即可 |

**缓存失效模式**（选其一即可）：
| 模式 | 一致性 | 适用场景 |
|------|--------|---------|
| TTL 过期 | 最终一致 | 大部分场景（默认） |
| 主动失效 | 强一致 | 用户权限、订单状态 |
| 版本标签 | 强一致 | 精确控制，需人工审查 |

**AI 生成缓存代码前必须读取 `.omc/cache-ttl-policy.yaml`，TTL 不得硬编码。**

### 3.2 缓存异常防护（AI 必检项）

AI 生成缓存代码时必须包含以下防护，否则审查阻断：

| 风险 | 防护策略 | 代码要求 |
|------|---------|---------|
| **穿透**（key 不存在） | 空值缓存 + 参数校验 | 数据库无数据时缓存 NULL_MARKER，TTL=2min |
| **击穿**（热点失效） | 互斥锁 / 逻辑过期 | 使用 SETNX 分布式锁保护重建 |
| **雪崩**（集中过期） | 随机 TTL 偏移 | TTL ±20% jitter，来自缓存策略配置 |

```go
// 缓存读写模板 — AI 生成时必须包含空值处理和 TTL
func GetData(key string) (*Data, error) {
    val, err := cache.Get(key)
    if err == nil {
        if val == NULL_MARKER { return nil, nil }
        return unmarshal(val)
    }
    data, err := db.Query(key)
    if errors.Is(err, sql.ErrNoRows) {
        cache.Set(key, NULL_MARKER, 2*time.Minute) // 空值缓存
        return nil, nil
    }
    cache.Set(key, marshal(data), ttlWithJitter(30*time.Minute)) // 随机 TTL
    return data, nil
}
```

### 3.3 缓存可观测性

| 指标 | 告警阈值 | 用途 |
|------|---------|------|
| **命中率** | <60% 告警, <40% 紧急 | 策略有效性 |
| **P99 延迟** | >5ms(L1), >10ms(L2) | 性能监控 |
| **淘汰率** | >30% = 扩容 | 容量规划 |
| **穿透率** | >5% 告警 | 空值缓存配置 |

---

## 第 4 章：AI 缓存使用规则

### 4.1 AI 生成缓存代码的强制要求

| 规则 | 说明 | 违反后果 |
|------|------|---------|
| **必须声明一致性级别** | 每个缓存操作必须注明强一致/最终一致 | 代码审查阻断 |
| **必须处理空值** | 缓存未命中且数据库无数据时，必须缓存空值标记 | 缓存穿透风险 |
| **必须设置 TTL** | 禁止无 TTL 的缓存写入 | 内存泄漏、脏数据 |
| **必须使用随机 TTL** | TTL 必须包含随机偏移，防止雪崩 | 缓存雪崩风险 |
| **必须处理锁竞争** | 热点数据重建必须使用互斥锁 | 缓存击穿风险 |
| **禁止缓存敏感数据** | 密码、token、密钥不得写入任何缓存 | 违反 P5，安全事件 |
| **必须记录缓存命中率** | 关键缓存必须暴露命中率指标 | 可观测性缺失 |

### 4.2 AI 缓存代码模板

```yaml
# AI 生成缓存代码前必须遵循的模板
cache_code_template:
  required_sections:
    - name: "cache_key_design"
      rule: "key 必须有明确命名规范：{domain}:{entity}:{id}:{version}"

    - name: "ttl_definition"
      rule: "TTL 必须来自 .omc/cache-ttl-policy.yaml，不得硬编码"

    - name: "null_value_handling"
      rule: "数据库无数据时必须缓存 NULL_MARKER，TTL=2min"

    - name: "cache_invalidation"
      rule: "写操作必须清除或更新相关缓存"

    - name: "error_handling"
      rule: "缓存操作失败不得阻断业务流程（降级为直读 DB）"

    - name: "metrics"
      rule: "必须记录 cache_hit / cache_miss 计数器"

  prohibited_patterns:
    - "cache.Set(key, data)  // 无 TTL"
    - "cache.Get(key) // 无空值处理"
    - "cache.Set('password', pwd) // 缓存敏感数据"
    - "if cache.Get(key) == nil { db.Query(key) } // 无锁保护热点重建"
```

---

## 第 5 章：Code Review SLA

### 5.1 响应时间目标

时间从 PR 创建且 L0-L3 全部通过后开始计算。

| PR 类型 | 首次响应 | 完成审查 | 超时升级 |
|---------|---------|---------|---------|
| **P0 Hotfix** | 5 min | 15 min | 5min → on-call |
| **P1 紧急特性** | 15 min | 1 h | 15min → tech lead |
| **P2 日常特性** | 2 h | 4 h | 2h → reviewer + lead |
| **P3 重构/优化** | 4 h | 8 h | 4h → reviewer |
| **P4 文档/注释** | 8 h | 24 h | 8h → 自动标记 `needs-review` |
| **夜间 AI PR** | 次日 10:00 | 次日 14:00 | 未审查 → 阻塞合并 |

### 5.2 超时升级与队列管理

| 升级级别 | 触发条件 | 动作 |
|---------|---------|------|
| **L1 提醒** | 首次响应超过 SLA 50% | Slack DM 提醒 |
| **L2 升级** | 首次响应超时 | Slack @mention + email |
| **L3 紧急** | 完成审查超时 | 自动分配备用 reviewer + PagerDuty (P0/P1) |
| **L4 上报** | 超过 SLA 200% | 工程总监 + 写入周报 |

**队列规则**：
- 优先级：P0 Hotfix > P1 > 即将超时 PR > P2 > P3 > P4
- 每 reviewer 最多同时持有 3 个 PR
- 同作者的 PR 不分配同一 reviewer
- 夜间 AI PR 次日 10:00 开始批量审查，14:00 前完成

### 5.3 自动化预审查（AI Reviewer）

AI Reviewer 在 Human Reviewer 前完成自动审查，降低人工负载 50-70%。

| 检查项 | 执行方 | 阻断？ | 人工关注点 |
|--------|-------|:------:|-----------|
| 幻觉检测（API/符号/依赖） | AI 自动 | **是** | — |
| 安全检查（SQL/XSS/路径/密钥） | AI + SAST | **是** | — |
| Spec 对齐（AC 覆盖） | AI 自动 | **是** | — |
| 错误处理、缓存规则 | AI 自动 | 是 | — |
| 测试质量、架构一致 | AI 建议 | 警告 | 业务逻辑正确性 |
| 代码规范（lint/命名） | AI 自动 | lint=是 | 用户体验、架构权衡 |

**流程**：PR → L0-L3 通过 → AI Reviewer → 置信度≥0.7 → Human Review 队列；否则标记问题 + AI 自修 ≤3 轮。

---

## 第 5 章：环境特定的 AI 约束

### 5.1 环境约束矩阵

| 约束维度 | sandbox | dev | staging | prod |
|---------|---------|-----|---------|------|
| **代码创建** | 允许 | 允许（PR 方式） | 禁止（仅 CI 部署） | 禁止 |
| **代码删除** | 允许 | 允许（PR 方式） | 禁止 | 禁止 |
| **数据库读** | 允许（sandbox DB） | 允许（dev DB） | 允许（脱敏 DB） | **禁止直连** |
| **数据库写** | 允许（sandbox DB） | 允许（migration via PR） | 仅 CI 执行 migration | 仅 CI 执行 |
| **缓存读** | 允许 | 允许 | 允许 | 禁止直连 |
| **缓存写** | 允许 | 允许 | 仅 CI 部署时 | 禁止 |
| **API 调用** | 允许（限额 1000/日） | 允许（限额 5000/日） | 允许（限额 2000/日） | **禁止** |
| **模型级别** | 仅 Tier-3 | 最高 Tier-2 | 最高 Tier-2 | N/A |
| **文件系统** | 完全读写 | 分支内读写 | 只读 | 只读（日志） |
| **网络访问** | 出口白名单 | 内部 VPC | 隔离 VPC | 禁止 |
| **生产数据访问** | 禁止 | 禁止（仅脱敏） | 仅脱敏快照 | N/A（本身就是生产） |
| **Auto-merge** | 允许 | 禁止 | 禁止 | 禁止 |
| **自修轮次** | 5 轮 | 3 轮 | 2 轮 | N/A |
| **审计日志** | 无（可选） | 基础 | 全量 | 全量 + 合规 |

### 5.2 环境约束详解

| 环境 | AI 可执行 | AI 不可执行 |
|------|----------|------------|
| **sandbox** | CRUD 操作、auto-merge、5 轮自修 | API 超限额 |
| **dev** | 创建 PR、运行测试、lint、3 轮自修 | 合并 PR、操作生产配置 |
| **staging** | 触发 E2E、读取报告、性能分析 | 直写 DB、部署、改配置 |
| **prod** | 读取监控/日志、生成分析报告 | 任何写操作、部署、直连 DB/缓存/MQ |

**关键规则**：
- sandbox 超过 24h 无活动自动销毁；数据不可流向其他环境
- dev 所有变更必须走 PR 流程，禁止直接 push
- staging 部署由 CI 执行，使用 T-7d 生产脱敏快照
- prod AI 完全只读（监控指标、脱敏日志、告警历史）

### 5.3 环境越界检测

| 越界类型 | 严重级别 | 自动动作 |
|---------|---------|---------|
| AI 直连生产 DB | **CRITICAL** | 立即断开 + 告警 |
| AI 在生产环境执行写操作 | **CRITICAL** | 立即停止 + 告警 |
| 生产数据流入 dev | **HIGH** | 阻断 + 告警 |
| sandbox 数据流向其他环境 | **HIGH** | 阻断 + 清理 |
| AI 超模型级别调用 | **MEDIUM** | 降级模型 + 记录 |
| AI 超时自修轮次 | **LOW** | 停止自修 + 转人工 |

---

## 附录 A：快速参考

```
环境分层：
sandbox（实验）→ dev（开发）→ staging（预生产）→ prod（生产）
单向流动，禁止反向数据传递

数据脱敏：
公开→无需脱敏 | 内部→部分遮蔽 | 机密→不可逆替换 | 限制→完全移除

缓存防护：
穿透→布隆过滤器+空值缓存 | 击穿→互斥锁 | 雪崩→随机TTL

Review SLA：
P0 Hotfix: 5min 响应 / 15min 完成
P1 紧急:   15min 响应 / 1h 完成
P2 日常:   2h 响应 / 4h 完成
P3 重构:   4h 响应 / 8h 完成

AI 环境约束：
sandbox=自由实验 | dev=PR 门禁 | staging=只读+CI 部署 | prod=完全只读
```

## 附录 B：版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **v5.4** | **2026-04-18** | **初始版本 — 环境管理、测试数据脱敏、环境晋升规则、缓存架构与异常防护、AI 缓存规则、Code Review SLA、自动化预审查、环境特定 AI 约束** |
