# AI Coding 规范 v5.2：工具参考

> 版本：v5.2 | 2026-04-17
> 定位：配置参考、命令速查、模板库、故障排查
> 前置：必须阅读 01-core-specification.md
> 数据源：Claude Code 官方文档 (code.claude.com/docs) + 社区实战 + 自动编码专项研究
> 变更：基于 v5.1 引入 solution-quality-gate.sh、domain-knowledge/ 目录、设计模板

---

## 目录

1. [第 1 章：CLI 完整参考](#第-1-章cli-完整参考)
2. [第 2 章：Settings 配置](#第-2-章settings-配置)
3. [第 3 章：Hooks 系统](#第-3-章hooks-系统)
4. [第 4 章：Skills 系统](#第-4-章skills-系统)
5. [第 5 章：Memory 系统](#第-5-章memory-系统)
6. [第 6 章：配置模板库](#第-6-章配置模板库)
7. [第 7 章：故障排查](#第-7-章故障排查)
8. [第 8 章：快速参考卡](#第-8-章快速参考卡)

---

## 第 1 章：CLI 完整参考

### 1.1 系统要求

| 要求 | 值 |
|---|---|
| **操作系统** | macOS 13.0+, Windows 10 1809+, Windows Server 2019+, Ubuntu 20.04+, Debian 10+, Alpine 3.19+ |
| **硬件** | 4 GB+ RAM, x64 或 ARM64 |
| **网络** | 需要互联网连接（从 storage.googleapis.com 下载） |
| **Shell** | Bash, Zsh, PowerShell, CMD。Windows 原生需要 Git for Windows |
| **附加依赖** | ripgrep（内置，备选：安装系统 ripgrep + `USE_BUILTIN_RIPGREP=0`） |
| **账户** | Claude Pro、Max、Team、Enterprise 或 Console (API)。免费计划不包含 Claude Code |
| **替代提供商** | Amazon Bedrock, Google Vertex AI, Microsoft Foundry |

### 1.2 安装方法

#### 原生安装（推荐 - 自动更新）

```bash
# macOS / Linux / WSL
curl -fsSL https://claude.ai/install.sh | bash

# Windows PowerShell
irm https://claude.ai/install.ps1 | iex

# Windows CMD
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

#### 包管理器（不自动更新）

```bash
# Homebrew (macOS/Linux)
brew install --cask claude-code          # stable 频道
brew install --cask claude-code@latest   # latest 频道
brew upgrade claude-code                 # 手动更新

# WinGet (Windows)
winget install Anthropic.ClaudeCode
winget upgrade Anthropic.ClaudeCode      # 手动更新
```

#### 版本锁定

```bash
# 安装 stable 频道
curl -fsSL https://claude.ai/install.sh | bash -s stable

# 安装指定版本（如 2.1.89）
curl -fsSL https://claude.ai/install.sh | bash -s 2.1.89
```

#### 卸载

```bash
# 原生安装卸载
rm -f ~/.local/bin/claude && rm -rf ~/.local/share/claude

# 删除配置文件（将清除所有设置和历史）
rm -rf ~/.claude ~/.claude.json
```

### 1.3 启动命令

```bash
# 交互模式
claude

# 带初始提示
claude "explain this project"

# 打印模式（非交互）
claude -p "explain this function"

# 管道模式
cat file | claude -p "query"

# 继续最近会话
claude -c

# 恢复指定会话
claude -r "auth-refactor" "Finish this PR"

# 更新到最新版本
claude update
```

### 1.4 所有 CLI 标志（Flags）详解

#### 核心操作标志

| 标志 | 说明 | 示例 |
|---|---|---|
| `--print`, `-p` | 打印响应，非交互模式 | `claude -p "query"` |
| `--continue`, `-c` | 加载当前目录最近的会话 | `claude --continue` |
| `--resume`, `-r` | 按 ID/名称恢复会话，或显示选择器 | `claude --resume auth-refactor` |
| `--name`, `-n` | 设置会话显示名称 | `claude -n "my-feature-work"` |
| `--version`, `-v` | 输出版本号 | `claude -v` |

#### 权限与安全标志

| 标志 | 说明 | 示例 |
|---|---|---|
| `--permission-mode` | 起始权限模式 | `--permission-mode plan` |
| `--dangerously-skip-permissions` | 跳过所有权限提示 | `claude --dangerously-skip-permissions` |
| `--allow-dangerously-skip-permissions` | 在 Shift+Tab 循环中添加 bypassPermissions | `--permission-mode plan --allow-dangerously-skip-permissions` |
| `--allowedTools` | 无需提示即可执行的工具 | `--allowedTools "Bash(npm run lint)" "Read"` |
| `--disallowedTools` | 模型无法使用的工具 | `--disallowedTools "Bash(curl *)"` |
| `--tools` | 限制可用工具集 | `claude --tools "Bash,Edit,Read"` |

#### 系统提示标志

| 标志 | 说明 |
|---|---|
| `--system-prompt` | 替换整个默认系统提示 |
| `--system-prompt-file` | 从文件加载系统提示，替换默认提示 |
| `--append-system-prompt` | 追加文本到默认系统提示 |
| `--append-system-prompt-file` | 从文件加载并追加到默认系统提示 |

注：`--system-prompt` 和 `--system-prompt-file` 互斥。追加标志可与任一替换标志组合。自动化场景优先使用追加标志以保留内置能力。

#### 模型与性能标志

| 标志 | 说明 | 示例 |
|---|---|---|
| `--model` | 设置模型：别名或完整名称 | `claude --model claude-sonnet-4-6` |
| `--effort` | 设置努力程度：low/medium/high/max | `claude --effort high` |
| `--max-budget-usd` | 最大美元支出（仅打印模式） | `--max-budget-usd 5.00` |
| `--max-turns` | 限制 agentic 轮次（仅打印模式） | `--max-turns 3` |
| `--always-thinking` | 始终启用思考 | `claude --always-thinking` |

#### 输出格式标志

| 标志 | 说明 | 示例 |
|---|---|---|
| `--output-format` | 输出格式：text/json/stream-json | `--output-format json` |
| `--input-format` | 输入格式：text/stream-json | `--input-format stream-json` |
| `--json-schema` | 按 JSON Schema 验证输出 | `--json-schema '{"type":"object"}'` |
| `--include-hook-events` | 包含钩子生命周期事件（需 stream-json） | `--include-hook-events` |
| `--include-partial-messages` | 包含部分流事件 | `--include-partial-messages` |
| `--replay-user-messages` | 在 stdout 回显用户消息 | `--replay-user-messages` |

#### 自动化与脚本标志

| 标志 | 说明 | 示例 |
|---|---|---|
| `--bare` | 最小模式：跳过 hooks/skills/plugins/MCP/auto-memory/CLAUDE.md 自动发现。设置 `CLAUDE_CODE_SIMPLE`。适合脚本调用 | `claude --bare -p "query"` |
| `--exclude-dynamic-system-prompt-sections` | 将每台机器特有的系统提示部分移入第一条用户消息。改善脚本/多用户场景的提示缓存复用 | `claude -p --exclude-dynamic-system-prompt-sections "query"` |
| `--no-session-persistence` | 禁用会话持久化（仅打印模式） | `--no-session-persistence` |
| `--session-id` | 使用特定会话 UUID | `--session-id "550e8400-..."` |
| `--fork-session` | 恢复时创建新会话 ID | `--resume abc123 --fork-session` |

#### Agent 与 Sub-Agent 标志

| 标志 | 说明 | 示例 |
|---|---|---|
| `--agent` | 指定代理（覆盖 `agent` 设置） | `claude --agent my-custom-agent` |
| `--agents` | 通过 JSON 动态定义自定义子代理 | `--agents '{"reviewer":{"description":"...","prompt":"..."}}'` |

#### Git 与 Worktree 标志

| 标志 | 说明 | 示例 |
|---|---|---|
| `--worktree`, `-w` | 在隔离的 git worktree 中启动 | `claude -w feature-auth` |
| `--tmux` | 创建 tmux 会话（需配合 `--worktree`） | `claude -w feature-auth --tmux` |
| `--from-pr` | 从 GitHub PR 恢复会话 | `claude --from-pr 123` |

#### 多平台与集成标志

| 标志 | 说明 | 示例 |
|---|---|---|
| `--remote` | 创建 claude.ai 上的新 Web 会话 | `claude --remote "Fix the login bug"` |
| `--remote-control`, `--rc` | 启动 Remote Control 会话 | `claude --remote-control "My Project"` |
| `--remote-control-session-name-prefix` | 自动生成的 Remote Control 会话名称前缀 | `--remote-control-session-name-prefix dev-box` |
| `--teleport` | 在本地终端恢复 Web 会话 | `claude --teleport` |
| `--chrome` | 启用 Chrome 浏览器集成 | `claude --chrome` |
| `--no-chrome` | 禁用 Chrome 浏览器集成 | `claude --no-chrome` |
| `--ide` | 启动时自动连接 IDE（仅有一个有效 IDE 时） | `claude --ide` |

#### 配置与调试标志

| 标志 | 说明 | 示例 |
|---|---|---|
| `--add-dir` | 添加额外工作目录（自动发现其 `.claude/skills/`） | `claude --add-dir ../apps ../lib` |
| `--settings` | 指定 settings JSON 文件或 JSON 字符串 | `claude --settings ./settings.json` |
| `--setting-sources` | 指定加载的设置源 | `--setting-sources user,project` |
| `--mcp-config` | 从 JSON 文件/字符串加载 MCP 服务器 | `claude --mcp-config ./mcp.json` |
| `--strict-mcp-config` | 仅使用 `--mcp-config` 中的 MCP 服务器 | `--strict-mcp-config --mcp-config ./mcp.json` |
| `--plugin-dir` | 从目录加载插件 | `claude --plugin-dir ./my-plugins` |
| `--debug` | 启用调试模式（可带类别过滤） | `claude --debug "api,mcp"` |
| `--debug-file` | 将调试日志写入文件 | `claude --debug-file /tmp/debug.log` |
| `--verbose` | 启用详细日志，显示逐轮输出 | `claude --verbose` |

#### 自动模式标志

| 标志 | 说明 |
|---|---|
| `--enable-auto-mode` | 解锁 auto 模式（需 Team/Enterprise/API 计划 + Sonnet 4.6+） |
| `--betas` | API 请求的 Beta 头（仅 API 密钥用户） |

#### 其他标志

| 标志 | 说明 | 示例 |
|---|---|---|
| `--init` | 运行初始化钩子并启动交互模式 | `claude --init` |
| `--init-only` | 仅运行初始化钩子 | `claude --init-only` |
| `--maintenance` | 运行维护钩子并启动交互模式 | `claude --maintenance` |
| `--teammate-mode` | 设置代理团队显示模式：auto/in-process/tmux | `--teammate-mode in-process` |
| `--channels` | 指定 Claude 应监听通道通知的 MCP 服务器 | `--channels plugin:my-notifier@my-marketplace` |
| `--dangerously-load-development-channels` | 启用未在白名单上的通道（本地开发） | `--dangerously-load-development-channels server:webhook` |
| `--fallback-model` | 默认模型过载时自动回退 | `--fallback-model sonnet` |
| `--disable-slash-commands` | 禁用所有技能和命令 | `claude --disable-slash-commands` |
| `--permission-prompt-tool` | 指定处理权限提示的 MCP 工具 | `--permission-prompt-tool mcp_auth_tool` |

### 1.5 子命令详解

```bash
# 认证管理
claude auth login          # 登录 Anthropic 账户
claude auth login --console  # 控制台认证模式
claude auth logout         # 登出
claude auth status         # 显示认证状态（JSON 格式）
claude auth status --text  # 显示认证状态（文本格式）

# 更新与维护
claude update              # 更新到最新版本
claude doctor              # 诊断安装/配置问题

# 子代理管理
claude agents              # 列出所有配置的子代理

# 自动模式管理
claude auto-mode defaults  # 输出内置自动模式分类器规则（JSON）
claude auto-mode config    # 显示应用了设置后的有效自动模式配置

# MCP 服务器管理
claude mcp add github -- npx -y @modelcontextprotocol/server-github
claude mcp list            # 列出已配置的 MCP 服务器
claude mcp remove <name>   # 移除 MCP 服务器

# 插件管理
claude plugin install code-review@claude-plugins-official
claude plugin list         # 列出已安装插件

# Remote Control
claude remote-control --name "My Project"

# CI/脚本令牌
claude setup-token         # 生成持久 OAuth 令牌（CI/脚本用）
```

### 1.6 管道模式（-p）完整指南

管道模式是非交互式调用，适合 CI/CD、脚本和流水线集成。

#### 基础用法

```bash
# 简单查询
claude -p "Explain what this project does"

# 管道输入
cat error.log | claude -p "Explain this build error"

# 输出重定向
cat code.py | claude -p "Analyze for bugs" > analysis.txt
```

#### 结构化输出

```bash
# JSON 输出
claude -p "List all API endpoints" --output-format json

# 流式 JSON（实时处理）
claude -p "Analyze this log file" --output-format stream-json

# 按 Schema 验证输出
claude -p --json-schema '{"type":"object","properties":{"files":{"type":"array","items":{"type":"string"}}}}' "Find all TypeScript files"
```

#### 成本与轮次控制

```bash
# 设置最大费用
claude -p "Analyze the entire codebase" --max-budget-usd 5.00

# 设置最大轮次
claude -p "Fix all type errors" --max-turns 10
```

#### 工具限制

```bash
# 仅允许特定工具
claude -p "Fix lint errors" \
  --allowedTools "Bash(npm run lint) Bash(npx prettier *) Edit Read"

# 仅允许读取工具
claude -p "Review the auth module" --tools "Read,Grep,Glob"
```

#### 自动化流水线典型调用

```bash
claude --bare -p "Review PR #123 for security issues" \
  --permission-mode auto \
  --max-budget-usd 10.00 \
  --max-turns 20 \
  --output-format stream-json \
  --allowedTools "Edit Read Bash(npm run *) Bash(git *)" \
  --no-session-persistence
```

### 1.7 环境变量参考

| 环境变量 | 说明 | 值/示例 |
|---|---|---|
| `CLAUDE_CODE_SIMPLE` | `--bare` 自动设置，禁用自动发现 | `1` |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY` | 禁用自动记忆 | `1` |
| `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` | 从 `--add-dir` 路径加载 CLAUDE.md | `1` |
| `CLAUDE_CODE_EFFORT_LEVEL` | 默认努力程度 | `low`/`medium`/`high`/`max` |
| `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING` | 禁用 Opus/Sonnet 4.6 自适应思考 | `1` |
| `CLAUDE_CODE_USE_POWERSHELL_TOOL` | Windows 启用 PowerShell 工具 | `1` |
| `CLAUDE_CODE_GIT_BASH_PATH` | Windows 上 git-bash.exe 路径 | `C:\Program Files\Git\bin\bash.exe` |
| `MAX_THINKING_TOKENS` | 限制思考 Token 预算 | `0`（仅对 Opus/Sonnet 4.6 有效） |
| `SLASH_COMMAND_TOOL_CHAR_BUDGET` | 覆盖技能描述的字符预算 | 整数 |
| `HTTPS_PROXY` / `HTTP_PROXY` | 代理服务器 | `https://proxy.example.com:8080` |
| `NODE_EXTRA_CA_CERTS` | 企业 CA 证书路径 | `/path/to/ca-bundle.pem` |
| `BROWSER` | 覆盖 OAuth 登录浏览器路径 | `/usr/bin/firefox` |
| `CLAUDE_REMOTE_CONTROL_SESSION_NAME_PREFIX` | Remote Control 会话名称前缀 | `dev-box-` |
| `CLAUDE_CODE_DEBUG_LOGS_DIR` | 调试日志目录 | `/tmp/claude-logs` |
| `CLAUDE_CODE_NEW_INIT` | 启用交互式多阶段 `/init` 流程 | `1` |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | 固定 Opus 模型版本 | `anthropic.claude-opus-4-6` |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | 固定 Sonnet 模型版本 | `anthropic.claude-sonnet-4-6` |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | 固定 Haiku 模型版本 | `anthropic.claude-haiku-4-5` |
| `CLAUDE_CODE_SKIP_BEDROCK_AUTH` | 网关处理认证时跳过 Bedrock 认证 | `1` |
| `CLAUDE_CODE_SKIP_VERTEX_AUTH` | 网关处理认证时跳过 Vertex 认证 | `1` |
| `CLAUDE_CODE_SKIP_FOUNDRY_AUTH` | 网关处理认证时跳过 Foundry 认证 | `1` |
| `ANTHROPIC_BASE_URL` | LLM 网关基础 URL（API） | `https://gateway.example.com/v1` |
| `ANTHROPIC_BEDROCK_BASE_URL` | LLM 网关基础 URL（Bedrock） | `https://gateway.example.com/bedrock` |
| `ANTHROPIC_VERTEX_BASE_URL` | LLM 网关基础 URL（Vertex） | `https://gateway.example.com/vertex` |
| `ANTHROPIC_FOUNDRY_BASE_URL` | LLM 网关基础 URL（Foundry） | `https://gateway.example.com/foundry` |
| `CLAUDE_CODE_SUBAGENT_MODEL` | 覆盖子代理模型 | `sonnet`/`opus`/`haiku` |
| `DISABLE_AUTOUPDATER` | 禁用自动更新（settings env 中设置） | `1` |
| `USE_BUILTIN_RIPGREP` | 使用内置 ripgrep | `0`（使用系统 ripgrep） |

### 1.8 安装/更新/卸载

```bash
# 安装（推荐）
curl -fsSL https://claude.ai/install.sh | bash

# 更新
claude update

# 版本锁定安装
curl -fsSL https://claude.ai/install.sh | bash -s 2.1.89

# Homebrew 安装
brew install --cask claude-code

# Homebrew 更新
brew upgrade claude-code

# 卸载
rm -f ~/.local/bin/claude && rm -rf ~/.local/share/claude
rm -rf ~/.claude ~/.claude.json
```

### 1.9 交互式键盘快捷键

| 快捷键 | 操作 |
|---|---|
| `?` | 显示所有键盘快捷键 |
| `Tab` | 命令补全 |
| `Up` | 命令历史 |
| `/` | 显示所有命令和技能 |
| `Esc` | 取消当前操作 |
| `Esc+Esc` | 打开回退菜单 |
| `Ctrl+C` | 尝试取消当前操作 |
| `Ctrl+D` / `exit` | 退出 Claude Code |
| `Ctrl+G` | 在文本编辑器中打开计划（计划模式） |
| `Ctrl+O` | 切换详细模式（显示思考） |
| `Shift+Tab` | 循环切换权限模式 |
| `Option+T` / `Alt+T` | 切换思考开/关 |

---

## 第 2 章：Settings 配置

### 2.1 配置作用域与优先级

| 作用域 | 位置 | 适用对象 | 是否共享 |
|---|---|---|---|
| **Managed（托管）** | 服务器/MDM/`/etc/claude-code/managed-settings.json` | 组织所有用户 | 是 |
| **User（用户）** | `~/.claude/settings.json` | 你，所有项目 | 否 |
| **Project（项目）** | `.claude/settings.json` | 所有协作者 | 是（git 版本控制） |
| **Local（本地）** | `.claude/settings.local.json` | 你，此仓库 | 否（通常 gitignore） |

**优先级（高到低）：**
1. Managed 设置（不可被覆盖）
2. 命令行参数（会话级）
3. Local 设置
4. Project 设置
5. User 设置

**关键规则：** 如果工具在任一级别被 deny，其他级别无法 allow。

### 2.2 settings.json 完整结构

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",

  "permissions": {
    "defaultMode": "default",
    "allow": [],
    "ask": [],
    "deny": [],
    "disableBypassPermissionsMode": "disable",
    "disableAutoMode": "disable"
  },

  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "USE_BUILTIN_RIPGREP": "0"
  },

  "autoUpdatesChannel": "stable",

  "sandbox": {
    "enabled": true,
    "filesystem": {
      "allowWrite": [],
      "denyWrite": [],
      "denyRead": [],
      "allowRead": []
    },
    "network": {
      "allowedDomains": []
    },
    "autoAllowBashIfSandboxed": true,
    "allowUnsandboxedCommands": true,
    "excludedCommands": []
  },

  "autoMemoryEnabled": true,
  "autoMemoryDirectory": "~/.claude/projects",

  "claudeMdExcludes": [],

  "model": "claude-sonnet-4-6",
  "effort": "medium",
  "alwaysThinkingEnabled": false,
  "showThinkingSummaries": false,

  "plugins": {
    "enabled": [],
    "disabled": []
  },

  "cleanupPeriodDays": 7,

  "disableSkillShellExecution": false,

  "hooks": {},

  "companyAnnouncements": [],

  "autoMode": {
    "environment": []
  },

  "allowManagedHooksOnly": false,
  "allowManagedMcpServersOnly": false,
  "allowManagedPermissionRulesOnly": false,
  "forceRemoteSettingsRefresh": false
}
```

### 2.3 所有设置项详解

#### 权限设置（permissions）

| 设置项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `permissions.defaultMode` | string | `"default"` | 起始权限模式：default/acceptEdits/plan/auto/dontAsk/bypassPermissions |
| `permissions.allow[]` | string[] | `[]` | 自动允许的工具/命令规则列表 |
| `permissions.ask[]` | string[] | `[]` | 需要询问的工具/命令规则列表 |
| `permissions.deny[]` | string[] | `[]` | 禁止的工具/命令规则列表 |
| `permissions.disableBypassPermissionsMode` | string | - | 设为 `"disable"` 禁止 bypassPermissions 模式 |
| `permissions.disableAutoMode` | string | - | 设为 `"disable"` 禁止 auto 模式 |

#### 权限规则语法

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test *)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Edit(/src/**/*.ts)",
      "Read(~/.zshrc)",
      "WebFetch(domain:example.com)",
      "mcp__puppeteer__puppeteer_navigate"
    ],
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(git push main)",
      "Bash(git push master)",
      "Bash(rm -rf *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./credentials/**)"
    ]
  }
}
```

**语法说明：**
- `Bash(pattern)` - 匹配 Shell 命令（支持 glob：`*`, `**`, `?`）
- `Bash(*)` - 匹配所有 Bash 命令
- `Read` / `Read(path)` - 文件读取（路径支持 `//` 绝对、`~/` home、`/` 项目相对、`./` cwd 相对）
- `Edit` / `Edit(path)` - 文件编辑
- `Glob` / `Glob(path)` - 文件 glob
- `Grep` - grep 工具
- `WebFetch` / `WebFetch(pattern)` - Web 抓取
- `WebSearch` - Web 搜索
- `Skill` / `Skill(name)` - 技能
- `MCP` / `MCP(server)` - MCP 服务器

**规则评估顺序：** deny -> ask -> allow。首先匹配的规则生效。Deny 规则始终优先。

**复合命令感知：** Claude Code 感知 shell 操作符（`&&`, `||`, `;`, `|`, `|&`, `&`, 换行）。`Bash(safe-cmd *)` 不授予 `safe-cmd && other-cmd` 权限。每个子命令必须独立匹配。

#### 环境变量（env）

```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "USE_BUILTIN_RIPGREP": "0",
    "DISABLE_AUTOUPDATER": "1",
    "HTTPS_PROXY": "http://proxy.example.com:8080",
    "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe",
    "NODE_EXTRA_CA_CERTS": "/path/to/ca-bundle.pem"
  }
}
```

#### 自动更新（autoUpdatesChannel）

```json
{ "autoUpdatesChannel": "stable" }
```
值：`"latest"`（默认）, `"stable"`。完全禁用自动更新需在 `env` 中设置 `"DISABLE_AUTOUPDATER": "1"`。

#### 沙箱（sandbox）

```json
{
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "allowWrite": ["~/.kube", "/tmp/build"],
      "denyWrite": [],
      "denyRead": ["~/"],
      "allowRead": ["."]
    },
    "network": {
      "allowedDomains": ["*.github.com", "*.npmjs.org"]
    },
    "autoAllowBashIfSandboxed": true,
    "allowUnsandboxedCommands": true,
    "excludedCommands": ["cmd.exe", "powershell.exe"]
  }
}
```

| 沙箱设置 | 说明 |
|---|---|
| `sandbox.enabled` | 是否启用沙箱 |
| `sandbox.filesystem.allowWrite` | 允许写入的路径 |
| `sandbox.filesystem.denyWrite` | 禁止写入的路径 |
| `sandbox.filesystem.denyRead` | 禁止读取的路径 |
| `sandbox.filesystem.allowRead` | 允许读取的路径 |
| `sandbox.network.allowedDomains` | 允许访问的域名（支持 glob） |
| `sandbox.autoAllowBashIfSandboxed` | 沙箱内的 Bash 命令自动批准 |
| `sandbox.allowUnsandboxedCommands` | 是否允许 Claude 重试非沙箱命令 |
| `sandbox.excludedCommands` | 从沙箱中排除的命令 |

**平台沙箱技术：** macOS = Seatbelt, Linux/WSL2 = bubblewrap, Windows = 计划中（暂不支持）

#### 受保护路径（始终提示或拒绝）

无论权限模式如何，写入以下路径始终需要提示或被拒绝：

**目录：** `.git`, `.claude`（除 `.claude/commands`, `.claude/agents`, `.claude/skills`, `.claude/worktrees` 外）, `.vscode`, `.idea`, `.husky`

**文件：** `.gitconfig`, `.gitmodules`, `.bashrc`, `.bash_profile`, `.zshrc`, `.zprofile`, `.profile`, `.ripgreprc`, `.mcp.json`, `.claude.json`

#### 模型与性能

```json
{
  "model": "claude-sonnet-4-6",
  "effort": "medium",
  "alwaysThinkingEnabled": false,
  "showThinkingSummaries": false
}
```

#### 自动记忆

```json
{
  "autoMemoryEnabled": true,
  "autoMemoryDirectory": "~/.claude/projects"
}
```

注：`autoMemoryDirectory` 仅从托管、本地和用户设置读取（不在项目设置中生效）。

#### CLAUDE.md 排除

```json
{
  "claudeMdExcludes": [
    "**/monorepo/CLAUDE.md",
    "/home/user/monorepo/other-team/.claude/rules/**"
  ]
}
```

#### 插件

```json
{
  "plugins": {
    "enabled": ["plugin-name"],
    "disabled": ["other-plugin"]
  }
}
```

#### 清理周期

```json
{ "cleanupPeriodDays": 7 }
```
用于自动清理孤立 worktree。

#### 技能 Shell 执行

```json
{ "disableSkillShellExecution": true }
```
禁用技能中的 `` !`command` `` 语法执行。

#### 公司公告

```json
{
  "companyAnnouncements": [
    "Welcome to Acme Corp!",
    "Reminder: Code reviews required"
  ]
}
```

#### 自动模式配置

```json
{
  "autoMode": {
    "environment": [
      "Organization: Acme Corp. Primary use: software development",
      "Source control: github.com/acme-corp",
      "Cloud provider(s): AWS, GCP",
      "Trusted internal domains: *.corp.example.com",
      "Key internal services: Jenkins at ci.example.com"
    ]
  }
}
```

#### 托管专用设置（仅在托管设置中生效）

| 设置 | 说明 |
|---|---|
| `allowManagedHooksOnly` | 仅加载托管和 SDK 钩子 |
| `allowManagedMcpServersOnly` | 仅允许白名单 MCP 服务器 |
| `allowManagedPermissionRulesOnly` | 禁止用户/项目设置定义权限规则 |
| `allowedChannelPlugins` | 可推送消息的通道插件白名单 |
| `blockedMarketplaces` | 被禁止的插件市场源黑名单 |
| `channelsEnabled` | 为 Team/Enterprise 用户启用通道 |
| `forceRemoteSettingsRefresh` | 远程设置获取失败时阻止启动（fail-closed） |
| `sandbox.filesystem.allowManagedReadPathsOnly` | 仅尊重托管 allowRead 路径 |
| `sandbox.network.allowManagedDomainsOnly` | 仅尊重托管 allowedDomains |
| `strictKnownMarketplaces` | 控制用户可添加的插件市场 |
| `pluginTrustMessage` | 自定义插件信任警告消息 |

### 2.4 各自治等级的推荐配置

#### L1 辅助编码（每步人工确认）

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "default",
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(git push *)",
      "Read(./.env)",
      "Read(./secrets/**)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "allowUnsandboxedCommands": false
  },
  "autoMemoryEnabled": true,
  "effort": "high",
  "model": "claude-sonnet-4-6"
}
```

#### L2 半自主编码（推荐默认）

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test *)",
      "Bash(npm run build)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git add *)",
      "Read",
      "Edit",
      "Glob",
      "Grep"
    ],
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(git push main)",
      "Bash(git push master)",
      "Bash(git force *)",
      "Bash(rm -rf *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./credentials/**)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "network": {
      "allowedDomains": ["*.github.com", "*.npmjs.org", "registry.npmjs.org"]
    },
    "autoAllowBashIfSandboxed": true,
    "allowUnsandboxedCommands": false
  },
  "autoMemoryEnabled": true,
  "effort": "high",
  "model": "claude-sonnet-4-6",
  "cleanupPeriodDays": 7
}
```

#### L3 受限自主编码（夜间/周末开发）

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "auto",
    "allow": [
      "Bash(npm run *)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git checkout *)",
      "Bash(git branch *)",
      "Read",
      "Edit",
      "Write",
      "Glob",
      "Grep",
      "Bash(npx *)"
    ],
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(git push main)",
      "Bash(git push master)",
      "Bash(git push -f *)",
      "Bash(rm -rf *)",
      "Bash(git reset --hard *)",
      "Read(./.env)",
      "Read(./secrets/**)",
      "Read(./credentials/**)",
      "Edit(.git/**)",
      "Edit(.claude/**)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "allowRead": ["."]
    },
    "network": {
      "allowedDomains": ["*.github.com", "*.npmjs.org"]
    },
    "autoAllowBashIfSandboxed": true,
    "allowUnsandboxedCommands": false
  },
  "autoMemoryEnabled": true,
  "autoMode": {
    "environment": [
      "Organization: dev team. Primary use: feature development",
      "Source control: github.com/your-org",
      "Cloud provider(s): AWS",
      "Trusted internal domains: *.internal.example.com"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "echo '[AUDIT] $(date): Edit/Write by Claude' >> /tmp/claude-audit.log" }
        ]
      }
    ]
  },
  "effort": "high",
  "model": "claude-sonnet-4-6"
}
```

#### L4 完全自主编码（成熟团队）

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "auto",
    "allow": [
      "Bash(npm run *)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git checkout *)",
      "Bash(git branch *)",
      "Bash(git push origin !main)",
      "Bash(git push origin !master)",
      "Read",
      "Edit",
      "Write",
      "Glob",
      "Grep",
      "Bash(npx *)"
    ],
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(git push origin main)",
      "Bash(git push origin master)",
      "Bash(git push -f *)",
      "Bash(rm -rf / *)",
      "Bash(sudo *)",
      "Read(./secrets/**)",
      "Read(./credentials/**)",
      "Edit(.git/**)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "network": {
      "allowedDomains": ["*.github.com", "*.npmjs.org", "registry.npmjs.org", "*.your-domain.com"]
    },
    "autoAllowBashIfSandboxed": true,
    "allowUnsandboxedCommands": false
  },
  "autoMemoryEnabled": true,
  "autoMode": {
    "environment": [
      "Organization: mature dev team. Primary use: autonomous feature development",
      "Source control: github.com/your-org",
      "Cloud provider(s): AWS, GCP",
      "Trusted cloud buckets: s3://your-build-artifacts",
      "Trusted internal domains: *.internal.example.com",
      "Key internal services: CI at ci.example.com"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "/usr/local/bin/claude-audit.sh" }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "/usr/local/bin/claude-bash-audit.sh" }
        ]
      }
    ],
    "ConfigChange": [
      {
        "hooks": [
          { "type": "command", "command": "/usr/local/bin/log-config-change.sh" }
        ]
      }
    ]
  },
  "effort": "high",
  "model": "claude-sonnet-4-6",
  "allowManagedHooksOnly": true,
  "allowManagedMcpServersOnly": false
}
```

