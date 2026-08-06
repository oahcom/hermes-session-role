# Claude Code 特性对 HE Session 生态的可用性分析

> 版本: 1.0 | 基于 `claude --help` + 三项目代码扫描

---

## 一、当前系统边界

HE 用 **tmux + ccs.py + bus** 搭建了完整的多角色 session 管理。Claude Code 自身也有一大堆内置特性，两者重叠但定位不同。

```
HE Session 系统：
  ccs.py start <role> → tmux session（claude code 进程）
                      → workspace（claude code 实例）
                      → bus 通信

Claude Code 原生：
  claude --bg         → 后台 agent
  claude agents       → 管理列表
  claude -w           → worktree 隔离
  claude -p           → 非交互模式
```

关键在于**哪些 CC 特性可以复用/接管**，避免 HE 重复造。

---

## 二、逐一分析

### 2.1 Agent 管理（高价值）

| 特性 | 说明 | HE 现状 | 方案 |
|------|------|---------|------|
| `claude agents --json` | 列出所有 agent（含后台），JSON 输出 | HE 通过 tmux + sentinel 文件维护 | 替换 sentinel 轮询，CC 原生 API 更可靠 |
| `claude --bg` | 启动后台 agent 立即返回 | `ccs start --detach` | 互补——HE 管理 tmux 生命周期，CC agent 提供内向监控 CLI |

**结论**：过渡到 `claude agents --json` 替换 `list_sentinels()` + `/tmp/ccs-sentinels/`，减少自建轮询开销。

### 2.2 非交互模式（高价值）

| 特性 | 说明 | HE 现状 | 方案 |
|------|------|---------|------|
| `-p` / `--print` | 单次问答，stdout 输出 | `ccs send` + 读 output | pipeline 可用 `-p` 替代部分 `ccs send` 场景 |
| `--json-schema` | 结构化输出验证 | bus 消息无 schema 验证 | pipeline 调用子任务时用 schema 保证产出格式 |
| `--output-format` | json/stream-json | 无 | 日志/审计对接 |

**结论**：`--json-schema` 填补了 HE 最大的空白——**产出格式无契约**。工作流步骤可用 JSON Schema 声明期望产出，`-p` 模式执行。

### 2.3 Plugin / 技能市场（高价值）

| 特性 | 说明 | HE 现状 | 方案 |
|------|------|---------|------|
| `claude plugin init` | 脚手架新技能 | 手动写 SKILL.md | 用 `plugin init` 标准化创建流程 |
| `claude plugin list` | 列出已安装 | `ls .claude/skills/` | 统一 CLI |
| `claude plugin update` | 更新（需重启） | `deploy_role_skills.sh` | 对接到 CC 更新机制 |
| `claude plugin eval` | 跑 evals 评分 | 无 | 技能质量评估 |
| `claude plugin tag` | release 版本管理 | 无 | 技能版本化 |
| `claude plugin marketplace` | 市场分发 | 共享源目录 | 可扩展 |

**结论**：HE 的共享源（97 SKILL.md）转为 Plugin 格式，获得版本管理 + 分发 + eval。**这是最大的改进空间**——skill 升级不可追溯现在是痛点（改共享源后所有 workspace symlink 指向新版，无法灰度）。

### 2.4 安全 / 隔离（中价值）

| 特性 | 说明 | HE 现状 | 方案 |
|------|------|---------|------|
| `--safe-mode` | 禁用所有自定义 | 无对应 | **重要**：故障排查入口 |
| `--bare` | 最小模式（跳 CLAUDE.md） | 无 | CI/测试环境可用 |
| `--tools` / `--allowed-tools` | 工具白名单 | roles.py `_FORBIDDEN_MAP` + workspace `permissions.allow` | 互补——HE 按角色隔离，CC 按 session 隔离 |
| `--permission-mode` | 权限模式 | 已用 `defaultMode` | HE 已覆盖 |

**结论**：`--safe-mode` 应加入故障处理 SOP。roles.py 的 `_FORBIDDEN_MAP` 可以通过 `--disallowed-tools` 下沉到 CC。

### 2.5 工作流集成（中价值）

| 特性 | 说明 | HE 现状 | 方案 |
|------|------|---------|------|
| `claude mcp serve` | CC 作为 MCP server | `ccs.py send` + bus 通信 | pipeline 通过 MCP 调用 CC |
| `--worktree` | git worktree | `ccs workspace create` | 可复用，减少自建 |
| `--tmux` | tmux 内启动 | tmux_ops.py | 互补 |
| `--effort` | 推理力度 | 无 | 工作流可指定步骤 effort 级别 |

**结论**：`mcp serve` 最有趣——让 pipeline workflow engine 通过 **MCP 协议**而不是 `subprocess ccs.py send` 跟角色 session 通信。CC 当 MCP server，pipeline 当 MCP client。

### 2.6 会话管理（低价值）

| 特性 | 说明 | HE 现状 | 方案 |
|------|------|---------|------|
| `claude -r` / `--resume` | 恢复 session | HE session 持续运行 | 不冲突 |
| `claude --from-pr` | 关联 PR | 无 | 可忽略 |
| `claude project purge` | 删除 state | 手动 rm | 可纳入 cleanup SOP |

---

## 三、优先级排序（按投入产出比）

### P0：立即可用，零改造成本

| 特性 | 用法 |
|------|------|
| `--safe-mode` | 加到故障排查第一条 |
| `claude agents --json` | 替换 `list_sentinels()` 的健康检查 |
| `-p` + `--json-schema` | workflow exit_condition 增加 schema 验证步骤 |

### P1：近期改进，中等改造

| 特性 | 改动量 | 收益 |
|------|--------|------|
| `mcp serve` 替代 IPC | pipeline→ccs `send` 替换为 MCP | 标准协议，减少 subprocess 损耗 |
| `plugin` 格式封装 | 共享源技能加 `plugin.json` | 版本化 + marketplace + eval |
| `--effort` 对接 pipeline | workflow step 支持 effort 参数 | 精细控制推理开销 |

### P2：远期

| 特性 | 理由 |
|------|------|
| `--agents` JSON | 自定义 agent 与 persona 定义冗余 |
| `--worktree` | `ccs workspace` 已覆盖 |
| `--disallowed-tools` | HE 的 `_FORBIDDEN_MAP` 已够用 |

---

## 四、具体建议摘要

```diff
- _tmux_send(tmux_name, "status")      # 发命令读输出
+ subprocess.run(["claude", "agents", "--json"])   # 读原生状态

- sentinel list → parse JSON files      # 维护哨兵文件
+ claude agents --json                  # CC 原生 API

- bus 消息无 schema 验证                 # 产出格式全靠人格
+ workflow step 加 json_schema 字段
+ engine 用 claude -p --json-schema 执行

- deploy_role_skills.sh                  # 原始 symlink 部署
+ plugin init → plugin install          # 标准化插件生命周期

- subprocess ccs.py send                  # pipeline→session 通信
+ mcp client → mcp server (cc session)  # 标准 MCP 协议
```
