# Session 三项目架构

版本: 2026-07-25 | 范围: hermes-session-roles / session-launcher / session-pipeline | 方法: 代码通读 46 源文件 + 4 专家工作流审查

> 本项目内部架构参见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

---

## TL;DR（给 AI 的第一段）

- 三个项目不是"定义→执行→路由"流水线。实际关系是：**session-roles（定义）→ launcher（进程管理） + pipeline（路由+工作流）**，两者各自独立消费 session-roles 的定义输出。pipeline 和 launcher 不直接通信，pipeline 通过 subprocess 调 launcher/ccs.py send
- 执行循环已存在（`pipeflow/daemon.py` while 循环），不是断裂的
- **角色契约（persona JSON → produce/consume 关系）是唯一不依赖任何运行时假设的资产**
- **最大风险是接口无文档**：`_ensure_role_alive()` 从 pipeline subprocess 调 launcher/ccs.py start 并注入无效 `/loop`，launcher 改 CLI 时 pipeline 静默失败
- **下一步唯一最该做的事**：把 `_ensure_role_alive()` 从 `drive="loop"` 改为 `drive="ondemand"`。改动点：`engine.py:582` 将 `"--drive", "loop"` 改为 `"--drive", "ondemand"`。效果：CCS 处理完消息自行退出，不浪费资源；engine 下次 `_send_to_role` 时再启动。代价 ~2-3s 启动延迟，收益 ~8GB 显存

---

## 1. 三个项目解决的根本问题

AI 上下文有限，但工程工作无限。一个 session 只能装一件事的上下文。把运维、开发、审查、决策塞进同一个 session = 全部稀释成通用水平。

三项目的核心回答：**让每个专业角色独占一个独立进程、一个独立上下文、一个独立循环。**

| 项目 | 层次 | 解决什么 |
|------|------|----------|
| hermes-session-roles | 定义层 | 专业知识蒸馏与隔离——角色 prompt 做到极致深度不被稀释 |
| session-launcher | 进程管理 | 跨 session 持久化——AI session ephemeral，tmux+哨兵让它持久 |
| session-pipeline | 路由+执行 | 有状态消息路由 + 工作流引擎 |

### 实际关系（非三层流水线，两消费者并行）

```
session-roles（定义）
  ├──→ launcher（进程管理）         ← 读 persona JSON 启动 CCS + 注入 prompt
  └──→ pipeline（路由+工作流）      ← 读 persona JSON 构建路由表
         └──→ launcher/ccs.py send  ← 唯一跨项目调用方式（subprocess）
```

---

## 2. 执行循环（代码追踪）

循环已存在，**不是断裂的**。

```
pipeflow/daemon.py:51-76       while True (sleep 10s) — 这是系统唯一的执行循环
  └── engine.py:258            run_once()
        ├── _ensure_role_alive()          检查 CCS 是否存活，死了则启动并注入 /loop（无效但无害）。不阻塞
        ├── SQLite 扫描                   workflow_instances WHERE status IN (pending, running)
        │     └── 对每个运行中工作流：
        │           ├── 步骤未开始               → 发初始 prompt 给目标角色
        │           ├── exit_condition 匹配      → 推进到下一步
        │           ├── 超时未完成               → 提醒→重复提醒→升级给 coordinator
        │           └── 子工作流完成             → 推进父工作流
        ├── _check_anomalies()                检测多步骤卡死→尝试自愈（重发 prompt）
        └── _scan_tasks()                     同步 task 状态 + 子工作流级联推进
```

---

## 3. 角色契约（唯一核心资产）

### 3.1 定义

角色契约 = {身份 + 专业域 + 输入信号 + 产出承诺 + 校验标准 + 能力工具 + 协作组}

不依赖任何运行时假设：不需要 `/loop`、CCS 存活、tmux——纯数据，换任何底层都成立。

### 3.2 字段消费现状

| 字段 | 定义位置 | 消费情况 | 状态 |
|------|----------|----------|------|
| name/title/category | persona JSON | models.py PersonaDef | ✅ |
| system_prompt + prompt_refs | persona JSON | role_assembler 编译 → inject to workspace | ✅ |
| constraints | persona JSON | gatekeeper 校验 + wake_permission | ✅ |
| lifecycle/drive | persona JSON | ccs.py start 消费（ondemand/infinite） | ✅ |
| output_targets | persona JSON | pipeline/router.py → produce/consume 推导 | ✅ |
| input_signals | persona JSON | launcher/routing/roles.py 推导 bus_track（core.py:414）+ launcher/events/signals.py 检查器 | ✅ 已消费 |
| eval_criteria | persona JSON | 仅注入 CLAUDE.md，无运行时执行 | ⚠️ 无运行时执行 |
| skills + skill_refs | persona JSON | role_assembler 读 skill，**未自动 /skill load** | ⚠️ 无自动加载 |
| workgroup | persona JSON | 存在但**无任何代码消费** | ❌ 完全未用 |
| cron_schedule | persona JSON | 存在但**无消费者**（CronCreate 在 tmux 不可用） | ❌ 无消费者 |
| mcp 段 | **不存在** | 所有 CCS 共享全局 MCP | ❌ 缺字段 |
| sla_seconds | **不存在** | tracker 硬编码 300s | ❌ 缺字段 |

