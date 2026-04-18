# AI Coding 规范 v5.4：成本与吞吐管理

> 版本：v5.4 | 2026-04-18
> 定位：大规模 Auto-Coding 场景下的 API 成本控制、模型路由、吞吐优化、ROI 度量
> 前置：必须先阅读并理解 [01-core-specification.md](01-core-specification.md)

---

## 第 1 章：成本原则

### 1.1 核心成本原则

| # | 原则 | 说明 |
|---|------|------|
| **C1** | **预算先行** | 所有 AI 使用必须有明确的预算上限，超预算自动阻断 |
| **C2** | **模型分级** | 按任务复杂度选择模型，禁止过度使用高价模型 |
| **C3** | **Token 效率** | 每个 Prompt 必须优化 Token 用量，禁止无意义上下文堆砌 |
| **C4** | **可追溯** | 每次 API 调用的成本必须可追溯到任务/PR/Feature |
| **C5** | **ROI 正向** | AI 编码的 ROI 必须持续为正，否则自动降级 |

### 1.2 成本与自治等级的关系

| 成本项 | L1 | L2 | L3 | L4 |
|--------|----|----|----|----|
| **预算审批** | 人工逐笔 | 周度预算包 | 月度预算包 | 季度预算+AI 自优化 |
| **模型选择** | 人工指定 | AI 建议+人工确认 | AI 自主路由 | AI 自主路由+审计 |
| **成本追踪** | 手动记录 | 自动追踪到 PR | 自动追踪到 Feature | 同 L3 + 自动报表 |
| **超预算处理** | 立即停止 | 告警+等待审批 | 告警+自动降级模型 | 告警+自动优化 |

---

## 第 2 章：API 成本预算

### 2.1 预算层级

| 层级 | 周期 | 适用对象 | 告警阈值 | 阻断阈值 |
|------|------|---------|---------|---------|
| **组织级** | 月度 | 整个团队/部门 | 80% | 100% |
| **项目级** | 月度 | 单个项目 | 80% | 100% |
| **团队级** | 周度 | 开发小组 | 75% | 90% |
| **个人级** | 日度 | 单个开发者/AI Agent | 70% | 85% |

### 2.2 预算配置模板

```yaml
# .omc/cost-budget.yaml
apiVersion: ai-coding/v5.4
kind: CostBudget
metadata:
  project: my-project
  period: 2026-04

spec:
  monthly_budget_usd: 5000
  daily_budget_usd: 200
  alerts:
    - threshold: 0.50   # 50%
      action: notify     # 通知负责人
      channel: "#ai-cost-alerts"
    - threshold: 0.80   # 80%
      action: warn       # 告警+要求审批
      channel: "#ai-cost-alerts"
    - threshold: 0.95   # 95%
      action: throttle   # 降级到廉价模型
    - threshold: 1.00   # 100%
      action: halt       # 停止非关键调用
  exemptions:
    - feature: "security-patch"  # 安全修复不受预算限制
    - feature: "hotfix"           # 紧急修复不受预算限制
```

### 2.3 预算执行规则

| 规则 | 说明 | 执行方式 |
|------|------|---------|
| **滚动预测** | 基于当前消耗速率预测月底总支出 | 每日计算，剩余天数 * 日均消耗 + 已消耗 |
| **预留缓冲** | 预算的 15% 必须预留用于紧急任务 | 不可分配给日常 Auto-Coding |
| **跨期结转** | 未用完的预算可结转 30%，上限 20% | 自动计算到下月预算 |
| **预算调整** | 月中可申请调整，需人工审批 | 通过 `.gate/budget-change.json` 记录 |

### 2.4 成本分摊模型

| 分摊维度 | 计算方式 | 用途 |
|---------|---------|------|
| **按 PR** | PR 生命周期内所有 API 调用之和 | PR 成本评审、效率对比 |
| **按 Feature** | Spec 关联的所有 API 调用之和 | Feature ROI 分析 |
| **按模块** | 修改的文件所属模块的 API 调用之和 | 模块级成本优化 |
| **按 Agent** | 每个 Agent 的 API 调用之和 | Agent 效率对比 |
| **按模型** | 每个模型的 API 调用之和 | 模型路由优化 |

