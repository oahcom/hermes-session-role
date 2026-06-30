# Quick Start

Zero dependencies. Python 3.10+ stdlib only.

---

## Prerequisites

- Python 3.10+
- Git (optional, for repository operations)

No `pip install` needed. No virtual environment setup. Just clone and run.

---

## Clone

```bash
git clone <repo-url> hermes-session-roles
cd hermes-session-roles
```

---

## List All Personas

```bash
python3 src/cli.py list
```

Output:

```
共 7 个人格/角色，分 4 个分类:
  信息采集: 1
  处理: 1
  管理: 2
  维护: 2
  生产: 1

  maintainer                        运维者          守卫系统健康，监控服务状态，故障自愈
  scout                             侦察兵          扫描 GitHub、技术社区，发现新工具、模式、情报
  consumer                          信息消费者       验证、归纳、去重、沉淀其他角色的 bus 产出
  curator                           信息维护者       清理过期 bus/memory/datasets，去重，压缩，对抗熵增
  coordinator                       管理者          监控多 session 生态状态，发现瓶颈，调度资源
  developer                         开发者          根据需求/architecture/code_fix 信号编写代码
  closer                            闭环者          追踪未完成的 bus/staged/卡住进程，推动 done
```

---

## List Session Roles Only

```bash
python3 src/cli.py list --roles
```

Filters out standalone personas; shows only the 7 session roles that have lifecycle/input/output definitions.

---

## Show Role Details

```bash
python3 src/cli.py show maintainer
```

Prints the full JSON definition including `system_prompt`, `input_signals`, `output_targets`, `eval_criteria`, and all metadata fields.

---

## Semantic Search

Search by natural language task description:

```bash
python3 src/cli.py search "修服务器"
python3 src/cli.py search "清理"
python3 src/cli.py search "写代码"
python3 src/cli.py search "监控"
python3 src/cli.py search "deploy"
```

Search uses Chinese character tokenization (unigram + bigram) with synonym expansion. No external search library required.

### How Ranking Works

1. Tokenize query into Chinese unigrams/bigrams and English words
2. Expand tokens via synonym table (e.g., "修" expands to "修复", "维护", "运维", "诊断", ...)
3. Score each persona across weighted fields (title: 30, description: 30, category: 15, name: 10, prompt: 5)
4. Bonus for full character coverage of query in persona fields (+25)
5. Bonus for ordered character match (+0-20)

---

## Load System Prompt

Get the rendered system prompt for a role (with placeholders filled):

```bash
# Plain text output
python3 src/cli.py load maintainer

# JSON output (for programmatic use)
python3 src/cli.py load maintainer --json
```

JSON output format:

```json
{
  "persona": "maintainer",
  "title": "运维者",
  "system_prompt": "你是 运维者 (maintainer)，Hermes Agent 生态的运维守护者...",
  "config_overrides": {},
  "eval_criteria": ["所有核心服务 active | 验证: ...", "..."]
}
```

### Pass Extra Context Variables

```bash
python3 src/cli.py load maintainer -e target_service=sister-agent-dkk
```

This sets `{target_service}` in the system prompt template.

---

## Run Tests

```bash
python3 tests/test_search.py
```

Self-check mode runs 9 assertions verifying search quality:

| Test | Description |
|------|-------------|
| "修服务器" | `maintainer` ranks first, score > 30 |
| "清理" | `curator` in top 3 |
| "写代码" | `developer` ranks first |
| "监控" | `coordinator` in top 3 |
| "deploy" | English query does not crash |
| (empty) | Empty input returns `[]` |
| "!@#$%^" | Noise input does not crash |
| "运维" | Synonym matches `maintainer` |
| "修复服务" | Multi-keyword matches `maintainer` first |