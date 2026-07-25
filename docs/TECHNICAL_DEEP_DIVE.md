# Hermes Session Roles — Technical Deep Dive

## 1. 项目定位

Session 生态的**定义层**。所有 CCS（Claude Code Session）的角色身份在这里注册。不启动进程、不路由消息——只定义"谁是谁、该做什么、怎么协作"。

```
session-roles (定义层) → session-launcher (执行层) → session-pipeline (路由层)
```

## 2. 核心数据模型

`models.py` 定义两个 dataclass：

### PersonaDef
- name, title, description, category
- system_prompt: 角色系统提示词（最长字段）
- config_overrides: 运行时参数重载
- eval_criteria: 验收标准列表
- prompt_refs: 模块化 prompt 引用路径
- skills, skill_refs: 技能清单与路径
- goal: 角色目标
- constraints: 红线约束

### RoleDef（PersonaDef 扩展）
- lifecycle: infinite | ondemand
- drive: cron | loop | ondemand
- cron_schedule: 驱动方式为 cron 时使用
- input_signals: 输入信号列表（bus 分类 / shell 命令）
- output_targets: 输出目标列表（bus cat=xxx 格式）
- session_hint: cron | interactive | background

关系: RoleDef 继承 PersonaDef，增加角色专属的运行时字段。Browser Harness 只用 PersonaDef，Session 角色用 RoleDef。

## 3. 文件结构全览

```
hermes-session-roles/
├── personas/
│   ├── session-roles/            # 25 个基础设施角色 JSON
│   │   ├── persona_00_maintainer.json  # 运维者
│   │   ├── persona_01_scout.json       # 侦察兵
│   │   ├── persona_02_consumer.json    # 信息消费者
│   │   ├── persona_03_curator.json     # 信息维护者
│   │   ├── persona_04_coordinator.json # 管理者
│   │   ├── persona_05_engineer.json    # 开发工程师
│   │   ├── persona_06_closer.json      # 闭环者
│   │   ├── persona_07_consumer.json
│   │   ├── persona_08_optimizer.json   # 性能优化师
│   │   ├── persona_09_codex-dev.json   # Codex 开发者
│   │   ├── persona_10_ccs-monitor.json # Session 监控者
│   │   ├── persona_11_debate_verifier.json # 辩论验证者
│   │   ├── persona_12_debate_verifier.json
│   │   ├── persona_13_product_architect.json
│   │   ├── persona_14_knowledge_curator.json
│   │   ├── persona_15_security_auditor.json
│   │   ├── persona_16_pm.json
│   │   ├── persona_17_reviewer.json
│   │   ├── persona_18_qa.json
│   │   ├── persona_19_devops.json
│   │   ├── persona_20_writer.json
│   │   ├── persona_21_lr.json           # 技术负责人
│   │   ├── persona_22_pg.json           # 程序实现员
│   │   ├── persona_23_investigator_python.json
│   │   ├── persona_24_investigator_senior.json
│   │   ├── persona_24_investigator_general.json   # 注意: 24 有两个编号冲突
│   │   └── persona_25_archivist.json
│   └── browser-harness/          # 57 个浏览器自动化人格
│       ├── persona_01_core.json         # 10 核心人格
│       ├── persona_02_specialized.json  # 25 专业人格
│       ├── persona_03_advanced.json     # 22 高级人格
│       ├── _bh_to_sr_map.json           # BH → Session 角色映射
│       ├── _bh_route_config.json        # BH 路由扩展配置
│       ├── _ccs_injection_rules.json    # CCS 注入规则
│       └── _ecosystem_health.json       # 生态健康检查配置
├── prompts/
│   ├── base.md*              # 多版本 base prompt (base.md.1 - base.md.5)
│   └── roles/                # 角色专业 prompt 模板
├── src/
│   ├── models.py             # PersonaDef + RoleDef dataclass
│   ├── registry.py           # load_all / get / list_roles / list_personas / register
│   ├── search.py             # 中文语义搜索（bigram + 同义词 + 字段加权）
│   ├── cli.py                # CLI 入口: list / show / load / search
│   ├── validate_roles.py     # 26 角色全量校验（P0/P1/P2 三级检查）
│   ├── role_assembler.py     # 动态组装 system prompt（MetaGPT 模式）
│   ├── registry.py (role loading consolidated)     # 角色关系图谱（生产者→消费者矩阵）
│   ├── paths.py              # 统一路径管理
│   └── skills_discovery.py   # Skill 发现工具
├── tests/
│   ├── test_search.py        # 15 个搜索回归测试
│   └── test_registry.py      # 注册表测试
└── docs/
    ├── ARCHITECTURE.md       # 原有架构文档
    ├── ARCHITECTURE_PROTOCOL.md
    ├── INDEX.md
    ├── QUICKSTART.md
    ├── ROLE_TEMPLATE.md
    ├── SEARCH.md
    └── TECHNICAL_DEEP_DIVE.md  # 本文档
```

## 4. 核心模块详解

### 4.1 registry.py — 角色注册表

全局单例，从 `personas/session-roles/*.json` 和 `personas/browser-harness/*.json` 加载所有角色。

```python
load_all()                   # 懒加载，首次访问时扫描磁盘
get(name)                    # 按 name 查找（先查 role 再查 persona）
list_roles()                 # 仅返回 session 角色
list_personas(category=None) # 返回 browser-harness 人格，可选分类过滤
list_categories()            # 返回所有分类及其计数
register(obj)                # 注册自定义角色（运行时注入）
```

