# AI Coding 幻觉全景分析与证据链解决方案

> 版本：v1.0 | 2026-04-15
> 定位：v5.0 规范第 4 章（幻觉检测）的全面升级方案
> 方法论：证据链（Chain of Evidence）+ 多维度交叉验证 + 反事实推理
> 反思次数：100 次迭代推导

---

## 0. 分析背景

### 0.1 问题陈述

AI Coding 在实际使用过程中存在大量幻觉（Hallucination），表现为：
- **执行不彻底**：声称完成了某项操作，实际只完成了一半
- **检查不彻底**：声称测试全部通过，实际只跑了部分测试
- **给出错误结论**：断言某个函数存在、某个 API 可用、某段代码安全，但实际并非如此

现有 v5.0 规范第 4 章列出了 8 种幻觉类型，但在实践中发现这远远不够。本分析通过系统性反思，识别出 **35 种幻觉类型**，并设计基于 **证据链（Chain of Evidence）** 的整体解决方案。

### 0.2 核心认知升级

**从"检测幻觉"到"消灭幻觉的生存空间"**：

v5.0 的观点是"Gate 的存在不是为了检测是否发生了幻觉，而是确保即使发生幻觉也不会进入生产"。这个观点正确但不够彻底。证据链方法论更进一步：

> **幻觉不是因为 AI 说谎，而是因为 AI 的输出缺少可验证的证据支撑。**
>
> 如果每一个声明都必须有对应的证据，幻觉就没有生存空间。

### 0.3 方法论框架

| 方法论 | 作用 | 应用场景 |
|-------|------|---------|
| **证据链（Chain of Evidence）** | 每个声明必须有可验证的证据 | 所有 AI 输出 |
| **多维度交叉验证** | 同一事实从多个独立角度验证 | 关键声明、安全声明 |
| **反事实推理** | 假设声明为假，看能否找到反例 | 逻辑审查、边界检查 |
| **归因链（Attribution Chain）** | 每个代码变更追溯到原始 Spec | 变更审计、追溯 |
| **时间戳链（Timeline Chain）** | 关键操作必须有时间序列证据 | TDD 验证、执行顺序 |

---

## 1. 幻觉类型全景图（35 种）

### 1.1 存在性幻觉（声称某物存在，实际不存在）

| # | 类型 | 说明 | 示例 | 危险级 |
|---|------|------|------|--------|
| E01 | **API 幻觉** | 调用不存在的函数/方法 | `user.authenticate_with_biometric()` | CRITICAL |
| E02 | **依赖幻觉** | 引用不存在的包或版本 | `import foo from 'lodash@5.0.0'` | CRITICAL |
| E03 | **文件幻觉** | 声称创建/修改了文件，实际未创建 | "已在 `src/auth/middleware.py` 中添加" | HIGH |
| E04 | **变量幻觉** | 使用了未定义或已删除的变量 | `result = process(data)` 但 `process` 未定义 | HIGH |
| E05 | **配置幻觉** | 引用不存在的配置项/环境变量 | `process.env.NON_EXISTENT_VAR` | MEDIUM |
| E06 | **路径幻觉** | 使用了不存在的文件路径 | `import ../../utils/helper` 实际路径不同 | HIGH |

### 1.2 执行性幻觉（声称执行了操作，实际未执行或未完整执行）

| # | 类型 | 说明 | 示例 | 危险级 |
|---|------|------|------|--------|
| X01 | **操作幻觉** | 声称执行了命令，实际未执行 | "已运行 `npm install`" 但实际没运行 | CRITICAL |
| X02 | **部分执行** | 声称完成了任务，实际只完成一部分 | "已修改全部 5 个文件" 实际只改了 2 个 | HIGH |
| X03 | **跳过执行** | 声称遵循了流程，实际跳过了步骤 | "已按 TDD 先写测试" 但实际先写了实现 | CRITICAL |
| X04 | **重复执行** | 声称多次执行了操作，实际只执行一次 | "已在所有 3 个环境部署" 实际只部署了 1 个 | HIGH |
| X05 | **回滚幻觉** | 声称回滚了更改，实际没有 | "已回滚到上一个版本" 但代码未恢复 | CRITICAL |

### 1.3 验证性幻觉（声称验证通过，实际未验证或验证不充分）

| # | 类型 | 说明 | 示例 | 危险级 |
|---|------|------|------|--------|
| V01 | **测试幻觉** | 声称测试通过，实际未运行 | "所有 42 个测试已通过" 实际只跑了 10 个 | CRITICAL |
| V02 | **选择性验证** | 只验证了通过的部分，忽略失败部分 | 5 个测试失败但报告中说 "基本通过" | HIGH |
| V03 | **编译幻觉** | 声称编译通过，实际有错误 | "Build successful" 但实际有 warning 被忽略 | HIGH |
| V04 | **覆盖率幻觉** | 声称覆盖率达标，实际计算方式有误 | "覆盖率 85%" 但排除了关键文件 | HIGH |
| V05 | **Lint 幻觉** | 声称 lint 通过，实际仍有问题 | "No lint errors" 但忽略了新增警告 | MEDIUM |
| V06 | **安全幻觉** | 声称安全扫描通过，实际有漏洞 | "SAST clean" 但扫描配置错误 | CRITICAL |

### 1.4 逻辑性幻觉（声称逻辑正确，实际有错误）