---

## 第 3 章：模型路由策略

### 3.1 模型分级与定价参考

| 级别 | 模型示例 | 相对成本 | 能力级别 | 适用场景 |
|------|---------|---------|---------|---------|
| **Tier-1 旗舰** | Claude Opus, GPT-4o | 10x | 最高推理、复杂设计 | 架构设计、复杂 Bug 诊断、安全审查 |
| **Tier-2 标准** | Claude Sonnet, GPT-4o-mini | 3x | 强编码、良好推理 | 核心逻辑编码、代码审查、测试生成 |
| **Tier-3 轻量** | Claude Haiku, GPT-3.5-turbo | 1x | 快速响应、简单任务 | 代码补全、注释生成、格式化、lint 修复 |
| **Tier-4 专用** | Codex, StarCoder | 0.5x | 编码专用 | 纯代码补全、语法修正 |

### 3.2 路由决策树

```
任务进入
  │
  ├─ 是否涉及架构决策/系统设计？
  │   └─ YES → Tier-1（Opus）
  │   └─ NO ↓
  ├─ 是否涉及安全/加密/权限逻辑？
  │   └─ YES → Tier-1（Opus）
  │   └─ NO ↓
  ├─ 是否为核心业务逻辑（>20 行）？
  │   └─ YES → Tier-2（Sonnet）
  │   └─ NO ↓
  ├─ 是否为测试生成/代码审查/文档同步？
  │   └─ YES → Tier-2（Sonnet）
  │   └─ NO ↓
  ├─ 是否为代码补全/格式化/lint 修复/注释？
  │   └─ YES → Tier-3（Haiku）
  │   └─ NO ↓
  └─ 默认 → Tier-2（Sonnet）
```

### 3.3 路由配置

```yaml
# .omc/model-routing.yaml
apiVersion: ai-coding/v5.4
kind: ModelRouting
spec:
  rules:
    - name: "architecture-design"
      trigger: "方案设计文档生成"
      model: tier-1
      max_tokens: 8000
    - name: "core-implementation"
      trigger: "核心业务逻辑实现"
      model: tier-2
      max_tokens: 4000
    - name: "test-generation"
      trigger: "测试代码生成"
      model: tier-2
      max_tokens: 3000
    - name: "code-review"
      trigger: "AI Code Review"
      model: tier-2
      max_tokens: 4000
    - name: "lint-fix"
      trigger: "Lint/格式修复"
      model: tier-3
      max_tokens: 1000
    - name: "comment-generation"
      trigger: "注释/文档生成"
      model: tier-3
      max_tokens: 1500
    - name: "code-completion"
      trigger: "代码补全"
      model: tier-4
      max_tokens: 500
  fallback:
    - condition: "tier-1 rate limited"
      fallback_to: tier-2
    - condition: "budget exceeded 90%"
      fallback_to: tier-3
```

### 3.4 动态路由调整

| 触发条件 | 调整动作 | 恢复条件 |
|---------|---------|---------|
| 预算消耗 > 80% | Tier-1 → Tier-2，Tier-2 → Tier-3 | 预算恢复至 < 70% |
| 预算消耗 > 95% | 所有任务 → Tier-3 | 预算审批通过 |
| 模型响应时间 > 30s | 降级到下一级模型 | 原模型响应恢复 |
| 连续 3 次调用失败 | 切换到备用模型 | 原模型恢复 |
| 月度预算耗尽 | 仅允许 Tier-4 + 紧急豁免 | 次月预算生效 |

### 3.5 模型性能基线

| 指标 | Tier-1 | Tier-2 | Tier-3 | Tier-4 |
|------|--------|--------|--------|--------|
| **一次通过率** | ≥ 85% | ≥ 70% | ≥ 50% | ≥ 35% |
| **平均响应时间** | ≤ 15s | ≤ 8s | ≤ 3s | ≤ 1s |
| **幻觉率** | < 2% | < 5% | < 10% | < 15% |
| **适用 Token 范围** | 4K-32K | 2K-8K | 0.5K-3K | 0.5K-1K |