### 2.5 配置示例

#### CI/CD 流水线配置

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "dontAsk",
    "allow": [
      "Bash(npm run *)",
      "Bash(git *)",
      "Read",
      "Edit",
      "Write",
      "Glob",
      "Grep"
    ],
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Read(./secrets/**)",
      "Read(./.env*)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "allowUnsandboxedCommands": false
  },
  "autoMemoryEnabled": false,
  "disableSkillShellExecution": true,
  "model": "claude-sonnet-4-6",
  "effort": "medium"
}
```

对应的 CI 调用：

```bash
claude --bare -p "Review PR changes for security issues" \
  --permission-mode dontAsk \
  --max-budget-usd 5.00 \
  --max-turns 10 \
  --output-format json \
  --no-session-persistence
```

#### 团队协作配置

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test *)",
      "Bash(git status)",
      "Read",
      "Edit",
      "Glob",
      "Grep"
    ],
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(git push main)",
      "Bash(git push master)",
      "Read(./.env)",
      "Read(./secrets/**)"
    ]
  },
  "autoMemoryEnabled": true,
  "effort": "high",
  "model": "claude-sonnet-4-6",
  "companyAnnouncements": [
    "Team reminder: All PRs require at least one review before merge"
  ]
}
```

#### 个人开发配置

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "acceptEdits"
  },
  "autoUpdatesChannel": "stable",
  "autoMemoryEnabled": true,
  "effort": "high",
  "alwaysThinkingEnabled": false,
  "showThinkingSummaries": true,
  "model": "claude-sonnet-4-6",
  "cleanupPeriodDays": 7,
  "env": {
    "USE_BUILTIN_RIPGREP": "1"
  }
}
```

#### 企业部署配置（托管设置）

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "acceptEdits",
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(git push main)",
      "Bash(git push master)",
      "Bash(git force *)",
      "Bash(rm -rf *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./credentials/**)",
      "Read(./config/secrets/**)"
    ],
    "disableBypassPermissionsMode": "disable",
    "disableAutoMode": "disable"
  },
  "allowManagedPermissionRulesOnly": true,
  "allowManagedHooksOnly": true,
  "allowManagedMcpServersOnly": true,
  "forceRemoteSettingsRefresh": true,
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "allowRead": ["."],
      "allowWrite": ["/tmp/build"]
    },
    "network": {
      "allowedDomains": ["*.github.com", "*.npmjs.org", "*.your-company.com"]
    },
    "autoAllowBashIfSandboxed": true,
    "allowUnsandboxedCommands": false
  },
  "autoMemoryEnabled": true,
  "autoMode": {
    "environment": [
      "Organization: Acme Corp. Primary use: software development",
      "Source control: github.com/acme-corp and all repos under it",
      "Cloud provider(s): AWS, GCP",
      "Trusted cloud buckets: s3://acme-build-artifacts, gs://acme-ml-datasets",
      "Trusted internal domains: *.corp.example.com, api.internal.example.com",
      "Key internal services: Jenkins at ci.example.com, Artifactory at artifacts.example.com"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          { "type": "command", "command": "/usr/local/bin/claude-audit.sh" }
        ]
      }
    ],
    "ConfigChange": [
      {
        "hooks": [
          { "type": "command", "command": "/usr/local/bin/log-config-change.sh" }
        ]
      }
    ]
  },
  "model": "claude-sonnet-4-6",
  "effort": "high"
}
```

---

## 第 3 章：Hooks 系统

### 3.1 钩子类型

| 钩子类型 | 触发时机 | 用途 |
|---|---|---|
| **PreToolUse** | 工具调用执行前 | 权限评估、自定义安全门、命令验证 |
| **PostToolUse** | 工具调用完成后 | 审计日志、合规跟踪、通知 |
| **Notification** | Claude 需要用户注意时 | 桌面通知、声音警报、消息转发 |
| **SessionStart** | 会话开始时 | 环境准备、上下文初始化 |
| **SessionEnd** | 会话结束时 | 清理、状态保存 |
| **PermissionDenied** | 自动模式拒绝操作时 | 程序化重试处理、告警 |
| **ConfigChange** | 设置被修改时 | 检测未授权的配置变更 |
| **WorktreeCreate** | 自定义 worktree 创建时 | 自定义 worktree 初始化逻辑 |
| **WorktreeRemove** | 自定义 worktree 移除时 | 自定义 worktree 清理逻辑 |
| **SubagentStart** / **SubagentEnd** | 子代理生命周期 | 子代理环境准备/清理 |
| **UserPromptSubmit** | 用户提示发送前 | 提示词转换、敏感信息过滤 |
| **InstructionsLoaded** | 指令文件加载时 | 动态指令注入 |

### 3.2 钩子配置语法

#### 基本结构

```json
{
  "hooks": {
    "HookType": [
      {
        "matcher": "pattern",
        "hooks": [
          { "type": "command", "command": "shell-command-here" }
        ]
      }
    ]
  }
}
```

#### Matcher 匹配模式

| Matcher 值 | 匹配范围 |
|---|---|
| `""`（空字符串） | 匹配所有 |
| `"Edit"` | 仅匹配 Edit 工具 |
| `"Bash(npm run *)"` | 匹配 Bash 工具中符合模式的命令 |
| `"Edit|Write"` | 匹配 Edit 或 Write 工具（正则 OR） |
| `".*"` | 匹配所有（正则） |

#### 钩子返回值

- 退出码 `0`：允许继续
- 退出码 `1`：标准失败
- 退出码 `2`：阻塞操作（优先级高于 allow 规则）

**注意：** 钩子决策不绕过权限规则。deny 和 ask 规则无论钩子输出如何都会被评估。

### 3.3 常用钩子模式

#### 自动 Lint（编辑后格式化）

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "prettier --write {{file_path}}" }
        ]
      }
    ]
  }
}
```

#### 测试门禁（提交前测试）

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(git commit *)",
        "hooks": [
          { "type": "command", "command": "npm run test && npm run lint" }
        ]
      }
    ]
  }
}
```

#### 安全扫描（编辑后检查）

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "npx secret-scan --path {{file_path}}" }
        ]
      }
    ]
  }
}
```

#### 代码格式化（批量）

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "npx prettier --write 'src/**/*.{ts,tsx}'" }
        ]
      }
    ]
  }
}
```

#### 会话通知

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'Claude Code' 'Claude Code needs your attention'"
          }
        ]
      }
    ]
  }
}
```

