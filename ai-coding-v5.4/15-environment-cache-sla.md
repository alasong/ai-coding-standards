# AI Coding 规范 v5.4：环境管理、缓存策略与 Code Review SLA

> 版本：v5.4 | 2026-04-18
> 定位：大规模 Auto-Coding 场景下的环境治理、缓存架构设计、高并发 PR 审查 SLA
> 前置：[01-core-specification.md](01-core-specification.md) P1-P11、[06-cicd-pipeline.md](06-cicd-pipeline.md) L5 环境晋升、[13-deploy-rollback.md](13-deploy-rollback.md) 部署策略

---

## 第 1 章：环境管理

### 1.1 为什么需要独立的环境规范

06-cicd-pipeline.md 定义了 L5 环境晋升流程，但未回答以下问题：

- **环境定义缺失**：dev/staging/prod 各自的能力边界、数据隔离级别、AI 约束是什么？
- **测试数据管理**：AI 生成的代码需要测试数据，但生产数据不可直接用于测试，如何生成和脱敏？
- **环境晋升规则**：代码从 dev 到 prod 必须满足哪些条件？谁能批准晋升？
- **AI 环境约束**：AI 在不同环境中能做什么、不能做什么？

**核心原则**：环境是代码质量的放大器。设计良好的环境体系能让 AI 生成的代码在低成本环境（dev/staging）中被充分验证，仅将经过验证的代码推入生产。

### 1.2 环境定义与能力矩阵

| 环境 | 用途 | 数据源 | 部署频率 | 部署方式 | 回滚策略 |
|------|------|--------|---------|---------|---------|
| **dev** | 开发验证、单元测试、集成测试 | 合成数据 / 脱敏快照 | 每次 PR 创建 | CI 自动 | 重建容器 |
| **staging** | 预生产验证、E2E 测试、性能基线 | 生产脱敏快照（T-7d） | 每次 main merge | CI + 金丝雀 | 蓝绿切换 |
| **prod** | 生产服务、真实用户 | 真实数据 | 金丝雀渐进 | 金丝雀 + 监控 | 自动回滚 |
| **sandbox** | AI 实验、原型验证、Poc | 完全合成数据 | 按需 | AI 自助 | 销毁重建 |

### 1.3 环境隔离规则

```
┌──────────────────────────────────────────────────────┐
│                    网络隔离层                          │
├──────────────────────────────────────────────────────┤
│                                                      │
│  sandbox ──→ dev ──→ staging ──→ prod                │
│  (单向流)     (单向流)   (单向流)   (终点)            │
│                                                      │
│  禁止反向流动：prod → dev = 违反 P10 数据分级           │
│  禁止跨环境直连：dev 不可直连 prod DB                  │
│  禁止环境泄漏：生产配置不得出现在 dev/staging 代码中     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

| 隔离维度 | dev | staging | prod | sandbox |
|---------|-----|---------|------|---------|
| **网络** | 内部 VPC | 隔离 VPC，仅通 CI | 生产 VPC，WAF 保护 | 独立 VPC，出口白名单 |
| **数据库** | 独立实例 / Docker | 独立实例，脱敏数据 | 生产实例，多可用区 | 独立实例，可频繁重建 |
| **缓存** | 独立 Redis / 内存 | 独立 Redis，预热数据 | 生产 Redis 集群 | 独立 Redis |
| **消息队列** | 独立 Topic | 独立 Topic | 生产 Topic | 独立 Topic |
| **配置管理** | `.env.dev` | `.env.staging` | 密钥管理服务（KMS） | `.env.sandbox` |
| **日志保留** | 7 天 | 30 天 | 1 年 | 24 小时 |
| **监控级别** | 基础健康检查 | 全量指标 + 告警 | 全量 + SLO + 业务指标 | 无（按需开启） |

### 1.4 环境配置管理

```yaml
# .omc/environments.yaml
apiVersion: ai-coding/v5.4
kind: EnvironmentConfig

