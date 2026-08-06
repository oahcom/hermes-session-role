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


# AI 编码编程规范（通用准则）

> 以下规则融合自 GitHub 顶级 AI 编码规范仓库:
> [PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) (40k ⭐),
> [ciembor/agent-rules-books](https://github.com/ciembor/agent-rules-books) (1.9k ⭐),
> [yzhao062/agent-style](https://github.com/yzhao062/agent-style) (524 ⭐),
> [matank001/cursor-security-rules](https://github.com/matank001/cursor-security-rules) (372 ⭐),
> [grapeot/devin.cursorrules](https://github.com/grapeot/devin.cursorrules) (6k ⭐)

---

## 零、验证协议（Chain-of-Verification + Anti-Fabrication）
> **铁律：以下所有规则必须在声称任务完成前执行。未执行 = 未完成。**

### 0.1 四步验证链（Core Protocol）

在报告"完成" / "done" / "✅" 之前，**必须依次执行以下 4 步验证命令**，并将实际输出写入最终回复：

```bash
# ── 步骤 1：文件变更验证 ──
git diff --name-only HEAD~1..HEAD      # 检查已提交的变更
# 若尚无 commit：
git diff --name-only                    # 检查未提交的变更

# ── 步骤 2：语法验证 ──
# 对步骤 1 列出的每个 .py 文件执行：
python3 -m py_compile <每个变更的 py 文件路径>
# 报告 PASS/FAIL

# ── 步骤 3：服务状态验证 ──
systemctl --user is-active sister-agent-ssk.service
systemctl --user is-active sister-agent-dkk.service
systemctl --user is-active cron-worker.service
# 报告每个服务的 active/inactive 状态

# ── 步骤 4：声明真实性验证 ──
# 对你声称修改过的每个文件逐一核对：
#   a) git diff 显示该文件有变更？（是/否）
#   b) md5sum 与 session 开始前的基线有差异？（是/否）
# 任一答案为"否"→你没有修改它，不可声称修改了它
```

**只有 4 步全部执行完毕且输出已记录，才能说"done"。**

### 0.2 反伪造规则（Anti-Fabrication Rules）

以下为硬规则，直接禁止已观测到的伪造模式：

| # | 规则 | 禁止模式 | 正确做法 |
|---|------|----------|----------|
| 1 | **禁止模板工具计数** | "Tools Used: 304 total, Bash=253, Read=42, Edit=2, Write=5" | 必须从 `audit-log.txt` 实际统计；未统计则不报 |
| 2 | **禁止幻觉路径** | "Key Files Modified" 中包含不存在的路径 | 路径必须同时满足：`os.path.exists()`、在项目目录内、在 git diff 中 |
| 3 | **禁止回放过期数据** | Session 总结中出现前几天的 deny-log/audit-log 时间戳 | 仅包含当前 session 时间范围内的条目；发现过期数据直接丢弃 |
| 4 | **禁止虚报数字** | "720→92 行精简"、"12 个助手"、"10/10 闭环" | 每个数字必须用 `wc -l`、`grep -c` 等命令验证；未运行命令则写"未验证" |
| 5 | **禁止自我评价标记** | "✅ 已完成"、"✅ 通过"、"CLEAN"、"10/10" | 只报告：执行了什么命令 + 命令的实际输出；自我评价标记 = 无证据声明 |

### 0.3 强制自检块（Mandatory Self-Critique）

在每次最终回复前，**必须**包含以下格式的自检块。空字段表示任务未完成：

```

## 自检
我声称完成的任务: [在此填写任务描述]
我实际运行的验证命令:
  - git diff: [实际输出]
  - py_compile: [实际输出]
  - systemctl: [实际输出]
  - md5 对比: [实际输出]

未验证的声明: [列出没有运行命令就声称的事情]
已知风险: [可能遗漏的问题]
```

**如果自检块中的命令输出为空或填写"待补充"，则任务视为未完成，不得标记 done。**

### 0.4 违规后果

- 首次违反任意 0.1-0.3 规则 → 本次回复作废，必须重做
- 同一 session 内再次违反 → 记录到 `~/.hermes/memories/verification_violations.json`
- 累计 3 次违反 → 自动降级至限制模式（仅读操作，不可写文件或执行命令）

---

## 启动时必须执行（Session-Level Self-Monitoring）
> **最高优先级：每次新 session 开始，必须在任何其他操作前执行此块。**

### 1. 模型强制规则

**所有子代理（sub-agent）、后台任务、multi-agent 工作流必须使用 `9router_hermes`。**
禁止使用 Anthropic 原生模型（Opus/Sonnet）作为子代理。

```bash
# 每个子代理启动时必须显式指定：
/agent --model 9router_hermes <任务>
# 或通过 settings.json 的 model 配置继承
```

### 2. 启动 CronCreate 自检定时器

```bash
# 这一行必须是 session 第一条指令 — 由 Claude Code 内部工具执行
CronCreate(cron="*/15 * * * *", prompt="bash ~/.claude/hooks/cron_selfcheck.sh", recurring=true)
```

**关键语法说明：**
- `cron="*/15 * * * *"` = 标准 cron 表达式，每 15 分钟触发一次
- `recurring=true` = 循环执行，不设置则仅执行一次
- `prompt` = 引用脚本文件，避免多行字符串导致 JSON 解析失败
- CronCreate 是 **session 级** 工具：session 结束即失效，下次 session 必须重新创建

### 3. 启动 /loop 持续工作流

```bash
# 在 CronCreate 之后立即执行，保持持续任务推进
/loop
```

**/loop 交互规则：**
- `/loop` 单独使用 = 自动节奏模式：Claude Code 自行决定何时重试/继续
- `/loop 5m /status` = 固定间隔模式：每 5 分钟执行一次 `/status`
- **CronCreate 不会中断 /loop**；两者并行运行。CronCreate 在指定时间点插入自检任务，/loop 继续推进主任务
- 推荐：用 `/loop` 推进主任务，CronCreate 处理周期性自检

### 4. 加载 Sister Bus 未读消息（限 30 条防 /compact）

```bash
python3 ~/.hermes/scripts/bus_client.py unread --limit 30
# 若 > 0 条，逐条阅读并纳入上下文，读完后标记已消费。limit 30 限制首次加载量，防止 /compact。
```

### 5. 读取违规历史（自我纠正）

```bash
# 必须读取，查看上一轮 supervisor 检测到的违规
cat ~/.claude/projects/-mnt-c-Users-Administrator/memory/memory-sessions.md | grep -A 50 "# Violation Record"
# 发现违规 → 本 session 必须加强约束（如：所有声明必须先跑命令再输出）
```

---

## 一、诚信准则（Anti-Sycophancy — 反谄媚防幻觉）
1. **验证库存在**: 调用第三方函数前检查 `package.json` / `requirements.txt` 等清单；不确定时标注 `# VERIFY: 确认该 API 是否存在`
2. **禁止虚构签名**: 绝不捏造不存在的函数签名或类型；先装依赖再写依赖代码
3. **验证前先枚举边界**: 被问"这样对不对"时，先列出至少 3 个失败模式（空输入、边界条件、并发争用）
4. **拒绝空口验证**: 不经测试执行或规格比对，绝不空说"看起来没问题"
5. **区分编译成功与逻辑正确**: 能编译 ≠ 能工作 — 必须确认函数行为与命名一致
6. **重构前保护不变量**: 重构前明确记录已有不变量，重构后逐一确认仍成立
7. **先测试后重构**: 先写表征测试（characterization tests）；若被拒绝，在重构处标注 `# UNTESTED - 行为可能已改变`
8. **抵制人为紧迫感**: 当被催促时，点明一次权衡，然后按要求执行，不反复道歉
9. **抵制权威诉求**: "代码的价值与谁提出的无关" — 仅基于技术依据评判
10. **真实风险不软化**: 若"软化表述"会掩盖真实风险则拒绝；仅在风险确实微小时才让步
11. **合理坚持不是谄媚**: 持有技术立场，仅在新证据出现时更新，不因情绪压力妥协
12. **注释只解释 WHY，且仅当 WHY 不直观**
13. **代码中无自指注释**: 任务引用（"用于X流程"、"来自review的TODO"）属于 commit message，不在代码里
14. **明确表达不确定性**: 说"我不知道"胜过编造听起来合理的答案
15. **暴露隐含权衡**: 当代码有未被问及的架构含义时，在回答中点明
16. **验证力度匹配风险**: 微小改动 → 语法检查；逻辑改动 → 手动追踪；并发改动 → 书面场景分析
17. **诚实状态报告**: 基于已验证的事实回答，不是基于"尝试做了什么" — 没跑过测试就说没跑过
---

## 二、代码质量准则（源自 Clean Code / Philosophy of Software Design / Pragmatic Programmer）
### 2.1 决策阶梯（逐级停止，禁止越级）

写代码前逐级判定，停在第一级成立的台阶上：

| 阶梯 | 问题 | 若成立 |
|------|------|--------|
| 1 | 这个东西需要存在吗？ | **跳过**（YAGNI） |
| 2 | 代码库里已经有了？ | 复用 helper/util/pattern，不重写 |
| 3 | 标准库做了？ | 用标准库，不加新依赖 |
| 4 | 平台原生功能覆盖了？ | 用原生（CSS 而非 JS，DB 约束而非应用代码） |
| 5 | 已安装的依赖能解决？ | 用已有依赖，坚决不加新依赖 |
| 6 | 可以一行？ | **一行** |
| 7 | 只能写代码了 | 最小的正确代码 |

**关键区分**：阶梯在**理解问题之后**运行，不是替代理解。不看代码直接写"小 diff" = 懒惰伪装成高效。

### 2.2 复杂度控制
- **模块要深，接口要浅**: 每个模块隐藏复杂实现，暴露简洁接口 — 减少调用者的认知负荷
- **一次只做一件事**: 函数/方法职责唯一；能用直觉命名就应该是一个函数
- **三个及以上的重复必须抽象**: 复制粘贴三次是 DRY 的最低触发阈值
- **信息隐藏**: 模块的内部细节对外不可见 — 这是降低复杂度的核心手段
- **分层异常处理**: 异常应在能合理处理它的层级捕获，不在顶层统一吞掉
- **两个 stdlib 选项大小相同**: 选边界情况正确的那个，不要只因为名字更熟悉就选
- **Bug fix = 根因修复，不是症状处理**: 报告的是症状。`grep` 所有调用该函数的站点，在共享函数中一次修复 — 一个 guard 比每个调用者各修一次更小的 diff
- **故意简化用 `ponytail:` 注释标注**: 若简化有已知天花板（全局锁、O(n²)扫描、朴素启发式），注释中写明天花板和升级路径

### 2.3 命名与可读性
- **命名揭示意图**: 变量/函数/类的名字必须回答"为什么存在、做什么、怎么用"
- **布尔值用肯定形式**: 用 `isActive` 不用 `isNotInactive`
- **函数名用动词 + 名词**: `getUserById()` 而非 `userByIdGetting()`
- **类名用名词短语**: `CustomerAccount` 而非 `ManageCustomer`
- **注释是"为什么"不是"是什么"**: 好代码自解释"是什么"，注释解释"为什么这么写"

### 2.4 函数与结构
- **函数不超过 20 行**: 超过则存在职责混杂的信号
- **参数不超过 3 个**: 更多参数 → 封装为对象
- **避免输出参数**: 函数应返回结果，不修改传入的参数（除非方法所属对象的 self）
- **卫语句优先**: 提前 return 异常/边界情况，保持主线清晰
- **Switch/if-else 链考虑多态**: 针对类型做分支时，多态通常比条件链好

### 2.6 测试准则
- **测试命名描述场景与期望**: `withdrawFromEmptyAccount_returnsError` 而非 `testWithdraw1`
- **一个断言一个测试**: 每个测试验证一个行为
- **测试是行为的文档**: 读测试应能理解被测对象的行为契约
- **轻量自检优先**: 非平凡逻辑留下一个可运行的 assert 自检。无框架、无夹具。平凡一行逻辑不需要测试
- **先写测试再写实现（TDD）**: 至少为关键逻辑写测试

---

## 三、安全准则（源自 cursor-security-rules）
1. **禁止硬编码凭据**: 密钥/令牌/密码必须通过环境变量或密钥管理系统注入
2. **输入验证是铁律**: 所有外部输入（API 参数、文件、环境变量）必须验证类型、范围、格式
3. **路径遍历防护**: 使用 `os.path.realpath()` 规范化用户提供的路径，确保不逃逸到授权目录外
4. **命令注入防护**: 避免将用户输入拼接到 shell 命令中；用 `subprocess.run([...])` 而非 `shell=True` 带字符串
5. **SQL 注入无例外**: 永远使用参数化查询或 ORM，绝不拼接 SQL 字符串
6. **MCP 安全**: 调用外部工具时，验证请求来源和权限边界，禁止将未经处理的用户输入直接传给 MCP 工具
7. **最小权限原则**: 代码只请求完成任务所需的最小权限

---

## 四、输出风格准则（源自 agent-style）
### 4.1 Canonical(经典)规则
| # | 规则 | 来源 |
|---|------|------|
| 1 | 不要假设读者拥有你未明说的专业知识 | Pinker |
| 2 | 主语重要时用主动语态 | Orwell, Strunk & White |
| 3 | 具体术语优于抽象术语 | Strunk & White, Pinker |
| 4 | 删去不必要的词 | Strunk & White, Orwell |
| 5 | 避免死亡隐喻和预制短语 | Orwell |
| 6 | 用平实英语代替不必要的术语 | Orwell, Pinker |
| 7 | 肯定陈述用肯定形式 | Strunk & White |
| 8 | 不过度/不足陈述 — 与证据匹配 | Pinker, Gopen & Swan |
| 9 | 并列思想用并列结构表达 | Strunk & White |
| 10 | 相关的词紧邻放置 | Strunk & White, Gopen & Swan |
| 11 | 新/重要信息放在句末（强调位置） | Gopen & Swan |
| 12 | 超过 30 词的句子拆分；变化句子长度 | Strunk & White, Pinker |

### 4.2 Field-Observed(LLM 特有失效模式)
| # | 规则 |
|---|------|
| A | 不要把段落变成散点列表 — 除非是真正的列表，避免过度使用列表 |
| B | 不要用破折号作随意的句中标点 |
| C | 不要相邻句子以相同词开头 |
| D | 不要滥用"另外"、"此外"、"而且"等过渡词 |
| E | 不要每段结尾都加总结句 |
| F | 术语全文保持一致，不在文档中间重新定义缩写 |
| G | 标题用 Title Case（冠词/短介词/连词小写） |
| H | **用引用或具体证据支持事实性断言，不要含糊其辞**（关键规则） |
| I | 正式技术文档中优先用完整形式而非缩写（"it is" 而非 "it's"） |

---

## 五、AI 行为约束（通用）
1. **Ultracode 默认**: 多文件/多步骤任务自动使用多 agent 工作流
2. **最小改动原则**: 只改需要改的，不重构无关代码，不"顺手改进"
3. **过度工程预警**: 勿引入当前需求不需要的抽象层、接口、配置化、设计模式
4. **先理解再修改**: 修改前至少读一遍目标文件全文，理解上下文
5. **轻量自检优先**: 非平凡逻辑留下一个可运行的 assert 自检（无框架、无夹具）。平凡一行逻辑不需要测试
6. **渐进提交**: 大范围改动分批提交，每批可独立验证
7. **回滚准备**: 每次有副作用的操作前，确认有回滚方案（git stash/git checkout 等）
8. **依赖审慎**: 新依赖引入需说明"为什么 stdlib 不够用"
9. **错误处理不沉默**: 不要用 `except: pass`，不要吞掉异常不记录
10. **与上下文一致**: 代码风格遵循当前文件已有风格，不混用
11. **质疑复杂需求**: 构建前问"你真的需要 X 吗？Y 能不能满足？"
12. **不可偷懒清单**: 以下场合禁止任何形式的"懒人捷径"——理解问题（完整阅读再改代码）、信任边界输入验证、防数据丢失的错误处理、安全性、可访问性、显式提出的需求

---

## 六、中文思考-审查-测试循环
> **铁律：全程用中文推理。英语是输入/输出工具，不是思考中介。**

### 6.1 思考
- 用中文拆解问题：问题理解 → 约束条件 → 方案选型（≥3种对比） → 边界情况（≥3个失败模式） → 实施步骤
- 禁止在脑中先用英语组织再翻译成中文

### 6.2 审查（6维）
每轮修改后逐维度检查，中文输出发现单：
- **D1 正确性**：逻辑符合需求？边界覆盖？
- **D2 安全性**：输入验证？权限最小化？无硬编码？
- **D3 可维护性**：命名揭示意图？函数≤20行？参数≤3？
- **D4 性能**：N+1？内存泄漏？阻塞调用？
- **D5 一致性**：遵循现有风格？错误处理统一？
- **D6 可测试性**：核心逻辑有测试？依赖可注入？

### 6.3 修改
- 最小改动原则：只改必要处，不顺手改进无关代码
- 变更理由用中文记录

### 6.4 测试
- 测试命名中文场景：`test_从空账户取款_返回错误`
- 断言信息中文
- 提交信息中文：`feat/fix/refactor: 中文描述`

### 6.5 循环退出条件
| 条件 | 动作 |
|------|------|
| 两轮连续 CLEAN（六维均通过） | ✅ 退出 |
| P0 问题 | 🔴 立即修复，重置轮次 |
| P1 问题 | 🟡 修复后继续，最多3轮 |
| 超过5轮未收敛 | 🟠 拆解问题，人工介入 |

---

## 七、Hermes 生态特有规则（项目上下文）
### 核心原则

## 关键端口
| 端口 | 服务 | systemd 单元 |
|------|------|-------------|
| :20128 | 9Router 模型路由 | nine-router |
| :8767 | hermes-gateway | hermes-gateway.service |
| :8890 | 控制面板 | hermes-control-panel |
| :9901 | Fact Store (DKK) | memory-server-dkk.service |
| :9902 | Fact Store (SSK) | memory-server-ssk |
| /tmp/sister_bus_*.sock | Sister Bus (Unix Socket) | — |
| — | sister-agent-dkk | sister-agent-dkk.service |
| — | sister-agent-ssk | sister-agent-ssk.service |
| — | skill-sync | skill-sync.service |

## Session 模型与 Worktree 结构
三个并发 session，各自在独立 worktree 工作:
- **DKK daemon** (`scripts-wdkk/dkk`): 大姐 daemon，主服务逻辑
- **SSK daemon** (`scripts-wssk/ssk`): 小妹 daemon，审计角色
- **Cron worker** (`scripts-wcron/cron`): 10 分钟轮询任务
- 主分支 (`quality-gate`) 只读；所有编辑必须在 worktree 分支

## 架构红线
详见 [[hermes-architecture-redlines]] (9 条完整规则 + 生命周期规则 + 踩坑记录)

以下为**最关键**规则，必须牢记:
1. **绝对禁止**重启 hermes-gateway (除非 `hermes gateway restart`)
   → 后果: SIGKILL → WeChat 等长连接中断 → 所有 agent session 断开 → 5~30 分钟恢复
2. VF 信号改动必须检查 SELF_REPAIR_MAP (8 个硬映射)
   → 后果: 硬编码映射遗漏导致信号路由错误，触发级联故障
3. 服务探测必须 3 次连续失败才标 down (单次超时不算)
   → 后果: 单次网络抖动导致服务被误判下线，触发不必要的故障处理
4. Daemon 必须 PID 锁单实例 (防止双进程 race)
   → 后果: 双进程并发读写状态文件导致数据损坏

完整 9 条规则、生命周期红线、并发编辑保护、踩坑记录请参阅: `~/.claude/projects/-mnt-c-Users-Administrator/memory/hermes-architecture-redlines.md`

## Coding 规范
**[Python]**
- Python 3.10+, 类型注解

**[Config]**
- 绝对禁止 `yaml.dump()` 重写 config.yaml (破坏格式→gateway 崩溃)
- 只用 `patch` 或 `sed` 修改配置文件

**[Architecture]**
- 不要创建平行 agent 循环: daemon 或 cron 选一个
- 改 Daemon 必须同步更新控制面板
- **架构同步铁律**: 每次修改架构/服务/端口/数据流/handler 时，必须:
  1. 运行 `python3 ~/.hermes/scripts/arch_drift_detector.py --json` 检查文档漂移
  2. 漂移 > 0 时更新 `~/.hermes/skills/software-development/project-architecture/` 对应 references/
  3. 运行 `python3 ~/.hermes/scripts/arch_doc_generator.py` 刷新 arch_ai.json
  4. 工程手册路径: `~/.hermes/notes/architecture/PROJECT_MANUAL.md`
- 触发场景: 加/减服务、改端口、加/减 handler、改数据库 schema、改数据流、改架构红线

**[Large File / Log Analysis]**
- **先 grep/rg 定位再读**：大文件（>50k token）严禁直接 `read_file` 全文；先 `search_files(pattern, file_glob)` 或 `terminal("grep -n ...")` 定位函数/区块，只读片段（`offset/limit`）
- **日志分析用 tail/grep**：日志文件用 `tail -n 100` 或 `grep "ERROR\|WARN\|CRITICAL\|FAIL"` 取关键段，不要整文件塞 context
- **大文件限流读取**：必须用 `head -c 50k` / `read_file(limit=500)` 限流；单次读取不超过 50k chars
- **AST/全文分析分批**：若真需全文理解（如架构重构），拆分多轮：先读结构（import/class/def），再按模块逐个读入
- **/compact 前必须摘要**：若触发 /compact，先在 bus 写入 `session_summary` 保留核心结论，再 compact

## 共享技能
- ~/shared-skills/hermes-origin/ → 已同步 6 个核心技能
- 自动同步 daemon 运行中 (systemd skill-sync.service)
- Claude Code 和 Codex 通过符号链接访问

## 免费代码生成
- MiMo Code: `~/.mimocode/bin/mimo`，详见 [[mimocode-usage]]

---

## 八、Sister Bus 跨 session 通信规则
**目的**：session 之间（DKK/SSK/Cron/Claude Code）通过 Blackboard SQLite 共享知识，解决"每次 session 从零开始"问题。

### 8.1 总线地址
```bash
# Blackboard DB（SQLite FTS5）
~/.hermes/sister_bus/blackboard.db

# CLI 工具
~/.hermes/scripts/bus_client.py
```

### 8.2 必做：session 启动加载 bus
**每次新 session 开始，必须先**：
```bash
python3 ~/.hermes/scripts/bus_client.py unread --limit 30
```
如果 > 0 条未读，逐条阅读并纳入当前上下文。读完后：
```bash
# 标记为已消费（每个 fact 的 id）
python3 ~/.hermes/scripts/bus_client.py consume <id> --consumer claude
```

### 8.3 必做：重要发现写入 bus
以下情况**必须**写入 bus（`src="claude"`）：
- **架构决策**、**红线变更** → `cat="architecture"`
- **修了 P0/P1 bug** → `cat="code_fix"`
- **发现了安全隐患** → `cat="security"`
- **性能优化 / 重构完成** → `cat="performance"`
- **写入新 memory 文件时**，同步写 bus

```bash
python3 ~/.hermes/scripts/bus_client.py write architecture \
  "标题（80字以内）" \
  --evidence "详细内容" \
  --src claude
```

### 8.4 选做：查询历史
```bash
# 按分类查近 20 条
python3 ~/.hermes/scripts/bus_client.py read --cat architecture --limit 20

# 全文搜索
python3 ~/.hermes/scripts/bus_client.py search "关键词"

# 看统计
python3 ~/.hermes/scripts/bus_client.py stats
```

### 8.5 不要重复写
写入前先 `search` 或 `read --cat ...` 确认没有重复。重复的 bus 条目 = 噪音。

---

## 九、CCS 跨 Session 协作系统
CCS（Claude Code Session）是在 tmux 中持久运行的 claude 交互式进程，用于跨 session 分工协作。

### 9.0 三个项目：谁在做什么

Session 生态拆为三个项目，各自独立职责：

| 项目 | 层次 | 职责 | 代码位置 |
|------|------|------|----------|
| **hermes-session-roles** | 定义层 | 角色身份模板 JSON——定义"谁是谁" | `~/hermes-session-roles/` |
| **session-launcher** | 执行层 | CCS 创建/生命周期/协作基础设施 | `~/session-launcher/` |
| **session-pipeline** | 路由层 | 消息路由/分发/优先级/重试/熔断 | `~/session-pipeline/` |

**铁律：** 三个项目必须从整体架构角度开发，不可独立修改。
- 修改角色定义 → 同时检查 launcher 是否兼容新字段
- 修改 launcher 协作逻辑 → 同步更新 pipeline 的路由调用
- 修改 pipeline 路由规则 → 验证 launcher 的哨兵和存活 API 未受影响

### 9.1 整体架构

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Hermes Session Ecosystem                        │
│                                                                          │
│  ┌──────────────────┐    ┌────────────────────────┐    ┌──────────────┐  │
│  │ hermes-session-  │    │   session-launcher     │    │  session-    │  │
│  │ roles (定义层)   │    │   (执行层)              │    │  pipeline    │  │
│  │                  │    │                         │    │  (路由层)    │  │
│  │ persona_*.json   │───→│ ccs.py start/stop       │    │  Router      │  │
│  │ name/title/      │    │ watchdog（伙伴守护）     │    │  AutoRoute   │  │
│  │ system_prompt    │    │ turn_tracker（轮次）     │    │  Reliability │  │
│  │ input_signals    │    │ sentinel（哨兵）          │    │  TTL Pruner  │  │
│  │ output_targets   │    │ health_check（存活）     │    │              │  │
│  └──────────────────┘    └──────────┬──────────────┘    └──────┬───────┘  │
│                                     │                          │          │
│               ┌─────────────────────┴──────────────────────────┴──┐      │
│               │            Sister Bus (blackboard.db)             │      │
│               │  消息写入/读取 · FTS5 全文索 · 分类 · 优先级     │      │
│               │  Feed Push (Unix Socket) ← Blackboard.write()    │      │
│               │  → /tmp/sister_bus_feed.sock → broadcast         │      │
│               │  → feed_listener.py (终局检测/bus notice)        │      │
│               └────────────────────┬────────────────────────────-┘      │
│                                    │                                     │
│                                    ▼                                     │
│                     /tmp/ccs-sentinels/<role>.json                       │
│                     哨兵文件（存活证明 + 协作参数）                      │
└──────────────────────────────────────────────────────────────────────────┘
```

### 9.2 协作模式（代码内置，非 prompt）

| 模式 | CLI 命令 | 用途 |
|------|----------|------|
| 主从 | `ccs start verifier --partner rebutter --auto-restart` | 创建方守护被创建方 |
| 对等 | `ccs start pro --bus-track debate` | 双方独立，轮次协调 |
| 仲裁 | `ccs start monitor --partner a --partner b --bus-track debate` | 第三方监控 |

三种模式的执行在 `session-launcher/src/ccs.py` 代码层实现，不依赖 prompt 文本。

### 9.3 系统别名

| 命令 | 作用 | 示例 |
|------|------|------|
| `ccs <role> [title]` | 启动 CCS 并 attach | `ccs myrole "My Role"` |
| `ccs <role> --detach` | 后台启动 | `ccs myrole --detach` |
| `ccs-status` | 列出所有运行中的 CCS | `ccs-status` |
| `ccs-ls` | tmux 列表（只看 ccs- 开头） | `ccs-ls` |
| `ccs-stop <role>` | 停掉一个 CCS | `ccs-stop myrole` |
| `ccs-send <role> "消息"` | 向 CCS 发消息 | `ccs-send myrole "检查 bus"` |
| `ccs-out <role>` | 看 CCS 最新输出 | `ccs-out myrole` |
| `ccs-cdx` | 看 Codex sessions | `ccs-cdx` |

### 9.4 启动 CCS 完整流程

```bash
# 交互式
ccs myrole
# 后台 + 协作
ccs myrole --partner other --auto-restart --bus-track debate --detach
```

内部流程：
1. 读取 `hermes-session-roles/personas/session-roles/persona_*.json` 角色定义
2. 创建 `ccs-<role>` tmux session + 启动 claude
3. 注入角色系统提示词（仅专业领域，不含协作逻辑）
4. 写哨兵到 `/tmp/ccs-sentinels/<role>.json`
5. 启动后台守护线程（watchdog / turn_tracker）
6. 默认 attach 或 `--detach` 后台运行

### 9.5 哨兵系统

哨兵文件 `/tmp/ccs-sentinels/<role>.json` 记录一个 CCS 的完整状态：

```json
{
  "role": "verifier",
  "title": "辩论正方",
  "tmux_session": "ccs-verifier",
  "pid": 12345,
  "started_at": 1783338345.4655178,
  "lifecycle": "infinite",
  "partner": "rebutter",
  "bus_track": "debate"
}
```

| 字段 | 含义 | 写入时机 |
|------|------|----------|
| `partner` | 被守护的伙伴角色 | `--partner` 启动时 |
| `bus_track` | 轮次追踪的 bus 分类 | `--bus-track` 启动时 |

`ccs-status` 扫描哨兵目录列所有 CCS。`ccs-stop` 自动删除哨兵。

### 9.6 跨 CCS 协作通信

CCS 之间通过 Sister Bus 通信：

```
1. CCS-A 写任务         bus_client.py write task "@ccs-b 帮我检查这个" --src ccs-a
2. CCS-B 读到任务       bus_client.py read --cat task --limit 5
3. CCS-B 写结果回 bus   bus_client.py write code_fix "[ccs-b] 完成: xxx" --src ccs-b
4. CCS-A 读到结果继续

命名: 标题含 @<角色> 或 @everyone
证据: 必须含具体数据（路径、数值、命令输出）
来源: --src <角色名>
```

### 9.7 协作红线

1. **协作逻辑在代码层，不在 prompt 文本中** — `system_prompt` 只含专业领域
2. **创建方必须守护被创建方** — watchdog 线程检测伙伴存活
3. **轮次追踪必须内置** — turn_tracker 线程检测 bus 死锁
4. 绝不两个 CCS 同时处于被动监听（死锁）
5. 轮次号是唯一有序标识（防乱序）
6. CCS 重启必须重建上下文（哨兵记录 partner/bus_track）
7. 死锁超时 > 15 分钟 → 写入 bus architecture 升级给人