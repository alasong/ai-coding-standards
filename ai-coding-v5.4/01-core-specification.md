# AI Coding 规范 v5.5：方案设计驱动的 Auto-Coding

> 版本：v5.5 | 2026-04-24
> 定位：强制执行的治理标准 + 自治等级定义 + 方案设计驱动
> 地位：所有 AI Coding 活动必须遵守本规范的核心原则
> 变更：基于 v5.4 新增深度评分、流程裁剪档位、核心竞争力框架；消除内部引用矛盾

---

## 文档定位与适用范围

本文档是 AI Coding 规范 v5.0 系列的**核心规范**，定义不可违反的原则性约束和自治等级模型。

### 本文档包含

- 23 条核心原则（P1-P23），P1-P11 为不可违反的核心底线
- 4 级自治等级模型（L1-L4）
- TDD 与质量保障流程
- AI 幻觉检测与防护体系
- Spec 驱动开发流程
- Prompt 管理框架
- 人与 AI 的分工定义

### 配套文档

| # | 文档 | 说明 |
|---|------|------|
| 00 | **规范哲学** | 元规则：为什么存在、追求什么、从想法到产品 |
| 01 | **核心规范**（本文档） | 核心原则、自治等级、TDD、Spec 驱动、Prompt 管理、幻觉检测 |
| 02 | Auto-Coding 实践 | 自主编码模式、定时任务、夜间开发、自修复 CI、Supervisor-Worker |
| 03 | 多 Agent 与多平台 | Sub-Agents、Agent SDK、多平台协同、Slack/Channels |
| 04 | 安全与治理 | 企业部署、权限管理、MCP 安全、合规、审计 |
| 05 | 工具参考 | CLI 参考、Settings、Hooks、Skills、配置模板 |
| 07 | 反幻觉方案 | 45 种幻觉类型、证据链方法论、检测与防护方案 |
| 18 | 规范演进治理 | 规范生命周期、变更请求、审批矩阵、过渡期、版本管理 |

---

## 第 1 章：核心原则

### 1.1 核心原则清单（P1-P11，不可违反）

> 格式：每条规则 = 必须（具体行为）+ 不得（禁止行为）+ 验证（如何检查）。AI 按此执行，不得跳过任一项。

**P1 商业驱动**
- 必须：每个 Spec 包含 `business_goal` 字段，描述商业目标
- 不得：创建无 `business_goal` 的 Spec
- 验证：Spec YAML frontmatter 中 `business_goal` 非空

**P2 DCP 门禁**
- 必须：每个 Phase 完成前记录 DCP 检查结果到 `ipd/phase-N/dcp-checklist.md`
- 不得：跳过 DCP 直接进入下一 Phase
- 必须：DCP 检查必须附带深度评分（depth score），不仅检查"有没有做"，还检查"做得够不够深"
- 不得：由完成该 Phase 工作的 Agent 给自己评分。深度评分必须由独立 Agent（critic/architect/reviewer）执行
- 必须：DCP checklist 的 PASS/FAIL 判定由独立 Gate Checker Agent 执行（§1.7），不得由产出物创建者自评
- 验证：`ipd/phase-N/dcp-checklist.md` 存在且所有检查项为 PASS；`.gate/depth-score-{phase}.json` 存在且每项 ≥ 2 分；`scored_by` 字段不为 "self"

**P3 TDD 先行**
- 必须：测试先于实现编写，测试必须先失败（Red），再写实现（Green）
- 必须：测试 commit 在实现 commit 之前（不同 commit）
- 不得：测试和实现在同一 commit 中
- 不得：跳过 Red 阶段直接写实现
- 验证：`git log --oneline` 检查提交顺序；`.gate/tdd-report.json` 检查 Red 阶段记录

**P4 人工审查**
- 必须：每个 PR 有 AI Reviewer 结果（幻觉检测）和 Human Reviewer 签名
- 不得：无审查签名的 PR 合并到 main
- 验证：PR 描述中包含 AI Reviewer 输出 + Human Reviewer 签名

**P5 密钥不入代码**
- 必须：密钥、密码、token 使用环境变量或密钥管理服务
- 不得：代码或配置文件中出现硬编码密钥
- 验证：pre-commit hook（gitleaks）+ CI SAST 扫描，零 CRITICAL

**P6 单一信息源**
- 必须：每个事实在一个地方定义，其他地方引用
- 不得：同一事实在多处定义（会导致不一致）
- 验证：CI 检查文档间引用链，无循环引用

**P7 Spec 驱动**
- 必须：AI 生成代码前读取对应 Spec 文件（`specs/F{NNN}-*.md`）
- 必须：Spec 状态为 `ready` 或 `in-progress`
- 不得：无 Spec 文件直接编码
- 验证：PR 描述引用 Spec 文件路径；CI 检查 Spec 存在且状态正确

**P8 最小批量**
- 必须：一次只生成一个函数或小模块
- 不得：单个函数 > 50 行或单个文件 > 200 行（不含测试）
- 验证：CI 检查新增函数行数（`gocyclo`）和文件大小

**P9 Prompt 版本化**
- 必须：生成代码的 Prompt 存储在 `prompts/` 目录，包含 YAML frontmatter（id、version、model、status）
- 不得：使用未版本化的 Prompt 生成生产代码
- 验证：PR 描述声明使用的 Prompt 版本；`prompts/` 中存在对应文件

**P10 数据分级**
- 必须：发送给 AI 的数据经过分类，Restricted 数据经 pre-send 扫描拦截
- 不得：将密钥、PII、生产数据库内容发送给 AI
- 验证：pre-send hook 扫描，拦截 Restricted 数据

**P11 证据链**
- 必须：每个声明有 ≥2 条机器可验证证据
- 必须：证据来自不同工具或不同人/Agent（同一 CI 的多个输出视为单一证据源）
- 不得：证据链断裂（声明→证据之间必须有可追溯路径）
- 验证：`.gate/` 目录中每个声明有对应证据文件；证据交叉引用 ≥2 条

### 1.2 工程实践原则（P12-P22）

> 格式同上。语言无关原则：表格中的 Go 示例仅为 Go 语言下的具体表现，其他语言翻译为等效检查。
> 每条原则至少有两层保护（L1 AI 约束 + L2/L3/L4 之一）。

**P12 环境一致性**
- 必须：开发环境通过声明式配置管理（`.mise.toml`、`Makefile`）
- 不得：靠运行时重试或手动安装来弥补环境差异
- 验证：`make check-env` 通过；新开发者能一键 `make setup`

**P13 错误不吞**
- 必须：所有错误必须处理或返回
- 不得：`//nolint:errcheck`、`_ = json.Marshal(...)`、空 `catch`/`except`
- 验证：`go vet ./...` 零问题；pre-commit 拦截 `//nolint:errcheck`

**P14 租户隔离**
- 必须：租户 ID 从请求上下文提取
- 不得：代码中出现硬编码租户字符串
- 验证：pre-commit 扫描硬编码租户模式；测试验证多租户隔离

