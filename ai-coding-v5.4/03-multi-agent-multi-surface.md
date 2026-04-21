# AI Coding 规范 v5.5：多 Agent 与多平台

> 版本：v5.5 | 2026-04-21
> 定位：Sub-Agents、Agent SDK、协作会诊模式、多平台协同的实践指南
> 前置：必须先阅读并理解 [01-core-specification.md](01-core-specification.md)

---

## 第 1 章：Sub-Agents

### 1.1 什么是 Sub-Agent

Sub-Agent 是主 Agent 启动的独立执行单元，每个 Sub-Agent 有独立的上下文窗口和工具集。

### 1.2 Sub-Agent 类型

| 类型 | 能力 | 适用场景 |
|------|------|---------|
| Explore | 只读（Read、Grep、Glob、Bash） | 代码探索、文件搜索 |
| Plan | 只读 + 规划 | 架构设计、实现规划 |
| general-purpose | 全部工具 | 实现、调试、重构 |

### 1.3 安全约束

- Sub-Agent 继承主 Agent 的权限限制（deny 规则）
- Sub-Agent 不得修改安全敏感文件（secrets/、.env）
- Sub-Agent 的所有输出必须经过主 Agent 验证
- 安全相关变更必须在主 Agent 上下文中审查

---

## 第 2 章：协作会诊式多 Agent（质量导向）

> **核心原则**：多 Agent 的首要目标是提高产出质量，不是提高执行效率。多个独立视角审视同一个产出物，比单个 Agent 在任何单一上下文窗口中都能达到更深的理解。

### 2.1 两种多 Agent 模式

| 维度 | 流水线模式（第 11 章） | 会诊模式（本章） |
|------|----------------------|-----------------|
| **目的** | 效率：并行开发不同模块 | 质量：多视角深度审视同一产出 |
| **结构** | 接力式（A 做完传 B） | 会诊式（A/B/C 独立审视同一对象） |
| **上下文** | 每个 Agent 只看自己那部分 | 每个 Agent 加载不同视角的规范章节 |
| **适用** | 大功能的模块级并行开发 | 关键模块的质量保障、复杂设计决策 |
| **产出** | 代码片段拼装 | 单一高质量产出 + 多视角审查报告 |

### 2.2 会诊模式架构

```
主 Agent（任务入口）
  │ 判断任务复杂度，决定是否启用会诊模式
  ▼
TeamCreate("quality-review-{feature}")
  │
  ├── Architect Agent (Plan 类型)
  │   视角："这个设计与现有架构一致吗？有没有更简单的方案？"
  │   加载：01-core §1.6(IPD)、docs/architecture/、ADR 文件
  │   产出：design-review.md
  │
  ├── Coder Agent (general-purpose)
  │   视角："这段代码能正确工作吗？有没有边界条件遗漏？"
  │   加载：Spec 文件、01-core §1.1(P1-P11)、相关源代码
  │   产出：代码 + 实现说明
  │
  ├── Test Agent (general-purpose)
  │   视角："Spec 的每个验收标准都有对应测试吗？边界条件覆盖了吗？"
  │   加载：Spec 文件（不看 Coder 的实现代码）
  │   产出：测试用例
  │
  ├── Security Agent (general-purpose)
  │   视角："这段代码有没有注入、越权、数据泄露的可能？"
  │   加载：04-security-governance、05-tool-reference §4(A01-A09)
  │   产出：security-review.md
  │
  └── Gate Checker Agent (只读，独立上下文)
      视角："以上所有 Agent 的结论可信吗？证据链完整吗？"
      加载：01-core §1.7(Gate)、所有上游产出物
      产出：gate-report-{date}.md（Pass/Fail）
```

### 2.3 会诊模式执行规则

| 规则 | 说明 |
|------|------|
| **独立上下文** | 每个 Agent 加载不同视角的规范章节和文件，不共享完整对话上下文 |
| **独立判断** | Agent 之间不看彼此的中间结论，只做独立判断（Gate Checker 除外） |
| **文件传递** | Agent 通过文件（不是上下文）传递产出物 |
| **Gate 汇总** | 所有 Agent 产出必须有明确的 Pass/Fail 标准，Gate Checker 做最终裁定 |
| **动态组建** | 不是固定 5 个全跑。小任务 2-3 个 Agent，大任务 5+ 个 |

### 2.4 何时启用会诊模式

| 任务复杂度 | Agent 数量 | 启用角色 | 示例 |
|-----------|-----------|---------|------|
| **简单**（≤50 行，单文件） | 1 | 单 Agent 自行完成 | 修复 typo、添加日志 |
| **中等**（≤500 行，2-3 文件） | 2-3 | Coder + Gate Checker (+ Security 可选) | 新增 API 端点、修改数据结构 |
| **复杂**（>500 行，多模块） | 4-5 | Architect + Coder + Test + Gate Checker | 新增认证模块、重构核心流程 |
| **关键**（安全/资金/核心） | 5+ | Architect + Coder + Test + Security + Gate Checker | 支付流程、权限系统、数据库迁移 |

### 2.5 会诊模式 vs 单 Agent 的质量对比

单 Agent 执行一个中等复杂度任务时的问题：
- 又要理解需求又要设计又要编码又要审查 → 每个角度都浅
- 自己审查自己的代码 → 确认偏见，看不到自己假设的盲区
- 8000 行规范全塞进一个窗口 → 注意力稀释，关键规则被淹没

