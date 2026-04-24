# AI Coding 规范 v5.5：API 契约与版本管理

> 版本：v5.5 | 2026-04-24
> 定位：大规模 Auto-Coding 下的 API 契约管理、版本策略、兼容性保证、漂移检测
> 前置：[01-core-specification.md](01-core-specification.md) 第 1 章（核心原则 P7/P8/P11）、[06-cicd-pipeline.md](06-cicd-pipeline.md) 第 2 章（L4 契约测试）

---

## 第 1 章：为什么需要 API 契约规范

大规模 Auto-Coding = 每天数十至数百个 AI 生成的端点变更。没有标准化契约管理意味着：

- AI 生成代码与 API 文档不同步——前端按旧 API 调用
- 无意识的破坏性变更传播到消费者端
- 多服务并行开发时接口定义冲突
- 契约测试缺失导致集成层频繁崩溃
- 版本策略混乱——URL、Header、Query 混用

**核心原则**：API 契约是"单一信息源"（P6）的第一优先级载体。所有 API 行为必须以 OpenAPI Spec 为基准，代码是 Spec 的实现，而非相反。

---

## 第 2 章：OpenAPI/Swagger 契约管理

### 2.1 契约文件组织结构

```
specs/api/
├── openapi.yaml              # 主 OpenAPI 3.0.3 文档（入口，使用 $ref）
├── paths/                    # 按资源分组的端点定义
│   ├── users.yaml
│   ├── orders.yaml
│   └── products.yaml
├── schemas/                  # 共享数据模型
│   ├── user.yaml
│   ├── order.yaml
│   └── common/
│       ├── pagination.yaml
│       └── error-response.yaml
├── parameters/               # 共享参数
│   ├── path-id.yaml
│   └── query-page.yaml
├── responses/                # 共享响应
│   ├── 200-ok.yaml
│   ├── 400-bad-request.yaml
│   └── 401-unauthorized.yaml
└── examples/                 # 请求/响应示例
    ├── user-create-request.yaml
    └── user-create-response.yaml
```

**拆分规则**：
- 主文件仅包含 `openapi`、`info`、`servers`、`paths` 的 `$ref` 引用、`components` 的 `$ref` 引用
- 每个路径文件不得超过 200 行（遵循 P8 最小批量）
- schema 文件按领域边界拆分，不得跨域引用

### 2.2 AI 生成 OpenAPI Spec 的规则

| 规则 | 说明 | 验证方式 |
|------|------|---------|
| **Spec 与代码同生** | AI 生成 API 代码时，必须在同一 PR 中生成/更新对应的 OpenAPI Spec 片段 | PR 文件扫描：有 `src/api/` 变更则必须有 `specs/api/` 变更 |
| **Spec 先于代码** | 新端点开发流程：先写 Spec → Spec 评审通过 → 生成代码实现 | CI 检查：Spec 文件的 git commit 时间戳必须早于实现代码 |
| **Spec 必须可解析** | 生成的 Spec 必须通过 `openapi-parser` 验证 | `npx @apidevtools/swagger-cli validate specs/api/openapi.yaml` |
| **示例不可省略** | 每个端点必须有至少 1 个 request example 和 1 个 response example | CI 检查 example 覆盖率 |
| **错误响应全覆盖** | 每个端点必须定义 200/400/401/500 响应 schema | Schema 完整性扫描 |
| **AI 不得编造 HTTP 方法** | 仅允许标准方法：GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS | HTTP 方法白名单校验 |

### 2.3 Spec 生成与更新的 AI 工作流

```
1. AI 读取 specs/ 中的任务队列（P7 Spec 驱动）
2. 识别需要新增/变更的 API 端点
3. 在 specs/api/paths/ 中新增或修改端点定义
4. 在 specs/api/schemas/ 中新增或修改数据模型
5. 运行 openapi-parser 验证 Spec 合法性
6. 生成代码实现（server handler + client stub）
7. 更新 specs/api/ 中的 example 文件
8. 提交 Spec 变更（独立 commit，先于实现 commit）
```

**Commit 顺序要求**：

```
commit 1: "spec: add POST /api/v1/users endpoint"     ← OpenAPI spec 变更
commit 2: "feat: implement POST /api/v1/users handler" ← 代码实现
commit 3: "test: add contract tests for POST /api/v1/users" ← 契约测试
```

**违反此顺序 = P3 TDD 先行违反 = CI 阻断。**

### 2.4 Spec 验证门禁

