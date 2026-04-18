# AI Coding 规范 v5.4：数据治理与国际化（i18n/A11y）

> 版本：v5.4 | 2026-04-18
> 定位：大规模 Auto-Coding 场景下的数据血缘、数据质量、GDPR 合规、国际化、可访问性
> 前置：[01-core-specification.md](01-core-specification.md) P10 数据分级/P11 证据链、[04-security-governance.md](04-security-governance.md) 安全底线、[08-database-migration.md](08-database-migration.md) 数据变更管理

---

## 第 1 章：数据治理

### 1.1 数据血缘（Data Lineage）

**核心原则：每条数据在 Auto-Coding 流水线中的来源、变换和去向必须可追溯。**

#### 1.1.1 血缘追踪要求

| 层级 | 要求 | 实现方式 |
|------|------|---------|
| **来源追踪** | 每条输入数据标注来源系统、时间、责任人 | 元数据标签 + 时间戳 |
| **变换记录** | 每次 AI 生成、转换、聚合操作记录输入→输出映射 | `.gate/lineage/` 日志 |
| **去向追踪** | 输出数据写入目标、消费方、保留期限必须声明 | 数据出口登记表 |

#### 1.1.2 AI 生成的数据血缘

AI 生成的代码、Spec、测试用例属于"衍生数据"，必须记录：

```
┌──────────────────────────────────────────────────────┐
│ 数据血缘记录模板                                       │
├──────────────────────────────────────────────────────┤
│ 来源：  {需求文档 | Spec 文件 | 现有代码 | 用户输入}   │
│ 变换：  {AI 模型} @ {版本} + {Prompt 文件}             │
│ 输出：  {生成文件列表}                                 │
│ 校验：  {测试覆盖 | 人工审查 | CI 验证结果}              │
│ 时间：  {生成时间戳}                                    │
│ 证据：  {.gate/ 目录下的验证产物}                       │
└──────────────────────────────────────────────────────┘
```

**AI 规则：** AI 生成任何代码文件后，必须自动将血缘元数据写入 `.gate/lineage/{filename}.json`，包含 `source_files`、`prompt_version`、`model_id`、`timestamp` 字段。

#### 1.1.3 血缘完整性检查

CI 必须在 L3 门禁中执行：

- [ ] 所有生成文件有对应的血缘记录
- [ ] 血缘记录中的 source_files 指向实际存在的文件
- [ ] 证据链（P11）不断裂：source → prompt → output → verification

### 1.2 数据质量检查

#### 1.2.1 质量维度

| 维度 | 检查项 | 自动化方式 |
|------|--------|-----------|
| **完整性** | 必填字段非空、关联数据存在 | Schema 校验 + 外键检查 |
| **准确性** | 数值范围合理、枚举值合法 | 断言测试 + 边界值验证 |
| **一致性** | 跨系统数据一致、格式统一 | 一致性校验脚本 |
| **时效性** | 数据在有效期内、非过期缓存 | TTL 检查 + 时间戳对比 |
| **唯一性** | 无重复记录、主键不冲突 | 唯一约束 + 去重检测 |

#### 1.2.2 AI 代码生成的质量门禁

在 Spec 驱动流程中，AI 生成代码后必须通过：

```
┌─────────────────────────────────┐
│ AI 数据质量门禁                   │
├─────────────────────────────────┤
│ 1. 输入数据验证：所有输入参数有    │
│    类型标注 + 范围约束             │
│ 2. 输出数据验证：返回值有明确的    │
│    成功/失败/边界分支              │
│ 3. 空值防御：null/undefined 有    │
│    明确处理路径，不静默传播         │
│ 4. 数据转换安全：类型转换不丢失    │
│    精度，不截断关键信息             │
│ 5. 错误数据隔离：脏数据进入时      │
│    快速失败，不污染下游             │
└─────────────────────────────────┘
```

**违反后果：** 未通过质量门禁的生成结果不得进入 PR 阶段，自动标记 `[DATA-QUALITY-FAILED]`。

### 1.3 PII 处理（超越 P10）

P10 定义了数据分级，本节定义 PII（个人身份信息）的具体处理规则。

#### 1.3.1 PII 分类

| 类别 | 示例 | 处理要求 |
|------|------|---------|
| **直接标识符** | 姓名、身份证号、邮箱、手机号 | 必须加密存储，传输中必须 TLS |
| **准标识符** | 邮编、出生日期、性别、职业 | 组合使用需脱敏，单独使用需记录 |
| **敏感 PII** | 生物特征、医疗记录、宗教信仰 | 禁止发送给 AI，禁止明文存储 |
| **衍生 PII** | 用户画像、行为分析结果 | 按来源数据的最高级别处理 |

#### 1.3.2 AI 场景下的 PII 防护

```
┌──────────────────────────────────────────────────┐
│ PII 处理规则（Auto-Coding 场景）                   │
├──────────────────────────────────────────────────┤
│ 禁止行为：                                        │
│ · 将包含 PII 的生产数据发送给 AI 提供者              │
│ · 在测试数据中使用真实的 PII                        │
│ · 在日志中打印未脱敏的 PII                          │
│ · 在 AI 生成的代码中硬编码 PII 处理逻辑               │
│                                                    │
│ 必须行为：                                        │
│ · 测试数据使用合成数据（Synthetic Data）             │
│ · 日志中的 PII 必须脱敏（掩码/哈希）                  │
│ · 开发环境数据必须经过脱敏管道                        │
│ · AI 生成的数据访问代码必须包含权限检查                │
└──────────────────────────────────────────────────┘
```

#### 1.3.3 脱敏标准

