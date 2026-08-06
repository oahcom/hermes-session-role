# RFC: 复用 Claude Code 原生特性替代 HE 自建轮子

状态: **草案** | 优先级: P0 | 影响范围: session-launcher / session-pipeline / hermes-session-roles

---

## 问题

HE 在三个层面上与 Claude Code 重复建设：

1. **进程管理**：`sentinel.py`(432 行) + `/tmp/ccs-sentinels/` 做 CC 已在做的 agent 跟踪
2. **技能部署**：`deploy_role_skills.sh` + `sync-daemon.sh`(838 行 bash) 做 CC plugin 做的事
3. **进程通信**：`subprocess ccs.py send` + bus fallback 做 MCP 做的事

每项自建代码都有维护成本、故障点、版本漂移风险。本 RFC 不引入新功能，**只把 HE 做的事退还给 CC**。

---

## 方案一：Plugin 封装共享源技能

### 目标

97 个 SKILL.md 从裸目录升级为标准 **Claude Code Plugin** 格式，获得版本管理 + 依赖声明 + eval 质量门禁 + 逐角色灰度更新。

### 现状

```
~/shared-skills/hermes-origin/skills/
├── code/write_code/SKILL.md
├── code/refactor/SKILL.md
└── deploy_role_skills.sh  →  ln -sfn 到 34 个 workspace
```

缺点：改一个 skill 全部 workspace 立刻生效，无法灰度、无法回滚、无版本追踪。

### 目标

```
~/shared-skills/hermes-origin/skills/
├── code/write_code/
│   ├── SKILL.md
│   └── plugin.json        ← 新增
├── code/refactor/
│   ├── SKILL.md
│   └── plugin.json
└── deploy_role_skills.sh  →  claude plugin install <name>@<version>
```

### plugin.json 示例

```json
{
  "name": "write_code",
  "version": "1.0.0",
  "description": "根据任务描述生成符合规范的代码",
  "category": "code",
  "dependencies": [],
  "evaluator": {
    "cases": ["evals/case.yaml"],
    "grader": "graders/quality.md"
  },
  "compatible": ">=2.1.0"
}
```

### 实施步骤

| 步骤 | 文件 | 工作量 |
|------|------|--------|
| 1.1 | 为 97 个 SKILL.md 生成 `plugin.json` | 自动化脚本（约 50 行 Python），从 SKILL.md 的 frontmatter 提取 name/description |
| 1.2 | `deploy_role_skills.sh` 改为调用 `claude plugin install` | 修改 deploy 函数 |
| 1.3 | `sync-daemon.sh` 去掉 skill 同步逻辑（保留心跳/健康检查） | 砍掉约 400 行 |
| 1.4 | `ccs start` 部署技能改为 `claude plugin install --version <pin>` | 在 workspace settings.json 加 `overridePlugins` |
| 1.5 | 技能更新改为 `claude plugin update <name>` | 操作手册更新 |

### 灰度逻辑

每个 workspace 可以钉住不同版本。ccs start 写入的 settings.json 包含：

```json
{
  "overridePlugins": {
    "enabled": ["write_code@1.0.0", "refactor@1.2.0"],
    "disabled": []
  }
}
```

版本升级：先改 `reviewer` workspace 钉 `write_code@1.1.0`，测试一周期后再全量改默认。

### 回滚

```bash
claude plugin update write_code@1.0.0     # 回到旧版
# 或在 workspace settings.json 直接钉旧版本
```

---

## 方案二：JSON Schema 工作流验证

### 目标

工作流步骤从**信任角色人格声明**变为**可验证的结构化产出契约**。

### 现状

```json
// full_dev_pipeline.json s1
"exit_condition": {
  "bus_category": "architecture",
  "text_contains": "full_dev_pipeline/s1-complete"
}
// verify 字段（shell 脚本，失败不阻断推进）
"verify": "python3 -c \"assert Path.home().joinpath('ccs-workspaces/product_architect/PRD.md').exists()\""
```

### 目标

```json
"exit_condition": {
  "bus_category": "architecture",
  "text_contains": "full_dev_pipeline/s1-complete",
  "json_schema": {
    "type": "object",
    "required": ["PRD", "DESIGN", "sections"],
    "properties": {
      "PRD": {"type": "string", "minLength": 200},
      "DESIGN": {"type": "string"},
      "sections": {
        "type": "array",
        "items": {"type": "string"},
        "contains": ["Problem", "Users", "Scope", "Success Criteria"]
      }
    }
  }
}
```

### 实施步骤

| 步骤 | 改动 | 工作量 |
|------|------|--------|
| 2.1 | `Step` 数据类新增 `exit_schema: dict = None` | `pipeflow/engine.py` +5 行 |
| 2.2 | `_tick` 中 exit 匹配后增加 schema 验证 | `pipeflow/engine.py` +20 行 |
| 2.3 | schema 验证函数：调用 `claude -p --json-schema` 但这不是对的方式 | `pipeflow/engine.py` +30 行 |
| 2.4 | 替代：python `jsonschema` stdlib 验证（schema 检查产出物，不是检查 LLM 输出） | 依赖 `jsonschema` 或手写轻量校验 |

