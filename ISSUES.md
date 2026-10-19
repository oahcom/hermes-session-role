# hermes-session-roles 问题单

审查时间：2026-10-16 | HEAD：`e652d2e`

> ⚠️ **本单条目为建单时快照。核实前不要直接开工** —— 用
> `git log -S "<缺陷特征串>" -- <文件>` 查是否有修复提交。
> R71 session 复核（2026-10-16 23:40）：
>
> | 条目 | 状态 | 复核依据 |
> |------|------|----------|
> | R2 | ✅ 已修 | `validate_roles.py` 的 `REQUIRED_FIELDS` 已含 `lifecycle` |
> | R6 冲突点 | ✅ 已修 | base.md:374 现为「测试方法名用英文…（标识符一律英文）」，旧的中文规则已移除 |
> | R6 重复段 | ⚠️ **不建议按原方案删** | 原建议"删除与全局 CLAUDE.md 重复的 165 行"。实测角色 session 对全局独有内容（如「多 Session 架构」）零认知，而 base.md 内容有认知 → 全局 CLAUDE.md 疑未注入角色 session，删副本将丢失规则。详见 `~/hermes/workspace/R71-角色对话质量根因修复/ROUND3.md` 第十/十三节 |
>
> 未复核条目不等同于未修 —— 开工前请自行 `git log -S` 确认。

标注说明：**[已验证]** = 本机实际执行复现；**[代码确认]** = 读码确认逻辑缺陷，未构造运行时复现。

---

## R1 [P0] coordinator 的 workgroup 覆盖代码内置的 `{"*"}` 通配 → 协调者无法向多数角色下发决策消息 [已验证]

- 位置：`personas/session-roles/persona_04_coordinator.json`（`workgroup`）与 `~/session-launcher/src/routing/gatekeeper.py:101,121,215`
- 证据：gatekeeper 先写 `matrix = {"coordinator": {"*"}}`，随后 `if roles: matrix[name] = roles` 用 JSON 值整个覆盖。实测：
  ```
  PYTHONPATH=src python3 -c "import routing.gatekeeper as g; print(g.WORKGROUP_MATRIX['coordinator'])"
  → {'pm', 'pg', 'devops', 'lr'}
  ```
  coordinator persona 的 `workgroup` 仅 4 项（lr/pm/pg/devops），而其 `collab.track.notify_roles=["closer"]`、`guard.watch=["pm","engineer"]` 中 closer 与 engineer 均不在该集合内 → 角色按自身契约发通知也会被门禁拒。
- 失败场景：coordinator 向 engineer/qa/reviewer/writer/curator/scout 发任一条含"分配/决策/审批"的红消息，被 `gatekeeper.py:215` 判 `not in workgroup matrix, red message blocked`。
- 修复方向：gatekeeper 改 `matrix.setdefault(name, roles)`（保留内置通配），或本 persona 的 workgroup 显式加入 `"*"`。两处择一，建议改 gatekeeper 侧以免每个新增角色重复踩。

## R2 [P0] validate_roles 对缺少 `lifecycle` 字段的角色静默跳过全部深度校验，返回 0 假绿 [已验证]

- 位置：`src/validate_roles.py:364`（`if "lifecycle" not in data: return role_count`），`REQUIRED_FIELDS`（`:17-20`）不含 `lifecycle`
- 证据：构造缺 `lifecycle` 且注入 6 处非法字段（`drive=NONSENSE`、`output_targets=["垃圾格式"]`、`mcp_servers=[]`、`skills=["nonexistent"]`、`skill_refs={}`、非法 `eval_criteria`）的角色文件 → 输出 `错误数: 0 / 所有角色验证通过`，返回码 0。同一文件补齐 `lifecycle` 后同内容立刻报 11 个 FAIL。
- 失败场景：任何新建角色 JSON 少写一个 `lifecycle` 键，drive 校验、bus 分类校验、skills/skill_refs 校验、mcp 校验、eval_criteria 校验全部不执行 → 畸形角色直接进生产；且 `tests/test_registry.py:68` 把返回码 0 当作通过。
- 修复方向：把 `lifecycle` 加入 `REQUIRED_FIELDS`，删除 `:364` 的提前 return。

