# Session Roles（角色定义层）

## 定位

Session 生态的**定义层**——每个 CCS（Claude Code Session）是谁、做什么、怎么协作，纯 JSON 声明。

**核心职责：定义每个角色长什么样（装什么知识、听什么信号、产什么东西），让 session-launcher 知道怎么把角色启动起来，让 session-pipeline 知道消息该送给谁。**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Hermes Session Ecosystem                          │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  hermes-session-roles  ← 本项目（定义层）                     │      │
│  │                                                               │      │
│  │  personas/session-roles/*.json    → 31 基础设施角色            │      │
│  │  personas/browser-harness/*.json  → 57 浏览器自动化人格        │      │
│  │  prompts/roles/*.md               → 角色专业 prompt 模板       │      │
│  │                                                               │      │
│  │  src/cli.py          → list/show/load/search CLI              │      │
│  │  src/search.py       → 中文语义搜索引擎                        │      │
│  │  src/validate_roles.py → 31 角色全量校验                       │      │
│  │  src/role_assembler.py → 动态组装 system prompt                │      │
│  └──────────────────────────┬───────────────────────────────────┘      │
│                              │                                          │
│              ┌───────────────┴───────────────┐                         │
│              ▼                               ▼                         │
│  ┌──────────────────────┐       ┌──────────────────────────────────┐   │
│  │ session-launcher     │       │ session-pipeline                 │   │
│  │ 执行层（tmux/CCS）   │       │ 路由层（消息分发/优先级）         │   │
│  └──────────────────────┘       └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 方法论蒸馏（核心设计哲学）

AI 不是全能的。把所有人的工作塞进一个上下文，AI 什么都干不好。单 agent 多角色意味着每个角色分到的 prompt 只有 1/N——被稀释成通用水平。

**三个项目存在的唯一目的：让人从多 agent 协作中逐步退出。**

```
多 agent 并行 = 每个 agent 拥有独立的完整上下文
              = 每个角色的提示词可以蒸馏到顶级水平
              = 不用在切换角色时丢失思维状态
```

### prompt 蒸馏检查清单

| 问题 | 如果答案是"否" |
|------|---------------|
| system_prompt 是否包含 L0-L3 全部四层知识？ | 缺少某一层意味着角色缺少对应维度的判断力 |
| CLAUDE.md 里是否有其他角色的指令？ | 上下文不纯，专业度被稀释 |
| 一个新人读完 prompt 能立刻按独特标准工作？ | 说明只是通用知识，不是方法论蒸馏 |
| 每条规则是不是真人踩坑后才写出来的？ | 如果是网上找的 checklist，就是通用知识 |

---

## 项目结构

```
personas/
  session-roles/               # 25 个基础设施角色（JSON)
    persona_00_maintainer.json
    persona_01_scout.json
    persona_02_consumer.json
    persona_03_curator.json
    ...
  browser-harness/             # 57 个浏览器自动化人格
    persona_01_core.json       # 10 核心人格
    persona_02_specialized.json # 25 专业人格
    persona_03_advanced.json   # 22 高级人格
    _bh_to_sr_map.json         # 浏览器人格 → Session 角色映射

prompts/
  roles/                       # 角色专业 prompt 模板 (.md)
  skills/                      # 技能库模板

src/
  cli.py                  → CLI 入口（list/show/load/search）
  models.py               → PersonaDef + RoleDef dataclass
  registry.py             → load_all/get/list_*/register 注册表
  search.py               → 中文语义搜索（bigram + 同义词 + 字段加权）
  validate_roles.py       → 31 角色全量校验
  role_assembler.py       → 动态组装 system prompt
  # role_relations.py     → [已删除] 角色关系图谱（迁移至 Router API）
  inject_skills.py        → 技能注入工具
  create_skill_library.py → 技能库创建工具
tests/
  test_search.py          → 15 个搜索回归测试
```

---

## 角色清单```

---

## 角色清单（23 编号角色 + 8 非编号角色）

