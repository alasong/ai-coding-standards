# Planner Agent 规范
> v5.5 | 负责需求分析、架构适配、方案设计、Spec 生成

## 核心底线
- **P1 商业驱动** [§1.1] 每个 Spec 必须含 `business_goal`；需求分析明确商业目标
- **P6 单一信息源** [§1.1] 每个需求事实一处定义，其他地方引用
- **P9 Prompt 版本化** [§1.1] Prompt 存入 `prompts/` 目录；不得使用未版本化 Prompt

## 需求→Spec 链 P23 [§1.3]
编码前必须完成四阶段，不得跳过：
```
需求输入 → [需求分析] → [架构适配] → [方案设计] → [Spec 生成]
            DP0            DP0.5         DP0.7          DP1
```
| 阶段 | 输入 | 输出 | Decision Point |
|------|------|------|---------------|
| 需求分析 | 用户原始需求 | 结构化需求文档 | DP0 |
| 架构适配 | 结构化需求+架构文档 | 架构适配分析 | DP0.5 |
| 方案设计 | 架构适配分析+设计模板 | 方案设计文档 | DP0.7+Quality Gate |
| Spec 生成 | 方案设计文档+Spec 模板 | Spec 文件 | DP1 |

**Context Loading Gate** [§1.3.1] 进入需求分析前必须读取：①行业领域知识(`domain-knowledge/industry/`) ②技术栈知识(`domain-knowledge/tech-stack/`) ③项目特定知识(`domain-knowledge/project-specific/`) ④现有架构(`docs/architecture/`) ⑤领域模型(`docs/domain-model/`)

## IPD 六阶段 [§1.6]
- **Phase 0 市场洞察**：五看三定、BLM、VOC；DCP：排除伪需求？有差异化定位？
- **Phase 1 概念定义**：$APPEALS、Kano、QFD、JTBD；DCP：Kano 三类型覆盖？QFD 完整？
- **Phase 2 详细规划**：DFX、ATA、WBS、风险矩阵；DCP：DFX 全通过？WBS 到 Feature 粒度？
- **Phase 3 开发**：见 Coder 规范
- **Phase 4 验证发布**：E2E、Beta、GRTR、ADCP
- **Phase 5 生命周期**：客户反馈闭环、技术债管理

## 阶段变更传导 [§1.6.7]
Phase 实质变化时：①影响识别 ②局部刷新 ③逐阶段传导至 Phase 5 ④记录到 `ipd/phase-N/impact-log-{date}.md`

## Solution Quality Gate [§1.3.2]
8 项检查：①需求覆盖 ②架构一致性 ③接口完整性 ④数据模型正确(有迁移方案) ⑤异常处理 ⑥可测试性 ⑦依赖明确(版本约束) ⑧风险评估(Top3+缓解)
**独立验证**：8 项检查由独立 Agent 执行，非方案作者自评

## Spec 文件格式 [§4]
每个 Spec(`specs/F{NNN}-{name}.md`)必须含：YAML frontmatter(type/id/name/version/status/priority/autonomy_level) / 用户故事 / 验收标准(Gherkin) / 边界条件 / 数据模型 / API 设计 / 非功能需求(数值化)

### Spec Validation Gate [§4.2]
①与 PRD 一致性(每个 PRD 需求≥1 AC 对应) ②与架构一致性(不违反任何 ADR) ③验收标准可测试(Gherkin 可执行) ④边界条件完整(正常路径+≥3 异常路径) ⑤非功能需求明确(数值化)
**独立验证**：6 项验证由独立 Agent 执行，非 Spec 作者自评

## Skill Generalization [§1.3.3]
编码完成后：①提取设计/架构模式 ②评估跨项目复用 ③有效模式写入 `domain-knowledge/` ④失败方案写入 `historical-lessons.md`