**P15 并发安全**
- 必须：被多个 goroutine 读写的变量使用 `sync.RWMutex` 或 `atomic.Value` 保护
- 不得：无保护地并发读写共享状态
- 验证：`go test -race ./...` 零数据竞争

**P16 资源清理**
- 必须：所有 map/channel/goroutine 有清理机制（TTL、上限、关闭信号）
- 不得：创建无清理逻辑的全局缓存或后台 goroutine
- 验证：内存泄漏测试通过；GC 压力监控正常

**P17 输入校验**
- 必须：所有外部输入（HTTP 参数、用户输入、文件路径）经过类型校验 + 边界检查
- 不得：信任调用方输入
- 验证：模糊测试通过；非法输入返回 400 Bad Request

**P18 JSON 安全**
- 必须：SSE/HTTP 响应数据使用 `json.Marshal` 或等效序列化
- 不得：字符串拼接 JSON
- 验证：CI 检查 SSE `data:` 后面为合法 JSON

**P19 认证门禁**
- 必须：所有写操作端点（POST/PUT/DELETE）有认证和角色校验
- 不得：无认证的写端点上线
- 验证：集成测试验证未认证请求返回 401/403

**P20 速率保护**
- 必须：所有昂贵端点有速率限制
- 不得：无 rate limiter 的端点上线
- 验证：压力测试返回 429 Too Many Requests

**P21 数据一致性**
- 必须：DB 写入失败返回错误
- 不得：用空返回值或成功状态码掩盖写失败
- 验证：故障注入测试验证事务回滚

**P22 IP 不暴露**
- 必须：生产 IP/域名通过 `.env` 或 `config.yaml` 注入
- 不得：代码中出现生产 IP 或域名
- 验证：pre-commit 扫描已知 IP 模式

### 1.2.2 补充原则（P23-P24）

> P23 定义在 §1.3。P24 由 [10-dependency-management.md](10-dependency-management.md) 引入。

**P24 标准库优先**
- 必须：AI 引入新依赖前必须证明标准库无法实现，且已有依赖无法复用
- 不得：仅因"方便"引入新的第三方依赖
- 验证：PR 描述中包含依赖引入理由；依赖审批记录（见 10-dependency-management.md）

### 1.2.1 多层执行机制

P12-P22 通过四层机制自动拦截，不是靠 AI 自觉：

| 层级 | 机制 | 示例 | 拦截能力 |
|------|------|------|---------|
| L1 AI 约束 | 规范声明 | 本文件 P13-P22 | 弱——AI 可能遗忘 |
| L2 Pre-commit | Git hook | 拦截 `//nolint:errcheck` | 强——提交时阻断 |
| L3 CI Gate | CI 门禁 | `go test -race` | 强——CI 阻断 |
| L4 Runtime | 代码防护 | `writeJSON` 返回 500 | 强——运行时兜底 |

**规则**：每条原则至少 L1 + L2/L3/L4 之一。只有 L1 的视为"未落地"。

### 1.3 P23：需求→Spec 链

```
需求输入 → [需求分析] → [架构适配] → [方案设计] → [Spec 生成] → 编码执行
            DP0            DP0.5         DP0.7          DP1
```

| 阶段 | 输入 | 输出 | 验证 |
|------|------|------|------|
| 需求分析 | 用户原始需求 | 结构化需求文档 | DP0 |
| 架构适配 | 结构化需求 + 架构文档 | 架构适配分析 | DP0.5 |
| 方案设计 | 架构适配分析 + 设计模板 | 方案设计文档 | DP0.7 + Quality Gate |
| Spec 生成 | 方案设计文档 + Spec 模板 | Spec 文件 | DP1 |

**必须/不得/验证**：
- 必须：编码前完成全部四阶段，每阶段以上一阶段输出为输入
- 不得：跳过任一阶段或从外部 URL 加载 Prompt
- 验证：PR 描述中声明每个 DP 的通过状态

#### 1.3.1 Context Loading Gate（进入需求分析前必须读取）

1. 行业领域知识 → `domain-knowledge/industry/{domain}.md`
2. 技术栈知识 → `domain-knowledge/tech-stack/{stack}.md`
3. 项目特定知识 → `domain-knowledge/project-specific/`
4. 现有架构理解 → `docs/architecture/`
5. 领域模型 → `docs/domain-model/`

#### 1.3.2 Solution Quality Gate（8 项检查）

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

#### 1.3.3 Skill Generalization（编码完成后执行）

1. 提取本次使用的设计/架构模式
2. 评估是否可跨项目复用
3. 有效模式写入 `domain-knowledge/`
4. 失败方案写入 `lessons/`（见 20-lessons-learned.md）

### 1.4 自治等级模型（L1-L4）

| 等级 | 名称 | 人类干预点 | 适用场景 |
|------|------|-----------|---------|
| **L1** | 辅助编码 | 每一步 | 新手团队、安全敏感项目 |
| **L2** | 半自主编码 | 每个 PR 合并前 | **日常开发（推荐默认）** |
| **L3** | 受限自主编码 | PR 合并前 + DCP 门禁 | 夜间/周末开发、成熟团队 |
| **L4** | 完全自主编码 | DCP 门禁 + 定期审计 | 高成熟度团队、低风险变更 |

#### 升级路径

| 升级 | 前置条件 | 验证方式 |
|------|---------|---------|
| **L1 → L2** | ≥20 PR 无事故、TDD ≥80%、两层 Review 已建立、CI Gate 已配置 | 检查 PR 历史、.gate/tdd-report.json、最近 5 个 PR 签名 |
| **L2 → L3** | L2 运行 ≥1 月、自主成功率 ≥70%、幻觉率 <5%、异步 DP 机制已建立 | 计算 PR 通过率、验证 Slack 通知/DP 模板/超时策略 |
| **L3 → L4** | L3 运行 ≥3 月、自主成功率 ≥85%、每周审计 ≥95%、零事故、回滚机制已演练 | 检查 4 周审计报告、回滚演练记录、监控告警配置 |

#### 降级条件（满足任一即降级）：

| 触发条件 | 降级目标 |
|---------|---------|
| 生产安全事故（AI 代码导致） | 降到 L2 |
| 幻觉代码合并到 main | 降到 L2 |
| 审计通过率连续 2 周 < 95%（L4） | 降到 L3 |
| 自主成功率连续 2 周 < 70%（L3） | 降到 L2 |
| TDD 执行率 < 80% | 降到 L1 |
| 密钥泄露到代码仓库 | 降到 L1 |

### 1.5 设计启发式（AI 可执行的架构思考）

**数据流分析**：数据从哪来 → 经过哪些转换 → 最终到哪 → 每步类型是否一致

**生命周期分析**：创建后如何读取 → 如何更新 → 如何删除/归档 → 如果从未更新会怎样

**时间维度分析**：第 1 次使用 → 第 10 次 → 第 1000 次 → 系统变好还是变差

**代码构造检查清单**（写入代码前必须执行）：

