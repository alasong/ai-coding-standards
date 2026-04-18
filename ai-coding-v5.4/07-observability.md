# AI Coding 规范 v5.4：可观测性

> 版本：v5.4 | 2026-04-18
> 定位：AI 生成代码的日志、指标、追踪规范 — 让 AI 代码自描述、可诊断、可观测
> 前置：[01-core-specification.md](01-core-specification.md) P12-P22（工程实践原则）

---

## 第 1 章：核心原则

### 1.1 为什么可观测性在 Auto-Coding 中更重要

大规模 Auto-Coding 场景下，AI 生成的代码上线后如果出现故障：
- 人类审查者需要在最短时间内定位问题根因
- L3/L4 自主运行时，AI 自己需要读取日志和指标做 Self-Correction
- 没有统一的日志/指标格式，多个 AI Agent 产生的数据无法聚合分析

**核心原则**：AI 生成的代码必须具备**自描述能力**——通过日志、指标、追踪三种手段，让系统在运行时完全可见。

### 1.2 三大支柱概览

| 支柱 | 回答的问题 | AI 生成要求 |
|------|-----------|:----------:|
| **日志（Logging）** | "发生了什么？" | **强制** | 每个函数入口/出口/异常必须有日志 |
| **指标（Metrics）** | "系统状态如何？" | **强制** | 每个端点必须暴露 RED 指标 |
| **追踪（Tracing）** | "请求经过了哪些服务？" | **强制** | 所有跨服务/跨模块调用必须传播 trace context |

---

## 第 2 章：日志规范

### 2.1 结构化日志格式

AI 生成的所有日志必须使用结构化日志（JSON 格式），不得使用纯文本 `fmt.Printf` / `console.log`。

```json
{
  "level": "error",
  "timestamp": "2026-04-18T10:00:00.000Z",
  "service": "user-service",
  "trace_id": "abc123def456",
  "span_id": "span789",
  "message": "failed to create user",
  "correlation_id": "corr-001",
  "user_id": "usr-123",
  "error": "duplicate key: email already exists",
  "stack_trace": "...",
  "latency_ms": 45,
  "code_file": "handler.go:42",
  "ai_generated": true
}
```

### 2.2 必填字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `level` | string | **是** | `debug` / `info` / `warn` / `error` / `fatal` |
| `timestamp` | string | **是** | RFC 3339 格式 |
| `message` | string | **是** | 人类可读的事件描述 |
| `trace_id` | string | **是** | 分布式追踪 ID |
| `service` | string | **是** | 服务名称 |
| `error` | string | 条件 | level=error 时必填 |
| `stack_trace` | string | 条件 | error + panic 时附加 |
| `correlation_id` | string | 推荐 | 业务关联 ID |
| `user_id` / `tenant_id` | string | 推荐 | 用于租户隔离排查 |

### 2.3 日志级别使用规范

| 级别 | 使用场景 | 示例 | 禁止行为 |
|------|---------|------|---------|
| **DEBUG** | 调试信息、中间状态 | "开始查询缓存"、"SQL 参数列表" | 不得包含敏感数据 |
| **INFO** | 正常业务流程 | "用户创建成功"、"订单状态变更为已支付" | 不得高频输出（防日志风暴） |
| **WARN** | 可恢复的异常、降级 | "缓存未命中，回退到 DB"、"重试第 1 次" | 不得忽略不处理 |
| **ERROR** | 需要人工介入的异常 | "数据库连接失败"、"第三方支付超时" | 不得吞掉不返回 |
| **FATAL** | 进程无法继续运行 | "无法绑定端口"、"配置文件缺失" | 不得在非启动阶段使用 |

### 2.4 AI 生成日志规则