### 3.3 为什么"角色契约的质量决定系统天花板"

代码保证"如约执行"。契约保证"执行的是什么"。角色定义错了，再完美的路由也只是把垃圾送得更快。

---

## 4. Claude Code 五机制的分层映射

### 4.1 当前 vs 应然

| 机制 | 作用域 | 当前问题 | 应然 |
|------|--------|----------|------|
| CLAUDE.md | 进程级 | 系统级 CLAUDE.md 含项目细节；三项目无自己的 CLAUDE.md；角色级 CLAUDE.md 被 inject 但不含契约区块 | 系统级放通用准则，项目级放项目规则，角色级放角色契约编译结果 |
| Skill | 对话级 | skill_refs 被引用但**不自动加载**，内容编译进 prompt 失去热更新能力 | CCS 启动时自动 /skill load |
| MCP | 进程级 | **所有角色共享同一套 MCP 工具**（maintainer 和 debate_verifier 看到 10+ 相同工具） | 角色级 per-workspace settings.json 隔离 MCP |
| 对话 prompt | 对话级 | **承载了本应放 CLAUDE.md 的身份定义**（"你是谁"+"请做什么"混在一起） | 只承载任务指令 |
| Settings | 进程级 | 没有 per-workspace settings.json | 三层继承：全局→项目→角色 |

### 4.2 最严重的分层越界

1. **MCP 扁平化**：所有 CCS 共享全局 MCP，低质 LLM 在 30+ 工具中选择困难。应该角色级隔离
2. **对话 prompt 过载**：`_build_role_prompt()` + `auto_send` 把身份和任务混发。身份应放角色 CLAUDE.md
3. **Skill 形同虚设**：角色能力写在 prompt 里而不是通过 `/skill load` 加载，无法热更新

---

## 5. 存活的三层定义

| 层级 | 含义 | 当前有？ |
|------|------|----------|
| L1 进程存活 | tmux session 存在，CCS 进程在运行 | ✅ `_is_alive()` + tmux has-session |
| L2 思考存活 | LLM 在消耗 token 推理（哪怕空转） | ❌ 无 |
| L3 产出存活 | 角色产生有意义的 bus 消息或文件变更 | ❌ 无 |

**`/loop` 不可用的陷阱**：CCS 活着（L1 ✅）但 LLM 可能空转（L3 ❌），系统认为"存活正常"。
`_ensure_role_alive()` 注入 `/loop` 是无用操作——不会报错，但 CCS 也不会因此进入工作循环。

**这不是崩溃性故障**——engine.py 每 10s 主动 `ccs.py send` 推动工作流，CCS 收到消息仍能正常处理。问题在于 CCS 在 idle 时浪费资源（~8GB 显存）。

---

## 6. 三项目价值审计（按文件粒度）

### 6.1 高价值文件（18 文件占 ~90% 价值）

| 项目 | 文件 | 行数 | 职责 | 价值 |
|------|------|------|------|------|
| session-roles | src/models.py | 150 | PersonaDef + RoleDef 数据结构 | 🔴🔴🔴 |
| session-roles | src/registry.py | 120 | JSON 加载 + 注册表 | 🔴🔴🔴 |
| session-roles | src/role_assembler.py | 139 | 三层 prompt 编译 | 🔴🔴🔴 |
| session-roles | src/validate_roles.py | ~150 | JSON schema + 校验 | 🔴🔴 |
| session-roles | src/shared_loader.py | ~80 | 统一导出 | 🔴🔴 |
| launcher | src/ccs.py | 477 | CLI 入口 + 命令分发 | 🔴🔴🔴 |
| launcher | src/core.py | 554 | CCS 生命周期（start/send/stop/health） | 🔴🔴🔴 |
| launcher | src/routing/roles.py | ~250 | 角色加载 + workspace 注入 + 权限 | 🔴🔴🔴 |
| launcher | src/routing/gatekeeper.py | ~120 | 三源验证 + 敏感操作门禁 | 🔴🔴 |
| launcher | src/ops/sentinel.py | ~150 | 哨兵文件系统 | 🟡 |
| pipeline | src/routing/router.py | 365 | 路由表 + produce/consume 推导 | 🔴🔴🔴 |
| pipeline | src/routing/routes.py | 284 | route_all + route_to_ccs | 🔴🔴🔴 |
| pipeline | src/routing/auto.py | 303 | 自动路由消费 + investigator 分派 | 🔴🔴🔴 |
| pipeline | src/routing/polling.py | 81 | 消息轮询 + cursor | 🔴🔴 |
| pipeline | src/pipeflow/engine.py | 847 | 工作流状态机执行器 | 🔴🔴🔴 |
| pipeline | src/pipeflow/daemon.py | 88 | while 循环 driver | 🔴🔴🔴 |
| pipeline | src/lifecycle/manager.py | 995 | 状态机核心 + 审批 + 回滚 | 🔴🔴🔴 |
| pipeline | src/reliability.py + core | ~300 | 熔断器/心跳/幂等消费/ACK | 🔴🔴 |

