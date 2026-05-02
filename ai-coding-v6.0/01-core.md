# AI Coding 规范 v6.0：核心规范

> 版本：v6.0 | 2026-05-02
> 定位：不可违反的核心原则 + 自治等级 + TDD + Spec 驱动 + 幻觉防护
> 关联：[00-philosophy.md](00-philosophy.md)（元规则）、[02-state-machine.md](02-state-machine.md)（可执行状态机）、[03-structured-constraints.md](03-structured-constraints.md)（结构化约束）

---

## 第 1 章：核心原则（P1-P24）

### 1.1 P1-P11：核心底线（不可违反）

**P1 商业驱动**
- 必须：每个 Spec 包含 `business_goal` 字段，描述商业目标
- 不得：创建无 `business_goal` 的 Spec
- 验证：Spec YAML frontmatter 中 `business_goal` 非空

**P2 DCP 门禁**
- 必须：每个 Phase 完成前记录 DCP 检查结果到 `ipd/phase-N/dcp-checklist.md`
- 不得：跳过 DCP 直接进入下一 Phase
- 必须：DCP 检查附带深度评分，由独立 Agent 执行
- 不得：由完成该 Phase 工作的 Agent 自评。Gate Checker 独立判定 PASS/FAIL
- 验证：checklist 全 PASS + `.gate/depth-score-{phase}.json` 每项 ≥ 2 + `scored_by` ≠ "self"

**P3 TDD 先行**
- 必须：测试先于实现，必须先失败（Red）再写实现（Green）
- 必须：测试 commit 在实现 commit 之前（不同 commit）
- 不得：测试和实现在同一 commit；跳过 Red 阶段
- 验证：`git log` 检查提交顺序 + `.gate/tdd-report.json` 检查 Red 记录

**P4 人工审查**
- 必须：每个 PR 有 AI Reviewer 结果（幻觉检测）+ Human Reviewer 签名
- 不得：无审查签名的 PR 合并到 main
- 验证：PR 描述中包含两者输出

**P5 密钥不入代码**
- 必须：密钥、密码、token 使用环境变量或密钥管理
- 不得：代码或配置文件中出现硬编码密钥
- 验证：pre-commit hook（gitleaks）+ CI SAST 扫描，零 CRITICAL

**P6 单一信息源**
- 必须：每个事实在一个地方定义，其他地方引用
- 不得：同一事实在多处定义
- 验证：CI 检查文档间引用链，无循环引用

**P7 Spec 驱动**
- 必须：AI 生成代码前读取对应 Spec 文件（`specs/F{NNN}-*.md`），状态为 `ready` 或 `in-progress`
- 不得：无 Spec 文件直接编码
- 验证：PR 描述引用 Spec 路径 + CI 检查 Spec 存在

**P8 最小批量**
- 必须：一次只生成一个函数或小模块
- 不得：单函数 > 50 行或单文件 > 200 行（不含测试）
- 验证：CI 检查新增函数行数和文件大小

**P9 Prompt 版本化**
- 必须：Prompt 存储在 `prompts/` 目录，包含 YAML frontmatter（id、version、model、status）
- 不得：使用未版本化的 Prompt 生成生产代码
- 验证：PR 描述声明 Prompt 版本 + `prompts/` 中存在对应文件

**P10 数据分级**
- 必须：发送给 AI 的数据经分类，Restricted 数据 pre-send 扫描拦截
- 不得：将密钥、PII、生产数据库内容发送给 AI
- 验证：pre-send hook 扫描，拦截 Restricted 数据

**P11 证据链**
- 必须：每个声明有 ≥ 2 条机器可验证证据，来自不同工具/来源
- 不得：证据链断裂（声明→证据无可追溯路径）
- 验证：`.gate/` 目录中每个声明有对应证据文件，交叉引用 ≥ 2 条

### 1.2 P12-P22：工程实践

**P12 环境一致性**
- 必须：开发环境通过声明式配置管理（`.mise.toml`、`Makefile`）
- 不得：靠运行时重试或手动安装来弥补环境差异
- 验证：`make check-env` 通过；新开发者能一键 `make setup`

**P13 错误不吞**
- 必须：所有错误必须处理或返回
- 不得：空错误处理（`//nolint:errcheck`、空 `catch`/`except`）
- 验证：`go vet ./...` 零问题 + pre-commit 拦截空错误处理

