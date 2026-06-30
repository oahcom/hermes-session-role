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
python3 tests/test_search.py
# 9/9 passed

# Syntax check
python3 -m py_compile src/models.py src/search.py src/cli.py
# No output = OK
```

## CLI Commands

### List all personas/roles
```bash
python3 src/cli.py list                    # All 57 personas + 7 roles
python3 src/cli.py list --roles            # Only 7 session roles
python3 src/cli.py list --category 维护     # Filter by category
```

### Show details
```bash
python3 src/cli.py show maintainer         # Full JSON
python3 src/cli.py show scout
```

### Load system prompt (for session bootstrap)
```bash
python3 src/cli.py load maintainer         # Raw prompt
python3 src/cli.py load maintainer --json  # JSON with metadata
python3 src/cli.py load maintainer --extra key=val  # Template vars
```

### Semantic search
```bash
python3 src/cli.py search "修服务器"       # Top 5 matches
python3 src/cli.py search "清理" --top 3   # Top 3 matches
python3 src/cli.py search "写代码"
python3 src/cli.py search "翻译文档"
```

## Expected Search Results

| Query | Top Match | Reason |
|-------|-----------|--------|
| "修服务器" | maintainer | 运维守护者，守卫系统健康 |
| "清理" | curator | 信息维护者，清理过期 bus/memory |
| "写代码" | developer | 开发者，根据需求编写代码 |
| "翻译文档" | i18n-localizer | 国际化/本地化测试专家 |

## Adding a Role
```bash
# 1. Copy template
cp docs/ROLE_TEMPLATE.md personas/session-roles/persona_XX_newrole.json

# 2. Edit JSON
# 3. Validate
python3 src/cli.py show newrole

# 4. Test search
python3 src/cli.py search "相关查询"

# 5. Commit
git add personas/session-roles/persona_XX_newrole.json
git commit -m "feat: add newrole role (中文描述)"
```