**路由优化规则**：如果某类任务在 Tier-2 的一次通过率连续 10 次 ≥ 90%，则降级为 Tier-3；如果连续 5 次 < 50%，则升级为 Tier-1。

---

## 第 4 章：Prompt 优化

### 4.1 Token 优化策略

| 策略 | 说明 | 预期节省 |
|------|------|---------|
| **上下文裁剪** | 移除与当前任务无关的文件和代码段 | 20-40% |
| **符号引用替代全文** | 用 `函数签名` 替代完整函数体 | 30-50% |
| **增量上下文** | 仅发送变更部分 + 接口契约，不发送完整文件 | 40-60% |
| **系统 Prompt 缓存** | 系统 Prompt 使用缓存前缀（Anthropic Prompt Caching） | 50-80% input cost |
| **示例精简** | 每个规则仅保留 1 个最优示例，不堆砌 | 15-25% |
| **去重压缩** | 合并重复的指令和约束 | 10-20% |

### 4.2 Prompt 分层加载

与 [01-core-specification.md](01-core-specification.md) 第 3.2 节 Progressive Disclosure 对齐：

| 优先级 | 内容 | 加载时机 | Token 预算 |
|--------|------|---------|-----------|
| **P0 必须** | Spec 文件、接口契约、验收标准 | 每次任务 | ≤ 1000 tokens |
| **P1 按需** | 相关文件片段、架构约束 | 首次提到时 | ≤ 3000 tokens |
| **P2 可选** | 商业计划、项目历史、领域知识 | 手动注入 | ≤ 5000 tokens |
| **P3 禁止** | 密钥、敏感配置、内部 IP | 永不加载 | 0 tokens |

### 4.3 上下文压缩规则

```
原始上下文 → [移除空白/注释] → [提取关键符号] → [压缩指令] → [缓存前缀] → 发送
```

| 压缩阶段 | 动作 | 保留内容 |
|---------|------|---------|
| **去除冗余** | 移除注释、空行、import 列表 | 保留函数体和类型定义 |
| **符号提取** | 提取函数签名、接口定义、类型声明 | 保留契约，移除实现细节 |
| **指令压缩** | 合并重复约束，使用引用替代描述 | 保留核心约束 |
| **缓存前缀** | 将不变的上下文（系统 Prompt、架构约束）标记为缓存前缀 | 利用 Prompt Caching |

### 4.4 Prompt 模板规范

```yaml
# prompts/template-v2.yaml
id: feature-impl-v2
version: 2.0
model: tier-2
max_input_tokens: 4000
max_output_tokens: 2000
system_prompt_cached: true  # 利用 Prompt Caching

sections:
  - name: "system"
    priority: P0
    content: "你是一个 Go 后端开发助手。遵循项目编码规范，见 @core-spec.md"
    cache: true

  - name: "spec"
    priority: P0
    content: "{{ spec_file }}"
    max_tokens: 1500

  - name: "context"
    priority: P1
    content: "{{ related_symbols }}"  # 仅符号引用，非全文
    max_tokens: 2000

  - name: "instruction"
    priority: P0
    content: "基于上述 Spec 实现代码。遵循 TDD 先行原则。"
    max_tokens: 200
```

### 4.5 Prompt 效率指标

| 指标 | 目标 | 告警阈值 |
|------|:----:|---------|
| **Token/函数** | ≤ 500 | > 1000 |
| **Prompt 一次通过率** | ≥ 70% | < 50% |
| **上下文命中率** | ≥ 60%（AI 确实使用了加载的上下文） | < 30% |
| **系统 Prompt 缓存命中率** | ≥ 80% | < 50% |
| **冗余上下文比例** | < 20% | > 40% |

---

## 第 5 章：上下文复用策略

### 5.1 上下文缓存架构