| 规则 | 说明 |
|------|------|
| **函数入口日志** | 每个公开函数入口记录 INFO 级别日志，包含关键入参（脱敏后） |
| **函数出口日志** | 正常返回时不记录 INFO（避免噪声），异常返回时记录 ERROR |
| **错误上下文** | 记录错误时必须附加上下文：`log.Error("msg", "key", value)`，不得仅 `log.Error(err)` |
| **禁止日志的内容** | 密钥、token、密码、完整信用卡号、PII 原始数据 |
| **限频日志** | 同一消息每秒输出不得超过 10 次，超过时自动限流并记录 WARN |
| **敏感数据脱敏** | 邮箱显示前 3 位 + `***`，手机号显示后 4 位，IP 显示前三段 |

### 2.5 日志聚合与查询

```
AI 生成的日志必须兼容以下查询模式：

1. 按 trace_id 查询完整请求链路
2. 按 user_id 查询特定用户的所有操作
3. 按 error 类型查询同类错误
4. 按 service + level 查询特定服务的错误率
5. 按时间窗口聚合错误率趋势
```

---

## 第 3 章：指标规范

### 3.1 RED 方法论

AI 生成的每个服务端点必须暴露 **RED 指标**：

| 指标 | 名称模式 | 说明 | 示例 |
|------|---------|------|------|
| **Rate** | `{service}_{endpoint}_requests_total` | 请求速率 | `user_service_create_requests_total` |
| **Errors** | `{service}_{endpoint}_errors_total` | 错误速率 | `user_service_create_errors_total` |
| **Duration** | `{service}_{endpoint}_duration_seconds` | 请求延迟（Histogram） | `user_service_create_duration_seconds` |

### 3.2 必须暴露的核心指标

| 类别 | 指标 | 类型 | 说明 |
|------|------|------|------|
| **HTTP 端点** | `{endpoint}_requests_total` | Counter | 请求总数，带 method + status 标签 |
| | `{endpoint}_errors_total` | Counter | 错误总数，带 error_type 标签 |
| | `{endpoint}_duration_seconds` | Histogram | 延迟分布，bucket: 10ms, 50ms, 100ms, 500ms, 1s, 5s |
| **数据库** | `db_query_duration_seconds` | Histogram | 数据库查询延迟 |
| | `db_connection_pool_size` | Gauge | 连接池当前大小 |
| | `db_connection_pool_available` | Gauge | 可用连接数 |
| | `db_errors_total` | Counter | 数据库错误总数 |
| **缓存** | `cache_hits_total` / `cache_misses_total` | Counter | 缓存命中率 |
| | `cache_evictions_total` | Counter | 缓存淘汰数 |
| **队列** | `queue_depth` | Gauge | 队列积压深度 |
| | `queue_processing_duration_seconds` | Histogram | 消息处理延迟 |
| **AI 特有** | `ai_api_calls_total` | Counter | AI API 调用次数 |
| | `ai_api_cost_usd` | Counter | AI API 累计费用 |
| | `ai_self_correction_attempts_total` | Counter | Self-Correction 触发次数 |
| | `ai_hallucination_detected_total` | Counter | 幻觉检出次数 |

### 3.3 SLO/SLA 定义

| 指标 | SLO 目标 | SLA 承诺 | 测量窗口 |
|------|:-------:|:--------:|---------|
| **可用性** | 99.9% | 99.5% | 30 天滑动窗口 |
| **P99 延迟** | < 500ms | < 1s | 5 分钟窗口 |
| **错误率** | < 1% | < 5% | 5 分钟窗口 |
| **AI 响应延迟** | < 30s | < 60s | 5 分钟窗口 |

### 3.4 SLO 预算消耗

```
Error Budget = (1 - SLO 目标) × 总请求数

示例：SLO 99.9%，月请求数 1000 万
  Error Budget = 0.001 × 10,000,000 = 10,000 次错误/月

预算消耗 > 50% → 告警（Warning）
预算消耗 > 80% → 告警（Critical）+ 暂停 L3/L4 自主部署
预算消耗 = 100% → 立即停止所有非紧急变更
```

