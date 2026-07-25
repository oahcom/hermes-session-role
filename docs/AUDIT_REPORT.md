# Hermes Session 三项目 — 代码审计报告

> 审计时间: 2026-07-23 | 范围: hermes-session-roles / session-launcher / session-pipeline

---

## 发现清单

### F1 跨项目代码重复

**严重度: 高 | 类别: 死代码/维护负债**

两个项目各自维护完全相同的 `template_registry.py` 和 `template_validator.py`：

- `session-launcher/src/template_registry.py` (528 行) ≡ `session-pipeline/src/template_registry.py` (md5 完全一致)
- `session-launcher/src/template_validator.py` (205 行) ≡ `session-pipeline/src/template_validator.py` (md5 完全一致)
- `session-launcher/src/migration_scripts.py` (425 行) ≈ `session-launcher/src/migration/scripts.py` (414 行, 仅差 11 行)

**影响:** 修改需同步两/三份，极大概率 drift。实测两份 template_registry 已完全相同但各自为政。

**建议:** 抽取到共享位置 `~/.hermes/lib/` 或指定一个项目持有、另一个通过 `sys.path` 或符号链接引用。

---

### F2 Thin Wrapper 泛滥

**严重度: 高 | 类别: 死代码**

三项目共有 **15+ 个文件** 仅做 re-export，不做任何额外逻辑：

| 文件 | 行数 | 实际代码 |
|------|------|---------|
| session-launcher/src/role_manager.py | 27 | `from routing.roles import ...` |
| session-launcher/src/workflow_client.py | 13 | `from workflow.client import ...` |
| session-launcher/src/signal_parser.py | 28 | `from events.parser import ...` |
| session-launcher/src/launcher.py | 82 | `from core import ...` 全量 re-export |
| session-pipeline/src/router.py | 5 | `from routing.router import ...` |
| session-pipeline/src/auto_route.py | 5 | `from routing.auto import ...` |
| session-pipeline/src/workflow_engine.py | 5 | `from pipeflow.engine import ...` |
| session-pipeline/src/workflow_db.py | 5 | `from pipeflow.db import ...` |
| session-pipeline/src/routing_db.py | 5 | `from routing.rdb import ...` |
| session-pipeline/src/composite_runner.py | 5 | `from pipeflow.composite import ...` |
| session-pipeline/src/composite_models.py | 5 | `from pipeflow.models import ...` |
| session-pipeline/src/workflow_daemon.py | 11 | `from pipeflow.daemon import ...` |
| session-launcher/src/launcher.py | 82 | 全量 re-export core 旧接口 |
| session-launcher/src/lifecycle_manager.py | 75 | 委托 session-pipeline LifecycleManager |

合计约 **355 行纯 re-export 代码**。加上维护这些文件的 import 跟踪成本。

**建议:** 清理所有纯 re-export 的 stub，直接修改导入方。保留 `launcher.py` 一个兼容层（迁移期）。删除其余。

---

### F3 sys.path 污染（14 处）

**严重度: 中 | 类别: 技术选型可优化**

session-launcher 有 12 处 `sys.path.insert(0, ...)`，pipeline 有 2 处跨项目插入：

```
launcher:
  src/__init__.py          # auto insert src/
  src/paths.py             # ensure_paths() 统一注册
  src/launcher.py          # self insert
  src/wf.py                # self insert
  src/pool_cli.py          # self insert
  src/parallel_worker.py   # self insert
  src/ecosystem_cli.py     # + remove/reorder
  src/__main__.py          # self insert
  src/lesson_injector.py   # bus_protocol src
  src/routing/partner.py   # self insert
  src/routing/gateway.py   # self insert
  src/lifecycle_manager.py # session-pipeline (跨项目)
  src/ops/runner.py        # session-pipeline (跨项目)

pipeline:
  workflow/client.py       # session-launcher (跨项目)
  routing/auto.py          # session-launcher (跨项目)
```

**影响:** 运行时因为 `sys.path` 顺序不同可能出现模块遮蔽。跨项目依赖时隐式耦合。

**建议:** 跨项目调用统一走 `subprocess`（`python3 /path/to/ccs.py`）或安装为 pip 包。不要靠 sys.path 串起来。

---

### F4 双向跨项目依赖（循环耦合）

**严重度: 高 | 类别: 职责错误**

```
session-launcher ──→ session-pipeline
  (lifecycle_manager.py import pipeline lifecycle)
  (ops/runner.py import pipeline router)
  (paths.py add pipeline src to sys.path)

session-pipeline ──→ session-launcher
  (workflow/client.py import launcher workflow.client)
  (routing/auto.py import launcher sentinel)
  (routing/routes.py exec launcher ccs.py)
```

互为依赖方。改 launcher 可能 break pipeline，改 pipeline 可能 break launcher，无版本契约。

**建议:** 三项目的依赖关系必须单向：`roles → launcher → pipeline`。launcher 不应反向依赖 pipeline。目前的 `lifecycle_manager.py` 应内聚到 launcher 自己，或整个 `lifecycle` 模块明确归 pipeline 所有。

---

### F5 角色 JSON 编号错乱

**严重度: 中 | 类别: 低质量代码**

编号缺失和冲突：

- **missing 02:** 无 `persona_02_consumer.json`（consumer 文件完全丢失）
- **missing 07:** 无 `persona_07_consumer.json`（consumer 已在 02 缺失，07 也缺失）
- **missing 09:** 无 `persona_09_codex-dev.json`（期待 09 但实际是 `persona_10_codex_dev.json`）
- **编号冲突:** `persona_24_investigator_senior.json` 和旧文档说 "persona_24_investigator_general.json" 都占 24 号，实际 general 在 `persona_25_investigator_general.json`
- **编号跳跃:** 01 → 03 → 04 → 05 → 06 → 08 → 10 → 11 ...（跳过 02/07/09）
- **共计 23 个有效角色文件** + 1 个 test 文件（persona_99_test.json），但文档声称 26 个