| 检查项 | 工具 | 阻断？ | 说明 |
|--------|------|:------:|------|
| YAML 语法验证 | `swagger-cli validate` | **是** | 语法错误或引用断裂 |
| Schema 完整性 | 自定义脚本 `scripts/check-spec-completeness.py` | **是** | 每个端点有 request/response schema |
| Example 覆盖 | 自定义脚本 `scripts/check-spec-examples.py` | 警告 | 覆盖率 < 100% 警告，< 50% 阻断 |
| 安全扫描 | `spectral lint` | **是** | 安全规则：HTTPS 强制、敏感字段标记 |
| 规范一致性 | `spectral` 自定义规则集 | **是** | 命名规范、HTTP 方法语义、状态码使用 |

### 2.5 Spectral 自定义规则集

```yaml
# .spectral.yaml
extends: spectral:oas
rules:
  # 命名规范：path 参数必须使用 kebab-case
  path-params-kebab-case:
    description: Path parameters must use kebab-case
    given: "$.paths[*][*].parameters[?(@.in == 'path')]"
    severity: error
    then:
      field: name
      function: pattern
      functionOptions:
        match: "^[a-z][a-z0-9]*(-[a-z0-9]+)*$"

  # 必须有 operationId
  operation-id-required:
    description: Every operation must have an operationId
    given: "$.paths[*][*]"
    severity: error
    then:
      field: operationId
      function: truthy

  # operationId 必须使用 camelCase
  operation-id-camelcase:
    description: operationId must use camelCase
    given: "$.paths[*][*].operationId"
    severity: error
    then:
      function: pattern
      functionOptions:
        match: "^[a-z][a-zA-Z0-9]*$"

  # 响应必须有 schema
  response-schema-required:
    description: Every response with content must have a schema
    given: "$.paths[*][*].responses[*].content.*"
    severity: error
    then:
      field: schema
      function: truthy

  # 必须有描述
  description-required:
    description: Every operation must have a description
    given: "$.paths[*][*]"
    severity: warn
    then:
      field: description
      function: truthy

  # 错误响应必须引用通用 error schema
  error-response-schema:
    description: 4xx/5xx responses must use common error schema
    given: "$.paths[*][*].responses[?(@property >= '400')].content[*].schema"
    severity: error
    then:
      function: schema
      functionOptions:
        schema:
          type: object
          required: [code, message]
          properties:
            code:
              type: string
            message:
              type: string
```

---

## 第 3 章：契约测试

### 3.1 契约测试在 Pipeline 中的位置

契约测试在 [06-cicd-pipeline.md](06-cicd-pipeline.md) L4 层（集成验证层）执行：

| 层级 | 契约测试角色 |
|------|------------|
| **L2（测试验证）** | 单元测试覆盖 handler 级别逻辑，不涉及 HTTP 层 |
| **L3（质量审查）** | `scripts/check-api-drift.py` 检测实现 vs Spec 的漂移 |
| **L4（集成验证）** | Pact/Dredd 端到端契约验证，**阻断合并** |

### 3.2 Dredd — 服务端契约验证

Dredd 验证实际 HTTP 响应是否符合 OpenAPI Spec 定义。

```yaml
# .github/workflows/contract-test.yml (节选)
contract-test:
  name: Dredd Contract Test
  runs-on: ubuntu-latest
  timeout-minutes: 15
  steps:
    - uses: actions/checkout@v4
    - name: Build and start server (test mode)
      run: make test-server &
    - name: Wait for server ready
      run: wait-for-it localhost:3000 --timeout=30
    - name: Run Dredd
      run: |
        dredd specs/api/openapi.yaml http://localhost:3000 \
          --config dredd.yml \
          --reporter api-elements \
          --output .gate/dredd-report.json
    - name: Upload evidence
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: contract-test-evidence
        path: .gate/
```

**Dredd 配置要点**：

```yaml
# dredd.yml
dry-run: false
reporter: [junit, cli]
output: [.gate/dredd-report.json]
language: ""
server-wait: 5
init: false
custom: {}
names: false
only: []
server: ""
server-ready: false
```

**AI 特有规则**：
- AI 生成新端点后，必须同时生成对应的 Dredd hook 文件
- Dredd 失败 = L4 不通过 = PR 不得合并
- Dredd 输出必须写入 `.gate/dredd-report.json` 作为证据链的一部分（P11）

### 3.3 Pact — Consumer-Driven 契约测试

适用于微服务架构，消费者定义期望，提供者验证能否满足。