| 类别 | 检查项 |
|------|--------|
| 数据持久化 | INSERT/UPDATE 包含所有非空列；JSONB 用 `json.Marshal`；新增字段确认 migration 存在 |
| 字符串处理 | `fmt.Sprintf` 中 `%` 用 `%%` 转义；用户输入经 sanitization 后再拼入 SQL/log/URL |
| 并发安全 | 读写 map 有 mutex 保护；goroutine 中闭包变量已拷贝 |
| 输入校验 | 外部输入经类型校验 + 边界检查；路径参数防穿越 |
| 错误处理 | 所有错误被返回或处理；禁止 `//nolint:errcheck`；错误消息不泄露内部细节 |

### 1.6 IPD 流程与方法引擎

每个阶段必须有明确的方法、AI 辅助方式和决策标准。自治等级（L1-L4）仅影响 Phase 3。

#### 1.6.1 Phase 0：市场洞察

**目标**：明确"为什么要做"。方法：五看三定（行业/市场/客户/竞争/自己 → 目标/策略/路径）、BLM 模型、技术趋势雷达、VOC 分析、竞品范围确认（≥3 维度、≥1 非直接竞品）。

**DCP 检查**：商业机会经过五看验证？排除了伪需求？有明确差异化定位？

#### 1.6.2 Phase 1：概念定义

**目标**：明确"做什么"。方法：$APPEALS（8 维度竞争力评估）、Kano 模型（基本/期望/兴奋型需求）、QFD（客户需求→技术参数映射）、JTBD（用户场景分析）、价值曲线、核心竞争力画像（综合三工具产出三层竞争力：入场券/拉开差距/杀手锏 + 竞品追赶预警 + 防守优先级）。

**DCP 检查**：需求分类覆盖 Kano 三类型？QFD 矩阵完整？JTBD 覆盖核心用户场景？核心竞争力综合识别完成（三层画像 + 竞品追赶预警）？需求反例定义明确？潜在变量识别完整？

#### 1.6.3 Phase 2：详细规划

**目标**：明确"怎么做"。方法：DFX（可维护性/可扩展性/安全性/性能）、架构权衡分析(ATA)、WBS 分解（到 Feature 粒度）、风险矩阵、里程碑规划。

**DCP 检查**：DFX 全通过？架构方案经过权衡分析？WBS 分解到 Feature 粒度？Top 3 风险有缓解方案？核心竞争力→架构适配传导完成？深度评分≥60%？P11 证据链完整？

#### 1.6.4 Phase 3：AI 辅助开发

**目标**：高质量交付。方法：TDD 先行(P3)、Spec 驱动(P7)、最小批量(P8)、Self-Correction Loop(≤3 轮)、两层审查(P4)、质量降级机制、设计启发式、构造检查清单。详见全文各章节。

**DCP 检查**：TDD 合规率 ≥ 80%？幻觉率 < 5%？Spec 覆盖度 100%？深度评分≥60%？P11 证据链完整？

#### 1.6.5 Phase 4：验证发布

**目标**：确保"做好了"。方法：

| 方法 | 说明 | 产出 |
|------|------|------|
| **E2E 测试** | 端到端场景覆盖，模拟真实用户路径 | E2E 测试报告 |
| **Beta 测试** | 真实用户在受控环境下的试用 | Beta 反馈汇总、满意度评分 |
| **GRTR**（General Technical Review） | 性能/安全/兼容性跨部门评审 | GRTR 评审报告 |
| **ADCP**（Availability Decision Checkpoint） | 可用性决策：系统是否准备好上线 | ADCP 决策记录 |
| **发布 Readiness 检查** | 部署脚本、回滚计划、监控告警就绪 | Release Readiness Checklist |
| **性能验收** | 对照 .performance-budget.yaml 逐项验证 | 性能验收报告 |
| **安全验收** | DAST 扫描、渗透测试、合规检查 | 安全验收报告 |
| **用户文档审查** | 帮助文档、API 文档、Release Notes 完整性 | 文档审查清单 |

**DCP 检查**：E2E 测试 100% 通过？Beta 用户满意度达标？GRTR/ADCP 全通过？性能预算合规？安全扫描无高危？深度评分≥60%？P11 证据链完整？

#### 1.6.6 Phase 5：生命周期

**目标**：持续改进。方法：

| 方法 | 说明 | 产出 |
|------|------|------|
| **客户反馈闭环** | 收集→分类→优先级排序→纳入 Backlog→验证 | 反馈处理报告 |
| **技术债管理** | 识别→分级→排期→偿还→验证 | 技术债台账 |
| **生命周期趋势分析** | 用户活跃、留存、性能趋势、错误率趋势 | 生命周期仪表盘 |
| **产品退市策略(EOL)** | 版本下线通知、迁移路径、数据清理 | EOL 计划 |
| **Lessons Learned** | 每 Feature 结束后提取教训，写入 20-lessons-learned.md | 教训注册表 |
| **深度评分回溯** | 对照 Phase 0-2 的深度评分基线，验证预测准确性 | 深度评分回溯报告 |
| **传导回 Phase 0** | 生命周期发现的竞品变化/需求变化传导至下一轮 Phase 0 | Phase 0 刷新触发 |

**DCP 检查**：客户反馈响应时间达标？技术债趋势可控？生命周期指标在预期范围内？Lessons Learned 已提取？传导检查已完成？深度评分≥60%？P11 证据链完整？

---

**IPD 六阶段与自治等级的关系**：自治等级（L1-L4）仅影响 **Phase 3** 的执行方式。Phase 0-2 和 Phase 4-5 的决策质量由上述方法论保障，不受自治等级影响。

### 1.6.7 阶段间变更传导规则（Phase Change Propagation）

> **核心原则**：IPD 六阶段不是顺序流水线，而是依赖链。下游阶段的决策以上游阶段的产出为输入。

当任一 Phase N 的产出物发生**实质性变化**时（新增、修改、废弃关键假设或结论），必须执行传导检查：

| 步骤 | 动作 | 产出 |
|------|------|------|
| **1. 影响识别** | 列出 Phase N+1 的核心假设，逐一判断是否仍成立 | 影响清单 |
| **2. 局部刷新** | 不成立的假设所在阶段，重新生成受影响章节 | 刷新后的产出物 |
| **3. 逐阶段传导** | 从 Phase N+1 传导至 Phase 5，每阶段输出 PASS 或 REFRESHED | 传导矩阵 |
| **4. 记录** | 写入 `ipd/phase-N/impact-log-{date}.md` | 审计追溯 |

**传导方向与依赖关系**：

| 依赖关系 | 上游产出（被依赖） | 上游变化时的下游检查重点 |
|---------|--------------|-------------------|
| Phase 1 → Phase 0 | 市场洞察报告、竞品范围声明 | 新竞品是否改变差异化定位、优先级排序 |
| Phase 2 → Phase 1 | 概念定义、JTBD、Kano 分类 | 需求优先级变化是否影响架构预留 |
| Phase 3 → Phase 2 | 架构决策、WBS、风险矩阵 | Sprint 范围是否覆盖已识别风险 |
| Phase 4 → Phase 3 | 已交付代码、测试结果 | 发布标准是否因交付质量调整 |
| Phase 5 → Phase 4 | 发布版本、用户反馈 | 生命周期策略是否因市场反馈变化 |

