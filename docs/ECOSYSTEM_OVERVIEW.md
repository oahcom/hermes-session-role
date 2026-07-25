# Hermes Session Ecosystem — 三项目整合总览

## 架构全景

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  角色定义                    执行引擎                   路由+调度        │
│  hermes-session-roles        session-launcher          session-pipeline │
│  (定义层)                     (执行层)                  (路由层)         │
│                                                                         │
│  ┌─────────────────┐    ┌───────────────────┐    ┌───────────────────┐  │
│  │ personas/*.json  │    │ ccs.py            │    │ router.py         │  │
│  │ name/title       │───→│ start/stop/send   │    │ auto_route.py     │  │
│  │ system_prompt    │    │ watchdog/tracker  │    │ reliability.py    │  │
│  │ input_signals    │    │ partner_client    │    │ workflow_engine   │  │
│  │ output_targets   │    │ ecosystem_health  │    │ pipeflow/         │  │
│  └────────┬────────┘    └────────┬──────────┘    └────────┬──────────┘  │
│           │                     │                        │              │
│           └─────────────────────┼────────────────────────┘              │
│                                 │                                       │
│                    ┌────────────▼────────────┐                          │
│                    │     Sister Bus          │                          │
│                    │  blackboard.db (SQLite)  │                          │
│                    │  + Unix Socket (feed)   │                          │
│                    │  + FTS5 全文搜索        │                          │
│                    └─────────────────────────┘                          │
│                                 │                                       │
│                    ┌────────────▼────────────┐                          │
│                    │   CCS Workspaces        │                          │
│                    │   ~/ccs-workspaces/     │                          │
│                    │   各角色独立 CLAUDE.md   │                          │
│                    │   由 daemon 驱动            │                          │
│                    └─────────────────────────┘                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 三项目分工

| 项目 | 类比 | 职责 | 代码量 | 核心语言 |
|------|------|------|--------|----------|
| hermes-session-roles | /etc/passwd | 角色身份定义 | ~2700 行 | JSON + Python |
| session-launcher | systemd | 进程管理、上下文隔离 | ~6000 行 | Python |
| session-pipeline | 消息队列 + 路由表 | 通信基础设施 | ~4000 行 | Python |

## 核心概念对比

| 概念 | hermes-session-roles | session-launcher | session-pipeline |
|------|---------------------|------------------|------------------|
| 角色 | PersonaDef / RoleDef（JSON） | CCS tmux session | Router produce/consume 映射 |
| 数据流 | 角色 → launcher 注入知识 | workspace CLAUDE.md | Bus → 消费者路由 |
| 生命周期 | lifecycle + drive 字段 | start/stop/watchdog | 消息 TTL |
| 通信 | — | send / send-direct / send-safe | Bus poll + priority |
| 协作 | ~~role_relations 矩阵~~ (已删除) → 注册表元数据 | partner_client (Layer 1-3) | 消费联动 |
| 健康 | 角色 JSON 验证 | ecosystem_health.py | CCS 哨兵实时派生 |

## 数据流全景

```
1. 角色定义阶段（session-roles）

   persona_05_engineer.json ──→ session-launcher 读取
   ├── name, title, system_prompt  → 构建 CCS workspace CLAUDE.md
   ├── input_signals               → pipeline 用来自动推导 consume 分类
   └── output_targets              → pipeline 用来自动推导 produce 分类

2. 启动阶段（session-launcher）

   ccs.py start engineer
   ├── 读取 hermes-session-roles 的角色定义
   ├── 创建 ~/ccs-workspaces/ccs-engineer/
   ├── 注入 KNOWLEDGE 块到 CLAUDE.md（红线+专业+输入信号+输出目标）
   ├── 启动 tmux + claude 进程
   └── 写哨兵 /tmp/ccs-sentinels/engineer.json
       └── watchdog 守护伙伴存活
       └── tracker 轮次死锁检测

3. 路由阶段（session-pipeline）

   auto_route.py --daemon
   ├── 轮询 Bus 未消费消息（60s 间隔）
   ├── Router.get_consumers(category) → 确定应消费的角色
   ├── 按优先级排序（security > code_fix > architecture）
   └── 通知角色（Bus write 或 CCS send）

4. 消费联动（session-launcher）

   partner_client.py confirm / send-safe
   ├── Layer 1: 双信号确认交付（task.status + bus notification）
   ├── Layer 2: 伙伴状态解析（哨兵 + tmux + workflow DB）
   └── Layer 3: 唤醒 / 强制发送消息
```

## 项目文件引用关系

```
session-launcher
├── src/routing/roles.py
│   └── loads  → hermes-session-roles/personas/session-roles/*.json
│   └── reads  → hermes-session-roles/prompts/base.md
├── src/ecosystem_health.py
│   └── checks → hermes-session-roles/src/validate_roles.py
│   └── checks → session-pipeline/src/router.py
└── src/ops/sentinel.py
    └── reads  → hermes-session-roles/personas/session-roles/*.json

session-pipeline
├── src/routing/router.py
│   └── loads  → hermes-session-roles/personas/session-roles/*.json
│   └── loads  → hermes-session-roles/personas/browser-harness/_bh_route_config.json
└── src/routing/auto.py
    └── calls  → session-launcher/src/ops/sentinel.py
    └── sends  → Sister Bus
```

## 关键设计决策

### 为什么协作逻辑在代码层不在 prompt 中？

协作逻辑（守护伙伴、死锁检测、权限控制）全部在 `ccs.py`、`partner_client.py`、`watchdog.py` 的 Python 代码中实现，不在角色 prompt 里写协作规则。原因是:
- AI 会自由解释协作规则，代码执行是确定的
- prompt 里注入协作逻辑会稀释角色专业度
- 协作规则变更不用重新生成角色 prompt

### 为什么哨兵数据从 tmux 实时派生？

V1.0 使用持久化 JSON 哨兵文件导致:
- 孤儿文件堆积（CCS 异常退出后哨兵没清理）
- 与 tmux 真实状态不一致
- 并发写入竞争

V2.0 全部从 tmux sessions + 角色 JSON 实时派生，只有一个 `/tmp/ccs-health/{role}.json` 存 watchdog 状态。

### 为什么消息路由是 pull 不是 push？

`session-pipeline` 采用 poll 模式（每 60s 拉取未消费消息），而非事件 push:
- push 需要维护长连接 + 重连逻辑
- poll 天然支持幂等消费
- poll 更容易做熔断和流量控制
- 60s 延迟对非实时系统可接受

## 公共 API

三个项目各提供一个 PUBLIC_API.md:

| 项目 | API 地址 | 核心功能 |
|------|---------|---------|
| hermes-session-roles | PUBLIC_API.md, src/cli.py | list/show/load/search |
| session-launcher | PUBLIC_API.md, src/ccs.py | start/stop/send/status/health |
| session-pipeline | PUBLIC_API.md, src/router.py, src/auto_route.py | route/poll/dashboard |

## 故障排查快速索引

| 症状 | 可能原因 | 检查命令 |
|------|---------|---------|
| CCS 启动失败 | 内存不足 | `free -m` |
| CCS 进程消失 | watchdog 未启动 | `ccs status` |
| 消息路由不到 | 消费者 consume 分类不匹配 | `auto_route.py --route-all --dry-run` |
| 死锁提醒 | bus 分类无新消息 >5min | `bus_client.py read --cat X` |
| 角色定义不生效 | roles.py 缓存未刷新 | `ccs.py reload-knowledge` |
| 路由表不一致 | DB 与 JSON 不同步 | `router.py audit` |

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| V2.0 | 2026-07 | 哨兵系统重写（tmux 实时派生）, ecosystem_health 统一检查, 配置文件热重载 |
| V1.1 | 2026-06 | 跨角色协作增强（PartnerClient 三层架构） |
| V1.0 | 2026-05 | 初版三项目拆分完成 |