```
┌─────────────────────────────────────────────────┐
│               Context Cache Layer               │
├─────────────────────────────────────────────────┤
│                                                 │
│  L1: Hot Cache (内存, TTL=30min)                │
│      - 当前任务的活跃上下文                       │
│      - 最近 3 个任务的上下文                      │
│                                                 │
│  L2: Warm Cache (磁盘, TTL=24h)                 │
│      - 系统 Prompt 缓存（缓存前缀）              │
│      - 常用架构约束和编码规范                    │
│      - 频繁引用的符号表                         │
│                                                 │
│  L3: Cold Cache (持久化, TTL=7d)                │
│      - 历史任务上下文索引                        │
│      - 项目知识库引用                           │
│      - 领域知识文档摘要                         │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 5.2 缓存复用规则

| 缓存项 | 复用范围 | 失效条件 | 节省估算 |
|--------|---------|---------|---------|
| **系统 Prompt** | 所有任务（同项目） | 规范变更 | 每次调用节省 300-800 tokens |
| **编码规范** | 所有任务（同项目） | 规范变更 | 每次调用节省 500-1500 tokens |
| **接口契约** | 同模块任务 | 接口变更 | 每次调用节省 200-600 tokens |
| **架构约束** | 所有任务（同项目） | 架构决策变更 | 每次调用节省 100-400 tokens |
| **符号表** | 同文件/模块任务 | 文件变更 | 每次调用节省 100-300 tokens |
| **历史任务上下文** | 相关任务 | 7 天过期 | 新任务节省 200-500 tokens |

### 5.3 上下文复用配置

```yaml
# .omc/context-cache.yaml
apiVersion: ai-coding/v5.4
kind: ContextCache
spec:
  hot_cache:
    ttl_minutes: 30
    max_entries: 5
    eviction: LRU
  warm_cache:
    ttl_hours: 24
    max_size_mb: 100
    items:
      - system_prompt
      - coding_standards
      - architecture_constraints
      - symbol_table
  cold_cache:
    ttl_days: 7
    index_type: semantic_search
  cache_invalidation:
    - trigger: "git commit to main"
      action: "invalidate affected symbols"
    - trigger: "architecture decision updated"
      action: "invalidate architecture_constraints"
```

### 5.4 跨任务上下文传递

```
Task A 完成 → [提取关键决策] → [更新符号表] → [写入上下文索引]
                                                    │
                                                    ▼
Task B 启动 → [查询相关上下文] → [加载缓存项] → [组装 Prompt]
```

| 传递项 | 内容 | 用途 |
|--------|------|------|
| **决策记录** | Task A 做出的架构/设计决策 | Task B 保持一致性 |
| **符号变更** | 新增/修改的函数和类型 | Task B 知晓最新接口 |
| **经验教训** | Task A 遇到的问题和解决方案 | Task B 避免重复错误 |
| **规范调整** | Task A 发现的规范不足 | Task B 使用更新后的规范 |

---

## 第 6 章：吞吐优化

### 6.1 并行任务执行

```
┌─────────────────────────────────────────────┐
│              Task Orchestrator               │
├─────────────────────────────────────────────┤
│                                             │
│  Queue: [F001] [F002] [F003] [F004] [F005]  │
│         │      │      │                     │
│         ▼      ▼      ▼                     │
│     ┌──────┐┌──────┐┌──────┐                │
│     │Agent1││Agent2││Agent3│                │
│     └──────┘└──────┘└──────┘                │
│         │      │      │                     │
│         ▼      ▼      ▼                     │
│     [F001] [F002] [F003]  ← 并行执行         │
│                                             │
└─────────────────────────────────────────────┘
```

### 6.2 并行度控制

| 并行度 | 适用场景 | 最大并发任务数 | 注意事项 |
|--------|---------|-------------|---------|
| **低（1-2）** | 单开发者项目、高复杂度任务 | 2 | 避免上下文切换开销 |
| **中（3-5）** | 小团队、中等复杂度 | 5 | 注意文件冲突和依赖 |
| **高（6-10）** | 夜间工厂模式、L3/L4 | 10 | 需要严格的任务隔离 |
| **超高（10+）** | 大规模重构、批量生成 | 按需 | 需要专用编排器 |

### 6.3 任务依赖与调度

| 依赖类型 | 示例 | 调度策略 |
|---------|------|---------|
| **无依赖** | 独立 Feature 实现 | 立即并行执行 |
| **顺序依赖** | F002 依赖 F001 的接口 | F001 完成后再调度 F002 |
| **部分依赖** | F003 依赖 F001 的部分输出 | F001 产出接口后并行 |
| **资源竞争** | 多个任务修改同一文件 | 串行化或文件级锁定 |

### 6.4 批处理优化

| 场景 | 批处理策略 | 吞吐提升 |
|------|-----------|---------|
| **批量 Lint 修复** | 合并多个文件修复为一次调用 | 3-5x |
| **批量测试生成** | 按模块批量生成测试而非逐文件 | 2-3x |
| **批量代码审查** | 合并小 PR 为批量审查 | 2-4x |
| **批量注释生成** | 按文件批量生成文档注释 | 4-6x |
| **批量依赖更新** | 一次性处理所有过期依赖 | 3-5x |

### 6.5 管道效率优化

```
[Spec 读取] → [测试生成] → [实现生成] → [Self-Correction] → [Code Review] → [PR 创建]
     │            │             │              │                  │              │
     │ (可预加载)  │ (可并行)     │ (流水线)      │ (按需触发)        │ (可批量)      │ (自动)
