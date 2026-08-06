# Claude Code 特性参考

> 版本: 2.0 | 更新: 2026-07-27
> 来源: `claude --help`、`claude <subcommand> --help`、实际运行验证
> 目的：记录 Claude Code 运行时特性、命令体系、技能/MCP/Hook/Plugin 加载机制

---

## 零、基本信息

| 属性 | 值 |
|------|-----|
| 版本 | 2.1.220 |
| 安装方式 | `npx @anthropic-ai/claude-code` 或 native build |
| 更新 | `claude update` |
| 健康检查 | `claude doctor` |
| CLI 启动 | `claude [options] [command] [prompt]` |
| 默认模式 | 交互式 session，`-p/--print` 切换非交互 |

---

## 一、技能体系（Skills）

### 1.1 核心原则

**技能不被"加载"，被"发现"。** Claude Code 没有按需加载/卸载技能的命令。

| 命令 | 作用 |
|------|------|
| `/skills` | 列出当前可用技能（仅列表） |
| `--disable-slash-commands` | 禁用在会话内所有技能 |
| `--bare` | 最小模式：跳过 CLAUDE.md 发现，**技能仍可通过 `/skill-name` 解析** |

### 1.2 发现路径

```
~/.claude/skills/               # 全局 — 所有 session 可见
<project>/.claude/skills/       # 项目级 — 仅该项目可见
```

Claude Code 启动时自动扫描这些目录，每个含 `SKILL.md` 的子目录注册为可用技能。

### 1.3 Plugins（新型技能）

从 2.x 起，Plugin 是技能的正式封装格式，提供版本管理、市场分发和依赖管理：

| 命令 | 作用 |
|------|------|
| `claude plugin init <name>` | 在 `~/.claude/skills/<name>/` 脚手架新插件 |
| `claude plugin install <plugin>` | 从 marketplace 安装 |
| `claude plugin list` | 列出已安装 |
| `claude plugin update <plugin>` | 更新（需重启） |
| `claude plugin details <name>` | 查看组件清单和预估 token 成本 |
| `claude plugin validate <path>` | 验证 manifest |
| `claude plugin eval <path>` | 运行 eval 用例评分 |
| `claude plugin marketplace` | 管理市场 |
| `claude plugin tag <path>` | 创建 release git tag |

**SKILL.md（传统技能）与 Plugin（包装格式）的关系**：Plugin 是对一组技能的封装，含 `plugin.json` 元数据和版本管理。技能可以在两种格式下工作。

### 1.4 HE 角色技能部署

```
~/shared-skills/hermes-origin/skills/   # 共享源（97 SKILL.md，26 分类）
    ↓ ln -sfn（deploy_role_skills.sh）
~/ccs-workspaces/<role>/.claude/skills/ # 角色专属
```

调用链：`ccs start <role>` → `core.py start()` → `deploy_role_skills.sh <role>`

---

## 二、Slash Commands（会话内命令）

| 命令 | 作用 |
|------|------|
| `/help` | 显示帮助 |
| `/clear` | 清空上下文，不中断 session |
| `/compact` | 压缩上下文 |
| `/resume` | 列出/恢复历史 session |
| `/rename` | 重命名当前 session |
| `/goal` | 设置 session 级目标 |
| `/loop` | 循环模式（自动/固定间隔） |
| `/fast` | 切快速模式（Opus 快速版） |
| `/code-review` | 审查未提交变更 |
| `/skills` | 列出可用技能 |
| `/config` | 查看/修改配置 |
| `/status` | 查看 session 状态 |
| `/plan` | 进入架构计划模式 |
| `/design` | 同 `/plan` |
| `/doctor` | 运行完整健康检查并修复问题 |

> **注意**：`claude --help` **不列出 slash commands**，以上列表来自实际运行验证。
> `--disable-slash-commands` 可以禁用所有技能。

---

## 三、Settings & Config

### 3.1 配置层级

```
~/.claude/settings.json                  # 全局用户设置
<project>/.claude/settings.json          # 项目设置（继承全局）
<project>/.claude/settings.local.json    # 本地覆盖（不提交）
```

加载来源控制：`--setting-sources user,project,local`

### 3.2 settings.json 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `model` | string | 默认模型 |
| `agent` | string | 默认 agent |
| `env` | object | 环境变量（如 `ANTHROPIC_MODEL`） |
| `permissions` | object | 权限模式（allow/disallow/defaultMode） |
| `hooks` | object | Hook 配置 |
| `mcpServers` | object | MCP Server 注册表 |
| `theme` | object | 主题配置 |
| `keybindings` | string | keybindings.json 路径 |

