# AI Coding 规范 v5.5：数据库迁移

> 版本：v5.5 | 2026-04-24
> 定位：AI 自主修改数据库 Schema 的安全规范 — TDD、destructive change 检测、蓝绿迁移、回滚
> 前置：[01-core-specification.md](01-core-specification.md) P3（TDD 先行）、[06-cicd-pipeline.md](06-cicd-pipeline.md)

---

## 第 1 章：核心原则

### 1.1 为什么数据库迁移需要独立规范

数据库是 AI 自主编码中**风险最高**的环节。代码可以回滚，但数据变更一旦执行就不可逆。大规模 Auto-Coding 场景下，多个 AI Agent 同时修改 Schema 会导致：

- **destructive change**（DROP、RENAME、类型变更）导致数据丢失
- **并发迁移冲突**：两个迁移脚本同时执行产生不可预期的结果
- **向前不兼容**：新 Schema 与旧代码不兼容，回滚时读取失败
- **数据一致性破坏**：NOT NULL 约束、外键约束在旧数据上失败

**核心原则**：数据库迁移必须遵循"向前兼容"（forward-compatible）策略——所有迁移必须在旧代码和新代码同时运行时保持可用。

### 1.2 数据库迁移分级

| 级别 | 变更类型 | 风险 | AI 自主权限 |
|------|---------|:----:|:----------:|
| **Safe** | 新增表、新增列（允许 NULL）、新增索引 | LOW | L2+ 自主执行 |
| **Caution** | 修改默认值、新增非空列（需默认值）、扩列类型 | MEDIUM | L3+ 自主执行，需人工确认 |
| **Dangerous** | DROP 表/列、RENAME、类型变更、缩列类型 | HIGH | **禁止自主执行**，必须人工 |
| **Complex** | 数据迁移、分表/分库、主从切换 | CRITICAL | **禁止 AI 执行**，必须人工 |

### 1.3 迁移文件命名规范

```
{timestamp}_{type}_{description}.sql
```

| 字段 | 说明 | 示例 |
|------|------|------|
| timestamp | Unix 时间戳（秒） | `1713456000` |
| type | `safe` / `caution` / `dangerous` | `safe` |
| description | 蛇形命名描述 | `add_user_email_index` |

完整示例：`1713456000_safe_add_user_email_index.sql`

**AI 特有规则**：AI 生成的迁移文件必须在文件头部注释中声明 `ai-generated: true`、对应的 Spec ID、变更级别。

---

## 第 2 章：迁移 TDD 流程

### 2.1 迁移测试优先

每个数据库迁移必须**先写测试**，测试通过后才能执行迁移。

```
1. 写迁移测试（migration_test.go）
   a. 测试迁移可以执行（Up）
   b. 测试迁移可以回滚（Down）
   c. 测试迁移后数据完整性
2. 写迁移脚本（migration.sql）
3. 在干净的测试数据库运行迁移 → 测试通过
4. 在 CI 中运行 → 记录到 .gate/migration-test.json
5. 合并后执行
```

### 2.2 迁移测试模板

```go
func TestMigration_Up(t *testing.T) {
    db := setupTestDB(t)
    
    // Before: 验证旧 Schema 存在
    assertTableExists(t, db, "users")
    
    // Execute migration
    err := migration.Up(db)
    require.NoError(t, err)
    
    // After: 验证新 Schema 生效
    assertColumnExists(t, db, "users", "email_verified")
    
    // Data integrity: 验证旧数据仍然可读
    rows, err := db.Query("SELECT id, name, email FROM users")
    require.NoError(t, err)
    rows.Close()
    
    // New data path: 验证新列可写
    _, err = db.Exec("INSERT INTO users (name, email, email_verified) VALUES (?, ?, ?)",
        "test", "test@example.com", false)
    require.NoError(t, err)
}

func TestMigration_Down(t *testing.T) {
    db := setupTestDB(t)
    migration.Up(db)
    
    err := migration.Down(db)
    require.NoError(t, err)
    
    // 验证回滚后旧代码仍然可以工作
    assertColumnNotExists(t, db, "users", "email_verified")
}
```

### 2.3 CI 中的迁移验证

```
┌──────────────────────────────────────────────────┐
│ CI Pipeline L4: 集成验证层                         │
│                                                   │
│  1. 创建干净测试数据库                              │
│  2. 执行所有未运行的迁移脚本                         │
│  3. 运行迁移测试（Up + Down + 数据完整性）            │
│  4. 验证迁移后 E2E 测试通过                         │
│  5. 验证迁移回滚后 E2E 测试仍通过（向前兼容验证）      │
│  6. 输出 .gate/migration-report.json               │
└──────────────────────────────────────────────────┘
```