```

| 优化项 | 说明 | 效果 |
|--------|------|------|
| **预加载** | 在任务排队时预加载 Spec 和上下文 | 减少等待时间 30-50% |
| **流水线** | 测试生成和实现生成可重叠执行 | 总耗时减少 20-30% |
| **异步审查** | AI Review 和 PR 创建异步执行 | 不阻塞后续任务 |
| **管道缓冲** | 每个阶段有缓冲区，避免阻塞传递 | 吞吐量提升 15-25% |
| **失败快返** | 编译/类型检查失败立即返回，不等待完整生成 | 减少浪费 40-60% |

### 6.6 夜间工厂模式

| 配置项 | 说明 |
|--------|------|
| **运行窗口** | 22:00 - 06:00（本地时间） |
| **任务队列** | 从 `specs/` 中读取 `status: ready` 的任务 |
| **最大并行度** | 5-10 个并发任务 |
| **模型策略** | 优先使用 Tier-2，必要时升级到 Tier-1 |
| **输出** | 每个任务产出独立 PR，不直接合并到 main |
| **次日审查** | 早晨由 Human Reviewer 批量审查夜间 PR |
| **失败处理** | 自修复 ≤ 3 轮，超过后标记为 `failed`，次日人工处理 |

---

## 第 7 章：ROI 度量

### 7.1 ROI 计算公式

```
AI 编码 ROI = (人类等效成本 - AI 实际成本) / AI 实际成本

其中：
  人类等效成本 = 等效人类工时 × 人类时薪
  AI 实际成本 = API 调用成本 + 人工审查成本 + 基础设施成本