environments:
  sandbox:
    purpose: "AI 实验与原型验证"
    data_policy: synthetic_only
    ai_constraints:
      allowed_operations: [create, read, update, delete]
      max_api_calls_per_day: 1000
      model_tier_limit: tier-3
      auto_cleanup_hours: 24

  dev:
    purpose: "开发验证、单元/集成测试"
    data_policy: synthetic_or_masked
    ai_constraints:
      allowed_operations: [create, read, update, delete]
      max_api_calls_per_day: 5000
      model_tier_limit: tier-2
      auto_cleanup_hours: null

  staging:
    purpose: "预生产验证、E2E、性能基线"
    data_policy: masked_production_snapshot
    ai_constraints:
      allowed_operations: [read, deploy, test]
      max_api_calls_per_day: 2000
      model_tier_limit: tier-2
      write_restricted: true  # 禁止 AI 直接写入生产数据

  prod:
    purpose: "生产服务"
    data_policy: real_data
    ai_constraints:
      allowed_operations: [read, monitor]
      max_api_calls_per_day: 0  # AI 不直接操作
      model_tier_limit: null
      write_restricted: true
      direct_access: false  # AI 不可直连
```

**P22 IP 不暴露规则**：所有环境的 IP、域名、端点必须通过环境变量或配置中心获取，禁止硬编码在代码中。

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

## 第 3 章：环境晋升规则

### 3.1 晋升路径

```
sandbox (实验)
    │  原型验证通过 → 人工确认
    ▼
dev (开发)
    │  代码创建 PR → L0-L4 全部通过
    ▼
staging (预生产)
    │  PR 合并到 main → L5 环境晋升 → 冒烟测试通过
    ▼
prod (生产)
    │  金丝雀 5% → 25% → 50% → 100%
    ▼
production (全量)
```

### 3.2 晋升门禁

| 晋升路径 | 前置条件 | 验证项 | 审批方式 |
|---------|---------|--------|---------|
| **sandbox → dev** | 原型功能可用 | 代码可编译、基础测试通过 | AI 自助 |
| **dev → staging** | PR 创建 + L0-L4 全绿 | 06-cicd-pipeline.md L0-L4 全部通过 | AI + Human Reviewer |
| **staging → prod** | PR 合并到 main | 冒烟测试通过 + 金丝雀健康检查 | L2/L3 自动，L4 自动，L1 人工 |

### 3.3 晋升失败处理

| 失败阶段 | 自动动作 | 通知对象 | 恢复方式 |
|---------|---------|---------|---------|
| **L0 阻断** | 拒绝 commit | 开发者本地 | 修正后重新 commit |
| **L1-L2 阻断** | 标记 PR 为 failed | PR 作者 + Slack | AI 自修 ≤3 轮 → 转人工 |
| **L3 阻断** | 标记 PR 为 blocked | 安全团队 + PR 作者 | 安全漏洞=人工修复；幻觉=AI 自修 |
| **L4 阻断** | 拒绝合并 | PR 作者 + 审查者 | AI 自修 ≤3 轮 → 转人工 |
| **staging 冒烟失败** | 自动回滚 staging | on-call + 技术负责人 | 分析根因，修复后重新部署 |
| **金丝雀失败** | 自动回收流量 | on-call + PagerDuty | 自动回滚，记录到事故报告 |

### 3.4 紧急晋升通道（Hotfix）

| 条件 | 流程 | 事后要求 |
|------|------|---------|
| **P0 生产事故** | 跳过 dev/staging，直接金丝雀 5% → 验证 → 100% | 24h 内补齐 L0-L4 验证 + 事故复盘 |
| **安全漏洞修复** | L0-L3 必须在 hotfix 分支运行，L4 可异步 | 48h 内完成 E2E 验证 |
| **数据修复脚本** | 必须在 staging 验证后人工审批执行 | 执行结果审计记录 |

**核心规则**：紧急通道不等于无验证通道。所有安全相关检查（L0 密钥扫描、L3 SAST）不得跳过。

---

## 第 4 章：缓存策略

### 4.1 缓存分层架构

```
┌─────────────────────────────────────────────────────┐
│                  应用层                               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  L1: 本地缓存（进程内, TTL=1-5min）                   │
│      - 计算结果缓存                                    │
│      - 配置缓存                                       │
│      - 会话状态                                       │
│      实现: sync.Map, local-cache, LRU                │
│                                                     │
│  L2: 分布式缓存（Redis/Memcached, TTL=5min-24h）      │
│      - 用户会话                                       │
│      - 热点数据（排行榜、配置中心）                     │
│      - API 响应缓存                                   │
│      实现: Redis Cluster, Memcached                  │
│                                                     │
│  L3: CDN 缓存（边缘节点, TTL=1h-7d）                  │
│      - 静态资源                                       │
│      - API 公共响应（OpenAPI Spec、SDK）              │
│      实现: CloudFront, Cloudflare                    │
│                                                     │
│  L4: 数据库缓存（Query Cache, Buffer Pool）           │
│      - 查询结果集                                     │
│      - 索引缓存                                       │
│      实现: DB 内置（PostgreSQL shared_buffers）       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 4.2 缓存选型指南