#### 命令验证（禁止危险命令）

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(rm -rf *)",
        "hooks": [
          { "type": "command", "command": "echo 'BLOCKED: rm -rf is not allowed' >&2; exit 2" }
        ]
      }
    ]
  }
}
```

### 3.4 企业钩子

#### 审计日志（所有文件编辑）

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/local/bin/audit-edit.sh {{file_path}} ${CLAUDE_SESSION_ID}"
          }
        ]
      }
    ]
  }
}
```

审计脚本示例 (`/usr/local/bin/audit-edit.sh`)：

```bash
#!/bin/bash
# audit-edit.sh <file_path> <session_id>
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] SESSION=$2 FILE=$1 ACTION=edit" \
  >> /var/log/claude-audit.log
```

#### 配置变更检测

```json
{
  "hooks": {
    "ConfigChange": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/usr/local/bin/log-config-change.sh"
          }
        ]
      }
    ]
  }
}
```

#### 全面审计（所有工具调用）

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/local/bin/claude-audit.sh"
          }
        ]
      }
    ]
  }
}
```

#### 子代理生命周期钩子

```json
{
  "hooks": {
    "SubagentStart": [
      {
        "matcher": "db-agent",
        "hooks": [
          { "type": "command", "command": "./scripts/setup-db-connection.sh" }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          { "type": "command", "command": "./scripts/cleanup-db-connection.sh" }
        ]
      }
    ]
  }
}
```

### 3.5 子代理级钩子（Frontmatter 钩子）

子代理可以在其定义文件的 frontmatter 中声明钩子，仅在该子代理会话中生效：

```yaml
---
name: code-reviewer
description: Review code changes with automatic linting
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh $TOOL_INPUT"
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-linter.sh"
---
```

### 3.6 钩子最佳实践

1. **幂等性**：钩子命令应可安全重复执行。避免在 PostToolUse 中创建重复记录。

2. **性能**：PreToolUse 钩子会阻塞工具执行。确保脚本快速返回（建议 <1 秒）。耗时操作放在 PostToolUse 中。

3. **错误处理**：PreToolUse 中退出码 `2` 阻塞操作。确保脚本在所有路径上都有明确的退出码。

4. **日志**：钩子输出写入 stderr 会被记录。使用结构化日志格式（JSON 或键值对）。

5. **安全**：钩子中不要硬编码敏感信息。使用环境变量或密钥管理工具。

6. **测试**：在应用钩子前，用 `claude -p` 测试钩子行为，确认不会意外阻塞正常操作。

7. **优先级理解**：
   - 钩子决策不覆盖权限规则
   - Deny 和 ask 规则始终优先评估
   - 阻塞钩子（退出码 2）优先级高于 allow 规则
   - 托管钩子可通过 `allowManagedHooksOnly` 强制独占

8. **变量替换**：钩子命令中支持 `{{file_path}}` 等变量替换。

---

## 第 4 章：Skills 系统

### 4.1 Skill 定义与位置

| 位置 | 路径 | 适用对象 | 优先级 |
|---|---|---|---|
| 企业 | 托管设置 | 组织所有用户 | 最高 |
| 个人 | `~/.claude/skills/<skill-name>/SKILL.md` | 你所有项目 | 高 |
| 项目 | `.claude/skills/<skill-name>/SKILL.md` | 此项目 | 中 |
| 插件 | `<plugin>/skills/<skill-name>/SKILL.md` | 启用插件的项目 | 低 |

优先级：Enterprise > Personal > Project。插件技能使用 `plugin-name:skill-name` 命名空间。

### 4.2 Skill 目录结构

```
my-skill/
├── SKILL.md           # 主指令文件（必需）
├── template.md        # Claude 填写的模板（可选）
├── examples/
│   └── sample.md      # 输出示例（可选）
└── scripts/
    └── validate.sh    # Claude 可执行的脚本（可选）