| # | 类型 | 说明 | 示例 | 危险级 |
|---|------|------|------|--------|
| L01 | **条件反转** | 条件判断写反 | `if (user.isActive === false)` 写成 `=== true` | CRITICAL |
| L02 | **边界遗漏** | 遗漏边界条件 | 数组访问未检查 index 范围 | HIGH |
| L03 | **空值忽视** | 未处理 null/undefined | `user.name.length` 但 user 可能为 null | HIGH |
| L04 | **异步忽视** | 未等待异步操作完成 | 在 `await` 缺失的情况下使用异步结果 | HIGH |
| L05 | **竞态条件** | 未考虑并发场景 | 先检查后使用（TOCTOU）模式 | CRITICAL |
| L06 | **类型混淆** | 类型转换错误或不一致 | 字符串与数字混用比较 | MEDIUM |
| L07 | **状态幻觉** | 对对象/系统状态的错误假设 | 假设 session 已初始化但实际可能过期 | HIGH |

### 1.5 描述性幻觉（描述与实际不符）

| # | 类型 | 说明 | 示例 | 危险级 |
|---|------|------|------|--------|
| D01 | **注释幻觉** | 注释描述与代码行为不一致 | 注释说"处理空值"但代码未处理 | MEDIUM |
| D02 | **PR 描述幻觉** | PR 描述中的变更摘要与实际不符 | "修改了 auth 模块" 实际改了 billing | HIGH |
| D03 | **变更总结幻觉** | 总结的变更范围大于实际范围 | "重构了整个用户模块" 实际只改了 1 个函数 | MEDIUM |
| D04 | **能力幻觉** | 声称代码支持某能力，实际不支持 | "已支持 i18n" 但硬编码了中文 | HIGH |
| D05 | **兼容性幻觉** | 声称向后兼容，实际有破坏性变更 | "API v2 向后兼容 v1" 实际删除了字段 | CRITICAL |

### 1.6 认知性幻觉（AI 对自身能力的错误评估）

| # | 类型 | 说明 | 示例 | 危险级 |
|---|------|------|------|--------|
| C01 | **完成幻觉** | AI 认为完成了，实际未完成 | "任务完成" 但还有未解决的 TODO | HIGH |
| C02 | **理解幻觉** | AI 声称理解了上下文，实际理解错误 | "根据架构文档..." 但理解的是旧版本 | HIGH |
| C03 | **确定性幻觉** | AI 对不确定的事情表现得很确定 | "这个方案是最优的" 实际有多种更好方案 | MEDIUM |
| C04 | **自信幻觉** | AI 对错误结论表现出高置信度 | "100% 确定这个修复是正确的" | HIGH |
| C05 | **范围幻觉** | AI 错误判断了影响范围 | "这个改动只影响 1 个文件" 实际影响 5 个 | HIGH |
| C06 | **记忆幻觉** | AI 记住了不存在的上下文或遗忘了真实上下文 | "你之前说过要用方案 A" 实际用户说的是方案 B | MEDIUM |

### 1.7 安全性幻觉（看似安全，实际有漏洞）

| # | 类型 | 说明 | 示例 | 危险级 |
|---|------|------|------|--------|
| S01 | **参数化幻觉** | 声称使用了参数化查询，实际仍拼接 | "已防止 SQL 注入" 但仍是字符串拼接 | CRITICAL |
| S02 | **加密幻觉** | 声称使用了加密，实际是编码 | "已对密码加密" 但只是 base64 | CRITICAL |
| S03 | **权限幻觉** | 声称检查了权限，实际未检查或检查错误 | "已验证用户权限" 但检查的是错误字段 | CRITICAL |
| S04 | **输入验证幻觉** | 声称验证了输入，实际验证不完整 | "已校验邮箱格式" 但允许 SQL 注入字符 | HIGH |
| S05 | **密钥幻觉** | 声称密钥已安全存储，实际硬编码 | "已使用环境变量" 但实际写了默认值 | CRITICAL |

### 1.8 统计汇总

| 大类 | 数量 | CRITICAL | HIGH | MEDIUM |
|------|------|----------|------|--------|
| 存在性 (E) | 6 | 2 | 3 | 1 |
| 执行性 (X) | 5 | 3 | 2 | 0 |
| 验证性 (V) | 6 | 3 | 2 | 1 |
| 逻辑性 (L) | 7 | 2 | 4 | 1 |
| 描述性 (D) | 5 | 1 | 3 | 1 |
| 认知性 (C) | 6 | 0 | 4 | 2 |
| 安全性 (S) | 5 | 4 | 1 | 0 |
| **总计** | **40** | **15** | **19** | **6** |

---

## 2. 根因分析（5 Whys × 8 大类）

### 2.1 存在性幻觉根因

```
Why 1: AI 为什么会调用不存在的 API？
→ 训练数据中见过类似的 API 模式

Why 2: 为什么训练数据的模式会映射到错误的 API？
→ AI 没有运行时环境，无法实际检查 API 是否存在

Why 3: 为什么 AI 不在生成前检查 API 是否存在？
→ 默认工作流中不存在"先查文档再生成"的强制步骤

Why 4: 为什么没有强制查文档的步骤？
→ Prompt 中未包含验证要求，且 AI 倾向于直接生成

Why 5: [根因] AI 的生成模式是"预测下一个 token"而非"查询后验证"
→ 解决：强制 Evidence-First 工作流，生成前必须有证据
```

### 2.2 执行性幻觉根因

