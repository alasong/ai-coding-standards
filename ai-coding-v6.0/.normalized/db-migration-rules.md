# DB Migration Agent 规范
> v5.5 | 负责数据库迁移审查、数据一致性验证、破坏性变更检测、回滚策略

## 核心底线
- **P11 证据链** [§1.1] 每个迁移结论必须有 ≥2 条可验证证据（测试输出 + .gate/ 记录）
- **P21 数据一致性** [§5] DB 写入失败必须返回错误，不得吞异常；迁移前后 row count 必须一致
- **独立验证** [08-database-migration §8] 迁移审查不得由迁移脚本编写者自评；必须由独立 Agent 执行

## TDD 迁移流程 [§2]
```
读 Spec → 写迁移测试(Up/Down/数据完整性) → CI 记录 Red → 写迁移脚本 → 测试通过(Green) → 输出 .gate/migration-report.json
```
- 测试必须验证：迁移前 schema 状态 → 执行迁移 → 迁移后 schema 状态 → 旧数据可读 → 新列可写 → 回滚后旧代码可用
- 迁移测试和迁移脚本不得同 commit 提交

## Destructive Change 检测 [§3.1]
| 危险操作 | 检测模式 | 动作 |
|---------|---------|------|
| `DROP TABLE/COLUMN` | 正则 `DROP\s+(TABLE\|COLUMN)` | **阻断**，转人工 |
| `RENAME TABLE/COLUMN` | 正则 `RENAME\s+(TABLE\|COLUMN)` | **阻断**，转人工 |
| 类型变更（VARCHAR→INT） | SQL 解析器对比列类型 | **阻断**，转人工 |
| `ALTER COLUMN ... NOT NULL` | 新增 NOT NULL 约束 | 验证旧数据无 NULL |
| `DELETE FROM` / `TRUNCATE` | 正则匹配 | **阻断**，转人工 |
- 向下不兼容变更（Dangerous/Complex 级）禁止 AI 自主执行，必须人工审批 [§1.2]
- Safe 级：新增表/列（允许 NULL）/索引 → AI 可自主执行
- Caution 级：修改默认值/新增非空列（需默认值） → L3+ 需人工确认
- Dangerous/Complex 级：DROP/RENAME/类型变更/分库分表 → **禁止 AI 执行**

## Expand-Contract 模式 [§3.2]
破坏性变更必须使用三步模式，禁止一步到位：
```
Phase 1 — Expand: 新增列（旧列保留），双写/trigger 同步
Phase 2 — Migrate: 数据回填（幂等），WHERE IS NULL 防重复
Phase 3 — Contract: 旧代码完全下线后 DROP 旧列
```
- 每个 Phase 独立迁移文件，不得在一次迁移中同时 Expand + Contract
- Phase 2 必须可安全重入（幂等），主从延迟 >5s 时暂停

## 数据一致性 [§4.3, §7.2]
- 迁移前后 row count 必须一致；checksum 验证通过
- 事务包裹迁移：每个迁移在独立事务中执行，失败自动回滚
- 大表（>100 万行）迁移必须分批：每批 ≤10000 行，批次间隔 ≥1s
- 迁移后验证：旧数据可读 + 新列可写 + E2E 测试通过

## 回滚策略 [§5]
- 每个迁移必须有 Down 方法；Down 脚本必须存在且可执行
- Safe/Caution 级：Down 方法可由 AI 生成；Dangerous 级：Down 必须人工编写
- 向前兼容回滚：代码回滚到旧版本，数据库保持新 Schema 不变，旧代码忽略新列仍正常工作
- 回滚不会丢失数据：类型变更无 Down 方法，不得自动回滚
- 触发条件：迁移失败 → 自动 Down()；E2E 失败 → 自动 Down() + 通知；错误率 >5% → 人工确认

## 零停机迁移 [§4.2, §4.3]
- 大表迁移必须分批，不得一次性 UPDATE 全表
- 锁表时间 <1s：PostgreSQL CREATE INDEX 必须用 `CONCURRENTLY`
- 使用 online schema change：`SET lock_timeout = '10s'`，`SET statement_timeout = '30min'`
- 蓝绿迁移 Step 4-7（流量切换/清理）必须人工确认

## Migration 文件规范 [§1.3, §6.3]
- 文件名格式：`{timestamp}_{type}_{description}.sql`
- 文件头部必须声明：`ai-generated: true`、Spec ID、变更级别（Safe/Caution/Dangerous）、`depends_on: []`
- 必须包含：版本号、描述、Up 方法、Down 方法、事务声明
- 幂等性：Safe 级必须幂等（`IF NOT EXISTS`）；Caution 建议幂等；Dangerous 禁止幂等

## 多 Agent 冲突检测 [§6]
- 同表操作多个迁移 → 按依赖关系拓扑排序
- 外键引用 → 被引用的迁移必须先执行
- 时间戳冲突 → 自动重新分配

## DCP 检查清单
- [ ] 迁移脚本有对应测试（Up + Down + 数据完整性）
- [ ] Down 脚本存在且可执行
- [ ] 数据一致性验证通过（row count / checksum）
- [ ] 破坏性变更已检测并标记
- [ ] Expand-Contract 模式正确使用
- [ ] 回滚演练通过（在测试库执行 Down 验证）
- [ ] 变更级别与 AI 权限匹配
- [ ] 文件命名/格式/声明完整
- [ ] 大表分批策略声明
- [ ] 独立 Agent 审查（非脚本编写者自评）

## 迁移禁止行为
- 不得在一次迁移中同时执行 Expand + Contract
- 不得直接 DROP/RENAME/MODIFY 生产列
- 不得一次性 UPDATE 超过 100 万行的表
- 不得跳过迁移测试直接执行
- 不得由迁移编写者自评审查结果
- 不得在没有 Down 方法的情况下提交迁移
