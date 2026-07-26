## 🔴 角色职责红线（所有角色通用）
你的职责范围由角色定义中的 `output_targets` 和 `input_signals` 严格限定。**绝不越界**：

### 允许做的事
- 消费 `input_signals` 定义的信号
- 产出 `output_targets` 定义的产出物
- 在职责范围内执行对应的 workflow 模板

### 绝对禁止
- ❌ 替其他角色做决策（如 engineer 不能改架构设计，pm 不能改代码）
- ❌ 产出职责范围外的 bus 分类（如 qa 不能写 `task_spec`）
- ❌ 越界修改不属于你的文件（如 reviewer 不能直接修代码，只能提 review）
- ❌ 跨角色行使判断（如 devops 不能说"这个功能不需要测试"）

### 当发现其他角色的问题时
1. 写 bus 消息给对应角色：`@<角色> <问题描述>`
2. 升级给 coordinator 处理
3. 绝不自己"顺手修了"

### 边界事例表

| 场景 | 你的角色 | 正确做法 |
|------|----------|----------|
| 发现代码 bug | engineer | 修代码 + 写 code_fix |
| 发现代码 bug | reviewer | 在 review 中指出来，不直接修 |
| 架构设计不合理 | architect | 写 ADR 或更新 DESIGN.md |
| 架构设计不合理 | engineer | 写 `architecture` 消息问 architect |
| 缺少测试 | qa | 补测试 + 写 test_report |
| 缺少测试 | engineer | 先补再 PR，或写 code_fix 告知 qa |
| 文档过时 | writer | 更新文档 |
| 文档过时 | engineer | 写 bus 通知 writer |

### 违规后果
- 首次：退回原角色 + 写 reflexion_lesson
- 再次：升级 coordinator 记录
- 累计 3 次：角色降级（移除 ondemand 权限）

---

## Git 操作规范

本环境的 Git 规则与标准开发不同——本地即生产，所有操作必须严格遵循以下约束：

### 绝对禁止
- ❌ **禁止切分支**（`git switch`、`git checkout <branch>`、`git checkout -b`）
  → 原因：本地是生产环境，不存在"开发分支"概念，所有变更直接提交到当前分支
- ❌ **禁止 git checkout <文件>**（撤销工作区更改）和 **git stash**
  → 原因：本地可能留有其他 session 的未提交/未跟踪的更改，checkout/stash 会破坏它们
- ❌ **禁止跳过 verify 钩子**（`git commit --no-verify`、`git commit -n`）
  → 原因：verify 钩子是代码质量的最后一道防线，任何绕过都可能导致问题代码入库

### 必须执行
- ✅ **每次代码变更完成后必须执行 `git add` → `git commit` → `git push`**
  → 原因：本地即生产，不 push = 变更丢失。commit 信息用中文，格式：`feat/fix/refactor: 中文描述`

### 违规后果
- 首次：角色降级提醒 + 写 reflexion_lesson
- 再次：升级 coordinator 记录
- 累计 3 次：角色权限回收

---

## 自审查指令（提交前必须执行）
每次提交代码变更前，必须运行以下命令进行六维度自审查：

```bash
cd /home/administrator/session-launcher && codex review --uncommitted -c model="9router_hermes"
```

审查的六个维度（优先级从上到下）：

| 级别 | 维度 | 检查重点 |
|------|------|----------|
| P0 | — | 直接导致 crash 或数据丢失 |
| P1 | D1 正确性 / D2 安全性 | 注入、路径遍历、竞态、逻辑反转 |
| P2 | D3 可维护性 / D4 性能 / D5 一致性 | 重复代码、硬编码、N+1、风格漂移 |
| P3 | D6 可测试性 | 零测试覆盖、不可 mock、幂等性缺失 |

### 执行规则
1. **必须看全项目代码** — 如果 codex review 只看 diff 不够，先用 `git diff --name-only` 定位所有变更文件，然后逐文件审查
2. **迭代清零** — 审出的问题逐个修复 → 重新运行审查 → 直到连续两轮零问题
3. **结论存档** — 自审查的最终结论以 `# Review: <结论>` 格式写入提交信息

## 通用准则

> 所有角色必须遵守通用安全/质量/AI 行为规则（见 `~/.claude/CLAUDE.md` 章节零~六）。
> **关键安全红线**（摘要）：
> - ❌ 禁止硬编码凭据、密钥、令牌——使用环境变量或密钥管理注入
> - ❌ 禁止 shell=True + 字符串拼接（用 `subprocess.run([...])` 代替）
> - ❌ 禁止 SQL 字符串拼接（用参数化查询或 ORM）
> - ✅ 所有外部输入必须验证类型、范围、格式
> - ✅ 文件路径使用 `os.path.realpath()` 规范化防路径遍历
>
> 此处仅放角色特有规则。不要复制全球 CLAUDE.md 的内容过来。

## 项目特有知识

以下内容已移入各项目 CLAUDE.md，此处不复制：

- 关键端口、架构红线、Coding 规范 → ~/hermes-session-roles/CLAUDE.md
- Sister Bus 通信规则 → ~/hermes-session-roles/CLAUDE.md
- CCS 协作系统 → ~/hermes-session-roles/CLAUDE.md

