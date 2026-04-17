# AI Coding 规范 v5.3：安全与治理

> 版本：v5.3 | 2026-04-17
> 定位：企业级安全实现、权限管理、MCP 安全、合规审计
> 前置：必须先阅读并理解 [01-core-specification.md](01-core-specification.md)

---

## 第 1 章：安全原则

### 1.1 绝对底线（来自 P5、P10）

- 禁止硬编码密钥（API keys、密码、tokens）
- 禁止 eval/exec/动态导入
- 验证所有外部输入
- 禁止 SQL 字符串拼接（使用参数化查询）
- 禁止路径穿越
- 错误消息不得泄露内部细节

### 1.2 多层执行机制

| 层级 | 机制 | 示例 |
|------|------|------|
| L1 AI 约束 | 规范声明 | AGENTS.md 中安全声明 |
| L2 Pre-commit | Git hook 自动拦截 | 密钥扫描、lint |
| L3 CI Gate | CI 门禁 | SAST、依赖审计 |
| L4 Runtime | 代码本身防护 | 参数化查询、认证中间件 |

**执行原则**：一条规则至少有两层保护。

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

## 第 5 章：应急响应

| 场景 | 应急动作 |
|------|---------|
| 密钥泄露到代码仓库 | 立即回滚 → 轮换密钥 → 全面审计 |
| Restricted 数据被发送给 AI | 立即停止 → 数据影响评估 → 通知数据保护负责人 |
| 幻觉代码合并到 main | 立即 revert → 根因分析 → 强化审查 |
| AI 提供者质量严重退化 | 降低自治等级 → 切换模型 → 回归测试 |