```

### 4.3 SKILL.md Frontmatter 字段参考

```yaml
---
name: my-skill                          # 可选，省略则使用目录名
description: What this skill does       # 推荐 - 帮助 Claude 决定何时使用
when_to_use: Additional trigger context # 可选 - 追加到 description（合计 1536 字符上限）
argument-hint: [filename] [format]      # 可选 - 自动补全中显示
disable-model-invocation: true          # 阻止自动加载，仅手动调用
user-invocable: false                   # 从 / 菜单隐藏，仅 Claude 可调用
allowed-tools: Read Grep                # 无需权限即可使用的工具
model: claude-sonnet-4-6                # 覆盖模型
effort: high                            # 覆盖努力程度
context: fork                           # 在分叉子代理中运行
agent: Explore                          # context:fork 时的子代理类型
hooks: {}                               # 技能级钩子
paths: "src/**/*.ts"                    # 限制激活的文件模式
shell: powershell                       # !`command` 块的 shell（默认 bash）
---
```

**所有 frontmatter 字段说明：**

| 字段 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `name` | string | 否 | 唯一标识符（小写 + 连字符）。省略时使用目录名 |
| `description` | string | 推荐 | 技能描述，用于自动触发匹配 |
| `when_to_use` | string | 否 | 额外触发上下文，追加到 description |
| `argument-hint` | string | 否 | 参数提示，显示在自动补全中 |
| `disable-model-invocation` | boolean | 否 | 设为 `true` 阻止模型自动加载，仅 `/skill-name` 手动调用 |
| `user-invocable` | boolean | 否 | 设为 `false` 从 `/` 菜单隐藏，仅模型可调用 |
| `allowed-tools` | string | 否 | 无需权限即可使用的工具列表（空格分隔） |
| `model` | string | 否 | 覆盖模型：完整模型 ID 或别名 |
| `effort` | string | 否 | 覆盖努力程度：low/medium/high/max |
| `context` | string | 否 | 设为 `fork` 在分叉子代理中运行技能 |
| `agent` | string | 否 | 当 `context: fork` 时指定子代理类型（如 Explore） |
| `hooks` | object | 否 | 技能范围的钩子配置 |
| `paths` | string | 否 | 限制技能激活的文件模式（glob） |
| `shell` | string | 否 | `` !`command` `` 块使用的 shell（默认 bash） |

### 4.4 字符串替换

在技能内容中可用的变量：

| 变量 | 说明 |
|---|---|
| `$ARGUMENTS` | 调用技能时传入的所有参数 |
| `$ARGUMENTS[N]` | 第 N 个参数（0-based 索引） |
| `$N` | `$ARGUMENTS[N]` 的简写 |
| `${CLAUDE_SESSION_ID}` | 当前会话 ID |
| `${CLAUDE_SKILL_DIR}` | 包含 SKILL.md 的目录路径 |

### 4.5 动态上下文注入

技能支持 `` !`<command>` `` 语法，在技能内容发送给 Claude 之前执行 shell 命令，输出替换占位符：

````markdown
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
allowed-tools: Bash(gh *)
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
- Changed files: !`gh pr diff --name-only`

## Your task
Summarize this pull request...
````

多行命令：

````markdown
## Environment
```!
node --version
npm --version
git status --short
```
````

### 4.6 调用模式

#### 1. 自然语言（Claude 自动决定）

```
"How does this authentication work?"
Claude 自动匹配并加载相关技能
```

#### 2. 手动斜杠命令

```
/explain-code src/auth/login.ts
/fix-issue 123
/deploy production
/migrate-component SearchBar React Vue
```

#### 3. @提及（保证执行）

```
@"code-reviewer (agent)" look at the auth changes
```

#### 4. 会话级代理

```bash
# CLI 级别
claude --agent code-reviewer

# settings.json 中
{ "agent": "code-reviewer" }
```

#### 5. 插件命名空间

```
/plugin-name:skill-name arg1 arg2
```

### 4.7 团队 Skill 共享

技能可通过项目目录共享：

```
project/
└── .claude/
    └── skills/
        ├── deploy/
        │   └── SKILL.md          # 团队共享部署技能
        ├── code-review/
        │   └── SKILL.md          # 团队共享代码审查技能
        └── test-patterns/
            └── SKILL.md          # 团队共享测试模式技能
```

所有协作者克隆仓库后即可使用这些技能。

### 4.8 常用 Skill 模板

#### Commit 技能

```markdown
---
name: commit
description: Create well-structured git commits with conventional commit messages
argument-hint: [scope] [type]
allowed-tools: Bash(git *) Read Glob Grep
---

