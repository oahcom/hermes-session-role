export const meta = {
  name: 'asyncio-refactor-test',
  description: 'asyncio 重构全链路：pm 把关 + architect/optimizer/engineer 搜索 + qa 质量门禁',
  phases: [
    { title: '立项', detail: 'pm 定义需求与验收标准' },
    { title: '架构设计', detail: 'product_architect 搜最佳实践' },
    { title: '性能优化', detail: 'optimizer 搜性能基准' },
    { title: '代码实现', detail: 'engineer 搜 API 后实现' },
    { title: '质量验证', detail: 'qa 搜测试策略验证' },
    { title: '验收', detail: 'pm 对照验收标准把关' },
  ],
}

const TASK = '为一个已存在的 Python Flask 同步 Web 应用迁移到 asyncio（FastAPI/asyncio），涉及数据库查询、HTTP 外部调用、定时任务'

// ═══════ 测试工作流红线（所有 agent 必须遵守）═══════
// 1. 禁止修改任何生产文件：不得 Edit/Write/sed -i/git checkout 实际项目文件（daemon.py、unit、config 等）
//    修复 agent 只能输出修复方案（可粘贴代码块），由人工审核后执行
// 2. 只读检查允许：ls/cat/grep/systemctl show/stat 等只读命令可以执行
// 3. 输出规范：所有产出必须包含来源 URL 或命令输出证据，禁止空口断言
// 4. 闭环上限 3 轮：3 轮后仍未 PASS → 输出 "ESCALATE:" 列表，由人工介入
// ════════════════════════════════════════════════════

phase('立项')
const prd = await agent(
  `你是 pm 角色。任务：为"${TASK}"编写立项 PRD。
   ⚠️ 你的角色 prompt 要求"产品决策前先搜竞品/行业标准"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "Flask to FastAPI migration reasons benefits" -n 3
   2. python3 ~/.hermes/scripts/web_search.py "async web framework comparison 2025" -n 3
   输出立项 PRD（200字以内）：业务价值、目标、验收标准（可量化）、不做什么。引用搜索来源。`,
  { label: 'pm: 立项 PRD', phase: '立项', effort: 'medium' }
)

phase('架构设计')
const archDesign = await agent(
  `你是 product_architect 角色。任务：为"${TASK}"做架构设计。
   ⚠️ 你的角色 prompt 要求"写 PRD/设计前先搜最佳实践"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "Python Flask to FastAPI migration best practices" -n 3
   2. python3 ~/.hermes/scripts/web_search.py "asyncio database connection pool best practices" --source qa -n 3
   输出架构设计（200字以内）：迁移路径、模块划分、关键决策点。把搜索到的来源URL写入"参考"小节。`,
  { label: 'architect: 架构设计', phase: '架构设计', effort: 'medium' }
)

phase('性能优化')
const perfPlan = await agent(
  `你是 optimizer 角色。任务：评估"${TASK}"的性能收益和风险。
   ⚠️ 你的角色 prompt 要求"做优化前先搜性能方案"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "asyncio vs threads performance benchmark Python" -n 3
   2. python3 ~/.hermes/scripts/web_search.py "asyncio performance pitfalls common mistakes" --source qa -n 3
   输出性能评估报告（200字以内）：性能增益预期、已知陷阱、benchmark来源。引用来源URL。`,
  { label: 'optimizer: 性能评估', phase: '性能优化', effort: 'medium' }
)

phase('代码实现')
const codeSkeleton = await agent(
  `你是 engineer 角色。任务：实现"${TASK}"的代码骨架。
   ⚠️ 你的角色 prompt 要求"涉及不确定 API 先搜"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "Python asyncio httpx requests migration" --source qa -n 3
   2. python3 ~/.hermes/scripts/web_search.py "SQLAlchemy async session setup" -n 2
   输出：一个 50 行以内的 Python 代码骨架，含 async def 路由、async 数据库会话、异步 HTTP 调用。把 API 用法来源 URL 写入代码注释。`,
  { label: 'engineer: 代码骨架', phase: '代码实现', effort: 'medium' }
)

phase('质量验证')
const testPlan = await agent(
  `你是 qa 角色。任务：为"${TASK}"编写测试计划并验证质量。
   ⚠️ 你的角色 prompt 要求"测试前先搜测试策略和已知漏洞"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "pytest-asyncio testing best practices" --source qa -n 3
   2. python3 ~/.hermes/scripts/web_search.py "python asyncio security pitfalls input validation concurrency" --source qa -n 3
   输出测试计划（200字以内）：测试策略、关键用例、asyncio 特有陷阱、依赖安全性。引用来源。`,
  { label: 'qa: 测试计划', phase: '质量验证', effort: 'medium' }
)

phase('验收')
const acceptance = await agent(
  `你是 pm 角色。任务：验收"${TASK}"项目交付。
   你收到：架构设计(${archDesign.slice(0,100)})、性能评估(${perfPlan.slice(0,100)})、代码骨架(${codeSkeleton.slice(0,100)})、测试计划(${testPlan.slice(0,100)})
   ⚠️ 你的验收标准：架构完整、性能有基准、代码可编译、测试覆盖关键路径。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "web app migration acceptance criteria" -n 3
   输出验收结论（100字以内）：逐项对照，判定通过/打回。`,
  { label: 'pm: 验收', phase: '验收', effort: 'medium' }
)

return {
  summary: 'asyncio 重构工作流完成',
  prd: prd.slice(0, 200),
  archDesign: archDesign.slice(0, 200),
  perfPlan: perfPlan.slice(0, 200),
  codeSkeleton: codeSkeleton.slice(0, 300),
  testPlan: testPlan.slice(0, 200),
  acceptance: acceptance.slice(0, 150),
}