| 数据类型 | 脱敏方式 | 示例 |
|----------|---------|------|
| 邮箱 | 保留域名，掩码用户名 | `j***@example.com` |
| 手机号 | 保留前 3 后 4 | `138****5678` |
| 身份证 | 保留前 6 后 4 | `110105********1234` |
| 姓名 | 保留姓，名用 * | `张*` |
| 地址 | 保留省市，详细掩码 | `北京市朝阳区***` |

#### 1.3.4 合成数据规范

测试和开发环境必须使用合成数据：

- 合成数据必须保持与生产数据相同的 schema 和约束
- 合成数据中的 PII 必须是虚构的、无法反向关联到真实个人的
- 合成数据生成工具必须在安全清单中登记
- AI 代码审查时，必须验证测试数据不是生产数据的副本

### 1.4 数据保留策略

#### 1.4.1 保留周期矩阵

| 数据类型 | 保留期限 | 超期处理 | 法律依据 |
|----------|---------|---------|---------|
| AI 会话日志 | 90 天 | 自动删除 | 内部政策 |
| PR 记录 + 代码 | 项目生命周期 + 3 年 | 归档 | 审计要求 |
| CI/CD 构建产物 | 180 天 | 自动清理 | 内部政策 |
| `.gate/` 证据产物 | 项目生命周期 + 1 年 | 归档 | P11 证据链 |
| 用户业务数据 | 按业务定义 | 按 1.5 节 GDPR 规则 | GDPR/法规 |
| AI Prompt 记录 | 180 天 | 自动删除 | P9 Prompt 版本化 |
| 审计日志 | 7 年 | 归档到冷存储 | 合规要求 |

#### 1.4.2 自动清理机制

```yaml
# .omc/retention-policy.yaml — 声明式数据保留配置
policies:
  - scope: ".gate/evidence/"
    max_age_days: 365
    action: archive_to_cold_storage
  - scope: ".omc/logs/"
    max_age_days: 90
    action: delete
  - scope: "build/artifacts/"
    max_age_days: 180
    action: delete
  - scope: "prompts/"
    max_age_days: 180
    action: delete
```

**AI 规则：** AI 生成清理脚本时，必须：
1. 先列出即将超期的数据（dry-run 模式）
2. 清理操作必须是幂等的
3. 清理前必须检查数据是否被其他系统引用
4. 清理操作本身必须记录审计日志

### 1.5 GDPR 合规

#### 1.5.1 GDPR 核心权利映射

| GDPR 权利 | Auto-Coding 实现 | 责任方 |
|-----------|-----------------|--------|
| **知情权（Art.13-14）** | 数据收集点必须有隐私声明引用 | 应用开发者 |
| **访问权（Art.15）** | 提供数据导出 API，返回用户全部数据 | 后端服务 |
| **更正权（Art.16）** | 提供数据更新端点，记录变更历史 | 后端服务 |
| **删除权（Art.17）** | 软删除 + 物理删除双机制（见 1.5.3） | 后端服务 + DBA |
| **可携带权（Art.20）** | 导出标准格式（JSON/CSV） | 后端服务 |
| **反对权（Art.21）** | 提供 opt-out 机制，停止处理 | 应用开发者 |

#### 1.5.2 AI 代码生成的 GDPR 合规规则

AI 在生成涉及个人数据的代码时，必须自动包含：

1. **数据处理记录**：每个数据处理函数必须记录 `purpose`、`legal_basis`、`retention_period`
2. **同意管理**：涉及用户同意的流程必须有明确的同意记录、撤回机制
3. **DPIA 标记**：AI 识别到高风险数据处理时，必须在代码注释中标注 `[DPIA-REQUIRED]`
4. **跨境传输保护**：涉及数据跨境的代码路径必须标注 `[CROSS-BORDER]`

```python
# AI 生成的数据处理函数示例 — 必须包含 GDPR 元数据
@data_processor(
    purpose="user_profile_management",
    legal_basis="consent",       # GDPR Art.6(1)(a)
    retention_period="P2Y",      # ISO 8601 持续时间
    data_categories=["profile", "contact"],
    cross_border=False
)
def update_user_profile(user_id: str, data: ProfileUpdate):
    """[DPIA-LOW] Standard profile update — risk assessment completed."""
    ...
```

#### 1.5.3 数据删除机制

```
用户发起删除请求
        │
        ▼
┌──────────────────────┐
│ 1. 软删除（立即）      │  — 标记 is_deleted，业务不可见
│    保留期：30 天       │
└──────────────────────┘
        │
        ▼
┌──────────────────────┐
│ 2. 匿名化（30 天后）   │  — PII 替换为不可逆哈希
│    统计用途数据保留     │
└──────────────────────┘
        │
        ▼
┌──────────────────────┐
│ 3. 物理删除（90 天后） │  — 从主存储和备份中擦除
│    法律保留除外        │
└──────────────────────┘
```

**法律保留例外：** 涉及财务、医疗、法律合规的数据，在法定保留期内不得物理删除，仅执行匿名化。

---

## 第 2 章：数据备份与恢复

### 2.1 备份策略

#### 2.1.1 分层备份架构

| 层级 | 对象 | 频率 | 保留 | 存储位置 |
|------|------|------|------|---------|
| **L1 实时** | 事务日志（WAL/Binlog） | 持续 | 7 天 | 异地同步 |
| **L2 增量** | 变更数据块 | 每小时 | 30 天 | 跨区域 |
| **L3 全量** | 完整数据库快照 | 每日 | 90 天 | 冷存储 |
| **L4 归档** | 合规归档数据 | 每月 | 7 年 | 不可变存储（WORM） |