**不触发传导的变化**：格式调整、错别字、不影响结论的措辞修改、补充已有结论的证据。

**触发传导的变化**：新增竞品、差异化定位改变、需求优先级重排、架构决策变更、风险矩阵更新、Sprint 范围调整。

### 1.6.8 深度评分与基线提升机制（Depth Score & Bar Raising）

> **核心问题**：静态的检查清单只能保证"动作做了"，不能保证"做得够深"。深度评分解决"够不够深"的问题，基线提升机制确保深度标准不断抬高。

#### 评分规则

每个 Phase 的 DCP 深度评分表包含 3-5 个维度，每个维度 0-3 分：

| 分数 | 定义 | 判断标准 |
|------|------|---------|
| **0** | 未做 | 该维度完全没有涉及 |
| **1** | 表面层 | 有输出但停留在"有无对比"（功能对照表、数量统计、只有 happy path） |
| **2** | 机制层 | 拆解了"怎么做"和"为什么"（竞品的实现机制、设计的权衡理由、测试覆盖边界） |
| **3** | 批判层 | 指出了"做得不好的地方"（竞品的缺陷、Spec 自身的盲区、未验证的假设） |

**通过条件**：每项 ≥ 2 分，且总分 ≥ 该阶段满分 × 60%。

#### 评分维度定义（各 Phase）

| Phase | 维度 1 | 维度 2 | 维度 3 | 维度 4 |
|-------|--------|--------|--------|--------|
| **P0 市场洞察** | 竞品机制拆解 | 用户边界场景 | 差异化批判 | 自身盲区识别 |
| **P1 概念定义** | 需求反例定义 | 潜在变量识别 | 场景覆盖度 | 伪需求排除 |
| **P2 详细规划** | 架构反向推导 | 风险自评 | 依赖影响链 | 约束条件枚举 |
| **P3 AI 开发** | 测试深度分布 | Spec 反例 AC | 错误路径覆盖 | 边界条件枚举 |
| **P4 验证发布** | 失败模式覆盖 | 用户真实反馈 | 回归风险识别 | 发布条件批判 |
| **P5 生命周期** | 反馈闭环质量 | 技术债趋势 | 退化预警 | 改进建议批判 |

#### 基线提升机制

深度评分表是**活的**，随项目经验生长：

1. **基线记录**：每个 Feature 完成后，记录该 Phase 的最高得分到 `.gate/depth-baselines.json`
2. **下次不低于基线**：同一 Phase 的后续 DCP 评分不得低于已有基线
3. **盲区注入**：开发过程中发现的"当初没想到"的事，必须写入该 Phase 的评分维度，成为永久新维度
4. **基线提升**：当某维度连续 3 个 Feature 都拿到 3 分，该维度的通过线从 ≥ 2 提升到 ≥ 3

```json
// .gate/depth-baselines.json 示例
{
  "P0": {
    "竞品机制拆解": { "baseline": 2, "history": [2, 3, 2] },
    "用户边界场景": { "baseline": 1, "history": [1], "promoted": true }
  }
}
```

#### 独立 Agent 验证（防止自评变成样子货）

评分报告 `.gate/depth-score-{phase}.json` 必须包含 `self_check` 字段，自动检测异常模式：

| 异常模式 | 检测逻辑 | 动作 |
|---------|---------|------|
| 全 3 分 | 所有维度都是 3 分 | 标记 `[DEPTH-SUSPECT]`，要求人工复核 |
| 全 2 分且该 Phase 产出变更 > 5 文件 | 所有维度都是 2 分，且涉及实质变更 | 标记 `[DEPTH-ROBOTIC]`，要求至少 1 项差异化评分；≤5 行纯代码修复的全 2 分视为正常 |
| 评分与缺陷不一致 | 评分 ≥ 80% 但该 Phase 后续发现 ≥ 3 个设计缺陷 | 标记 `[DEPTH-INVALID]`，回溯调整该维度基线 |

**新项目基线初始值**：新项目无历史数据时，所有维度初始基线 = 1 分（而非 0 分），避免首期评分缺乏参考锚点。

**基线上限**：单维度基线最高为 2 分（不得提升到 3 分）。3 分是"批判层"满分，代表发现了前人未见的盲区，不应作为"必须达到的标准"，否则会惩罚真正的批判性思考。

**独立 Agent 要求：**
- 深度评分必须由独立 Agent 执行，该 Agent 不得与完成该 Phase 工作的 Agent 共享对话上下文
- 评分报告必须包含 `scored_by: "independent {agent_type}"` 字段
- 若 `scored_by` 字段为 "self"、"self-assessment" 或同类 Agent 生成，标记 `[DEPTH-SELF-SCORED]`，判定为无效评分，必须重新评分
- 独立 Agent 评分与自评差异 ≥ 2 分时，以独立 Agent 评分为准

#### 关键特性深度分级（Feature Depth Tiering）

> **核心问题**：不同特性的深度要求不同。一刀切的深度标准要么浪费资源在非关键特性上，要么在关键特性上深度不足。

深度评分根据特性关键程度分级执行：

| 级别 | 定义 | 通过线 | Multi-Pass | 审查视角 | 方法要求 |
|------|------|--------|-----------|---------|---------|
| **D1 核心特性** | 直接影响收入/安全/合规/核心用户体验 | 每项 ≥ 2.5 分，总分 ≥ 75% | 6 Pass 全执行 | 3+ 对抗视角（竞品/审计/攻击者/用户） | 竞品机制拆解必须到代码级，架构权衡必须有量化分析 |
| **D2 重要特性** | 影响次要用户体验/性能/可扩展性 | 每项 ≥ 2 分，总分 ≥ 60% | 5 Pass（P3 可简化为 2 视角） | 2 对抗视角 | 竞品机制拆解到功能级，架构权衡有定性分析 |
| **D3 一般特性** | 内部工具/管理后台/边缘功能 | 每项 ≥ 1.5 分，总分 ≥ 50% | 3 Pass（P1+P4+P5） | 1 对抗视角 | 功能对照即可 |
| **D4 维护特性** | Bug 修复/格式调整/文档更新 | 每项 ≥ 1 分 | S 档（见 §1.6.9） | 跳过 | 无 |

**级别判定**：由 Spec 的 YAML frontmatter `depth_tier` 字段声明，由 Tech Lead 在 DCP 中确认。若未声明，默认按 D2 执行。

**级别升级触发条件**：
- 安全/合规相关特性自动升级为 D1
- 涉及用户数据/隐私的特性自动升级为 D1
- P0 生产事故修复自动升级为 D2
- 连续 3 个 D2 特性因深度不足导致回归，自动升级为 D1

**关键特性额外审查要求（D1）**：
- P3 对抗审查必须包含"如果安全团队看这个设计，会质疑什么"视角
- P4 Gate Checker 必须使用 sonnet 或 opus（不得用 haiku）
- P6 深度评分的"自身盲区识别"维度必须 ≥ 3 分
- 必须在 `.gate/` 中额外产出 `d1-risk-assessment.json`，包含≥3 条风险分析
- Lessons Learned 强制引用：必须引用 ≥2 条 open 教训

