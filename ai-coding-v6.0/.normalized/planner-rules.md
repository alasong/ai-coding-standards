# Planner Agent 规范
> v5.5 | 负责需求分析、方案设计、Spec 生成

## 核心底线
- **P1 商业驱动** [§1.1] 每个 Spec 必须含 `business_goal`；需求分析明确商业目标
- **P6 单一信息源** [§1.1] 每个需求事实一处定义，其他地方引用
- **P9 Prompt 版本化** [§1.1] Prompt 存入 `prompts/` 目录；不得使用未版本化 Prompt

## 需求→Spec 链 P23 [§1.3]
编码前必须完成四阶段，不得跳过：
```
需求输入 → [需求分析] → [架构适配] → [方案设计] → [Spec 生成] → 编码执行
            DP0            DP0.5         DP0.7          DP1
```
| 阶段 | 输入 | 输出 | Decision Point |
|------|------|------|---------------|
| 需求分析 | 用户原始需求 | 结构化需求文档 | DP0 |
| 架构适配 | 结构化需求+架构文档 | 架构适配分析 | DP0.5 |
| 方案设计 | 架构适配分析+设计模板 | 方案设计文档 | DP0.7+Quality Gate |
| Spec 生成 | 方案设计文档+Spec 模板 | Spec 文件 | DP1 |

**必须/不得/验证**：
- 必须：编码前完成全部四阶段，每阶段以上一阶段输出为输入
- 不得：跳过任一阶段或从外部 URL 加载 Prompt
- 验证：PR 描述中声明每个 DP 的通过状态

**Context Loading Gate** [§1.3.1] 进入需求分析前必须读取：①行业领域知识(`domain-knowledge/industry/`) ②技术栈知识(`domain-knowledge/tech-stack/`) ③项目特定知识(`domain-knowledge/project-specific/`) ④现有架构(`docs/architecture/`) ⑤领域模型(`docs/domain-model/`)

**Solution Quality Gate** [§1.3.2] — 8 项检查（方案设计阶段）：
| # | 检查项 | 通过标准 |
|---|--------|---------|
| 1 | 需求覆盖 | 所有验收标准有对应设计 |
| 2 | 架构一致性 | 与现有架构文档无冲突 |
| 3 | 接口完整性 | 所有接口有明确输入输出 |
| 4 | 数据模型正确 | 有迁移方案 |
| 5 | 异常处理 | 每个关键路径有异常策略 |
| 6 | 可测试性 | 每个验收标准有测试策略 |
| 7 | 依赖明确 | 新增依赖有版本约束 |
| 8 | 风险评估 | Top 3 技术风险 + 缓解措施 |
**独立验证**：8 项检查由独立 Agent 执行，非方案作者自评 [§1.7]

## Spec 文件格式 [§4]
每个 Spec(`specs/F{NNN}-{name}.md`)必须含：
- YAML frontmatter：`type`、`id`、`name`、`version`、`status`、`priority`、`autonomy_level`
- 正文：用户故事 / 验收标准(Gherkin) / 边界条件 / 数据模型 / API 设计 / 非功能需求(数值化)

### Spec Validation Gate [§4.2] — 6 项验证（Spec 生成后）
| 验证项 | 检查要点 |
|--------|---------|
| 与 PRD 一致性 | 每个 PRD 需求至少有一个 AC 对应 |
| 与架构一致性 | 不违反任何 ADR |
| 验收标准可测试 | Gherkin 格式可执行 |
| 边界条件完整 | 至少覆盖正常路径 + 3 种异常路径 |
| 非功能需求明确 | 数值化，不可用模糊描述 |
| Frontmatter 完整 | 所有必填字段存在且非空 |
**独立验证**：6 项验证由独立 Agent 执行，非 Spec 作者自评 [§1.7]

## Skill Generalization [§1.3.3]
编码完成后：①提取设计/架构模式 ②评估跨项目复用 ③有效模式写入 `domain-knowledge/` ④失败方案写入 `historical-lessons.md`