```

### 7.2 成本构成

| 成本项 | 计算方式 | 占比参考 |
|--------|---------|---------|
| **API 调用成本** | Σ(每次调用的 token 数 × 单价) | 30-50% |
| **人工审查成本** | 审查工时 × 审查者时薪 | 30-40% |
| **基础设施成本** | CI 运行时间 × 单价 + 存储成本 | 10-20% |
| **返工成本** | 修复 AI 错误代码的工时 × 时薪 | 5-15% |
| **管理成本** | 任务编排、预算管理的工时 | 5-10% |

### 7.3 人类等效成本估算

| 任务类型 | 人类等效工时 | AI 实际工时 | 效率倍率 |
|---------|------------|------------|---------|
| **简单 CRUD** | 2-4 小时 | 5-15 分钟 | 8-16x |
| **中等业务逻辑** | 4-8 小时 | 15-45 分钟 | 5-16x |
| **复杂算法** | 8-16 小时 | 1-3 小时 | 3-8x |
| **架构设计** | 16-40 小时 | 2-6 小时 | 3-8x |
| **测试生成** | 4-8 小时 | 10-30 分钟 | 8-24x |
| **代码重构** | 4-12 小时 | 15-60 分钟 | 4-12x |
| **文档同步** | 2-4 小时 | 5-15 分钟 | 8-16x |

### 7.4 ROI 仪表盘

| 指标 | 计算方式 | 健康范围 | 告警阈值 |
|------|---------|---------|---------|
| **总体 ROI** | (等效成本 - 实际成本) / 实际成本 | ≥ 3.0 | < 1.5 |
| **每 PR 成本** | API 成本 + 审查成本 / PR 数 | ≤ 等效成本的 30% | > 等效成本的 50% |
| **每 Feature 成本** | Feature 关联的所有 API 调用 | ≤ 预算的 5% | > 预算的 10% |
| **每 Token 产出** | 有效代码行 / 总输入 Token | ≥ 0.01 行/token | < 0.005 行/token |
| **审查效率** | PR 审查时间 / PR 大小 | ≤ 人类手动编码的 50% | > 人类手动编码的 80% |

### 7.5 ROI 报告模板

```yaml
# .gate/roi-report-{week}.yaml
period: "2026-W16"
summary:
  total_api_cost_usd: 1250
  human_review_cost_usd: 800
  infrastructure_cost_usd: 200
  total_ai_cost_usd: 2250
  equivalent_human_cost_usd: 12000
  roi: 4.33  # (12000 - 2250) / 2250

breakdown_by_task:
  - task_type: "feature-impl"
    count: 15
    api_cost_usd: 750
    equivalent_human_hours: 60
    roi: 5.2
  - task_type: "test-generation"
    count: 20
    api_cost_usd: 200
    equivalent_human_hours: 25
    roi: 8.5
  - task_type: "code-review"
    count: 15
    api_cost_usd: 150
    equivalent_human_hours: 15
    roi: 3.0
  - task_type: "lint-fix"
    count: 30
    api_cost_usd: 50
    equivalent_human_hours: 5
    roi: 2.8

trend:
  - week: "W14"
    roi: 3.8
  - week: "W15"
    roi: 4.1
  - week: "W16"
    roi: 4.33  # 上升趋势 ✓
```

### 7.6 ROI 降级触发

| 条件 | 动作 |
|------|------|
| ROI 连续 2 周 < 1.5 | 分析根因，优化模型路由和 Prompt |
| ROI 连续 4 周 < 1.0 | 降低自治等级，增加人工参与 |
| 单任务成本 > 等效人类成本 | 立即停止该任务的 AI 执行，转人工 |
| 返工成本 > API 成本的 50% | 提升审查级别，切换更高质量模型 |

---

## 第 8 章：成本异常检测

### 8.1 异常检测规则

| 异常类型 | 检测规则 | 严重级别 | 自动动作 |
|---------|---------|---------|---------|
| **突增型** | 小时消耗 > 日均 3 倍 | HIGH | 告警 + 限流 |
| **持续型** | 连续 2 小时消耗 > 日均 2 倍 | MEDIUM | 告警 + 分析 |
| **偏离型** | 日消耗偏离 30 天均值 > 2σ | MEDIUM | 告警 |
| **模型异常** | 单个调用 > 预算的 5% | HIGH | 阻断 + 告警 |
| **频率异常** | 每分钟调用次数 > 基线 5 倍 | HIGH | 限流 + 告警 |
| **Token 异常** | 单次输出 > 预期 3 倍 | LOW | 记录 + 分析 |

### 8.2 基线计算

```
基线 = 过去 30 天的日均消耗
标准差 = 过去 30 天的日消耗标准差
异常阈值 = 基线 + 2 × 标准差
```

| 时间窗口 | 用途 | 计算频率 |
|---------|------|---------|
| **1 小时** | 实时异常检测 | 每 5 分钟 |
| **1 天** | 日度异常检测 | 每小时 |
| **7 天** | 周趋势分析 | 每日 |
| **30 天** | 月度基线和预算 | 每日 |

### 8.3 异常响应流程

```
检测到异常
    │
    ├─ 严重级别 = HIGH？
    │   └─ YES → [限流] → [告警] → [根因分析] → [修复/上报]
    │   └─ NO ↓
    ├─ 严重级别 = MEDIUM？
    │   └─ YES → [告警] → [持续监控] → [24h 后评估]
    │   └─ NO ↓
    └─ 严重级别 = LOW？
        └─ YES → [记录] → [周报中包含]