#### 2.1.2 Auto-Coding 特有的备份对象

除业务数据外，以下 Auto-Coding 产物也必须纳入备份：

| 备份对象 | 重要性 | 备份频率 | 恢复优先级 |
|----------|--------|---------|-----------|
| `.gate/` 证据产物 | CRITICAL | 每次 CI 完成后 | P0 — 证据链断裂=合规失效 |
| `specs/` 设计文档 | HIGH | 每次变更后 | P1 |
| `prompts/` Prompt 记录 | HIGH | 每次变更后 | P1 — P9 要求 |
| 代码仓库 | CRITICAL | 实时（Git 多副本） | P0 |
| AI 会话日志 | LOW | 每日 | P3 — 仅用于审计 |
| 合成数据集 | MEDIUM | 每周 | P2 |

### 2.2 RPO/RTO 目标

#### 2.2.1 恢复指标

| 系统/数据 | RPO（最大数据丢失） | RTO（最大恢复时间） | 恢复方式 |
|-----------|-------------------|-------------------|---------|
| 生产数据库 | ≤ 15 分钟 | ≤ 1 小时 | PITR（时间点恢复） |
| 代码仓库 | ≤ 0（不丢失） | ≤ 15 分钟 | 多副本自动切换 |
| `.gate/` 证据 | ≤ 1 小时 | ≤ 2 小时 | L3 全量恢复 |
| CI/CD 状态 | ≤ 4 小时 | ≤ 4 小时 | 重新触发 Pipeline |
| 配置文件 | ≤ 24 小时 | ≤ 1 小时 | Git 历史恢复 |

#### 2.2.2 自动验证

CI 每周必须执行一次备份完整性检查：

```bash
#!/bin/bash
# .omc/scripts/verify-backup.sh
# 验证备份完整性 — CI 定时任务执行

echo "=== Backup Integrity Check ==="

# 1. 验证备份文件存在且非空
# 2. 验证备份文件校验和与记录一致
# 3. 验证最近 24h 的增量备份链完整
# 4. 随机抽样恢复测试（小型数据集）

# 输出：PASS/FAIL + 详情
# 失败时触发告警
```

### 2.3 恢复演练

#### 2.3.1 演练频率

| 场景 | 频率 | 参与方 | 验证标准 |
|------|------|--------|---------|
| **单表恢复** | 每月 | 运维 + AI 辅助 | 数据完整性 100% |
| **全库 PITR** | 每季度 | 运维 + DBA | RPO/RTO 达标 |
| **跨区域灾备** | 每半年 | 全团队 | 业务恢复验证 |
| **AI 证据链恢复** | 每季度 | AI + 人工验证 | `.gate/` 数据完整 |

#### 2.3.2 演练流程

```
┌──────────────────────────────────────┐
│ 1. 选择恢复场景（随机或定向）          │
│ 2. 模拟故障（断开源/删除测试数据）     │
│ 3. 执行恢复流程（按 Runbook）          │
│ 4. 验证数据完整性（校验和 + 抽样）     │
│ 5. 记录实际 RPO/RTO                   │
│ 6. 对比目标值，生成报告                │
│ 7. 修复发现的问题，更新 Runbook        │
└──────────────────────────────────────┘
```

#### 2.3.3 AI 辅助恢复

L3/L4 Auto-Coding 场景下，AI 可以参与恢复流程：

- **允许：** 读取备份、执行恢复脚本、验证数据完整性、生成恢复报告
- **禁止：** 自主决定恢复策略、跳过验证步骤、修改恢复后的数据
- **要求：** 所有 AI 执行的恢复操作必须记录到审计日志，包含时间戳、操作、结果

---

## 第 3 章：国际化（i18n）

### 3.1 多语言支持

#### 3.1.1 语言架构原则

**核心原则：代码与文本分离，所有用户可见文本必须通过 i18n 框架管理。**

| 原则 | 规则 | 违反后果 |
|------|------|---------|
| **零硬编码文本** | 代码中不得出现用户可见的硬编码字符串 | AI Reviewer 拦截 |
| **单一翻译源** | 翻译文件是用户文本的唯一信息源（P6） | CI 阻塞 |
| **默认语言完整** | 默认语言（en-US）必须有 100% 翻译覆盖 | PR 拒绝 |
| **翻译缺失优雅降级** | 缺失翻译时回退到默认语言，不崩溃 | 运行时保护 |

#### 3.1.2 翻译文件结构

```
locales/
├── en-US/
│   ├── common.json        # 通用翻译
│   ├── auth.json          # 认证模块
│   └── dashboard.json     # 仪表板模块
├── zh-CN/
│   ├── common.json
│   ├── auth.json
│   └── dashboard.json
├── ja-JP/
│   └── ...
└── ar-SA/                 # RTL 语言
    └── ...
```

**AI 规则：** AI 生成包含用户可见文本的代码时，必须：
1. 使用 i18n 函数/组件（如 `t('key')`、`<Trans>`）包裹文本
2. 自动生成对应的翻译 key 到默认语言文件
3. 翻译 key 命名规范：`{module}.{component}.{element}`，如 `auth.login.submit_button`

#### 3.1.3 AI i18n 代码生成规则