```
Consumer (Frontend/Service A)          Provider (Service B)
┌──────────────────┐                   ┌──────────────────┐
│ 1. 定义 Pact     │                   │                  │
│    (期望请求/响应)│                   │                  │
│                  │── 2. Pact 文件 ──→│                  │
│                  │   (JSON)          │                  │
│                  │                   │ 3. 验证 Pact     │
│                  │                   │    能否满足期望   │
│ 5. 确认兼容      │←── 4. 验证结果 ───│                  │
│                  │                   │                  │
│ 6. 发布到 Broker │←── publish ──────→│ 7. 验证通过     │
└──────────────────┘                   └──────────────────┘
```

**Pact 工作流程**：

```yaml
# CI 中 Consumer 侧
pact-consumer-test:
  steps:
    - uses: actions/checkout@v4
    - name: Run consumer tests
      run: make test-consumer
    - name: Generate and publish Pact
      run: |
        pact-broker publish pacts/ \
          --consumer-app-version $GIT_SHA \
          --broker-base-url $PACT_BROKER_URL

# CI 中 Provider 侧
pact-provider-verify:
  needs: pact-consumer-test
  steps:
    - uses: actions/checkout@v4
    - name: Start provider
      run: make test-server &
    - name: Verify against Pact Broker
      run: |
        pact-provider-verifier \
          --provider-base-url http://localhost:3000 \
          --broker-base-url $PACT_BROKER_URL \
          --provider-app-version $GIT_SHA \
          --publish-verification-results
    - name: Can I Deploy
      run: |
        pact-broker can-i-deploy \
          --pacticipant service-b \
          --broker-base-url $PACT_BROKER_URL
```

**Pact 管理规则**：

| 规则 | 说明 |
|------|------|
| **消费者驱动** | Pact 文件由消费者侧测试生成，不由提供者侧手写 |
| **Pact Broker 集中管理** | 所有 Pact 文件发布到 Pact Broker，不得通过文件传输 |
| **Can-I-Deploy 门禁** | 部署前必须通过 `pact-broker can-i-deploy` 检查 |
| **Pact 版本绑定 Git SHA** | 每次 Pact 发布必须绑定提供者的 Git commit SHA |
| **AI 生成消费者测试时必须包含 Pact** | 这是 P3 TDD 先行的延伸——消费者测试 = Pact 定义 |

### 3.4 API Drift 检测

Drift = 代码实现的行为与 OpenAPI Spec 定义不一致。

| 检测方式 | 工具 | 运行时机 | 阻断？ |
|---------|------|---------|:------:|
| **静态漂移** | `scripts/check-api-drift.py` | L3 质量审查层 | 警告→阻断 |
| **动态漂移** | Dredd（实际 HTTP 调用） | L4 集成验证层 | **是** |
| **Schema 漂移** | `spectral` lint | L0 pre-commit | **是** |
| **运行时漂移** | 代理层对比（Envoy/NGINX） | 运行时 | 告警 |

**静态漂移检测逻辑**：

```
1. 解析 OpenAPI Spec 中的所有路径和操作
2. 扫描代码中的路由定义（从框架中提取）
3. 比对两端点集合：
   - Spec 有但代码无 → 缺失实现
   - 代码有但 Spec 无 → 未文档化端点
   - 两者都有但参数/schema 不匹配 → 漂移
4. 输出 drift-report.json 到 .gate/
```

**漂移严重级别**：

| 级别 | 条件 | 处理 |
|------|------|------|
| **BLOCK** | 端点完全缺失（Spec 有代码无，或反之） | L3 阻断 |
| **BLOCK** | 请求参数不匹配（类型/必填/枚举） | L3 阻断 |
| **BLOCK** | 响应 schema 不兼容（字段缺失或类型改变） | L3 阻断 |
| **WARN** | 描述文字不一致 | 记录到 PR 描述 |
| **WARN** | Example 与实际响应字段不完全匹配 | 记录到 PR 描述 |

---

## 第 4 章：向后兼容性规则

### 4.1 变更分类矩阵

