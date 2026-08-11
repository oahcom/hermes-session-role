export const meta = {
  name: 'monitor-recovery-r2',
  description: '监控告警二轮修复：pm打回(watchdog未生效) → maintainer/engineer落实 → qa实测验证 → pm复验',
  phases: [
    { title: '修复落实', detail: 'engineer 补 WatchdogSec + sd_notify' },
    { title: '修复验证', detail: 'qa 实测 kill -9 验证自动重启' },
    { title: 'pm复验', detail: 'pm 逐项复验' },
  ],
}

const R1_ISSUES = 'pm验收打回原因：watchdog 未生效——dkk/ssk service 及全部 drop-in 无 WatchdogSec 配置，daemon 代码无 sd_notify/watchdog 握手，所谓 watchdog 实为业务心跳（heartbeat_*.json 内循环存活），非 systemd watchdog。需补 service 加 WatchdogSec=NNs + daemon 加 sd_notify "WATCHDOG=1" 心跳，实测一次 "kill -9 主进程→80s 内自动重启" 后再交付'

phase('修复落实')
const fixExecution = await agent(
  `你是 maintainer+engineer 联合角色。一轮告警响应被 pm 打回，现在落实 watchdog 修复。
   打回原因：${R1_ISSUES}

   ⚠️ 你的角色 prompt 要求"处理异常前先搜已知故障模式和官方修复"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "systemd watchdog notify Type=notify setup python" --source qa -n 3
   2. python3 ~/.hermes/scripts/web_search.py "sd_notify Python example systemd" --source qa -n 2

   输出：**可执行的修复方案**（不是建议）：
   - unit 文件需加的 WatchdogSec 配置（给 dkk/service 的两处具体修改）
   - daemon 代码需加的 sd_notify 心跳（给出可粘贴的 Python 代码）
   - 验证命令（如何确认 watchdog 生效）
   引用来源URL。`,
  { label: 'maintainer+engineer: R2 修复', phase: '修复落实', effort: 'medium' }
)

phase('修复验证')
const verifyFix = await agent(
  `你是 qa 角色。二轮验证 watchdog 修复是否真正生效。
   ⚠️ 你的角色 prompt 要求"测试前先搜测试策略"。
   你必须执行：
   1. python3 ~/.hermes/scripts/web_search.py "systemd watchdog test kill SIGKILL restart" --source qa -n 3

   你必须**实际执行验证**（不是描述）：
   1. 查看 dkk 配置：systemctl --user show sister-agent-dkk.service --property=WatchdogUSec 2>&1
   2. 查看 ss k 配置：systemctl --user show sister-agent-ssk.service --property=WatchdogUSec 2>&1
   3. 查看 unit 文件：cat ~/.config/systemd/user/sister-agent-dkk.service 2>/dev/null | grep -i watchdog
   4. daemon 是否有 sd_notify：grep -rn "sd_notify\\|WATCHDOG" ~/.hermes/scripts/sister_agent_daemon.py 2>/dev/null || echo "无 sd_notify"

   输出：验证报告，含实际命令输出（不是描述）。逐项判定 watchdog 是否真正落地。`,
  { label: 'qa: R2 验证', phase: '修复验证', effort: 'medium' }
)

phase('pm复验')
const reAcceptance = await agent(
  `你是 pm 角色。告警二轮，复验 watchdog 修复结果。
   你收到修复方案(${fixExecution.slice(0,150)})和验证(${verifyFix.slice(0,150)})。
   对照打回原因逐项复验：
   1. WatchdogSec 是否已配置到 dkk/ssk？
   2. daemon 是否已有 sd_notify 心跳？
   3. "kill -9 → 自动重启"场景是否实测过？

   如果全部通过 → 输出"通过"
   如果未落实 → **再次打回**，列出未修复项
   输出：复验结论（100字以内），明确 PASS/FAIL。`,
  { label: 'pm: R2 复验', phase: 'pm复验', effort: 'medium' }
)

return {
  summary: '告警响应二轮完成',
  fixExecution: fixExecution.slice(0, 200),
  verifyFix: verifyFix.slice(0, 200),
  reAcceptance: reAcceptance.slice(0, 100),
}