| 缓存层级 | 适用场景 | 淘汰策略 | 一致性模型 | 典型 TTL |
|---------|---------|---------|-----------|---------|
| **L1 本地** | 高频读、低延迟、小数据量 | LRU / TTL | 最终一致（多实例不一致） | 1-5 min |
| **L2 分布式** | 跨实例共享、中等数据量 | LRU / LFU / TTL | 强一致（单写） / 最终一致（多写） | 5 min - 24 h |
| **L3 CDN** | 静态资源、公共 API | TTL + 手动清除 | 最终一致 | 1 h - 7 d |
| **L4 DB** | 查询优化 | DB 自动管理 | 强一致 | DB 自动 |

### 4.3 缓存失效模式（Cache Invalidation Patterns）

| 模式 | 说明 | 适用场景 | 一致性 | 实现复杂度 |
|------|------|---------|--------|-----------|
| **TTL 过期** | 数据到期自动失效 | 大部分场景 | 最终一致 | 低 |
| **主动失效** | 写操作时主动清除相关缓存 | 强一致性要求 | 强一致 | 中 |
| **惰性失效** | 读取时检查版本，过期则重新加载 | 读多写少 | 最终一致 | 低 |
| **版本标签** | 缓存 key 携带版本号，数据变更时升级版本 | 精确控制 | 强一致 | 中 |
| **事件驱动** | 数据变更事件触发缓存失效 | 微服务、事件溯源 | 最终一致 | 高 |
| **广播失效** | 写操作广播失效消息到所有节点 | 分布式系统 | 强一致 | 高 |

```yaml
# .omc/cache-invalidation.yaml
apiVersion: ai-coding/v5.4
kind: CacheInvalidationPolicy

policies:
  - name: "user-profile"
    cache_layer: L2
    invalidation: "active-on-write"
    ttl_minutes: 30
    key_pattern: "user:profile:{user_id}"
    on_write:
      - action: "delete"
        key_pattern: "user:profile:{user_id}"
      - action: "delete"
        key_pattern: "user:permissions:{user_id}"

  - name: "product-catalog"
    cache_layer: L2
    invalidation: "version-tag"
    ttl_minutes: 60
    key_pattern: "product:catalog:v{version}"
    on_write:
      - action: "increment_version"
        key: "product:catalog:version"

  - name: "api-response"
    cache_layer: L2
    invalidation: "ttl-expiry"
    ttl_minutes: 5
    key_pattern: "api:{method}:{path}:{query_hash}"

  - name: "static-assets"
    cache_layer: L3
    invalidation: "cdn-purge"
    ttl_hours: 24
    on_write:
      - action: "purge_cdn"
        path_pattern: "/assets/**"
```

### 4.4 一致性保障