```
┌──────────────────────────────────────────────────┐
│ AI i18n 生成规则                                  │
├──────────────────────────────────────────────────┤
│ 触发条件：生成包含用户可见文本的代码                │
│                                                    │
│ 必须执行：                                        │
│ 1. 识别所有用户可见文本（错误消息、按钮、标签、      │
│    提示、占位符、通知）                             │
│ 2. 提取文本到翻译文件，生成结构化 key               │
│ 3. 用 i18n 函数替换原始文本                        │
│ 4. 处理复数形式（使用 ICU MessageFormat）           │
│ 5. 处理日期/数字/货币格式（使用区域感知格式化）      │
│                                                    │
│ 禁止：                                            │
│ · 在代码中硬编码任何用户可见文本                     │
│ · 使用字符串拼接构建翻译文本                        │
│ · 假设所有语言的文本长度相同                         │
│ · 在 CSS 中使用固定宽度限制文本容器                  │
└──────────────────────────────────────────────────┘
```

#### 3.1.4 复数与性别处理

AI 生成涉及复数或性别的文本时，必须使用 ICU MessageFormat：

```json
{
  "dashboard.item_count": "{count, plural, =0{No items} =1{One item} other{# items}}",
  "user.greeting": "{gender, select, male{Hello Mr. {name}} female{Hello Ms. {name}} other{Hello {name}}}"
}
```

**注意：** 不同语言的复数规则不同（中文无复数变化，阿拉伯语有 6 种复数形式），AI 不得假设英文复数规则适用于所有语言。

### 3.2 日期/时间/数字格式化

#### 3.2.1 格式化规则

| 类型 | 存储格式 | 显示格式 | AI 生成规则 |
|------|---------|---------|------------|
| **日期** | ISO 8601 (`2026-04-18`) | 区域感知（`2026/04/18` vs `04/18/2026`） | 使用 `Intl.DateTimeFormat` 或等效 |
| **时间** | UTC 时间戳 | 区域时区 + 12/24 小时制 | 服务端存 UTC，客户端按 locale 转换 |
| **数字** | 原生数值类型 | 区域分组符（`1,000` vs `1.000`） | 使用 `Intl.NumberFormat` 或等效 |
| **货币** | 最小货币单位（整数） | 区域货币符号 + 小数位 | 服务端计算，客户端格式化 |
| **百分比** | 小数（0.15） | 区域格式（`15%` vs `15 %`） | 使用 `Intl.NumberFormat` |

#### 3.2.2 AI 格式化代码生成规则

```javascript
// ✅ 正确 — AI 应该生成的代码
function formatPrice(amount: number, currency: string, locale: string) {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount / 100); // 从最小单位转换
}

// ❌ 错误 — AI 不得生成的代码
function formatPrice(amount: number) {
  return '$' + (amount / 100).toFixed(2);  // 硬编码货币和格式
}
```

**AI 规则：**
1. 所有日期/时间在存储层必须是 UTC，显示层按 locale 转换
2. 不得在代码中硬编码时区（除系统级 UTC 转换外）
3. 数字格式化必须使用区域感知的 API，不得手动添加千位分隔符
4. 货币计算必须使用整数（最小货币单位）避免浮点精度问题

### 3.3 RTL 布局支持

#### 3.3.1 RTL 适配要求

| 场景 | LTR 行为 | RTL 行为 | AI 生成规则 |
|------|---------|---------|------------|
| **文本对齐** | `text-align: left` | `text-align: right` | 使用 `start/end` 代替 `left/right` |
| **Flex 方向** | `flex-direction: row` | 自动翻转 | 使用 `row` + 逻辑属性 |
| **Margin/Padding** | `margin-left` | `margin-right` | 使用 `margin-inline-start` |
| **图标方向** | 箭头向右 | 箭头向左 | 镜像翻转方向性图标 |
| **导航顺序** | 从左到右 | 从右到左 | Tab 顺序自动适配 |

#### 3.3.2 CSS 逻辑属性

AI 生成 CSS/样式代码时，必须使用逻辑属性：

```css
/* ✅ 正确 — 使用逻辑属性 */
.container {
  padding-inline-start: 16px;   /* 自动适配 LTR/RTL */
  padding-inline-end: 8px;
  border-inline-start: 1px solid #ccc;
  text-align: start;
}

/* ❌ 错误 — 使用物理方向 */
.container {
  padding-left: 16px;   /* RTL 下不正确 */
  padding-right: 8px;
  border-left: 1px solid #ccc;
  text-align: left;
}
```

#### 3.3.3 RTL 检查清单

AI 生成 UI 代码后，必须自动检查：

- [ ] 所有方向性 CSS 使用逻辑属性（start/end 而非 left/right）
- [ ] 方向性图标（箭头、前进/后退）有 RTL 变体
- [ ] 布局翻转后视觉层级仍然正确
- [ ] Tab 导航顺序在 RTL 下合理
- [ ] 文本溢出处理在 RTL 下正确（截断在正确的一侧）

### 3.4 时区与日历系统

#### 3.4.1 时区处理

| 层级 | 规则 |
|------|------|
| **存储层** | 所有时间以 UTC 存储 |
| **API 层** | 传输 ISO 8601 格式，标注时区偏移 |
| **展示层** | 按用户本地时区展示 |
| **业务逻辑** | 基于 UTC 计算，避免 DST 陷阱 |

**AI 规则：** AI 在处理时间相关逻辑时：
1. 禁止在比较、计算、存储时使用本地时区
2. 涉及"天"的业务逻辑必须考虑时区边界（如 `2026-04-18` 在不同时区代表不同时间段）
3. 涉及周期性任务（cron）必须明确时区

#### 3.4.2 日历系统

| 日历 | 使用区域 | AI 注意事项 |
|------|---------|------------|
| **公历（Gregorian）** | 全球通用 | 默认日历系统 |
| **农历（Chinese）** | 中国、部分东亚 | 节日日期转换需要特殊处理 |
| **伊斯兰历（Hijri）** | 中东、北非 | 月份长度不固定，每年偏移约 11 天 |
| **日本和历** | 日本 | 年号变更时需要更新 |

