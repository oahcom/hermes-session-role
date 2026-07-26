# Architecture — hermes-session-roles

## Purpose
Role registry for Hermes multi-session ecosystem. Defines professional identity, prompts, I/O signals, and eval criteria for 31 session roles + 57 browser-harness personas. **Pure data layer -- zero runtime logic, zero dependencies on other two projects.**

## Position in ecosystem

```
hermes-session-roles (定义层)      ← 最底层，不引用其他项目
  ├──→ session-launcher (执行层)   ← 读 persona JSON 启动 CCS + 注入 prompt
  └──→ session-pipeline (路由层)   ← 读 roles_export.json 构建路由表
         └──→ launcher/ccs.py send ← 唯一跨项目调用（subprocess）
```

## File Layout

```
personas/
  session-roles/               # 31 基础设施角色（persona_XX_name.json）
  browser-harness/             # 57 浏览器自动化人格
    persona_01_core.json       # 10 核心人格
    persona_02_specialized.json # 25 专业人格
    persona_03_advanced.json   # 22 高级人格
    _bh_to_sr_map.json         # 浏览器人格 → Session 角色映射
    _bh_route_config.json      # 浏览器路由配置
    _ccs_injection_rules.json  # CCS 注入规则
    _ecosystem_health.json     # 生态健康检查

prompts/
  base.md                      # Layer 0: 全体角色共享（红线、协作协议）
  roles/                       # Layer 1: 各角色专业 prompt（23 个 .md 文件）
  mixins/                      # Layer 2: 驱动模式（loop/cron/ondemand）

src/
  models.py            # PersonaDef + RoleDef dataclass（~157行）
  shared_loader.py     # 统一角色加载器 + produce/consume 提取 + --export（~212行）
  validate_roles.py    # 全量校验 JSON schema + produce/consume 分类 + prompt 质量（~313行）
  registry.py          # 注册表 load_all/get/list_*/register + 契约变更通知（~145行）
  role_assembler.py    # 动态组装 system prompt, base→role→driver（~139行）
  paths.py             # 路径常量（不依赖 hermes_bus.config，~74行）

tests/
  test_registry.py

docs/
  ARCHITECTURE.md      # 本文档
  ARCHITECTURE_PROTOCOL.md
  ECOSYSTEM_OVERVIEW.md
  AUDIT_REPORT.md
  ...
```

## Data Model

### PersonaDef (browser-harness compatible, `models.py`）

```python
@dataclass
class PersonaDef:
    name: str
    title: str
    description: str
    category: str
    system_prompt: str
    config_overrides: dict = {}
    eval_criteria: list[str] = []
    prompt_refs: dict[str, str] = {}  # 模块化 prompt 引用（base/role/driver）
    skills: list[str] = []
    skill_refs: dict[str, str] = {}
    goal: str = ""
    constraints: list[str] = []
    mcp_servers: list[str] = []        # 角色需要的 MCP server
    mcp_tools: dict[str, list] = {}    # 角色能用的具体工具
    mcp_permissions: dict[str, list] = {}  # MCP 操作权限
    sla_seconds: int = 0              # 消息响应超时秒数
    auto_send_messages: list[str] = []  # 自动发送消息列表
```

### RoleDef (extends PersonaDef, `models.py`）

```python
@dataclass
class RoleDef(PersonaDef):
    lifecycle: str        # "infinite" | "ondemand"
    drive: str            # "cron" | "loop" | "ondemand" | "goal"
    cron_schedule: str    # e.g. "*/15 * * * *"
    idle_action: str      # "exit" | "continue"
    input_signals: list   # [{"type":"bus","spec":{"category":"..."},"filter":"..."}]
    output_targets: list  # ["bus cat=code_fix 修复方案", ...]
    session_hint: str     # "cron" | "interactive" | "background"
```

### RoleExport (via `shared_loader.py` -- consumed by pipeline）

```python
@dataclass
class RoleExport:
    name, title, category, description: str
    lifecycle, drive, cron_schedule: str
    routing: RoleRouting     # {produce: [...], consume: [...], consume_all: bool}
    workgroup: list[str]
    auto_send_messages: list[str]
```

## Three-Layer Prompt Architecture

