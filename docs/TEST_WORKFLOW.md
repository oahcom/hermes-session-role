# hermes-session-roles — 测试工作流

> 非代码文档，描述测试的运行方式、覆盖范围、质量门禁。

---

## 测试金字塔

```
          ┌─────────────┐
          │  集成测试   │  ← 需补齐（registry 加载、JSON schema、CLI 集成）
          ├─────────────┤
          │  单元测试   │  ✅ 15 个搜索测试
          └─────────────┘
```

---

## 现有测试

### `tests/test_search.py` — 单元测试（15/15 通过）

| 测试用例 | 验证点 |
|---------|--------|
| `test_search_修复` | "修服务器" → maintainer 排第一，分>30 |
| `test_search_清理` | "清理" → curator 在前三 |
| `test_search_代码` | "写代码" → developer 排第一 |
| `test_search_监控` | "监控" → coordinator/supervisor 在结果中 |
| `test_search_英文` | 英文关键词不崩（ponytail: 同义词待补） |
| `test_search_空输入` | 空字符串返回 [] |
| `test_search_噪音` | 特殊字符不崩 |
| `test_search_同义词` | "运维" → maintainer（同义词扩展） |
| `test_search_多关键词` | "修复服务" → maintainer 排第一 |
| `test_search_浏览器登录` | "登录表单" → form-expert (browser-harness) |
| `test_search_网页抓取` | "网页抓取" → scraper-engineer |
| `test_search_档案管理` | "知识库归档" → archivist |
| `test_search_性能优化` | "性能慢" → optimizer |
| `test_search_所有角色可搜` | 14 个角色 title 搜索均命中 |
| `test_search_浏览器人格不覆盖角色` | "修服务器" 结果中 role 数 ≥ persona 数 |

---

## 质量门禁

### 提交前必须通过

```bash
cd /home/administrator/hermes-session-roles
python3 tests/test_search.py
# 输出必须包含: "结果: 15 通过, 0 失败"
```

### 新增角色验证清单（手工冒烟）

```bash
# 1. CLI 基础功能
python3 src/cli.py list --roles
python3 src/cli.py show <new_role>
python3 src/cli.py search "<new_role 关键词>" --top 5

# 2. eval_criteria 可执行
# 逐条在 shell 执行，确认返回码 0

# 3. 回归搜索
python3 tests/test_search.py
```

---

## 缺失测试（待补齐）

| 类别 | 缺失项 | 优先级 |
|------|--------|--------|
| Registry | `load_all()` 正确加载所有 JSON | HIGH |
| Registry | 同名 PersonaDef/RoleDef 冲突处理 | HIGH |
| Registry | 目录不存在/JSON 语法错误的错误处理 | MEDIUM |
| Schema | JSON Schema 验证（必填字段、类型、枚举） | HIGH |
| CLI | `validate` 子命令批量检查 | MEDIUM |
| CLI | `--json` 输出格式稳定性 | LOW |
| CLI | `load` 命令模板替换边界情况（`{` 字符） | MEDIUM |
| CLI | `search` 结果排序稳定性 | LOW |
| Integration | 角色 JSON → session-launcher prompt 注入 | HIGH |
| Integration | 角色 JSON → session-pipeline 路由自动生成 | HIGH |

---

## CI/CD 集成（未来）

建议在合并前跑：

```yaml
# .github/workflows/test.yml (示例)
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Python syntax check
        run: python3 -m py_compile src/models.py src/registry.py src/search.py src/cli.py
      - name: Search tests
        run: python3 tests/test_search.py
      - name: Schema validation (future)
        run: python3 scripts/validate_roles.py
```

---

## 运行环境要求

- Python 3.10+
- 无第三方依赖（纯 stdlib）
- 项目根目录可写（registry 加载时扫描 `personas/`）

---

## 故障排查

| 现象 | 排查步骤 |
|------|----------|
| 搜索结果为空 | 1. `load_all()` 是否执行 2. `personas/session-roles/` 目录是否存在 3. JSON 文件名是否以 `persona_` 开头 |
| 角色不在搜索结果 | 1. JSON 中 `name` 字段是否正确 2. `system_prompt` 是否为空 3. 字段权重是否导致分数过低 |
| CLI 报错 import | 1. 确认在项目根目录运行 2. `sys.path` 是否包含 `src/` |
| eval_criteria 失败 | 1. 手工在 shell 执行该命令 2. 确认返回码 0 3. 检查路径/环境变量 |

---

## 维护责任

- 搜索算法变更 → 必须跑全量 `test_search.py` + 手工验证 5 个典型查询
- 新增角色 → 必须通过上述"新增角色验证清单"
- 同义词表更新 → 必须回归 `test_search_同义词` 和 `test_search_多关键词`
- 字段权重调整 → 必须同步 `docs/SEARCH.md` 权重表