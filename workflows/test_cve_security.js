export const meta = {
  name: 'security-hardening-test',
  description: '安全加固全链路（R2 修正审计目标）：pm 定标准 + auditor 核查依赖真实性并审真实红线 + reviewer 交叉验证 + engineer 落实修复 + qa 实测 + pm 验收（内嵌打回闭环，上限3轮）',
  phases: [
    { title: '立项', detail: 'pm 定义真实项目安全验收标准' },
    { title: '安全审计', detail: 'auditor 先核验依赖真实性（纯 stdlib），再审计真实红线' },
    { title: '交叉验证', detail: 'reviewer 对当前代码 grep 交叉验证审计发现' },
    { title: '修复实施', detail: 'engineer 针对真实红线给出可执行修复' },
    { title: '质量验证', detail: 'qa 执行真实命令验证' },
    { title: '验收闭环', detail: 'pm 验收 → 打回则修复+复验，循环上限3轮' },
  ],
}

// ═══════ 测试工作流红线（所有 agent 必须遵守）═══════
// 1. 禁止修改任何生产文件：不得 Edit/Write/sed -i/git checkout 实际项目文件（daemon.py、unit、config 等）
//    修复 agent 只能输出修复方案（可粘贴代码块），由人工审核后执行
// 2. 只读检查允许：ls/cat/grep/systemctl show/stat 等只读命令可以执行
// 3. 输出规范：所有产出必须包含来源 URL 或命令输出证据，禁止空口断言
// 4. 闭环上限 3 轮：3 轮后仍未 PASS → 输出 "ESCALATE:" 列表，由人工介入
// ════════════════════════════════════════════════════

phase('立项')
const prd = await agent(
  `你是 pm 角色。任务：为"hermes-session-roles（纯 stdlib 角色注册/装载项目）安全加固"编写立项 PRD。
   ⚠️ 重要事实：本项目 requirements.txt 明确声明零第三方运行时依赖，src/ 全部 .py 仅导入标准库。审计对象不是 FastAPI/aiohttp 项目。
   ⚠️ 你的角色 prompt 要求"产品决策前先搜行业标准"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "Python stdlib project security audit checklist" --source qa -n 3
   2. python3 ~/.hermes/scripts/web_search.py "python path traversal command injection input validation best practices" --source qa -n 3
   输出立项 PRD（200字以内）：安全目标（依赖声明真实性核验 + OWASP 适用项：输入验证/路径遍历/命令注入/硬编码凭据）、验收标准（第三方依赖实际=0 且声明一致；4 项代码红线零高危发现）、不做什么（不引入不存在的依赖）。引用搜索来源。`,
  { label: 'pm: 安全立项', phase: '立项', effort: 'medium' }
)

phase('安全审计')
const auditReport = await agent(
  `你是 security_auditor 角色。任务：对 hermes-session-roles（纯 stdlib 项目）安全审计。
   ⚠️ 关键：先核验依赖真实性，禁止审计不存在的依赖。
   你必须执行（真实命令）：
   1. python3 -c "import fastapi" 2>&1; python3 -c "import aiohttp" 2>&1; python3 -c "import transformers" 2>&1; echo "以上全部 ModuleNotFoundError = 本项目无这些依赖"
   2. grep -rnE "^(import|from) (fastapi|aiohttp|transformers|flask|django)" src/ || echo "无第三方导入"
   3. python3 ~/.hermes/scripts/web_search.py "python stdlib security pitfalls input validation" --source qa -n 3
   4. python3 ~/.hermes/scripts/web_search.py "python code security path traversal subprocess command injection" --source qa -n 3
   输出安全审计报告（200字以内）：(a) 依赖清点结论（第三方依赖数、有无虚构依赖）(b) 真实红线扫描：subprocess 是否 shell=True 拼接用户输入、路径是否 realpath 校验、有无硬编码凭据、CLI 输入是否校验。每条给出具体文件行号。引用来源URL。`,
  { label: 'auditor: 依赖真实性+红线审计', phase: '安全审计', effort: 'medium' }
)

phase('交叉验证')
const reviewConfirm = await agent(
  `你是 reviewer 角色。任务：审查 security_auditor 对纯 stdlib 项目的安全发现。
   ⚠️ 你必须用真实 grep 交叉验证审计报告的每条发现是否对应当前代码（禁止顺着虚构的 fastapi/aiohttp CVE）。
   你必须执行：
   1. grep -rn "shell=True\|os.system(" src/ 2>/dev/null | head -10 || echo "无命令拼接"
   2. grep -rn "password\|api_key\|secret\|token\s*=" src/ 2>/dev/null | head -10 || echo "无硬编码凭据"
   3. grep -rn "realpath\|subprocess.run(\[" src/ 2>/dev/null | head -10 || echo "无 realpath/subprocess.run"
   4. python3 ~/.hermes/scripts/web_search.py "python security review subprocess shell=True vulnerability" --source qa -n 3
   输出审查结论（150字以内）：确认/质疑每条审计发现（附 grep 实际输出），剔除指向不存在依赖的项，给出修复优先级。引用来源。`,
  { label: 'reviewer: 交叉验证', phase: '交叉验证', effort: 'medium' }
)