**P14 租户隔离**
- 必须：租户 ID 从请求上下文提取
- 不得：代码中出现硬编码租户字符串
- 验证：pre-commit 扫描硬编码租户模式

**P15 并发安全**
- 必须：共享状态使用 mutex 或 atomic 保护
- 不得：无保护地并发读写共享状态
- 验证：`go test -race ./...` 零数据竞争

**P16 资源清理**
- 必须：所有 map/channel/goroutine 有清理机制（TTL、上限、关闭信号）
- 不得：创建无清理逻辑的全局缓存或后台 goroutine
- 验证：内存泄漏测试通过

**P17 输入校验**
- 必须：所有外部输入类型校验 + 边界检查
- 不得：信任调用方输入
- 验证：模糊测试通过 + 非法输入返回 400

**P18 JSON 安全**
- 必须：SSE/HTTP 响应使用序列化函数
- 不得：字符串拼接 JSON
- 验证：CI 检查 SSE `data:` 后为合法 JSON

**P19 认证门禁**
- 必须：所有写端点（POST/PUT/DELETE）有认证和角色校验
- 不得：无认证的写端点上线
- 验证：集成测试验证未认证请求返回 401/403

**P20 速率保护**
- 必须：昂贵端点有速率限制
- 不得：无 rate limiter 的端点上线
- 验证：压力测试返回 429

**P21 数据一致性**
- 必须：DB 写入失败返回错误
- 不得：用空返回值或成功状态码掩盖写失败
- 验证：故障注入测试验证事务回滚

**P22 IP 不暴露**
- 必须：生产 IP/域名通过环境变量或配置注入
- 不得：代码中出现生产 IP 或域名
- 验证：pre-commit 扫描 IP 模式

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

#### 1.3.2 Solution Quality Gate（8 项检查，由独立 Agent 执行）

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
4. 失败方案写入 `lessons/`

### 1.4 P24：标准库优先

**P24 标准库优先**
- 必须：新依赖前证明标准库无法实现且已有依赖无法复用
- 不得：仅因"方便"引入新依赖
- 验证：PR 描述包含依赖引入理由

### 1.5 设计启发式（AI 可执行的架构思考）

**数据流分析**：数据从哪来 → 经过哪些转换 → 最终到哪 → 每步类型是否一致

**生命周期分析**：创建后如何读取 → 如何更新 → 如何删除/归档 → 如果从未更新会怎样

**时间维度分析**：第 1 次使用 → 第 10 次 → 第 1000 次 → 系统变好还是变差

**代码构造检查清单**（写入代码前必须执行）：

| 类别 | 检查项 |
|------|--------|
| 数据持久化 | INSERT/UPDATE 包含所有非空列；JSONB 用 `json.Marshal`；新增字段确认 migration 存在 |
| 字符串处理 | 格式化字符串中 `%` 正确转义；用户输入经 sanitization 后再拼入 SQL/log/URL |
| 并发安全 | 读写 map 有 mutex 保护；goroutine 中闭包变量已拷贝 |
| 输入校验 | 外部输入经类型校验 + 边界检查；路径参数防穿越 |
| 错误处理 | 所有错误被返回或处理；禁止 `//nolint:errcheck`；错误消息不泄露内部细节 |

### 1.6 多层执行机制

P12-P22 通过四层机制自动拦截：

| 层级 | 机制 | 示例 | 拦截能力 |
|------|------|------|---------|
| L1 AI 约束 | 规范声明 | 本文件 P13-P22 | 弱 |
| L2 Pre-commit | Git hook | 拦截空错误处理 | 强 |
| L3 CI Gate | CI 门禁 | `go test -race` | 强 |
| L4 Runtime | 代码防护 | 写操作返回 500 | 强 |

规则：每条原则至少 L1 + L2/L3/L4 之一。只有 L1 视为"未落地"。
状态机实现：见 [02-state-machine.md](02-state-machine.md)。

---

## 第 2 章：自治等级（L1-L4）

| 等级 | 名称 | 人类干预点 | 适用场景 |
|------|------|-----------|---------|
| **L1** | 辅助编码 | 每一步 | 新手团队、安全敏感 |
| **L2** | 半自主（默认） | 每个 PR 合并前 | 日常开发 |
| **L3** | 受限自主 | PR 合并前 + DCP | 夜间开发、成熟团队 |
| **L4** | 完全自主 | DCP + 定期审计 | 高成熟度、低风险 |

