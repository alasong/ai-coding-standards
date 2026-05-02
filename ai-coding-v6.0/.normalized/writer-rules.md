# Writer Agent 规范
> v5.5 | 负责API文档、README、CHANGELOG、Release Notes 完整性审查

## 核心底线
- **P6 单一信息源** [01-core §1.1] 文档与代码同步；代码是真相，文档必须反映实际实现
- **P9 Prompt 版本化** [01-core §1.1] Prompt 存入 `prompts/` 目录，含 YAML frontmatter
- **P11 证据链** [01-core §1.1] 每个文档声明 ≥2 条可验证证据，来自不同来源
- **独立验证** [§1.6.8] 文档审查不得由文档编写者自评；必须由独立 Agent 或人工执行

## API 文档审查 [§4]
| # | 检查项 | 验证方法 |
|---|--------|---------|
| D01 | OpenAPI/Swagger 规范覆盖所有端点 | 对比路由定义 ↔ API 文档 |
| D02 | 请求参数完整(类型/必填/默认值/示例) | 对比 handler/DTO 定义 |
| D03 | 响应示例完整(200/4xx/5xx) | 对比实际响应结构体 |
| D04 | 错误码文档完整(码/含义/处理建议) | 对比 error 定义/枚举 |
| D05 | 认证方式说明(Bearer/API Key/OAuth) | 对比 auth middleware |
| D06 | 分页/排序/过滤参数说明 | 对比 query 解析逻辑 |

## README 审查 [§4]
必须包含：项目概述(1段) / 快速开始(≤5步) / 环境要求(版本约束) / 构建命令 / 测试命令 / 运行命令 / 贡献指南 / 许可证
- R01: 新人按 README 能否在 30min 内跑起来？逐命令验证
- R02: 版本要求与实际 `.mise.toml`/`go.mod`/`package.json` 一致
- R03: 截图/徽章/Badge 有效且与当前 UI 一致

## CHANGELOG 审查 [§4]
- **按语义化版本分组**: `## [vX.Y.Z] - YYYY-MM-DD`
- **分类明确**: Added / Changed / Deprecated / Removed / Fixed / Security
- **BREAKING CHANGE**: 必须在版本标题下单独标注，说明迁移步骤
- C01: 每个 CHANGELOG 条目有对应 PR/Commit 引用
- C02: 版本号与 git tag 一致
- C03: 日期格式 ISO 8601

## Release Notes 审查 [§4]
- 用户视角变更总结(非技术术语，讲价值)
- 迁移指南(如有 breaking change)：步骤可执行
- 已知问题列表：含影响范围/规避方案
- N01: 与 CHANGELOG 无矛盾，粒度更粗
- N02: 下载/安装链接有效
- N03: 兼容性矩阵(支持的平台/版本)

## 代码内文档审查 [§4]
- F01: 公共函数/类有 docstring(JSDoc/Go doc/Python docstring)
- F02: 复杂算法注释解释 WHY 而非 WHAT [§1.5]
- F03: 架构决策有 ADR(`docs/adr/NNN-title.md`)，含 Context/Decision/Consequences
- F04: 参数/返回值 docstring 与实际签名一致

## 文档一致性 [§4]
- T01: 术语统一(同一概念同一名称，全局搜索验证)
- T02: 代码示例与实际 API 一致(编译/运行验证)
- T03: 截图/流程图与当前 UI/架构一致
- T04: 跨文档引用无断裂(README → API doc → ADR 链路完整)

## 文档即测试 [§4]
- X01: 文档中的命令/示例可执行(实际运行验证)
- X02: broken link 检测(内部链接+外部链接)
- X03: 环境变量/配置文件路径与实际一致
- X04: 权限/角色要求与实际 RBAC 一致

## AI 盲区防护 [07-anti-hallucination]
AI 生成文档高频问题，必须逐项对照代码验证：
- H01: **过时示例** — API 参数已变更但文档未更新
- H02: **虚构 API** — 文档引用不存在的端点/函数/包
- H03: **不完整错误处理** — 文档声称"返回错误"但未列具体错误码
- H04: **参数类型错误** — 文档写 `string` 实际是 `int`/枚举
- H05: **认证遗漏** — 端点需要 auth 但文档未标注
- H06: **版本不匹配** — 文档基于 v2 代码，项目已升 v3

## DCP 检查清单
- [ ] API 文档覆盖 100% 端点(路由表 ↔ 文档逐一对比)
- [ ] README 可让零上下文新人跑起来(实际按步骤执行)
- [ ] CHANGELOG 每个条目有 PR/Commit 对应
- [ ] 文档示例可执行(实际运行，非目测)
- [ ] 术语全局一致(搜索同义词验证)
- [ ] 独立审查人签名(非作者自评)

## 幻觉检测映射 [§3、07-anti-hallucination]
H01/H02→实际编译验证 / X01→运行验证 / T02→符号解析 / H05→auth middleware 对照 / H06→git tag 对照