| 变更类型 | 示例 | 兼容性 | 是否可独立发布 |
|---------|------|:------:|:-------------:|
| **新增端点** | `POST /api/v1/users` | 完全兼容 | **是** |
| **新增可选请求参数** | `GET /users?sort=name`（不传=默认排序） | 兼容 | **是** |
| **新增响应字段** | 用户响应新增 `avatar_url` | 兼容 | **是** |
| **新增枚举值** | `status` 枚举新增 `"archived"` | 兼容 | **是** |
| **扩展错误码** | 新增 429 Too Many Requests 响应 | 兼容 | **是** |
| **新增可选请求头** | `X-Request-Id` | 兼容 | **是** |
| **响应字段默认值扩展** | 字段从 `required` 改为 `optional` 且提供默认值 | 兼容 | **是** |
| **---** | **---** | **---** | **---** |
| **删除端点** | 移除 `GET /api/v1/legacy/users` | **破坏** | 否 |
| **删除/重命名字段** | 移除 `user.name` 或改名 `user.full_name` | **破坏** | 否 |
| **字段类型变更** | `age: integer` → `age: string` | **破坏** | 否 |
| **必填变可选（无默认值）** | 删除参数校验逻辑 | **破坏** | 否 |
| **HTTP 方法变更** | `POST` → `PUT` | **破坏** | 否 |
| **状态码变更** | 成功响应从 200 → 201 | **破坏** | 否 |
| **路径变更** | `/users` → `/customers` | **破坏** | 否 |
| **认证方式变更** | API Key → OAuth2 | **破坏** | 否 |
| **分页方式变更** | offset/limit → cursor | **破坏** | 否 |
| **枚举值删除** | 移除 `"active"` 状态 | **破坏** | 否 |
| **参数顺序/位置变更** | path param → query param | **破坏** | 否 |

### 4.2 AI 兼容性自动检查

AI 生成代码时，CI 自动运行兼容性检查：

```yaml
# CI 兼容性检查步骤
api-compatibility-check:
  steps:
    - name: Extract API changes
      run: |
        python scripts/extract-api-changes.py \
          --base ${{ github.event.before }} \
          --head ${{ github.sha }} \
          --output .gate/api-changes.json

    - name: Classify breaking changes
      run: |
        python scripts/classify-breaking-changes.py \
          --changes .gate/api-changes.json \
          --output .gate/breaking-changes.json

    - name: Block on breaking changes
      if: steps.classify.outputs.breaking_count > 0
      run: |
        echo "Breaking changes detected:"
        cat .gate/breaking-changes.json
        exit 1
```

**兼容性分类脚本输出**：

```json
// .gate/breaking-changes.json
{
  "summary": {
    "compatible_changes": 3,
    "breaking_changes": 1,
    "blocked": true
  },
  "breaking": [
    {
      "type": "field_removed",
      "path": "/api/v1/users",
      "field": "legacy_id",
      "severity": "BLOCK",
      "rule": "R-BC-04: 不得删除已发布字段"
    }
  ],
  "compatible": [
    {
      "type": "field_added",
      "path": "/api/v1/users",
      "field": "avatar_url",
      "rule": "R-BC-03: 新增可选字段安全"
    }
  ]
}
```

### 4.3 兼容性规则速查

| 规则编号 | 规则 | 违反后果 |
|---------|------|---------|
| **R-BC-01** | 不得删除已有端点 | CI 阻断 |
| **R-BC-02** | 不得删除已有请求参数 | CI 阻断 |
| **R-BC-03** | 新增字段必须可选或提供默认值 | CI 阻断 |
| **R-BC-04** | 不得删除已有响应字段 | CI 阻断 |
| **R-BC-05** | 不得变更字段类型 | CI 阻断 |
| **R-BC-06** | 不得变更 HTTP 方法语义 | CI 阻断 |
| **R-BC-07** | 不得变更必填约束（required→optional 除外且有条件） | CI 阻断 |
| **R-BC-08** | 不得删除枚举值 | CI 阻断 |
| **R-BC-09** | 不得变更认证方式 | CI 阻断 |
| **R-BC-10** | 不得变更分页机制 | CI 阻断 |

**R-BC-07 的有条件规则**：`required` → `optional` 是兼容的仅当：(a) 字段在服务端有合理的默认值，且 (b) 默认值不会改变已有消费者的行为语义。

---

## 第 5 章：破坏性变更通知机制

### 5.1 破坏性变更的定义

破坏性变更（Breaking Change）= 现有消费者在不修改代码的情况下，调用新 API 会出现失败或行为改变。

### 5.2 通知时间线

```
T-90天  发布 Deprecation Notice（废弃通知）
  ↓
T-60天  发布 Migration Guide（迁移指南）
  ↓
T-30天  发送 Final Warning（最终警告）
  ↓
T-0     执行破坏性变更 + 旧版本继续运行（并行期）
  ↓
T+30天  旧版本停止服务（Sunset）
```

### 5.3 通知渠道矩阵