这里的核心设计是：**schema 验证的不是角色写的 bus 消息，而是角色的产出物文件**。工作流步骤完成时，角色的产出物在 workspace 目录下，pipeline 用 schema 去检查文件的存在性、完整性、格式正确性。

```python
def _validate_exit_schema(step: Step, role: str) -> tuple[bool, list[str]]:
    """验证角色的产出物是否符合 exit_schema 定义。"""
    schema = step.exit_schema or {}
    workspace = Path.home() / "ccs-workspaces" / role
    errors = []
    for req in schema.get("required", []):
        path = workspace / req
        if not path.exists():
            errors.append(f"缺少必要产出: {req}")
            continue
        prop = schema.get("properties", {}).get(req, {})
        if "minLength" in prop and len(path.read_text()) < prop["minLength"]:
            errors.append(f"{req} 长度不足 ({len(path.read_text())} < {prop['minLength']})")
    return len(errors) == 0, errors
```

### 工作流模板迁移

现有 32 个模板逐一加 `exit_schema`。按类型模板化：

- **architect/design 类**：检查 `PRD.md` + `DESIGN.md` 含必需章节
- **code 类**：检查 `.py` 文件存在 + 测试通过
- **review 类**：检查 `REVIEW.md` 含六维维度
- **doc 类**：检查文档文件存在
- **test 类**：检查测试运行返回码 0

---

## 方案三：MCP serve 替代 ccs send IPC

### 目标

消除 `subprocess ccs.py send` 的路径冲突，用标准 MCP 协议做 pipeline↔session 通信。

### 现状

```
pipeline engine
  → subprocess(["python3", "ccs.py", "send", role, prompt])  ← 每次都 import core.py
    → Python path 冲突 → 异常 → except:pass → 消息靠 bus fallback
```

### 目标

```
pipeline engine（MCP client）
  → tools/call("send-to-role", {role, message, wf_id, step_id})
    → session（MCP server，claude mcp serve）
      → return {delivery: "confirmed", session_id: "..."}
```

### 实施步骤

| 步骤 | 改动 | 工作量 |
|------|------|--------|
| 3.1 | `claude mcp serve` 的 tool 定义：`send-to-role` | 核心改动 |
| 3.2 | pipeline engine 去掉 `subprocess ccs.py send` | `_send_to_role` 重写 |
| 3.3 | bus fallback 保留为备选通道 | 如果 MCP 不可达，回退 bus |
| 3.4 | `_ensure_role_alive` 改为 MCP health check | 替代 tmux has-session |

### Tool 定义

Claude Code MCP serve 模式下，pipeline 作为外部 MCP client 连接，暴露的 tool：

```
send-to-role(role, message, wf_id?, step_id?)
  → {"delivery": "confirmed", "session_id": "...", "delivered_at": timestamp}

role-status(role)
  → {"alive": bool, "current_step": str, "idle_seconds": int}
```

### 通信协议

```
pipeline ──→ MCP connect ──→ claude mcp serve
             ↓
             tools/call("send-to-role", {role: "engineer", message: "..."})
             ↓
             {"delivery": "confirmed"}  ← 有回执、有超时
```

对比当前 `ccs.py send`：

```
pipeline → subprocess ccs.py → import core → _tmux_send → tmux send-keys
          → fallback: bus write
          → 无回执
```

---

## 实施路线图

```
Phase 1（2-3 天）——插件封装
├── 为 97 个 SKILL.md 生成 plugin.json
├── 验证 claude plugin install 可用
└── deploy_role_skills.sh 改为 plugin install

Phase 2（1-2 天）——JSON Schema 验证
├── Step 数据类加 exit_schema
├── _tick 集成产出物验证
└── 首批 8 个关键模板加 schema（dev/arch/review/qa/doc/design/hotfix/task）

Phase 3（2-3 天）——MCP IPC
├── 确定 claude mcp serve 的 tool API
├── _send_to_role 改为 MCP client
└── 保留 bus fallback

Phase 4（持续）——技能版本管理
├── 确定灰度发布流程
├── skill 更新 SOP
└── 淘汰 sync-daemon.sh 的 skill 同步逻辑
```

## 风险

| 风险 | 可能性 | 缓解 |
|------|--------|------|
| `claude mcp serve` 不支持多 client 同时连接 | 中 | 每个 session 独占 socket，pipeline 连 session |
| `claude plugin install` 不支持无网络环境 | 低 | HE 已有共享源目录可作为本地 marketplace |
| `claude agents --json` 不列出 CCS 管理的 tmux session | 中 | sentinel 保留为 fallback 读 tmux |
| 模板迁移工作量大 | 中 | 先 P0 模板（dev/arch/review/qa），其余按需 |