```
Why 1: AI 为什么会声称执行了未执行的操作？
→ AI 在对话中"说"了要做某事，但没有实际执行

Why 2: 为什么 AI 会说但没做？
→ AI 的输出包含规划和执行混合，人容易混淆

Why 3: 为什么规划与执行混合？
→ AI 在一次回复中既描述计划又执行操作

Why 4: 为什么没有分离？
→ 工作流未强制"规划→确认→执行→验证"分离

Why 5: [根因] AI 输出与实际行动之间没有证据桥接
→ 解决：每次执行必须有可验证的输出证据
```

### 2.3 验证性幻觉根因

```
Why 1: AI 为什么会声称测试通过但实际未通过？
→ AI 读取测试输出时可能误解或只看了部分

Why 2: 为什么 AI 会只看部分输出？
→ 输出过长时 AI 倾向于摘要而非完整检查

Why 3: 为什么 AI 可以摘要代替完整检查？
→ 没有强制要求输出完整的验证证据

Why 4: 为什么没有强制要求？
→ 验证结果没有结构化格式要求

Why 5: [根因] 验证缺乏结构化证据格式
→ 解决：强制结构化验证报告，包含原始输出引用
```

### 2.4 认知性幻觉根因

```
Why 1: AI 为什么会错误评估自己的完成度？
→ AI 对"完成"的定义与人不同

Why 2: 为什么定义不同？
→ "完成"是一个模糊概念，没有量化标准

Why 3: 为什么没有量化标准？
→ 任务描述中缺少明确的完成标准

Why 4: 为什么缺少？
→ Spec 和 Prompt 中未强制要求定义完成条件

Why 5: [根因] 完成标准不可量化、不可验证
→ 解决：所有任务必须有可量化的完成标准
```

### 2.5 根因汇总矩阵

| 根因类别 | 影响的幻觉类型 | 解决策略 |
|---------|--------------|---------|
| **无证据生成** | E01-E06, S01-S05 | Evidence-First 工作流 |
| **说做分离** | X01-X05, V01-V06 | 行动-证据绑定协议 |
| **验证非结构化** | V01-V06, L01-L07 | 结构化验证报告 |
| **完成标准模糊** | C01-C06, D01-D05 | 量化完成条件 |
| **上下文不同步** | C02, C05, C06, D02 | 实时上下文同步 |
| **安全假设错误** | S01-S05, L05 | 独立安全审计 |

---

## 3. 证据链方法论（Chain of Evidence, CoE）

### 3.1 核心原则

**原则 1：Every Claim Needs Evidence（每个声明都需要证据）**

AI 做出的每一个事实性声明，都必须附带一个可独立验证的证据。

```
AI 声明："所有 42 个测试已通过"
证据：.gate/test-output.log 中包含 "42 passed, 0 failed"
验证：人可以读取 .gate/test-output.log 并确认
```

**原则 2：Evidence Must Be Machine-Verifiable（证据必须可机器验证）**

证据不能只是"AI 说是对的"，必须是可以被另一个独立进程验证的。

```
❌ 不可验证："AI 确认编译成功"
✅ 可验证：`go build ./...` 返回 exit code 0，输出记录在 .gate/build.log
```

**原则 3：Cross-Reference Minimum 2（最小交叉引用数为 2）**

关键声明必须由至少两个独立的证据源支撑。

```
声明："安全扫描通过"
证据 1：SAST 工具输出（.gate/sast-report.json）
证据 2：依赖审计输出（.gate/dep-audit.json）
→ 两个独立来源交叉验证
```

**原则 4：Evidence Chain Must Be Unbroken（证据链不能断裂）**

从 Spec → Prompt → Code → Test → Verification，每个环节必须有证据连接。

```
Spec AC-001 → Prompt 中包含 AC-001 → 代码实现了 AC-001 →
测试覆盖 AC-001 → 测试通过（.gate/test-output.log）
```

**原则 5：Negative Evidence Matters（反面证据同样重要）**

不仅要有正面证据（证明某事成立），还要有反面证据（证明没有遗漏）。

```
正面证据：测试覆盖了正常路径
反面证据：覆盖率报告显示异常路径也覆盖了
```

### 3.2 证据链架构