---

## 第 3 章：Destructive Change 检测

### 3.1 自动检测规则

CI 必须在 L3 层自动扫描所有迁移脚本，检测 destructive change：

| 危险操作 | 检测模式 | 动作 |
|---------|---------|------|
| `DROP TABLE` | 正则 `DROP\s+TABLE` | **阻断**，转人工 |
| `DROP COLUMN` | 正则 `DROP\s+COLUMN` / `ALTER\s+.*\s+DROP` | **阻断**，转人工 |
| `RENAME TABLE/COLUMN` | 正则 `RENAME\s+(TABLE|COLUMN)` | **阻断**，转人工 |
| 类型变更（VARCHAR→INT 等） | SQL 解析器对比旧/新列类型 | **阻断**，转人工 |
| `ALTER COLUMN ... NOT NULL` | 正则 `NOT\s+NULL` 新增 | 验证旧数据无 NULL |
| `ADD CONSTRAINT` 外键 | 正则 `FOREIGN\s+KEY` | 验证引用存在 |
| `DELETE FROM` | 正则 `DELETE\s+FROM` | **阻断**，转人工 |
| `TRUNCATE` | 正则 `TRUNCATE` | **阻断**，转人工 |

### 3.2 向前兼容规则（Expand-Contract 模式）

所有需要修改列结构的操作，必须使用 Expand-Contract 两步模式：

**场景：将 `name` 列重命名为 `full_name`**

```
Phase 1 — Expand（新代码部署前执行）：
  ALTER TABLE users ADD COLUMN full_name VARCHAR(255);
  -- 旧代码仍写 name，新代码读写 full_name
  -- 两个列同时存在，数据通过 trigger 或双写保持同步

Phase 2 — Migrate（新代码部署后、旧代码完全下线前执行）：
  UPDATE users SET full_name = name WHERE full_name IS NULL;
  -- 数据回填，确保两个列数据一致

Phase 3 — Contract（旧代码完全下线后执行）：
  ALTER TABLE users DROP COLUMN name;
  -- 安全删除旧列
```

**AI 必须遵循的规则**：
1. 禁止在一次迁移中同时执行 Expand 和 Contract
2. 每个 Phase 必须独立为一个迁移文件
3. Phase 2 必须可安全重入（幂等）
4. Phase 3 的删除必须在监控下执行（见第 5 章）

### 3.3 NOT NULL 列添加规范

```
禁止：ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL;
原因：如果表已有数据，NOT NULL 列添加会因现有行的 NULL 值而失败。

正确做法：
  -- Step 1: 添加允许 NULL 的列
  ALTER TABLE users ADD COLUMN email_verified BOOLEAN;
  -- Step 2: 填充默认值（大表需分批，避免锁表）
  UPDATE users SET email_verified = false WHERE email_verified IS NULL;
  -- Step 3: 添加 NOT NULL 约束
  ALTER TABLE users ALTER COLUMN email_verified SET NOT NULL;
```

### 3.4 索引创建规范

| 操作 | 注意事项 |
|------|---------|
| CREATE INDEX | PostgreSQL 中会锁表，必须使用 `CREATE INDEX CONCURRENTLY` |
| 多列索引 | 注意列的顺序：区分度高的列在前 |
| 部分索引 | `WHERE` 条件索引可以减小体积 |
| 主键变更 | 禁止在线表上直接 ALTER PRIMARY KEY，需蓝绿迁移 |

---

## 第 4 章：蓝绿数据库迁移

### 4.1 适用场景

蓝绿数据库迁移适用于：
- 需要修改列类型
- 需要拆分/合并表
- 需要迁移大量数据
- 零停机要求

