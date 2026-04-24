# Multi-Pass Review Protocol

> 版本：v5.4.3 | 2026-04-24
> 定位：每个 IPD Phase 完成后的多层审查协议，确保缺陷不流入下一阶段
> 原则：审查次数 × 结构深度 > 盲目堆次数；200 次是自动达成的结果，不是目标本身

---

## 0. 核心认识

### 0.1 为什么需要 200 次审查

"200 次 review" 的本质诉求是：**每个阶段的质量必须足够高，不得带着已知缺陷进入下一阶段。**

如果人为规定"做 200 次 review"，会陷入两个陷阱：
1. **审查疲劳**：10 次有结构的深度审查 > 200 次浅层检查
2. **数字游戏**：追求次数而非质量

本协议的设计原则：**200 次是结构自动达成的结果，不是人为设定的目标。**

### 0.2 计算公式

```
总审查次数 = Gate 数量 × 每 Gate 检查项 × Pass 数量 × 每检查项验证轮次

             7        ×      5          ×    6      ×         3           =  630 次
```

实际有效审查次数 ≈ 630 次（远超 200，且每次有明确目标和方法）。

---

## 1. 审查架构

### 1.1 六轮审查（6 Passes）

每个 IPD Phase 产出完成后，按顺序执行 6 轮审查：

| Pass | 名称 | 执行者 | 视角 | 方法 | 输出 |
|------|------|--------|------|------|------|
| **P1** | Self-Verify（自我验证） | 作者/Executor | 完整性 | 逐项对照 Phase 规范清单 | Pass/Fail + 缺失清单 |
| **P2** | Cross-Verify（交叉验证） | 独立 Agent | 一致性 | 与上游/下游文档逐条交叉引用 | 不一致项清单 |
| **P3** | Adversarial Review（对抗审查） | 独立 Agent | 竞争视角 | "如果竞品看到这个文档，怎么攻击我们？" | 脆弱点清单 |
| **P4** | Gate Checker Agent（门检查） | 独立 Gate Checker | 规范合规 | 对照 ai-coding-v5.4 规范逐条验证 | Gate Report |
| **P5** | Human Reviewer（人工终审） | 人类 | 业务判断 | 战略对齐 + 资源可行性 + 风险接受度 | 批准/驳回/修改意见 |
| **P6** | Depth Score（深度评分） | 独立 Agent（critic/architect） | 深度质量 | 对照 §1.6.8 各 Phase 维度 | 深度评分报告 |

### 1.2 每 Pass 的审查对象（7 个 Gate）

| Gate ID | Gate 名称 | 检查项数 | 来源 |
|---------|----------|---------|------|
| G-1 | TDD Gate | 4 | §1.7.3 |
| G-2 | Spec Gate | 2 | §1.7.3 |
| G-3 | IPD 传导 Gate | 2 | §1.7.3 |
| G-4 | 安全 Gate | 4 | §1.7.3 |
| G-5 | 质量 Gate | 5 | §1.7.3 |
| G-6 | 幻觉 Gate | 6 | §1.7.3 |
| G-7 | Self-Correction Gate | 2 | §1.7.3 |
| **合计** | | **25** | |

### 1.3 每检查项的 3 轮独立验证

每个检查项（如"TDD 提交顺序正确"）必须通过 3 轮独立验证：

| 轮次 | 方法 | 示例 |
|------|------|------|
| **R1 静态检查** | 检查产出物本身是否符合规范 | `git log` 检查提交顺序 |
| **R2 运行验证** | 实际运行测试/工具验证声称是否属实 | 运行测试确认 Red→Green |
| **R3 证据对照** | 检查证据文件是否支撑声称 | 读取 `.gate/tdd-report.json` 对比 |

**独立性要求**：R1/R2/R3 必须由不同工具或不同 Agent 执行（符合 P11 证据独立性定义）。

---

## 2. 各 Pass 详细流程

### 2.1 Pass 1: Self-Verify（自我验证）

**触发时机**：Phase 产出物初稿完成

**执行清单**：