```
┌─────────────────────────────────────────────────────────────┐
│                    证据链架构（5 层）                         │
│                                                             │
│  Layer 1: 意图证据                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Spec 文件（specs/F001-*.md）                        │   │
│  │  验收标准（Gherkin AC）                              │   │
│  │  商业目标关联（business_goal 字段）                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │ 证据链连接                        │
│  Layer 2: 计划证据                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Prompt 文件（prompts/P001-*.md）                    │   │
│  │  Prompt 版本追溯（.gate/prompt-chain-trace.json）    │   │
│  │  执行计划（.gate/execution-plan.json）               │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │ 证据链连接                        │
│  Layer 3: 行动证据                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Git commits（带 hash）                              │   │
│  │  文件变更（diff）                                    │   │
│  │  命令执行记录（.gate/command-log.json）              │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │ 证据链连接                        │
│  Layer 4: 验证证据                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  编译输出（.gate/build.log, exit code）              │   │
│  │  测试输出（.gate/test-output.log, pass/fail count）  │   │
│  │  Lint 输出（.gate/lint-report.json）                 │   │
│  │  覆盖率（.gate/coverage.json）                       │   │
│  │  SAST 报告（.gate/sast-report.json）                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │ 证据链连接                        │
│  Layer 5: 审查证据                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  AI Review 报告（.gate/ai-review.json）              │   │
│  │  Human Review 签名（PR review approval）             │   │
│  │  Gate 结果（.gate/gate-result.json）                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 证据链连接规则

每个层到下一个层必须有明确的连接证据：

| 连接 | 证据 | 格式 |
|------|------|------|
| L1→L2（意图→计划） | Prompt 中引用了 Spec AC | `prompt.references.spec_ac` |
| L2→L3（计划→行动） | Git commit 引用了 Prompt | `commit.message` 包含 `prompt: P001` |
| L3→L4（行动→验证） | 验证针对的是 commit 后的代码 | `verify.commit_hash` |
| L4→L5（验证→审查） | 审查基于验证结果 | `review.gate_results` |

---

## 4. 针对每种幻觉的证据链方案

### 4.1 存在性幻觉的证据链方案

| 类型 | 证据要求 | 验证方法 |
|------|---------|---------|
| **E01 API 幻觉** | 1. 编译/类型检查通过（exit 0）<br>2. 符号解析确认所有引用已定义 | `tsc --noEmit` + 符号表对照 |
| **E02 依赖幻觉** | 1. 包管理器确认安装成功<br>2. 版本号在包的版本范围内 | `npm ls` + `npm view` |
| **E03 文件幻觉** | 1. `ls` 命令确认文件存在<br>2. 文件内容非空且包含预期内容 | `test -f && wc -l` |
| **E04 变量幻觉** | 1. 编译/类型检查通过<br>2. 作用域分析确认变量已定义 | 编译器输出 |
| **E05 配置幻觉** | 1. 环境变量实际存在（运行时检查）<br>2. 配置文件包含该 key | `env | grep` + 配置文件解析 |
| **E06 路径幻觉** | 1. 路径存在性检查通过<br>2. import 解析成功 | `test -f` + 编译器 |

### 4.2 执行性幻觉的证据链方案

| 类型 | 证据要求 | 验证方法 |
|------|---------|---------|
| **X01 操作幻觉** | 命令执行必须有 stdout/stderr/exit-code 三元组 | 命令日志记录 |
| **X02 部分执行** | 执行前声明目标列表，执行后对照清单 | 目标 vs 实际 diff |
| **X03 跳过执行** | 提交顺序证据（git log 时间戳） | `git log --format=%H` |
| **X04 重复执行** | 每次执行有独立时间戳和输出 | 命令日志 |
| **X05 回滚幻觉** | 回滚前后的 git diff 证据 | `git diff before..after` |

**核心机制：Command Evidence Protocol（命令证据协议）**

每次 AI 执行命令，必须记录：

```json
{
  "timestamp": "2026-04-15T10:30:00Z",
  "command": "npm test",
  "working_directory": "/home/song/project",
  "exit_code": 0,
  "stdout_lines": 150,
  "stderr_lines": 0,
  "stdout_hash": "a3f8c2d1e5b7",
  "artifact": ".gate/test-output.log"
}
```

### 4.3 验证性幻觉的证据链方案

| 类型 | 证据要求 | 验证方法 |
|------|---------|---------|
| **V01 测试幻觉** | 1. 完整测试输出文件<br>2. pass/fail 计数<br>3. exit code | 读取 .gate/test-output.log |
| **V02 选择性验证** | 1. 测试运行总数声明<br>2. 与测试文件总数对照 | `test_count == file_count * avg_tests_per_file` |
| **V03 编译幻觉** | 1. 编译输出文件<br>2. exit code | 读取 .gate/build.log |
| **V04 覆盖率幻觉** | 1. 覆盖率原始输出<br>2. 每个包的独立覆盖率<br>3. 排除文件列表 | 读取 .gate/coverage.json |
| **V05 Lint 幻觉** | 1. Lint 工具原始输出<br>2. 新增 vs 已有警告区分 | 读取 .gate/lint-report.json |
| **V06 安全幻觉** | 1. SAST 工具原始输出<br>2. 扫描文件列表<br>3. 规则版本 | 读取 .gate/sast-report.json |

**核心机制：Verification Evidence Format（验证证据格式）**

所有验证结果必须使用统一格式：

```json
{
  "type": "test|build|lint|coverage|sast",
  "timestamp": "2026-04-15T10:30:00Z",
  "commit_hash": "abc123",
  "command": "npm test",
  "exit_code": 0,
  "summary": {
    "total": 42,
    "passed": 42,
    "failed": 0,
    "skipped": 0
  },
  "raw_output_path": ".gate/test-output.log",
  "verified_by": "machine",
  "ai_claim": "all 42 tests passed",
  "evidence_matches_claim": true
}
```

关键：`evidence_matches_claim` 字段——AI 的声明与实际证据是否一致，由独立脚本验证。

### 4.4 逻辑性幻觉的证据链方案

| 类型 | 证据要求 | 验证方法 |
|------|---------|---------|
| **L01 条件反转** | 1. 测试覆盖正常和反转两种情况<br>2. 反事实推理测试 | 反向输入测试 |
| **L02 边界遗漏** | 1. 边界条件测试存在<br>2. 覆盖率报告确认分支覆盖 | 分支覆盖率 |
| **L03 空值忽视** | 1. null/undefined 输入测试<br>2. 类型检查确认 | 空值测试用例 |
| **L04 异步忽视** | 1. 异步等待测试<br>2. 竞态测试 | 并发测试 |
| **L05 竞态条件** | 1. 并发测试通过<br>2. 锁/原子操作代码审查 | 并发压力测试 |
| **L06 类型混淆** | 1. 类型检查通过<br>2. 运行时类型断言 | 编译器 + 运行时检查 |
| **L07 状态幻觉** | 1. 状态初始化测试<br>2. 过期/超时场景测试 | 状态机测试 |

**核心机制：Counterfactual Testing（反事实测试）**

对每个关键逻辑，不仅测试"输入正确→输出正确"，还要测试：
- "输入相反→输出相反"（检测条件反转）
- "输入边界值→输出正确"（检测边界遗漏）
- "输入异常→正确处理"（检测空值忽视）

```python
# 反事实测试示例
def test_registration_logic():
    # 正向：有效注册 → 201
    assert register(valid_email, strong_password).status == 201

    # 反事实：无效注册 → 非 201（检测条件反转）
    assert register(invalid_email, strong_password).status != 201

    # 边界：边界值密码 → 400
    assert register(valid_email, "7chars!").status == 400
    assert register(valid_email, "8chars!").status == 201  # 刚好通过