Create a git commit following conventional commit format:
`type(scope): description`

Steps:
1. Review staged and unstaged changes with `git diff`
2. Determine appropriate type (feat/fix/refactor/chore/docs/test)
3. Determine scope from modified files/directories
4. Write concise, imperative description
5. Stage relevant files and commit
6. Show commit summary

Rules:
- Never commit .env files or secrets
- Never commit node_modules/ or build artifacts
- Always run lint and test before committing
- Use semantic commit messages
- Include body for complex changes
```

#### Review-PR 技能

```markdown
---
name: review-pr
description: Comprehensive pull request review with security and quality checks
argument-hint: [pr-number-or-url]
context: fork
agent: Explore
allowed-tools: Bash(gh *) Read Grep Glob
---

Review the specified pull request:

1. Fetch PR diff: !`gh pr diff $ARGUMENTS`
2. Get PR details: !`gh pr view $ARGUMENTS --json title,body,files`
3. Get PR comments: !`gh pr view $ARGUMENTS --comments`

Review checklist:
- **Correctness**: Does the code work as intended?
- **Security**: SQL injection, XSS, auth bypass, data exposure?
- **Performance**: N+1 queries, memory leaks, inefficient algorithms?
- **Style**: Consistent with codebase conventions?
- **Tests**: Adequate test coverage? Edge cases?
- **Documentation**: README, API docs updated?

Output structured review with severity markers:
- 🔴 Critical (must fix before merge)
- 🟡 Nit (should fix)
- 🟣 Pre-existing (not introduced by this PR)
```

#### Deploy 技能

```markdown
---
name: deploy
description: Deploy application to specified environment with safety checks
argument-hint: [environment]
allowed-tools: Bash(npm *) Bash(git *) Read
hooks:
  PreToolUse:
    - matcher: "Bash(*deploy*)"
      hooks:
        - type: command
          command: "echo 'Deploy initiated at $(date)'"
---

Deploy to environment: $ARGUMENTS

Pre-deployment checklist:
1. Verify current branch is main/master
2. Run `npm run lint` - must pass
3. Run `npm test` - must pass
4. Run `npm run build` - must pass

Deployment steps:
1. Create git tag with version
2. Push to remote
3. Trigger deployment pipeline
4. Verify deployment health check

Safety rules:
- NEVER deploy to production without explicit approval
- Always create a tag before deploying
- Verify health check passes before declaring success
- Log all deployment actions
```

#### Test 技能

```markdown
---
name: test
description: Run and analyze test suites with coverage reporting
argument-hint: [test-pattern]
allowed-tools: Bash(npm run test *) Bash(npx *) Read Grep Glob
---

Execute test suite with the following approach:

1. If $ARGUMENTS is specified, run matching tests:
   `npm test -- -t "$ARGUMENTS"`
2. If no arguments, run full test suite
3. Analyze output for failures
4. If failures found:
   - Identify root cause
   - Fix PRODUCTION code (never modify tests to pass)
   - Re-run tests
5. Report pass/fail status

Coverage rules:
- Minimum 80% line coverage required
- Minimum 70% branch coverage required
- Report uncovered files for follow-up
```

---

## 第 5 章：Memory 系统

### 5.1 CLAUDE.md 位置和优先级

#### 文件位置

| 作用域 | 位置 | 用途 | 是否共享 |
|---|---|---|---|
| 托管策略 | `/etc/claude-code/CLAUDE.md`（Linux）或平台等效 | 组织级指令 | 所有用户 |
| 项目 | `./CLAUDE.md` 或 `./.claude/CLAUDE.md` | 团队共享指令 | 是（git） |
| 用户 | `~/.claude/CLAUDE.md` | 个人偏好，所有项目 | 仅你 |
| 本地 | `./CLAUDE.local.md` | 个人项目级偏好 | 仅你（gitignore） |

#### CLAUDE.md 加载规则

1. **目录树遍历**：从工作目录向上遍历，在每个层级加载 `CLAUDE.md` 和 `CLAUDE.local.md`
2. **同层优先级**：`CLAUDE.local.md` 在 `CLAUDE.md` 之后追加（个人偏好优先）
3. **按需加载**：子目录的 CLAUDE.md 仅在 Claude 读取该目录中的文件时加载
4. **注释剥离**：HTML 块注释 `<!-- ... -->` 在注入上下文前被移除
5. **大小建议**：每个文件不超过 200 行

#### 导入其他文件

```markdown
See @README.md for project overview and @package.json for npm commands.

# Git workflow
@docs/git-instructions.md

# Personal overrides
@~/.claude/my-project-instructions.md
```

- 相对路径相对于包含导入的文件解析
- 最大递归深度：5 层

### 5.2 Auto Memory 机制

自动记忆是 Claude 的自我学习系统，跨会话积累知识。

**存储位置：** `~/.claude/projects/<project>/memory/`
```
memory/
├── MEMORY.md          # 简洁索引，每次会话加载（前 200 行或 25KB）
├── debugging.md       # 主题文件，按需加载
├── api-conventions.md # 主题文件，按需加载
```

**启用/禁用：**
```json
{ "autoMemoryEnabled": true }
```

或环境变量：
```bash
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
```

**自定义存储位置**（仅用户或本地设置）：
```json
{ "autoMemoryDirectory": "~/my-custom-memory-dir" }
```

### 5.3 .claude/rules/ 目录

```
project/
├── .claude/
│   ├── CLAUDE.md           # 主项目指令
│   └── rules/
│       ├── code-style.md   # 无条件规则
│       ├── testing.md      # 无条件规则
│       └── api-design.md   # 可包含路径范围规则
```

**路径范围规则示例：**

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "lib/**/*.{ts,tsx}"
---

# API Development Rules
- All API endpoints must include input validation
- Use standard error response format
```

### 5.4 YAML Frontmatter 路径级规则

`.claude/rules/` 目录中的文件支持 YAML frontmatter 来限定规则的适用范围：

```markdown
---
paths:
  - "src/frontend/**/*.tsx"
  - "components/**/*.{ts,tsx}"
---

# Frontend Rules
- Use functional components with hooks
- No class components
- Props must be typed with interfaces
```

路径模式使用 glob 语法，仅在匹配的文件被读取时才加载规则内容，有效节省上下文。

### 5.5 记忆生命周期

| 阶段 | 行为 |
|---|---|
| **创建** | Claude 在会话中自动积累关键信息（约定、模式、陷阱） |
| **存储** | 写入 `~/.claude/projects/<project>/memory/` |
| **加载** | 新会话启动时加载 `MEMORY.md`（前 200 行/25KB） |
| **按需** | 其他主题文件在 Claude 判断相关时加载 |
| **更新** | Claude 在会话结束时自动更新记忆文件 |
| **清理** | 用户可手动编辑或删除记忆文件 |

### 5.6 各自治等级的记忆策略

| 自治等级 | 记忆策略 | 说明 |
|---|---|---|
| **L1** | 开启 Auto Memory | 每次会话积累经验，适合新手团队学习项目约定 |
| **L2** | 开启 Auto Memory + 项目 rules | 在 Auto Memory 基础上补充 `.claude/rules/` 中的结构化规则 |
| **L3** | Auto Memory + 子代理 Memory | 子代理也配置 `memory: project`，共享项目级知识 |
| **L4** | Auto Memory + 托管记忆 + 定期清理 | 组织级 CLAUDE.md 提供基础约定，Auto Memory 补充项目细节 |

---

## 第 6 章：配置模板库

### 6.1 L1 辅助编码模板

**特征**：每步人工确认，最高安全级别

#### settings.json

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "default",
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(git push *)",
      "Read(./.env)",
      "Read(./secrets/**)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "allowUnsandboxedCommands": false
  },
  "autoMemoryEnabled": true,
  "effort": "high",
  "model": "claude-sonnet-4-6"
}
```

#### CLAUDE.md

```markdown
# Project Conventions (L1 - Assisted Coding)

## Build Commands
- Build: npm run build
- Test: npm test
- Lint: npm run lint

## Rules
- Always ask before making changes
- Run tests after every code change
- Never modify tests to make them pass
- Follow existing code patterns
```

#### 子代理定义（可选）

```yaml
# .claude/agents/explorer.md
---
name: explorer
description: Explores codebase for context before changes
tools: Read, Grep, Glob
model: haiku
---

Explore the codebase to understand patterns and conventions.
Report findings concisely.
```

### 6.2 L2 半自主编码模板

**特征**：每个 PR 合并前人工审查（推荐默认等级）

#### settings.json

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test *)",
      "Bash(npm run build)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git add *)",
      "Read",
      "Edit",
      "Glob",
      "Grep"
    ],
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(git push main)",
      "Bash(git push master)",
      "Bash(git force *)",
      "Bash(rm -rf *)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "network": {
      "allowedDomains": ["*.github.com", "*.npmjs.org", "registry.npmjs.org"]
    },
    "autoAllowBashIfSandboxed": true,
    "allowUnsandboxedCommands": false
  },
  "autoMemoryEnabled": true,
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "prettier --write {{file_path}} 2>/dev/null || true" }
        ]
      }
    ]
  },
  "effort": "high",
  "model": "claude-sonnet-4-6"
}
```

#### CLAUDE.md

```markdown
# Project Conventions (L2 - Semi-Autonomous)

## Build & Test
- Build: npm run build
- Test: npm test (single: npm test -- -t "name")
- Lint: npm run lint

## TDD Rules
- Write tests BEFORE implementation
- Red -> Green -> Refactor cycle
- Never modify tests to make them pass - fix production code

## Code Style
- TypeScript strict mode
- 2-space indentation
- ES modules (import/export)
- Error handling: try/catch with specific error types

## Git Workflow
- Create feature branches from main
- Conventional commit messages
- Squash merge to main
- Human review required before merge
```

### 6.3 L3 受限自主编码模板（夜间开发）

**特征**：每个 PR 合并前人工审查 + DCP 门禁

#### settings.json

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "auto",
    "allow": [
      "Bash(npm run *)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git checkout *)",
      "Bash(git branch *)",
      "Read",
      "Edit",
      "Write",
      "Glob",
      "Grep",
      "Bash(npx *)"
    ],
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(git push main)",
      "Bash(git push master)",
      "Bash(git push -f *)",
      "Bash(rm -rf *)",
      "Bash(git reset --hard *)",
      "Read(./.env)",
      "Read(./secrets/**)",
      "Read(./credentials/**)",
      "Edit(.git/**)",
      "Edit(.claude/**)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "allowRead": ["."]
    },
    "network": {
      "allowedDomains": ["*.github.com", "*.npmjs.org"]
    },
    "autoAllowBashIfSandboxed": true,
    "allowUnsandboxedCommands": false
  },
  "autoMemoryEnabled": true,
  "autoMode": {
    "environment": [
      "Organization: dev team. Primary use: overnight feature development",
      "Source control: github.com/your-org",
      "Cloud provider(s): AWS",
      "Trusted internal domains: *.internal.example.com"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "echo '[$(date -u +%Y-%m-%dT%H:%M:%SZ)] EDIT {{file_path}}' >> /tmp/claude-audit.log" }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "notify-send 'Claude Code' 'Nightly run needs attention'" }
        ]
      }
    ]
  },
  "effort": "high",
  "model": "claude-sonnet-4-6"
}
```

#### 夜间启动脚本

```bash
#!/bin/bash
# overnight.sh - Queue tasks for overnight autonomous development

PROJECT_DIR="/path/to/project"
cd "$PROJECT_DIR"

