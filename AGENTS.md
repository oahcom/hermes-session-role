# Hermes Session Roles

Registers career identities for Claude Code sessions -- 7 session roles and 57 browser-automation personas. Each definition declares who the session is, what it produces, and which signals drive it.

## File Tree

```
session-roles/
  personas/
    browser-harness/            57 browser-automation personas
      persona_01_core.json
      persona_02_specialized.json
      persona_03_advanced.json
    session-roles/              7 infrastructure roles
      persona_00_maintainer.json
      persona_01_scout.json
      persona_02_consumer.json
      persona_03_curator.json
      persona_04_coordinator.json
      persona_05_developer.json
      persona_06_closer.json
  src/
    models.py                   PersonaDef, RoleDef, register/get/load_all
    search.py                   keyword + synonym semantic search (stdlib only)
    cli.py                      CLI entry point (4 subcommands below)
  tests/
    test_search.py
```

## CLI Commands

All commands load definitions first, then operate on them.

```
python src/cli.py list [--roles] [--category CAT]
python src/cli.py show <name>
python src/cli.py load <name> [--json] [--extra key=val ...]
python src/cli.py search <query> [--top N]
```

| Command  | Purpose                                                      |
|----------|--------------------------------------------------------------|
| `list`   | List personas grouped by category, or `--roles` for the 7 roles only |
| `show`   | Dump full JSON of a persona or role                          |
| `load`   | Render system prompt (with optional template vars)           |
| `search` | Semantic search across all definitions (top-5 default)       |

## Quick Reference

Common search queries:

```bash
python src/cli.py search "修服务器"          # maintainer role
python src/cli.py search "安全审计"           # security personas
python src/cli.py search "数据采集 爬虫"      # data-collection personas
python src/cli.py search "自动化部署"         # automation personas
```

Adding a new role -- add entry to `personas/session-roles/persona_NN_name.json` with these required fields:

```json
{
  "name": "string",
  "title": "string",
  "description": "string",
  "category": "string",
  "system_prompt": "string",
  "lifecycle": "infinite|ondemand",
  "drive": "cron|loop|ondemand",
  "input_signals": [],
  "output_targets": []
}
```

## Red Lines

1. Never edit on `main`/`quality-gate` directly. All edits go on a worktree branch.
2. Commit format: `feat/fix/chore: short description in English` -- keep it under 72 chars.
3. Verify before marking done: `git diff --name-only`, `python -m py_compile` on every changed `.py` file, `python -m pytest` if tests exist.
4. Zero external dependencies. Search uses only stdlib (`difflib` / `re`). Do not add pip packages.
