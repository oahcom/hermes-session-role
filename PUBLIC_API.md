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

CLI 入口：`python3 src/role_assembler.py <role_name> [--output <path>] [--inject <claude.md path>]`。
动态组装角色 system prompt（Layer 0 base.md + Layer 1 roles/<name>.md + skill）。

## ValidateRoles (`validate_roles.py`)

CLI 入口（`main()`，argparse），用 `python3 src/validate_roles.py` 运行。无 `validate_all()`/`validate_role()` 两个 API 函数。

## SharedLoader (`shared_loader.py`)

| 函数 | 参数 | 返回 |
|------|------|------|
| `load_roles()` | — | `list[dict]` |
| `export_all()` | — | `list[dict]` |
| `export_role(role)` | `dict` | `RoleExport` |
| `write_export()` | — | `str` (输出路径) |

> 注：原 `cli.py`（list/show/load/search）与 `search.py`（中文语义搜索）已剪枝
> （零 runtime importer）。列表/校验用 `validate_roles.py --roles`；prompt
> 组装用 `role_assembler.py <role>`。

## Models (`models.py`)

定义了 `PersonaDef`, `RoleDef`, `render_prompt_from_refs` 等数据模型和工具函数。所有类型均为 `dataclass`。