```

### 8.4 Kill Switch

| 触发条件 | 动作 | 恢复 |
|---------|------|------|
| 日预算耗尽 | 停止所有非 Tier-4 调用 | 次日重置或人工审批 |
| 单小时消耗 > 日预算 50% | 限流到 1 个并发任务 | 消耗恢复正常 |
| 检测到恶意/异常调用模式 | 立即停止所有 AI 调用 | 安全审计后恢复 |
| API 提供者返回异常错误率 > 50% | 切换到备用模型提供者 | 原提供者恢复 |

### 8.5 异常检测配置

```yaml
# .omc/anomaly-detection.yaml
apiVersion: ai-coding/v5.4
kind: AnomalyDetection
spec:
  baselines:
    - window: 30d
      metric: daily_cost_usd
      expected: 150
      stddev: 30
  rules:
    - name: "hourly-spike"
      condition: "hourly_cost > 3 * daily_average / 24"
      severity: HIGH
      action: ["throttle", "alert"]
    - name: "daily-deviation"
      condition: "daily_cost > baseline + 2 * stddev"
      severity: MEDIUM
      action: ["alert", "monitor"]
    - name: "single-call-expensive"
      condition: "call_cost > daily_budget * 0.05"
      severity: HIGH
      action: ["block", "alert"]
    - name: "frequency-spike"
      condition: "calls_per_minute > 5 * baseline_cpm"
      severity: HIGH
      action: ["throttle", "alert"]
  kill_switch:
    - condition: "daily_budget_consumed"
      action: "stop_non_tier4"
    - condition: "hourly_cost > daily_budget * 0.5"
      action: "limit_to_1_concurrent"
    - condition: "api_error_rate > 0.5"
      action: "switch_provider"
```

---

## 第 9 章：Per-Task 成本追踪

### 9.1 成本追踪架构

```
每次 API 调用 → [记录调用元数据] → [关联到 Task/PR/Feature]
                                            │
                                            ▼
                               ┌────────────────────────┐
                               │   Cost Attribution DB   │
                               ├────────────────────────┤
                               │ call_id, timestamp      │
                               │ task_id, pr_id, spec_id │
                               │ model, input_tokens     │
                               │ output_tokens, cost_usd  │
                               │ status, retry_count     │
                               └────────────────────────┘
                                            │
                                            ▼
                               ┌────────────────────────┐
                               │   Cost Reports          │
                               ├────────────────────────┤
                               │ Per-Task / Per-PR       │
                               │ Per-Feature / Per-Module│
                               │ Per-Model / Per-Agent   │
                               │ Daily / Weekly / Monthly│
                               └────────────────────────┘
```

### 9.2 调用记录格式

```json
{
  "call_id": "call-20260418-001",
  "timestamp": "2026-04-18T10:30:00Z",
  "task": {
    "spec_id": "F003",
    "pr_id": "PR-142",
    "feature": "user-authentication"
  },
  "model": "claude-sonnet-4-20250514",
  "tier": "tier-2",
  "tokens": {
    "input": 2500,
    "output": 800,
    "cache_read": 1800,
    "cache_hit_rate": 0.72
  },
  "cost_usd": 0.0185,
  "status": "success",
  "retry_count": 0,
  "duration_ms": 3200
}
```

### 9.3 成本聚合维度

| 维度 | 聚合方式 | 报表频率 |
|------|---------|---------|
| **Per Task** | 单个任务的累计成本 | 实时 |
| **Per PR** | PR 生命周期内所有调用 | PR 关闭时 |
| **Per Feature** | Spec 关联的所有调用 | Feature 完成时 |
| **Per Module** | 按代码模块归集 | 周度 |
| **Per Model** | 按模型归集 | 日度 |
| **Per Agent** | 按 Agent 归集 | 周度 |
| **Per Developer** | 按开发者归集 | 周度 |

### 9.4 成本报表

```yaml
# .gate/cost-report-{date}.yaml
date: "2026-04-18"
summary:
  total_calls: 156
  total_cost_usd: 45.20
  avg_cost_per_call_usd: 0.29
  cache_hit_rate: 0.68