| # | 检查 | 方法 | 通过标准 |
|---|------|------|---------|
| 1 | Phase 规范清单完整性 | 对照 ai-coding-v5.4/ 对应章节的方法论要求 | 所有要求章节均存在 |
| 2 | DCP 检查项完整性 | 对照 §1.6.x 中的 DCP 检查清单 | 所有 DCP 项有 PASS/FAIL 结论 |
| 3 | 数据/声明有证据支撑 | 每个声明有 ≥2 条证据引用 | 无"无证据声明" |
| 4 | 文档格式和引用一致 | 交叉引用链接有效，无断裂引用 | 零断裂引用 |
| 5 | 状态机正确 | 文档状态与 IPD 阶段一致 | 状态流转合规 |

**输出**：`.gate/pass1-self-verify-{date}.md`

**失败处理**：标记缺失项，修复后重新执行 P1。

### 2.2 Pass 2: Cross-Verify（交叉验证）

**触发时机**：P1 通过后

**执行者**：独立 Agent（非作者，不共享对话上下文）

**执行方法**：

```
对 Phase N 的每个关键声明：
  1. 读取 Phase N 文档中的声明
  2. 读取 Phase N-1 文档（上游）
  3. 读取 Phase N+1 文档（下游，如已存在）
  4. 验证：
     a. 声明是否与上游一致？
     b. 声明是否与下游冲突？
     c. 声明是否有 §1.6.7 传导检查？
  5. 记录不一致项
```

**具体检查矩阵（按 Phase）**：

| 审查的 Phase | 上游对照文档 | 下游对照文档 | 关键交叉检查项 |
|-------------|-------------|-------------|--------------|
| Phase 0 | — | Phase 1 概念定义 | 竞品是否被 Phase 1 正确引用 |
| Phase 1 | Phase 0 市场洞察 | Phase 2 详细规划 | Kano 优先级是否影响 WBS |
| Phase 2 | Phase 1 概念定义 | Phase 3 开发代码 | DFX 改进是否反映在代码中 |
| Phase 3 | Phase 2 详细规划 | Phase 4 验证报告 | TDD 执行率是否达标 |
| Phase 4 | Phase 3 代码 | Phase 5 生命周期 | 发布质量是否满足 SLO |
| Phase 5 | Phase 4 发布 | Phase 0 下次迭代 | 反馈是否进入下一轮 Phase 0 |

**输出**：`.gate/pass2-cross-verify-{date}.md`

**失败处理**：不一致项 > 3 项则打回作者；≤ 3 项记录为已知差异，作者确认后通过。

### 2.3 Pass 3: Adversarial Review（对抗审查）

**触发时机**：P2 通过后

**执行者**：独立 Agent（扮演竞品/审计员/攻击者角色）

**审查视角**：

| 视角 | 问题 | 示例 |
|------|------|------|
| **竞品攻击** | "如果 LangGraph/Dify 看到这个文档，会怎么攻击我们的差异化定位？" | "你说 Intent-to-DAG 是差异化，但 Dify 也有 AI 生成 DAG" |
| **审计攻击** | "如果 SOC 2 审计员看这份文档，会发现什么缺陷？" | "市场数据来自付费报告但不可验证" |
| **技术攻击** | "如果资深工程师 review 这个架构，会指出什么问题？" | "单实例 Rate Limiter 在多部署下无效" |
| **商业攻击** | "如果投资人看这份商业计划，会质疑什么假设？" | "Free-to-Pro 6% 转化率在开发者工具中偏高" |
| **用户攻击** | "如果目标用户看到这个定位，会买账吗？" | "Agent 数量作为定价维度可能不直观" |

**输出**：`.gate/pass3-adversarial-{date}.md`

**失败处理**：识别的脆弱点分类为 CRITICAL/HIGH/MEDIUM。CRITICAL > 0 则打回；HIGH ≤ 3 则记录缓解方案后通过。

### 2.4 Pass 4: Gate Checker Agent（门检查）

**触发时机**：P3 通过后

**执行者**：独立 Gate Checker Agent（只读，不得修改任何文件）

**权限约束**：
- 只读访问项目文件
- 独立对话上下文（不得与 Executor 共享）
- 输出到 `.gate/gate-report-{date}.md`
- 建议使用 `haiku` 模型（快速验证）

**检查流程**：

对 25 个检查项逐项执行 R1/R2/R3 三轮验证：