**建议:**
1. 确认丢失的 3 个角色是否是故意删除（consumer 等）
2. 重新编号为连续序列或弃用编号改用 `name` 前缀（如 `maintainer.json`）
3. 更新 README 角色计数 26→23

---

### F6 events/ 模块孤立（723 行疑似死代码）

**严重度: 高 | 类别: 死代码**

`session-launcher/src/events/` 包含三个文件共 723 行代码：

| 文件 | 行数 |
|------|------|
| signals.py | 229 |
| parser.py | 240 |
| notify.py | 254 |

**但 events 模块仅被 `events/__init__.py` 内部引用，以及两个兼容层引用:**

- `launcher.py: 从 events.signals import check_signal`（兼容 re-export）
- `signal_parser.py: 从 events.parser import parse_signal`（兼容 re-export）

**除此之外，没有任何活跃的 Python 代码调用 events 模块的功能。** 外部也可能通过 bus/subprocess 使用。

**建议:** 如果是被 subprocess 调用的（如 cron 任务），明确标注并移出 `src/`。如果是被废弃的旧接口，标注 deprecated 并在下个版本删除。

---

### F7 lifecycle/manager.py 职责过载（824 行, 38 方法）

**严重度: 中 | 类别: 低质量代码**

`session-pipeline/src/lifecycle/manager.py` 是最长的单个文件（824 行，38 个方法），职责混合：

- workflow step 状态机
- template upsert
- approval token 管理
- 审计日志记录
- 通知引擎
- 数据库连接管理
- BS 检测器
- subprocess bus_client 调用

单一文件承载了 6-7 个独立职责。

**建议:** 拆分为：
- `manager.py` — 状态机编排（保留 ~300 行）
- `step_engine.py` — step 类型处理
- `approval.py` — token + 审批逻辑
- `audit.py` — 审计日志

---

### F8 P0 Exemption 过度工程（454 行, 1 个 Class）

**严重度: 中 | 类别: 技术选型可优化**

`session-launcher/src/p0_exemption.py` 用 454 行实现一个类。核心功能只有：

- 创建 P0 任务豁免（提供 template_id）
- 检查超时（4h 宽限期）
- 写审计日志

但实际包含了：
- SQLite 连接管理（30 行 CRUD 重复）
- 全套 `__enter__/__exit__` 上下文管理
- 角色白名单硬编码
- 工作时间计算（pm 工作时间 8-22 点）
- 多级降级逻辑

**建议:** 精简到 ~100 行，去掉上下文管理器（未用于 with 语句）、角色硬编码改为运行时注入、SQLite CRUD 抽取到共享 DB 模块。

---

### F9 role_relations.py — 硬编码矩阵 vs 角色 JSON 自动推导

**严重度: 中 | 类别: 职责错误**

`hermes-session-roles/src/role_relations.py` 维护一份硬编码的 producer→consumer 矩阵（18 个角色关系）。

而 session-pipeline 的 `routing/router.py` 已经从相同角色的 JSON 文件自动推导 produce/consume 关系。

两份映射（硬编码 + 自动推导）可能不同步。修改角色 JSON 后容易忘记更新 role_relations.py。

**建议:** 废弃硬编码矩阵，改为调用 pipeline 的 Router API 动态获取：

```python
# 替代 role_relations.get_relations("scout")
from router import get_router
router = get_router()
router.get_consumers("architecture")  # 自动推导结果
```

或保留 role_relations 但改为从 JSON 实时构建的自动生成代码。

---

### F10 validate_roles.py — prompts/roles 目录错误处理

**严重度: 低 | 类别: 低质量代码**

`validate_roles.py:145` 检查 `prompt_refs` 引用的文件存在性：

```python
prompts_dir = os.path.join(os.path.dirname(__file__), "..", "prompts")
if os.path.isdir(prompts_dir):
```

但角色 JSON 的 `prompt_refs.base = "base.md"`，实际文件在 `prompts/base.md` 但有多版本（base.md.1 ~ base.md.5）。验证器只检查 `base.md` 是否存在——多版本文件没有检查。

此外，`prompts/roles/` 子目录的检查（第 179 行）遍历 `*.md` 文件检查 `## 参考来源` 存在性。但 `prompts/roles/` 已 gitignored 或空的可能下，该检查会跳过，降级质量门禁效果。

---

## 严重度分布

| 严重度 | 数量 | 发现 |
|--------|------|------|
| 高 | 4 | F1 跨项目重复, F2 Thin Wrapper 泛滥, F4 循环耦合, F6 events 孤立 |
| 中 | 5 | F3 sys.path 污染, F5 编号错乱, F7 职责过载, F8 过度工程, F9 硬编码 |
| 低 | 1 | F10 验证器不完整 |

## 行动建议优先级

1. **P0:** 删除被复制粘贴的 `template_registry.py` / `template_validator.py` 副本，统一指向一个源
2. **P0:** 修复角色数量声明（26→24）和编号冲突
3. **P1:** 清理 15 个 thin wrapper stub，直接改导入方
4. **P1:** 解耦跨项目循环依赖（lifecycle_manager 归属仲裁）
5. **P2:** 精简 p0_exemption.py 到合理大小
6. **P2:** 确认 events/ 模块是否活跃，不活跃则标记 deprecated
7. **P3:** 统一 sys.path 管理策略