by_task:
  - task_id: "F003"
    task_name: "用户认证"
    calls: 12
    cost_usd: 8.50
    model_breakdown:
      tier-1: { calls: 2, cost_usd: 4.00 }
      tier-2: { calls: 8, cost_usd: 4.00 }
      tier-3: { calls: 2, cost_usd: 0.50 }
    status: completed

  - task_id: "F004"
    task_name: "支付接口"
    calls: 18
    cost_usd: 15.30
    status: in-progress

by_model:
  tier-1: { calls: 5, cost_usd: 12.00, pct: 26.5 }
  tier-2: { calls: 85, cost_usd: 28.00, pct: 61.9 }
  tier-3: { calls: 66, cost_usd: 5.20, pct: 11.5 }

budget:
  daily_budget_usd: 200
  consumed_usd: 45.20
  consumed_pct: 0.226
  remaining_usd: 154.80
```

### 9.5 成本看板指标

| 指标 | 说明 | 健康范围 |
|------|------|---------|
| **日均消耗** | 过去 7 天日均 API 成本 | 在预算的 60-80% 范围内 |
| **单 PR 成本** | 每个 PR 的平均 AI 成本 | ≤ 人类等效成本的 30% |
| **缓存命中率** | Prompt Caching 的命中比例 | ≥ 60% |
| **重试率** | 需要重试的调用比例 | < 15% |
| **模型分布** | Tier-1/2/3 的调用比例 | Tier-1 < 10%, Tier-2 < 60%, Tier-3 > 30% |
| **任务完成率** | 成功完成的任务比例 | ≥ 80% |
| **成本/代码行** | 每 1000 行有效代码的 AI 成本 | ≤ 等效人类的 30% |

---

## 附录 A：快速参考

```
成本原则：
C1 预算先行 ── C2 模型分级 ── C3 Token 效率 ── C4 可追溯 ── C5 ROI 正向

模型路由：
Tier-1（架构/安全）→ Tier-2（核心逻辑/测试/审查）→ Tier-3（补全/格式化）→ Tier-4（纯编码）

预算告警：50% 通知 → 80% 警告 → 95% 限流 → 100% 停止

ROI 计算：(等效人类成本 - AI 实际成本) / AI 实际成本 ≥ 3.0 为健康

Kill Switch：日预算耗尽 → 停止非 Tier-4
            单小时 > 日预算 50% → 限流 1 并发
            异常模式 → 立即停止
```

## 附录 B：成本优化清单

| 优化项 | 预期节省 | 实施难度 | 优先级 |
|--------|---------|---------|--------|
| 启用 Prompt Caching | 50-80% input cost | 低 | P0 |
| 模型路由优化 | 30-50% 总体成本 | 中 | P0 |
| 上下文裁剪 | 20-40% token 用量 | 低 | P1 |
| 批处理优化 | 3-6x 吞吐 | 中 | P1 |
| 夜间工厂模式 | 利用非高峰定价 | 低 | P1 |
| 跨任务上下文复用 | 15-30% 重复 token | 中 | P2 |
| 示例精简 | 15-25% prompt 大小 | 低 | P2 |
| ROI 驱动的降级 | 自动优化低效任务 | 高 | P2 |

## 附录 C：版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **v5.4** | **2026-04-18** | **初始版本 — API 成本预算、模型路由、Prompt 优化、上下文复用、吞吐优化、ROI 度量、异常检测、Per-Task 追踪** |
