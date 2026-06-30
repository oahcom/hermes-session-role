# Hermes Session Roles

Role registry for the Hermes Agent multi-session ecosystem. Defines the professional identity of every session: who they are, why they exist, how they work, what they produce, and who consumes their output.

Merges Browser Harness persona system (290+ expert personas) with Hermes infrastructure roles (operations / reconnaissance / consumption / curation / management / development / closure).

---

## Architecture Overview

```
hermes-session-roles/
├── personas/
│   ├── browser-harness/      → Browser automation expert personas (outward, web-facing)
│   │   ├── persona_01_core.json
│   │   ├── persona_02_specialized.json
│   │   └── persona_03_advanced.json
│   └── session-roles/        → Infrastructure roles (inward, system-facing)
│       ├── persona_00_maintainer.json
│       ├── persona_01_scout.json
│       ├── persona_02_consumer.json
│       ├── persona_03_curator.json
│       ├── persona_04_coordinator.json
│       ├── persona_05_developer.json
│       └── persona_06_closer.json
├── src/
│   ├── models.py              → PersonaDef, RoleDef
│   ├── search.py              → Semantic search (reused from Browser Harness)
│   └── cli.py                 → persona list/show/load/search
└── tests/
    └── test_search.py
```

### Component Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                        Session Runtime                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│   │  DKK Daemon  │     │  SSK Daemon  │     │ Cron Worker  │   │
│   └──────┬───────┘     └──────┬───────┘     └──────┬───────┘   │
│          │                    │                    │             │
│          └────────────────────┼────────────────────┘             │
│                               ▼                                  │
│                    ┌────────────────────┐                        │
│                    │  Sister Bus (SQLite)│◄──┐                   │
│                    │  Blackboard FTS5    │   │                   │
│                    └─────────┬──────────┘   │                   │
│                              │              │                   │
│          ┌───────────────────┼───────────────┘                   │
│          ▼                   ▼                                   │
│   ┌──────────────┐     ┌──────────────┐                         │
│   │  RoleDef     │     │  PersonaDef  │                         │
│   │  (7 roles)   │     │  (290+ personas)│                       │
│   │  lifecycle   │     │  config_overrides│                      │
│   │  drive       │     │  eval_criteria │                        │
│   │  input_signals│    └──────────────┘                         │
│   │  output_targets                          │                   │
│   └──────────────┘                            │                  │
│          │                                    │                  │
│          ▼                                    ▼                  │
│   ┌─────────────────────────────────────────────────┐           │
│   │              src/models.py (registry)            │           │
│   │  load_all() → register() → list_roles/list_personas│          │
│   └─────────────────────────────────────────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Usage

### Direct CLI (no install needed)

```bash
# List all session roles
python3 src/cli.py list --roles

# List all personas by category
python3 src/cli.py list --category 安全

# Show full details for a role
python3 src/cli.py show maintainer

# Semantic search by task description
python3 src/cli.py search "修服务器"
python3 src/cli.py search "清理"

# Load system prompt (for injection into another session)
python3 src/cli.py load maintainer --json
```

### Integration

Import in Python:

```python
from src.models import load_all, get, list_roles, list_personas

load_all()  # Loads all JSON files from personas/
role = get("maintainer")
print(role.render_system_prompt())
```

---

## Core Concepts

### PersonaDef (Base)

Inherited from Browser Harness. Defines a reusable expert personality.

| Field | Type | Purpose |
|-------|------|---------|
| `name` | str | Unique identifier |
| `title` | str | Display title |
| `description` | str | One-line purpose |
| `category` | str | Group for filtering |
| `system_prompt` | str | LLM system prompt with `{persona_name}`, `{persona_title}` placeholders |
| `config_overrides` | dict | Runtime config (e.g., `json_output`, `daemon_mode`) |
| `eval_criteria` | list[str] | Verification criteria for quality control |

### RoleDef (Extended)

Extends `PersonaDef` with session lifecycle control fields.

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `lifecycle` | str | `"infinite"` | `infinite` (cron/loop) or `ondemand` (interactive) |
| `drive` | str | `"cron"` | `cron` \| `loop` \| `ondemand` |
| `cron_schedule` | str | `""` | Cron expression when `drive="cron"` |
| `idle_action` | str | `"exit"` | Behavior when no work: `exit` \| `continue` \| `wait` |
| `input_signals` | list[dict] | `[]` | Signal sources with filters (who produces input) |
| `output_targets` | list[str] | `[]` | Output destinations (who consumes output) |
| `session_hint` | str | `"cron"` | `cron` \| `interactive` \| `background` for session type hint |

---

## Session Role Matrix

| Role | Title | Category | Lifecycle | Drive | Schedule | Purpose |
|------|-------|----------|-----------|-------|----------|---------|
| `maintainer` | 运维者 | 维护 | infinite | cron | `*/15 * * * *` | Service health, auto-repair, alerting |
| `scout` | 侦察兵 | 信息采集 | infinite | loop | — | GitHub/tech community reconnaissance |
| `consumer` | 信息消费者 | 处理 | infinite | cron | `*/30 * * * *` | Validate, dedupe, persist bus output |
| `curator` | 信息维护者 | 维护 | infinite | cron | `0 * * * *` | Cleanup bus/memory/worktree entropy |
| `coordinator` | 管理者 | 管理 | infinite | loop | — | Ecosystem monitoring, bottleneck detection |
| `developer` | 开发者 | 生产 | ondemand | ondemand | — | Code implementation from signals |
| `closer` | 闭环者 | 管理 | ondemand | ondemand | — | Close stale bus/staged/processes |

---

## Signal Flow Summary

```
GitHub / Tech Community
         │
         ▼
    ┌─────────┐
    │  scout  │ ──► bus cat=architecture (new findings)
    └────┬────┘       │      bus cat=evolution_report (scan reports)
         │            │
         ▼            ▼
    ┌─────────┐  ┌─────────┐
    │coordinator│  │ consumer│ ◄─── validates & persists
    └────┬────┘  └────┬────┘
         │            │
         ▼            ▼
    ┌─────────┐  ┌─────────┐
    │ developer│  │curator  │ ◄─── cleanup entropy
    └────┬────┘  └────┬────┘
         │            │
         ▼            ▼
    ┌─────────┐  ┌─────────┐
    │maintainer│  │ closer  │ ◄─── close loops
    └────┬────┘  └────┬────┘
         │            │
         ▼            ▼
      Services    bus/architecture
      healthy      clean state
```

---

## Files of Interest

| Path | Description |
|------|-------------|
| `personas/session-roles/` | 7 infrastructure role definitions |
| `personas/browser-harness/` | 290+ browser automation personas |
| `src/models.py` | `PersonaDef`, `RoleDef`, registry (`load_all`, `get`, `list_roles`, `list_personas`) |
| `src/search.py` | Semantic search with Chinese tokenization + synonym expansion |
| `src/cli.py` | CLI: `list`, `show`, `load`, `search` |
| `tests/test_search.py` | Self-check tests for search quality |