### 升级路径

| 升级 | 前置条件 |
|------|---------|
| L1 → L2 | ≥20 PR 无事故 + TDD ≥80% + 两层 Review + CI Gate |
| L2 → L3 | L2 ≥1 月 + 成功率 ≥70% + 幻觉率 <5% + 异步 DP |
| L3 → L4 | L3 ≥3 月 + 成功率 ≥85% + 审计 ≥95% + 零事故 + 回滚演练 |

### 降级条件

| 触发 | 降级目标 |
|------|---------|
| 生产安全事故 | L2 |
| 幻觉代码合并到 main | L2 |
| 审计 < 95% 连续 2 周（L4） | L3 |
| 自主成功率 < 70% 连续 2 周（L3） | L2 |
| TDD < 80% | L1 |
| 密钥泄露 | L1 |

### 与流程裁剪的关系

自治等级（L1-L4）控制"谁做"，流程裁剪（S/M/L/XL）控制"做多重"。两者正交。L4 跑 S 档 = 全自动小修，L4 跑 XL 档 = 全自动平台级重构。

---

## 第 3 章：流程裁剪档位（Process Profile）

| 档位 | 执行阶段 | DCP | 适用场景 |
|------|---------|-----|---------|
| **S** | 仅 Phase 3 | 0 | 单文件 ≤50 行，无 API/架构变更 |
| **M** | Phase 1→3 | 1 | 1-3 个 Spec |
| **L** | Phase 0→3 | 2 | 3-10 个 Spec / 架构变更 |
| **XL** | Phase 0→4 + Phase 5 前置 | 3+ | 10+ Spec / 平台级 / 生产发布 |

**不可裁剪项**（任何档位必须遵守）：P1-P11、P12-P22、TDD（P3）、安全底线（P5/P17/P19）。

**可裁剪项**：

| 维度 | S | M | L | XL |
|------|---|---|---|----|
| Phase 0 文档 | 跳过 | 跳过 | 完整 | 完整+外部验证 |
| Phase 1 文档 | 跳过 | 压缩（Kano+JTBD） | 完整 | 完整 |
| Phase 2 ATA/DFX | 跳过 | 跳过 | 完整 | 完整+独立评审 |
| 深度评分维度 | 0 | 2 | 4 | 4+ |
| Multi-Pass Review | 2 Pass | 3 Pass | 5 Pass | 5 Pass+审计 |
| 传导检查 | 跳过 | 仅下游 | 全链 | 全链+回溯 |

**S 档对 P23 的豁免**：可跳过"需求分析→架构适配→方案设计"，但仍需有效 Spec 文件 + P1-P11 合规 + P12-P22 合规。

**档位升级触发条件**：
- S → M：变更扩散 > 3 文件或引入新 API 端点
- M → L：涉及架构决策或 > 3 个 Spec
- L → XL：涉及平台级重构或 > 10 个 Spec

---

## 第 4 章：IPD 六阶段方法引擎

自治等级仅影响 Phase 3。Phase 0-2 和 Phase 4-5 的决策质量由方法论保障。

### Phase 0：市场洞察

方法：五看三定（行业/市场/客户/竞争/自己 → 目标/策略/路径）、BLM 模型、技术趋势雷达、VOC 分析、竞品范围确认（≥3 维度、≥1 非直接竞品）。
DCP：商业机会经过五看验证？排除伪需求？有差异化定位？

### Phase 1：概念定义

方法：$APPEALS、Kano 模型、QFD 矩阵、JTBD、价值曲线、核心竞争力画像（三层竞争力：入场券/拉开差距/杀手锏 + 竞品追赶预警 + 防守优先级）。
DCP：需求分类覆盖 Kano 三类型？QFD 矩阵完整？核心竞争力综合识别完成？

### Phase 2：详细规划

方法：DFX（可维护性/可扩展性/安全性/性能）、架构权衡分析(ATA)、WBS 分解、风险矩阵、里程碑规划。
DCP：DFX 全通过？架构经过权衡分析？WBS 到 Feature 粒度？Top 3 风险有缓解方案？

### Phase 3：AI 辅助开发