**AI 特有规则**：L3/L4 自主部署前，AI 必须检查当前 SLO 预算消耗状态。预算消耗 > 50% 时，禁止自主部署新特性（仅允许修复 Bug）。

---

## 第 4 章：分布式追踪规范

### 4.1 Trace Context 传播

```
客户端请求 → [trace_id, span_id, parent_span_id] → 服务 A
    服务 A 处理 → 创建新 span → 传播 [trace_id, 新span_id, 原span_id] → 服务 B
        服务 B 处理 → 创建新 span → 传播 [trace_id, 新span_id, 原span_id] → 服务 C
```

**AI 必须遵循的规则**：
1. 所有跨服务 HTTP/gRPC 调用必须传播 `trace_id` 和 `span_id`
2. HTTP 请求使用 W3C Trace Context 标准：`traceparent: 00-{trace_id}-{span_id}-01`
3. 消息队列（Kafka/RabbitMQ）必须在消息 headers 中传播 trace context
4. 异步任务（goroutine/celery）必须复制 trace context 到子任务

### 4.2 Span 属性规范

每个 span 必须包含：

| 属性 | 说明 | 示例 |
|------|------|------|
| `service.name` | 服务名称 | `user-service` |
| `operation.name` | 操作名称 | `createUser` |
| `span.kind` | span 类型 | `server` / `client` / `producer` / `consumer` |
| `http.method` | HTTP 方法 | `POST` |
| `http.url` | 请求 URL（路径部分，不含查询参数） | `/api/v1/users` |
| `http.status_code` | HTTP 状态码 | `200` / `500` |
| `error` | 是否为错误 span | `true` / `false` |
| `error.message` | 错误消息 | `duplicate key` |

### 4.3 Trace 采样策略

| 采样策略 | 采样率 | 说明 |
|---------|:------:|------|
| **默认** | 10% | 正常流量 |
| **错误全采样** | 100% | 所有错误请求的 trace 必须完整保留 |
| **慢请求全采样** | 100% | 延迟 > P99 的请求全采样 |
| **AI 生成请求** | 50% | AI 生成代码处理的请求提高采样率，便于排查 |

---

## 第 5 章：告警策略

### 5.1 告警分级

| 级别 | 名称 | 响应时间 | 通知方式 | 示例 |
|------|------|---------|---------|------|
| **P0** | Critical | 5 分钟 | PagerDuty + Slack + 电话 | 服务不可用、数据丢失 |
| **P1** | High | 30 分钟 | Slack + PagerDuty | 错误率 > 5%、SLO 预算 > 80% |
| **P2** | Medium | 2 小时 | Slack | 单个实例宕机、延迟增长 |
| **P3** | Low | 工作日 | Slack / Email | 磁盘空间预警、依赖版本过期 |

### 5.2 核心告警规则

| 告警 | 条件 | 级别 | 自动动作 |
|------|------|:----:|---------|
| 服务不可用 | 健康检查连续 3 次失败 | P0 | 自动回滚 + 通知 on-call |
| 错误率飙升 | 5 分钟窗口错误率 > 5% | P1 | 标记问题 + 通知 |
| 延迟飙升 | 5 分钟窗口 P99 > 基线×2 | P1 | 标记问题 + 通知 |
| SLO 预算消耗 > 80% | 误差预算消耗 > 80% | P1 | 暂停 L3/L4 自主部署 |
| 数据库连接池耗尽 | 可用连接 = 0 | P0 | 重启连接池 + 通知 |
| 磁盘空间 < 10% | 磁盘使用率 > 90% | P2 | 清理旧日志 + 通知 |
| AI 幻觉检出 | L3 检出幻觉 | P2 | 标记 PR + 通知审核者 |
| AI 成本异常 | 小时费用 > 基线×3 | P1 | 暂停自主任务 + 通知 |

### 5.3 告警降噪规则

