"""role_relations.py — 角色关系图谱（SwarmVault 知识图谱模式）

显式映射三个 session 项目中所有角色的关系：
- 信息生产者 → 信息消费者
- 协作依赖
- 数据流方向

用法:
    from role_relations import get_relations, get_downstream, get_upstream
"""

# ── 角色关系矩阵（生产者 → 消费者）──
# structure: {producer_role: [(consumer_role, data_category, description), ...]}

_PRODUCE_CONSUME_MAP: dict[str, list[tuple[str, str, str]]] = {
    # 侦察兵 → 下游
    "scout": [
        ("curator", "architecture", "架构发现归档"),
        ("coordinator", "evolution_report", "趋势报告供调度"),
        ("product_architect", "architecture", "架构变更供设计参考"),
    ],
    # 运维者 → 下游
    "maintainer": [
        ("engineer", "code_fix", "需代码修复的问题"),
        ("coordinator", "architecture", "需升级的架构问题"),
    ],
    # 信息维护者 → 下游
    "curator": [
        ("coordinator", "architecture", "整理后的架构信息"),
        ("scout", "evolution_report", "趋势反馈指导侦察方向"),
    ],
    # 管理者 → 下游
    "coordinator": [
        ("pm", "task_spec", "分解后的任务"),
        ("engineer", "task_spec", "分配的任务"),
        ("reviewer", "test_report", "待审查的测试报告"),
        ("closer", "ops", "待闭环的操作项"),
    ],
    # 开发者 → 下游
    "engineer": [
        ("reviewer", "code_fix", "待审查的代码修复"),
        ("qa", "code_fix", "待测试的代码"),
    ],
    # 审查者 → 下游
    "reviewer": [
        ("engineer", "code_fix", "审查意见"),
        ("pm", "test_report", "审查报告"),
    ],
    # QA → 下游
    "qa": [
        ("engineer", "bug_report", "发现的 bug"),
        ("pm", "test_report", "测试报告"),
    ],
    # 产品架构师 → 下游
    "product_architect": [
        ("engineer", "prd", "产品需求文档"),
        ("engineer", "system_design", "系统设计"),
        ("pm", "task_spec", "拆解的任务规格"),
    ],
    # 知识管理者 → 下游
    "knowledge_curator": [
        ("curator", "reflexion_lesson", "经验教训"),
        ("coordinator", "reflexion_lesson", "经验教训供调度参考"),
    ],
    # 安全审计者 → 下游
    "security_auditor": [
        ("coordinator", "security", "安全问题"),
        ("maintainer", "security", "需修复的安全问题"),
    ],
    # 闭环者 → 下游
    "closer": [
        ("coordinator", "architecture", "闭环后的状态"),
        ("pm", "ops", "操作完成报告"),
    ],
    # 辩论验证者
    "debate_verifier": [
        ("coordinator", "deception", "辩论结果"),
    ],
    # PM → 下游
    "pm": [
        ("engineer", "user_story", "用户故事"),
        ("qa", "test_plan", "测试计划"),
    ],
    # 写手
    "writer": [
        ("curator", "architecture", "文档输出"),
        ("coordinator", "evolution_report", "报告输出"),
    ],
}

def get_relations(role: str) -> list[tuple[str, str, str]]:
    """获取角色的产出关系：谁消费本角色的输出。"""
    return _PRODUCE_CONSUME_MAP.get(role, [])

def get_downstream(role: str) -> list[str]:
    """获取角色的下游消费者列表。"""
    return list({consumer for consumer, _, _ in _PRODUCE_CONSUME_MAP.get(role, [])})

def get_upstream(role: str) -> list[str]:
    """获取角色的上游生产者列表（谁产出给本角色）。"""
    upstream = []
    for producer, relations in _PRODUCE_CONSUME_MAP.items():
        for consumer, _, _ in relations:
            if consumer == role:
                upstream.append(producer)
    return upstream

def get_data_flow(role: str) -> dict:
    """获取角色的完整数据流。"""
    return {
        "role": role,
        "produces_to": get_downstream(role),
        "consumes_from": get_upstream(role),
        "produce_details": get_relations(role),
    }

def get_all_roles() -> list[str]:
    """获取全部有定义的角色的列表。"""
    return sorted(_PRODUCE_CONSUME_MAP.keys())

def get_data_categories() -> dict[str, list[str]]:
    """按数据分类列出参与角色。"""
    categories: dict[str, list[str]] = {}
    for producer, relations in _PRODUCE_CONSUME_MAP.items():
        for consumer, cat, _ in relations:
            categories.setdefault(cat, set())
            categories[cat].add(producer)
            categories[cat].add(consumer)
    return {k: sorted(v) for k, v in categories.items()}

