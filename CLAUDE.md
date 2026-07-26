# hermes-session-roles — 角色定义层

> 是本项目的操作手册，不是角色知识库。角色知识在 prompts/ 目录。

## 项目职责

定义"谁是谁"——角色身份模板 JSON，供 launcher 和 pipeline 消费。

## 关键规则

### 角色 JSON Schema
- `personas/session-roles/persona_*.json` 是单一真相来源
- 每个角色的 `system_prompt` 字段必须与其他两个文件的内容**不重叠**：
  - `prompts/base.md`（角色职责红线、Git 规范、自审查指令、工作流操作指南）
  - `prompts/roles/<role>.md`（专长领域、工作方法论）
  - skill 文件（prompts/skills/）
- 结构字段（`input_signals`、`output_targets`、`eval_criteria`、`workgroup`）不被复制到任何 md 文件
- 所有角色 JSON 必须通过 `src/validate_roles.py` 验证

### prompt 编译规则
```bash
# 验证所有角色 JSON
python3 src/validate_roles.py

# 编译单个角色
python3 src/role_assembler.py <role_name>

# 查看角色输出分类
grep -A2 output_targets personas/session-roles/persona_*.json
```

### 架构红线（精简）
参见 `docs/ARCHITECTURE_PROTOCOL.md` 完整版。核心：
1. gateway 不可重启（SIGKILL → 长连接断开 5-30min）
2. 服务探测 3 次连续失败才标 down
3. Daemon 必须 PID 锁单实例
4. 三个项目同步修改

### Sister Bus 分类体系
| 分类 | 用途 |
|------|------|
| architecture | 架构决策、红线变更 |
| code_fix | 代码变更、问题修复 |
| security | 安全事件 |
| performance | 性能优化/重构 |
| task_spec | 任务规范 |
| code_review | 代码审查 |
| bug_report | 缺陷报告 |
| blocker | 阻塞性问题 |
| scheduler | 定时调度 |

## CCS 协作概览
- 三种协作模式：主从、对等、仲裁
- 协作逻辑在代码层（turn_tracker/watchdog），不在 prompt 中
- CCS 通过 Sister Bus 通信
- 参见 `~/session-launcher/` 执行层实现
- 参见 `~/session-pipeline/` 路由层实现

## 禁止操作
- ❌ 直接修改 `prompts/base.md` 或 `prompts/roles/*.md` 时不更新对应的 persona JSON
- ❌ 向 `prompts/base.md` 写回全球规则（已移入 `~/.claude/CLAUDE.md`）
- ❌ 在 persona.json 的 `system_prompt` 中写 `prompts/roles/*.md` 已覆盖的内容
- ❌ 跨项目修改：本项目的文件调整不直接影响 launcher 或 pipeline 的代码

## 验证命令
```bash
python3 src/validate_roles.py          # 验证所有角色
python3 src/role_assembler.py <role>   # 编译角色输出
python3 ~/.hermes/scripts/bus_client.py stats  # 总线统计
```