| 一致性级别 | 定义 | 适用场景 | 性能影响 |
|-----------|------|---------|---------|
| **强一致** | 写操作完成后，所有后续读操作返回最新值 | 用户权限、订单状态、余额 | 写性能降低 20-40% |
| **最终一致** | 写操作完成后，经过一段时间所有读操作返回最新值 | 产品目录、排行榜、推荐列表 | 无性能影响 |
| **会话一致** | 同一用户会话内的读操作返回一致数据 | 用户购物车、个人设置 | 低性能影响 |

**规则**：AI 生成缓存代码时，必须在函数文档注释中声明使用的一致性级别。默认为最终一致，强一致必须经过人工审查。

---

## 第 5 章：缓存异常防护

### 5.1 缓存穿透（Cache Penetration）

**定义**：请求的数据在缓存和数据库中都不存在，导致每次请求都打到数据库。

| 防护策略 | 说明 | 适用场景 |
|---------|------|---------|
| **布隆过滤器** | 在缓存前用 Bloom Filter 判断数据是否存在 | 大量不存在的 key |
| **空值缓存** | 数据库查询为空时，缓存一个空值标记（TTL 较短） | 少量不存在的 key |
| **参数校验** | 在缓存查询前校验请求参数合法性 | 恶意攻击场景 |

```go
// 空值缓存示例 — AI 生成缓存代码时必须包含空值处理
func GetUserProfile(userID string) (*UserProfile, error) {
    cacheKey := fmt.Sprintf("user:profile:%s", userID)

    // 1. 尝试从缓存读取
    val, err := cache.Get(cacheKey)
    if err == nil {
        if val == NULL_MARKER {
            return nil, nil  // 数据确实不存在
        }
        return unmarshal(val)
    }

    // 2. 缓存未命中，查询数据库
    profile, err := db.GetUserProfile(userID)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            // 数据库也没有，缓存空值标记（短 TTL）
            cache.Set(cacheKey, NULL_MARKER, 2*time.Minute)
            return nil, nil
        }
        return nil, err
    }

    // 3. 写入缓存
    cache.Set(cacheKey, marshal(profile), 30*time.Minute)
    return profile, nil
}
```

### 5.2 缓存击穿（Cache Breakdown）

**定义**：热点数据的缓存失效瞬间，大量并发请求同时打到数据库。

| 防护策略 | 说明 | 实现方式 |
|---------|------|---------|
| **互斥锁** | 缓存失效时仅允许一个请求重建缓存，其他等待 | `SETNX` 分布式锁 |
| **逻辑过期** | 缓存值包含过期时间，过期后异步重建，旧值继续服务 | 缓存值包装 `{data, expire_at}` |
| **预加载** | 在过期前主动刷新缓存 | 后台定时任务 |

```go
// 互斥锁重建缓存 — AI 必须实现锁机制防止并发击穿
func GetHotData(key string) (string, error) {
    val, err := cache.Get(key)
    if err == nil {
        return val, nil
    }

    // 缓存失效，尝试获取锁
    lockKey := fmt.Sprintf("lock:%s", key)
    acquired, err := cache.SetNX(lockKey, "1", 10*time.Second)
    if err != nil {
        return "", err
    }

    if acquired {
        // 获取到锁，重建缓存
        data, err := db.Query(key)
        if err != nil {
            return "", err
        }
        cache.Set(key, data, 30*time.Minute)
        cache.Delete(lockKey)
        return data, nil
    }

    // 未获取到锁，等待后重试
    time.Sleep(50 * time.Millisecond)
    return cache.Get(key)
}
```

### 5.3 缓存雪崩（Cache Avalanche）

**定义**：大量缓存在同一时间过期，导致数据库负载瞬间飙升。

| 防护策略 | 说明 | 效果 |
|---------|------|------|
| **随机 TTL** | 在基准 TTL 上增加随机偏移（±20%） | 打散过期时间点 |
| **分级过期** | 不同类别数据设置不同 TTL，避免集中过期 | 降低同时过期比例 |
| **多级缓存** | L1+L2 多层缓存，L2 雪崩时 L1 仍可用 | 降低数据库压力 |
| **限流降级** | 数据库请求超阈值时触发限流 | 防止数据库被打挂 |

