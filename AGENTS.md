# hermes-session-roles AGENTS.md

## 项目概述
Session 生态的**定义层**——声明每个 CCS 的身份、专长、输入输出契约、验收标准。
纯数据，无逻辑。

## 整体架构
```
hermes-session-roles (定义层 — 本项目)       ← 最底层，不引用其他两项目
  ├──→ session-launcher (执行层)             ← 读 persona JSON 启动 CCS + 注入 prompt
  └──→ session-pipeline (路由+执行层)         ← 读 roles_export.json 构建路由表 + 执行工作流
         └──→ launcher/ccs.py send           ← 唯一跨项目调用（subprocess）
```

**注意：这不是三层流水线。session-roles 同时被 launcher 和 pipeline 独立消费。pipeline 和 launcher 不直接通信。**

**铁律：修改角色 JSON 时必须同时考虑上下游影响。**

## Git 工作流
1. 禁止切换分支，始终在 main 分支工作
2. 小步提交，每完成一个逻辑单元立即 commit
3. 出错用新提交修复，不要 revert
4. 本地即生产环境

## 协作红线
1. system_prompt 只写专业能力——协作逻辑一律不写
2. eval_criteria 必须可执行——禁止写"质量高"这种不可验证的标准
3. schema 只增不改——新字段可加，旧字段不能删
4. 文件命名：persona_XX_name.json

---

## Prompt 规范（2026-07-15 版）

### 一、三层 prompt 架构

每个角色的完整 prompt 由 role_assembler 从三层文件动态组装：

```
Layer 0: base.md（所有角色共享）
  └─ 角色红线（边界/违规后果）
  └─ 协作协议（bus 通信规范）
  └─ wf 操作手册（通用 CLI）

Layer 1: roles/<name>.md（角色专业能力）
  └─ 身份定位（我是谁）
  └─ 专长领域（我会什么）
  └─ 工作方法论（我怎么做）
  └─ 行为红线（什么不能做）
  └─ 输入/输出信号（我消费什么、产出什么）
  └─ 生态衔接（和谁协作）
  └─ 关键原则

Layer 2: mixins/<driver>.md（驱动模式）
  └─ loop_driver.md → 永不停止 + 退避重试 + 每轮读 bus
  └─ cron_driver.md → 检查→退出，不与"永不停止"冲突
  └─ ondemand_driver.md → 一次只做一件事，完成退出
```

### 二、每层的内容边界

| 层 | 包含 | 不包含 |
|----|------|--------|
| base.md | 红线、协作协议、wf 手册 | 永不停止指令、自审查指令、特定角色技能 |
| roles/\*.md | 角色身份、专长、方法论、信号契约 | 协作逻辑（如"永不停止"）、通用基线 |
| mixins/\*.md | 驱动模式特定的生命周期指令 | 角色专业知识、信号契约 |

### 三、各类指令的正确归属

| 指令 | 归属 | 理由 |
|------|------|------|
| 角色红线（不越界、不替决策） | base.md | 所有角色通用 |
| 协作协议（bus 格式、证据要求） | base.md | 所有角色通用 |
| wf 操作手册 | base.md | 所有角色通用 |
| 永不停止、退避重试 | mixins/loop_driver.md | 只适用于 loop 驱动角色 |
| 9Router 错误恢复 | mixins/loop_driver.md | 同上 |
| 自审查六维（提交前检查） | roles/engineer.md, roles/pg.md | 只适用于写代码的角色 |
| D1-D6 审查维度 | roles/reviewer.md | reviewer 原本就有（审查别人 PR） |
| cron 角色退出逻辑 | mixins/cron_driver.md | cron 驱动角色不该循环等待 |

### 四、角色 prompt 文件结构标准

每个 roles/\*.md 必须按以下顺序组织：

```
# <name> - 角色系统提示词

## 参考来源（可选）
- <外部 URL>

---

## 身份定位
你是谁、核心职责一句话

---

## 专长领域
- 技能1
- 技能2

---

## 输入信号
| 信号来源 | 分类 | 过滤条件 |

## 输出目标
| 目标分类 | 产出内容 |

---

## 工作流程/方法论
### Step 1: ...
### Step 2: ...

---

## 行为红线（可选）
### ❌ 禁止事项

---

## 生态衔接
- 上游: xxx → 你 → 下游: yyy

---

## 关键原则（可选）
> 一句哲学总结
```