| 渠道 | 触发时机 | 通知对象 | 内容 |
|------|---------|---------|------|
| **API Response Header** | 每次调用废弃端点 | 调用方应用 | `Sunset: <date>` + `Deprecation: true` |
| **API 开发者门户** | 废弃通知发布时 | 所有 API 消费者 | 废弃列表 + 迁移指南 |
| **邮件通知** | T-90/T-30 天 | 已注册的 API 密钥所有者 | 变更详情、影响范围、迁移步骤 |
| **Slack/Teams** | 废弃通知发布 + 最终警告 | 内部开发团队 | `#api-changes` channel 消息 |
| **PR/Release Notes** | 包含破坏性变更的 PR | Code Reviewer | PR 描述中必须标注 `BREAKING:` |
| **OpenAPI x-deprecated 扩展** | Spec 中标记废弃 | Spec 消费者/工具 | 字段级别的 `x-deprecated` 标记 |

### 5.4 废弃端点的 HTTP 响应头

```
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Aug 2026 00:00:00 GMT
Link: <https://docs.example.com/migration/v2-users>; rel="successor-version"

{
  "id": 123,
  "name": "John Doe",
  "legacy_id": "abc123"
}
```

| 响应头 | 说明 |
|--------|------|
| `Deprecation: true` | 标记此端点/字段已被废弃 |
| `Sunset: <HTTP-date>` | 此端点将被完全移除的日期 |
| `Link: <url>; rel="successor-version"` | 新版本的文档链接 |

### 5.5 OpenAPI Spec 中的废弃标记

```yaml
paths:
  /api/v1/users/{id}:
    get:
      deprecated: true
      summary: Get user by ID (deprecated, use v2)
      x-deprecated-reason: "Use /api/v2/users/{id} instead"
      x-deprecated-date: "2026-04-18"
      x-migration-guide: "https://docs.example.com/migrate/v1-to-v2"
```

### 5.6 AI 生成破坏性变更时的强制流程

```
1. AI 识别变更是否破坏性 → 自动分类
2. 如果是破坏性 → 阻断 CI，生成 BreakingChangeRequest
3. BreakingChangeRequest 必须包含：
   a. 变更详情（字段、端点、影响范围）
   b. 替代方案（新版本端点或迁移路径）
   c. 影响评估（已知消费者列表）
   d. 时间线（90 天废弃计划）
4. 人工审批 BreakingChangeRequest → 审批通过
5. 创建废弃通知 + 迁移指南文档
6. 发布通知到所有渠道
7. 并行发布新版本（不得先删后建）
8. 等待废弃期结束后再移除旧端点
```

---

## 第 6 章：版本策略

### 6.1 版本化方案选择

| 方案 | 示例 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|---------|
| **URL 版本** | `/api/v1/users` | 明确、可缓存、易调试 | URL 膨胀、浏览器可见 | **默认选择，外部 API** |
| **Header 版本** | `Accept: application/vnd.myapi.v2+json` | URL 干净、REST 纯粹 | 难调试、缓存复杂 | 内部微服务 API |
| **Query 版本** | `/api/users?version=2` | 简单 | 不安全、难缓存 | **禁止使用** |
| **内容协商** | `Accept-Version: v2` | 标准 | 支持度差 | **不推荐** |

### 6.2 推荐策略：URL 版本为主，Header 版本为辅

**外部 API（面向第三方/公开）**：

```
https://api.example.com/v1/users      # 当前稳定版本
https://api.example.com/v2/users      # 新版本
```

**内部 API（微服务间）**：

```
URL:  https://internal.service/v2/orders
Header: Accept-Version: v2.1.0         # 次版本/补丁版本用 Header
```

**版本选择规则**：

| 变更类型 | 版本变化 | 版本化方式 |
|---------|---------|-----------|
| 破坏性变更 | `v1` → `v2`（Major） | **URL 路径** |
| 新增端点/字段（兼容） | 不变，或 `v2.1`（Minor） | Header 或 URL 均可 |
| Bug 修复 | 不变，或 `v2.1.1`（Patch） | **不体现版本** |
| 字段废弃 | 不变，标记 `deprecated: true` | 不升级版本 |

### 6.3 主版本号选择规则

**何时升级主版本号（v1 → v2）**：

满足以下任一条件时必须升级：
1. 删除已有端点或字段
2. 变更已有字段的类型
3. 变更已有端点的 HTTP 方法
4. 变更认证机制
5. 变更错误响应格式
6. 删除枚举值

**不升级主版本号的情况**：
- 新增端点
- 新增可选字段
- 新增错误码
- 新增枚举值
- Bug 修复（不改变已有行为）

### 6.4 废弃与生命周期政策