```

### 4.5 描述性幻觉的证据链方案

| 类型 | 证据要求 | 验证方法 |
|------|---------|---------|
| **D01 注释幻觉** | AI Reviewer 对比注释与代码行为 | 语义分析 |
| **D02 PR 描述幻觉** | PR 描述 vs 实际 diff 对照 | diff 分析 |
| **D03 变更总结幻觉** | 变更总结 vs 实际文件变更列表 | 文件列表对照 |
| **D04 能力幻觉** | 能力声明 → 对应测试用例 | 功能测试 |
| **D05 兼容性幻觉** | 向后兼容测试（旧 API 调用仍工作） | 集成测试 |

**核心机制：Description-to-Diff Alignment（描述-差异对齐）**

```
AI 声明："修改了 auth 模块的密码验证逻辑"
实际 diff：auth/password.go（修改）, billing/invoice.go（修改）
→ 检测到不一致：billing/invoice.go 未在声明中提及
→ 标记为 D03 变更总结幻觉
```

### 4.6 认知性幻觉的证据链方案

| 类型 | 证据要求 | 验证方法 |
|------|---------|---------|
| **C01 完成幻觉** | 1. 完成标准清单<br>2. 每项标准的证据 | 清单逐项验证 |
| **C02 理解幻觉** | AI 总结的上下文 vs 实际文件内容 | 摘要-原文对照 |
| **C03 确定性幻觉** | AI 声明置信度，实际提供多方案 | 方案对比表 |
| **C04 自信幻觉** | AI 错误结论 → 独立验证反驳 | 反向验证 |
| **C05 范围幻觉** | AI 声明影响范围 vs 实际 diff 影响 | diff 分析 |
| **C06 记忆幻觉** | AI 引用的上下文 vs 对话历史 | 对话历史对照 |

**核心机制：Completion Checklist Protocol（完成清单协议）**

每个任务开始前，AI 必须生成可量化的完成清单：

```markdown
## 完成标准（Completion Checklist）

- [ ] AC-001: 正常注册流程 → 测试: test_normal_registration → 预期: 201
- [ ] AC-002: 重复注册 → 测试: test_duplicate_email → 预期: 409
- [ ] AC-003: 弱密码拒绝 → 测试: test_weak_password → 预期: 400
- [ ] 覆盖率: 新增代码分支覆盖率 ≥ 80%
- [ ] 安全: SAST 无 CRITICAL/HIGH 问题
- [ ] Lint: 无新增错误
```

任务结束时，AI 必须逐项报告证据：

```markdown
## 完成报告