### 3.3 运行时覆盖

```bash
# 临时覆盖（优先级高于配置文件）
claude --settings ./my-settings.json     # 额外加载配置文件
claude --settings '{"model":"sonnet"}'   # JSON 字符串覆盖
claude --model opus                      # 模型覆盖
claude --effort max                      # 推理力度
claude --fallback-model sonnet           # 降级模型
```

### 3.4 CLAUDE.md

```bash
~/.claude/CLAUDE.md          # 全局身份指令
<project>/CLAUDE.md          # 项目指令（代码库中）
```

**自动发现**：Claude Code 启动时自动读取当前目录的 `CLAUDE.md`。`--bare` 模式跳过发现。

---

## 四、Hook 系统

### 4.1 配置

```json
{
  "hooks": {
    "PreToolUse": [{ "matcher": "Bash", "hooks": [{"type": "command", "command": ".."}] }],
    "PostToolUse": [{ "matcher": "*", "hooks": [{"type": "command", "command": ".."}] }],
    "Stop": [{ "hooks": [{"type": "command", "command": ".."}] }]
  }
}
```

### 4.2 Hook 类型

| Hook | 触发时机 | matcher 过滤 | 常见用途 |
|------|----------|-------------|----------|
| `PreToolUse` | 调用工具前 | 按工具名匹配 | 安全检查、路径拦截、命令重写 |
| `PostToolUse` | 工具返回后 | 按工具名匹配 | 结果过滤、审计日志、输出裁剪 |
| `Stop` | session 停止前 | 无（全局） | 条件守卫（阻止不合条件的停止） |

每个 Hook 可以配置多个 `hooks` 条目，按顺序执行。`timeout` 控制超时。

---

## 五、MCP Server

### 5.1 CLI 管理

| 命令 | 作用 |
|------|------|
| `claude mcp list` | 列出已配置（含未批准的 `.mcp.json`） |
| `claude mcp get <name>` | 查看详情（未批准的显示为 ⏸ 待审批） |
| `claude mcp add <name> <command>` | 添加 stdio 类型 |
| `claude mcp add --transport http <name> <url>` | 添加 HTTP/SSE 类型 |
| `claude mcp add-json <name> <json>` | JSON 字符串添加 |
| `claude mcp add-from-claude-desktop` | 从 Claude Desktop 导入 |
| `claude mcp remove <name>` | 移除 |
| `claude mcp login <name>` | OAuth 认证 |
| `claude mcp logout <name>` | 清除 OAuth 凭据 |
| `claude mcp reset-project-choices` | 重置项目级 `.mcp.json` 审批状态 |
| `claude mcp serve` | 将 Claude Code 本身暴露为 MCP server |

### 5.2 注册来源

1. **全局 settings.json** `mcpServers` 字段
2. **项目 settings.json**（继承 + 覆盖全局）
3. **插件 `.mcp.json`** 文件（marketplace 或 cache 目录）
4. **`--mcp-config` CLI 参数**（临时加载，可多次指定）
5. **`--strict-mcp-config`** 仅用 `--mcp-config`，忽略所有其他来源

### 5.3 HE 集成

`_load_mcp_registry()` 从全局 settings.json + 所有插件目录的 `.mcp.json` 合并注册表。角色 workspace 的 `settings.json` 继承全局 MCP，再按 `persona.mcp_servers` 增补。

---

## 六、Agent 系统

### 6.1 后台 Agent

```bash
claude --bg                              # 启动后台 agent
claude agents                            # 管理列表
claude agents --json                     # JSON 格式输出（适合脚本）
claude agents --all                      # 包含已完成的
claude agents --cwd <path>              # 按目录过滤
```

启动参数：`--agent <name>`、`--effort`、`--model`、`--permission-mode`、`--add-dir`、`--mcp-config`

### 6.2 自定义 Agent 定义

```bash
claude --agents '{"reviewer":{"description":"审查代码","prompt":"你是审查者"}}'
```

### 6.3 UltraReview

```bash
claude ultrareview [target]             # 云端多agent代码审查
claude ultrareview --json               # 输出原始 bugs.json
claude ultrareview --timeout 30         # 超时（分钟）
```

---

## 七、Plugin 市场

### 7.1 市场命令

