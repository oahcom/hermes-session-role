# Hermes Session Roles — 文档索引

> 角色注册表：31 个 session-role JSON，定义 Claude Code session 的职业身份、prompt、输入输出链路。

## 快速链接

| 文档 | 说明 |
|------|------|
| [QUICKSTART](QUICKSTART.md) | 5 分钟上手：安装、CLI 用法、搜索验证 |
| [ARCHITECTURE](ARCHITECTURE.md) | 架构设计：文件布局、数据模型、信号流、CLI 接口 |
| [SEARCH](SEARCH.md) | 搜索算法：bigram 分词、字段加权、同义词展、测试用例 |
| [ROLE_TEMPLATE](ROLE_TEMPLATE.md) | 新角色模板：JSON 模板 + system_prompt 结构 + 验证清单 |

## 核心文件路径

```
hermes-session-roles/
  personas/
    browser-harness/   → 57 个浏览器自动化专家人格（3 个 JSON 文件）
    session-roles/      → 7 个基础设施角色（每个独立 JSON）
  src/
    models.py           → PersonaDef + RoleDef + registry
    registry.py         → load_all/get/list_* 注册表（纯加载索引）
    validate_roles.py   → 31 角色全量校验 (CLI: --roles/--category)
    role_assembler.py   → 动态组装 system prompt (CLI 入口)
  docs/                 → 本文档
```

## 命令速查

```bash
python3 src/validate_roles.py --roles          # 列出全部 31 角色
python3 src/validate_roles.py --category 维护   # 按分类筛选
python3 src/validate_roles.py                   # 全量校验 (JSON 结构完整性)

python3 src/role_assembler.py maintainer        # 输出角色 system_prompt 文本
python3 src/role_assembler.py maintainer --output prompt.md            # 写入 prompt.md
python3 src/role_assembler.py maintainer --inject ccs-workspaces/maintainer/CLAUDE.md  # 注入 KNOWLEDGE 块
```

## 搜索基准

> ⚠️ `search.py` 与 `cli.py search` 已剪枝（零 runtime importer）。语义搜索能力
> 暂未生效—如需恢复，参见 [SEARCH.md](SEARCH.md)（当前标记为存档候选）。

```
（原搜索基准）
"修服务器" → maintainer  # 37-43 分
"清理"     → curator     # 62-64 分
"写代码"   → developer   # 67-71 分
```

## 红线

- 不加新依赖（stdlib only）
- 每 JSON 改完必须 `python3 src/role_assembler.py <name>` 验证
- 改完必须 git commit，不留 staged
- `python3 src/validate_roles.py` 零错误