```yaml
# .omc/cache-ttl-policy.yaml
apiVersion: ai-coding/v5.4
kind: CacheTTLPolicy

# 随机 TTL 偏移策略
ttl_randomization:
  enabled: true
  jitter_percent: 20  # ±20% 随机偏移

policies:
  - category: "user-session"
    base_ttl_minutes: 120
    min_ttl_minutes: 96
    max_ttl_minutes: 144
    refresh_before_expiry_minutes: 10

  - category: "api-response"
    base_ttl_minutes: 5
    min_ttl_minutes: 4
    max_ttl_minutes: 6

  - category: "product-catalog"
    base_ttl_minutes: 60
    min_ttl_minutes: 48
    max_ttl_minutes: 72
    refresh_before_expiry_minutes: 5

  - category: "config-data"
    base_ttl_minutes: 1440  # 24h
    min_ttl_minutes: 1152
    max_ttl_minutes: 1728
    refresh_strategy: "event-driven"  # 配置变更事件驱动刷新
```

### 5.4 淘汰策略（Eviction Policies）

| 策略 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| **LRU（最近最少使用）** | 通用场景 | 实现简单、效果好 | 对周期性访问不友好 |
| **LFU（最不经常使用）** | 访问频率差异大的场景 | 保护热点数据 | 对新数据不友好 |
| **TTL（过期淘汰）** | 时效性数据 | 保证数据新鲜度 | 需要配合其他策略 |
| **Random（随机淘汰）** | 缓存大小均匀的场景 | 极低开销 | 可能淘汰热点数据 |
| **ARC（自适应替换）** | 混合访问模式 | 自适应最优 | 实现复杂 |

**默认策略**：L2 分布式缓存使用 LRU + TTL 组合，L1 本地缓存使用 LRU。

---

## 第 6 章：AI 缓存使用规则

### 6.1 AI 生成缓存代码的强制要求

| 规则 | 说明 | 违反后果 |
|------|------|---------|
| **必须声明一致性级别** | 每个缓存操作必须注明强一致/最终一致 | 代码审查阻断 |
| **必须处理空值** | 缓存未命中且数据库无数据时，必须缓存空值标记 | 缓存穿透风险 |
| **必须设置 TTL** | 禁止无 TTL 的缓存写入 | 内存泄漏、脏数据 |
| **必须使用随机 TTL** | TTL 必须包含随机偏移，防止雪崩 | 缓存雪崩风险 |
| **必须处理锁竞争** | 热点数据重建必须使用互斥锁 | 缓存击穿风险 |
| **禁止缓存敏感数据** | 密码、token、密钥不得写入任何缓存 | 违反 P5，安全事件 |
| **必须记录缓存命中率** | 关键缓存必须暴露命中率指标 | 可观测性缺失 |

### 6.2 AI 缓存代码模板

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

### 6.3 缓存可观测性

| 指标 | 计算方式 | 告警阈值 | 用途 |
|------|---------|---------|------|
| **缓存命中率** | hits / (hits + misses) | < 60% 告警，< 40% 紧急 | 缓存策略有效性 |
| **缓存延迟** | 缓存读写 P99 延迟 | > 5ms (L1), > 10ms (L2) | 缓存性能 |
| **缓存容量使用率** | 已用容量 / 总容量 | > 80% 告警 | 容量规划 |
| **淘汰率** | 淘汰数 / 总写入数 | > 30% = 缓存不足 | 扩容决策 |
| **缓存穿透率** | 数据库空结果数 / 总查询数 | > 5% 告警 | 空值缓存配置 |
| **热 key 集中度** | Top 10 key 访问量 / 总访问量 | > 50% 告警 | 热点分解 |

---

## 第 7 章：Code Review SLA

### 7.1 为什么需要 Review SLA

大规模 Auto-Coding = 每天数十至数百个 AI 生成的 PR。没有 SLA 意味着：

- PR 堆积在 review 队列中，L3/L4 自主开发被人工审查阻塞
- 紧急 hotfix 等待 review 数小时，影响生产恢复
- Review 质量不稳定，不同 reviewer 标准不一
- AI Reviewer 和 Human Reviewer 的分工不清晰