**AI 规则：** 涉及日历显示的代码，必须使用 `Intl.DateTimeFormat` 的 `calendar` 选项，不得手动实现日历转换。

---

## 第 4 章：可访问性（A11y）

### 4.1 WCAG 合规

#### 4.1.1 合规目标

| 等级 | 目标 | 适用场景 |
|------|------|---------|
| **AA（最低）** | WCAG 2.2 Level AA 所有成功标准 | 所有面向用户的产品 |
| **AAA（推荐）** | 关键路径满足 AAA | 公共服务、政府项目 |
| **A（绝对底线）** | 所有 A 级标准必须满足 | 任何情况不得违反 |

#### 4.1.2 AI 代码生成的 WCAG 规则

```
┌──────────────────────────────────────────────────┐
│ AI A11y 生成规则（WCAG 2.2 AA）                    │
├──────────────────────────────────────────────────┤
│ 1. 感知性（Perceivable）                           │
│    · 所有非文本元素有替代文本（alt/aria-label）     │
│    · 色彩对比度 ≥ 4.5:1（正常文本）/ 3:1（大文本）  │
│    · 信息不得仅通过颜色传达                         │
│    · 内容在不同缩放倍数（200%）下可用                │
│                                                    │
│ 2. 操作性（Operable）                              │
│    · 所有功能可通过键盘操作                         │
│    · 焦点顺序合理且可见                             │
│    · 无自动播放的内容，或提供暂停机制                │
│    · 无时间限制，或提供延长机制                      │
│                                                    │
│ 3. 理解性（Understandable）                        │
│    · 页面语言正确声明（lang 属性）                   │
│    · 导航一致且可预测                               │
│    · 输入错误有明确提示和纠正建议                    │
│    · 表单字段有明确的标签                            │
│                                                    │
│ 4. 健壮性（Robust）                                │
│    · 有效的 HTML 标记                               │
│    · ARIA 属性使用正确                              │
│    · 状态变化有通知机制                              │
│    · 与主流辅助技术兼容                              │
└──────────────────────────────────────────────────┘
```

### 4.2 屏幕阅读器支持

#### 4.2.1 ARIA 规则

| 规则 | 要求 | 示例 |
|------|------|------|
| **语义 HTML 优先** | 优先使用 `<button>` 而非 `<div onclick>` | 语义元素自带 ARIA 角色 |
| **ARIA 角色匹配** | `role` 必须匹配元素的实际行为 | `<div role="button">` 必须有 `tabindex` 和键盘处理 |
| **ARIA 属性完整** | `aria-*` 属性值必须正确反映状态 | `aria-expanded="true/false"` 随状态更新 |
| **实时区域** | 动态内容变化必须通知屏幕阅读器 | `aria-live="polite/assertive"` |
| **标签关联** | 所有表单控件必须有 `<label>` | `<label for="email">` 关联 `<input id="email">` |

#### 4.2.2 AI 生成可访问 HTML 的规则

```html
<!-- ✅ 正确 — AI 应该生成的代码 -->
<form aria-labelledby="search-form-title">
  <h2 id="search-form-title">Search</h2>

  <div class="form-group">
    <label for="search-input">Search term</label>
    <input
      id="search-input"
      type="search"
      aria-describedby="search-help"
      required
      autocomplete="search"
    />
    <span id="search-help" class="help-text">
      Enter keywords to search the database
    </span>
  </div>

  <button type="submit" aria-busy="false">
    Search
  </button>

  <!-- 动态结果区域 -->
  <div aria-live="polite" aria-atomic="false" id="search-results">
  </div>
</form>

<!-- ❌ 错误 — AI 不得生成的代码 -->
<div onclick="doSearch()" class="btn">Search</div>
<input placeholder="Search..." />  <!-- 无 label -->
<span style="color: red;">Error</span>  <!-- 屏幕阅读器无法感知 -->
```

#### 4.2.3 图片与多媒体

AI 生成包含图片或多媒体的代码时：

| 类型 | 要求 | alt 文本规则 |
|------|------|-------------|
| **信息性图片** | 必须有描述性 alt 文本 | 描述图片传达的信息，而非图片本身 |
| **装饰性图片** | `alt=""`（空 alt） | 明确标记为装饰性，屏幕阅读器跳过 |
| **功能性图片（图标按钮）** | alt 描述功能 | `alt="Close dialog"` 而非 `alt="X icon"` |
| **复杂图表** | 提供长描述或替代文本 | 使用 `longdesc` 或关联的文本描述 |
| **视频** | 必须有字幕 | 字幕文件随视频一起部署 |
| **音频** | 必须有文字稿 | 文字稿在音频旁边可访问 |

### 4.3 键盘导航

#### 4.3.1 键盘交互标准

| 按键 | 行为 | 适用场景 |
|------|------|---------|
| **Tab** | 移动到下一个焦点元素 | 全局导航 |
| **Shift+Tab** | 移动到上一个焦点元素 | 全局导航 |
| **Enter** | 激活当前焦点元素 | 按钮、链接 |
| **Space** | 激活当前焦点元素 / 切换 | 按钮、复选框 |
| **Escape** | 关闭弹窗/菜单/模态框 | 覆盖层 |
| **Arrow Keys** | 在组内导航 | 菜单、Tab 列表、单选按钮组 |
| **Home/End** | 跳到组内第一个/最后一个 | 列表导航 |

#### 4.3.2 焦点管理

AI 生成涉及焦点管理的代码时：

