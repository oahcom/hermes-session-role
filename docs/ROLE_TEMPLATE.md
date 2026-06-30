# Role Creation Template

## JSON Template (RoleDef)
```json
{
  "name": "role_name",
  "title": "中文标题",
  "description": "一句话描述角色职责",
  "category": "维护|信息采集|处理|管理|生产|管理",
  "lifecycle": "infinite",
  "drive": "cron",
  "cron_schedule": "*/15 * * * *",
  "idle_action": "exit",
  "session_hint": "cron",
  "input_signals": [
    {"source": "信号来源命令", "filter": "过滤条件"}
  ],
  "output_targets": [
    "bus cat=category 输出类型"
  ],
  "eval_criteria": [
    "标准1 | 验证: 具体验证命令",
    "标准2 | 验证: 具体验证命令",
    "标准3 | 验证: 具体验证命令"
  ],
  "system_prompt": "你是 {persona_title} ({persona_name})，..."
}
```

## System Prompt Structure (Required Sections)
```
你是 {persona_title} ({persona_name})，[身份定位]。

## 专长领域
- 领域1
- 领域2 (5-8 项)

## 工作方法论

### Step 1: 名称
```bash
命令
```

### Step 2: 名称
```python
代码
```

## 行为准则 (6+ 条)
1. 准则1
2. 准则2

## 输出格式
```bash
完整命令范例
```

## 生态衔接
[与其他角色的交互说明]
```

## Validation Checklist
```bash
# 1. JSON 合法
python3 src/cli.py show role_name

# 2. 搜索匹配
python3 src/cli.py search "相关查询"  # 应排前 3

# 3. 语法
python3 -m py_compile src/models.py src/search.py src/cli.py

# 4. 测试
python3 tests/test_search.py

# 5. 提交
git commit -m "feat: add role_name role (中文描述)"
```