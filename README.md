# Hermes Session Roles

多 session Claude Code 生态的角色注册表。

9 个基础设施角色 + 59 个浏览器自动化人格，定义每个 session 的职业身份、系统提示词、输入输出信号链路、可验证评价标准。

## 快速开始

```bash
git clone <repo> hermes-session-roles && cd hermes-session-roles

# 查看所有角色/人格
python3 src/cli.py list --roles
python3 src/cli.py list --category 维护

# 查看详情
python3 src/cli.py show maintainer

# 加载提示词（用于 session 启动注入）
python3 src/cli.py load maintainer --json

# 语义搜索（支持中英文 + 同义词扩展）
python3 src/cli.py search "修服务器"
python3 src/cli.py search "写代码"
```

## 9 个 Session 角色

| 角色 | 标题 | 类型 | 周期 | 描述 |
|------|------|------|------|------|
| maintainer | 运维者 | cron 15min | 守卫系统健康，故障自愈 |
| scout | 侦察兵 | loop | GitHub/技术社区情报侦察 |
| consumer | 信息消费者 | cron 30min | bus 消息验证、去重、沉淀 |
| curator | 信息维护者 | cron 每小时 | 清理过期数据，对抗熵增 |
| coordinator | 管理者 | loop | 多 session 状态监控与调度 |
| developer | 开发者 | ondemand | 需求→代码→测试→提交 |
| closer | 闭环者 | ondemand | 积压清理，推动任务 done |
| archivist | 档案管理员 | cron 每日 3:00 | 长期记忆管理，知识索引 |
| optimizer | 性能优化师 | cron 每周日 4:00 | 系统性能瓶颈识别与优化 |

## 项目结构

```
hermes-session-roles/
  personas/
    browser-harness/    → 59 个浏览器自动化专家人格
    session-roles/      → 9 个基础设施角色
  src/
    models.py           → PersonaDef + RoleDef 数据类
    registry.py         → 加载、注册、查询
    search.py           → 中文语义搜索引擎
    cli.py              → list/show/load/search 四个子命令
  tests/
    test_search.py      → 15 个搜索回归测试
  docs/
    ARCHITECTURE.md     → 架构设计
    INDEX.md            → 文档索引
    QUICKSTART.md       → 快速开始
    ROLE_TEMPLATE.md    → 新角色模板
    SEARCH.md           → 搜索算法说明
```

## 测试

```bash
python3 tests/test_search.py          # 15/15 通过
python3 -m py_compile src/*.py        # 语法检查
```

## 添加新角色

```bash
cp docs/ROLE_TEMPLATE.md personas/session-roles/persona_XX_newrole.json
# 编辑 JSON...
python3 src/cli.py show newrole       # 验证
python3 src/cli.py search "相关查询"   # 测试搜索
git commit -m "feat: add newrole (中文描述)"
```

## 红线

- 不加新依赖（stdlib only）
- 每个 JSON 改完 `python3 src/cli.py show <name>` 验证
- 改完必须 git commit，不留 staged
- 测试 `python3 tests/test_search.py` 15/15 通过