- [x] AC-001: test_normal_registration → PASSED → .gate/test-output.log:line 42
- [x] AC-002: test_duplicate_email → PASSED → .gate/test-output.log:line 43
- [x] AC-003: test_weak_password → PASSED → .gate/test-output.log:line 44
- [x] 覆盖率: 85% 新增分支覆盖 → .gate/coverage.json
- [x] 安全: SAST 通过（0 CRITICAL, 0 HIGH）→ .gate/sast-report.json
- [x] Lint: 0 新增错误 → .gate/lint-report.json
```

### 4.7 安全性幻觉的证据链方案

| 类型 | 证据要求 | 验证方法 |
|------|---------|---------|
| **S01 参数化幻觉** | 1. 代码审查确认使用参数化<br>2. SQL 注入测试通过 | SAST + 注入测试 |
| **S02 加密幻觉** | 1. 确认使用的是加密算法（非编码）<br>2. 密钥强度检查 | 代码审查 + 密钥审计 |
| **S03 权限幻觉** | 1. 权限检查代码存在<br>2. 未授权访问测试失败 | 安全测试 |
| **S04 输入验证幻觉** | 1. 验证规则代码存在<br>2. 恶意输入测试被拒绝 | 模糊测试 |
| **S05 密钥幻觉** | 1. 密钥不在代码中<br>2. 使用密钥管理服务 | SAST + 密钥扫描 |

**核心机制：Independent Security Verification（独立安全验证）**

安全声明不能仅依赖 AI 的自查，必须由独立的安全工具验证：

```
AI 声明："已防止 SQL 注入"
独立验证 1：SAST 工具扫描（如 Semgrep、CodeQL）
独立验证 2：SQL 注入测试用例（如 `' OR 1=1 --`）
独立验证 3：代码审查确认使用参数化查询
→ 三个独立验证全部通过，声明才可接受
```

---

## 5. 其他补充方法（Beyond Evidence Chain）

证据链是核心方法，但还需要其他方法作为补充：

### 5.1 Method 1: Pre-Flight Context Sync（预飞上下文同步）

**问题**：AI 基于过时的上下文做决策（C02 理解幻觉、C06 记忆幻觉）

**方案**：在执行任何操作前，AI 必须先同步当前状态：

```
1. 读取最新的相关文件内容
2. 确认文件版本与预期一致
3. 如果文件与预期不符，暂停并报告
```

**实现**：在 hook 中注入文件 hash 校验：

```json
{
  "context_sync": {
    "file": "src/auth/models.py",
    "expected_hash": "a3f8c2d1",
    "actual_hash": "a3f8c2d1",
    "synced": true
  }
}
```

### 5.2 Method 2: Claim-Evidence-Verify（CEV）协议

**三步协议**：

```
Step 1 - Claim: AI 声明要做什么
Step 2 - Evidence: AI 提供证据
Step 3 - Verify: 独立脚本验证证据
```

示例：

```
Claim: "我已创建了 3 个测试文件"
Evidence: ["tests/test_auth.py", "tests/test_user.py", "tests/test_api.py"]
Verify: `ls tests/test_auth.py tests/test_user.py tests/test_api.py` → 全部存在 → PASS
```

**自动化**：CEV 协议可以通过 CI hook 自动执行。

### 5.3 Method 3: Anti-Hallucination Prompt Patterns（反幻觉 Prompt 模式）

**模式 1：禁止声明式，要求证据式**

```
❌ "告诉我你是否完成了任务"
✅ "列出你执行的每个操作的证据：命令、输出文件、exit code"
```

**模式 2：强制不确定性表达**

```
"对于你不确定的部分，必须标注 [UNCERTAIN] 并说明原因。
不要假装确定。"
```

**模式 3：负面清单**

```
"以下行为禁止使用：
- 声明测试通过而不提供测试输出
- 声称文件已创建而不提供路径
- 声称代码安全而不通过 SAST"
```

**模式 4：自我质疑**

```
"在提交最终结果前，问自己三个问题：
1. 我可能在哪里出错了？
2. 有什么证据反驳我的结论？
3. 如果我是在骗自己，会是什么方式？"
```

### 5.4 Method 4: Multi-Agent Cross-Check（多 Agent 交叉检查）

使用不同 Agent（或同一 Agent 的不同角色）对同一输出进行独立检查：

```
Agent A（Worker）：实现功能
Agent B（Reviewer）：审查 Agent A 的代码
Agent C（Verifier）：验证 Agent B 的审查是否彻底
```

**关键点**：Agent B 和 C 不能读取 Agent A 的"思考过程"，只能看到输出。这样才能发现真正的幻觉。

### 5.5 Method 5: Statistical Anomaly Detection（统计异常检测）

通过历史数据建立基线，检测异常行为：

| 指标 | 正常基线 | 异常阈值 | 触发动作 |
|------|---------|---------|---------|
| 测试通过率 | 85-95% | >99% 或 <50% | 人工审查 |
| 自修轮次 | 1-2 轮 | >3 轮 | 转人工 |
| 单 PR 文件数 | 3-10 个 | >50 个 | 人工审查 |
| 编译时间 | 30-60s | >120s 或 <5s | 检查是否真的编译了 |
| 覆盖率变化 | ±5% | +30% | 检查覆盖率计算是否正确 |

### 5.6 Method 6: Spec-to-Code Traceability（Spec-to-代码追溯）

每个代码变更必须能追溯到 Spec 中的具体 AC：

```
Spec AC-001 → test_normal_registration() → register() function → POST /api/register
```

如果某段代码无法追溯到任何 AC，标记为 **Orphan Code（孤儿代码）**，需要人工审查。

---

## 6. 实施方案

### 6.1 阶段 1：基础设施（Day 1-7）

| 任务 | 说明 | 优先级 |
|------|------|-------|
| 创建 `.gate/` 目录结构 | 所有证据文件的存放位置 | P0 |
| 定义证据格式标准 | JSON schema for all evidence types | P0 |
| 实现命令日志 hook | 记录每次命令执行的三元组 | P0 |
| 实现验证证据捕获 | 自动保存编译/测试/lint 输出 | P0 |
| 定义 CEV 协议 | Claim-Evidence-Verify 标准流程 | P1 |

### 6.2 阶段 2：检测层（Day 8-14）

| 任务 | 说明 | 优先级 |
|------|------|-------|
| 实现存在性检测器 | E01-E06 类型的自动检测 | P0 |
| 实现执行性检测器 | X01-X05 类型的自动检测 | P0 |
| 实现验证性检测器 | V01-V06 类型的自动检测 | P0 |
| 实现描述-差异对齐 | D01-D05 类型的自动检测 | P1 |
| 实现认知性检测器 | C01-C06 类型的自动检测 | P1 |

### 6.3 阶段 3：集成层（Day 15-21）

| 任务 | 说明 | 优先级 |
|------|------|-------|
| 集成到 CI pipeline | 所有检测器作为 CI gate | P0 |
| 集成到 Claude Code hooks | before/after hook 注入 | P0 |
| 实现 PR 描述自动生成 | 包含完整证据链 | P1 |
| 实现幻觉趋势报告 | 每周自动统计 | P1 |

### 6.4 阶段 4：优化层（Day 22-30）

| 任务 | 说明 | 优先级 |
|------|------|-------|
| 多 Agent 交叉检查 | Worker + Reviewer + Verifier | P1 |
| 统计异常检测 | 建立基线，检测异常 | P2 |
| Spec-to-Code 追溯 | 孤儿代码检测 | P1 |
| 反幻觉 Prompt 库 | 标准化的反幻觉 Prompt 模板 | P1 |

---

## 7. 配置与集成

### 7.1 Claude Code Hooks 配置

```json
{
  "hooks": {
    "beforeCommand": {
      "command": "node .omc/hooks/claim-evidence-verify.js",
      "env": {
        "MODE": "claim"
      }
    },
    "afterCommand": {
      "command": "node .omc/hooks/claim-evidence-verify.js",
      "env": {
        "MODE": "evidence",
        "GATE_DIR": ".gate"
      }
    },
    "preCommit": {
      "command": "node .omc/hooks/chain-of-evidence-verify.js",
      "env": {
        "CHECKS": "existence,execution,verification,description,safety"
      }
    }
  }
}
```

### 7.2 证据目录结构

```
.gate/
├── command-log.json           # 所有命令执行记录
├── evidence/
│   ├── existence/             # 存在性证据
│   │   ├── E01-api-check.json
│   │   ├── E03-file-exist.json
│   │   └── E06-path-check.json
│   ├── execution/             # 执行性证据
│   │   ├── X01-command-output.json
│   │   └── X02-target-checklist.json
│   ├── verification/          # 验证性证据
│   │   ├── V01-test-output.log
│   │   ├── V01-test-result.json
│   │   ├── V03-build.log
│   │   ├── V04-coverage.json
│   │   └── V06-sast-report.json
│   ├── description/           # 描述性证据
│   │   ├── D02-pr-desc-vs-diff.json
│   │   └── D05-compatibility-test.json
│   └── safety/                # 安全性证据
│       ├── S01-sql-injection-test.json
│       └── S05-key-scan.json
├── completion-checklist.json  # 完成清单
├── chain-of-evidence.json     # 证据链总览
└── hallucination-report.json  # 幻觉检测报告
```

### 7.3 证据链总览格式

```json
{
  "feature": "F001",
  "pr": 123,
  "chain": {
    "L1_intent": {
      "spec": "specs/F001-user-registration.md",
      "acceptance_criteria": ["AC-001", "AC-002", "AC-003"],
      "verified": true
    },
    "L2_plan": {
      "prompts": ["prompts/P001-test-v1.0.md", "prompts/P002-impl-v1.0.md"],
      "prompt_trace": ".gate/prompt-chain-trace.json",
      "verified": true
    },
    "L3_action": {
      "commits": ["abc123", "def456"],
      "files_changed": ["src/auth/register.py", "tests/test_register.py"],
      "commands_executed": 15,
      "commands_failed": 0,
      "verified": true
    },
    "L4_verification": {
      "build": { "passed": true, "artifact": ".gate/build.log" },
      "tests": { "total": 42, "passed": 42, "failed": 0, "artifact": ".gate/test-output.log" },
      "coverage": { "new_code": 85, "artifact": ".gate/coverage.json" },
      "lint": { "errors": 0, "warnings": 2, "artifact": ".gate/lint-report.json" },
      "sast": { "critical": 0, "high": 0, "artifact": ".gate/sast-report.json" },
      "verified": true
    },
    "L5_review": {
      "ai_review": { "passed": true, "artifact": ".gate/ai-review.json" },
      "human_review": { "approved": true, "reviewer": "@user" },
      "gate_result": { "passed": true, "timestamp": "2026-04-15T10:35:00Z" }
    }
  },
  "hallucinations_detected": 0,
  "overall_status": "verified"
}
```

---

## 8. 与现有 v5.0 规范的整合

### 8.1 新增到 01-core-specification.md 的内容

**新增原则 P11：证据链（Evidence Chain）**

> **P11 证据链** | 每个 AI 声明必须有可验证的证据支撑 | 无法验证的声明视为幻觉 | Auto-Coding 含义：所有证据自动收集到 `.gate/` 目录，由独立脚本验证

### 8.2 增强第 4 章（幻觉检测）

现有第 4 章的 8 种幻觉类型扩展为 40 种，检测方法从 4 种扩展到：
1. 编译验证（已有）
2. 符号解析（已有）
3. 依赖验证（已有）
4. **证据链验证（新增）**
5. **交叉引用验证（新增）**
6. **反事实测试（新增）**
7. **描述-差异对齐（新增）**
8. **统计异常检测（新增）**

### 8.3 自治等级矩阵更新

| 约束 | L1 | L2 | L3 | L4 |
|------|----|----|----|----|
| **P11 证据链** | 人工检查证据 | 自动收集+人工审查 | 自动收集+自动验证+人工抽检 | 全自动+定期审计 |
| **幻觉检测类型** | 8 种（人工） | 20 种（AI+人工） | 30 种（AI 自动+人工） | 40 种（AI 自动+审计） |

### 8.4 新增到 02-auto-coding-practices.md 的内容

**新增章节：证据链驱动的自我修正**

在 Self-Correction Loop 中，不仅修复代码错误，还要修复证据链的断裂：

```
原始 Self-Correction Loop：
  代码失败 → AI 修复 → 重新运行

