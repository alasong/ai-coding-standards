# AI Coding 规范 v6.0：Spec 演进治理

> 版本：v6.0 | 2026-05-02
> 定位：Spec 生命周期、版本管理、变更传播
> 前置：[01-core.md](01-core.md)（P7 Spec 驱动、P23 需求链）、[02-state-machine.md](02-state-machine.md)（PHASE_2.5_SPEC_GEN 状态）

---

## 第 1 章：Spec 生命周期

### 1.1 状态机

```
draft → validated → ready → in-progress → done
  │         │          │        │           │
  └─────────┴──────────┴────────┴───────────┴→ deprecated
```

| 转换 | 触发 | 执行者 |
|------|------|--------|
| draft → validated | Spec Validation Gate 通过 | AI + AI Reviewer |
| validated → ready | DCP 决策通过 | 人工 |
| ready → in-progress | Phase 3 开始 | AI |
| in-progress → done | TDD + Gate 全部通过 | AI |
| done → in-progress | 回归/修复 | AI |
| 任一状态 → deprecated | 需求取消 | 人工 |

### 1.2 版本管理

Spec 文件包含 YAML frontmatter：

```yaml
---
type: feature
id: F001
name: user-authentication
version: 1.2.0
status: ready
priority: P0
depth_tier: D1
business_goal: "实现用户认证，提升转化率"
depends_on: [F000]
---
```

版本变更规则：
- 格式调整/错别字 → patch
- 新增/修改 AC → minor
- 删除/重大变更 → major（需 DCP 审批）

---

## 第 2 章：变更传播

### 2.1 向下传播

Spec 变更影响：
1. **Task Contract**：如果 AC 变更，对应 Task Contract 必须更新 `spec_acceptance_criteria`
2. **测试用例**：新增/修改/删除 AC → 对应测试必须更新
3. **实现代码**：AC 变更 → 实现必须对齐

### 2.2 向上传播

实现过程中发现的约束变化必须回传：
- 技术限制 → 更新 Spec 边界条件
- 架构发现 → 更新方案设计
- 需求歧义 → 通知需求提出者

### 2.3 变更请求流程

```
变更请求 → 影响分析 → DCP 审批 → Spec 更新 → 向下传播 → 重新验证
```

影响分析必须检查：
- 受影响的 Task Contract 数量
- 受影响的测试用例数量
- 已完成的开发工作是否作废
- 是否需要重新执行 IPD 传导检查

---

## 第 3 章：规范版本管理

### 3.1 规范版本同步

规范集整体使用语义版本号（当前 v6.0）：
- 文档更新时同步更新版本号
- `.normalized/` 清洗版与原文版本号同步

### 3.2 变更记录

每个文档底部包含版本历史：

```markdown
## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v6.0 | 2026-05-02 | 基线版本 |
```

### 3.3 过渡期

重大规范变更设置过渡期（1-2 周）：
- 过渡期内新旧规范并行
- 过渡期结束强制使用新规范
- 过渡期通知通过 CLAUDE.md 和 `.normalized/` 同步