会诊模式下：
- 4 个 Agent × 各自深度思考 = 4 倍理解深度
- 独立上下文 = 4 份独立的规范注意力（每个 Agent 只关注与自己视角相关的规则）
- Gate Checker 独立验证 = 打破确认偏见

### 2.6 递归会诊模型（分形结构）

> **核心认知**：每个角色不是一个 Agent，而是一个可伸缩的团队。团队内部也使用会诊模式。这是分形/递归结构。

#### 2.6.1 为什么角色必须是团队

大型项目中，"架构视角"不是单个 Agent 能覆盖的：
- 系统架构师关注模块边界和依赖方向
- 数据架构师关注 schema 演进和数据一致性
- 安全架构师关注攻击面和威胁模型
- 性能架构师关注瓶颈和扩展性

如果把这些全部塞给一个 Architect Agent，上下文窗口会过载，每个角度都只能浅尝辄止。

**解决方案**：每个角色内部也是会诊结构。

#### 2.6.2 递归层级定义

```
Level 0: 角色级会诊（多角色对同一产出物的多视角会诊）
  ├── Architect 视角
  │   └── Level 1 会诊：系统架构师 + 数据架构师 + 安全架构师
  │       各自独立分析 → 汇总 → 本层 Gate 验证
  │
  ├── Coder 视角
  │   └── Level 1 会诊：模块A Coder + 模块B Coder + 模块C Coder
  │       各自独立开发 → 合并 → 本层 Gate 验证
  │
  ├── Test 视角
  │   └── Level 1 会诊：单元测试 + 集成测试 + E2E 测试 + 性能测试
  │       各自独立编写 → 汇总 → 本层 Gate 验证
  │
  └── Security 视角
      └── Level 1 会诊：SAST + 注入检测 + 权限审查 + 依赖审计
          各自独立检查 → 汇总 → 本层 Gate 验证
```

**同一个会诊模式，在不同粒度上重复**。L1 的每个专家如果负责的模块足够大，可以继续向下递归到 L2。

#### 2.6.3 递归深度决策矩阵

| 项目规模 | 建议深度 | 说明 | 示例 |
|---------|---------|------|------|
| **微型**（< 500 行） | L0 仅 | 单 Agent 直接执行 | 小脚本、配置修改 |
| **小型**（< 2000 行） | L0 | 角色级会诊，每个角色单 Agent | 新功能模块 |
| **中型**（< 10000 行） | L1 | 角色内部专家会诊 | 重构核心模块 |
| **大型**（> 10000 行） | L2 | 专家级任务再会诊 | 新子系统、微服务迁移 |
| **超大型**（> 50000 行） | L3 | 递归到具体函数级会诊 | 核心基础设施重构 |

#### 2.6.4 递归会诊执行规则

| 规则 | 说明 |
|------|------|
| **每层独立验证** | 子团队的 Gate Checker 验证本层产出，不依赖顶层验证 |
| **自底向上汇总** | L2 通过后汇总到 L1，L1 通过后汇总到 L0 |
| **逐层回退** | 任何一层 Gate 不通过，回退到该层重新会诊 |
| **共享上下文隔离** | 同层专家不共享对话上下文，只共享文件产出物 |
| **深度可控** | Director Agent 根据任务规模决定递归深度 |

---

### 2.7 规范落地执行架构

> **核心问题**：规范是给 AI 读的，但 AI 不会自动执行规范。需要三层架构确保规范被遵守。

#### 2.7.1 三层执行架构

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: Director Agent（活编译器）                    │
│                                                     │
│  - 运行时读取规范 Markdown，不依赖预编译配置           │
│  - 判断任务复杂度 → 决定递归深度                      │
│  - 动态组建会诊团队（角色数量 + 每层专家数量）          │
│  - 为每个 Agent 精确加载对应的规范章节                 │
│  - 触发 Gate Checker，收集证据链                      │
│  - 汇总报告 → 决定是否推进到下一阶段                   │
│                                                     │
│  风险：Director 本身可能误解规范 → 需要 Layer 3 兜底  │
└──────────────────────┬──────────────────────────────┘
                       │ 动态分发
┌──────────────────────▼──────────────────────────────┐
│ Layer 2: Agent 角色定义（上下文隔离）                  │
│                                                     │
│  - .omc/agents/ 目录下每个角色的独立 prompt            │
│  - 每个 Agent 只加载与自己视角相关的规范章节            │
│  - 避免 8000 行规范全塞一个窗口 → 注意力精准投放       │
│  - 每个 Agent 有明确的输入/输出/验证标准               │
│                                                     │
│  示例：Coder Agent 加载 P1-P11 + P13 + P17            │
│        不加载：P16(资源清理)/P20(速率保护) 等运维规则   │
└──────────────────────┬──────────────────────────────┘
                       │ 产出文件
┌──────────────────────▼──────────────────────────────┐
│ Layer 3: Hard Enforcement（硬兜底）                    │
│                                                     │
│  - pre-commit hooks: P5 密钥/P13 错误处理/P22 IP 暴露 │
│  - CI gates: P3 TDD/P7 Spec/P8 批量/P15 并发安全      │
│  - checker scripts: 规范中可自动化的检查项             │
│  - AI 可能遗忘/幻觉，用代码兜底                        │
│                                                     │
│  原则：Layer 1/2 是指导生成过程，Layer 3 是事后兜底    │
└─────────────────────────────────────────────────────┘
```

#### 2.7.2 三层关系

| 关系 | 说明 |
|------|------|
| L1 → L2 | Director 根据规范选择哪些角色、加载哪些章节 |
| L2 → L3 | Agent 产出的代码自动经过 hooks/CI 检查 |
| L3 → L1 | Layer 3 的失败结果反馈给 Director，触发修复或升级 |
| 互补 | L1+L2 覆盖"生成过程的正确性"，L3 覆盖"生成结果的正确性" |

#### 2.7.3 Director Agent 的 Prompt 核心结构

```
你是 AI Coding 规范的 Director Agent。
你的职责是：