### 五、eval_criteria 规范

每条 eval_criteria 必须是可执行的 shell 命令（返回 0=通过），或是以"验证:"开头的描述性标准：

```
# 可执行
"systemctl --user is-active sister-agent-dkk.service"

# 描述性（含"验证:"前缀）
"验证: 所有核心服务 active"
```

### 六、常见问题（修改 prompt 时自查）

| 场景 | 正确做法 |
|------|---------|
| 想加"永不停止"指令 | 放在 mixins/loop_driver.md，不在 base.md |
| 想加自审查指令 | 放在 roles/engineer.md 或 roles/pg.md，不在 base.md |
| 想增加角色红线 | 加在 base.md |
| 想加角色特有方法论 | 加在 roles/<name>.md |
| 想改角色驱动模式 | 改 persona JSON 的 drive 字段 + 对应 mixin |
| 加了新分类到 output_targets | 同步通知 session-pipeline（自动推导生效） |
| 加了新角色 | 按"新增角色清单"逐项检查 |

---

## 自维护指令（Agent 按此执行）

### 1. 每次修改角色后：全量验证

```bash
python3 src/validate_roles.py
# 预期: 文件数: 26, 角色数: 26, 错误数: 0

python3 tests/test_search.py
# 预期: 15/15 通过
```

### 2. 新增角色清单

- [ ] `python3 src/cli.py show <name>` 不报错
- [ ] `python3 tests/test_search.py` 全通过
- [ ] eval_criteria 每条能在 shell 里跑通
- [ ] system_prompt 无协作逻辑
- [ ] skill_refs 指向已存在的 skill 文件（不存在的文件=失败）
- [ ] drive=cron 时有 cron_schedule
- [ ] input_signals 的 source 可直接在 shell 执行
- [ ] output_targets 格式 `bus cat=<分类> <描述>`
- [ ] prompt_refs 包含 base + role + driver
- [ ] 文件命名 `persona_XX_name.json`，XX 两位数序号
- [ ] prompts 文件包含 `## 参考来源` 章节
- [ ] 参考来源必须有外部 URL（validator 强制）
- [ ] skills 非空数组（validator 强制）
- [ ] skill_refs 覆盖全部 skills（validator 强制文件存在）
- [ ] lifecycle/drive 合法值

### 3. 角色验证6维度

| 维度 | 检查内容 | 命令 |
|------|----------|------|
| D1 正确性 | JSON schema 完整、字段类型正确 | validate_roles.py |
| D2 安全性 | prompt 无越界指令、eval 注入 | grep -i "eval\|exec\|os.system" |
| D3 可维护性 | 命名规范、分类一致 | ls personas/session-roles/ |
| D4 性能 | prompt 长度、信号轮询频率 | wc -c system_prompt |
| D5 一致性 | 全部角色风格统一 | diff persona_*.json 结构 |
| D6 可测试性 | eval_criteria 可 shell 执行 | 逐条在 shell 运行 |

### 4. 跨项目联动

修改角色定义（input_signals / output_targets）后，session-pipeline 的路由表
自动更新。验证方式：

```bash
cd /home/administrator/session-pipeline
PYTHONPATH=src python3 -c "
from router import get_router
r = get_router()
print('maintainer produce:', r.role_produce_categories('maintainer'))
print('security consumers:', r.get_consumers('security'))
"
```

### 5. 每周自进化

- 检查是否有角色缺失 output_targets 或 input_signals
- 检查是否有重复角色（name 冲突）
- 检查 Browser Harness 映射是否需要更新
- 评估 prompt 蒸馏质量：每条规则是否来自真实踩坑
- 检查 prompt 层级归属是否正确（base vs roles vs mixins）

## Browser Harness 集成
57 个人格按三层组织：core(10) → specialized(25) → advanced(22)
通过 `_bh_to_sr_map.json` 桥接到 session 角色。