| 命令 | 作用 |
|------|------|
| `claude plugin marketplace` | 管理市场源 |
| `claude plugin install <name>` | 安装 |
| `claude plugin uninstall <name>` | 卸载 |
| `claude plugin update <name>` | 更新（需重启 session） |
| `claude plugin list` | 列出已安装 |
| `claude plugin details <name>` | 组件清单 + token 预估 |
| `claude plugin enable/disable <name>` | 启用/禁用 |
| `claude plugin prune` | 清理不需要的依赖 |

安装来源：`plugin@marketplace`（指定市场）、目录路径、URL（`.zip`）

---

## 八、非交互模式

### 8.1 Print 模式

```bash
claude -p "你好"                        # 单次问答，输出到 stdout
claude -p --output-format json          # JSON 格式
claude -p --output-format stream-json   # 流式 JSON
echo "你好" | claude -p                 # 管道输入
```

### 8.2 流式输入

```bash
claude -p --input-format stream-json     # 实时流式输入
```

### 8.3 结构化输出

```bash
claude -p --json-schema '{"type":"object","properties":{"name":{"type":"string"}},"required":["name"]}'
```

### 8.4 SDK 集成（MCP Server 模式）

```bash
claude mcp serve                         # 启动 MCP server，供 SDK 调用
```

### 8.5 其他非交互选项

| 选项 | 作用 |
|------|------|
| `--max-budget-usd <amount>` | API 费用上限 |
| `--no-session-persistence` | 不持久化 session |
| `--session-id <uuid>` | 指定 session ID |
| `--replay-user-messages` | 回显用户消息（流式确认） |
| `--include-hook-events` | 在输出流中包含 hook 事件 |
| `--include-partial-messages` | 包含部分消息块 |
| `--forward-subagent-text` | 转发 subagent 文本 |

---

## 九、工作流与隔离

### 9.1 Worktree

```bash
claude -w                                # 创建新 git worktree
claude -w feature-name                   # 指定名称
claude --tmux                            # 在 tmux 中启动 worktree session
claude --tmux=classic                    # 传统 tmux（非 iTerm2）
```

### 9.2 Session 管理

| 命令/选项 | 作用 |
|-----------|------|
| `claude -c` | 继续最近的 session |
| `claude -r` | 选择恢复 |
| `claude -r <id>` | 按 ID 恢复 |
| `claude --fork-session` | 恢复时创建新 session ID |
| `claude --from-pr <url>` | 关联 PR 恢复 |
| `claude -n <name>` | 命名 session |
| `claude project purge <path>` | 删除项目的所有 state |

---

## 十、安全和权限

### 10.1 权限模式

```bash
--permission-mode auto                   # 自动审批
--permission-mode bypassPermissions      # 跳过所有
--permission-mode manual                 # 手动确认
--permission-mode dontAsk                # 不问
--permission-mode plan                   # 计划模式（只读）
```

### 10.2 工具白名单/黑名单

```bash
--allowed-tools "Bash(git *) Edit"       # 只允许 Bash(git) 和 Edit
--disallowed-tools "Bash(rm *)"          # 禁止特定操作
--tools "Bash,Edit,Read"                 # 精确指定可用工具
--tools ""                               # 禁用所有工具
```

### 10.3 安全模式

```bash
--safe-mode                              # 禁用所有自定义（CLAUDE.md/skills/plugins/hooks/MCP/自定义命令）
claude doctor                            # 健康检查
```

---

## 十一、调试

```bash
-d, --debug [filter]                     # 调试模式（可选过滤类别）
--debug-file <path>                      # 输出到文件
--verbose                                # 详细日志
```

---

## 十二、常见误区

| # | 误区 | 正解 |
|---|------|------|
| 1 | `/skill <name>` 可以加载技能 | ❌ 未知命令；技能放 `.claude/skills/` 自动发现 |
| 2 | `/skills` 会加载技能 | ❌ 仅列表 |
| 3 | skills 需要 session 内命令激活 | ❌ 目录发现，零命令 |
| 4 | 修改 skill 后需重启 session | ❌ symlink 指向源，下次 `ccs start` 自动更新 |
| 5 | project settings.json 需写全量 MCP | ❌ 只写差异，继承全局 |
| 6 | `ccs start` 不涉及技能 | ❌ 已集成 `deploy_role_skills.sh` |
| 7 | Plugin 和 Skill 是两套系统 | ❌ Plugin 是对技能集的包装格式 |
| 8 | `--bare` 禁用所有技能 | ❌ `--bare` 只跳过 CLAUDE.md 发现，技能仍可通过 `/skill-name` 解析 |
| 9 | `--safe-mode` 禁用所有功能 | ❌ 管理策略（policy）仍然生效，auth/模型/内置工具/权限正常工作 |
