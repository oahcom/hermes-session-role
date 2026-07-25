# Architecture — hermes-session-roles

## Purpose
Role registry for Hermes multi-session ecosystem. Defines professional identity, prompts, I/O signals, and eval criteria for 31 session roles + 57 browser-harness personas.

## File Layout
```
personas/
  browser-harness/               # 57 浏览器自动化人格
    persona_01_core.json         # 10 核心人格
    persona_02_specialized.json  # 25 专业人格
    persona_03_advanced.json     # 22 高级人格
    _bh_to_sr_map.json           # 浏览器人格 → Session 角色映射
    _bh_route_config.json        # 浏览器路由配置
    _ccs_injection_rules.json    # CCS 注入规则
    _ecosystem_health.json       # 生态健康检查
  session-roles/                 # 31 基础设施角色
    persona_00_maintainer.json   # 运维守护者
    persona_01_scout.json        # 侦察兵
    persona_03_curator.json      # 信息维护者
    persona_04_coordinator.json  # 管理者
    persona_05_engineer.json     # 开发工程师
    persona_06_closer.json       # 闭环者
    persona_08_optimizer.json    # 性能优化师
    persona_10_codex_dev.json    # Codex 开发者
    persona_11_ccs_monitor.json  # Session 监控者
    persona_12_debate_verifier.json  # 正方验证者
    persona_13_product_architect.json  # 产品架构师
    persona_14_knowledge_curator.json  # 知识策展人
    persona_15_security_auditor.json   # 安全审计员
    persona_16_pm.json           # 产品经理
    persona_17_reviewer.json     # 代码审查者
    persona_18_qa.json           # 测试工程师
    persona_19_devops.json       # 运维工程师
    persona_20_writer.json       # 技术写手
    persona_21_lr.json           # 技术负责人
    persona_22_pg.json           # 程序实现员
    persona_23_investigator_python.json  # 刑侦员 Python
    persona_24_investigator_senior.json   # 刑侦员 全栈
    persona_25_investigator_general.json  # 刑侦员 杂
    persona_99_archivist.json    # 档案管理员
    persona_99_ccs-coordinator.json  # CCS 生态协调员
    persona_99_consumer.json     # 消息消费器
    persona_99_public.json       # 公共接口
    persona_99_rebutter.json     # 反方辩手
    persona_99_regression_test_return.json  # 回归测试
    persona_99_research.json     # 研究员
    persona_99_test.json         # 测试角色
src/
  models.py            # PersonaDef + RoleDef + render_system_prompt
  shared_loader.py     # 统一角色加载器 + produce/consume 提取 + --export
  validate_roles.py    # 全量校验（32 文件 + prompt 质量检查）
  registry.py          # 注册表（load_all/get/list_*/register）
  search.py            # 中文语义搜索（bigram + 同义词 + 字段加权）
  role_assembler.py    # 动态组装 system prompt
  registry.py (role loading consolidated)    # 角色关系图谱（生产者→消费者矩阵）
  cli.py               # CLI: list/show/load/search
prompts/
  base.md              # Layer 0: 全体角色共享（红线、协作协议）
  roles/               # Layer 1: 各角色专业 prompt（23 个 .md 文件）
  mixins/              # Layer 2: 驱动模式（loop/cron/ondemand）
tests/
  test_search.py       # 搜索回归测试
docs/
  ARCHITECTURE.md      # 本文档
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
    prompt_refs: dict[str, str] = {}  # 模块化 prompt 引用
    skills: list[str] = []
    skill_refs: dict[str, str] = {}
    goal: str = ""
    constraints: list[str] = []
```

### RoleDef (extends PersonaDef)
```python
@dataclass
class RoleDef(PersonaDef):
    lifecycle: str        # "infinite" | "ondemand"
    drive: str            # "cron" | "loop" | "ondemand" | "goal"
    cron_schedule: str    # e.g. "*/15 * * * *"
    idle_action: str      # "exit" | "continue"
    input_signals: list   # [{"type": "...", "spec": {...}, "filter": "..."}]
    output_targets: list  # ["bus cat=code_fix 修复方案", ...]
    session_hint: str     # "cron" | "interactive" | "background"
```

## Three-Layer Prompt Architecture
```
Layer 0: base.md（所有角色共享）
  └─ 角色红线（边界/违规后果）
  └─ 协作协议（bus 通信规范）
  └─ wf 操作手册（通用 CLI）

Layer 1: roles/<name>.md（角色专业能力）
  └─ 身份定位、专长领域、方法论、红线、信号契约

Layer 2: mixins/<driver>.md（驱动模式）
  └─ loop_driver.md → 永不停止 + 退避重试
  └─ cron_driver.md → 检查→退出
  └─ ondemand_driver.md → 一次只做一件事
```

## Search Algorithm
1. **Tokenize** — Chinese bigram + single chars + English words
2. **Field-weighted score** — title(30) + description(30) + category(15) + name(10) + prompt(5)
3. **Coverage bonus** — +25 if all query chars appear in title+description
4. **Sort desc**, return top_k

No external deps — only `difflib.SequenceMatcher` from stdlib.

## CLI Interface
```bash
python3 src/cli.py list [--category CAT] [--roles]
python3 src/cli.py show <name>
python3 src/cli.py load <name> [--json] [--extra KEY=VAL]
python3 src/cli.py search "查询" [--top N]
```

## Validation
```bash
python3 src/validate_roles.py
# 预期: 文件数: 31, 角色数: 31, 错误数: 0
```

## Red Lines
- No new dependencies (stdlib only)
- schema 只增不改
- Edit on branch, not main
- Verify: `python3 src/validate_roles.py` before commit