| 阶段 | 时长 | 状态 | AI 行为 |
|------|------|------|--------|
| **Active** | 从发布到废弃通知 | 正常维护 | AI 正常生成/修改代码 |
| **Deprecated** | 废弃通知后 ≥90 天 | 仅安全修复 | AI 不得在 Deprecated 端点上新增功能 |
| **Sunset** | 废弃后 ≥90 天 | 返回 410 Gone | AI 可安全移除代码和 Spec |
| **Removed** | Sunset 后 | 端点不存在 | Spec 中删除，代码中删除 |

**最小支持版本数**：同时必须至少有 **1 个 Active 版本**。不得出现"所有版本都已废弃"的空窗期。

### 6.5 版本迁移的 AI 辅助

| 任务 | AI 执行方式 |
|------|-----------|
| **迁移路径生成** | AI 读取 v1 和 v2 的 Spec，自动生成端点/字段映射表 |
| **消费者影响分析** | AI 分析日志/监控数据，识别使用废弃端点的消费者 |
| **迁移代码生成** | AI 生成从 v1 到 v2 的适配层代码 |
| **变更日志生成** | AI 对比两个版本的 Spec，自动生成 CHANGELOG |

---

## 第 7 章：AI 特定规则

### 7.1 AI 必须遵守的契约规则

| 规则 | 编号 | 说明 | 验证方式 |
|------|------|------|---------|
| **Spec 与代码同生** | AC-01 | 生成 API 代码的同时必须生成/更新 OpenAPI Spec | CI 文件扫描 |
| **Spec 先于代码提交** | AC-02 | Spec commit 时间戳必须早于代码 commit | CI commit 顺序检查 |
| **不得生成无 Spec 端点** | AC-03 | 代码中的路由必须在 Spec 中有对应定义 | Drift 检测 |
| **不得跳过契约测试** | AC-04 | 新端点必须有 Dredd/Pact 测试 | CI 检查测试覆盖率 |
| **不得生成不兼容变更** | AC-05 | 破坏性变更必须走 BreakingChangeRequest 流程 | CI 兼容性检查 |
| **不得编造 HTTP 状态码** | AC-06 | 仅使用标准 HTTP 状态码，语义必须正确 | Spec lint |
| **不得省略错误响应** | AC-07 | 每个端点必须定义 4xx 和 5xx 响应 schema | Spec 完整性扫描 |
| **不得生成重复 operationId** | AC-08 | operationId 必须全局唯一 | Spec lint |
| **不得使用内部字段名** | AC-09 | 对外字段名使用 camelCase，内部 snake_case 需映射 | 命名规范检查 |

### 7.2 AI 生成 API 代码的标准模板

当 AI 生成新 API 端点时，必须按以下顺序产出：

```
Phase 1 — Spec（独立 commit）:
  specs/api/paths/{resource}.yaml          # 端点定义
  specs/api/schemas/{resource}.yaml        # 数据模型
  specs/api/examples/{resource}-*.yaml     # 示例

Phase 2 — 实现（独立 commit）:
  src/api/handlers/{resource}.go           # Handler 实现
  src/api/routes/{resource}.go             # 路由注册
  src/api/dto/{resource}.go                # DTO/序列化

Phase 3 — 测试（独立 commit）:
  src/api/handlers/{resource}_test.go      # 单元测试
  tests/contract/{resource}.dredd.yml      # Dredd hook
  pacts/{consumer}-{provider}.json         # Pact（微服务场景）
```

### 7.3 AI 幻觉防护 — API 专项

针对 API 场景的幻觉类型及防护：

| 幻觉类型 | 编号 | 表现 | 防护 |
|---------|------|------|------|
| 虚构端点 | E01-API | 调用了 Spec 中不存在的端点 | Drift 检测 + Dredd |
| 虚构字段 | E04-API | 使用了 schema 中不存在的字段 | Schema 验证 |
| 错误状态码 | L07-API | 返回 200 但实际是错误场景 | Spec 状态码校验 |
| 遗漏验证 | L02-API | 未校验请求参数边界 | 输入校验模板 |
| 异步竞态 | L05-API | 并发写响应、连接未关闭 | Handler 模板 + lint |
| 完成幻觉 | C01-API | 声称"实现了 RESTful API"但只实现了 GET | AC 映射验证 |

### 7.4 AI 在 L3/L4 自治等级下的 API 行为约束