方法：TDD 先行(P3)、Spec 驱动(P7)、最小批量(P8)、Self-Correction ≤ 3 轮、两层审查(P4)。
DCP：TDD 合规率 ≥ 80%？幻觉率 < 5%？Spec 覆盖度 100%？

### Phase 4：验证发布

方法：E2E 测试、Beta 测试、GRTR（技术评审）、ADCP（可用性决策）、性能验收、安全验收、用户文档审查。
DCP：E2E 100% 通过？Beta 满意度达标？GRTR/ADCP 全通过？安全扫描无高危？

### Phase 5：生命周期

方法：客户反馈闭环、技术债管理、生命周期趋势分析、Lessons Learned、传导回 Phase 0。
DCP：反馈响应时间达标？技术债趋势可控？Lessons Learned 已提取？

### 阶段间变更传导（Phase Change Propagation）

IPD 六阶段是依赖链，不是顺序流水线。当任一 Phase N 产出物发生实质性变化时，必须执行传导检查：

1. **影响识别**：列出 Phase N+1 的核心假设，判断是否仍成立
2. **局部刷新**：重新生成受影响章节
3. **逐阶段传导**：从 Phase N+1 传导至 Phase 5
4. **记录**：写入 `ipd/phase-N/impact-log-{date}.md`

**触发传导的变化**：新增竞品、差异化定位改变、需求优先级重排、架构决策变更、风险矩阵更新。
**不触发传导的变化**：格式调整、错别字、不影响结论的措辞修改。

---

## 第 5 章：TDD 与质量保障

### 5.1 TDD 流程

```
读 Spec → 写测试 → 提交测试（CI 记录 Red）→ 写实现 → 测试通过（Green）→ 重构 → 全量验证 → 创建 PR
```

规则：
- 测试从 Spec 验收标准生成
- 测试和实现必须在不同 commit
- Red 阶段必须被记录

### 5.2 Self-Correction Loop（最多 3 轮）

```
失败 → Round 1 → 仍失败 → Round 2 → 仍失败 → Round 3 → 仍失败 → 停止，通知人工
```

规则：
- 每轮分析根因后最小修改
- 第 3 轮后标记 `[SELF-CORRECTION-EXHAUSTED]`
- 记录轮次到 `.gate/self-correction.json`
- 架构问题不使用自修（成功率 ~20%）

### 5.3 全量验证 Gate

流程：编译 → 全量测试 → lint → 失败则自修（最多 3 轮）

**覆盖率规则**：
- AC 覆盖（强制）：每个 AC ≥ 1 测试函数 + ≥ 2 证据项
- 新增代码（强制）：新函数/文件必须有测试
- 包覆盖率（趋势）：不得较基线下降 > 5%
- **测试深度评分**：每包按五维度评估——①边界条件 ②异常路径 ③并发安全 ④安全边界 ⑤业务行为正确性。1-5 分，≥ 3 合格
- 证据文件：`.gate/coverage.json` + `.gate/test-quality.json`

### 5.4 质量响应机制

| 级别 | 触发 | 动作 |
|------|------|------|
| L0 正常 | 一次通过率 > 80% | AI 自主推进 |
| L1 诊断 | 一次通过率 60-80% | 分析根因，重试（≤ 2 轮） |
| L2 增强 | 一次通过率 < 60% | 多 Agent 联合审查 |
| L3 人工决策 | 严重退化或架构分歧 | 人类提供决策，AI 继续编码 |

**禁止行为**：
- 不得以"质量降级"为由退回人工编码
- L3 阶段人类不提供编码工作，仅提供决策信息
- 连续 3 个 Feature 在 L0 完成 → 自动恢复 L0

---

## 第 6 章：Spec 驱动开发

### 6.1 Feature Spec 规范

每个 Feature 有且仅有一个 Spec 文件（`specs/F{NNN}-{name}.md`），包含：
- YAML frontmatter：type、id、name、version、status、priority、autonomy_level
- 正文：用户故事、验收标准（Gherkin 格式）、边界条件、数据模型、API 设计、非功能需求

### 6.2 Spec Validation Gate

| 验证项 | 检查要点 |
|--------|---------|
| 与需求一致性 | 每个需求条目至少有一个 AC 对应 |
| 与架构一致性 | 不违反任何 ADR |
| 验收标准可测试 | Gherkin 格式可执行 |
| 边界条件完整 | 正常路径 + ≥ 3 种异常路径 |
| 非功能需求明确 | 数值化，不得模糊描述 |