```
Layer 0: base.md（所有角色共享）
  └─ 角色红线（边界/违规后果）
  └─ 协作协议（bus 通信规范）
  └─ wf 操作手册（通用 CLI）

Layer 1: roles/<name>.md（角色专业能力）
  └─ 身份定位、专长领域、方法论、红线、信号契约

Layer 2: mixins/<driver>.md（驱动模式）
  └─ loop_driver.md → 永不停止 + 退避重试
  └─ cron_driver.md → 检查→退出
  └─ ondemand_driver.md → 一次只做一件事
```

汇编顺序：`base.md → roles/<name>.md → mixins/<driver>.md`，由 `role_assembler.py` 执行。

## Consumed fields audit

| 字段 | 定义位置 | 消费方 | 状态 |
|------|----------|--------|------|
| name/title/category | persona JSON | launcher routing/roles.py | ✅ |
| system_prompt + prompt_refs | persona JSON | role_assembler 编译 → inject workspace | ✅ |
| constraints | persona JSON | gatekeeper 校验 + wake_permission | ✅ |
| lifecycle/drive | persona JSON | ccs.py start 消费（ondemand/infinite） | ✅ |
| output_targets | persona JSON | pipeline/router.py → produce 推导 | ✅ |
| input_signals | persona JSON | 仅 render_system_prompt，无代码消费 | ⚠️ 无运行时读取 |
| eval_criteria | persona JSON | 仅注入 CLAUDE.md，无运行时执行 | ⚠️ 无运行时执行 |
| skills + skill_refs | persona JSON | role_assembler 读 skill，未自动 /skill load | ⚠️ 无自动加载 |
| workgroup | persona JSON | 存在但无任何代码消费 | ❌ 完全未用 |
| cron_schedule | persona JSON | 无消费者（CronCreate 在 tmux 不可用） | ❌ 无消费者 |
| mcp_servers/tools | models.py 已定义 | launcher _write_mcp_settings() 消费 | ✅ |
| sla_seconds | models.py 已定义 | tracker 硬编码 300s | ⚠️ 未使用 |
| auto_send_messages | models.py 已定义 | core.py start 时自动发送 | ✅ |

## Cross-project interface: `shared_loader.py --export`

Pipeline 的路由数据来源是 `~/.hermes/data/roles_export.json`（由 `shared_loader.py --export` 生成），
**不是直接读 persona JSON**。这意味着修改角色 JSON 后必须运行 export 才能被 pipeline 感知。

```bash
cd ~/hermes-session-roles
python3 src/shared_loader.py --export        # 生成 roles_export.json
python3 src/validate_roles.py                # 全量验证
```

### Produce/Consume 解析逻辑（单一权威实现）

位于 `shared_loader.py`:

- `_parse_produce_categories()`: 从 `output_targets` 中提取 `bus cat=(\w+)` 匹配项
- `_parse_consume_categories()`: 从 `input_signals` 的新格式（`type: bus, spec: {category}`）和旧格式（`source` 字符串中 `bus cat=`）分别提取
- `consume_all`: `"*"` 在消费分类中表示通吃所有分类

下游 launcher 的 `routing/roles.py` 和 pipeline 的 `routing/router.py` 各有独立的 produce/consume 解析实现（对 `output_targets` 做正则提取）—— 这不是重复，但存在细微偏差风险。

## 已知问题

1. **测试缺失**: 仅 `tests/test_registry.py` 一个测试文件
2. **`_parse_produce/consume_categories` 三处实现**: shared_loader.py, launcher/routing/roles.py, pipeline/routing/router.py 各有自己的正则解析——风险是解析不一致
3. **字段缺口**: `workgroup`, `cron_schedule`, `sla_seconds` 等字段定义但下游未消费

## Red Lines

- **Zero dependency on session-launcher or session-pipeline**（最下层）
- No new dependencies (stdlib only)
- schema 只增不改（新字段可加，旧字段不能删）
- Verify: `python3 src/validate_roles.py` before commit
- prompt_refs 引用的文件必须存在（validator 强制）
- skills 非空数组（validator 强制）
- eval_criteria 每条必须是可执行 shell 命令或 "验证:" 开头的描述性标准
