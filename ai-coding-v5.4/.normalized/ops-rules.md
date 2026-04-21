# Ops Agent 规范
> v5.4 | 部署与可观测性审查 — 部署 readiness、健康检查、日志/指标/追踪、SLO/SLA、告警、回滚策略

## 核心底线
- **P5 密钥不入代码** [13-deploy §8.1] 密钥、token、密码不得硬编码；必须通过配置注入，日志中不得明文记录
- **P11 证据链** [gate-checker §1.6] 每个部署声明 ≥2 条可验证证据（CI 日志 + 指标截图）；不得证据链断裂
- **P22 IP 不暴露** [architect §1.2] 架构/配置中不得含生产 IP/域名；所有地址通过配置注入

## 部署 Readiness [13-deploy §7.4]
部署前必须逐项确认，全部 PASS 方可部署：
- [ ] 所有依赖已就绪（服务依赖按拓扑排序 §4.1）
- [ ] 数据库迁移已执行且向前兼容（08-database-migration.md 验证）
- [ ] 配置已更新（无硬编码值）
- [ ] Feature Flag 已配置且默认关闭 [§5.4]
- [ ] Kill Switch 已配置（AI 生成代码必须）[§5.3]
- [ ] 回滚计划已定义（`.gate/rollback-plan.json` 存在）[§8.4]
- [ ] SLO 预算消耗 ≤ 50%（> 50% 禁止自主部署新特性）[07-observ §3.3]
- [ ] 不在维护窗口/业务高峰期 [§8.3]

## 健康检查 [13-deploy §1.2, §7.1]
- 每个服务必须有 `/liveness` 和 `/readiness` HTTP 端点
- `/health` 返回 200 且 JSON body 中所有 `dependencies` 字段值为 `healthy`
- 部署期间 `health_check_interval` ≤ 5s
- 健康检查必须在 CI 中验证通过（连续 3 次成功）

## 可观测性三支柱 [07-observ §1.2]

### 日志 [§2]
- 结构化日志（JSON 格式）；禁止纯文本 `console.log`/`fmt.Printf`
- 必填字段：`level`、`timestamp`(RFC3339)、`message`、`trace_id`、`service`
- 日志级别：DEBUG（调试）、INFO（正常流程）、WARN（可恢复异常）、ERROR（需人工介入）、FATAL（进程无法继续）
- 函数入口记录 INFO（关键入参脱敏）；错误返回记录 ERROR（含 trace_id + 上下文）
- 禁止记录：密钥、token、密码、PII 原始数据
- 限频：同一消息每秒 ≤ 10 次，超限自动限流并记录 WARN

### 指标 [§3]
- 每个端点暴露 RED 指标：`{svc}_{ep}_requests_total` (Rate)、`{svc}_{ep}_errors_total` (Errors)、`{svc}_{ep}_duration_seconds` (Duration/Histogram)
- 自定义业务指标：订单量、注册数、API 调用成功率
- SLO 目标：可用性 ≥ 99.9%、P99 < 500ms、错误率 < 1%、AI 响应 < 30s
- SLO burn rate 监控：Error Budget 消耗 > 50% → Warning；> 80% → Critical + 暂停自主部署

### 追踪 [§4]
- 分布式 trace 覆盖所有跨服务/跨模块调用
- HTTP 请求传播 W3C Trace Context：`traceparent: 00-{trace_id}-{span_id}-01`
- 消息队列在 headers 中传播 trace context
- 每个 span 包含：`service.name`、`operation.name`、`span.kind`、`http.status_code`
- 错误请求 100% 采样；慢请求（> P99）100% 采样；AI 生成请求 50% 采样

## 告警策略 [07-observ §5]
- P0 Critical（5min 响应）：服务不可用、数据丢失 → PagerDuty + 电话 + 自动回滚
- P1 High（30min）：错误率 > 5%、SLO 预算 > 80% → Slack + PagerDuty
- P2 Medium（2h）：单实例宕机、延迟增长 → Slack
- P3 Low（工作日）：磁盘预警、依赖过期 → Slack/Email
- 每条告警必须有 runbook；无 runbook 的告警不得上线
- 告警降噪：同源告警聚合、5min 去重、维护窗口降级、P1 30min 未处理 → 升级为 P0
- 禁止告警风暴：同一根因合并为一条

## 回滚策略 [13-deploy §2-3]
- 部署策略选型（由 Spec 指定，AI 不得自选）：
  | 策略 | 适用 | 回滚时间 |
  |------|------|---------|
  | 蓝绿 | 核心服务/零停机 | 秒级（路由切换 < 30s） |
  | 金丝雀 | 日常发布（默认） | 分钟级（5→25→50→100 流量回收） |
  | 滚动 | 非核心/资源受限 | 分钟级（反向逐批回退） |
- 全量回滚目标 < 5min（P0）；按服务回滚 < 15min（P2）
- 回滚不回滚数据库（向前兼容原则）；仅回滚代码到 LKG
- 回滚后验证写入 `.gate/rollback-report.json`
- 回滚演练记录：Kill Switch 每月至少一次演练

## 部署安全 [13-deploy §8]
- AI 只能通过 CI/CD Pipeline 部署，不得直接操作生产环境（禁止 `kubectl apply`、`docker run`）
- 不得跳过 Pipeline 层级（L0-L4 必须全部通过）
- 不得在维护窗口（周六 02:00-06:00 UTC）/业务高峰期触发部署
- 部署范围必须在 `.gate/deploy-scope.json` 中声明
- 部署审计日志由部署 Agent 生成，但完整性由 Gate Checker 独立验证

## SLO/SLA [07-observ §3.3-3.4]
| 指标 | SLO 目标 | SLA 承诺 | 测量窗口 |
|------|:-------:|:--------:|---------|
| 可用性 | 99.9% | 99.5% | 30 天滑动 |
| P99 延迟 | < 500ms | < 1s | 5 分钟 |
| 错误率 | < 1% | < 5% | 5 分钟 |

- Error Budget = (1 - SLO) × 总请求数；消耗 > 80% 暂停 L3/L4 自主部署
- L3/L4 自主部署前必须检查 SLO 预算消耗状态

## DCP 检查清单 [部署阶段]
全部 PASS 方可进入部署执行：
- 健康检查端点存在且 CI 验证通过？
- 可观测性三支柱就绪（日志 JSON + RED 指标 + trace 传播）？
- 回滚策略已验证（rollback-plan.json 存在 + 演练记录）？
- SLO 有明确定义且预算消耗 ≤ 50%？
- 所有依赖按拓扑排序就绪？
- 不在维护窗口？

## 独立验证 [§8.5, gate-checker §1.6]
- 部署审查不得由部署脚本编写者自评 PASS/FAIL
- 部署审计日志的完整性由 Gate Checker Agent 独立验证
- 深度评分差异 ≥ 2 分以独立 Agent 为准；自评结果一律无效