**核心原则**：Review SLA 保证审查时效性，自动化预审查降低人工负载，分层审查保证质量与效率的平衡。

### 7.2 Review 响应时间目标

| PR 类型 | 首次响应时间 | 完成审查时间 | 超时升级 |
|---------|------------|-------------|---------|
| **P0 Hotfix** | 5 分钟 | 15 分钟 | 5min 未响应 → 通知 on-call |
| **P1 紧急特性** | 15 分钟 | 1 小时 | 15min 未响应 → 通知 tech lead |
| **P2 日常特性** | 2 小时 | 4 小时 | 2h 未响应 → 通知 reviewer + lead |
| **P3 重构/优化** | 4 小时 | 8 小时（1 工作日） | 4h 未响应 → 通知 reviewer |
| **P4 文档/注释** | 8 小时 | 24 小时（1 工作日） | 8h 未响应 → 自动标记 `needs-review` |
| **夜间 AI PR** | 次日 10:00 | 次日 14:00 | 未审查 → 阻塞合并 |

**说明**：时间从 PR 创建且 L0-L3 全部通过后开始计算。L0-L3 未通过的 PR 不计入 SLA。

### 7.3 超时升级流程

```
PR 创建 → [AI Reviewer 自动审查 → 通过] → 进入 Human Review 队列
                                                │
                           首次响应超时 ────────┤
                                                ▼
                              一级升级：通知 reviewer + Slack @mention
                                                │
                           完成审查超时 ────────┤
                                                ▼
                              二级升级：通知 tech lead + 加入 review 队列顶部
                                                │
                           紧急 PR 超时 ────────┤
                                                ▼
                              三级升级：通知工程总监 + 自动分配可用 reviewer
```

| 升级级别 | 触发条件 | 动作 | 通知方式 |
|---------|---------|------|---------|
| **L1 提醒** | 首次响应时间超过 SLA 50% | 提醒 reviewer 即将超时 | Slack DM |
| **L2 升级** | 首次响应超时 | 通知 reviewer + tech lead | Slack @mention + email |
| **L3 紧急** | 完成审查超时 | 自动分配备用 reviewer | Slack + PagerDuty（P0/P1） |
| **L4 上报** | 超过 SLA 200% | 通知工程总监 + 写入周报 | email + 周报 |

### 7.4 Review 队列管理

```
┌─────────────────────────────────────────────┐
│              Review Queue Manager            │
├─────────────────────────────────────────────┤
│                                             │
│  优先级排序：                                 │
│  1. P0 Hotfix（最高）                         │
│  2. P1 紧急特性                              │
│  3. 即将超时的 PR（SLA 剩余 < 30min）         │
│  4. P2 日常特性                              │
│  5. 超时 PR（自动提升优先级）                  │
│  6. P3 重构/优化                             │
│  7. P4 文档/注释（最低）                      │
│                                             │
│  分配策略：                                   │
│  - 每个 reviewer 最多同时持有 3 个 PR         │
│  - 超过 3 个时自动分配给负载最低的 reviewer    │
│  - 同一作者的 PR 不分配给同一 reviewer         │
│                                             │
└─────────────────────────────────────────────┘
```

### 7.5 Review 队列配置

```yaml
# .omc/review-queue.yaml
apiVersion: ai-coding/v5.4
kind: ReviewQueue

sla:
  p0_hotfix:
    first_response_minutes: 5
    completion_minutes: 15
    escalation_minutes: 5

  p1_urgent:
    first_response_minutes: 15
    completion_minutes: 60
    escalation_minutes: 15

  p2_daily:
    first_response_minutes: 120
    completion_minutes: 240
    escalation_minutes: 120

  p3_refactor:
    first_response_minutes: 240
    completion_minutes: 480
    escalation_minutes: 240

  p4_docs:
    first_response_minutes: 480
    completion_minutes: 1440
    escalation_minutes: 480

queue:
  max_per_reviewer: 3
  auto_assign: true
  same_author_reviewer_conflict: true  # 同作者 PR 不分配同一 reviewer
  night_batch_review: true  # 夜间 AI PR 次日早晨批量审查
  night_batch_start: "10:00"
  night_batch_deadline: "14:00"
```