1. 接收任务描述，评估复杂度（参考 03-multi-agent §2.6.3 递归深度矩阵）
2. 根据复杂度，动态组建会诊团队（角色 + 每层专家数量）
3. 为每个 Agent 生成角色 prompt，包含：
   - 该角色需要加载的规范章节路径
   - 该角色的视角和问题框架
   - 该角色的输出格式要求
4. 启动 TeamCreate + Agent 分配任务
5. 收集各层 Gate Checker 的 Pass/Fail 报告
6. 如果所有 Gate Pass → 推进到下一阶段
7. 如果有 Gate Fail → 回退到对应层级重新会诊

关键规则：
- 你不得自己写代码，只负责编排
- 你不得跳过任何 Gate
- 每个 Agent 必须独立上下文，不得共享对话
- 所有判断必须有可验证证据（01-core §P11）
```

#### 2.7.4 复用现有 Agent + 动态映射

> **核心原则**：不自建 Agent，复用各工具已有的经过实战验证的专业 Agent。不同工具的 Agent 名称和能力不同，Director 必须在运行时动态映射。

**规范角色层（工具无关）**：这些角色是规范定义的抽象概念，不绑定任何具体工具：

| 规范角色 | 覆盖 IPD Phase | 职责 |
|---------|--------------|------|
| `researcher` | Phase 0 | 市场洞察、竞品分析、五看三定、伪需求检测 |
| `analyst` | Phase 1 | 概念定义、需求拆解、Kano/QFD、JTBD |
| `architect` | Phase 2 | 技术规划、DFX、ATA、WBS、风险矩阵 |
| `planner` | P23 | 方案设计 → Spec 生成 |
| `coder` | Phase 3 | 代码实现、调试、重构 |
| `reviewer` | Phase 3 | 代码审查、质量评分、幻觉检测 |
| `tester` | Phase 3/4 | 测试策略、E2E、flaky 测试 |
| `security` | Phase 3/4 | 安全漏洞检测、密钥扫描、注入防护 |
| `db-migration` | Phase 3 | 数据库迁移审查、数据一致性、回滚策略 |
| `performance` | Phase 3/4 | 性能基线审查、预算、N+1 检测、压力测试 |
| `designer` | Phase 1/3 | UI/UX 交互审查、可用性、可访问性 |
| `ops` | Phase 4/5 | 部署与可观测性审查、健康检查、SLO |
| `writer` | Phase 4/5 | 文档质量审查、API 文档、CHANGELOG |
| `gate-checker` | 全阶段 | 证据链验证、Pass/Fail 判定 |
| `explorer` | 全阶段 | 只读代码搜索、分析 |
| `director` | 全阶段 | 会诊编排、Gate 调度、报告汇总 |

**工具实现层（工具特定）**：Director 必须维护工具到角色的映射表，按工具动态切换：

```yaml
# .normalized/agent-registry.yaml
# 不同工具的 Agent 映射到规范角色
# Director 根据当前使用的工具查找对应的 Agent 类型

roles:
  architect:
    claude-code: "architect" (OMC)
    qwencli: "architect-agent" (示例)
    # 其他工具继续添加

  coder:
    claude-code: "general-purpose" (CC 内置)
    qwencli: "code-agent" (示例)

  reviewer:
    claude-code: "code-reviewer" (OMC)
    qwencli: "review-agent" (示例)

  gate-checker:
    claude-code: "verifier" (OMC)
    qwencli: "verify-agent" (示例)

  # ... 其他角色
```

**动态映射流程：**

```
Director 检测到当前工具 = "claude-code"
  → 查找 .normalized/agent-registry.yaml
  → architect → "architect" (OMC subagent_type)
  → coder → "general-purpose" (CC 内置 subagent_type)
  → 使用 Agent(subagent_type="architect", ...)

Director 检测到当前工具 = "qwencli"
  → 查找 .normalized/agent-registry.yaml
  → architect → "architect-agent" (qwencli 的 Agent 名)
  → 使用 qwencli 对应的 API 调用方式
