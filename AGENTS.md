# Hermes Session Roles 项目

## 项目概述

多 session Claude Code 生态的职业身份注册表。定义每个 session 的"我是谁、我为什么存在、我怎么工作、我产出什么、谁消费我的产出"。

融合 Browser Harness 人格系统（290+ 个专家人格）和 Hermes 基础设施角色（运维/侦察/消费/维护/管理/开发/闭环）。

## 架构

```
session-roles/
  personas/
    browser-harness/      → 浏览器自动化专家人格（外倾，面向网络）
      persona_01_core.json
      persona_02_specialized.json
      persona_03_advanced.json
    session-roles/         → 基础设施角色（内倾，面向系统）
      persona_00_maintainer.json
      persona_01_scout.json
      persona_02_consumer.json
      persona_03_curator.json
      persona_04_coordinator.json
      persona_05_developer.json
      persona_06_closer.json
  src/
    models.py              → PersonaDef, RoleDef
    registry.py            → load_all, get, list
    search.py              → 语义搜索（复用 Browser Harness）
    cli.py                 → persona list/show/load/search
```

## 关键决策

- 复用 Browser Harness 的 `PersonaDef` 结构（name/title/description/category/system_prompt/config_overrides/eval_criteria）
- 扩展 `lifecycle` + `input_signals` + `output_targets` 供 session 启动控制
- JSON 文件持久化，无需 DB
- 语义搜索用 stdlib 的 difflib，零外部依赖

## 文件操作规范

- 不要在 main 分支直接编辑
- 所有编辑在 worktree 分支进行
- 提交信息格式：`feat/fix/chore: 做了什么（中文）`

## 关键路径

| 路径 | 说明 |
|------|------|
| `personas/browser-harness/` | Browser Harness 的 50 个浏览器自动化人格 |
| `personas/session-roles/` | 基础设施 7 个角色 |
| `src/` | Python 注册表引擎 |
| `AGENTS.md` | 本文件 |