### 6.2 低价值/可精简（launcher ~22 文件，核心在 5 个）

| 模块 | 建议 | 原因 |
|------|------|------|
| lifecycle/ (5 文件) | 标记废弃 | 与 pipeline lifecycle **不同**（launcher 的是进程生命周期钩子，pipeline 的是工作流状态机）。但 launcher 的 lifecycle 低活跃度，可废弃 |
| events/ (4 文件) | 合并到 signal_parser.py | 只 signal_parser 被引用 |
| worker_pool + parallel + pool_cli | 删除 | 无实际消费方 |
| codex_ops | 保留但不动 | 低频使用，无需重构 |
| ecosystem_health* | 调用图验证后合并或删 | 与 runner.dashboard 重叠 |

---

## 7. 缺失的环节

### 7.1 角色契约缺口

| 缺口 | 影响 | 方案 |
|------|------|------|
| 无 mcp 段 | 所有角色共享 MCP，低质 LLM 迷失 | persona JSON 加 mcp_servers/tools/permissions |
| eval_criteria 无运行时执行 | 契约违反无闭环 | 定时器挑 eval_criteria 执行，失败写 bus |
| workgroup 字段废弃 | 协作组声明无人消费 | router 用 workgroup 做 fallback |
| output_targets 无送达确认 | 写了 bus 但无人消费不知 | delivery_mode + require_ack |
| 无契约版本追踪 | 角色变更无人感知 | audit log 消费 + 变更通知 |

### 7.2 `/loop` 不可用

不是崩溃性故障，但：
- `_ensure_role_alive()` 中 `tmux send-keys /loop` 是无用操作
- CCS 处理完一条消息后 idle 等下一轮 push
- engine 每 10s poll，轮询延迟增加响应时间

**修复方案**（一个改动点）：`engine.py:582` 将 `"--drive", "loop"` 改为 `"--drive", "ondemand"`。改成 ondemand 后，CCS 处理完消息自行 exit，不 idle 占资源；engine 下次 `_send_to_role` 时 `_ensure_role_alive()` 会重新启动 CCS。这是一行改动，不涉及架构变更。

### 7.3 Engine-Lifecycle 重复（pipeline 内部，不是跨项目）

**双 lifecycle 的初判是错误结论**（已在 9.2 争议与裁决中澄清）。实际问题是：

`engine.py` 有 3 处绕过 `lifecycle/manager.py` 直接写 SQL：
- `_advance_production_wf()` — 推进步骤时直接 `conn.execute` 更新 step_results
- `_tick()` — 超时检测时通过 `_sync_step_results()` 直接写数据库
- `_scan_tasks()` — 子工作流完成时直接 `conn.execute` 推进父工作流

后果：这些绕过丢掉了 lifecycle manager 的 RLock 保护 + 审批流程 + 状态校验。但这不是崩溃性问题——写入仍会成功，只是并发场景下可能丢失一致性。

### 7.4 执行层 vs 定义层语义鸿沟

persona JSON 定义了 `drive: "cron"` 的角色（maintainer、scout）和 `cron_schedule`，但：
- CronCreate 在 tmux 不可用
- systemd timer / OS cron 未建立
- 这些角色需要 pipeflow/daemon.py 驱动，但 daemon 的轮询只针对工作流不针对 cron 角色

---

## 8. 发展方向（按优先级）

### P0：CCS 改为 ondemand 模式（最优先）

一行改动：`engine.py:582` 将 `"--drive", "loop"` 改为 `"--drive", "ondemand"`。
- 现状：`/loop` 在 tmux 中不可用，注入它不报错但无效果。CCS 处理完消息后 idle 占 ~8GB 显存
- 改后：CCS 处理完消息自行 exit，engine 下次需要时 `_ensure_role_alive()` 重新启动。代价 ~2-3s 启动延迟