| 角色 | 标题 | 生命周期 | 驱动 | 产出分类 | 消费分类 |
|------|------|----------|------|----------|----------|
| maintainer | 运维者 | infinite | cron (15m) | code_fix, architecture | security |
| scout | 侦察兵 | infinite | loop | architecture, evolution_report | architecture |
| consumer | 信息消费者 | ondemand | ondemand | reflexion_lesson | * |
| curator | 信息维护者 | infinite | cron (hourly) | skill_audit, cleanup, architecture | skill_audit, architecture, code_fix, performance |
| coordinator | 管理者 | infinite | loop | scheduler, architecture, ccs_health | task_spec, workflow, user_story, test_plan, deployment_plan, deployment_report, test_report, bug_report, security_audit, evolution_report, changelog, ccs_health |
| engineer | 开发工程师 | ondemand | ondemand | code_fix, code_review, architecture | architecture, task_spec, user_story, code_review, bug_report, test_report, test_plan, documentation, security_audit, system_design |
| closer | 闭环者 | ondemand | ondemand | architecture | *, knowledge_distill, memory_store, system_design |
| optimizer | 性能优化师 | infinite | cron | architecture, optimization | architecture, performance, bug_report, code_review |
| codex-dev | Codex 开发者 | infinite | goal | code_review, code_fix | code_fix, architecture, optimization |
| ccs-monitor | Session 监控者 | infinite | loop | architecture, notice | architecture, notice, blocker, code_fix |
| debate_verifier | 正方验证者 | infinite | loop | debate, verification | debate, task_spec |
| product_architect | 产品架构师 | ondemand | ondemand | prd, system_design, task_spec | architecture, code_fix, product_design, blocker, design_issue, threat_model, security_audit |
| knowledge_curator | 知识策展人 | infinite | cron | architecture, code_fix, cleanup, knowledge_distill, memory_store | *, session_log |
| security_auditor | 安全审计员 | ondemand | ondemand | security_audit, code_fix, architecture | security, blocker, code_fix, threat_model, deployment_plan |
| pm | 产品经理 | ondemand | ondemand | user_story, feedback | prd, architecture, test_report, deployment_report, feedback, bug_report, documentation |
| reviewer | 代码审查者 | ondemand | ondemand | code_review, architecture | code_review, architecture, security |
| qa | 测试工程师 | ondemand | ondemand | test_plan, test_report, bug_report | task_spec, code_fix, prd, test_plan, bug_report |
| devops | 运维工程师 | ondemand | ondemand | deployment_plan, deployment_report, monitor_dashboard | architecture, code_fix, security, test_report, threat_model, deployment_plan, documentation |
| writer | 技术写手 | ondemand | ondemand | documentation, changelog | code_fix, architecture, deployment_plan, deployment_report, documentation |
| lr | 技术负责人 | ondemand | ondemand | tech_decision, architecture | task_spec, architecture, root_cause_analysis |
| pg | 程序实现员 | ondemand | ondemand | code_fix, code_review | task_spec, tech_decision, root_cause_analysis, bug_report, system_design, verification |
| investigator_python | 刑侦员 (Python) | ondemand | ondemand | root_cause_analysis | code_fix, architecture |
| investigator_senior | 刑侦员 (全栈) | ondemand | ondemand | root_cause_analysis | * |
| investigator_general | 刑侦员 (杂) | ondemand | ondemand | root_cause_analysis | * |
| archivist | 档案管理员 | ondemand | ondemand | architecture | reflexion_lesson, cleanup |

> 2026 年 7 月统计：31 角色全部定义完整，验证通过零错误。

---

## Browser Harness 集成

Browser Harness 是一个独立的浏览器自动化人格库，包含 57 个人格，按三个层级组织：

| 层级 | 文件 | 人格数 | 涵盖领域 |
|------|------|--------|----------|
| Core | `persona_01_core.json` | 10 | 安全审计、数据采集、UI 测试、登录表单等 |
| Specialized | `persona_02_specialized.json` | 25 | 爬虫、监控、OCR、支付、社交媒体等 |
| Advanced | `persona_03_advanced.json` | 22 | 复杂工作流引擎、反检测、多步骤操作等 |

### 人格 JSON 格式

```json
{
  "name": "security-auditor",
  "title": "安全审计师",
  "description": "OWASP Top 10 安全审计",
  "category": "安全",
  "system_prompt": "...",
  "config_overrides": {},
  "eval_criteria": []
}
```

### 与 Session 角色的关联

映射文件 `_bh_to_sr_map.json` 将 Browser Harness 人格桥接到 Session 角色：

```json
{
  "security-auditor": "security_auditor",
  "data-collector": "scout",
  "ui-tester": "qa"
}
```

