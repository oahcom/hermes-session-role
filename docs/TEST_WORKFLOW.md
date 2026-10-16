# 测试工作流

## 现有测试

> ⚠️ `tests/test_search.py` 与 `src/search.py` 已剪枝（零 runtime importer）。
> 语义搜索回归暂不可用—如需恢复，详见 [SEARCH.md](SEARCH.md)。

### `tests/test_registry.py` — Registry 加载/查询回归 (6/6 通过)

| 测试用例 | 验证点 |
|---------|--------|
| `test_load_all_count` | load_all 返回数量与 list_personas 一致 |
| `test_list_roles` | 角色列表 ≥ 20 含关键角色 |
| `test_list_personas` | 人格总数 ≥ 50 |
| `test_get_by_name` | get("maintainer") 返回正确角色 |
| `test_get_by_name_nonexistent` | 不存在返回 None |
| `test_categories` | 分类统计合计 = 人格总数 |

---

## 质量门禁

### 提交前必须通过

```bash
cd /home/administrator/hermes-session-roles
python3 -m pytest tests/ -q
# 6 passed (registry 回归)
```

---

### 新增角色验证清单（手工冒烟）

```bash
# 1. JSON 校验
python3 src/validate_roles.py

# 2. prompt 组装
python3 src/role_assembler.py <new_role>

# 3. 搜索能力（当前不可用 — search.py 已剪枝）
# 如需恢复：详见 SEARCH.md 恢复指南
```

---

## 缺失测试（待补齐）

| 类别 | 缺失项 | 优先级 |
|------|--------|--------|
| Registry | `load_all()` 正确加载所有 JSON | HIGH |
| Registry | 同名 PersonaDef/RoleDef 冲突处理 | HIGH |
| Registry | 目录不存在/JSON 语法错误的错误处理 | MEDIUM |
| Schema | JSON Schema 验证（必填字段、类型、枚举） | HIGH |
| CLI | `validate_roles` --roles/--category 格式稳定性 | MEDIUM |
| CLI | `--json` 输出格式稳定性 | LOW |
| CLI | `role_assembler` --inject 模板替换边界情况 | MEDIUM |
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
        run: python3 -m py_compile src/models.py src/registry.py src/role_assembler.py src/validate_roles.py
      - name: Registry tests
        run: python3 -m pytest tests/test_registry.py -q
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
| 角色校验失败 | 1. JSON 语法是否正确 2. 必填字段是否存在 3. `validate_roles.py` 输出错误详情 |
| 角色不在列表 | 1. JSON 文件名是否以 `persona_` 开头 2. `personas/session-roles/` 目录是否存在 3. `name` 字段是否与文件名匹配 |
| prompt 组装失败 | 1. role_name 是否存在 2. `src/role_assembler.py <name>` 是否报错 3. `prompts/roles/` 与 `prompts/base.md` 是否存在 |
| eval_criteria 失败 | 1. 手工在 shell 执行该命令 2. 确认返回码 0 3. 检查路径/环境变量 |

---

## 维护责任

- 新增角色 → 必须通过上述"新增角色验证清单"
- `validate_roles.py` 校验规则变更 → 同步更新 AGENTS.md 验收清单
- Registry 缓存逻辑变更 → 同步 `src/registry.py` 注释与 INDEX.md 红线