| 等级 | API Spec 变更 | 破坏性变更 | 契约测试 |
|------|-------------|-----------|---------|
| **L1** | 人工编写 Spec，人工评审 | 人工审批全流程 | 人工编写 |
| **L2** | AI 生成 Spec，人工审核 | 人工审批 BreakingChangeRequest | AI 生成，人工审核 |
| **L3** | AI 生成并自动验证 Spec | 自动检测 + 通知，人工审批 | AI 生成并自动运行 |
| **L4** | AI 全自动（兼容变更） | 自动检测 + 自动通知，定期审计 | AI 全自动 |

---

## 第 8 章：CI 集成与门禁

### 8.1 API 契约相关的 CI 门禁总览

所有门禁集成到 [06-cicd-pipeline.md](06-cicd-pipeline.md) 的 Pipeline 层级：

| Pipeline 层 | API 相关检查 | 阻断？ |
|------------|-------------|:------:|
| **L0** | Spectral lint（格式、命名、规范） | **是** |
| **L1** | OpenAPI Spec 可解析性（swagger-cli validate） | **是** |
| **L2** | 单元测试覆盖 handler 逻辑 | **是** |
| **L3** | 静态 API Drift 检测、AI Reviewer API 审查（AC-01 至 AC-09） | **是** |
| **L4** | Dredd 契约测试、Pact 验证、AC 映射验证 | **是** |
| **L5** | 金丝雀部署中的 API 兼容性验证 | **是** |

### 8.2 CI 状态报告

API 契约 CI 结果必须输出到 `.gate/` 目录：

```
.gate/
├── spec-lint.json              # Spectral lint 结果
├── spec-validate.json          # swagger-cli 验证结果
├── api-drift.json              # 静态漂移报告
├── dredd-report.json           # Dredd 契约测试输出
├── pact-verify.json            # Pact 验证结果
├── breaking-changes.json       # 破坏性变更分类
├── api-changes.json            # API 变更提取
└── evidence/
    ├── spec-examples-coverage.json  # Example 覆盖证据
    └── contract-test-logs.json      # 契约测试日志
```

### 8.3 自动化修复策略

| 失败类型 | AI 可自修？ | 最大轮次 | 说明 |
|---------|:----------:|:--------:|------|
| Spectral lint 警告 | **是** | 1 轮 | 命名规范、描述缺失 |
| Spec 解析失败 | **是** | 2 轮 | YAML 语法、引用错误 |
| Drift 检测 BLOCK | **是** | 2 轮 | 补充缺失 Spec 字段 |
| Dredd 失败 | **是** | 3 轮 | 响应格式修正 |
| Pact 不兼容 | **否** | — | 需要人工分析契约冲突 |
| 破坏性变更未走流程 | **否** | — | 必须人工审批 |
| Example 覆盖率低 | **是** | 1 轮 | 补充示例文件 |

---

## 第 9 章：微服务 API 契约管理

### 9.1 服务间契约定义

微服务架构下，每个服务既是 API 的提供者也是消费者：

```
┌─────────┐     Pact      ┌─────────┐
│ Service │ ────────────→ │ Service │
│   A     │  (consumer)   │   B     │
│         │ ←──────────── │         │
│         │   OpenAPI     │         │
│         │  (provider)   │         │
└─────────┘               └─────────┘
```

| 契约类型 | 方向 | 格式 | 工具 |
|---------|------|------|------|
| **对外 API** | 服务 → 外部消费者 | OpenAPI Spec | Dredd |
| **服务间调用** | 消费者服务 → 提供者服务 | Pact JSON | Pact Broker |
| **事件契约** | 事件发布者 → 事件订阅者 | AsyncAPI Schema | Schema Registry |

### 9.2 服务注册与契约发现

```
specs/api/
├── services/
│   ├── user-service/
│   │   ├── openapi.yaml          # 对外 API
│   │   └── pacts/                # 作为提供者的 Pact
│   │       ├── frontend-user-service.json
│   │       └── order-service-user-service.json
│   ├── order-service/
│   │   ├── openapi.yaml
│   │   └── pacts/
│   │       └── frontend-order-service.json
│   └── payment-service/
│       ├── openapi.yaml
│       └── pacts/
│           └── order-service-payment-service.json
```

**AI 生成微服务代码时的契约规则**：
1. 新服务必须生成 `openapi.yaml`（对外 API 定义）
2. 调用其他服务时，必须生成 Pact 消费者测试
3. 发布事件时，必须定义 AsyncAPI schema
4. AI 不得假设其他服务的内部实现——只能通过契约交互

### 9.3 跨服务版本协调