```javascript
// ✅ 正确 — AI 应该生成的焦点管理
function openModal(modalId: string) {
  const modal = document.getElementById(modalId);
  const previouslyFocused = document.activeElement;

  // 1. 打开时将焦点移入模态框
  modal.showModal();
  const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  firstFocusable?.focus();

  // 2. 模态框内焦点陷阱（Tab 不逃逸）
  modal.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      trapFocus(modal, e);
    }
    if (e.key === 'Escape') {
      closeModal(modalId, previouslyFocused);
    }
  });
}

function closeModal(modalId: string, returnFocusTo: HTMLElement | null) {
  document.getElementById(modalId)?.close();
  // 3. 关闭时将焦点返回到触发元素
  returnFocusTo?.focus();
}

// ❌ 错误 — AI 不得忽略焦点管理
function openModal() {
  document.querySelector('.modal').style.display = 'block';
  // 无焦点管理、无焦点陷阱、无返回焦点
}
```

#### 4.3.3 焦点可见性

AI 生成 CSS 时，不得移除焦点样式：

```css
/* ❌ 绝对禁止 — AI 不得生成 */
*:focus { outline: none; }
button:focus { outline: 0; }

/* ✅ 正确 — 自定义但保持可见 */
button:focus-visible {
  outline: 2px solid #0066cc;
  outline-offset: 2px;
  box-shadow: 0 0 0 4px rgba(0, 102, 204, 0.25);
}
```

### 4.4 AI 可访问 UI 生成规则

#### 4.4.1 生成检查清单

AI 在生成任何 UI 组件后，必须自动检查以下项目：

```
┌──────────────────────────────────────────────────┐
│ AI A11y 生成检查清单                              │
├──────────────────────────────────────────────────┤
│ 结构：                                            │
│ [ ] 使用语义 HTML 元素（非 div/span 模拟）         │
│ [ ] 标题层级正确（h1→h2→h3，不跳级）              │
│ [ ] 列表使用正确的列表元素（ul/ol/dl）             │
│ [ ] 表格有 <th> 和 scope 属性                      │
│                                                    │
│ 交互：                                            │
│ [ ] 所有交互元素可通过键盘访问                      │
│ [ ] 焦点顺序符合视觉流程                           │
│ [ ] 焦点样式可见且不被移除                          │
│ [ ] 模态框有焦点陷阱                                │
│                                                    │
│ 内容：                                            │
│ [ ] 图片有适当的 alt 文本                           │
│ [ ] 表单字段有 <label> 关联                         │
│ [ ] 错误消息与表单字段关联（aria-describedby）      │
│ [ ] 色彩对比度 ≥ 4.5:1                             │
│ [ ] 信息不单独依赖颜色传达                          │
│                                                    │
│ 动态内容：                                        │
│ [ ] 状态变化使用 aria-live 通知                     │
│ [ ] 加载状态使用 aria-busy                         │
│ [ ] 自动更新内容有适当的 live 策略                  │
└──────────────────────────────────────────────────┘
```

#### 4.4.2 AI 组件模板

AI 生成 UI 组件时，必须使用包含 A11y 的模板：

```tsx
// AI 生成的按钮组件模板 — 必须包含 A11y
interface AccessibleButtonProps {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
  variant?: 'primary' | 'secondary' | 'danger';
  ariaLabel?: string;  // 当按钮内容非文本时必须提供
}

function AccessibleButton({
  children,
  onClick,
  disabled = false,
  loading = false,
  variant = 'primary',
  ariaLabel,
}: AccessibleButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || loading}
      aria-label={ariaLabel}
      aria-busy={loading}
      className={`btn btn-${variant}`}
    >
      {loading && <span className="sr-only">Loading</span>}
      {children}
    </button>
  );
}
```

---

## 第 5 章：数据归档与清理

### 5.1 软删除

#### 5.1.1 软删除机制

```
┌──────────────────────────────────────────────────┐
│ 软删除标准实现                                     │
├──────────────────────────────────────────────────┤
│                                                    │
│ 数据库字段：                                       │
│   deleted_at   TIMESTAMP NULL                     │
│   deleted_by   VARCHAR(64) NULL                    │
│   delete_reason TEXT NULL                         │
│                                                    │
│ 行为：                                            │
│   · 删除操作设置 deleted_at = NOW()                │
│   · 查询默认加 WHERE deleted_at IS NULL            │
│   · 提供"回收站"视图查看软删除数据                   │
│   · 软删除数据支持恢复（deleted_at = NULL）          │
│                                                    │
│ AI 生成规则：                                     │
│   · 所有 delete 操作必须软删除，除非明确指定 FORCE   │
│   · ORM 模型必须有软删除 mixin                      │
│   · API 删除端点必须支持 soft/hard 参数              │
└──────────────────────────────────────────────────┘
```

#### 5.1.2 软删除的查询影响

AI 生成查询代码时，必须考虑软删除：

```sql
-- ✅ 正确 — AI 应该生成的查询
SELECT * FROM users WHERE deleted_at IS NULL AND status = 'active';

-- ❌ 错误 — 忽略软删除
SELECT * FROM users WHERE status = 'active';  -- 包含已删除记录

-- 关联查询必须检查关联表的软删除状态
SELECT o.* FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.deleted_at IS NULL
  AND u.deleted_at IS NULL;  -- 关联表也要检查
```

### 5.2 归档策略

#### 5.2.1 分层存储