这使得 Browser Harness 的浏览器自动化能力可以被 Session 角色消费——例如 security_auditor 可以调用 browser-harness 的安全审计人格执行自动化扫描。

---

## CLI 接口

```bash
# 列出角色
python3 src/cli.py list --roles                    # 全部 31 角色
python3 src/cli.py list --category 维护            # 按分类筛选

# 显示详情
python3 src/cli.py show maintainer                 # JSON 完整定义

# 加载 system prompt
python3 src/cli.py load maintainer                 # 纯文本
python3 src/cli.py load maintainer --json           # JSON 格式
python3 src/cli.py load maintainer --extra KEY=VAL  # 注入变量

# 语义搜索
python3 src/cli.py search "修服务器" --top 5
python3 src/cli.py search "写代码" --top 3
python3 src/cli.py search "监控报警" --top 3

# 角色组装（动态 prompt）
python3 src/role_assembler.py maintainer --output prompt.md
```

---

## 验证

```bash
# 全量角色校验
python3 src/validate_roles.py
# 输出: 文件数: 31, 角色数: 31, 错误数: 0, 所有角色验证通过

# 语义搜索回归（15 场景）
python3 tests/test_search.py
# 输出: 结果: 15/15 通过

# 快速冒烟
python3 src/cli.py list --roles
python3 src/cli.py show maintainer | python3 -m json.tool > /dev/null
python3 src/cli.py search "性能" --top 3
```

### 新增角色验证清单

- [ ] `python3 src/cli.py show <name>` 不报错
- [ ] `python3 tests/test_search.py` 全通过
- [ ] `eval_criteria` 每条能在 shell 里跑通
- [ ] `system_prompt` 无协作逻辑（无 watchdog/turn_tracker/重启等词）
- [ ] `drive=cron` 时有 `cron_schedule`
- [ ] `input_signals` 的 `source` 可直接在 shell 执行
- [ ] `output_targets` 格式 `bus cat=<分类> <描述>`
- [ ] 文件命名 `persona_XX_name.json`，XX 两位数序号
- [ ] `## 参考来源` 章节在 prompts 文件中有外部 URL
- [ ] `prompt_refs` 包含 base + role + driver 三层
- [ ] `skills` 非空数组
- [ ] `skill_refs` 覆盖全部 skills 且文件存在

---

## Prompt 规范

AGENTS.md 包含完整的三层 prompt 架构规范（2026-07-15 版），涵盖：

- 三层架构（base.md → roles/*.md → mixins/*.md）及各层内容边界
- 各类指令的正确归属表（"永不停止"在哪、"自审查"在哪）
- 角色 prompt 文件的结构标准
- eval_criteria 规范
- 常见问题自查表

**修改 prompt 前必须阅读 `AGENTS.md` 的 Prompt 规范章节。**

---

## 信号契约

### input_signals（消费端）

```json
{
  "type": "bus",
  "spec": {"category": "security"},
  "filter": "security_items"
}
```

新格式 = `{type, spec, filter, schedule, timeout_sec}`  
旧格式 = `{source, filter}`（自动转换 + DeprecationWarning）

### output_targets（产出端）

```json
["bus cat=code_fix 修复方案", "bus cat=architecture 架构异常"]
```

会被 session-pipeline 自动解析为路由表。

### eval_criteria

每条标准是可执行 shell 命令，返回码 0 = 通过：

```json
"eval_criteria": [
  "systemctl --user is-active sister-agent-dkk.service && echo OK",
  "curl -sf -o /dev/null http://localhost:8890 && echo OK"
]
```

---

## 依赖

- Python 3.10+ stdlib only
- 无第三方依赖
- 与 session-launcher 协作：提供角色定义 JSON
- 与 session-pipeline 协作：提供 produce/consume 映射

## 参考文档

| 文档 | 位置 | 说明 |
|------|------|------|
| 生态架构全景 | `session-launcher/HERMES_SESSION_ARCHITECTURE.md` | 三项目整体架构 + 角色社会隐喻 |
| 健康检查 | `session-launcher/src/ecosystem_health.py` | 跨三项目统一健康检查 |
| 角色关系图谱 | ~~`src/role_relations.py`~~ (已删除) → Router API | 生产者→消费者数据流矩阵 (动态推导) |