| 场景 | 策略 |
|------|------|
| 服务 A 调用服务 B 的 v1 API，服务 B 升级到 v2 | 服务 B 必须并行支持 v1+v2（90 天过渡），服务 A 在此期间迁移到 v2 |
| 服务 A 和 B 同时需要破坏性变更 | 原子发布：两个服务在同一 Release Train 中一起部署 |
| 服务 A 的变更不影响服务 B | 独立发布，但必须通过 Pact Broker 验证 can-i-deploy |

---

## 第 10 章：证据链与可追溯性

### 10.1 API 契约的证据链

每个 API 端点的完整证据链必须包含：

```
声明: "POST /api/v1/users 已实现"

1. 意图证据 → specs/api/paths/users.yaml 中的端点定义
2. 计划证据 → specs/api/schemas/user.yaml 中的数据模型
3. 行动证据 → src/api/handlers/users.go 中的代码实现
4. 验证证据 → .gate/dredd-report.json 中的契约测试通过记录
5. 审查证据 → .gate/ai-review.json 中 AC-01~AC-09 的通过记录
```

### 10.2 证据链的机器可验证性（P11 要求）

| 证据层 | 文件 | 验证命令 |
|--------|------|---------|
| 意图 | `specs/api/paths/users.yaml` | `swagger-cli validate` |
| 行动 | `src/api/handlers/users.go` | `go build ./...` |
| 验证 | `.gate/dredd-report.json` | `jq '.summary.passed' .gate/dredd-report.json` |
| 审查 | `.gate/ai-review.json` | `jq '.ac_checks[] \| select(.rule \|"startswith"("AC-"))' .gate/ai-review.json` |

**证据链断裂 = 端点未完成 = AC 覆盖率 < 100% = L4 不通过。**

---

## 附录 A：快速检查清单

### A.1 AI 生成 API 代码前的检查

- [ ] 是否已读取最新的 OpenAPI Spec？
- [ ] 新端点是否已在 Spec 中定义？
- [ ] 数据模型是否已在 schema 中定义？
- [ ] 错误响应 schema 是否已定义？
- [ ] 示例（example）是否已提供？

### A.2 AI 生成 API 代码后的检查

- [ ] Spec 是否与实现一致（无漂移）？
- [ ] 契约测试是否通过（Dredd/Pact）？
- [ ] 兼容性检查是否通过（无破坏性变更或已走流程）？
- [ ] `.gate/` 中的证据文件是否完整？
- [ ] operationId 是否全局唯一？
- [ ] 所有响应是否有 schema 定义？

### A.3 人工审查 API 变更时的检查

- [ ] 破坏性变更是否有 BreakingChangeRequest？
- [ ] 废弃通知是否已发布？
- [ ] 迁移指南是否可用？
- [ ] 消费者影响评估是否完成？
- [ ] 版本升级是否符合版本策略？

---

## 附录 B：工具链参考

| 工具 | 用途 | 安装命令 |
|------|------|---------|
| **OpenAPI Parser** | Spec 语法验证 | `npm install -g @apidevtools/swagger-cli` |
| **Spectral** | Spec lint 和规则检查 | `npm install -g @stoplight/spectral` |
| **Dredd** | HTTP 契约测试 | `npm install -g dredd` |
| **Pact CLI** | Consumer-Driven 契约测试 | 见 [pact.io](https://pact.io) |
| **openapi-diff** | Spec 版本对比 | `npm install -g @openapitools/openapi-diff` |
| **swagger-diff** | 破坏性变更检测 | `npm install -g swagger-diff` |

---

## 附录 C：与其他规范的交叉引用

| 引用 | 来源文档 | 说明 |
|------|---------|------|
| **P6 单一信息源** | 01-core-specification.md | API Spec 是接口行为的唯一信息源 |
| **P7 Spec 驱动** | 01-core-specification.md | AI 生成 API 代码必须以 OpenAPI Spec 为输入 |
| **P8 最小批量** | 01-core-specification.md | Spec 文件按资源拆分，单文件≤200 行 |
| **P11 证据链** | 01-core-specification.md + 07-anti-hallucination.md | 契约测试证据写入 `.gate/` |
| **L4 契约测试** | 06-cicd-pipeline.md | Dredd/Pact 在 L4 层运行 |
| **L3 Drift 检测** | 06-cicd-pipeline.md | 静态 API 漂移在 L3 层检查 |
| **A01-A09 审查** | 05-tool-reference.md | AI Reviewer 的 API 代码审查清单 |
| **E01/E04 幻觉** | 07-anti-hallucination.md | 虚构端点/字段的防护 |
| **L07 状态幻觉** | 07-anti-hallucination.md | HTTP 状态码错误 |
| **C01 完成幻觉** | 07-anti-hallucination.md | 端点覆盖度检查 |