### 4.2 蓝绿迁移流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 蓝绿迁移流程（AI 可执行 Step 1-3，Step 4-7 需人工确认）             │
│                                                                  │
│ Step 1: 创建新 Schema（Green）                                     │
│   - 在现有 DB 中创建新表/新列                                       │
│   - 不修改旧 Schema（Blue）                                        │
│                                                                  │
│ Step 2: 双写（Dual Write）                                         │
│   - 新代码同时写入 Blue 和 Green                                    │
│   - 读仍然从 Blue 读取                                              │
│   - 验证 Blue 和 Green 数据一致                                     │
│                                                                  │
│ Step 3: 数据回填（Backfill）                                        │
│   - 将 Blue 中的历史数据迁移到 Green                                │
│   - 分批执行，避免锁表                                             │
│   - 每批次验证数据完整性                                            │
│                                                                  │
│ Step 4: 切换读取 → Green（人工确认）                                │
│   - 灰度切换：10% → 50% → 100% 流量读 Green                       │
│   - 监控错误率和延迟                                               │
│                                                                  │
│ Step 5: 停止双写                                                   │
│   - 停止写入 Blue                                                  │
│   - 仅读写 Green                                                   │
│                                                                  │
│ Step 6: 清理 Blue（人工确认）                                       │
│   - 观察 ≥24 小时无问题                                             │
│   - 删除 Blue 的列/表                                              │
│                                                                  │
│ Step 7: 回滚预案                                                   │
│   - 如 Step 4 失败：立即切换回 Blue 读取                             │
│   - Green 数据不删除，保留回滚路径                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 大表数据迁移分批策略

```sql
-- 禁止一次性 UPDATE 大表（> 100 万行）
-- 正确做法：分批迁移

-- 方法 1：按 ID 范围分批
UPDATE users SET email_verified = false
WHERE id BETWEEN 1 AND 10000 AND email_verified IS NULL;

-- 方法 2：按时间分批
UPDATE users SET email_verified = false
WHERE created_at < '2026-01-01' AND email_verified IS NULL
LIMIT 1000;

-- 方法 3：使用 ctid（PostgreSQL）
UPDATE users SET email_verified = false
WHERE ctid IN (
    SELECT ctid FROM users WHERE email_verified IS NULL LIMIT 1000
);
```

**分批规则**：
- 每批次 ≤ 10000 行
- 批次间间隔 ≥ 1 秒（避免主库压力）
- 每批次后验证主从延迟 < 1 秒
- 主从延迟 > 5 秒时暂停迁移

### 4.4 幂等性要求

所有迁移脚本必须是幂等的——多次执行结果相同：

```sql
-- PostgreSQL 幂等示例
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'email_verified'
    ) THEN
        ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT false;
    END IF;
END $$;
```

**AI 必须遵循**：Safe 级别迁移必须幂等；Caution 级别建议幂等；Dangerous 级别禁止幂等（因为需要精确控制执行次数）。

### 4.5 连接池与超时

| 配置 | 值 | 说明 |
|------|-----|------|
| 迁移专用连接池 | 独立连接，不共享应用连接池 | 避免迁移耗尽应用连接 |
| Statement Timeout | `SET statement_timeout = '30min'` | 防止迁移无限阻塞 |
| Lock Timeout | `SET lock_timeout = '10s'` | 避免迁移等待锁 |
| 事务包装 | 每个迁移在独立事务中 | 失败时自动回滚 |

---

## 第 5 章：回滚策略

### 5.1 迁移回滚触发条件

| 触发条件 | 自动/人工 | 回滚动作 |
|---------|:--------:|---------|
| 迁移执行失败 | 自动 | 执行 `Down()` 方法 |
| 迁移后 E2E 测试失败 | 自动 | 执行 `Down()` 方法 + 通知 |
| 新代码部署后错误率 > 5% | 人工确认 | 代码回滚 + 数据库向前兼容 |
| 数据不一致检测触发 | 人工确认 | 代码回滚 + 数据修复脚本 |
| 蓝绿迁移 Step 4 失败 | 人工确认 | 切换回旧 Schema 读取 |

### 5.2 向前兼容是回滚的基础

```
核心认识：回滚不需要回滚数据库——只要新 Schema 对旧代码是向前兼容的，
         代码回滚后仍然可以读写新 Schema 中的新列（旧代码忽略新列即可）。

回滚步骤：
  1. 代码回滚到旧版本
  2. 数据库保持新 Schema 不变
  3. 旧代码忽略新列，仍然正常工作
  4. 数据不丢失
```

### 5.3 Down 方法编写规范

每个迁移文件必须包含 `Down()` 方法，但遵循以下约束：

| 操作类型 | Down 方法 | 注意事项 |
|---------|----------|---------|
| 新增表 | `DROP TABLE` | Safe 级别的迁移可以有 Down |
| 新增列 | `DROP COLUMN` | **仅在没有数据写入后执行** |
| 新增索引 | `DROP INDEX` | 可以随时安全执行 |
| 修改默认值 | 恢复原默认值 | 幂等操作 |
| 类型变更 | **无 Down 方法** | Dangerous 级别，不得自动回滚 |
| 数据迁移 | 反向迁移脚本 | 需要人工验证反向迁移正确性 |

