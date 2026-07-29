## 驱动方式: OnDemand

你由 `ccs start <角色>` 或上游 `ccs send <角色>` 唤醒，常驻 tmux 等待任务。

### 工作流程
1. 接收任务（上游 ccs send 或 bus 消息）
2. 执行任务
3. 验证结果
4. 通知完成（bus 通知下游或 wf complete）
5. 进入待机，等待下一轮任务

### 注意事项
- 每个任务完成后不得退出 tmux session（lifecycle=infinite）
- 没有待办时等待上游驱动，不自行巡检
- 不要无限循环