### 6.3 Spec 状态机

`draft → validated → ready → in-progress → done`（任一状态可 → `deprecated`）

| 转换 | 触发 | 执行者 |
|------|------|--------|
| draft → validated | Spec Validation Gate 通过 | AI + AI Reviewer |
| validated → ready | DCP 决策通过 | 人工 |
| ready → in-progress | Phase 3 开始 | AI |
| in-progress → done | TDD + Gate 全部通过 | AI |
| done → in-progress | 回归/修复 | AI |
| 任一状态 → deprecated | 需求取消 | 人工 |

---

## 第 7 章：AI 幻觉检测与防护

### 7.1 核心认识

AI 幻觉是 LLM 本质特征，**每次生成都可能发生**。防护目标是确保即使发生也不进入生产。

### 7.2 防护策略

| 策略 | 规则 |
|------|------|
| **Example-Driven** | 用真实项目代码示例替代规则描述 |
| **Prompt Chaining** | 复杂任务拆为：分析→设计→编码→验证，每步验证输出，失败最多重试 3 次 |
| **Progressive Disclosure** | P0（Spec、接口契约）每次加载；P1（相关源文件）按需加载；P2（历史）手动注入 |
| **两层审查** | AI Reviewer 检测幻觉 + Human Reviewer 专注业务逻辑 |

前置链：Prompt Chaining 用于编码阶段，必须先完成 P23 的 Requirement→Solution→Spec 链。

### 7.3 指标

| 指标 | 目标 | 告警 |
|------|:----:|------|
| 幻觉发生率 | < 5% | > 10% |
| 幻觉拦截率 | 100% | < 90% |
| 幻觉逃逸率 | 0% | > 0% |

### 7.4 45 种幻觉类型（8 大类）

| 类别 | 代码 | 描述 |
|------|------|------|
| **Existence** | E | 不存在的 API、库、符号 |
| **eXtension** | X | 错误的 API 签名、参数、返回类型 |
| **Version** | V | 不同版本特性混用 |
| **Logic** | L | 错误的业务逻辑或控制流 |
| **Dependency** | D | 缺失或错误的包版本 |
| **Context** | C | 代码与周围上下文不匹配 |
| **Security** | S | 脆弱模式、绕过检查 |
| **Hallucination** | H | 完全虚构的概念 |

### 7.5 检测清单

代码完成前验证：
1. 所有导入的函数/类在声明的库版本中存在
2. 所有函数调用使用正确的参数名和类型
3. 所有返回值被正确处理
4. 所有 import/require/from 引用已安装的包
5. 所有配置 key、环境变量、常量在代码库中有定义
6. 所有符号解析到实际定义

---

## 第 8 章：Gate Checker Agent

### 8.1 架构

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

### 8.2 权限约束

| 约束 | 说明 |
|------|------|
| **只读** | 不得 Edit、Write 或修改任何代码 |
| **独立上下文** | 不得与 Executor 共享同一对话上下文 |
| **输出文件** | 验证结果写入 `.gate/gate-report-{date}.md` |

### 8.3 Gate 检查项

| Gate | 检查内容 | 证据来源 |
|------|---------|---------|
| TDD Gate | 提交顺序、Red→Green、AC 覆盖 | git log + `.gate/tdd-report.json` |
| Spec Gate | Spec 存在、状态正确、API 对齐 | `specs/` 文件 + 代码对比 |
| IPD 传导 Gate | 上游变更触发下游刷新 | `ipd/phase-N/` 文件 |
| 安全 Gate | 密钥、SQL 拼接、eval/exec | gitleaks + 代码扫描 |
| 质量 Gate | 编译、vet、test、lint、覆盖率 | 构建输出 + coverage |
| 幻觉 Gate | API 存在性、依赖、符号解析 | 编译 + 符号解析 |
| Self-Correction Gate | 轮次≤3 | `.gate/self-correction.json` |
| DCP Gate | checklist PASS/FAIL + 深度评分独立性 | `ipd/phase-N/dcp-checklist.md` |

### 8.4 触发时机

| 时机 | 触发方式 |
|------|---------|
| Executor 完成一轮编码/修复 | Executor 主动调用 |
| PR 创建前 | CI Pipeline L3 层自动调用 |
| IPD Phase 转换 | Phase N → Phase N+1 时自动调用 |

