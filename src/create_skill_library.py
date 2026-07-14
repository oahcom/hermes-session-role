#!/usr/bin/env python3
"""创建技能库骨架目录和所有技能文档。"""
import os
from pathlib import Path

SKILLS_ROOT = Path(os.environ.get('HERMES_SKILLS_ROOT', str(Path.home() / 'shared-skills' / 'hermes-origin')))

# 技能模板文档
SKILLS = {
    # code/
    "skills/code/write_code.md": """# write_code — 编码技能

## 适用角色
engineer, pg, codex-dev, investigator_python

## 核心原则
1. **决策阶梯**：需要吗？→ 复用？→ 标准库？→ 原生？→ 已装依赖？→ 一行？→ 最小实现
2. **复杂度控制**：函数≤20行，参数≤3，单一职责，3次即抽象
3. **安全铁律**：输入必验，参数化查询，无硬编码凭据

## 风格
Python 3.10+ 类型注解全覆盖，Google Style，命名揭示意图

## 验证
- `python3 -m py_compile <file>` PASS
- 单测覆盖核心逻辑
- `arch_drift_detector --json` drift=0
""",
    "skills/code/write_tests.md": """# write_tests — 测试技能

## 命名
`test_<场景>_<期望>`

## 原则
- 一断言一测试
- 测试是行为文档
- 无框架，assert 自检

## 覆盖
- 边界：空输入、极值、并发
- 表征测试：重构前先写
""",
    "skills/code/refactor.md": """# refactor — 重构技能

## 红线
- 先测后改（表征测试）
- 保护不变量
- 单一重构不混入功能变更

## 常用手法
提取函数/类、多态替switch、卫语句、封装可变

## Ponytail
`# ponytail: 简化X，天花板Y，升级路径Z`
""",
    "skills/code/debug.md": """# debug — 调试技能

## 6步法
复现→定位→假设→验证→修复→回归

## 禁止
- 未复现就改代码
- 只改症状不改根因
- 吞异常
""",
    "skills/code/git_commit.md": """# git_commit — 提交规范

## 格式
`feat/fix/refactor/docs/chore: 中文描述`

## 预提交检查
```bash
python3 -m py_compile <changed.py>
pytest <tests> -x -q
```
""",
    # review/
    "skills/review/d1_correctness.md": """# D1 正确性审查

## 检查点
- 边界条件（空、极值、并发）
- 逻辑分支完整性（else、异常）
- 类型一致性
- 整数溢出、浮点精度

## 通过标准
无逻辑bug、边界全覆盖、类型严格匹配
""",
    "skills/review/d2_security.md": """# D2 安全审查

## OWASP Top 10
A01访问控制 A02加密 A03注入 A04不安全设计 A05配置错误
A06脆弱组件 A07认证失效 A08完整性 A09日志 A10SSRF

## 通过标准
零高危、零硬编码凭据、输入全验证
""",
    "skills/review/d3_maintainability.md": """# D3 可维护性审查

## 指标
命名揭示意图、函数≤20行/参数≤3、无重复代码、依赖注入
""",
    "skills/review/d4_performance.md": """# D4 性能审查

## 红旗
N+1查询、内存泄漏、阻塞IO、O(n²)算法

## 优化清单
连接池、批处理、缓存(TTL/LRU)、索引分页
""",
    "skills/review/d5_consistency.md": """# D5 一致性审查

## 统一项
代码风格、错误处理模式、日志格式、命名约定、配置管理
""",
    "skills/review/d6_testability.md": """# D6 可测试性审查

## 标准
核心逻辑有测试≥80%、依赖可注入、Mock友好、测试无间依赖
""",
    # arch/
    "skills/arch/intake_analysis.md": """# intake_analysis — 需求摄入

## 输出 INTAKE.md
- Problem/Users/Scope/Deadline 至少3字段
- 退出：`grep -E '^(Problem|Users|Scope|Deadline):' | wc -l >= 3`
""",
    "skills/arch/prd_write.md": """# prd_write — PRD编写

## 结构
Problem→User Stories(≥3)→Out of Scope→Goal→Criteria→Test Strategy

## 退出
`grep -E '^## ' PRD.md | wc -l >= 5`
""",
    "skills/arch/system_design.md": """# system_design — 系统设计

## 结构
Mermaid图→Module→Interface(≥3)→Data Flow→Tech Decisions(≥3)→Risk

## Ponytail
`# ponytail: 简化X, 升级路径Z`
""",
    "skills/arch/task_spec.md": """# task_spec — 任务规格

## TASKS.json
```json
{"tasks": [{"id":"","effort":"E1-E5","acceptance_criteria":"","depends_on":[]}]}
```

## 退出
每个task有acceptance_criteria
""",
    "skills/arch/adr_write.md": """# adr_write — ADR编写

## 格式
```
# ADR-N: 标题
## Status: Proposed/Accepted/Superseded
## Context: 背景问题
## Decision: 决策内容
## Consequences: 正负面影响
```
""",
    # pm/
    "skills/pm/requirement_analysis.md": """# requirement_analysis — 需求分析

## 三问
1. 谁会用？2. 不做会怎样？3. 验证标准？
""",
    "skills/pm/user_story_write.md": """# user_story_write — 用户故事

## 格式
As a <角色> / I want <功能> / So that <价值>
Acceptance Criteria: 列表
优先级: P0-P3 / 故事点: S/M/L
""",
    "skills/pm/priority_rank.md": """# priority_rank — 优先级排序

## P0-P3
- P0: 阻塞发布/安全/数据丢失
- P1: 核心功能缺失
- P2: 一般功能
- P3: 技术债/文档

## ROI = 价值/工时
""",
    "skills/pm/acceptance_verify.md": """# acceptance_verify — 验收

## 清单
功能符AC、单测通过、集成通过、文档同步、无回归
""",
    # qa/
    "skills/qa/test_plan.md": """# test_plan — 测试计划

## 内容
范围/策略、环境/数据、用例矩阵、通过标准、风险假设
""",
    "skills/qa/test_case_write.md": """# test_case_write — 测试用例

## 命名
`test_模块_场景_期望`
## 结构
Given-When-Then / Arrange-Act-Assert
""",
    "skills/qa/test_execute.md": """# test_execute — 测试执行

## 流程
环境确认→冒烟→功能全跑→回归→性能→报告
""",
    "skills/qa/test_report.md": """# test_report — 测试报告

## 内容
通过/失败/跳过统计、缺陷列表、覆盖率、发布建议
""",
    # devops/
    "skills/devops/deploy_plan.md": """# deploy_plan — 部署计划

## 内容
版本/变更摘要、步骤(蓝绿/滚动)、回滚方案、验证检查点、通知名单
""",
    "skills/devops/infra_provision.md": """# infra_provision — 基础设施

IaC(Terraform/Ansible)、幂等、环境隔离(dev/staging/prod)
""",
    "skills/devops/monitor_setup.md": """# monitor_setup — 监控搭建

四大信号：Latency/Traffic/Errors/Saturation
SLO/SLI定义、告警分级P1/P2/P3
""",
    "skills/devops/incident_response.md": """# incident_response — 故障响应

检测→分级→止血→根因→恢复→复盘(48h内)
""",
    "skills/devops/rollback.md": """# rollback — 回滚

## 触发
关键指标异常、用户投诉激增、数据不一致

## 步骤
确认版本→执行回滚→验证恢复→通知
""",
    # writer/
    "skills/writer/doc_structure.md": """# doc_structure — 文档结构

读者导向、概念→任务→参考、单一事实源头
""",
    "skills/writer/api_doc_write.md": """# api_doc_write — API文档

OpenAPI格式：路径/方法/参数/响应/错误码 + 示例
""",
    "skills/writer/changelog_write.md": """# changelog_write — 变更日志

## Keep a Changelog
## [版本] - YYYY-MM-DD
### Added/Changed/Deprecated/Removed/Fixed/Security
""",
    "skills/writer/readme_write.md": """# readme_write — README

简介(一句话价值)、快速开始(5min)、配置说明、架构概览、贡献指南、许可证
""",
    "skills/writer/version_bump.md": """# version_bump — 版本号

## SemVer
MAJOR: 不兼容API / MINOR: 后向兼容新增 / PATCH: 后向兼容修复
""",
    # lr/
    "skills/lr/tech_selection.md": """# tech_selection — 技术选型

## 方法
≥3备选→评估矩阵(功能/性能/生态/成本/许可)→红线检查→ADR
""",
    "skills/lr/redline_check.md": """# redline_check — 红线检查

## LR红线
无tech_decision PG不动手、选型≥3方案、必写ADR
""",
    "skills/lr/decision_record.md": """# decision_record — 决策记录

见 skills/arch/adr_write.md
""",
    "skills/lr/tradeoff_analysis.md": """# tradeoff_analysis — 权衡分析

维度：短期vs长期、买vs自建、一致性vs可用性
""",
    # pg/
    "skills/pg/decision_ladder.md": """# decision_ladder — 决策阶梯

## 7级
1. YAGNI→2. 复用→3. 标准库→4. 原生→5. 已有依赖→6. 一行→7. 最小实现
""",
    "skills/pg/impl_plan.md": """# impl_plan — 实施计划

任务分解(E1-E5)、依赖图、风险缓解、验收对齐
""",
    "skills/pg/risk_assess.md": """# risk_assess — 风险评估

## 矩阵
| 风险 | 概率 | 影响 | 缓解 |
""",
    "skills/pg/redline_enforce.md": """# redline_enforce — 红线执行

PG红线：无tech_decision不写代码、决策阶梯逐级、ponytail标记
""",
    # investigator/
    "skills/investigator/evidence_chain.md": """# evidence_chain — 证据链

## 7类证据
日志(时间戳/级别)、堆栈(完整调用链)、配置快照、代码定位(file:line)、
测试复现(最小用例)、监控指标(时序图)、变更历史(git blame)

## 输出
```
证据链: ID
1. [日志] <file>:<line> <内容>
2. [堆栈] <func> <调用链>
根因: <file>:<line> <描述>
```
""",
    "skills/investigator/stack_trace_analysis.md": """# stack_trace_analysis — 堆栈分析

识别异常类型→定位抛出点→回溯调用链→关联最近变更
""",
    "skills/investigator/root_cause_identify.md": """# root_cause — 根因识别

5Why法：连问5次触及系统性原因

分类：代码缺陷/配置错误/环境差异/依赖升级/架构缺陷/流程缺失
""",
    "skills/investigator/fix_propose.md": """# fix_propose — 修复提案

## 格式
根因: / 修复方案: / 影响面: / 验证: / 回滚: / 风险:
""",
    "skills/investigator/cross_stack_correlation.md": """# cross_stack — 跨栈关联

前后端↔DB↔基础设施、请求链路追踪、资源竞争分析
""",
    "skills/investigator/architecture_review.md": """# arch_review — 架构审查

模块边界清晰、无循环依赖、单一职责、信息隐藏、扩展点预留
""",
    "skills/investigator/systemic_root_cause.md": """# systemic_root_cause — 系统性根因

同类bug重复→流程缺失、性能反复→架构瓶颈、安全连发→威胁建模缺失
""",
    "skills/investigator/triage_decision.md": """# triage_decision — 分诊决策

阻塞主流程→P0？有workaround→P1？可复现？→N→增观测点。影响大→升级
""",
    "skills/investigator/log_analysis.md": """# log_analysis — 日志分析

grep ERROR/WARN/CRITICAL/FAIL、时间窗口关联、请求ID串联、结构解析
""",
    "skills/investigator/escalation_rule.md": """# escalation_rule — 升级规则

同一问题3轮未修→升级、P0>30min无进展→升级、影响≥3服务→升级
""",
    # security/
    "skills/security/owasp_scan.md": """# owasp_scan — OWASP扫描

Top 10: A01访问控制 A02加密 A03注入 A04不安全设计 A05配置错误
A06脆弱组件 A07认证 A08完整性 A09日志 A10SSRF
""",
    "skills/security/threat_model.md": """# threat_model — 威胁建模

STRIDE: Spoofing/Tampering/Repudiation/InfoDisclosure/DoS/Elevation
""",
    "skills/security/vuln_assess.md": """# vuln_assess — 漏洞评估

CVSS: 攻击向量/复杂度/权限/交互/范围/机密性/完整性/可用性
""",
    "skills/security/compliance_check.md": """# compliance_check — 合规检查

GDPR/个保法、ISO27001、SOC2、等保2.0
""",
    # coordination/
    "skills/coordination/cluster_monitor.md": """# cluster_monitor — 集群监控

CCS/Codex session数、角色分布、uptime、sentinel一致性、心跳异常
""",
    "skills/coordination/sentinel_audit.md": """# sentinel_audit — 哨兵审计

文件存在但tmux无session→清理、session在但心跳久→告警
""",
    "skills/coordination/cross_role_dispatch.md": """# cross_role_dispatch — 跨角色调度

Scout S级7天无人→engineer、Curator 3轮未果→codex-dev、CCS重启3次→人
""",
    "skills/coordination/escalation.md": """# escalation — 升级

写bus: `python3 ~/.hermes/scripts/bus_client.py write architecture "[升级]" --evidence <详情> --src coordinator`
""",
    "skills/coordination/brief_write.md": """# brief_write — 简报

模板: `运行:N 异常:N 积压:N 调度:X`
""",
    # closing/
    "skills/closing/backlog_scan.md": """# backlog_scan — 积压扫描

bus blocker未解决、code_fix未验证、GitHub issue>7天、PR review>3天
""",
    "skills/closing/close_loop.md": """# close_loop — 闭环

补测试、补文档、合并PR、关Issue、验收打勾
""",
    "skills/closing/close_report.md": """# close_report — 闭环报告

[closer] 第N轮闭环: 处理X个, 成功Y个, 剩余Z个
""",
    # optimization/
    "skills/optimization/profile_analysis.md": """# profile — 性能剖析

py-spy/cProfile/perf、火焰图/调用图
""",
    "skills/optimization/bottleneck_identify.md": """# bottleneck — 瓶颈识别

CPU热点、锁竞争、IO等待、内存分配热点
""",
    "skills/optimization/optimization_apply.md": """# optimization_apply — 优化应用

先测量后优化、单一变量、A/B验证、保留回滚
""",
    "skills/optimization/benchmark.md": """# benchmark — 基准测试

预热→稳态→多次取中位数、固定环境/数据→吞吐/延迟分位/资源
""",
    # codex/
    "skills/codex/goal_manage.md": """# goal_manage — GOAL管理

create_goal(objective,budget) → /goal轮次 → update_goal(status=complete)
""",
    "skills/codex/bus_poll.md": """# bus_poll — 总线轮询

```bash
python3 ~/.hermes/scripts/bus_client.py read --cat code_fix --limit 5 --json
python3 ~/.hermes/scripts/bus_client.py read --cat architecture --limit 5 --json
```
""",
    "skills/codex/code_write.md": """# code_write — Codex编码

单轮单任务、编辑后必验证、留痕(commit+bus)
""",
    "skills/codex/verify_commit.md": """# verify_commit — 验证提交

py_compile PASS、测试PASS、git diff符合预期
""",
    "skills/codex/budget_wrap.md": """# budget_wrap — 预算收尾

>10%→/goal继续、<10%→收尾complete
""",
    # debate/
    "skills/debate/argument_parse.md": """# argument_parse — 论点解析

核心主张→支撑证据→隐含假设→反驳预判
""",
    "skills/debate/evidence_check.md": """# evidence_check — 证据核验

来源可信可追溯、非相关关联、样本代表性
""",
    "skills/debate/verdict_write.md": """# verdict_write — 裁决

结论:支持/反驳/不确定 理由: 置信度:高/中/低
""",
    "skills/debate/escalation.md": """# escalation — 辩论升级

双方僵持>3轮、涉及架构红线、安全合规争议→升级
""",
    # knowledge/
    "skills/knowledge/knowledge_extract.md": """# knowledge_extract — 知识抽取

来源：代码审查发现、事后复盘、最佳实践、外部调研
""",
    "skills/knowledge/knowledge_organize.md": """# knowledge_organize — 知识组织

标签分类、关联链接、版本管理
""",
    "skills/knowledge/knowledge_verify.md": """# knowledge_verify — 知识验证

交叉验证≥2独立来源、标注时效性、标注适用边界
""",
    "skills/knowledge/knowledge_publish.md": """# knowledge_publish — 知识发布

```bash
python3 ~/.hermes/scripts/bus_client.py write knowledge "<标题>" --evidence "<内容>" --src knowledge_curator
```
""",
    # maintenance/
    "skills/maintenance/health_check.md": """# health_check — 健康检查

服务存活(systemctl is-active)、端口监听、磁盘/内存/CPU、ERROR计数
""",
    "skills/maintenance/diagnose.md": """# diagnose — 故障诊断

症状→假设→验证→定位、二分法缩小范围
""",
    "skills/maintenance/auto_fix.md": """# auto_fix — 自动修复

重启卡死、清理过期文件、证书续期、配置漂移纠正
""",
    "skills/maintenance/verify_fix.md": """# verify_fix — 修复验证

原故障指标恢复、无新告警、回归测试通过
""",
    # curation/
    "skills/curation/skill_audit.md": """# skill_audit — 技能审计

完整性(字段齐)、正确性(引用有效)、时效性(最近更新)、去重性(无嵌套)
""",
    "skills/curation/skill_sync.md": """# skill_sync — 技能同步

systemd skill-sync.service定时、符号链接分发Claude/Codex
""",
    "skills/curation/category_map.md": """# category_map — 分类映射

CATEGORIES.json: 角色↔分类、技能↔分类双向映射
""",
    "skills/curation/quality_gate.md": """# quality_gate — 质量门禁

validate_skills.py全通过、文件<30KB、无循环引用
""",
    # research/
    "skills/research/github_scan.md": """# github_scan — GitHub扫描

6领域: AI Agent框架/LLM推理/编程助手/多模态/基础设施/安全隐私
""",
    "skills/research/trend_analysis.md": """# trend_analysis — 趋势分析

Star增长率、Commit频次、Issue解决率、版本发布节奏
""",
    "skills/research/opportunity_eval.md": """# opportunity_eval — 机会评估

战略契合30%/技术可行25%/资源需求20%/竞争窗口15%/风险可控10%
""",
    "skills/research/report_write.md": """# report_write — 报告撰写

执行摘要→详细发现(含证据)→评分矩阵→行动建议→附录
""",
    # monitor/
    "skills/monitor/ccs_health_check.md": """# ccs_health — CCS健康检查

tmux session存活、sentinel一致性、最近bus活动、资源占用
""",
    "skills/monitor/log_anomaly_detect.md": """# log_anomaly — 日志异常

ERROR/CRITICAL/FAIL/TRACEBACK计数、关键词聚类、趋势突变
""",
    "skills/monitor/alert_write.md": """# alert_write — 告警

[monitor] 告警:标题 级别:P0/P1/P2 详情: 建议动作:
""",
}

# 创建所有目录
for relpath in SKILLS:
    dirpath = SKILLS_ROOT / os.path.dirname(relpath)
    dirpath.mkdir(parents=True, exist_ok=True)
    # 写.gitkeep
    (dirpath / ".gitkeep").touch()

# 写所有技能文档
written = 0
for relpath, content in sorted(SKILLS.items()):
    full = SKILLS_ROOT / relpath
    full.write_text(content)
    written += 1

print(f"创建 {written} 个技能文档在 {SKILLS_ROOT}")