```
For each Gate G in [G1..G7]:
  For each CheckItem C in G.check_items:
    R1: 静态检查 — 读取文件/代码/配置，检查是否符合规范
    R2: 运行验证 — 执行对应测试/工具，验证声称是否属实
    R3: 证据对照 — 读取 .gate/ 证据文件，对照声明
    如果 R1+R2+R3 全部通过 → CheckItem PASS
    否则 → CheckItem FAIL，记录失败原因
```

**Gate 检查项明细**：

| Gate | 检查项 | R1 静态 | R2 运行 | R3 证据 |
|------|--------|---------|---------|---------|
| G-1 TDD | 提交顺序 | `git log` | `git log --oneline` | `.gate/tdd-report.json` |
| G-1 TDD | Red→Green 记录 | PR 描述 | 测试历史 | `.gate/tdd-report.json` |
| G-1 TDD | AC 覆盖 | Spec AC 列表 | 测试函数列表 | `.gate/ac-coverage.json` |
| G-1 TDD | 新增代码测试 | 文件 diff | 测试覆盖率 | coverage 报告 |
| G-2 Spec | Spec 存在+状态 | `specs/` 目录 | — | PR 描述引用 |
| G-2 Spec | API 对齐 | Spec API 定义 | 代码 handler | API diff 报告 |
| G-3 IPD 传导 | 上游变更传导 | `impact-log-*.md` | 文件时间戳 | 传导矩阵 |
| G-3 IPD 传导 | WBS 引用 | Phase 2 WBS | Phase 3 commit | WBS 对照表 |
| G-4 安全 | 密钥 | gitleaks | 代码扫描 | `.gate/secret-scan.json` |
| G-4 安全 | SQL 拼接 | AST 扫描 | golangci-lint gosec | 扫描报告 |
| G-4 安全 | eval/exec | AST 扫描 | — | 扫描报告 |
| G-4 安全 | Protected Paths | 路径校验代码 | 测试用例 | 测试输出 |
| G-5 质量 | 编译 | `go build` | 实际编译 | 编译输出 |
| G-5 质量 | vet | `go vet` | 实际运行 | vet 输出 |
| G-5 质量 | test | `go test` | 实际运行 | 测试输出 |
| G-5 质量 | lint | `golangci-lint` | 实际运行 | lint 输出 |
| G-5 质量 | 覆盖率基线 | coverage 对比 | `go test -cover` | coverage.json |
| G-6 幻觉 | API 存在性 | 符号解析 | 编译 | import 验证 |
| G-6 幻觉 | 依赖存在 | `go mod verify` | 实际引用 | mod tidy 输出 |
| G-6 幻觉 | 注释一致性 | 注释 vs 代码 | — | 人工确认 |
| G-6 幻觉 | 文件存在 | `os.Stat` | 实际存在 | — |
| G-6 幻觉 | 变量存在 | 符号解析 | 编译 | — |
| G-6 幻觉 | 能力不夸大 | 文档 vs 实际 | 测试验证 | 功能矩阵 |
| G-7 Self-Correction | 轮次≤3 | `.gate/self-correction.json` | 轮次计数 | JSON 记录 |
| G-7 Self-Correction | 安全漏洞未自修提交 | SAST 报告 | 提交历史 | `.gate/security-scan.json` |

**输出**：`.gate/gate-report-{date}.md`

**失败处理**：任何 Gate FAIL → 返回 Executor 修复。不得手动绕过。

### 2.5 Pass 5: Human Reviewer（人工终审）

**触发时机**：P4 Gate Checker 全部 PASS

**执行者**：人类（项目所有者/技术负责人）

**审查内容**：

| # | 审查项 | 关注点 |
|---|--------|--------|
| 1 | 战略对齐 | Phase 产出是否对齐产品愿景和商业目标？ |
| 2 | 资源可行性 | 工作量估算是否合理？执行带宽是否匹配？ |
| 3 | 风险接受度 | 识别的风险是否在可接受范围内？缓解方案是否可信？ |
| 4 | 竞争态势 | 竞品动态是否需要调整策略？ |
| 5 | 时机判断 | 现在是进入下一阶段的最佳时机吗？ |

