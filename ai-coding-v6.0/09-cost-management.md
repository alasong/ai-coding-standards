# AI Coding 规范 v6.0：AI 成本管理

> 版本：v6.0 | 2026-05-02
> 定位：Token 预算、模型路由、成本控制
> 前置：[04-multi-agent.md](04-multi-agent.md)（Agent 资源配额）

---

## 第 1 章：Token 预算

### 1.1 预算层级

| 层级 | 预算 | 说明 |
|------|------|------|
| 任务级 | 按 Spec 复杂度分配 | 简单任务 < 50K tokens，复杂任务 < 200K tokens |
| Agent 级 | 单个 Agent 会话上限 | 默认 100K tokens，超时自动终止 |
| 项目级 | 每日/每周总预算 | 超出后非关键任务暂停 |

### 1.2 预算监控

- 每次 Agent 调用记录 token 消耗
- 超出预算 80% 时预警
- 超出预算 100% 时终止非关键任务
- 记录到 `.omc/logs/cost-{date}.json`

---

## 第 2 章：模型路由

### 2.1 能力分级（模型无关）

v6.0 不绑定具体模型厂商，使用能力分级描述：

| 能力等级 | 定位 | 典型用途 |
|---------|------|---------|
| **强** | 深度推理、复杂分析、不可出错场景 | 架构设计、代码审查、安全审查、Gate Checker（D1 特性） |
| **中** | 平衡质量与成本 | 代码生成、TDD 循环、Domain Agent 执行 |
| **弱** | 快速简单任务、高并发场景 | 文件搜索、格式化、简单文档编写 |

### 2.2 模型路由映射

各平台模型按能力等级映射：

| 任务类型 | 能力要求 | 百炼模型 | DeepSeek | SiliconFlow |
|---------|---------|---------|----------|-------------|
| 架构设计 | 强 | Qwen-Max / Qwen-Plus-Latest | deepseek-chat | Qwen2.5-Coder-32B |
| 代码审查 | 强 | Qwen-Max | deepseek-chat | Qwen2.5-Coder-32B |
| 安全审查 | 强 | Qwen-Max | deepseek-chat | Qwen2.5-Coder-32B |
| Gate Checker | 强 | Qwen-Max | deepseek-chat | Qwen2.5-Coder-32B |
| 代码生成 | 中 | Qwen-Plus | deepseek-coder | Qwen2.5-Coder-32B |
| TDD 执行 | 中 | Qwen-Plus | deepseek-coder | Qwen2.5-Coder-32B |
| 文件搜索 | 弱 | Qwen-Turbo | deepseek-coder-lite | 轻量模型 |
| 文档编写 | 弱 | Qwen-Turbo | deepseek-coder-lite | 轻量模型 |

### 2.3 动态路由

Director Agent 根据任务复杂度自动选择能力等级：
- 简单任务（S 档）→ 弱能力模型
- 中等任务（M 档）→ 中能力模型
- 复杂/关键任务（L/XL 档）→ 强能力模型

---

## 第 3 章：成本优化

### 3.1 上下文优化

- 使用 `.normalized/` 清洗后规范替代完整规范，减少上下文窗口占用
- 按需加载相关源文件（Progressive Disclosure）
- 避免重复加载已读文件

### 3.2 任务优化

- 任务拆解到最小可行粒度（P8 最小批量）
- 避免大范围重写，使用 Edit 而非 Write
- 并行独立任务减少总会话时间

### 3.3 缓存利用

- 利用 LLM 平台的 prompt caching 机制减少重复 token 消耗（百炼、DeepSeek、SiliconFlow 均支持 OpenAI 兼容接口的缓存）
- 系统 prompt 保持稳定以最大化缓存命中
