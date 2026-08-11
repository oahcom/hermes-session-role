export const meta = {
  name: 'monitor-recovery-test',
  description: '监控告警全链路：pm 定 SLA + maintainer/engineer 搜索 + qa 验证 + pm 验收（内嵌打回闭环，上限3轮）',
  phases: [
    { title: '立项', detail: 'pm 定义告警 SLA 与验收' },
    { title: '故障诊断', detail: 'maintainer 搜已知故障' },
    { title: '修复实施', detail: 'engineer 搜修复方案' },
    { title: '质量验证', detail: 'qa 搜验证策略' },
    { title: '验收闭环', detail: 'pm 验收 → 打回则修复+复验，循环上限3轮' },
  ],
}

phase('立项')
const prd = await agent(
  `你是 pm 角色。任务：为"systemd 服务告警响应流程"编写立项 PRD。
   ⚠️ 你的角色 prompt 要求"产品决策前先搜行业标准"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "SLA monitoring alert response best practices" -n 3
   2. python3 ~/.hermes/scripts/web_search.py "systemd service monitoring best practices" --source code -n 3
   输出立项 PRD（150字以内）：告警 SLA（MTTD/MTTR 目标）、升级路径、验收标准。引用搜索来源。`,
  { label: 'pm: 告警立项', phase: '立项', effort: 'medium' }
)

phase('故障诊断')
const diag = await agent(
  `你是 maintainer 角色。任务：诊断 systemd 服务反复重启故障。
   ⚠️ 你的角色 prompt 要求"收到服务告警先搜已知故障"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "systemd service restart loop fix" --source qa -n 3
   2. python3 ~/.hermes/scripts/web_search.py "systemd service failed exit status" --source qa -n 3
   输出故障诊断报告（150字以内）：可能根因、排查命令、社区已知修复。引用来源。`,
  { label: 'maintainer: 故障诊断', phase: '故障诊断', effort: 'medium' }
)

phase('修复实施')
const fix = await agent(
  `你是 engineer 角色。任务：实现 systemd 服务修复。
   ⚠️ 你的角色 prompt 要求"涉及 bug 先搜"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "systemd Restart=always loop prevention" --source qa -n 3
   2. python3 ~/.hermes/scripts/web_search.py "systemd watchdog configure" --source qa -n 2
   输出修复方案（150字以内）：unit 配置修改、watchdog 设置、自愈策略。引用来源。`,
  { label: 'engineer: 修复方案', phase: '修复实施', effort: 'medium' }
)

phase('质量验证')
const qaVerify = await agent(
  `你是 qa 角色。任务：验证 systemd 修复的可靠性。
   ⚠️ 你的角色 prompt 要求"测试前先搜测试策略"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "systemd unit test failure recovery" --source qa -n 3
   2. python3 ~/.hermes/scripts/web_search.py "systemd restart verification test" --source qa -n 2
   输出验证报告（150字以内）：重启测试方案、Watchdog 验证方法、回归风险。引用来源。`,
  { label: 'qa: 修复验证', phase: '质量验证', effort: 'medium' }
)

// ── 验收闭环：打回则带着打回原因进入修复+复验循环，上限3轮 ──
let round = 0
let verdict = ''
let lastReasons = ''
let lastFix = fix
let lastVerify = qaVerify

while (round < 3) {
  phase('验收闭环')
  const acceptance = await agent(
    `你是 pm 角色。任务：第${round + 1}轮验收告警响应流程。
     当前修复方案：${lastFix.slice(0, 200)}
     当前验证报告：${lastVerify.slice(0, 200)}
     ${round > 0 ? `上一轮打回原因：${lastReasons}` : ''}
     ⚠️ 你的验收标准：MTTR < 15min、重启循环消除、watchdog 生效。
     输出验收结论（100字以内）：
     - 全部通过 → 一行开头写 "PASS:" 并简述
     - 有未修复 → 一行开头写 "REJECT:" 并**逐条列出打回原因（每条必须是可执行的修复指令）**`,
    { label: `pm: 验收 R${round + 1}`, phase: '验收闭环', effort: 'medium' }
  )
  verdict = acceptance
  if (acceptance.startsWith('PASS')) break

  lastReasons = acceptance.replace(/^REJECT:/, '').slice(0, 300)
  phase('验收闭环')
  lastFix = await agent(
    `你是 engineer 角色。第${round + 2}轮：pm 打回，必须落实修复。
     打回原因：${lastReasons}
     ⚠️ 涉及修复先搜：python3 ~/.hermes/scripts/web_search.py "systemd watchdog sd_notify python" --source qa -n 3
     输出：针对每条打回原因给出**可执行命令/配置修改**（可粘贴代码），不是建议。`,
    { label: `engineer: 闭环修复 R${round + 1}`, phase: '验收闭环', effort: 'medium' }
  )
  phase('验收闭环')
  lastVerify = await agent(
    `你是 qa 角色。第${round + 2}轮：验证修复是否真正落地（执行真实命令确认，不是描述）。
     ⚠️ 涉及测试先搜：python3 ~/.hermes/scripts/web_search.py "systemd watchdog test" --source qa -n 3
     输出：验证结论，开头写 "FIXED:" 或 "NOT_FIXED:" 并含实际命令输出。`,
    { label: `qa: 闭环复验 R${round + 1}`, phase: '验收闭环', effort: 'medium' }
  )
  round++
}

return {
  summary: '监控告警工作流完成（内嵌闭环）',
  prd: prd.slice(0, 150),
  diag: diag.slice(0, 150),
  fix: fix.slice(0, 150),
  qaVerify: qaVerify.slice(0, 150),
  finalVerdict: verdict.slice(0, 150),
  closedRounds: round + 1,
}