# Create tmux session for overnight run
tmux new-session -d -s claude-night << 'EOF'
claude \
  --worktree overnight-auto-$(date +%Y%m%d) \
  --permission-mode auto \
  --enable-auto-mode \
  -n "nightly-auto-coding" \
  "Complete the following tasks:
  1. Implement user registration endpoint
  2. Add email validation middleware
  3. Write integration tests for auth module

  For each task:
  - Create tests first (TDD)
  - Implement the feature
  - Run full test suite
  - Create a PR on branch feat/task-name

  Safety rules:
  - Do NOT push to main or master
  - Do NOT modify .env or secret files
  - Do NOT delete directories
  - Stop after 50 iterations or 6 hours
  "
EOF

echo "Nightly autonomous coding started in tmux session 'claude-night'"
echo "Monitor with: tmux attach -t claude-night"
```

### 6.4 L4 完全自主编码模板

**特征**：DCP 门禁 + 定期审计

#### settings.json

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "auto",
    "allow": [
      "Bash(npm run *)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git checkout *)",
      "Bash(git branch *)",
      "Bash(git push origin !main)",
      "Bash(git push origin !master)",
      "Read",
      "Edit",
      "Write",
      "Glob",
      "Grep",
      "Bash(npx *)"
    ],
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(git push origin main)",
      "Bash(git push origin master)",
      "Bash(git push -f *)",
      "Bash(rm -rf / *)",
      "Bash(sudo *)",
      "Read(./secrets/**)",
      "Read(./credentials/**)",
      "Edit(.git/**)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "network": {
      "allowedDomains": ["*.github.com", "*.npmjs.org", "registry.npmjs.org", "*.your-domain.com"]
    },
    "autoAllowBashIfSandboxed": true,
    "allowUnsandboxedCommands": false
  },
  "autoMemoryEnabled": true,
  "autoMode": {
    "environment": [
      "Organization: mature dev team. Primary use: autonomous development",
      "Source control: github.com/your-org",
      "Cloud provider(s): AWS, GCP",
      "Trusted cloud buckets: s3://your-build-artifacts",
      "Trusted internal domains: *.internal.example.com",
      "Key internal services: CI at ci.example.com"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "/usr/local/bin/claude-audit.sh" }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "/usr/local/bin/claude-bash-audit.sh" }
        ]
      }
    ],
    "ConfigChange": [
      {
        "hooks": [
          { "type": "command", "command": "/usr/local/bin/log-config-change.sh" }
        ]
      }
    ]
  },
  "effort": "high",
  "model": "claude-sonnet-4-6",
  "allowManagedHooksOnly": true,
  "allowManagedMcpServersOnly": false
}
```

#### 审计脚本模板

```bash
#!/bin/bash
# /usr/local/bin/claude-audit.sh
# Audit all Claude Code file edits

AUDIT_LOG="/var/log/claude-audit.log"
SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"

# Log file edit audit
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] SESSION=$SESSION_ID ACTION=file-audit" \
  >> "$AUDIT_LOG"

# Optional: Send to centralized logging
# curl -s -X POST https://logging.internal.example.com/claude-audit \
#   -H "Content-Type: application/json" \
#   -d "{\"session\":\"$SESSION_ID\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
```

### 6.5 CI/CD 流水线模板

#### GitHub Actions

```yaml
name: Claude Code Auto Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Claude Code
        run: curl -fsSL https://claude.ai/install.sh | bash

      - name: Auto Review PR
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: "Review this pull request for code quality, correctness, and security."
          claude_args: "--max-turns 5 --permission-mode acceptEdits"
```

#### GitLab CI/CD

```yaml
stages:
  - ai

claude-review:
  stage: ai
  image: node:24-alpine3.21
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
  before_script:
    - curl -fsSL https://claude.ai/install.sh | bash
  script:
    - claude -p "${AI_FLOW_INPUT:-'Review and implement changes'}" \
        --permission-mode acceptEdits \
        --allowedTools "Bash Read Edit Write mcp__gitlab" \
        --max-turns 10 \
        --max-budget-usd 5.00 \
        --debug
  timeout: 30m
```

#### 自修复 CI 流水线

```yaml
name: Self-Healing CI
on:
  workflow_run:
    workflows: ["Build"]
    types: [completed]

jobs:
  auto-fix:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event.workflow_run.head_branch }}

      - name: Install Claude Code
        run: curl -fsSL https://claude.ai/install.sh | bash

      - name: Download build logs
        run: |
          gh run view ${{ github.event.workflow_run.id }} --log > build-log.txt
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Auto-fix CI failure
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            The CI build failed. Analyze the build logs and create a fix.
            Build logs are in build-log.txt.
            Create a new branch with the fix and open a PR.
          claude_args: "--max-turns 10 --permission-mode auto"
```

### 6.6 Agent Teams 模板

#### oh-my-claudecode 团队配置

```json
// .omc/teams/auto-coding-team/config.json
{
  "team_name": "auto-coding-team",
  "description": "Autonomous coding team for overnight feature development",
  "members": [
    {
      "name": "team-lead",
      "role": "orchestrator",
      "description": "Coordinates task assignment and merge resolution"
    },
    {
      "name": "backend-dev",
      "role": "worker",
      "description": "Implements backend API features"
    },
    {
      "name": "frontend-dev",
      "role": "worker",
      "description": "Implements frontend components"
    },
    {
      "name": "test-writer",
      "role": "worker",
      "description": "Writes and maintains test suites"
    }
  ]
}
```

#### Sub-Agent 定义模板

```yaml
# .claude/agents/backend-dev.md
---
name: backend-dev
description: Backend API implementation specialist. Implement RESTful endpoints, database models, and service logic.
tools: Read, Write, Edit, Grep, Glob, Bash
model: sonnet
memory: project
---

You are a backend developer specializing in API development.

When implementing features:
1. Explore existing patterns in the codebase
2. Write tests FIRST (TDD)
3. Implement the feature
4. Run full test suite
5. Create PR on branch feat/backend-<feature-name>

Rules:
- Follow existing naming conventions
- Use TypeScript strict mode
- All endpoints must have input validation
- Error handling: specific error types, never generic catch
- Never modify .env or secret files
```

### 6.7 MCP 安全配置模板

#### 基础 MCP 配置（仅受信服务器）

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "env": {}
    }
  }
}
```

#### 企业 MCP 配置（带网络限制）

```json
{
  "allowManagedMcpServersOnly": true,
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    },
    "jira": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-jira"],
      "env": {
        "JIRA_API_TOKEN": "${JIRA_TOKEN}"
      }
    }
  },
  "permissions": {
    "allow": [
      "mcp__github__*",
      "mcp__jira__*"
    ],
    "deny": [
      "mcp__filesystem__*"
    ]
  }
}
```

#### MCP 安全最佳实践

1. **仅使用受信服务器**：企业应使用 `allowManagedMcpServersOnly` 限制仅加载托管 MCP 服务器
2. **权限最小化**：为每个 MCP 服务器配置最小必要权限规则
3. **避免硬编码密钥**：使用环境变量注入敏感凭证
4. **命名空间规则**：使用 `mcp__servername__toolname` 格式精细控制工具访问
5. **定期审计**：通过 ConfigChange 钩子监控 MCP 配置变更

### 6.8 P23 方案设计模板

> **说明**：以下模板支持 P23 Requirement→Solution→Spec 链（见 01-core-specification.md 2.24）。详细模板文件见 `ai-coding/templates/` 目录。

#### 6.8.1 架构设计文档模板

文件路径：`docs/architecture/{feature-id}-architecture.md`

模板见：`templates/architecture-doc.md`

```markdown
# {Feature名称} 架构适配分析

> 需求来源：{specs/{feature-id}-spec.md}
> 创建时间：{YYYY-MM-DD}
> 状态：Draft | Approved | Rejected

## 1. 需求概述

## 2. 现有架构影响分析

## 3. 接口变更

## 4. 数据模型变更

## 5. 依赖变更

## 6. 风险评估

## 7. 决策点 DP0.5 确认
```

#### 6.8.2 方案设计文档模板

文件路径：`docs/solutions/{feature-id}-design.md`

模板见：`templates/solution-design.md`

```markdown
# {Feature名称} 方案设计

> 架构分析：{docs/architecture/{feature-id}-architecture.md}
> 创建时间：{YYYY-MM-DD}
> 状态：Draft | Approved | Rejected

## 1. 方案概述

## 2. 模块划分

## 3. 接口定义

## 4. 数据流设计

## 5. 异常处理策略

## 6. 测试策略

## 7. 依赖约束

## 8. 风险评估（Top 3）

## 9. Solution Quality Gate 检查记录

## 10. 决策点 DP0.7 确认
```

### 6.9 domain-knowledge/ 目录

> **说明**：支持 P23 的 Context Loading Gate（见 01-core-specification.md 2.24.3）。

```
domain-knowledge/
├── industry/
│   ├── fintech.md          # 金融科技领域知识
│   ├── healthcare.md       # 医疗健康领域知识
│   └── e-commerce.md       # 电商领域知识
├── tech-stack/
│   ├── go-gin.md           # Go + Gin 框架最佳实践
│   ├── python-fastapi.md   # Python + FastAPI 最佳实践
│   └── react-typescript.md # React + TypeScript 最佳实践
└── project-specific/
    ├── architecture-decisions.md  # 架构决策记录（ADR）
    ├── naming-conventions.md      # 命名规范
    └── historical-lessons.md      # 历史教训（失败方案记录）
```

### 6.10 方案质量门禁脚本

> **说明**：支持 P23 的 Solution Quality Gate（见 01-core-specification.md 2.24.4）。

脚本路径：`ai-coding/scripts/solution-quality-gate.sh`

使用方式：

```bash
# 在方案设计完成后、Spec 生成前执行
./ai-coding/scripts/solution-quality-gate.sh \
  --design docs/solutions/{feature-id}-design.md \
  --requirements docs/requirements/{feature-id}-requirements.md \
  --architecture docs/architecture/{feature-id}-architecture.md

# 输出：8 项检查结果，全部通过方可进入 Spec 生成
```

---

## 第 7 章：故障排查

### 7.1 安装问题

#### Claude Code 安装失败

| 症状 | 原因 | 解决方案 |
|---|---|---|
| `curl: command not found` | 系统缺少 curl | 安装 curl：`apt install curl` 或 `brew install curl` |
| 下载超时 | 网络问题或防火墙 | 设置代理：`export HTTPS_PROXY=http://proxy:8080` |
| `permission denied` | 安装目录无写权限 | 使用 `sudo` 或安装到用户目录 |
| Windows 安装失败 | 缺少 Git for Windows | 安装 Git for Windows，或使用 WSL |

#### 版本冲突

```bash
# 检查当前版本
claude -v

# 检查是否有旧 npm 安装
npm list -g @anthropic-ai/claude-code 2>/dev/null

# 卸载旧版本
npm uninstall -g @anthropic-ai/claude-code

# 重新安装原生版本
curl -fsSL https://claude.ai/install.sh | bash
```

#### ripgrep 问题

```bash
# Claude Code 内置 ripgrep，若失败可安装系统版本
# Ubuntu/Debian
sudo apt install ripgrep

# macOS
brew install ripgrep

# 然后设置环境变量
export USE_BUILTIN_RIPGREP=0
```

### 7.2 连接问题

#### 认证失败

```bash
# 检查认证状态
claude auth status

# 重新登录
claude auth login --console

# 如果使用 API 密钥
export ANTHROPIC_API_KEY="your-key-here"

# 使用企业网关
export ANTHROPIC_BASE_URL="https://gateway.company.com/v1"
```

#### 代理配置

```bash
# 设置 HTTP/HTTPS 代理
export HTTPS_PROXY='https://proxy.example.com:8080'
export HTTP_PROXY='http://proxy.example.com:8080'

# 企业 CA 证书
export NODE_EXTRA_CA_CERTS='/path/to/ca-bundle.pem'
```

#### 模型不可用