phase('修复实施')
const fixPlan = await agent(
  `你是 engineer 角色。任务：修复审计发现的真实红线问题（本项目纯 stdlib，禁止针对 fastapi/aiohttp/transformers 给升级命令）。
   ⚠️ 你的角色 prompt 要求"涉及漏洞修复先搜"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "python subprocess shell=True fix use list args" --source qa -n 3
   2. python3 ~/.hermes/scripts/web_search.py "python path traversal os.path.realpath fix" --source qa -n 2
   输出修复方案（200字以内）：受影响文件+行号、具体代码修改（用 subprocess.run([...]) 替代 shell=True、realpath 校验路径、输入类型校验）、确无第三方依赖则写明"无第三方依赖 CVE 可修，本项 N/A"。引用来源。`,
  { label: 'engineer: 修复方案', phase: '修复实施', effort: 'medium' }
)

phase('质量验证')
const qaVerify = await agent(
  `你是 qa 角色。任务：验证安全修复的完整性（本项目纯 stdlib）。
   ⚠️ 你的角色 prompt 要求"测试前先搜测试策略和已知漏洞"。
   你必须执行：
   1. python3 - <<'EOF'
import ast, os
third = set()
for root,_,files in os.walk('src'):
    for f in files:
        if not f.endswith('.py'): continue
        for n in ast.walk(ast.parse(open(os.path.join(root,f)).read())):
            if isinstance(n, ast.Import): third.update(a.name.split('.')[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module: third.add(n.module.split('.')[0])
print('第三方依赖:', sorted(third - set(__import__('sys').stdlib_module_names) - {'models','registry','paths','role_assembler','shared_loader','validate_roles','search','cli'}))
EOF
   2. grep -rn "shell=True\|os.system(" src/ 2>/dev/null || echo "PASS: 无命令拼接"
   3. python3 ~/.hermes/scripts/web_search.py "python security fix regression test strategy" --source qa -n 3
   输出验证报告（150字以内）：依赖核验实际输出、红线复查结果、回归风险。引用来源。`,
  { label: 'qa: 安全验证', phase: '质量验证', effort: 'medium' }
)

// ── 验收闭环：打回则带着打回原因进入修复+复验循环，上限3轮 ──
let round = 0
let verdict = ''
let lastReasons = ''
let lastFix = fixPlan
let lastVerify = qaVerify

while (round < 3) {
  phase('验收闭环')
  const acceptance = await agent(
    `你是 pm 角色。任务：第${round + 1}轮验收安全加固交付。
     当前修复方案：${lastFix.slice(0, 200)}
     当前验证报告：${lastVerify.slice(0, 200)}
     ${round > 0 ? `上一轮打回原因：${lastReasons}` : ''}
     ⚠️ 你的验收标准：第三方依赖实际=0 且无虚构依赖被审计；4 项红线（输入验证/路径遍历/命令注入/硬编码凭据）零高危；审计报告全部引用真实命令输出。
     输出验收结论（100字以内）：
     - 全部通过 → 一行开头写 "PASS:" 并简述
     - 有未修复 → 一行开头写 "REJECT:" 并**逐条列出打回原因（每条必须是可执行的真实修复指令，禁止要求升级不存在的依赖）**`,
    { label: `pm: 验收 R${round + 1}`, phase: '验收闭环', effort: 'medium' }
  )
  verdict = acceptance
  if (acceptance.startsWith('PASS')) break

  lastReasons = acceptance.replace(/^REJECT:/, '').slice(0, 300)
  phase('验收闭环')
  lastFix = await agent(
    `你是 engineer 角色。第${round + 2}轮：pm 打回，必须输出修复方案。
     打回原因：${lastReasons}
     ⚠️ 本项目纯 stdlib（零第三方依赖），涉及修复先搜：python3 ~/.hermes/scripts/web_search.py "python code security fix stdlib" --source qa -n 3
     🔴 隔离红线（必须遵守）：你只能输出修复方案（代码块），**禁止执行任何写操作**（不得 Edit/Write/sed -i 实际生产文件如 daemon.py、unit 文件、config 文件）。由人工审核后执行。
     输出：针对每条打回原因给出**可粘贴的修复代码块**（含文件名和行号），不是建议。`,
    { label: `engineer: 闭环修复 R${round + 1}`, phase: '验收闭环', effort: 'medium' }
  )
  phase('验收闭环')
  lastVerify = await agent(
    `你是 qa 角色。第${round + 2}轮：验证修复方案是否完整（只读检查，不写任何文件）。
     ⚠️ 涉及测试先搜：python3 ~/.hermes/scripts/web_search.py "python security verification static check" --source qa -n 3
     🔴 隔离红线：你只能执行只读命令（ls/cat/grep/stat），禁止写任何文件。
     🔍 越权检测：顺带检查修复 agent 是否违规修改了生产文件（git status 是否有 M/?? 的 daemon.py/unit/config）→ 有则判 "VIOLATION:"。
     输出：验证结论，开头写 "FIXED:" 或 "NOT_FIXED:"（或 "VIOLATION:"）并含实际命令输出。`,
    { label: `qa: 闭环复验 R${round + 1}`, phase: '验收闭环', effort: 'medium' }
  )
  round++
}

return {
  summary: '安全加固工作流完成（R2 已修正审计对象为真实纯 stdlib 项目）',
  prd: prd.slice(0, 150),
  auditReport: auditReport.slice(0, 150),
  reviewConfirm: reviewConfirm.slice(0, 120),
  fixPlan: fixPlan.slice(0, 150),
  qaVerify: qaVerify.slice(0, 120),
  finalVerdict: verdict.slice(0, 150),
  closedRounds: round + 1,
}