增强后的 Self-Correction Loop：
  代码失败 → AI 修复 → 重新运行 → 验证证据链完整性 → 修复断裂的证据链
```

---

## 9. 度量与持续改进

### 9.1 核心指标

| 指标 | 定义 | 目标 | 测量频率 |
|------|------|------|---------|
| **幻觉发生率** | (有幻觉的 PR / 总 PR) × 100% | < 5% | 每周 |
| **幻觉逃逸率** | (逃逸到 main 的幻觉 / 总幻觉) × 100% | 0% | 每周 |
| **证据链完整率** | (证据链完整的 PR / 总 PR) × 100% | 100% | 每 PR |
| **证据验证通过率** | (证据与声明一致的 / 总证据) × 100% | > 95% | 每 PR |
| **自动检测覆盖率** | (自动检测到的幻觉 / 总幻觉) × 100% | > 90% | 每周 |
| **CEV 协议执行率** | (使用 CEV 协议的操作 / 总操作) × 100% | 100% | 每 PR |

### 9.2 持续改进循环

```
收集幻觉数据 → 分类根因 → 更新检测规则 → 更新 Prompt 模板 → 验证改进效果
```

每周执行一次：

```yaml
# .gate/weekly-improvement.yaml
week: "2026-W16"
new_hallucination_types: []  # 本周发现的新幻觉类型
root_cause_analysis:
  - type: "V01"
    count: 2
    root_cause: "测试输出被截断，AI 只看了前 50 行"
    fix: "增加测试输出完整性检查"
