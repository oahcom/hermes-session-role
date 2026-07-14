# hermes-session-roles AGENTS.md

## 项目概述
Session 生态的**定义层**——声明每个 CCS 的身份、专长、输入输出契约、验收标准。
纯数据，无逻辑。

## 整体架构
```
hermes-session-roles  →  session-launcher  →  session-pipeline
  (定义层)              (执行层)              (路由层)
```

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

## 自维护指令（Agent 按此执行）

### 1. 每次修改角色后：全量验证

```bash
python3 src/validate_roles.py
# 预期: 文件数: 25, 角色数: 25, 错误数: 0

python3 tests/test_search.py
# 预期: 15/15 通过
```

### 2. 新增角色清单

- [ ] `python3 src/cli.py show <name>` 不报错
- [ ] `python3 tests/test_search.py` 全通过
- [ ] eval_criteria 每条能在 shell 里跑通
- [ ] system_prompt 无协作逻辑
- [ ] drive=cron 时有 cron_schedule
- [ ] input_signals 的 source 可直接在 shell 执行
- [ ] output_targets 格式 `bus cat=<分类> <描述>`
- [ ] 文件命名 `persona_XX_name.json`，XX 两位数序号
- [ ] prompts 文件包含 `## 参考来源` 章节
- [ ] 非原创角色必须有外部 URL 引用

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

## Browser Harness 集成
57 个人格按三层组织：core(10) → specialized(25) → advanced(22)
通过 `_bh_to_sr_map.json` 桥接到 session 角色。