**通用独立验证原则：**
> **不得由产出物的创建者对该产出物进行 PASS/FAIL 判定。所有 Gate 的 PASS/FAIL 必须由独立 Agent 或自动化工具决定。**
>
> 适用于：DCP Checklist（§1.6）、Solution Quality Gate（§1.3.2）、Spec Validation Gate（§4.2）、IPD 传导检查（§1.6.7）、Spec Evolution draft→review 转换（18-spec-evolution-governance.md §1.2）、部署审计完整性验证（13-deploy-rollback.md §8.5）、Supervisor-Worker 测试结果复测（02-auto-coding-practices.md §5、03-multi-agent-multi-surface.md §14.3）。
> 自动化工具（compiler, gitleaks, go test, golangci-lint）判定视为独立。

### 1.6.9 流程裁剪档位（Process Profile）

> L1-L4 控制 AI 自主程度，Process Profile 控制流程重量。两者正交。

| 档位 | 执行阶段 | DCP | 适用场景 |
|------|---------|-----|---------|
| **S** | 仅 Phase 3 | 0 | 单文件 ≤50 行，无 API/架构变更 |
| **M** | Phase 1→3 | 1 次 | 1-3 个 Spec |
| **L** | Phase 0→3 | 2 次 | 3-10 个 Spec / 架构变更 |
| **XL** | Phase 0→4 + Phase 5 前置 | 3+ 次 | 10+ Spec / 平台级 / 生产级发布 |

**不可裁剪项**（任何档位必须遵守）：
- P1-P11 核心原则
- P12-P22 工程实践
- TDD 流程（P3）
- 安全底线（P5 密钥不入代码、P17 输入校验、P19 认证门禁）

**可裁剪项**（按档位裁剪）：

| 裁剪维度 | S | M | L | XL |
|---------|---|---|---|----|
| Phase 0 文档 | 跳过 | 跳过（复用已有） | 完整 | 完整+外部验证 |
| Phase 1 文档 | 跳过 | 压缩（仅 Kano+JTBD） | 完整 | 完整 |
| Phase 2 ATA/DFX | 跳过 | 跳过 | 完整 | 完整+独立评审 |
| 深度评分维度 | 0 | 2 | 4 | 4+ |
| Multi-Pass Review | 2 Pass（Self+Human） | 3 Pass | 5 Pass | 5 Pass+审计 |
| 传导检查 | 跳过 | 仅下游 | 全链 | 全链+回溯 |

**档位选择**：由需求提出者 + 技术负责人共同确定。纯 AI 项目（L3/L4 夜间开发）按以下规则自动选择：
- Spec 行数 ≤ 50 行 + 单文件 → S
- 1-3 个 Spec 且无架构变更 → M
- 3-10 个 Spec 或含架构变更 → L
- 10+ Spec 或平台级/生产级发布 → XL
选错可升级（补 Phase）或降级（跳过剩余 Phase）。

**档位升级触发条件（Escape Hatch）**：
| 当前档位 | 升级触发条件 | 升级目标 |
|---------|-------------|---------|
| **S** | 变更扩散 > 3 文件或引入新 API 端点 | → M |
| **M** | 变更涉及架构决策或 > 3 个 Spec | → L |
| **L** | 变更涉及平台级重构或 > 10 个 Spec | → XL |
升级后必须补做被跳过阶段的最小必要产出。

**档位与自治等级的关系**：L4 可以跑 S 档（全自动小修），也可以跑 XL 档（全自动平台级重构）。自治等级管"谁做"，流程档位管"做多重"。

**S 档对 P23 的豁免**：S 档（仅 Phase 3，单文件 ≤50 行，无 API/架构变更）可跳过 P23 的"需求分析 → 架构适配 → 方案设计"阶段，但仍需：(a) 有有效 Spec 文件（可直接从需求生成，无需方案设计文档），(b) 遵守 P1-P11 核心原则，(c) 遵守 P12-P22 工程实践。

### 1.7 Gate Checker Agent（独立验证）

> **核心原则**：Gate 检查由独立的 Gate Checker Agent 执行，不混入 Executor 的上下文。Executor 完成一轮工作后触发 Gate Checker，Gate Checker 只读验证，输出 Pass/Fail 报告。

#### 1.7.1 架构

```
Executor Agent（写代码、跑测试、修复）
  │ 完成一轮工作后触发
  ▼
Gate Checker Agent（只读验证，独立上下文）
  │ 输出 Pass/Fail + 缺陷报告
  ▼
Pass → 创建 PR
Fail → 返回 Executor 修复
```

#### 1.7.2 权限约束

| 约束 | 说明 |
|------|------|
| **只读** | Gate Checker 不得 Edit、Write 或修改任何代码 |
| **独立上下文** | 不得与 Executor 共享同一对话上下文 |
| **输出文件** | 验证结果写入 `.gate/gate-report-{date}.md` |
| **模型** | 建议使用 haiku（快速验证）或 sonnet（复杂 Gate） |

#### 1.7.3 Gate 检查项

| Gate | 检查内容 | 证据来源 |
|------|---------|---------|
| **TDD Gate** | 提交顺序、Red→Green、AC 覆盖、新增代码测试 | git log + `.gate/tdd-report.json` |
| **Spec Gate** | Spec 存在、状态正确、API 对齐 | `specs/` 文件 + 代码对比 |
| **IPD 传导 Gate** | 上游变更触发下游刷新、WBS 引用 | `ipd/phase-N/` 文件 + WBS 对照 |
| **安全 Gate** | 密钥、SQL 拼接、eval/exec、Protected Paths | gitleaks + 代码扫描 |
| **质量 Gate** | 编译、vet、test、lint、覆盖率基线 | 构建输出 + coverage |
| **幻觉 Gate** | API 存在性、依赖、符号解析、注释一致性 | 编译 + 符号解析 |
| **Self-Correction Gate** | 轮次≤3、安全漏洞未自修提交 | `.gate/self-correction.json` |
| **DCP Gate** | Phase checklist PASS/FAIL 判定、深度评分独立性验证 | `ipd/phase-N/dcp-checklist.md` + `.gate/depth-score-{phase}.json` |
| **Solution Quality Gate** | 8 项检查由独立 Agent 执行，非方案作者自评 | 方案设计文档 + 8 项检查对照表 |
| **Spec Validation Gate** | 6 项验证由独立 Agent 执行，非 Spec 作者自评 | Spec 文件 + 6 项验证对照表 |

#### 1.7.4 触发时机

| 时机 | 触发方式 |
|------|---------|
| Executor 完成一轮编码/修复 | Executor 主动调用 Gate Checker Agent |
| PR 创建前 | CI Pipeline L3 层自动调用 |
| IPD Phase 转换 | Phase N → Phase N+1 时自动调用 |

### 1.8 Multi-Pass Review Protocol

> 完整定义：[19-multi-pass-review.md](19-multi-pass-review.md)
> 会诊模式实现：见 [03-multi-agent-multi-surface.md](03-multi-agent-multi-surface.md) 第 2 章

