---
title: "Hermes Session Ecosystem — Architecture Protocol"
version: "1.0"
date: "2026-07-08"
scope: "All roles in hermes-session-roles"
principle: "流程由协议驱动，不依赖 prompt 人格"
---

# Architecture Protocol（架构协议）

## 核心原则

1. **流程由协议驱动**：Phase 转换、产出物格式、验证标准由 protocol 定义，不由 role 的 prompt 人格定义
2. **产出物标准化**：所有角色遵循相同的文档格式（PRD、DESIGN、API_SPEC、TASKS）
3. **验证可自动化**：每个 Phase 的 exit condition 是可执行的命令（grep、wc、python -c）
4. **角色是执行者，不是人格**：角色的 system_prompt 只描述"做什么"和"怎么验证"，不描述"你是谁"

---

## Phase 定义（Universal，适用于任何项目）

### Phase 0: Requirements Intake（需求接入）

**输入**：用户需求（自然语言）或 bus cat=architecture 消息
**输出**：`workspace/<project>/INTAKE.md`
**exit condition**：`INTAKE.md` 包含至少 3 个字段

```markdown
# INTAKE: <project-name>
- Problem: <one-sentence problem statement>
- Users: <who uses this>
- Scope: <what is in scope>
- Deadline: <if any>
```

**验证命令**：
```bash
grep -E '^(Problem|Users|Scope|Deadline):' workspace/<project>/INTAKE.md | wc -l | awk '$1 >= 3 {exit 0} {exit 1}'
```

**handoff**：INTAKE.md 写入后，Phase 1 自动启动。

---

### Phase 1: PRD（Product Requirement Document）

**输入**：INTAKE.md
**输出**：`workspace/<project>/PRD.md`
**exit condition**：PRD.md 包含至少 5 个必需章节

```markdown
# PRD: <project-name>
## Problem Statement
## User Stories (≥3)
## Out of Scope
## Goal (one sentence)
## Criteria (ISC list)
## Test Strategy
```

**验证命令**：
```bash
grep -E '^(## |Problem Statement|User Stories|Out of Scope|Goal|Criteria|Test Strategy)' workspace/<project>/PRD.md | wc -l | awk '$1 >= 5 {exit 0} {exit 1}'
```

**handoff**：PRD.md 写入后，Phase 2 自动启动。

---

### Phase 2: System Design（系统设计）

**输入**：PRD.md + 现有代码分析
**输出**：`workspace/<project>/DESIGN.md`
**exit condition**：DESIGN.md 包含 Mermaid 图 + 接口定义

```markdown
# DESIGN: <project-name>
## Architecture Diagram (Mermaid)
## Module Definitions
## Interface Contracts (method signatures)
## Data Flow
## Technology Decisions (≥3 options compared)
## Risk Assessment
```

**验证命令**：
```bash
grep -c '```mermaid' workspace/<project>/DESIGN.md | awk '$1 >= 1 {exit 0} {exit 1}'
grep -E '^(class |def |function |interface |POST|GET|PUT|DELETE)' workspace/<project>/DESIGN.md | wc -l | awk '$1 >= 3 {exit 0} {exit 1}'
```

**handoff**：DESIGN.md 写入后，Phase 3 自动启动。

---

### Phase 3: Task Specification（任务规范）

**输入**：DESIGN.md
**输出**：`workspace/<project>/TASKS.json`
**exit condition**：TASKS.json 是 valid JSON，每个 task 有 acceptance_criteria

```json
{
  "project": "<name>",
  "tasks": [
    {
      "id": "T1",
      "title": "<one-line description>",
      "effort": "E1|E2|E3|E4|E5",
      "acceptance_criteria": ["<cmd that returns 0>"],
      "depends_on": [],
      "files_to_modify": ["<path>"]
    }
  ]
}
```

**验证命令**：
```bash
python3 -c "import json; t=json.load(open('workspace/<project>/TASKS.json')); assert 'tasks' in t and len(t['tasks']) >= 1 and all('acceptance_criteria' in task for task in t['tasks'])"
```

**handoff**：TASKS.json 写入后，下游角色（developer、coordinator）消费。

---

## 工作空间结构（Workspace Protocol）

```
~/.hermes/workspace/
  <project-name>/
    INTAKE.md        ← Phase 0
    PRD.md           ← Phase 1
    DESIGN.md        ← Phase 2
    TASKS.json       ← Phase 3
    CHANGELOG.md     ← 变更记录
    ARCHITECTURE.md  ← 总架构文档（汇总）
```

**规则**：
- 每个 Phase 的产出物写入固定路径
- 下游角色通过路径读取，不依赖 prompt 传递
- 所有文件用 Markdown，TASKS 用 JSON
- CHANGELOG.md 记录每个 Phase 的完成时间和决策依据

---

## 角色态度（Professional Protocol）

架构师对其他角色的态度不是"我是设计者你是执行者"，而是：

### 对 developer
```
关系：设计方 → 执行方
交互：TASKS.json 提供验收标准，developer 逐条验证
原则：不干预实现，不指定具体代码，只定义接口和约束
冲突：如果 developer 发现设计不可行，写 bus cat=design_issue，架构师评估修改
```

### 对 coordinator
```
关系：设计方 → 调度方
交互：TASKS.json 提供 effort 和 dependency，coordinator 决定排期
原则：不干预调度，不指定优先级，只提供技术评估
冲突：如果时间紧迫，coordinator 可以 ask 架构师简化 scope，架构师评估 tradeoff
```

### 对 consumer
```
关系：设计方 → 验证方
交互：PRD.md / DESIGN.md 提供验证依据，consumer 核对实现是否符合设计
原则：不干预验证，不解释设计意图，设计文档自解释
冲突：如果实现不符合设计，consumer 写 bus cat=design_issue，架构师确认是设计问题还是实现问题
```

### 对 maintainer
```
关系：设计方 → 运维方
交互：DESIGN.md 提供架构约束，maintainer 在约束内操作
原则：不干预运维，不指定具体操作，只定义"什么不能动"
冲突：如果运维操作违反架构约束，架构师标记红线，maintainer 遵守
```

---

## 通用性保证（Universality）

以上协议**不依赖任何特定角色名**。任何需要"设计"的场景都可以套用：

| 场景 | Phase 0 | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|---------|
| 新功能开发 | INTAKE → | PRD → | DESIGN → | TASKS |
| 架构重构 | 问题分析 → | 重构方案 → | 影响评估 → | 任务分解 |
| 技术选型 | 需求 → | 选型标准 → | 对比分析 → | 决策文档 |
| 文档编写 | 目标 → | 大纲 → | 内容 → | 审校清单 |

**关键点**：Phase 是固定的，内容是灵活的。不依赖"你是架构师"这个人格，而是依赖"这是 Phase 2，需要输出 DESIGN.md"这个协议。
