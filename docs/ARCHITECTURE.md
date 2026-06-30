# Architecture — hermes-session-roles

## Purpose
Role registry for Hermes multi-session ecosystem. Defines professional identity, prompts, I/O signals, and eval criteria for 7 infrastructure roles + 57 browser-harness personas.

## File Layout
```
personas/
  browser-harness/
    persona_01_core.json        # 29 core personas
    persona_02_specialized.json # 14 specialized personas  
    persona_03_advanced.json    # 14 advanced personas
  session-roles/
    persona_00_maintainer.json  # 运维守护者
    persona_01_scout.json       # 侦察兵
    persona_02_consumer.json    # 信息消费者
    persona_03_curator.json     # 信息维护者
    persona_04_coordinator.json # 管理者
    persona_05_developer.json   # 开发者
    persona_06_closer.json      # 闭环者
src/
  models.py        # PersonaDef + RoleDef + registry (load_all, get, list_*)
  search.py        # 中文语义搜索（bigram + 字段加权）
  cli.py           # CLI: list/show/load/search
tests/
  test_search.py   # 搜索回归测试
docs/
  ARCHITECTURE.md  # 本文档
```

## Data Model

### PersonaDef (browser-harness compatible)
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
```

### RoleDef (extends PersonaDef)
```python
@dataclass
class RoleDef(PersonaDef):
    lifecycle: str        # "infinite" | "ondemand"
    drive: str            # "cron" | "loop" | "ondemand"
    cron_schedule: str    # e.g. "*/15 * * * *"
    idle_action: str      # "exit" | "继续下一轮扫描"
    input_signals: list   # [{"source": "...", "filter": "..."}]
    output_targets: list  # ["bus cat=code_fix 修复方案", ...]
    session_hint: str     # "cron" | "interactive" | "background"
```

## Search Algorithm
1. **Tokenize** — Chinese bigram + single chars + English words
2. **Field-weighted score** — title(30) + description(30) + category(15) + name(10) + prompt(5)
3. **Coverage bonus** — +25 if all query chars appear in title+description
4. **Sort desc**, return top_k

No external deps — only `difflib.SequenceMatcher` from stdlib.

## Signal Flow (7 Roles)
| Role | Drive | Input | Output |
|------|-------|-------|--------|
| maintainer | cron (15m) | systemctl, curl, journalctl, bus security | bus cat=code_fix/architecture |
| scout | loop | GitHub Trending, HN, arXiv, bus architecture needs_research | bus cat=architecture/evolution_report |
| consumer | cron (30m) | bus unread --all | bus consume, bus cat=reflexion_lesson |
| curator | cron (hourly) | bus stats>200, memory>7d, worktree>1d | bus cat=architecture |
| coordinator | loop | bus stats, systemctl timers, git staged, session files | bus cat=architecture |
| developer | ondemand | user directive, bus architecture needs_impl, bus code_fix needs_patch | git commit, bus cat=code_fix |
| closer | ondemand | bus >24h unread, staged>24h, python>2h stuck | bus consume, git commit/stash, bus cat=architecture |

## CLI Interface
```bash
# List all
python3 src/cli.py list [--category CAT] [--roles]

# Show details
python3 src/cli.py show <name>

# Load system prompt (for session bootstrap)
python3 src/cli.py load <name> [--json] [--extra KEY=VAL]

# Semantic search
python3 src/cli.py search "查询" [--top N]
```

## Adding a Role
1. Create `personas/session-roles/persona_XX_name.json`
2. Use RoleDef fields (see existing JSONs)
3. `python3 src/cli.py show <name>` — validates JSON
4. `git commit -m "feat: add <role> role"` — commit

## Red Lines
- No new dependencies (stdlib only)
- Edit on branch, not main
- Commit: `feat/fix/refactor: 中文描述`
- Verify: `python3 src/cli.py show <name>` before commit
- Tests: `python3 tests/test_search.py` (9/9 must pass)