每个 IPD Phase 产出完成后，必须执行 **6 轮审查**，对 **7 个 Gate** 的 **25 个检查项** 逐项进行 **3 轮独立验证**：

| Pass | 名称 | 执行者 | 视角 |
|------|------|--------|------|
| **P1** | Self-Verify | 作者/Executor | 完整性 |
| **P2** | Cross-Verify | 独立 Agent | 上下游一致性 |
| **P3** | Adversarial Review | 独立 Agent | 竞品/审计/攻击者视角 |
| **P4** | Gate Checker | 独立 Gate Checker Agent | 规范合规（只读）|
| **P5** | Human Reviewer | 人类 | 战略对齐 + 风险接受度 |
| **P6** | Depth Score | 独立 Agent（critic/architect） | 深度质量（见 §1.6.8）|

**审查次数**：7 Gate × ~5 检查项 × 3 轮验证 × 6 Pass = **630 次**（自动达成 ≥200 次要求）。
每次审查必须有明确的工具、方法和通过标准，不得人为削减轮次以凑数字。

**逃逸条件**：微小变更（≤5 行单文件）、纯格式变更、紧急 Hotfix 可跳过部分 Pass，
但必须在 Gate Report 中注明原因。

### 1.9 Lessons Learned Protocol（教训链）

> 完整定义：[20-lessons-learned.md](20-lessons-learned.md)
> 与证据链（P11）并列：证据链记录"我们做对了"，教训链确保"我们不再犯同样的错"。

**核心规则**：

| 规则 | 内容 |
|------|------|
| **强制读取** | Feature 开发前必须读取 `lessons/lessons-registry.yaml`，引用相关教训到 Spec |
| **即时记录** | 开发中发现的新教训必须立即记录，不得延迟 |
| **48h 注入** | 教训记录后 48 小时内必须注入到对应规范或流程 |
| **深度评分联动** | 深度评分检查教训引用完整性，缺失标记 `[LESSONS-MISSING]` |

**教训级别**：L1 设计盲区 → L2 执行偏差 → L3 规范缺陷 → L4 系统性风险

**违反**：未引用相关教训 → P6 标记 `[LESSONS-MISSING]`，得分降级 1 级。

---

## 第 2 章：TDD 与质量保障

### 2.1 Auto-Coding TDD 流程（L2-L4）

```
读 Spec → 写测试 → 提交测试（CI 记录 Red）→ 写实现 → 测试通过（Green）→ 重构 → 全量验证 → 创建 PR
```

**规则**：
- 必须：测试从 Spec 验收标准生成，先于实现提交，先失败再写实现
- 不得：测试和实现在同一 commit 中；跳过 Red 阶段
- 验证：`git log` 检查提交顺序；`.gate/tdd-report.json` 检查 Red 记录

### 2.2 Self-Correction Loop（最多 3 轮）

```
失败 → Round 1 → 仍失败 → Round 2 → 仍失败 → Round 3 → 仍失败 → 停止，通知人工
```

**规则**：
- 必须：每轮分析错误原因后最小修改；第 3 轮失败后标记 `[SELF-CORRECTION-EXHAUSTED]`
- 不得：超过 3 轮继续自修；架构问题使用自修（成功率仅 20%）
- 验证：`.gate/self-correction.json` 记录轮次

### 2.3 全量验证 Gate

**流程**：编译 → 全量测试 → lint → 失败则自修（最多 3 轮）

**覆盖率规则**：
- AC 覆盖率（强制）：每个 AC ≥1 测试函数 + ≥2 证据项，<100%=未完成
- 新增代码（强制）：新函数/新文件必须有测试，否则阻塞合并
- ~~行覆盖率数字目标~~（已弃用：AI 时代数字无区分度，改为测试深度评估）
- 包覆盖率（趋势）：不得较基线下降 > 5%，作为 CI 警告
- **测试深度评分**（新增）：每个包按五维度评估——①边界条件 ②异常路径 ③并发安全 ④安全边界 ⑤业务行为正确性。评分 1-5 分，≥3 分为合格
- 证据文件：写入 `.gate/coverage.json` + `.gate/test-quality.json`

### 2.4 质量响应与增强机制

> 核心原则：质量波动是系统升级的信号，不是退回人工的理由。每次"失败"必须转化为一次知识库注入。

| 级别 | 触发条件 | 诊断动作 | 增强动作 | 闭环 |
|------|---------|---------|---------|------|
| **L0 正常** | 一次通过率 > 80% | 无 | AI 自主推进 | 成功模式提取到 `domain-knowledge/` |
| **L1 诊断** | 一次通过率 60-80% | 分析失败根因：Spec 不清晰？领域知识缺失？复杂度超限？ | 修复根因后重试（≤2 轮） | 根因写入 `.gate/quality-diagnosis.json` |
| **L2 增强** | 一次通过率 < 60% | 识别知识缺口，自动增强上下文：补充领域知识、拆分 Spec、引入专家 Agent 会诊 | 会诊式多 Agent 联合审查（见 03-multi-agent 第 2 章） | 增强措施写入知识库，基线提升 |
| **L3 人工决策** | 严重退化或架构级分歧 | **人不做编码工作**——提供业务判断/架构选择/优先级决策 | AI 基于人的决策继续编码 | 介入原因记录为教训，注入 `lessons/` |

**禁止行为**：
- 不得以"质量降级"为由直接退回人工编码
- 不得在 L1/L2 阶段跳过根因诊断直接升级干预级别
- 不得在 L3 阶段让人类替代 AI 编写代码（人类仅提供决策信息）

**升级恢复**：连续 3 个 Feature 在 L0 完成 → 自动恢复 L0 级别。

---

## 第 3 章：AI 幻觉检测与防护

### 3.1 核心认识

AI 幻觉是 LLM 的本质特征，**每次生成都可能发生**。防护目标是确保即使发生也不进入生产。

### 3.2 防护策略

| 策略 | 规则 |
|------|------|
| **Example-Driven** | 用真实项目代码示例替代规则描述，示例包含问题+错误示例+正确示例+原因 |
| **Prompt Chaining** | 复杂任务拆为：分析→设计→编码→验证，每步验证输出，失败最多重试 3 次 |
| **Progressive Disclosure** | P0（Spec、接口契约）每次加载；P1（相关源文件）按需加载；P2（历史）手动注入 |
| **两层审查** | AI Reviewer 检测幻觉 + Human Reviewer 专注业务逻辑 |

**前置链**：Prompt Chaining 用于编码阶段，必须先完成 P23 的 Requirement→Solution→Spec 链。

### 3.3 指标

| 指标 | 目标 | 告警 |
|------|:----:|------|
| 幻觉发生率 | < 5% | > 10% |
| 幻觉拦截率 | 100% | < 90% |
| 幻觉逃逸率 | 0% | > 0% |

---

## 第 4 章：Spec 驱动开发

### 4.1 Feature Spec 规范

每个 Feature 必须有且仅有一个 Spec 文件（`specs/F{NNN}-{name}.md`），包含 YAML frontmatter（type、id、name、version、status、priority、autonomy_level）和正文。