**输出**：`.gate/pass5-human-review-{date}.md`

**决策**：APPROVE / CONDITIONAL_APPROVE（附修改意见）/ REJECT

### 2.6 Pass 6: 深度评分（Depth Score — 新增）

**触发时机**：P5 人工终审 APPROVE 之后，Phase 标记完成之前

**执行者**：独立 Agent（critic 或 architect，不得是完成该 Phase 的 Agent）

**核心目的**：检查 Phase 产出的**深度质量**，而不仅是**完整性**。P1-P5 检查"动作做了没有"，P6 检查"做得够不够深"。

#### 评分维度

对照 §1.6.8 中定义的各 Phase 评分维度逐项评分（0-3 分）：

| # | 维度 | 方法 | 证据要求 |
|---|------|------|---------|
| 1 | 竞品/需求/架构机制拆解 | 检查是否分析了"怎么做"和"为什么"，不仅是"有无" | 引用文档具体章节 |
| 2 | 边界/反例/异常场景 | 检查是否包含"什么情况下不成立" | 引用具体反例或场景 |
| 3 | 盲区/假设/风险自评 | 检查是否指出了自身方案的缺陷或盲区 | 引用具体的盲区识别记录 |
| 4 | 批判性思维 | 检查是否对比了"不这么做会怎样"或"竞品为什么不这么做" | 引用具体分析段落 |

#### 通过标准

- 每项维度 ≥ 2 分
- 总分 ≥ 该维度满分 × 60%
- `self_check` 检测无异常（非全 3 分、非全 2 分）

#### 基线检查

1. 读取 `.gate/depth-baselines.json` 获取已有基线
2. 当前评分不得低于已有基线
3. 如果某维度得分 > 历史基线，更新基线值
4. 如果某维度连续 3 次 ≥ 3 分，标记 `promoted: true`（该维度通过线提升到 ≥ 3）

#### 盲区注入

开发过程中发现的"当初没想到"的事（如本次 F015 发现泛化引擎缺失实体识别维度）：
1. 记录到 `blind_spots` 数组
2. 每个盲区必须指定应归属的 Phase 和维度
3. 该盲区自动成为后续 Feature 的永久评分维度
4. 如果盲区数量 ≥ 2，当前 Phase 深度评分标记 `[DEPTH-GAP]`

#### 输出

```json
// .gate/depth-score-{phase}.json
{
  "phase": "P0",
  "feature": "F015",
  "scored_by": "agent:critic",
  "timestamp": "2026-04-19T...",
  "dimensions": [
    {
      "name": "竞品机制拆解",
      "score": 2,
      "baseline": 1,
      "evidence": "market-insight.md §3.1.1 拆解了 SkillClaw 机制，但未分析实体提取实现",
      "gap": "未覆盖 AgentSkillOS capability-tree"
    }
  ],
  "blind_spots": [
    {
      "discovered_in": "F015",
      "phase": "P0",
      "dimension": "变量提取机制分析",
      "description": "竞品如何处理用户输入中的结构化参数（时间/地点/关系）"
    }
  ],
  "self_check": {
    "scores": [2, 2, 2, 2],
    "all_max": false,
    "all_min": false,
    "verdict": "分布合理"
  },
  "total": 8,
  "max": 12,
  "passed": true,
  "flags": []
}
```

**失败处理**：任何维度 < 2 分 → 标记 `[DEPTH-FAIL]`，返回对应 Phase 重新深化。不得人工强制通过。

---

## 3. 审查次数统计

### 3.1 自动达成的审查次数

| 维度 | 数量 | 计算 |
|------|------|------|
| Gate 数量 | 7 | §1.7.3 定义 |
| 每 Gate 检查项 | ~5（25/7） | 实际 25 项 |
| 每检查项验证轮次 | 3 | R1 静态 + R2 运行 + R3 证据 |
| Pass 数量 | 6 | P1-P5 + 深度评分 |
| **总验证次数** | **≥630** | 7 × 5 × 3 × 6 = 630 |

**注**：630 > 200，自动达成。且每次验证有明确的工具、方法和通过标准。

### 3.2 每次审查的成本