| 层级 | 存储类型 | 访问延迟 | 成本 | 数据状态 |
|------|---------|---------|------|---------|
| **热存储** | 生产数据库 | < 10ms | 高 | 活跃数据 |
| **温存储** | 只读副本 / 归档库 | < 100ms | 中 | 近 90 天数据 |
| **冷存储** | 对象存储 / 磁带 | < 5s | 低 | 90 天 - 7 年 |
| **冻结存储** | 不可变存储（WORM） | < 1min | 极低 | 合规归档 |

#### 5.2.2 归档流程

```
数据达到归档阈值
        │
        ▼
┌──────────────────────────┐
│ 1. 识别可归档数据          │  — 按 created_at 和保留策略
└──────────────────────────┘
        │
        ▼
┌──────────────────────────┐
│ 2. 导出到归档存储          │  — 压缩 + 加密
└──────────────────────────┘
        │
        ▼
┌──────────────────────────┐
│ 3. 验证归档完整性          │  — 校验和 + 抽样查询
└──────────────────────────┘
        │
        ▼
┌──────────────────────────┐
│ 4. 从热存储删除            │  — 软删除标记
└──────────────────────────┘
        │
        ▼
┌──────────────────────────┐
│ 5. 记录归档元数据          │  — 归档 ID、范围、时间、大小
└──────────────────────────┘
```

### 5.3 数据生命周期

#### 5.3.1 生命周期阶段

```
  创建 → 活跃 → 静默 → 归档 → 删除
  │       │       │       │       │
  │       │       │       │       └─ 物理删除 / 匿名化
  │       │       │       └─ 合规保留结束
  │       │       └─ 无访问 > 90 天
  │       └─ 频繁读写
  └─ 数据生成
```

#### 5.3.2 生命周期自动管理

AI 可以辅助数据生命周期管理，但受以下约束：

| 操作 | AI 自主执行 | 需人工审批 |
|------|-----------|-----------|
| 识别可归档数据 | YES | — |
| 执行归档导出 | YES | — |
| 验证归档完整性 | YES | — |
| 从热存储删除 | — | YES（L3+ 需人工确认） |
| 修改保留策略 | — | YES（数据保护负责人） |
| 执行物理删除 | — | YES（法律合规确认） |

#### 5.3.3 生命周期配置

```yaml
# .omc/data-lifecycle.yaml — 声明式生命周期配置
lifecycle:
  - table: "user_sessions"
    stages:
      - status: active
        condition: "last_accessed > NOW() - INTERVAL '30 days'"
      - status: silent
        condition: "last_accessed > NOW() - INTERVAL '90 days'"
        action: "move_to_warm_storage"
      - status: archived
        condition: "last_accessed > NOW() - INTERVAL '180 days'"
        action: "export_and_archive"
      - status: deleted
        condition: "created_at > NOW() - INTERVAL '365 days'"
        action: "anonymize"
  - table: "ai_evidence"
    stages:
      - status: active
        condition: "project_status = 'active'"
      - status: archived
        condition: "project_status = 'completed' AND created_at > NOW() - INTERVAL '1 year'"
        action: "export_to_cold_storage"
```

---

## 第 6 章：AI 专属数据规则

### 6.1 AI 数据访问矩阵

#### 6.1.1 数据可访问性分类

| 数据类别 | AI 可读 | AI 可写 | AI 可发送提供者 | 条件 |
|----------|---------|---------|----------------|------|
| **公开文档** | YES | YES | YES | 代码、README、公开 API 文档 |
| **项目代码** | YES | YES（受限） | 部分 | 仅非敏感代码可发送给 AI 提供者 |
| **Spec 文件** | YES | YES | YES | Spec 不得包含密钥和 PII |
| **测试数据** | YES | YES | — | 必须是合成数据 |
| **生产数据库** | — | — | NEVER | AI 不得直接访问生产数据库 |
| **环境变量** | 只读非敏感 | NEVER | NEVER | .env 文件在 AI 权限中 deny |
| **用户 PII** | NEVER | NEVER | NEVER | 绝对禁止 |
| **密钥/Token** | NEVER | NEVER | NEVER | pre-commit + pre-send 双重拦截 |
| **AI 会话日志** | YES | YES | — | 日志中不得有敏感数据 |
| **`.gate/` 证据** | YES | YES | YES | 证据数据已脱敏 |

#### 6.1.2 AI 上下文窗口数据过滤

在将项目数据提供给 AI 时，必须经过过滤管道：

```
原始项目数据
        │
        ▼
┌──────────────────────┐
│ 1. 排除敏感文件        │  — .env, secrets/, *.key
│   (基于 .aiignore)    │
└──────────────────────┘
        │
        ▼
┌──────────────────────┐
│ 2. 扫描 PII           │  — 正则匹配 + 模式识别
│   (pre-send 扫描)     │
└──────────────────────┘
        │
        ▼
┌──────────────────────┐
│ 3. 截断过长内容        │  — 上下文窗口限制
│   (智能截断)           │  — 保留关键上下文
└──────────────────────┘
        │
        ▼
┌──────────────────────┐
│ 4. 记录审计日志        │  — 发送了什么、何时、给谁
│   (审计)               │
└──────────────────────┘
        │
        ▼
    发送给 AI 提供者
```

### 6.2 `.aiignore` 规范

#### 6.2.1 标准格式

```
# .aiignore — AI 上下文排除规则
# 语法同 .gitignore，仅影响 AI 可访问的文件范围

# 密钥和配置
.env
.env.*
*.key
*.pem
secrets/
credentials.json

# 敏感数据
data/production/
backups/
logs/auth/

# 大型二进制文件
*.zip
*.tar.gz
node_modules/
vendor/

# AI 不应参考的文件
TODO.md         # 未确认的计划文件
experiments/    # 实验性代码
```