懒加载策略: `_LOADED` 标记 + `_ROLES` / `_PERSONAS` 双列表，避免重复扫描磁盘。

### 4.2 search.py — 中文语义搜索

零外部依赖，纯 stdlib 实现。

**算法流程:**
1. **分词**: 中文单字 unigram + 双字 bigram + 英文单词
2. **同义词扩展**: 10+ 组同义词集（中英打通，如"修"→"fix"→"patch"）
3. **字段加权评分**: title=40, description=40, category=15, name=10, prompt=3
4. **完整覆盖加成**: query 所有单字都在 target 中 → +25 分
5. **偏序匹配加成**: 检查字序（"修服务器"匹配'修'→'服'→'务'→'器'顺序）→ 0-20 分

```bash
python3 src/cli.py search "修服务器" --top 5
# → [scout (65.2分), maintainer (42.0分), ...]
```

### 4.3 validate_roles.py — 角色全量校验

**P0 检查:**
- JSON 文件可解析
- 所有必填字段存在（name, title, description, category, system_prompt, skills, skill_refs, goal, constraints）
- 角色名唯一

**P1 检查:**
- lifecycle 有效（infinite/ondemand）
- drive 有效（daemon/ondemand）
- drive=cron 时 cron_schedule 必填
- input_signals 格式正确（旧/新格式兼容）
- output_targets 格式匹配 `bus cat=xxx`
- eval_criteria 可执行或描述性验收标准
- prompt_refs 引用的文件存在

**P2 检查:**
- skills 非空数组
- skill_refs 包含所有 skills 路径
- goal 非空
- constraints 非空数组

**Prompt 质量检查:**
- 每个 prompt 文件包含 `## 参考来源` 章节
- 非原创角色必须引用至少 1 个外部 URL
- 第一行必须包含自身角色名，不混入其他角色名

### 4.4 role_assembler.py — 动态 Prompt 组装

对标 MetaGPT 模式: `profile + goal + constraints + skills → 完整 prompt`

**组装顺序:**
1. 角色名 + 标题
2. 定位描述
3. 通用红线（base.md）
4. 目标
5. 红线约束
6. 行为约束技能（仅 PG/Coordinator/LR 有）
7. 输入信号
8. 输出目标
9. 评估标准
10. 历史教训

**行为约束 skill 仅注入到特定角色:**
- `pg`: redline_enforce, decision_ladder
- `coordinator`: cluster_monitor
- `lr`: redline_check
- 其余角色的 skill 通过原生 SKILL.md 按需加载，不在 prompt 中全文注入

### 4.5 registry.py (role loading consolidated) — 角色关系图谱

硬编码的生产者→消费者矩阵，18 个角色间的数据流关系。

核心 API:
```python
load_all(base_dir=None)    # 从目录加载所有人格/角色定义
list_roles()               # 列出所有 Session 角色
list_personas(category=None) # 列出人格（可筛选分类）
get(name)                  # 按名称获取
list_categories()          # 返回 {分类: 数量} 统计
register(obj)              # 注册一个人格/角色
```

## 5. CLI API

```bash
# 角色管理
python3 src/cli.py list --roles         # 全部 26 角色
python3 src/cli.py list --category 维护 # 按分类筛选
python3 src/cli.py show maintainer      # JSON 完整定义

# Prompt 加载
python3 src/cli.py load maintainer               # 纯文本
python3 src/cli.py load maintainer --json         # JSON 格式
python3 src/cli.py load maintainer --extra KEY=VAL # 注入变量

# 语义搜索
python3 src/cli.py search "修服务器" --top 5
python3 src/cli.py search "写代码" --top 3

# Prompt 组装
python3 src/role_assembler.py maintainer --output prompt.md
```

## 6. 数据流

```
角色 JSON 定义                   运行时使用方
──────────────────────────────────────────────
persona_XX_*.json ──→ session-launcher/role_manager.py
                     └─→ 注入到 CCS workspace CLAUDE.md

persona_XX_*.json ──→ session-pipeline/routing/router.py
                     └─→ 自动推导 produce/consume 关系

registry.py (role loading consolidated)  ──→ ecosystem_health.py
                     └─→ 关系一致性检查
```

## 7. 角色生命周期

| 生命周期 | 驱动方式 | 典型角色 | 行为 |
|---------|----------|----------|------|
| infinite | cron | maintainer, scout, curator | 长期运行，定期轮询 |
| infinite | loop | coordinator, ccs-monitor | 长期运行，自定节奏 |
| infinite | ondemand | — | 长期运行，被动触发 |
| infinite | goal | codex-dev | 目标导向持续运行 |
| ondemand | ondemand | engineer, closer, pm | 按需启动，超时自动退出 |

## 8. Browser Harness 集成

Browser Harness 是独立的浏览器自动化人格库，57 个人格按三层级组织:

| 层级 | 文件 | 数量 | 范围 |
|------|------|------|------|
| Core | persona_01_core.json | 10 | 安全审计、数据采集、UI 测试 |
| Specialized | persona_02_specialized.json | 25 | 爬虫、监控、OCR、支付 |
| Advanced | persona_03_advanced.json | 22 | 复杂工作流引擎、反检测 |

**桥接机制:** `_bh_to_sr_map.json` 将 BH 人格映射到 Session 角色(如 `security-auditor` → `security_auditor`)
**路由扩展:** `_bh_route_config.json` 扩展 Session 角色的 produce 分类
**注入规则:** `_ccs_injection_rules.json` 定义 CCS 启动时如何注入 BH 能力
