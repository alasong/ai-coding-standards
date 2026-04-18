# AI Coding 规范 v5.4：安全与治理

> 版本：v5.4 | 2026-04-17
> 定位：企业级安全实现、权限管理、MCP 安全、合规审计
> 前置：必须先阅读并理解 [01-core-specification.md](01-core-specification.md)

---

## 第 1 章：安全底线

安全底线见 [01-core-specification.md](01-core-specification.md) P5/P10。本文件不再重复。

---

## 第 2 章：权限管理

### 2.1 AI 权限模型

| 权限 | 说明 | 适用场景 |
|------|------|---------|
| Read | 只读代码和文档 | 代码审查、探索 |
| Write | 写入代码文件 | 特性开发、修复 |
| Execute | 运行命令 | 测试、构建 |
| Git | Git 操作 | 提交、创建分支/PR |

### 2.2 文件级权限

```json
{
  "permissions": {
    "allow": ["Bash(npm run test)", "Bash(go build ./...)"],
    "deny": [
      "Read(./.env)", "Read(./secrets/**)",
      "Bash(curl *)", "Bash(wget *)"
    ]
  }
}
```

---

## 第 3 章：MCP 安全

### 3.1 MCP Server 安全

- MCP Server 必须配置访问控制，仅暴露必要的工具
- MCP 访问数据库前必须经过脱敏过滤层
- MCP 不得暴露敏感配置信息

### 3.2 Sub-Agent 安全约束

- Sub-Agent 继承主 Agent 的权限限制
- Sub-Agent 不得修改安全敏感文件
- Sub-Agent 的所有输出必须经过主 Agent 验证

---

## 第 4 章：合规与审计

### 4.1 审计检查点

| 审计项 | 检查位置 | 频率 |
|--------|---------|------|
| P5 密钥不入代码 | pre-commit 日志 + SAST 报告 | 每次 commit |
| P10 数据分级 | pre-send 扫描日志 | 每次 AI 调用 |
| P4 人工审查 | PR review 记录 | 每个 PR |
| 幻觉检测 | AI Reviewer 报告 | 每个 PR |
| Kill Switch | Kill Switch 日志 | 实时 |

### 4.2 Context Loading Gate 安全

进入需求分析前必须通过 5 项安全检查：

| # | 检查项 | 说明 |
|---|--------|------|
| 1 | 知识来源可信 | 所有 domain-knowledge 文件有明确的来源和更新时间 |
| 2 | 无敏感数据 | domain-knowledge 中不包含密钥、token、内部 IP |
| 3 | 架构文档脱敏 | docs/architecture/ 中不暴露生产环境细节 |
| 4 | 权限边界明确 | AI 可访问的文件范围已声明 |
| 5 | 数据分级已知 | AI 了解各数据分类规则 |

---

## 第 5 章：提示注入防护

### 5.1 攻击向量

| 来源 | 攻击向量 | 风险级别 |
|------|---------|---------|
| Spec 文件 | 伪造的 Spec 包含恶意指令 | CRITICAL |
| 代码仓库 | 恶意文件包含注入指令 | HIGH |
| 依赖包 | package.json description 嵌入指令 | HIGH |
| 环境变量 | 恶意设置的环境变量 | HIGH |
| PR 评论 | 评论中嵌入覆盖指令 | MEDIUM |
| MCP 响应 | MCP 服务器返回注入内容 | MEDIUM |

### 5.2 四层防御

| 层 | 机制 | 说明 |
|----|------|------|
| L1 输入净化 | 检测覆盖型指令、角色覆盖、数据外泄、安全机制禁用 | 正则匹配 + 阻断 |
| L2 上下文验证 | 系统 Prompt 完整性、上下文篡改检测、预期 vs 实际 | Hash 比对 |
| L3 行为监控 | 异常操作模式、超出置信范围的操作、审计日志 | 运行时监控 |
| L4 输出验证 | 敏感数据泄露检查、预期行为匹配、异常输出阻断 | 输出门禁 |

### 5.3 关键检测规则

| 模式 | 严重级别 | 动作 |
|------|---------|------|
| `ignore/override/bypass` + `instruction/rule/constraint` | CRITICAL | 阻断 |
| `you are now/your new role` + `security/admin/root` | CRITICAL | 阻断 |
| `send/transmit/upload` + `env/secret/key/token` | CRITICAL | 阻断 |
| `disable/turn off/skip/bypass` + `security/sandbox/gate` | CRITICAL | 阻断 |
| `git push --force / reset --hard` | HIGH | 阻断 |

---

## 第 6 章：应急响应

| 场景 | 严重级别 | 应急动作 |
|------|---------|---------|
| 提示注入检测为 Critical | CRITICAL | 立即阻断 → 暂停 auto 模式 → P0 事件报告 → 隔离会话 → 根因分析 |
| 提示注入检测为 High | HIGH | 阻断当前操作 → 记录审计日志 → 净化上下文 → 继续执行 |
| 提示注入检测为 Medium/Low | MEDIUM | 记录审计日志 → 净化上下文 → 继续执行 |
| 密钥泄露到代码仓库 | CRITICAL | 立即回滚 → 轮换密钥 → 全面审计 |
| Restricted 数据发送给 AI | CRITICAL | 立即停止 → 数据影响评估 → 通知数据保护负责人 |
| 幻觉代码合并到 main | HIGH | 立即 revert → 根因分析 → 强化审查 |
| AI 提供者质量严重退化 | HIGH | 降低自治等级 → 切换模型 → 回归测试 |