#### 6.2.2 AI 行为规则

- AI 读取项目数据前，必须加载 `.aiignore` 并排除匹配的文件
- AI 不得绕过 `.aiignore` 读取被排除的文件
- CI 必须验证 `.aiignore` 的完整性（不得遗漏敏感文件路径）
- `.aiignore` 本身必须在版本控制中

### 6.3 AI 生成数据的安全边界

#### 6.3.1 生成内容约束

AI 生成的代码在处理数据时必须：

1. **输入验证：** 所有外部输入必须验证类型、范围、格式
2. **输出编码：** 输出到 HTML 时必须转义，输出到 SQL 时必须参数化
3. **错误处理：** 错误消息不得包含敏感数据（堆栈跟踪、内部路径、SQL 语句）
4. **日志安全：** 日志中不得记录密钥、token、完整 PII
5. **缓存安全：** 缓存不得包含未授权的跨租户数据

#### 6.3.2 AI 数据操作审批链

```
AI 识别需要数据操作（迁移、清理、归档）
        │
        ▼
┌──────────────────────────────────┐
│ 1. AI 编写操作计划（DRF 类似物）   │
│    → 操作类型、影响范围、回滚方案   │
└──────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────┐
│ 2. 自动安全检查                   │
│    · 影响数据量评估                │
│    · PII 影响分析                  │
│    · 回滚可行性                    │
│    · 合规影响                      │
└──────────────────────────────────┘
        │
     ┌──┴──┐
    通过    拒绝 → AI 修改方案
        │
        ▼
┌──────────────────────────────────┐
│ 3. 人工审批（数据保护负责人）      │
│    · 业务影响评估                  │
│    · 法律合规确认                  │
│    · 时间窗口确认                  │
└──────────────────────────────────┘
        │
        ▼
  执行操作 → 验证 → 记录审计日志
```

### 6.4 AI 数据使用审计

#### 6.4.1 审计日志格式

```json
{
  "audit_id": "audit-20260418-001",
  "timestamp": "2026-04-18T10:30:00Z",
  "agent_id": "auto-coder-agent-v5.4",
  "operation": "context_read",
  "data_categories": ["source_code", "spec_files", "test_data"],
  "files_accessed": ["src/auth/login.ts", "specs/auth-v2.md"],
  "files_blocked_by_aiignore": [".env", "secrets/db.key"],
  "pii_detected": false,
  "sent_to_provider": true,
  "provider": "alibaba-coding-plan",
  "token_count": 12450,
  "gate_verification": ".gate/audit-20260418-001.json"
}
```

#### 6.4.2 定期审计

| 审计频率 | 审计内容 | 审计方 |
|----------|---------|--------|
| **每次 AI 调用** | pre-send 扫描结果、发送的数据类别 | 自动化 |
| **每日** | 审计日志完整性、异常模式检测 | 自动化 |
| **每周** | 数据访问模式分析、`.aiignore` 覆盖率 | AI + 人工 |
| **每月** | 全面数据使用审计、合规报告 | 人工 + 数据保护负责人 |
| **每季度** | 第三方 AI 提供者数据安全审计 | 外部审计 |

---

## 附录 A：交叉引用

| 引用 | 关联文档 | 关联内容 |
|------|---------|---------|
| P9 Prompt 版本化 | [01-core-specification.md](01-core-specification.md) §1.1 | Prompt 记录保留 180 天 |
| P10 数据分级 | [01-core-specification.md](01-core-specification.md) §1.1 | PII 分类和 pre-send 扫描 |
| P11 证据链 | [01-core-specification.md](01-core-specification.md) §1.1 | `.gate/` 备份和归档 |
| P5/P17 输入验证 | [01-core-specification.md](01-core-specification.md) §1.1-1.2 | AI 生成代码的输入验证 |
| 安全底线 | [04-security-governance.md](04-security-governance.md) §1 | 密钥保护、输入验证 |
| 合规审计 | [04-security-governance.md](04-security-governance.md) §4 | GDPR 合规衔接 |
| DB 迁移 | [08-database-migration.md](08-database-migration.md) | 软删除列的迁移策略 |
| CI/CD 门禁 | [06-cicd-pipeline.md](06-cicd-pipeline.md) | 数据质量门禁集成 |
| 反幻觉 | [07-anti-hallucination.md](07-anti-hallucination.md) | AI 数据声明的证据验证 |

## 附录 B：术语表

| 术语 | 定义 |
|------|------|
| **PII** | Personal Identifiable Information，个人身份信息 |
| **GDPR** | General Data Protection Regulation，通用数据保护条例 |
| **DPIA** | Data Protection Impact Assessment，数据保护影响评估 |
| **RPO** | Recovery Point Objective，恢复点目标（最大允许数据丢失） |
| **RTO** | Recovery Time Objective，恢复时间目标（最大允许恢复时间） |
| **PITR** | Point-In-Time Recovery，时间点恢复 |
| **WORM** | Write Once Read Many，一次写入多次读取（不可变存储） |
| **i18n** | Internationalization，国际化（18 = 字母数） |
| **A11y** | Accessibility，可访问性（11 = 字母数） |
| **WCAG** | Web Content Accessibility Guidelines，Web 内容可访问性指南 |
| **RTL** | Right-To-Left，从右到左（阿拉伯语、希伯来语等） |
| **ARIA** | Accessible Rich Internet Applications，可访问富互联网应用 |
| **WAL** | Write-Ahead Log，预写式日志 |
| **合成数据** | Synthetic Data，人工生成的、不包含真实个人信息的数据 |
| **软删除** | Soft Delete，标记删除而非物理删除 |