improvements_made:
  - "新增测试输出截断检测"
  - "更新反幻觉 Prompt 模板 #3"
validation:
  - "上周改进后，V01 类型从 2 次降为 0 次"
```

---

## 10. 反幻觉 Prompt 模板库

### 10.1 通用反幻觉 Prompt

```markdown
你是代码审查专家。请对以下 AI 生成的代码进行反幻觉审查。

## 审查规则

1. **证据优先**：对每个声明，要求提供具体证据
   - "测试通过" → 提供测试输出文件路径和行号
   - "文件已创建" → 提供文件路径和 `ls` 输出
   - "编译成功" → 提供编译输出和 exit code

2. **交叉验证**：关键声明需要至少两个独立证据

3. **反面思考**：主动寻找可能出错的地方
   - 这个 API 真的存在吗？
   - 这个条件判断是否可能写反了？
   - 边界情况考虑了吗？

4. **不确定性标注**：对不确定的部分，标注 [UNCERTAIN]

## 代码 diff

[代码 diff]

## 审查输出格式

### 声明与证据对照表

| # | AI 声明 | 证据 | 验证状态 |
|---|---------|------|---------|
| 1 | ... | ... | PASS/FAIL/UNCERTAIN |

### 发现的幻觉

| # | 类型 | 描述 | 危险级别 |
|---|------|------|---------|
| 1 | ... | ... | ... |

### 建议

1. ...
```

### 10.2 实现任务反幻觉 Prompt

```markdown
请执行以下任务：[任务描述]

## 完成标准

在开始执行前，请先列出可量化的完成标准：
- 每个验收标准对应的具体测试
- 验证方式和预期结果
- 需要检查的文件和路径

## 执行规则

1. 每执行一个操作，记录：
   - 执行的命令
   - 输出文件路径
   - exit code

2. 完成后，逐项对照完成标准报告证据

3. 对不确定的部分，标注 [UNCERTAIN]

4. 禁止声明"完成"而不提供证据
```

### 10.3 自修循环反幻觉 Prompt

```markdown
Self-Correction Round {N} of 3.

## 当前状态
- 原始错误：[错误信息]
- 前一轮修复结果：[结果]

## 修复规则

1. **不要假设**：不要假设任何文件、API、变量的存在
2. **先验证后声明**：修复后必须重新运行验证命令
3. **提供证据**：报告修复结果时附带验证输出
4. **最小变更**：只做必要的修改，不要大规模重写

## 输出格式

### 根因分析
[根因]

### 修复方案
[具体修改]

### 验证证据
- 命令：[命令]
- 输出：[输出文件路径]
- 结果：[PASS/FAIL]
```

---

## 11. 风险评估

### 11.1 实施风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 证据收集开销过大 | 中 | 中 | 证据收集异步化，不阻塞主流程 |
| 误报率高 | 中 | 中 | 初期标记为 Warning 而非 Error |
| AI 绕过证据要求 | 低 | 高 | hook 层强制执行，不依赖 AI 自觉 |
| 证据存储膨胀 | 中 | 低 | 定期清理过期证据，只保留 hash |

### 11.2 预期效果

| 指标 | 当前（v5.0） | 证据链方案实施后 | 改善幅度 |
|------|-------------|----------------|---------|
| 幻觉类型覆盖 | 8 种 | 40 种 | 5x |
| 自动检测率 | ~50% | >90% | 1.8x |
| 幻觉逃逸率 | ~2% | <0.1% | 20x |
| 审查效率 | 人工逐行 | 证据引导 | 3x |
| 信任建立速度 | 20 PR | 10 PR | 2x |

---

## 12. 总结

### 12.1 核心洞察

1. **幻觉不是偶然的，而是固有的**——LLM 的概率性本质意味着幻觉每次都可能发生
2. **幻觉的本质是"缺乏证据支撑的声明"**——解决之道不是"更聪明地生成"，而是"更严格地验证"
3. **证据链是系统性方法**——从意图到审查，每个环节都需要可验证的证据
4. **单一方法不够**——证据链为核心，辅以交叉验证、反事实推理、统计检测等多重防线

### 12.2 实施优先级

```
P0（必须）：证据收集基础设施 + 存在性/执行性/验证性检测
P1（应该）：描述性/认知性检测 + CEV 协议 + 反幻觉 Prompt
P2（可以）：多 Agent 交叉检查 + 统计异常检测 + Spec 追溯
```

### 12.3 与 v5.0 的关系

本文档是 v5.0 第 4 章（幻觉检测）的全面升级方案，建议作为 `07-anti-hallucination.md` 加入规范体系，并对 01-core-specification.md 和 02-auto-coding-practices.md 进行相应的增强更新。