---

## 第 8 章：自动化预审查

### 8.1 AI Reviewer 自动审查

在 Human Reviewer 介入前，AI Reviewer 必须完成自动审查，降低人工负载。

```
PR 创建 → L0-L3 Pipeline 通过 → AI Reviewer 自动审查
                                     │
                          ┌──────────┴──────────┐
                          ▼                     ▼
                    审查通过                审查不通过
                    (置信度≥0.7)            (置信度<0.7 或发现问题)
                          │                     │
                          ▼                     ▼
                    进入 Human              标记问题 + 通知 AI
                    Review 队列              自修 ≤3 轮
```

### 8.2 AI Reviewer 审查清单

| 类别 | 检查项 | 自动/人工 | 阻断？ |
|------|--------|---------|:------:|
| **幻觉检测** | API 存在性、符号引用、依赖版本 | AI 自动 | **是** |
| **代码规范** | lint、命名、注释一致性 | AI 自动 | lint 错误=是 |
| **安全检查** | SQL 注入、XSS、路径穿越、密钥 | AI + SAST | **是** |
| **Spec 对齐** | 实现是否覆盖所有 AC | AI 自动 | **是** |
| **测试质量** | 断言合理性、覆盖路径、Mock 必要性 | AI 建议 | 警告 |
| **架构一致** | 不违反 ADR、无循环依赖 | AI 建议 | 警告 |
| **缓存规则** | TTL、空值处理、敏感数据 | AI 自动 | 敏感数据=是 |
| **错误处理** | 无吞错误、边界检查 | AI 自动 | **是** |

### 8.3 AI Reviewer 输出格式

```json
{
  "pr_id": "PR-142",
  "reviewer": "ai-reviewer-v2",
  "timestamp": "2026-04-18T10:30:00Z",
  "overall_status": "passed_with_comments",
  "confidence_score": 0.85,

  "checks": {
    "hallucination_scan": {
      "status": "passed",
      "details": "所有 API 引用已验证存在"
    },
    "security_scan": {
      "status": "passed",
      "details": "无 SQL 注入、XSS、路径穿越风险"
    },
    "spec_alignment": {
      "status": "passed",
      "ac_covered": ["AC-1", "AC-2", "AC-3"],
      "ac_not_covered": []
    },
    "cache_rules": {
      "status": "passed",
      "details": "所有缓存操作有 TTL，无敏感数据"
    },
    "error_handling": {
      "status": "passed",
      "details": "所有错误被返回或处理"
    }
  },

  "comments": [
    {
      "type": "suggestion",
      "file": "src/cache.go",
      "line": 42,
      "message": "建议在此处添加 metrics 计数器记录缓存命中率"
    }
  ],

  "human_review_focus": [
    "业务逻辑正确性（AI 无法验证业务语义）",
    "用户体验影响",
    "架构权衡是否合理"
  ]
}
```

### 8.4 预审查降低人工负载的效果

| 场景 | 无预审查 | 有预审查 | 效率提升 |
|------|---------|---------|---------|
| **幻觉问题** | 人工逐个检查 | AI 自动拦截 | 人工节省 80% |
| **规范问题** | 人工指出格式问题 | AI 自动修复 | 人工节省 60% |
| **安全问题** | 人工识别漏洞 | AI + SAST 双重拦截 | 人工节省 90% |
| **Spec 对齐** | 人工对照 Spec | AI 自动映射 AC | 人工节省 70% |
| **剩余人工** | — | 专注业务逻辑、架构权衡 | 审查时间减少 50-70% |

---

## 第 9 章：环境特定的 AI 约束

### 9.1 环境约束矩阵

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

### 9.2 环境约束详解

#### Sandbox 环境