**正文必须包含**：用户故事、验收标准（Gherkin 格式）、边界条件、数据模型、API 设计、非功能需求。

### 4.2 Spec Validation Gate

| 验证项 | 检查要点 |
|--------|---------|
| 与需求一致性 | 每个需求条目至少有一个 AC 对应 |
| 与架构一致性 | 不违反任何 ADR |
| 验收标准可测试 | Gherkin 格式可执行 |
| 边界条件完整 | 至少覆盖正常路径 + 3 种异常路径 |
| 非功能需求明确 | 数值化，不可用模糊描述 |

### 4.3 Spec 状态机

`draft → validated → ready → in-progress → done`（任一状态可 → `deprecated`）

**状态转换触发条件**：

| 转换 | 触发 | 执行者 |
|------|------|--------|
| draft → validated | Spec Validation Gate 通过 | AI + AI Reviewer |
| validated → ready | DCP 决策通过 | 人工 |
| ready → in-progress | Phase 3 开始 | AI |
| in-progress → done | TDD + Gate 全部通过 | AI |
| done → in-progress | 回归/修复 | AI |
| 任一状态 → deprecated | 需求取消 | 人工 |

---

## 第 5 章：Prompt 管理

### 5.1 Prompt 版本化（P9）

**规则**：
- 必须：Prompt 存储在 `prompts/` 目录，包含 YAML frontmatter（id、version、model、temperature、feature、status）
- 不得：使用未版本化的 Prompt 生成生产代码；从 URL 或外部服务加载 Prompt
- 验证：PR 描述声明使用的 Prompt 版本；`prompts/` 中存在对应文件

### 5.2 Prompt 安全

- Spec 中的用户输入不得直接拼接到 Prompt 中
- 每季度审查 Prompt 仓库，删除过时 Prompt

---

## 第 6 章：人与 AI 的分工

### 6.1 基础分工

| 活动 | 人类角色 | AI 角色 |
|------|---------|---------|
| 战略/产品/架构决策 | 决策者 | 信息整理、方案对比 |
| Spec 编写 | 审核者 | 草稿生成（L2+） |
| 测试/编码 | 审核者 | 执行者 |
| 安全审查 | 决策者 | 辅助扫描 |
| 部署运维 | 监督者（L1-L2）/ 审计者（L4） | 执行者 |

### 6.2 Decision Point

| DP | 时机 | 拦截的错误类型 |
|----|------|---------------|
| DP0 | 需求分析完成后 | 需求理解偏差 |
| DP0.5 | 架构适配完成后 | 架构不兼容 |
| DP0.7 | 方案设计完成后 | 方案不可行 |
| DP1 | AI 分析完代码结构后 | AI 误解需求 |
| DP2 | AI 给出技术方案后 | 过度工程 |
| DP3 | 全部完成后 | 功能不完整 |
| DP4 | Hotfix 时 | 修复引入新问题 |

**L3 异步模式**：DP1/DP2 阻塞，DP3 非阻塞，超时 2 小时自动降级为非阻塞。

**DCP 与 Decision Point 的区别**：DCP = 阶段级（宏观），DP = 任务级（微观），两者互补。

---

## 附录 A：术语表

| 术语 | 定义 |
|------|------|
| AI Coding | 使用 LLM 辅助完成软件开发全生命周期活动 |
| 自治等级 | AI 可以独立工作的程度，分为 L1-L4 |
| DCP | Decision Check Point，决策检查点 |
| Spec | Feature Specification，功能规格说明 |
| TDD | Test-Driven Development，测试驱动开发 |
| Self-Correction Loop | AI 自动生成→检查→自修的循环（最多 3 轮） |
| Prompt Chaining | 将复杂任务拆为顺序 Prompt 链 |
| Progressive Disclosure | 按需加载上下文的策略 |
| Example-Driven Prompting | 用代码示例驱动 AI 的方式 |
| AI 幻觉 | LLM 生成看似合理但实际错误的内容 |

## 附录 B：快速参考

```
核心原则：
P1 商业驱动 ── P2 DCP 门禁 ── P3 TDD 先行 ── P4 人工审查 ── P5 密钥不入
P6 单一信息 ── P7 Spec 驱动 ── P8 最小批量 ── P9 Prompt 版 ── P10 数据分级
P11 证据链 ── P23 需求→Spec 链（P12-P22 工程实践，见 1.2）

自治等级：
L1 辅助编码 ── L2 半自主（默认★）── L3 受限自主 ── L4 完全自主

TDD：Red → Green → Refactor
幻觉防护：Example-Driven + Prompt Chaining + Progressive Disclosure + 两层审查

Decision Point：DP0 需求 → DP0.5 架构 → DP0.7 方案 → DP1 理解 → DP2 方案 → DP3 发布 → DP4 变更
```

## 附录 C：版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v4.0 | 2026-04-13 | 基线版本 — 10 条核心原则 + IPD 流程 |
| v5.0 | 2026-04-14 | 重大重构 — 引入 4 级自治模型（L1-L4），增强幻觉检测 |
| v5.1 | 2026-04-16 | P11 证据链 + V04/C01 幻觉类型 |
| v5.2 | 2026-04-17 | P23 方案设计驱动、DP0/DP0.5/DP0.7、Context Loading Gate、Solution Quality Gate、Skill Generalization |
| **v5.4** | **2026-04-18** | **IPD 六阶段方法引擎：五看三定/BLM/$APPEALS/Kano/QFD/DFX/ATA/E2E/技术债管理** |
| **v5.5** | **2026-04-24** | **Phase 4/5 方法论扩充、45 种幻觉类型补全、lessons/ 目录创建、Process Profile 跨文档集成、关键特性深度分级、全链路断链修复** |

---

## 附录 D：全机制目录（Mechanism Catalog）

> 本附录汇总规范体系中的所有 Gate、方法、评分、流程机制。任何文档修改后必须对照本目录，确保该机制仍在正确位置被定义和引用。

### D.1 Gate 体系（15 个 Gate）