| Pass | 模型 | 预估 API 调用 | 时间估算 |
|------|------|-------------|---------|
| P1 Self-Verify | Sonnet | ~5 | 5-10 min |
| P2 Cross-Verify | Sonnet | ~15 | 15-25 min |
| P3 Adversarial | Sonnet/Opus | ~20 | 20-30 min |
| P4 Gate Checker | Haiku | ~75 (25 项 × 3 轮) | 10-15 min |
| P5 Human | 人工 | — | 15-30 min |
| P6 Depth Score | Opus/Sonnet | ~12 (4 维度 × 3 轮) | 10-20 min |
| **合计** | | ~127 | 75-130 min |

**成本优化**：
- 对于低风险 Phase（如格式调整），P3 可跳过或简化为 1 个视角
- P4 Gate Checker 使用 haiku 模型，成本极低
- 简单变更（<5 行单文件修改）可触发逃逸条件，跳过 P2-P3

---

## 4. 逃逸条件

以下情况可跳过部分审查：

| 条件 | 跳过的 Pass | 保留的 Pass | 说明 |
|------|------------|------------|------|
| 单文件修改 ≤5 行 | P2, P3 | P1, P4, P5 | 微小变更，交叉/对抗过度 |
| 纯格式/文档变更 | P2, P3, P4 | P1, P5 | 不涉及代码/架构 |
| 紧急 Hotfix（生产事故）| P3 | P1, P2, P4, P5 | 时间优先，事后补 P3 |
| AI Coding 自修 Round 2+ | P1, P3 | P2, P4 | 自修循环内，P4 Gate 足矣 |

**逃逸条件与 Process Profile 的关系**：下表中的逃逸条件对应 [01-core-specification.md](01-core-specification.md) §1.6.9 的 Process Profile S 档。当 Feature 被定为 M/L/XL 档位时，不得触发逃逸条件跳过审查。

---

## 5. 与现有规范的集成

### 5.1 修改 `01-core-specification.md`

在 §1.7 Gate Checker Agent 后新增 §1.8：

```markdown
### 1.8 Multi-Pass Review Protocol

> 完整定义：`19-multi-pass-review.md`

每个 IPD Phase 产出完成后，必须执行 6 轮审查（Self-Verify → Cross-Verify → Adversarial → Gate Checker → Human Reviewer → Depth Score）。
每轮审查对 7 个 Gate 的 25 个检查项逐项进行 3 轮独立验证。
总审查次数自动 ≥ 200（实际 630 次），不得人为削减轮次以凑数字。

逃逸条件：微小变更（≤5 行单文件）、纯格式变更、紧急 Hotfix 可跳过部分 Pass，
但必须在 Gate Report 中注明原因。
```

### 5.2 新增文档

在 `ai-coding-v5.4/INDEX.md` 中新增：

```
| 19 | [Multi-Pass Review Protocol](19-multi-pass-review.md) | 每阶段 6 轮审查 × 7 Gate × 5 检查项 × 3 轮验证 = 630 次审查 |
```

---

## 6. 审查结果记录模板

```markdown
# Gate Report — {Phase Name}

> Date: {date} | Phase: {N} | Reviewer: {Pass 执行者}

## Summary

| Gate | 检查项 | Pass | Fail | Skipped |
|------|--------|------|------|---------|
| G-1 TDD | 4 | | | |
| G-2 Spec | 2 | | | |
| ... | ... | | | |
| **Total** | **25** | | | |

## Pass Results

### P1 Self-Verify
- Status: PASS / FAIL
- Missing items: ...

### P2 Cross-Verify
- Status: PASS / FAIL
- Inconsistencies: ...

### P3 Adversarial
- Status: PASS / FAIL
- Vulnerabilities (CRITICAL/HIGH/MEDIUM): ...

### P4 Gate Checker
- Status: PASS / FAIL
- Failed check items: ...

### P5 Human Reviewer
- Decision: APPROVE / CONDITIONAL_APPROVE / REJECT
- Comments: ...

## Verdict

**APPROVED** / **REJECTED** — {理由}
```

---

*本文档定义了 ai-coding 规范中的审查协议。200 次是最低要求，实际结构自动达成 630 次。重点是每次审查有明确的工具、方法和通过标准，而非单纯的数字。*