| 策略 | 说明 |
|------|------|
| **告警聚合** | 同一根因的多个告警合并为一条 |
| **静默窗口** | 维护窗口期间降低告警级别 |
| **升级机制** | P1 告警 30 分钟未处理 → 升级为 P0 |
| **去重** | 5 分钟内相同告警只发送一次 |
| **AI 生成抑制** | AI 正在修复已知问题时，抑制关联告警 |

---

## 第 6 章：Dashboard 规范

### 6.1 必须存在的 Dashboard

| Dashboard | 受众 | 更新频率 |
|-----------|------|---------|
| **Service Overview** | 全体开发者 | 实时 |
| **AI Coding 质量面板** | AI 审核者 + 技术负责人 | 实时 |
| **SLO/SLA 面板** | SRE + 技术负责人 | 实时 |
| **Cost Dashboard** | 技术负责人 + 财务 | 每小时 |
| **Database Health** | DBA + SRE | 实时 |

### 6.2 Service Overview Dashboard 必须包含

| 面板 | 类型 | 说明 |
|------|------|------|
| 请求速率 | 时序图 | 各端点 QPS |
| 错误率 | 时序图 | 各端点错误率，标注 SLO 线 |
| 延迟分布 | 热力图 | P50/P90/P99 延迟 |
| Top 错误 | 表格 | 按错误类型排序 |
| 依赖健康度 | 状态图 | 数据库、缓存、第三方服务状态 |
| 部署历史 | 标注线 | 最近部署时间点和结果 |

### 6.3 AI Coding 质量面板必须包含

| 面板 | 类型 | 说明 |
|------|------|------|
| AI 生成 PR 趋势 | 时序图 | 每天 AI 生成的 PR 数 |
| AI PR 通过率 | 时序图 | Pipeline L1-L5 通过率 |
| 幻觉检出趋势 | 时序图 | 每天检出的幻觉数 |
| Self-Correction 次数 | 时序图 | 每天 Self-Correction 触发次数 |
| TDD 合规率 | 仪表盘 | 当前 TDD 执行率 |
| AC 覆盖率 | 仪表盘 | 当前 AC 覆盖率 |
| AI 成本趋势 | 时序图 | 每天 API 费用 |
| 自治等级状态 | 状态 | 当前等级 + 升级/降级历史 |

---

## 第 7 章：AI 生成代码的可观测性要求

### 7.1 AI 生成代码时的自动注入

AI 在生成任何服务端点代码时，必须自动注入以下可观测性代码：

```go
// 1. 日志：函数入口（INFO）
log.Info("handling request", "method", r.Method, "path", r.URL.Path, "trace_id", traceID)

// 2. 指标：请求计数
metrics.requests.WithLabelValues(method, path).Inc()

// 3. 指标：延迟计时
timer := metrics.duration.WithLabelValues(method, path).StartTimer()
defer timer.ObserveDuration()

// 4. 追踪：创建 span
ctx, span := tracer.Start(r.Context(), "handler.createUser")
defer span.End()

// 5. 错误日志：附加 trace_id
if err != nil {
    log.Error("failed to create user",
        "trace_id", traceID,
        "error", err.Error(),
        "user_input", sanitize(input))
    metrics.errors.WithLabelValues("create_user", errType).Inc()
    span.RecordError(err)
    span.SetStatus(codes.Error, err.Error())
    return errorResponse(w, err)
}
```

### 7.2 AI 可观测性 Checklist

AI 生成每个端点后必须自检：

- [ ] 函数入口有 INFO 日志（关键入参已脱敏）
- [ ] 错误返回有 ERROR 日志（含 trace_id 和上下文）
- [ ] 暴露了 RED 指标（Rate / Errors / Duration）
- [ ] 创建了 trace span（跨服务调用传播了 trace context）
- [ ] 错误 span 标记了 error=true 和 error.message
- [ ] 没有记录敏感数据（密钥、密码、PII）
- [ ] 日志格式为结构化 JSON
- [ ] 错误消息不暴露内部实现细节