---

## 第 9 章：Multi-Pass Review Protocol

每个 IPD Phase 产出完成后，执行 **6 轮审查**，对 **7 个 Gate** 的 **25 个检查项** 逐项进行 **3 轮独立验证**：

| Pass | 名称 | 执行者 | 视角 |
|------|------|--------|------|
| P1 | Self-Verify | 作者/Executor | 完整性 |
| P2 | Cross-Verify | 独立 Agent | 上下游一致性 |
| P3 | Adversarial Review | 独立 Agent | 竞品/审计/攻击者视角 |
| P4 | Gate Checker | 独立 Gate Checker Agent | 规范合规（只读）|
| P5 | Human Reviewer | 人类 | 战略对齐 + 风险接受度 |
| P6 | Depth Score | 独立 Agent（critic/architect） | 深度质量 |

审查次数：7 Gate × ~5 检查项 × 3 轮验证 × 6 Pass = 630 次。

**逃逸条件**：微小变更（≤5 行单文件）、纯格式变更、紧急 Hotfix 可跳过部分 Pass，但必须在 Gate Report 中注明原因。

---

## 第 10 章：Lessons Learned Protocol

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

## 第 11 章：深度评分与基线提升

### 评分规则

每个 Phase 的 DCP 深度评分表包含 3-5 个维度，每个维度 0-3 分：

| 分数 | 定义 | 说明 |
|------|------|------|
| 0 | 未做 | 完全未涉及 |
| 1 | 表面层 | 有输出但停留在"有无对比" |
| 2 | 机制层 | 拆解了"怎么做"和"为什么" |
| 3 | 批判层 | 指出了"做得不好的地方" |

**通过条件**：每项 ≥ 2 分，且总分 ≥ 该阶段满分 × 60%。

### 关键特性深度分级

| 级别 | 定义 | 通过线 | Multi-Pass | 审查视角 |
|------|------|--------|-----------|---------|
| D1 核心特性 | 直接影响收入/安全/合规/核心用户体验 | 每项 ≥ 2.5 分，总分 ≥ 75% | 6 Pass 全执行 | 3+ 对抗视角 |
| D2 重要特性 | 影响次要用户体验/性能/可扩展性 | 每项 ≥ 2 分，总分 ≥ 60% | 5 Pass | 2 对抗视角 |
| D3 一般特性 | 内部工具/管理后台/边缘功能 | 每项 ≥ 1.5 分，总分 ≥ 50% | 3 Pass（P1+P4+P5） | 1 对抗视角 |
| D4 维护特性 | Bug 修复/格式调整/文档更新 | 每项 ≥ 1 分 | S 档 | 跳过 |

级别由 Spec 的 YAML frontmatter `depth_tier` 字段声明，由 Tech Lead 在 DCP 中确认。未声明默认按 D2 执行。

### 基线提升机制

1. 每个 Feature 完成后，记录该 Phase 的最高得分到 `.gate/depth-baselines.json`
2. 同一 Phase 的后续 DCP 评分不得低于已有基线
3. 发现的盲区必须写入该 Phase 的评分维度，成为永久新维度
4. 某维度连续 3 个 Feature 都拿到 3 分，通过线从 ≥ 2 提升到 ≥ 3
5. 单维度基线最高为 2 分（不得提升到 3 分）
6. 新项目所有维度初始基线 = 1 分

### D1 核心特性额外审查要求

| 要求 | 说明 |
|------|------|
| P3 对抗视角 | 必须包含"如果安全团队看这个设计，会质疑什么" |
| P4 Gate Checker 模型 | 必须使用 sonnet 或 opus（不得用 haiku） |
| P6 深度评分 | "自身盲区识别"维度必须 ≥ 3 分 |
| 额外产出 | `.gate/d1-risk-assessment.json`，包含 ≥3 条风险分析 |
| Lessons 引用 | 必须引用 ≥2 条 open 教训 |

**级别升级触发**：安全/合规相关自动升级为 D1；涉及用户数据/隐私自动升级为 D1；P0 事故修复自动升级为 D2。

### 独立 Agent 验证