## R3 [P1] `mistakes` 字段被 `to_dict()` 白名单切断 → lr 的历史教训依加载顺序静默消失 [已验证]

- 位置：`src/role_assembler.py:216`（`role.get('mistakes', [])`）与 `src/models.py:32-38`（`to_dict` 白名单不含 mistakes）
- 证据：`load_role_json` 优先走 `registry.get()` → `to_dict()`。实测冷路径（直接读 JSON）`'mistakes' in j` → True；热路径（先 `registry.load_all()`）`'mistakes' in lr.to_dict()` → **False**，且 `assemble_role_prompt('lr')` 中 `'历史教训'` → False。JSON 中 mistakes 是 200+ 字的真实越权踩坑记录。
- 失败场景：任何先 `load_all()` 再组装 prompt 的调用方拿到缺失"历史教训"段的 lr prompt。launcher `routing/roles.py:49` 正是这样 import 的 —— 即最常见的生产路径。
- 修复方向：`PersonaDef` 增加 `mistakes: list = field(default_factory=list)` 并纳入 `to_dict()`。

## R4 [P1] CI 存在两处必失败步骤，配合 `|| echo` 使流水线无实际门禁 [已验证]

- 位置：`.github/workflows/test.yml:19`、`:22`、`:26`
- 证据：`:19` `find src/ -name '*.py' -exec python3 -m py_compile {} ;` 分号未转义 → `find: missing argument to '-exec'`（rc=1）；`:22` `python3 tests/test_search.py` 引用的文件已在 `e652d2e` 删除 → `can't open file ... [Errno 2]`（rc=2）；`:20` 的 `-run:` 是 `run:` 笔误；`:26` 的 `|| echo` 吞掉 validate 步骤非零码。
- 失败场景：每次 push 的 Test workflow 在 Syntax 检查即失败；即使通过，validate 步骤的"失败"与"通过"在 CI 视图上不可区分。
- 修复方向：`-exec ... {} +`；`test_search.py` 步骤改 pytest；validate 步骤去掉 `|| echo`。

## R5 [P1] `load_all(base_dir=...)` 的 5s TTL 缓存不区分 base_dir，第二次调用被静默忽略 [已验证]

- 位置：`src/registry.py:83`、`:88`（TTL 判断只看 `_LOADED_AT`，缓存键不含 `base_dir`）
- 证据：实测 `registry.load_all()` → 62；紧接着 `registry.load_all(base_dir=<临时目录，仅含 1 个角色>)` 仍返回 **62**，`list_roles()` 仍是完整 31 个角色。
- 失败场景：5 秒窗口内用不同 base_dir 做隔离加载的调用方（测试夹具、多根目录部署）拿到上一批数据且无任何告警。
- 修复方向：把 `base_dir` 纳入缓存键。

## R6 [P1] `prompts/base.md` 43% 是全局 CLAUDE.md 逐字副本，其中一条已被推翻的规则正注入 31 个角色 [已验证]

- 位置：`prompts/base.md:102-512` 与 `~/.claude/CLAUDE.md` 的重叠段；冲突点在 `prompts/base.md:374`
- 证据：脚本比对 `base.md` 非空长行 379 行、全局 199 行、**完全相同 164 行 → 43.3%**。`base.md:374` 逐字等于全局 §6.4 的 `- 测试命名中文场景：test_从空账户取款_返回错误`，而 memory `no-chinese-identifiers` 已明确"方法名/变量名一律英文，测试方法名也不例外；与 CLAUDE.md §6.4 冲突时以本条为准"。本项目 `CLAUDE.md` 禁止操作第 2 条亦明写"禁止向 prompts/base.md 写回全球规则"。
- 失败场景：全局规则修订后 base.md 副本不跟随，31 个角色的 system_prompt 持续注入已被推翻的"用中文写测试方法名"，与角色实际收到的"标识符一律英文"约束直接冲突 —— 角色面对互相矛盾的指令。
- 修复方向：删除 base.md 中与全局 CLAUDE.md 重复的整段，仅保留角色侧专有内容（同时消除 R6 与 R2 共同指向的"副本漂移"结构性风险）。