| # | Gate 名称 | 定义位置 | 执行时机 | 执行者 | 产出 |
|---|----------|---------|---------|--------|------|
| G-1 | Context Loading Gate | §1.3.1 | 需求分析前 | AI | 知识加载清单 |
| G-2 | Solution Quality Gate | §1.3.2 | 方案设计后 | 独立 Agent | 8 项检查报告 |
| G-3 | Spec Validation Gate | §4.2 | Spec 生成后 | 独立 Agent | 5 项验证报告 |
| G-4 | TDD Gate | §1.7.3 + 19-multi-pass | 代码提交后 | Gate Checker | 提交顺序/Red→Green/AC 覆盖 |
| G-5 | Spec Gate | §1.7.3 + 19-multi-pass | PR 创建前 | Gate Checker | Spec 存在+API 对齐 |
| G-6 | IPD 传导 Gate | §1.6.7 + 19-multi-pass | Phase 转换时 | Gate Checker | 传导矩阵 |
| G-7 | 安全 Gate | §1.7.3 + 19-multi-pass | CI L3 | Gate Checker | 密钥/SQL/eval/路径 |
| G-8 | 质量 Gate | §1.7.3 + 19-multi-pass | CI L1-L2 | Gate Checker | 编译/vet/test/lint/覆盖 |
| G-9 | 幻觉 Gate | §1.7.3 + 19-multi-pass | CI L3 | Gate Checker | API/依赖/符号/注释 |
| G-10 | Self-Correction Gate | §1.7.3 + 19-multi-pass | 自修后 | Gate Checker | 轮次≤3+无自修安全漏洞 |
| G-11 | DCP Gate | §1.7.3 | Phase 完成时 | Gate Checker | checklist + 深度评分 |
| G-12 | Pipeline Gate | 06-cicd-pipeline §2 | PR 合并时 | CI Pipeline | L0-L5 执行结果 |
| G-13 | Deployment Gate | 13-deploy-rollback §8 | 部署前 | CI + 人工 | 回滚计划+LKG 版本 |
| G-14 | Release Gate | 14-release-mgmt §7 | 发布前 | CI Pipeline | 7 类检查清单 |
| G-15 | Multi-Pass Review Gate | 19-multi-pass §1 | Phase 完成后 | 6 个独立角色 | 630 次验证报告 |

### D.2 方法论体系（IPD 六阶段）

| Phase | 方法论 | 关键工具 | 定义位置 |
|-------|--------|---------|---------|
| **P0 市场洞察** | 五看三定 | BLM 模型、技术趋势雷达、VOC 分析 | §1.6.1 |
| **P1 概念定义** | $APPEALS | Kano 模型、QFD 矩阵、JTBD、价值曲线、核心竞争力画像 | §1.6.2 |
| **P2 详细规划** | 架构设计 | DFX、ATA、WBS 分解、风险矩阵、里程碑规划 | §1.6.3 |
| **P3 AI 开发** | TDD 驱动 | Red→Green→Refactor、Self-Correction≤3 轮、两层审查 | §1.6.4 + §2.1 |
| **P4 验证发布** | 质量验证 | E2E、Beta 测试、GRTR、ADCP、性能/安全验收 | §1.6.5 |
| **P5 生命周期** | 持续改进 | 客户反馈闭环、技术债管理、Lessons Learned、传导回 P0 | §1.6.6 |

### D.3 评分体系（3 个维度）

| 评分 | 维度 | 分值 | 通过线 | 定义位置 |
|------|------|------|--------|---------|
| **深度评分** | 4 维度 × 0-3 分 | 4-12 分 | 每项≥2 + 总分≥60% | §1.6.8 |
| **深度评分** | 关键特性分级 | D1-D4 | D1: 每项≥2.5, 75% | §1.6.8 关键特性深度分级 |
| **测试深度评分** | 5 维度 × 1-5 分 | 5-25 分 | ≥3 分合格 | §2.3 覆盖率规则 |
| **基线提升** | 维度历史基线追踪 | 上限 2 分 | 连续 3 次=3 分→提升 | §1.6.8 |

### D.4 流程体系（6 条主链）

| 链 | 步骤 | 方法 | 定义位置 |
|----|------|------|---------|
| **需求→Spec 链** | 需求分析→架构适配→方案设计→Spec 生成 | DP0/DP0.5/DP0.7/DP1 | §1.3 |
| **IPD 六阶段链** | Phase 0→1→2→3→4→5 | 各阶段方法论 | §1.6 |
| **IPD 传导链** | Phase N 变化→影响识别→局部刷新→逐阶段传导 | 传导矩阵 | §1.6.7 |
| **TDD 链** | Red → Green → Refactor → 全量验证 → PR | git log 验证 | §2.1 |
| **Pipeline 链** | L0 → L1 → L2 → L3 → L4 → L5 | 分层门禁 | 06-cicd-pipeline |
| **审查链** | P1 Self-Verify → P2 Cross-Verify → P3 Adversarial → P4 Gate Checker → P5 Human → P6 Depth Score | 630 次验证 | 19-multi-pass |
| **教训链** | 发现→记录→注入→引用→验证→清理 | L1-L4 分级 | 20-lessons-learned |

### D.5 决策点体系（DP + DCP）

| 类型 | 数量 | 级别 | 定义位置 |
|------|------|------|---------|
| **Decision Point** | 7 个（DP0/DP0.5/DP0.7/DP1/DP2/DP3/DP4） | 任务级 | §6.2 |
| **DCP** | 6 个（Phase 0-5） | 阶段级 | §1.6 |
| **升级/降级** | L1↔L2↔L3↔L4 | 自治等级 | §1.4 |
| **Process Profile** | S/M/L/XL | 流程裁剪 | §1.6.9 |
| **Feature Depth Tier** | D1/D2/D3/D4 | 特性深度 | §1.6.8 关键特性深度分级 |

### D.6 防护体系（多层拦截）

| 层 | 机制 | 拦截能力 | 定义位置 |
|----|------|---------|---------|
| L1 AI 约束 | 规范声明 | 弱 | §1.2.1 |
| L2 Pre-commit | Git hook | 强 | §1.2.1 |
| L3 CI Gate | CI 门禁 | 强 | §1.2.1 |
| L4 Runtime | 代码防护 | 强 | §1.2.1 |
| 幻觉防护 | Example-Driven + Prompt Chaining + Progressive Disclosure + 两层审查 | 拦截率 100% | §3.2 |
| 45 种幻觉检测 | 8 大类（E/X/V/L/D/C/S/H） | 证据链验证 | 07-anti-hallucination §1 |

### D.7 安全体系

| 机制 | 定义位置 | 说明 |
|------|---------|------|
| P5 密钥不入代码 | §1.1 | pre-commit + SAST |
| P10 数据分级 | §1.1 | pre-send 扫描 |
| P17 输入校验 | §1.2 | 类型校验 + 边界检查 |
| P19 认证门禁 | §1.2 | 写端点认证 |
| 安全 Gate | §1.7.3 | 密钥/SQL/eval/路径 |
| DAST | 16-security-chaos §7 | L4+ 动态安全测试 |
| 混沌工程 | 16-security-chaos | L5+ 混沌注入 |

### D.8 全链路断链检查

| 链 | 上游 | 下游 | 连接点 | 状态 |
|----|------|------|--------|------|
| 需求→编码 | 需求分析 | Spec | P23 链 + DP0-1 | 完整 |
| Spec→开发 | Spec ready | TDD | P7 + Spec Validation | 完整 |
| 开发→审查 | 代码提交 | Multi-Pass | 19-multi-pass | 完整 |
| 审查→合并 | 全部 PASS | PR 合并 | Pipeline L0-L5 | 完整 |
| 合并→发布 | PR 合并 | Release | Release Gate + Cadence | 完整 |
| 发布→运维 | 部署 | 生命周期 | Deployment + Feedback | 完整 |
| 运维→反馈 | 用户反馈 | Phase 0 刷新 | 传导回 P0 | 完整 |
| 教训→注入 | 发现教训 | 规范/流程 | 48h 注入 | 完整 |
