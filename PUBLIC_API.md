# PUBLIC_API — hermes-session-roles

## Public API

> **位置**: `~/hermes-session-roles/src/`

## Direction

session-pipeline → session-launcher → **hermes-session-roles** (最底层，不引用另外两项目)

零违反：本层不引用 session-launcher 或 session-pipeline。

## Dependencies

hermes-session-roles **不引用** session-launcher 或 session-pipeline。零违反。

## Registry (`registry.py`)

| 函数 | 参数 | 返回 |
|------|------|------|
| `register(obj)` | `PersonaDef \| RoleDef` | `None` |
| `get(name)` | `str` | `Optional[PersonaDef \| RoleDef]` |
| `list_roles()` | — | `list[RoleDef]` |
| `list_personas(category)` | `Optional[str]` | `list[PersonaDef]` |
| `list_categories()` | — | `dict[str, int]` |
| `load_all(base_dir)` | `Optional[str]` | `int` (loaded count) |

## RoleAssembler (`role_assembler.py`)

| 函数 | 参数 | 返回 |
|------|------|------|
| `assemble_role_prompt(role_name)` | `str` | `str` (assembled prompt text) |
| `load_role_json(role_name)` | `str` | `dict[str, Any]` (delegates to registry.get) |

## ValidateRoles (`validate_roles.py`)

| 函数 | 参数 | 返回 |
|------|------|------|
| `validate_all()` | — | `list[str]` (错误列表, 空=通过) |
| `validate_role(role_name)` | `str` | `list[str]` |

## Search (`search.py`)

| 函数 | 参数 | 返回 |
|------|------|------|
| `search(query, top_k)` | `str, int` | `list[dict]` |

## SharedLoader (`shared_loader.py`)

| 函数 | 参数 | 返回 |
|------|------|------|
| `load_roles(roles_dir)` | `Optional[Path \| str]` | `list[dict]` |
| `load_role(name)` | `str` | `Optional[dict]` |
| `export_all()` | — | `list[dict]` |
| `export_role(role)` | `dict` | `RoleExport` |
| `write_export()` | — | `str` (输出路径) |

## CLI (`cli.py`)

| 命令 | 功能 |
|------|------|
| `list` | 列出所有角色 |
| `info <role>` | 查角色详情 |
| `validate [role]` | 校验角色 |
| `search <query>` | 语义搜索 |

## Models (`models.py`)

定义了 `PersonaDef`, `RoleDef`, `render_prompt_from_refs` 等数据模型和工具函数。所有类型均为 `dataclass`。