```bash
# 检查可用模型
claude --model claude-sonnet-4-6

# 使用备用模型
claude --fallback-model sonnet

# 检查提供商状态
claude auth status
```

### 7.3 上下文窗口问题

#### 上下文溢出

| 症状 | 解决方案 |
|---|---|
| "context window exceeded" | 1. 使用 `/clear` 清理不相关上下文 |
| 响应变慢 | 2. 使用 `--bare` 模式减少系统提示 |
| 记忆加载过多 | 3. 检查 CLAUDE.md 是否超过 200 行 |

#### 上下文管理技巧

```bash
# 清理会话
# 交互模式中: /clear

# 使用 bare 模式（跳过自动发现）
claude --bare -p "query"

# 排除动态系统提示部分（改善多机器缓存复用）
claude -p --exclude-dynamic-system-prompt-sections "query"

# 使用子代理隔离研究任务（不占主上下文）
"Use the explore agent to find all API endpoints"
```

#### CLAUDE.md 优化

- 单个文件不超过 200 行
- 使用 `@file` 导入按需加载
- 使用 `.claude/rules/` 路径范围规则
- 使用 `claudeMdExcludes` 排除不需要的 CLAUDE.md

### 7.4 权限问题

#### 工具被拒绝

```bash
# 检查当前权限配置
# 交互模式中: /permissions

# 临时允许工具
claude --allowedTools "Bash(npm run *) Edit Read Glob Grep"

# 检查 deny 规则
# 在 settings.json 中检查 permissions.deny 数组

# 检查托管策略是否覆盖
claude doctor
```

#### 受保护路径被阻止

```bash
# Claude Code 保护以下路径：
# .git, .claude (部分子目录除外), .vscode, .idea, .husky
# .gitconfig, .bashrc, .zshrc, .mcp.json, .claude.json

# 解决方案：
# 1. 不要在受保护路径中进行编辑
# 2. 使用 worktree 隔离需要修改 .claude 目录的工作
# 3. 在 settings.json 中设置 claudeMdExcludes
```

### 7.5 Hooks 问题

#### 钩子不执行

| 检查项 | 命令/操作 |
|---|---|
| 语法是否正确 | 验证 JSON 格式：`cat settings.json | python -m json.tool` |
| matcher 是否匹配 | 测试 matcher 正则是否匹配预期工具 |
| 脚本是否有执行权限 | `chmod +x /path/to/hook-script.sh` |
| 脚本路径是否正确 | `ls -la /path/to/hook-script.sh` |
| 退出码是否正确 | 钩子脚本必须返回 0（允许）或 2（阻塞） |

#### 钩子阻塞正常操作

```bash
# 临时禁用钩子
# 在 settings.json 中注释掉 hooks 配置

# 检查钩子脚本日志
cat /var/log/claude-audit.log

# 使用 --debug 模式查看钩子执行
claude --debug "hooks" -p "test query"
```

#### 托管钩子未加载

```bash
# 检查托管设置状态
claude auth status

# 验证 forceRemoteSettingsRefresh
# 如果为 true 且网络不通，CLI 将启动失败

# 临时解决：确保网络通畅后重试
```

### 7.6 MCP 问题

#### MCP 服务器无法连接

```bash
# 列出已配置的 MCP 服务器
claude mcp list

# 测试 MCP 服务器
claude --mcp-config ./mcp.json -p "test"

# 检查 MCP 权限规则
# 在 settings.json 中检查 permissions.allow 是否包含 "mcp__servername__*"
```

#### MCP 工具被拒绝

```json
// 在 settings.json 中添加 MCP 权限规则
{
  "permissions": {
    "allow": [
      "mcp__github__*",
      "mcp__filesystem__*"
    ]
  }
}
```

#### allowManagedMcpServersOnly 导致问题

```bash
# 如果启用了 allowManagedMcpServersOnly，
# 只有托管设置中的 MCP 服务器会被加载
# 解决方案：在托管设置中添加所需服务器
```

### 7.7 Auto-Coding 问题

#### 自修复循环（无限重试）

| 症状 | 解决方案 |
|---|---|
| 代理反复尝试修复同一问题 | 1. 设置 `--max-turns` 限制轮次 |
| 费用持续增长 | 2. 设置 `--max-budget-usd` 限制费用 |
| 时间持续消耗 | 3. 设置最大迭代次数（sub-agent `maxTurns`） |
| | 4. 使用 `/clear` 后重新描述任务 |

#### 定时任务不执行

```bash
# Desktop 定时任务
# 确保 Desktop 应用正在运行
# 检查 cron 表达式是否正确

# Cloud 定时任务
# 确保 GitHub 仓库已连接
# 检查任务定义中的 prompt 是否有效

# /loop 命令
# 确保会话保持打开状态
# 检查循环间隔是否合理
```

#### Agent Teams 协调失败

| 问题 | 解决方案 |
|---|---|
| 团队成员互相等待 | 使用 `blockedBy` 依赖明确执行顺序 |
| 合并冲突 | 使用 worktree 隔离，或在 task 中指定不同文件 |
| 任务重复执行 | 使用 TodoWrite 跟踪任务状态 |
| 成员长时间空闲 | 检查任务分配，确保所有成员有 pending 任务 |

#### 夜间开发中断

```bash
# 常见问题和解决方案：

# 1. 网络断开 -> 使用 tmux 保持会话
tmux new-session -d -s claude-night "claude ..."
tmux attach -t claude-night  # 恢复会话

# 2. API 限额耗尽 -> 设置 --max-budget-usd
claude -p "task" --max-budget-usd 50.00

# 3. 模型过载 -> 设置 --fallback-model
claude -p "task" --fallback-model sonnet

# 4. 磁盘空间不足 -> 定期检查
df -h ~/.claude/

# 5. 会话超时 -> 使用 Desktop 版本（无超时限制）
```

### 7.8 性能问题

#### 响应缓慢

| 原因 | 解决方案 |
|---|---|
| 上下文过大 | 使用 `/clear` 清理；使用 `--bare` 模式 |
| 模型过载 | 使用 `--fallback-model` 备用模型 |
| 网络延迟 | 检查网络连接；配置代理 |
| 提示缓存未命中 | 使用 `--exclude-dynamic-system-prompt-sections` |
| 文件过多 | 使用子代理进行文件探索 |

#### 启动缓慢

```bash
# 使用 bare 模式加速启动（跳过自动发现）
claude --bare -p "query"

# 减少 CLAUDE.md 大小（目标 < 200 行）
# 使用 @file 导入替代内联内容

# 禁用不需要的插件
# 在 settings.json 中设置 plugins.disabled

# 禁用不需要的自动发现
# 在 settings.json 中设置 claudeMdExcludes
```

#### 内存占用过高

```bash
# 检查 Claude Code 进程
ps aux | grep claude

# 定期清理会话
# 交互模式中: exit 或 Ctrl+D

# 清理缓存文件
rm -rf ~/.local/share/claude/cache/
```

### 7.9 快速修复指南

#### 万能诊断

```bash
# 第一步：运行 doctor
claude doctor

# 第二步：检查认证
claude auth status

# 第三步：检查版本
claude -v

# 第四步：检查配置
cat ~/.claude/settings.json 2>/dev/null
cat .claude/settings.json 2>/dev/null

# 第五步：检查 CLAUDE.md
ls -la CLAUDE.md .claude/CLAUDE.md 2>/dev/null
```

#### 快速修复清单

| 问题 | 快速修复 |
|---|---|
| 无法启动 | `claude auth login --console` |
| 命令找不到 | `curl -fsSL https://claude.ai/install.sh \| bash` |
| 权限太严 | `claude --permission-mode acceptEdits` |
| 权限太松 | `claude --permission-mode plan` |
| 上下文溢出 | `/clear` 或 `claude --bare` |
| 响应太慢 | 切换模型或减少上下文 |
| 钩子报错 | 检查钩子脚本退出码 |
| MCP 不工作 | `claude mcp list` 检查配置 |
| 会话丢失 | `claude -c` 或 `claude -r <name>` |
| 更新后异常 | `claude update` 或重新安装 |

#### 重置配置（破坏性操作，谨慎使用）

```bash
# 仅重置用户设置（保留项目设置）
rm -f ~/.claude/settings.json

# 完全重置（丢失所有设置和历史）
rm -rf ~/.claude ~/.claude.json

# 重新安装
curl -fsSL https://claude.ai/install.sh | bash
```

---

## 第 8 章：快速参考卡

### 8.1 CLI 速查卡

```
┌─────────────────────────────────────────────────────────────────┐
│                     Claude Code CLI 速查卡                       │
├─────────────────────────────────────────────────────────────────┤
│ 基础操作                                                         │
│   claude                  启动交互模式                           │
│   claude "query"          启动并带初始提示                        │
│   claude -p "query"       打印模式（非交互）                      │
│   claude -c               继续最近会话                           │
│   claude -r "name"        恢复指定会话                           │
│   claude update           更新到最新版本                          │
│                                                                  │
│ 权限控制                                                         │
│   --permission-mode MODE  default/acceptEdits/plan/auto/         │
│                           dontAsk/bypassPermissions               │
│   --dangerously-skip-permissions  跳过所有权限检查                │
│   --allowedTools "..."    自动允许的工具                         │
│                                                                  │
│ 自动化                                                           │
│   --bare                  最小模式（脚本调用）                    │
│   --max-turns N           最大轮次限制                           │
│   --max-budget-usd N      最大费用限制                           │
│   --output-format json    JSON 输出                              │
│   --no-session-persistence 禁用会话持久化                         │
│                                                                  │
│ Git                                                              │
│   --worktree name         在隔离 worktree 中启动                  │
│   --tmux                  创建 tmux 会话                         │
│   --from-pr 123           从 PR 恢复会话                          │
│                                                                  │
│ 模型                                                             │
│   --model sonnet          设置模型                               │
│   --effort high           设置努力程度                           │
│   --fallback-model sonnet 备用模型                               │
│                                                                  │
│ 多平台                                                           │
│   --remote "task"         创建 Web 会话                          │
│   --remote-control name   启动 Remote Control                    │
│   --teleport              本地恢复 Web 会话                      │
│   --chrome                启用 Chrome 集成                       │
├─────────────────────────────────────────────────────────────────┤
│ 诊断命令                                                         │
│   claude doctor           诊断安装/配置问题                       │
│   claude auth status      检查认证状态                           │
│   claude -v               显示版本                               │
│   claude agents           列出子代理                            │
│   claude mcp list         列出 MCP 服务器                        │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Settings 速查卡

```
┌─────────────────────────────────────────────────────────────────┐
│                   Settings 配置速查卡                            │
├─────────────────────────────────────────────────────────────────┤
│ 作用域优先级（高到低）                                             │
│   1. Managed（托管）     组织级，不可覆盖                         │
│   2. CLI 参数            会话级覆盖                              │
│   3. Local（本地）       .claude/settings.local.json             │
│   4. Project（项目）     .claude/settings.json                   │
│   5. User（用户）        ~/.claude/settings.json                 │
│                                                                  │
│ 权限模式                                                          │
│   default          每步确认（最安全）                             │
│   acceptEdits      自动接受文件编辑（推荐 L2）                     │
│   plan             只读模式（分析/探索）                           │
│   auto             分类器自动审核（L3/L4）                         │
│   dontAsk          无提示（CI 流水线）                            │
│   bypassPermissions 全部跳过（仅限隔离环境）                       │
│                                                                  │
│ 关键设置                                                          │
│   permissions.defaultMode     起始权限模式                        │
│   permissions.allow/deny[]    权限规则                            │
│   sandbox.enabled             沙箱开关                            │
│   autoMemoryEnabled           自动记忆                            │
│   model                       模型选择                            │
│   effort                      努力程度 low/medium/high/max        │
│   autoMode.environment[]      自动模式环境描述                     │
│                                                                  │
│ 托管专用设置                                                       │
│   allowManagedHooksOnly       仅托管钩子                          │
│   allowManagedMcpServersOnly  仅托管 MCP                          │
│   allowManagedPermissionRulesOnly 仅托管权限规则                   │
│   forceRemoteSettingsRefresh  获取失败则阻止启动                   │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 Hooks 速查卡