### P0：完善角色契约（持续投入）

```
models.py 加：mcp_servers, mcp_tools, mcp_permissions, sla_seconds, auto_send_messages
validate_roles.py 加：mcp 校验, produce/consume 分类注册表校验
registry.py 加：契约变更触发通知（写 bus architecture）
```

### P1：消除 engine.py 对 lifecycle manager 的绕过

修复 `engine.py` 中 3 处绕过 `lifecycle/manager.py` 直接写 SQL 的路径（`_advance_production_wf()`, `_tick()`, `_scan_tasks()`）。这些绕过丢失了 RLock 保护和审批流程。合并到 `LifecycleManager.advance()`。

**注意**：launcher 的 lifecycle/ 是进程生命周期钩子（start/stop 事件），pipeline 的 lifecycle/manager 是工作流状态机（步骤类型/审批/回滚），两者是不同的关注点，不存在"重复"。

### P2：launcher 瘦身

保留 5 核心（ccs.py, core.py, roles.py, gatekeeper.py, sentinel.py）+ 2 辅助（ccs_config.py, workspace.py）。其余标记废弃或合并。

---

## 9. 多 Agent 审查结果（2026-07-25）

### 共识

1. 文档与实际代码有显著 gap
2. Persona JSON 字段定义了但下游不消费（`cron_schedule`, `workgroup`, MCP 声明等）
3. 跨项目调用边界无文档（`_ensure_role_alive()` 是典型案例）
4. 无角色定义变更门禁

### 争议与裁决

| 争议 | 裁决 |
|------|------|
| 双 lifecycle？ | ❌ 不存在跨项目重复。但 engine.py 内部有 3 处绕过 lifecycle manager 直接写 SQL——这是真正的内部重复 |
| `_ensure_role_alive` 在哪？ | pipeline/engine.py，不是 launcher。跨项目耦合未文档化 |
| launcher 文件数 30 vs 22？ | 22 准确。应注明统计日期 |
| Codex CLI 定位 | **是工具，不是后端**。codex_ops.py 把它塞进 tmux pane 是强行适配 |
| ecosystem_health.py 删/留？ | 先做调用图验证，看 runner.dashboard 是否覆盖其输出 |
| 类别注册表优先级 | P2，降级。40 个隐式分类无实际事故记录，应先修有 runtime 影响的问题 |

### 最该先做的一件事

> **把 `_ensure_role_alive()` 的 `drive="loop"` 改为 `drive="ondemand"`。改动点在 `engine.py:582`，一行。**

理由：
- `/loop` 在 tmux 中不可用——CCS 收到 `/loop` 命令后不会进入工作循环，但不报错
- 改成 ondemand 后 CCS 处理完消息就退出，不 idle 占资源（~8GB 显存/实例）
- engine 下次需要时通过 `_ensure_role_alive()` 重新启动，代价 ~2-3s 启动延迟
- **没有专家反对**

---

## 10. 关键修正记录

| 原断言 | 结论 | 依据 |
|--------|------|------|
| 执行层断裂 | ❌ 执行循环存在 | pipeline 专家代码追踪 |
| watchdog/sentinel 是僵尸 | ❌ 活跃，被 --partner 触发 | launcher 专家验证 |
| CCS 从不持久运行 | ⚠️ ondemand 不持久，但 engine 会启动持久 CCS | 双方证据 |
| launcher/pipeline 各持半套工作流 | ⚠️ launcher lifecycle 是空壳；但 engine.py 有 3 处绕过 lifecycle manager | pipeline 专家发现 |
| 双 lifecycle | ❌ 不存在跨项目重复 | 综合裁决 |
| Codex CLI 是第二后端 | ❌ 是工具，不是后端 | 用户纠正 + Codex 专家 |

---

## 附录：三项目核心入口

| 项目 | 入口 | 调用方式 |
|------|------|----------|
| session-roles | `python3 src/cli.py list/show/load/search` | CLI |
| session-roles | `python3 src/role_assembler.py <role>` | CLI |
| session-roles | `python3 src/shared_loader.py` | CLI |
| session-roles | `python3 src/validate_roles.py` | CLI |
| session-launcher | `python3 src/ccs.py start\|stop\|send\|output` | subprocess（by pipeline）或 CLI |
| session-pipeline | `python3 src/pipeflow/daemon.py --interval 10` | systemd / 后台进程 |
| session-pipeline | `python3 -m routing.router register\|list\|audit` | CLI |
| session-pipeline | `python3 -m routing.auto --route-all` | CLI / cron |
