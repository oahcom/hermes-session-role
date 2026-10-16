# Quick Start

## Installation
```bash
git clone <repo> hermes-session-roles
cd hermes-session-roles
# No dependencies — stdlib only
```

## Verify
```bash
# All tests pass
python3 -m pytest tests/ -q
# 6 passed (registry 加载/查询 回归)

# Syntax check
python3 -m py_compile src/models.py src/registry.py src/role_assembler.py
# No output = OK
```

## CLI Commands

### List & validate personas/roles
```bash
python3 src/validate_roles.py --roles           # All 31 roles (JSON list)
python3 src/validate_roles.py --category 维护      # Filter by category
python3 src/validate_roles.py                    # Full validation (must be 0 errors)
```

### Load system prompt (for session bootstrap)
```bash
python3 src/role_assembler.py maintainer          # Raw system_prompt 文本
python3 src/role_assembler.py maintainer --output prompt.md   # 写入 prompt.md
python3 src/role_assembler.py maintainer --inject ccs-workspaces/maintainer/CLAUDE.md  # 注入 KNOWLEDGE 块
```

> ⚠️ `cli.py` (list/show/load/search) 与 `search.py` (semantic search) 已剪枝
> (零 runtime importer)。列表/校验用 `validate_roles.py`；prompt 用 `role_assembler.py`。
> 语义搜索能力暂未生效—详见 [SEARCH.md](SEARCH.md)（存档候选）。

## Adding a Role
```bash
# 1. Copy template
cp docs/ROLE_TEMPLATE.md personas/session-roles/persona_XX_newrole.json

# 2. Edit JSON
# 3. Validate
python3 src/validate_roles.py

# 4. Commit
git add personas/session-roles/persona_XX_newrole.json
git commit -m "feat: add newrole role (中文描述)"
```