## R7 [P1] workgroup 中存在幽灵角色 `verifier`，校验器不覆盖 workgroup 故未被发现 [已验证]

- 位置：`personas/session-roles/persona_99_rebutter.json` 的 `workgroup: [{"role": "verifier"}]`；`src/validate_roles.py:129` 的 `_validate_collab` 只校验 `collab.guard.watch`
- 证据：全仓角色名集合中不存在 `verifier`（只有 `debate_verifier`）。实测：
  ```
  gatekeeper.WORKGROUP_MATRIX['rebutter'] → {'verifier'}
  ```
  同文件 `collab.track.notify_roles=["debate_verifier"]`，与 workgroup 自相矛盾。
- 失败场景：rebutter 向真实存在的 `debate_verifier` 发红消息 → `'debate_verifier' not in {'verifier'}` 且无 `"*"` → 被门禁拒绝，辩论对无法闭合。
- 修复方向：workgroup 中 `verifier` 改为 `debate_verifier`；在 `_validate_collab` 同层增加 workgroup 角色存在性校验（防止同类幽灵再现，与 R2 同属"校验覆盖不全"）。

## R8 [P2] PUBLIC_API.md 列出已被删除的函数 [已验证]

- 位置：`PUBLIC_API.md:21`（`register(obj)`）、`:44`（`load_role(name)`）
- 证据：`grep -n "def load_role\b\|def register" src/*.py` 仅命中 `shared_loader.py:132 def load_roles()`；`e652d2e` 提交信息即"删除 ... registry.register/_notify_bus_contract_change"。另 `:49-63` RoleAssembler 小节重复三次。
- 失败场景：下游项目按该"公开 API 契约"调用 `shared_loader.load_role("qa")` → `AttributeError`；契约文档失去可信度。
- 修复方向：移除这两行；去重 RoleAssembler 小节。

## R9 [P2] `--roles` 是空操作，但三处文档宣称它是"列表"参数 [已验证]

- 位置：`src/validate_roles.py:154`（`action="store_true"`；全文件仅 `args.category` 被读取）；`README.md:174`、`:20`、`:81`
- 证据：`grep -n "args\." src/validate_roles.py` 只匹配 `args_category = args.category`。README:174 写 `python3 src/validate_roles.py --roles  # 全部 31 角色`。
- 失败场景：执行 `validate_roles.py --roles qa` 期望只验 qa → 实际全量运行且不报错，用户误判"qa 已单独校验通过"。
- 修复方向：`--roles` 改为接收角色名列表并真正过滤，或从文档删除该参数。

---

## 与既有问题单的关系

今天已有另一份三项目问题单：`~/.hermes/notes/audit/THREE_PROJECT_ISSUES_2026-10-16.md`（`TP-001..TP-011`）。核对重叠度后，**本单 9 条与 TP 单无重复**（覆盖 CI、registry 缓存、validate 假绿、gatekeeper 矩阵、base.md 副本漂移等不同面）。唯一交叉点是 TP-004 与 `session-pipeline/ISSUES.md` G8 涉及同一个卡死实例，但根因机制不同，已在 G8 内注明互补关系。

## 跨项目

- **R1/R7** 的生效点在 `session-launcher/src/routing/gatekeeper.py`：矩阵覆盖语义（L2）与 workgroup 校验缺失需在该侧一并收口。
- **R2/R7** 同源 —— 校验器"静默跳过"与"覆盖不全"是同一类缺陷，建议一次性审计 `validate_roles.py` 的全部 early-return 分支。
- 未发现模型名越权：`personas/` 与 `prompts/` 中无 Anthropic 原生模型残留，仅有 2 处 `9router_hermes`。