- 深度评分必须由独立 Agent 执行，不得与完成该 Phase 工作的 Agent 共享对话上下文
- 评分报告必须包含 `scored_by: "independent {agent_type}"`
- `scored_by` 为 "self" 标记 `[DEPTH-SELF-SCORED]`，判定无效
- 独立 Agent 评分与自评差异 ≥ 2 分时，以独立 Agent 评分为准

### 深度评分异常模式检测

| 异常模式 | 检测逻辑 | 动作 |
|---------|---------|------|
| 全 3 分 | 所有维度都是 3 分 | 标记 `[DEPTH-SUSPECT]`，要求人工复核 |
| 全 2 分 + 变更 > 5 文件 | 所有维度都是 2 分，涉及实质变更 | 标记 `[DEPTH-ROBOTIC]`，要求至少 1 项差异化评分 |
| 评分与缺陷不一致 | 评分 ≥ 80% 但后续发现 ≥ 3 个设计缺陷 | 标记 `[DEPTH-INVALID]`，回溯调整基线 |

### 通用独立验证原则

> **不得由产出物的创建者对该产出物进行 PASS/FAIL 判定。所有 Gate 的 PASS/FAIL 必须由独立 Agent 或自动化工具决定。**
>
> 适用于：DCP Checklist、Solution Quality Gate、Spec Validation Gate、IPD 传导检查、部署审计完整性验证。
> 自动化工具（compiler、gitleaks、go test、lint）判定视为独立。

---

## 第 12 章：Prompt 管理

### 12.1 Prompt 版本化（P9）

规则：
- 必须：Prompt 存储在 `prompts/` 目录，包含 YAML frontmatter（id、version、model、temperature、feature、status）
- 不得：使用未版本化的 Prompt 生成生产代码；从 URL 或外部服务加载 Prompt
- 验证：PR 描述声明使用的 Prompt 版本；`prompts/` 中存在对应文件

### 12.2 Prompt 安全

- Spec 中的用户输入不得直接拼接到 Prompt 中
- 每季度审查 Prompt 仓库，删除过时 Prompt

---

## 第 13 章：人与 AI 的分工

### 13.1 基础分工

| 活动 | 人类角色 | AI 角色 |
|------|---------|---------|
| 战略/产品/架构决策 | 决策者 | 信息整理、方案对比 |
| Spec 编写 | 审核者 | 草稿生成（L2+） |
| 测试/编码 | 审核者 | 执行者 |
| 安全审查 | 决策者 | 辅助扫描 |
| 部署运维 | 监督者（L1-L2）/ 审计者（L4） | 执行者 |

### 13.2 Decision Point

| DP | 时机 | 拦截的错误类型 |
|----|------|---------------|
| DP0 | 需求分析完成后 | 需求理解偏差 |
| DP0.5 | 架构适配完成后 | 架构不兼容 |
| DP0.7 | 方案设计完成后 | 方案不可行 |
| DP1 | AI 分析完代码结构后 | AI 误解需求 |
| DP2 | AI 给出技术方案后 | 过度工程 |
| DP3 | 全部完成后 | 功能不完整 |
| DP4 | Hotfix 时 | 修复引入新问题 |

L3 异步模式：DP1/DP2 阻塞，DP3 非阻塞，超时 2 小时自动降级为非阻塞。
DCP 与 DP 的区别：DCP = 阶段级（宏观），DP = 任务级（微观），两者互补。

---

## 附录 A：快速参考

```
核心原则：
P1 商业驱动 ── P2 DCP 门禁 ── P3 TDD 先行 ── P4 人工审查 ── P5 密钥不入
P6 单一信息 ── P7 Spec 驱动 ── P8 最小批量 ── P9 Prompt 版 ── P10 数据分级
P11 证据链 ── P12-P22 工程实践 ── P23 需求→Spec 链 ── P24 标准库优先

自治等级：L1 辅助 ── L2 半自主（默认）── L3 受限自主 ── L4 完全自主
流程裁剪：S（单文件）── M（1-3 Spec）── L（3-10 Spec）── XL（10+ Spec）
TDD：Red → Green → Refactor
幻觉防护：Example-Driven + Prompt Chaining + Progressive Disclosure + 两层审查
深度评分：0 未做 → 1 表面 → 2 机制 → 3 批判。每项 ≥ 2，总分 ≥ 60%
特性深度：D1 核心 → D2 重要 → D3 一般 → D4 维护
Multi-Pass：6 Pass × 7 Gate × 3 轮 = 630 次验证
```
