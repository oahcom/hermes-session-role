# PUBLIC_API — hermes-session-roles

## Public API

> **位置**: `~/hermes-session-roles/src/`

## Direction

session-pipeline → session-launcher → **hermes-session-roles** (最底层，不引用另外两项目)

零违反：本层不引用 session-launcher 或 session-pipeline。

## Dependencies

hermes-session-roles **不引用** session-launcher 或 session-pipeline。零违反。

## RoleAssembler (`role_assembler.py`)

| 函数 | 参数 | 返回 |
|------|------|------|
| `assemble_role(role_name)` | str | `dict` (system_prompt + skills + signals) |
| `list_roles()` | — | `list[str]` |

## Registry (`registry.py`)

| 函数 | 参数 | 返回 |
|------|------|------|
| `register_role(role_name, config)` | str, dict | `bool` |
| `get_role(role_name)` | str | `Optional[dict]` |
| `deregister_role(role_name)` | str | `bool` |
| `list_all_roles()` | — | `list[dict]` |

## RoleRelations (`role_relations.py`)

| 函数 | 参数 | 返回 |
|------|------|------|
| `get_relations(role_name)` | str | `list[dict]` |
| `get_downstream(role_name)` | str | `list[str]` |

## ValidateRoles (`validate_roles.py`)

| 函数 | 参数 | 返回 |
|------|------|------|
| `validate_all()` | — | `list[str]` (错误列表, 空=通过) |
| `validate_role(role_name)` | str | `list[str]` |

## Search (`search.py`)

| 函数 | 参数 | 返回 |
|------|------|------|
| `search_roles(query)` | str | `list[dict]` |
| `search_skills(query)` | str | `list[dict]` |

## CLI (`cli.py`)

| 命令 | 功能 |
|------|------|
| `list` | 列出所有角色 |
| `info <role>` | 查角色详情 |
| `validate [role]` | 校验角色 |

## Models (`models.py`)

定义了 `RoleConfig`, `SkillDefinition`, `SignalMapping` 等数据模型。所有类型均为 `dataclass`。
