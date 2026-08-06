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
    search.py           → 中文语义搜索引擎
    cli.py              → list/show/load/search 四个子命令
  tests/
    test_search.py      → 9 个搜索回归测试
  docs/                 → 本文档
```

## 命令速查

```bash
python3 src/cli.py list                  # 全部
python3 src/cli.py list --roles          # 仅 session 角色
python3 src/cli.py show maintainer       # 查看详细 JSON
python3 src/cli.py load maintainer       # 加载 prompt 文本
python3 src/cli.py search "修服务器"      # 语义搜索
python3 tests/test_search.py             # 运行全部测试
```

## 搜索基准

```python
"修服务器" → maintainer  # 37-43 分
"清理"     → curator     # 62-64 分
"写代码"   → developer   # 67-71 分
"翻译文档" → i18n-localizer  # 30-33 分
"运维"     → maintainer  # 76-84 分
"部署"     → maintainer
"关闭任务" → closer
```

## 红线

- 不加新依赖（stdlib only）
- 每 JSON 改完必须 `python3 src/cli.py show <name>` 验证
- 改完必须 git commit，不留 staged
- 测试必须 `python3 tests/test_search.py` 9/9 通过