```
┌─────────────────────────────────────────────────────────────────┐
│                     Hooks 系统速查卡                             │
├─────────────────────────────────────────────────────────────────┤
│ 钩子类型与触发时机                                                 │
│   PreToolUse        工具执行前     安全门/命令验证                 │
│   PostToolUse       工具完成后     审计/通知/格式化                │
│   Notification      需要用户注意   桌面通知                        │
│   SessionStart      会话开始       环境准备                        │
│   SessionEnd        会话结束       清理/状态保存                   │
│   PermissionDenied  自动模式拒绝   重试/告警                       │
│   ConfigChange      设置变更       配置审计                        │
│   SubagentStart/End 子代理生命周期  环境准备/清理                   │
│   WorktreeCreate/Remove worktree  初始化/清理                     │
│   UserPromptSubmit  提示发送前     转换/过滤                       │
│                                                                  │
│ Matcher 匹配模式                                                   │
│   ""                匹配所有                                       │
│   "Edit"            匹配 Edit 工具                                 │
│   "Edit|Write"      匹配 Edit 或 Write                            │
│   "Bash(npm run *)"' 匹配符合模式的 Bash 命令                     │
│   ".*"              正则匹配所有                                   │
│                                                                  │
│ 退出码                                                            │
│   0                 允许继续                                       │
│   1                 标准失败                                       │
│   2                 阻塞操作（优先级高于 allow 规则）               │
│                                                                  │
│ 优先级规则                                                        │
│   钩子不覆盖权限规则                                               │
│   Deny 和 ask 规则始终优先                                         │
│   阻塞钩子（退出码 2）优先级最高                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 8.4 自治等级速查卡

```
┌─────────────────────────────────────────────────────────────────┐
│                   自治等级速查卡（v5.0）                          │
├──────┬──────────────┬──────────────────┬────────────────────────┤
│ 等级 │     名称     │   人类干预点     │      适用场景          │
├──────┼──────────────┼──────────────────┼────────────────────────┤
│  L1  │  辅助编码    │  每一步          │ 新手团队、安全敏感项目   │
│  L2  │  半自主编码  │  每个 PR 合并前  │ 日常开发（推荐默认）     │
│  L3  │  受限自主编码│  PR 合并+DCP门禁 │ 夜间/周末开发、自修复 CI │
│  L4  │  完全自主编码│  DCP 门禁+定期审计│ 成熟团队、低风险变更    │
├──────┴──────────────┴──────────────────┴────────────────────────┤
│                                                                  │
│ 约束矩阵                                                         │
│ 约束          │ L1     │ L2     │ L3     │ L4                   │
│ TDD 先行      │ 强制   │ 强制   │ 强制   │ 强制                  │
│ 人工审查      │ 每次提交│ PR 前 │ PR 前 │ 每周审计              │
│ DCP 门禁      │ 强制   │ 强制   │ 强制   │ 简化                  │
│ Spec 驱动     │ 强制   │ 强制   │ 强制   │ 可简化                │
│ 自修复限制    │ <=3 轮 │ <=3 轮 │ <=3 轮 │ <=3 轮               │
│ MCP 访问      │ 只读   │ 读写过滤│ 读写+脱敏│ 读写+脱敏+审计      │
│ 自动合并      │ 禁止   │ 禁止   │ 禁止   │ 仅 trivial fix        │
│                                                                  │
│ 升级路径                                                          │
│ L1 -> L2：积累 20 个 PR 无安全事故                                │
│ L2 -> L3：L2 运行 1 个月，自主成功率 > 70%                        │
│ L3 -> L4：L3 运行 3 个月，自主成功率 > 85%，审计通过率 > 95%      │
└─────────────────────────────────────────────────────────────────┘
```

### 8.5 故障排查决策树

```
Claude Code 出现问题？
│
├─ 无法启动？
│  ├─ 命令找不到 → 重新安装：curl -fsSL https://claude.ai/install.sh | bash
│  ├─ 认证失败 → claude auth login --console
│  ├─ 网络问题 → 设置 HTTPS_PROXY 环境变量
│  └─ 仍失败 → claude doctor
│
├─ 响应异常？
│  ├─ 上下文溢出 → /clear 或使用 --bare 模式
│  ├─ 响应变慢 → 检查 CLAUDE.md 大小（目标 < 200 行）
│  ├─ 模型不可用 → 使用 --fallback-model
│  └─ 幻觉/错误 → 提供更具体的验证标准（测试、预期输出）
│
├─ 权限问题？
│  ├─ 工具被拒绝 → 检查 settings.json 中 permissions.deny
│  ├─ 权限太严 → claude --permission-mode acceptEdits
│  ├─ 权限太松 → claude --permission-mode plan
│  └─ 托管策略覆盖 → 联系管理员调整 managed settings
│
├─ Hooks 不工作？
│  ├─ 不执行 → 检查 JSON 格式、脚本权限、matcher 匹配
│  ├─ 阻塞正常操作 → 检查脚本退出码（应为 0）
│  └─ 托管钩子未加载 → 检查网络和 forceRemoteSettingsRefresh
│
├─ MCP 问题？
│  ├─ 服务器不连接 → claude mcp list 检查配置
│  ├─ 工具被拒绝 → permissions.allow 中添加 "mcp__server__*"
│  └─ allowManagedMcpServersOnly → 在托管设置中添加服务器
│
├─ Auto-Coding 问题？
│  ├─ 无限重试 → 设置 --max-turns 和 --max-budget-usd
│  ├─ 费用过高 → 设置 --max-budget-usd 上限
│  ├─ 夜间中断 → 使用 tmux 保持会话
│  └─ Agent Teams 混乱 → 检查任务依赖和分配
│
└─ 性能问题？
   ├─ 启动慢 → 使用 --bare 模式
   ├─ 响应慢 → 减少上下文，使用 --bare
   ├─ 内存高 → 定期清理会话
   └─ 仍慢 → 使用 --fallback-model
```

### 8.6 环境变量速查卡

```
┌─────────────────────────────────────────────────────────────────┐
│                  环境变量速查卡                                  │
├─────────────────────────────────────────────────────────────────┤
│ 功能控制                                                         │
│   CLAUDE_CODE_SIMPLE               1 = 最小模式（--bare 设置）   │
│   CLAUDE_CODE_DISABLE_AUTO_MEMORY  1 = 禁用自动记忆              │
│   CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING  1 = 禁用自适应思考      │
│   CLAUDE_CODE_EFFORT_LEVEL         low/medium/high/max           │
│   CLAUDE_CODE_NEW_INIT             1 = 启用交互式 /init 流程     │
│                                                                  │
│ 网络与代理                                                       │
│   HTTPS_PROXY / HTTP_PROXY         代理服务器地址                │
│   ANTHROPIC_BASE_URL               LLM 网关基础 URL              │
│   ANTHROPIC_BEDROCK_BASE_URL       Bedrock 网关 URL              │
│   ANTHROPIC_VERTEX_BASE_URL        Vertex 网关 URL               │
│   ANTHROPIC_FOUNDRY_BASE_URL       Foundry 网关 URL              │
│   NODE_EXTRA_CA_CERTS              企业 CA 证书路径              │
│                                                                  │
│ 模型固定                                                         │
│   ANTHROPIC_DEFAULT_OPUS_MODEL     固定 Opus 模型版本            │
│   ANTHROPIC_DEFAULT_SONNET_MODEL   固定 Sonnet 模型版本          │
│   ANTHROPIC_DEFAULT_HAIKU_MODEL    固定 Haiku 模型版本           │
│                                                                  │
│ 认证跳过（网关场景）                                               │
│   CLAUDE_CODE_SKIP_BEDROCK_AUTH    1 = 跳过 Bedrock 认证         │
│   CLAUDE_CODE_SKIP_VERTEX_AUTH     1 = 跳过 Vertex 认证          │
│   CLAUDE_CODE_SKIP_FOUNDRY_AUTH    1 = 跳过 Foundry 认证         │
│                                                                  │
│ 其他                                                             │
│   CLAUDE_CODE_GIT_BASH_PATH        Windows git-bash 路径         │
│   CLAUDE_CODE_USE_POWERSHELL_TOOL  1 = Windows 启用 PowerShell  │
│   CLAUDE_REMOTE_CONTROL_SESSION_NAME_PREFIX  RC 会话名称前缀     │
│   CLAUDE_CODE_DEBUG_LOGS_DIR       调试日志目录                  │
│   CLAUDE_CODE_SUBAGENT_MODEL       覆盖子代理模型                │
│   MAX_THINKING_TOKENS              思考 Token 预算               │
│   USE_BUILTIN_RIPGREP              0 = 使用系统 ripgrep          │
│   DISABLE_AUTOUPDATER              1 = 禁用自动更新              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 附录：配置文件的完整位置参考

### 文件系统布局

```
~/.claude/                          # 用户级配置目录
├── settings.json                   # 用户级设置
├── CLAUDE.md                       # 用户级指令
├── agents/                         # 用户级子代理定义
├── skills/                         # 用户级技能
├── projects/                       # 项目记忆存储
│   └── <project>/
│       └── memory/
│           ├── MEMORY.md
│           └── <topic>.md
└── agent-memory/                   # 子代理持久记忆
    └── <agent-name>/

.claude/                            # 项目级配置目录（git 版本控制）
├── settings.json                   # 项目级设置
├── settings.local.json             # 本地设置（gitignore）
├── CLAUDE.md                       # 项目级指令
├── CLAUDE.local.md                 # 本地项目指令（gitignore）
├── rules/                          # 路径范围规则
│   ├── code-style.md
│   └── testing.md
├── agents/                         # 项目级子代理
│   └── <name>.md
├── skills/                         # 项目级技能
│   └── <skill-name>/
│       └── SKILL.md
└── worktrees/                      # Git worktrees

/etc/claude-code/                   # 企业级配置（Linux）
├── CLAUDE.md                       # 组织级指令
└── managed-settings.json           # 托管设置

/omc/state/                         # oh-my-claudecode 状态
├── <mode>.json
└── ...
/omc/plans/                         # oh-my-claudecode 计划
└── <plan-name>.md
/omc/notepads/                      # oh-my-claudecode 笔记
└── <plan-name>/
```

### 配置文件加载顺序

```
启动 Claude Code
  │
  ├─ 1. 加载 Managed Settings（服务器/MDM）
  ├─ 2. 加载 User Settings (~/.claude/settings.json)
  ├─ 3. 加载 Project Settings (.claude/settings.json)
  ├─ 4. 加载 Local Settings (.claude/settings.local.json)
  ├─ 5. 应用 CLI 参数覆盖
  │
  ├─ 6. 加载 CLAUDE.md（从 cwd 向上遍历）
  ├─ 7. 加载 .claude/rules/（按需）
  ├─ 8. 加载 Agents（按优先级）
  ├─ 9. 加载 Skills（按优先级）
  ├─ 10. 加载 MCP 服务器
  ├─ 11. 加载 Hooks
  ├─ 12. 加载 Auto Memory
  │
  └─ 就绪
```

---

*本文档基于 Claude Code 官方文档 (code.claude.com/docs)、oh-my-claudecode 框架实践，以及 auto-coding 专项研究（5 份研究文档，约 5334 行）综合编写。*
*技术细节请参考：/home/song/blank/auto-coding/ 目录下的研究文档。*
*版本：v5.0 | 2026-04-14*
