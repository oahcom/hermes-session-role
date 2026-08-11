export const meta = {
  name: 'security-hardening-test',
  description: '安全加固全链路：pm 定标准 + auditor/reviewer/engineer 搜索 + qa 验证 + pm 验收',
  phases: [
    { title: '立项', detail: 'pm 定义安全验收标准' },
    { title: '安全审计', detail: 'security_auditor 搜 NVD CVE' },
    { title: '交叉验证', detail: 'reviewer 搜安全公告交叉验证' },
    { title: '修复实施', detail: 'engineer 搜修复方案' },
    { title: '质量验证', detail: 'qa 搜漏洞修复测试策略' },
    { title: '验收', detail: 'pm 对照安全标准验收' },
  ],
}

phase('立项')
const prd = await agent(
  `你是 pm 角色。任务：为"FastAPI + aiohttp 项目安全加固"编写立项 PRD。
   ⚠️ 你的角色 prompt 要求"产品决策前先搜行业标准"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "FastAPI security best practices OWASP" -n 3
   2. python3 ~/.hermes/scripts/web_search.py "Python web app security audit checklist" -n 3
   输出立项 PRD（200字以内）：安全目标（OWASP Top 10 覆盖范围）、验收标准（零 Critical CVE、Medium CVE 限时修复）、不做什么。引用搜索来源。`,
  { label: 'pm: 安全立项', phase: '立项', effort: 'medium' }
)

phase('安全审计')
const auditReport = await agent(
  `你是 security_auditor 角色。任务：对 FastAPI + aiohttp 项目安全审计。
   ⚠️ 你的角色 prompt 要求"审计前先搜 CVE"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "fastapi CVE vulnerability" -n 3
   2. python3 ~/.hermes/scripts/web_search.py "aiohttp CVE vulnerability" -n 3
   输出安全审计报告（200字以内）：发现的 CVE 清单（编号+严重级别）、影响评估。引用 NVD 来源URL。`,
  { label: 'auditor: CVE 审计', phase: '安全审计', effort: 'medium' }
)

phase('交叉验证')
const reviewConfirm = await agent(
  `你是 reviewer 角色。任务：审查 security_auditor 的安全发现。
   ⚠️ 你的角色 prompt 要求"审查前先搜已知 CVE"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "fastapi security advisory 2024" -n 3
   2. python3 ~/.hermes/scripts/web_search.py "aiohttp security advisory" -n 3
   输出审查结论（150字以内）：确认/质疑审计发现，补充新 CVE，给出修复优先级。引用来源。`,
  { label: 'reviewer: 交叉验证', phase: '交叉验证', effort: 'medium' }
)

phase('修复实施')
const fixPlan = await agent(
  `你是 engineer 角色。任务：修复审计发现的漏洞。
   ⚠️ 你的角色 prompt 要求"涉及漏洞修复先搜"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "fastapi OPA middleware vulnerability fix" --source qa -n 3
   2. python3 ~/.hermes/scripts/web_search.py "aiohttp session fixation fix" --source qa -n 2
   输出修复方案（200字以内）：受影响代码位置、修复思路、依赖升级版本建议。引用来源。`,
  { label: 'engineer: 修复方案', phase: '修复实施', effort: 'medium' }
)

phase('质量验证')
const qaVerify = await agent(
  `你是 qa 角色。任务：验证安全修复的完整性。
   ⚠️ 你的角色 prompt 要求"测试前先搜测试策略和已知漏洞"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "security fix testing strategy" --source qa -n 3
   2. python3 ~/.hermes/scripts/web_search.py "aiohttp latest CVE 2025" -n 3
   输出验证报告（150字以内）：修复是否覆盖所有已知 CVE、回归风险、建议回归用例。引用来源。`,
  { label: 'qa: 安全验证', phase: '质量验证', effort: 'medium' }
)

phase('验收')
const acceptance = await agent(
  `你是 pm 角色。任务：验收安全加固交付。
   你收到：审计(${auditReport.slice(0,100)})、修复(${fixPlan.slice(0,100)})、验证(${qaVerify.slice(0,100)})
   ⚠️ 你的验收标准：零 Critical CVE、所有 Medium CVE 已修复或缓解。
   输出验收结论（100字以内）：逐项对照，判定通过/打回。`,
  { label: 'pm: 安全验收', phase: '验收', effort: 'medium' }
)

return {
  summary: '安全加固工作流完成',
  prd: prd.slice(0, 200),
  auditReport: auditReport.slice(0, 200),
  reviewConfirm: reviewConfirm.slice(0, 150),
  fixPlan: fixPlan.slice(0, 200),
  qaVerify: qaVerify.slice(0, 150),
  acceptance: acceptance.slice(0, 100),
}