```

#### 2.7.5 规范清洗（Spec Normalization）

> **核心问题**：规范原文是治理文档，不适合直接注入 Agent 上下文。清洗后规范是**工具无关的指令集**，与规范原文一起发布。

**为什么需要清洗：**

| 问题 | 原文特征 | 清洗后 |
|------|---------|-------|
| **噪声** | 8000 行规范中单个 Agent 只需 10-20% | 只保留与该角色相关的章节 |
| **语气** | "不得/禁止/必须"（治理语言） | "你应该/请避免"（指令语言） |
| **交叉引用** | "见 §X.Y"（死链接） | 直接展开引用内容 |
| **语言无关** | 表格中的 Go 示例 + 通用原则 | 只保留该 Agent 使用的语言示例 |
| **冗余** | 同一原则在多处重复 | 去重后保留最精确的一条 |

**清洗流程：**

```
规范原文 (ai-coding-v5.4/*.md)
    │
    ▼
Director Agent 执行清洗:
  1. 提取：根据角色定位，提取相关章节
  2. 翻译：治理语言 → 指令语言
  3. 展开：交叉引用 → 实际内容
  4. 精简：去重 + 只保留相关语言示例
  5. 压缩：去除空行、合并短句、紧凑排版
  6. 逐条确认：每条规则对照原文验证，确保语义不变、来源可追溯
    │
    ▼
清洗后规范 (ai-coding-v5.4/.normalized/{role}-rules.md)
    │ 与规范原文一起发布，版本同步
    ▼
注入 Agent prompt: "你必须遵循以下规则：{cleaned_spec}"
```

**清洗后规范是规范集的一部分，一起发布。** 原因：
- 规范原文 = 人类可读的治理标准
- 清洗后规范 = Agent 可读的执行指令
- 两者是同一条规范的不同表现形式，共享版本号
- 规范更新时，对应的清洗版必须同步更新

**清洗后规范的存储位置**：`ai-coding-v5.4/.normalized/{role}-rules.md`

| 文件 | 规范角色 | 来源章节 |
|------|---------|---------|
| `.normalized/researcher-rules.md` | researcher | §1.6.1(Phase0)、五看三定、BLM、VOC |
| `.normalized/analyst-rules.md` | analyst | §1.6.2(Phase1)、$APPEALS、Kano、QFD、JTBD |
| `.normalized/architect-rules.md` | architect | §1.6.3(Phase2)、DFX、ATA、WBS、风险矩阵 |
| `.normalized/planner-rules.md` | planner | §1.3(P23)、§4(Spec格式)、Quality Gate |
| `.normalized/coder-rules.md` | coder | P1-P11(核心)、P12-P22(工程)、TDD、Self-Correction |
| `.normalized/reviewer-rules.md` | reviewer | P4(人工审查)、P11(证据链)、A01-A09 审查清单 |
| `.normalized/security-rules.md` | security | P5(密钥)、P14(租户)、P19(认证)、安全治理 |
| `.normalized/tester-rules.md` | tester | P3(TDD)、测试深度评分、AC 覆盖规则 |
| `.normalized/gate-checker-rules.md` | gate-checker | §1.7(Gate)、P11(证据链)、独立验证原则 |
| `.normalized/explorer-rules.md` | explorer | 只读约束、搜索策略 |
| `.normalized/db-migration-rules.md` | db-migration | 08-database-migration、TDD迁移、Expand-Contract |
| `.normalized/performance-rules.md` | performance | 11-performance-baseline、性能预算、N+1检测 |
| `.normalized/designer-rules.md` | designer | 交互审查、A11y、可用性、响应式 |
| `.normalized/ops-rules.md` | ops | 13-deploy-rollback、07-observability、SLO |
| `.normalized/writer-rules.md` | writer | 文档质量、API文档、CHANGELOG、文档即测试 |
| `.normalized/director-rules.md` | director | §2.1-§2.7(会诊编排)、Agent映射、Gate调度 |

**清洗原则：**

| 原则 | 说明 |
|------|------|
| **工具无关** | 清洗后规范不提及任何具体工具名，只定义角色行为标准 |
| **单向翻译** | 原文 → 清洗版，不可反向推导 |
| **可追溯** | 每段清洗后内容标注来源（`来源: 01-core §1.1 P1`） |
| **版本同步** | 规范原文更新后，对应的清洗版必须更新（共享版本号） |
| **可审计** | 清洗后的规范可由人类审查，确认翻译正确 |
| **不改变语义** | 清洗只改变格式和语气，不改变规则含义 |
| **随规范发布** | 清洗后规范是规范集的一部分，不是运行时临时文件 |
| **紧凑格式** | 去除冗余空行和修饰，合并短句，控制文件大小 |
| **逐条确认** | 每条规则必须对照原文逐条验证：语义不变、来源可追溯、无遗漏 |

**清洗后格式示例（coder-rules.md）：**

```markdown
# Coder Agent 规范

> 版本: v5.5 | 来源: 01-core-specification.md

## 核心底线（不可违反）
- 必须商业驱动：代码必须对应 Spec 中的 business_goal 字段 [来源: 01-core P1]
- 必须 TDD 先行：测试先于实现，先失败再写实现 [来源: 01-core P3]
- 必须 Spec 驱动：编码前读取对应 Spec 文件 [来源: 01-core P7]
- 最小批量：单个函数 ≤50 行，单个文件 ≤200 行 [来源: 01-core P8]
- 密钥不入代码：使用环境变量或密钥管理 [来源: 01-core P5]

## 工程实践
- 错误处理：所有错误必须处理或返回，禁止空 catch/nolint [来源: 01-core P13]
- 输入校验：所有外部输入必须类型校验 + 边界检查 [来源: 01-core P17]
- JSON 安全：使用 json.Marshal 序列化，禁止字符串拼接 [来源: 01-core P18]
...
```

#### 2.7.6 Agent 注入模板

Director 分发任务时，为每个 Agent 构造 prompt：

```
你是 {role_name}。

## 任务
{具体任务描述，来自 Spec}

## 你必须遵循的规范
{加载 ai-coding-v5.4/.normalized/{role}-rules.md 内容}

## 你的视角
你只关注 {X} 方面的问题。你不关注 {Y} 方面的问题（交给其他角色）。

## 你的输入
{input_files 列表}

## 你的输出
{output_file}，必须满足：{验证标准}

## 关键约束
- 不得跳过 Self-Correction Loop（最多 3 轮）
- 所有判断必须有可验证证据
- 输出写入文件，不依赖口头描述
```

**Director 组装流程：**

```
1. 读取 .normalized/agent-registry.yaml → 找到当前工具对应的 Agent 类型
2. 读取 .normalized/{role}-rules.md → 获取该角色的规范指令
3. 读取 Spec 文件 → 获取任务描述、输入、输出
4. 组装 prompt → 调用 Agent(type=映射后的Agent, prompt=组装结果)
5. 收集产出 → 交给 Gate Checker 验证
```

---

## 第 3 章：Agent SDK

### 3.1 Agent Teams 模式

```bash
# 创建团队
TeamCreate(team_name="feature-team", description="Implement feature set")

# 创建任务
TaskCreate(subject="Implement F001", description="Spec at specs/F001.md")

# 设置依赖
TaskUpdate(taskId="2", addBlockedBy=["1"])

# 启动成员
Agent(name="worker-frontend", subagent_type="general-purpose", team_name="feature-team")
Agent(name="worker-backend", subagent_type="general-purpose", team_name="feature-team")
```

### 3.2 通信机制

- Team Lead 通过 SendMessage 向 Worker 分配任务
- Worker 通过 TaskUpdate 更新任务状态
- Worker 完成后自动发送消息给 Team Lead
- Team Lead 通过 TaskList 查看整体进度

---

## 第 4 章：多平台协同

### 4.1 平台支持

| 平台 | 能力 |
|------|------|
| CLI | 完整工具集，会话级运行 |
| Desktop App | 定时任务、Remote Control |
| Cloud | 云端定时任务，关机也可运行 |

### 4.2 通知与监控

- 阻塞事件：通过 Slack/Telegram/webhook 发送告警
- 进度通知：Remote Control 查看仪表板
- 完成报告：自动生成并发送到 Channel

---

## 第 5 章：与配套文档的关系

| 文档 | 关系 |
|------|------|
| 01 核心规范 | 定义了分工原则，本文档定义多 Agent 协调实现 |
| 02 Auto-Coding 实践 | 定义了 Supervisor-Worker 模式，本文档定义具体 Agent 类型 |
| 04 安全与治理 | 定义了 Sub-Agent 安全约束，本文档引用 |
| 05 工具参考 | 定义了 CLI 命令，本文档定义使用模式 |

---

## 第 6 章：冲突检测与解决

### 6.1 冲突定义

当多个 Agent 同时修改同一文件或同一代码区域时，产生写冲突。冲突分为三级：

| 级别 | 定义 | 处理方式 |
|------|------|---------|
| L1 行级冲突 | 两个 Agent 修改不同行 | 自动合并 |
| L2 区域级冲突 | 两个 Agent 修改相邻行（±5 行内） | 自动检测 + 策略合并 |
| L3 语义级冲突 | 两个 Agent 修改同一函数/类/逻辑块 | 需要协调解决 |

### 6.2 冲突检测

写前检测：Agent 编辑文件 F 前读取其当前 Git SHA，与启动时记录的 SHA 对比。若不一致，说明其他 Agent 已修改该文件，触发三方 diff（base / current / agent_edits）检测重叠区域并按级别分类。

### 6.3 冲突解决策略

| 冲突级别 | 策略 | 执行方 |
|----------|------|--------|
| L1 | 自动合并（行级叠加） | 系统 |
| L2 | 区域排序 + 语义分析合并 | 协调 Agent |
| L3 | 锁定文件 → 排队串行化 → 按依赖顺序合并 | 协调 Agent |

L2 流程：识别冲突边界 → 按依赖图确定优先级 → 高优先变更先合并 → 低优先变更 rebase → 失败则升级为 L3。

L3 流程：冻结双方写权限 → 提取变更意图（Task/Spec）→ 判断兼容性（兼容则按依赖序合并，不兼容则回退低优先级并重新分配）→ 生成冲突报告到 `.omc/logs/conflict-{timestamp}.md`。

### 6.4 冲突预防

- **工作空间隔离**：优先让不同 Agent 操作不同文件集
- **任务依赖驱动**：有依赖关系的任务串行执行（见第 6 章）
- **文件粒度分配**：同一逻辑单元（如同一函数）不分配给多个 Agent

---

## 第 7 章：依赖图自动构建

### 7.1 依赖图数据结构

依赖图由节点（任务）和边（依赖关系）组成：

```json
{
  "nodes": [{"id": "T001", "type": "task", "spec": "specs/F001.md", "files_touched": ["src/auth.py", "tests/test_auth.py"], "status": "pending"}],
  "edges": [{"from": "T001", "to": "T002", "type": "file_dependency", "reason": "T002 imports module defined in T001"}]
}
```

### 7.2 自动依赖推断

| 维度 | 检测方法 | 示例 |
|------|---------|------|
| 文件级依赖 | import/require 语句分析 | B import A → B 依赖 A |
| 函数级依赖 | 函数调用图 | B calls A.foo() → B 依赖 A |
| Spec 级依赖 | Spec 文件中的依赖声明 | F002.md references F001 |
| 数据流依赖 | 数据库 schema 变更 | Migration A 必须在 Query B 之前 |
| 测试依赖 | 测试文件引用 | test_B tests module_A → test_B 依赖 A |

构建流程：读取所有 Spec 文件 → 解析 target_files / depends_on → 静态分析代码 import 构建模块依赖图 → 合并两类依赖 → 检测循环依赖（存在则报告并请求人工介入）→ 输出 DAG → 生成任务执行计划。

### 7.3 依赖图维护

通过 `TaskUpdate` 对依赖图进行操作：构建（`action="build"`）、查询（`action="query"`）、更新（任务完成后自动检查下游任务是否可解锁）。

### 7.4 循环依赖处理

检测到循环依赖时：标记链路中所有任务为 `[CYCLE-DETECTED]` → 报告循环路径 → 建议破环方案（移除最弱依赖边）→ 等待人工确认后继续。

---

## 第 8 章：合并冲突自动处理

### 8.1 处理策略分层

| 策略 | 适用场景 | 成功率 | 回退 |
|------|---------|--------|------|
| 自动三路合并 | 无重叠编辑 | ~95% | → 语义合并 |
| 语义合并 | 重叠但逻辑兼容 | ~70% | → 回退重排 |
| 回退重排 | 逻辑不兼容 | ~90% | → 上报人工 |
| 人工介入 | 以上全部失败 | 100% | — |

### 8.2 自动三路合并

使用 `git merge-tree <base> HEAD feature-branch-agent-a` 进行标准三路合并。成功则自动提交，有冲突则进入语义合并。

### 8.3 语义合并
三路合并冲突时协调 Agent 执行：解析冲突标记 → 读取双方 Spec 理解变更意图 → 判断兼容性（不同关注点可重组保留，不兼容则进入回退重排）→ 合并后运行测试套件验证。

### 8.4 回退重排
逻辑不兼容时：按依赖图确定优先级 → 保留高优先级变更 → `git checkout <base> -- <conflicted-files>` 回退低优先级变更 → 将其任务状态设为 `rebase_needed` 并通过 `addBlockedBy` 确保在高优先级任务完成后重新执行。

### 8.5 合并冲突报告格式

```markdown
# 合并冲突报告 - {timestamp}

## 冲突摘要
- 涉及文件：src/auth.py, src/models/user.py
- 冲突 Agent：worker-backend (T003), worker-frontend (T007)
- 冲突级别：L3 语义级

## 冲突详情
### src/auth.py:45-62
- Agent A (T003): 添加 JWT token 刷新逻辑
- Agent B (T007): 修改认证中间件签名

## 解决方案
- 策略：回退重排
- 优先级：T003 > T007（T007 依赖 T003 的模块）
- 操作：保留 T003，T007 标记为 rebase_needed

## 验证
- 合并后测试：PASS (42/42)
- T007 重排状态：等待 T003 完成
```

---

## 第 9 章：文件锁定机制

### 9.1 锁定协议

采用乐观锁为主、悲观锁为辅的策略：

| 锁类型 | 场景 | 行为 |
|--------|------|------|
| 乐观读锁 | 大多数编辑场景 | 允许并发读取，写前检测冲突 |
| 悲观写锁 | L3 冲突场景、关键文件 | 独占访问，其他 Agent 排队 |

### 9.2 锁状态管理

锁状态存储在 `.omc/locks/` 目录下，每个条目包含：file、locked_by、task_id、lock_type、acquired_at、expires_at（默认 30 分钟）、lock_level。等待队列记录请求文件、请求者、task_id 和时间戳。

### 9.3 锁定粒度

| 粒度级别 | 锁定范围 | 适用场景 |
|----------|---------|---------|
| `file` | 整个文件 | 重构、大规模变更 |
| `region` | 文件的逻辑区域（函数/类） | 同一文件不同区域的并行编辑 |
| `line-range` | 指定行范围 | 精确控制的最小锁定 |

### 9.4 锁定生命周期

请求锁定（`TaskUpdate action="request_lock"`）→ 写入锁文件并设置 expires_at → 持锁编辑（每 5 分钟心跳续期）→ 释放锁定（`action="release_lock"`，从锁文件移除并通知队列下一个等待者）。锁超时（expires_at 到达且无心跳）时自动释放。

### 9.5 死锁预防

有序请求（按文件路径字典序）→ 超时释放（默认 30 分钟）→ 心跳续期（每 5 分钟）→ 无嵌套锁（同时只持有一个写锁）→ 定期扫描等待图检测循环。

---

## 第 10 章：并行度控制

###10.1 并行度决策因素

| 因素 | 权重 | 说明 |
|------|------|------|
| 任务独立性 | 高 | DAG 中无依赖的节点可并行 |
| 资源约束 | 高 | API 配额、内存、CPU 限制 |
| 冲突概率 | 中 | 同文件操作数越多，冲突概率越高 |
| 任务类型 | 中 | 只读任务（Explore）可高度并行 |
| 代码库规模 | 低 | 大项目适合更多并行 |

###10.2 并行度计算

基于 DAG 最大可并行集、资源上限（API 速率 / 最大 Agent 数）、冲突因子衰减（同文件任务数 * CONFLICT_COST）计算最小值，绝对上限默认为 8。

###10.3 动态并行度调整

保守启动 `min(ready_tasks, 4)`，运行时调整：连续 2 轮无冲突则 +1，检测到冲突则 -1，API 限流则 -2（范围 [1, 8]）。差异化：Explore 不受限，general-purpose 受限制，Plan 最多 2 个并行。

###10.4 并行执行编排

Team Lead 根据依赖图按批次启动：无依赖任务全并行 → 通过 TaskList 检测完成 → 解锁依赖前序任务的下一批。

---

## 第 11 章：Agent 协调协议

###11.1 状态报告协议

每个 Agent 定期报告状态（agent_name、task_id、status、progress、blockers、estimated_completion）。状态机：`pending → in_progress → [self-correction (max 3 rounds)] → completed | blocked → unblocked → in_progress | failed → [escalation] → human-review`。

###11.2 工作交接协议

交接流程：Agent A 完成当前阶段 → 生成交接报告（已完成内容 / Git SHA / 遗留问题 / 下一步 / 关键文件列表）→ 更新状态为 `handoff_ready` → Team Lead 通知 Agent B → Agent B 读取报告后继续。

**交接报告模板：**

```markdown
# 交接报告 - T003

## 交接方：worker-backend → 接收方：worker-backend-test

## 已完成
- [x] 实现 JWT token 生成逻辑 (src/auth.py:120-185)
- [x] 添加 token 验证中间件 (src/middleware/auth.py)
- [x] 编写单元测试 12 个 (tests/test_auth.py)

## 当前状态
- 分支：feature/auth-backend
- 最后提交：a1b2c3d - "add token validation"
- 测试状态：12/12 PASS

## 遗留问题
- 需要集成 Redis 黑名单（依赖 T005 的 Redis 配置）
- refresh_token 存储方案待确认

## 下一步
1. 等待 T005 完成后集成 Redis 黑名单
2. 补充集成测试
3. 性能测试（token 验证 < 5ms）
```

###11.3 故障恢复协议

| 故障类型 | 检测方式 | 恢复策略 |
|----------|---------|---------|
| Agent 崩溃 | 心跳超时（5 分钟无活动） | 重新分配任务给新 Agent |
| 自修循环耗尽 | 3 轮自修后仍失败 | 标记 `[SELF-CORRECTION-EXHAUSTED]`，上报人工 |
| 依赖不可满足 | 依赖任务失败 | 阻塞链中所有下游任务标记 `blocked_upstream_failure` |
| 资源耗尽 | API 配额用尽 | 暂停非关键 Agent，保留核心任务 |
| 合并不可解决 | 多次合并失败 | 上报人工审查 |

恢复流程：检测故障 → 分类 → 执行恢复（崩溃则保留工作区并创建新 Agent；自修耗尽则收集日志并标记 `needs_human_review`；依赖断裂则标记下游并尝试替代路径）→ 记录事件到 `.omc/logs/failure-{timestamp}.md`。

###11.4 心跳与保活

心跳间隔 5 分钟（任何 TaskUpdate / SendMessage 即视为心跳）。超时阈值 15 分钟：第一次超时发探测 → 第二次标记 suspect → 第三次标记 failed 并触发恢复流程。

---

## 第 12 章：Spec 驱动的 Agent 分配

###12.1 Spec 文件规范

每个任务必须有对应的 Spec 文件，存放在 `specs/` 目录，包含：元信息（ID、Title、Priority、Depends On、Agent Type）、目标、输入、输出、验收标准、约束。

```markdown
# specs/F001-auth-module.md

## 元信息
- ID: F001
- Title: 用户认证模块
- Priority: P0
- Depends On: [F000]
- Agent Type: general-purpose

## 目标
实现 JWT 认证模块，包括 token 生成、验证、刷新。

## 输出
- src/auth.py - 认证核心逻辑
- src/middleware/auth.py - 认证中间件
- tests/test_auth.py - 单元测试

## 验收标准
1. token 生成 < 10ms
2. token 验证 < 5ms
3. AC 覆盖率 100%
4. 通过安全审查（04-security-governance.md）

## 约束
- 使用 PyJWT 库
- 密钥从环境变量读取（禁止硬编码）
```

###12.2 Agent 自动分配流程

Team Lead 扫描 specs/ → 解析每个 Spec 的元信息 → 查询依赖图（依赖满足则标记 ready，否则标记 blocked 并设置 blockedBy）→ 对 ready 的 Spec 按 Agent Type 分配 → 创建 Task 并关联 Spec 路径 → 持续监控（完成则解锁下游，失败则触发故障恢复）。

###12.3 Spec → Task 映射

一个 Spec 可映射多个 Task（实现、测试、审查），通过 `blockedBy` 表达 Task 间的执行顺序。

```json
{
  "spec_file": "specs/F001-auth-module.md",
  "tasks": [
    {"id": "T001", "subject": "实现 JWT token 生成", "files": ["src/auth.py"], "agent_type": "general-purpose", "status": "pending"},
    {"id": "T002", "subject": "编写认证单元测试", "files": ["tests/test_auth.py"], "agent_type": "general-purpose", "status": "pending", "blockedBy": ["T001"]},
    {"id": "T003", "subject": "安全审查 - 认证模块", "files": ["src/auth.py", "src/middleware/auth.py"], "agent_type": "Plan", "status": "pending", "blockedBy": ["T001", "T002"]}
  ]
}
```

### 12.4 Agent 任务领取协议

**Pull 模式**：空闲 Agent 查询 TaskList → 筛选 `status=="pending"` 且未分配且无阻塞且类型匹配的任务 → `TaskUpdate(taskId, owner, status="in_progress")` 认领。

**Push 模式**：Team Lead 根据依赖图和 Agent 空闲状态主动分配 → `TaskUpdate(taskId, owner)` → `SendMessage` 通知。

### 12.5 Spec 版本与追溯

Spec 文件纳入 Git 版本控制，包含变更记录表。Agent 生成代码时在注释中记录 `# Spec: F001 v1.1`。变更 Spec 后相关任务需要重新评估。

---

## 第 13 章：上下文共享与传播

###13.1 上下文传播机制

多 Agent 场景下每个 Agent 有独立上下文窗口。上游 Agent 完成后写入 `.omc/context/{task_id}.md`（包含变更文件列表、新增 API 签名、关键设计决策、已知限制、Git commit SHA），下游 Agent 启动前自动读取并注入上下文。

###13.2 上下文摘要格式

```markdown
# 上下文摘要 - T001

## 基本信息
- Task: T001 | Agent: worker-auth | Completed: 2026-04-18T11:30:00Z
- Branch: feature/auth-backend | Commit: a1b2c3d

## 变更文件
| 文件 | 行数 | 说明 |
|------|------|------|
| src/auth.py | 185 | JWT 认证核心逻辑 |
| src/middleware/auth.py | 62 | 认证中间件 |
| tests/test_auth.py | 245 | 单元测试 12 个 |

## 新增 API
```python
def generate_token(user_id: str, role: str) -> str: ...
def verify_token(token: str) -> dict: ...
def refresh_token(old_token: str) -> str: ...
```

## 设计决策
- 使用 HS256 算法（项目规模不需要 RSA）
- token 有效期 15 分钟，refresh_token 7 天

## 已知限制
- 不支持多租户隔离
- token 撤销后黑名单最长 15 分钟生效
```

###13.3 上下文传播规则

| 规则 | 说明 |
|------|------|
| **下游必读** | 下游 Agent 启动前必须读取所有上游依赖的上下文摘要 |
| **变更通知** | 上游完成后自动通知下游等待的 Agent |
| **版本匹配** | 下游使用上游提交的 commit SHA 作为基准 |
| **过期清理** | 上下文摘要保留 30 天 |

---

## 第 14 章：多 Agent 测试协调

###14.1 测试并行策略

测试按类型分区并行执行：单元测试（按模块分区）、集成测试（按服务分区）、E2E 测试（按场景分区）、安全测试（SAST + 渗透）。协调器汇总所有结果生成测试报告。

###14.2 测试数据隔离

| 测试类型 | 数据隔离方式 |
|---------|-------------|
| 单元测试 | Mock 所有外部依赖，无需隔离 |
| 集成测试 | 独立测试数据库（每个 Agent 用不同 schema） |
| E2E 测试 | 容器化测试环境，测试后销毁 |
| 性能测试 | 独占环境，避免与其他测试互相干扰 |

### 14.3 测试结果汇总

协调器汇总各 Agent 测试结果到 `.omc/test-results/aggregate.yaml`，格式包含各 Agent 各类型的 passed/failed/skipped 计数，有失败即整体失败。

**独立验证**：协调器不得仅依赖 Worker 自报的测试结果。对于关键路径测试（安全、核心业务逻辑），协调器必须独立重新运行至少 1 个代表性测试以验证 Worker 报告的真实性。此要求与 [02-auto-coding-practices.md](02-auto-coding-practices.md) Supervisor-Worker 模式的独立复测要求一致。

---

## 第 15 章：Agent 资源配额

###15.1 配额定义

| 资源类型 | 配额示例 | 超限行为 |
|---------|---------|---------|
| API 调用次数 | 50 次/任务 | 停止执行，上报 Team Lead |
| 上下文窗口使用 | 80% | 触发上下文压缩 |
| 文件写入数 | 10 个文件/任务 | 警告，超过 15 个阻断 |
| 执行时间 | 30 分钟/任务 | 超时终止 |
| 自修轮次 | 3 轮 | 超限转人工（见 01-core-specification.md） |

###15.2 配额配置

按 Agent 类型差异化配置（`.omc/agent-quota.yaml`）：Explore 只读（max_file_writes=0，15 分钟）、Plan 不写代码（max_file_writes=0，20 分钟）、general-purpose 标准配额（max_api_calls=50，max_file_writes=15，45 分钟）。

---

## 第 16 章：Agent 生命周期管理

### 16.1 生命周期状态

`created → warming → idle → in_progress → [completed | failed | cancelled] → handoff → in_progress (next agent)`

### 16.2 生命周期事件

| 事件 | 触发动作 |
|------|---------|
| Agent 创建 | 加载团队配置、权限策略、上下文模板 |
| Agent 空闲 | 等待 TaskList 分配、超时 15 分钟自动休眠 |
| Agent 完成 | 生成总结、释放资源、通知 Team Lead |
| Agent 失败 | 收集日志、标记任务、触发恢复协议（第 10 章） |
| Agent 取消 | 保留 Git 工作区、释放锁、记录取消原因 |

### 16.3 团队清理

所有 Agent 完成任务后，Team Lead 执行 `TeamDelete` 清理团队目录和任务列表，并发送 shutdown 消息关闭所有 Worker。

---

## 附录：与其他文档的交叉引用

| 交叉引用 | 关联内容 |
|---------|---------|
| [01-core-specification.md](01-core-specification.md) | 分工原则、P8 最小批量、自修循环限制 |
| [02-auto-coding-practices.md](02-auto-coding-practices.md) | Supervisor-Worker 模式、自主编码模式 |
| [04-security-governance.md](04-security-governance.md) | Sub-Agent 安全约束、权限模型 |
| [05-tool-reference.md](05-tool-reference.md) | CLI 命令参考、TeamCreate/TaskCreate 等 |
| [06-cicd-pipeline.md](06-cicd-pipeline.md) | 多 Agent 生成的代码通过同一 Pipeline |
| [10-dependency-management.md](10-dependency-management.md) | 多 Agent 引入依赖的审批协调 |