**关键约束**：Safe/Caution 级别的迁移 Down 方法可以由 AI 生成，Dangerous/Complex 级别的 Down 方法必须人工编写和验证。

---

## 第 6 章：多 Agent 并发迁移冲突解决

### 6.1 冲突场景

```
Agent A 创建迁移：1713456000_safe_add_user_email.sql（给 users 表加 email 列）
Agent B 创建迁移：1713456001_safe_add_user_phone.sql（给 users 表加 phone 列）

问题：两个迁移都操作同一个表，如果并发执行可能产生：
  - 表锁冲突
  - 迁移顺序依赖
  - 外键引用顺序问题
```

### 6.2 冲突检测规则

| 检测项 | 检测方法 | 处理策略 |
|--------|---------|---------|
| 同表操作 | 解析 SQL 中的表名，检查是否有多个迁移操作同一表 | 按依赖关系排序 |
| 外键引用 | 检查新表是否引用了其他迁移创建的表 | 被引用的迁移必须先执行 |
| 列依赖 | 检查是否有迁移引用了其他迁移新增的列 | 按依赖关系排序 |
| 时间戳冲突 | 检查是否有迁移使用相同的时间戳 | 自动重新分配时间戳 |

### 6.3 迁移依赖图

```
迁移脚本提交后，CI 必须构建依赖图：

  Migration A (add users table)     Migration C (add orders table)
              │                                      │
              ├──→ Migration B (add email to users)   │
              │                                      │
              └──────────────┬───────────────────────┘
                             │
                  Migration D (add user_id FK to orders)

执行顺序：A → B → C → D（拓扑排序）
```

**AI 特有规则**：AI 生成的迁移文件必须在文件头部注释中声明 `depends_on: []`，列出依赖的其他迁移文件。CI 在构建依赖图时优先使用声明的依赖，同时验证声明是否正确。

---

## 第 7 章：迁移监控与告警

### 7.1 迁移执行监控

| 监控项 | 告警阈值 | 动作 |
|--------|---------|------|
| 迁移执行时长 | > 5 分钟 | 警告，可能锁表 |
| 迁移执行时长 | > 30 分钟 | 阻断，可能死锁 |
| 主从延迟 | > 5 秒 | 暂停迁移 |
| 表锁等待 | > 10 秒 | 暂停迁移 |
| 磁盘空间 | 剩余 < 20% | 阻断迁移 |
| 连接数 | 使用率 > 80% | 警告 |

### 7.2 迁移后验证

```json
{
  "type": "migration-report",
  "migration_file": "1713456000_safe_add_user_email.sql",
  "level": "safe",
  "executed_at": "2026-04-18T10:00:00Z",
  "duration_ms": 234,
  "up_result": "success",
  "down_result": "success",
  "data_integrity": {
    "old_data_readable": true,
    "new_column_writable": true,
    "row_count_before": 15000,
    "row_count_after": 15000
  },
  "forward_compatible": true,
  "evidence": [
    ".gate/migration-test-up.json",
    ".gate/migration-test-down.json"
  ]
}
```

---

## 第 8 章：AI 生成迁移的特殊约束

### 8.1 AI 生成迁移的限制

| 约束 | 说明 |
|------|------|
| 仅允许 Safe 级别自主执行 | Caution 级别需人工确认，Dangerous/Complex 禁止 |
| 不得删除数据 | `DELETE` / `TRUNCATE` 完全禁止 |
| 不得修改生产数据 | 仅允许 DDL，不允许 DML（除非在测试环境） |
| 必须包含 Down 方法 | 每个迁移必须有回滚路径 |
| 必须声明依赖 | `depends_on` 字段必须声明 |
| 必须经过测试数据库验证 | 迁移必须在 CI 的测试数据库中验证通过 |
| 大表操作必须分批 | 超过 100 万行的表禁止一次性 ALTER |

### 8.2 AI 迁移生成 Checklist

AI 生成迁移脚本后，必须逐项自检：

- [ ] 变更级别正确（Safe/Caution/Dangerous）
- [ ] 不包含 DROP / DELETE / TRUNCATE（除非 Dangerous 且人工确认）
- [ ] 包含 Down 方法
- [ ] 声明了 depends_on
- [ ] 新列有默认值（如果后续会加 NOT NULL）
- [ ] 大表操作有分批策略
- [ ] 迁移文件名格式正确
- [ ] 文件头部有 ai-generated 注释
- [ ] 对应的测试文件已创建