- **目的**：AI 实验、原型验证、技术 PoC
- **自由度最高**：允许 AI 进行创建、修改、删除操作
- **自动清理**：超过 24 小时无活动的 sandbox 自动销毁
- **数据隔离**：sandbox 数据严格隔离，不可流向其他环境
- **成本控制**：API 调用有日限额，超出后降级到最低成本模型

#### Dev 环境

- **目的**：开发验证、单元测试、集成测试
- **PR 门禁**：所有代码变更必须通过 PR 流程，禁止直接 push
- **数据限制**：仅使用合成数据或脱敏数据
- **AI 可执行**：创建 PR、运行测试、执行 lint、Self-Correction（≤3 轮）
- **AI 不可执行**：合并 PR（需 Human Reviewer）、操作生产配置

#### Staging 环境

- **目的**：预生产验证、E2E 测试、性能基线
- **只读为主**：AI 仅可读取 staging 环境状态和测试结果
- **部署由 CI**：代码部署由 CI Pipeline 执行，非 AI 直接操作
- **数据限制**：使用 T-7d 的生产脱敏快照
- **AI 可执行**：触发 E2E 测试、读取测试报告、生成性能分析
- **AI 不可执行**：直接写数据库、修改配置、部署代码

#### Production 环境

- **目的**：生产服务
- **AI 完全只读**：AI 仅可读取监控指标、日志（脱敏后）、告警信息
- **所有操作由 CI/Human**：部署、回滚、配置变更均由 CI Pipeline 或人工执行
- **禁止直连**：AI 不可直连生产数据库、缓存、消息队列
- **AI 可执行**：生成事故分析报告、建议回滚方案（需人工确认）、分析监控趋势
- **AI 不可执行**：任何写操作、部署操作、配置变更、数据查询

### 9.3 环境约束配置

```yaml
# .omc/environment-constraints.yaml
apiVersion: ai-coding/v5.4
kind: EnvironmentConstraints

environments:
  sandbox:
    ai_access:
      code_operations: [create, read, update, delete]
      db_operations: [read, write]
      api_calls_per_day: 1000
      max_model_tier: tier-3
      auto_merge: true
      self_correction_max_rounds: 5
      data_access: synthetic_only
      network: egress_allowlist
      auto_cleanup_hours: 24

  dev:
    ai_access:
      code_operations: [create, read, update]  # delete via PR
      db_operations: [read]  # write via migration PR
      api_calls_per_day: 5000
      max_model_tier: tier-2
      auto_merge: false
      self_correction_max_rounds: 3
      data_access: synthetic_or_masked
      network: internal_vpc

  staging:
    ai_access:
      code_operations: [read]
      db_operations: [read]
      api_calls_per_day: 2000
      max_model_tier: tier-2
      auto_merge: false
      self_correction_max_rounds: 2
      data_access: masked_production_snapshot
      network: isolated_vpc
      deploy: ci_only

  prod:
    ai_access:
      code_operations: []  # 无代码操作权限
      db_operations: []  # 无数据库权限
      api_calls_per_day: 0
      max_model_tier: null
      auto_merge: false
      self_correction_max_rounds: 0
      data_access: none
      network: none
      read_only:
        - monitoring_metrics
        - sanitized_logs
        - alert_history
      all_operations: human_or_ci_only
```

### 9.4 环境越界检测

| 越界类型 | 检测方式 | 严重级别 | 自动动作 |
|---------|---------|---------|---------|
| **AI 直连生产 DB** | 网络连接审计 + 配置检查 | **CRITICAL** | 立即断开连接 + 告警 |
| **生产数据流入 dev** | pre-send 扫描 + 数据水印 | **HIGH** | 阻断 + 告警 |
| **AI 在生产环境执行写操作** | 操作日志审计 | **CRITICAL** | 立即停止 + 告警 |
| **sandbox 数据流向其他环境** | 数据标签追踪 | **HIGH** | 阻断 + 清理 |
| **AI 超模型级别调用** | API 调用元数据检查 | **MEDIUM** | 降级模型 + 记录 |
| **AI 超时自修轮次** | Self-Correction 计数 | **LOW** | 停止自修 + 转人工 |

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
