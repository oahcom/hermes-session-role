#!/usr/bin/env python3
"""为 23 个 persona JSON 注入 skills / skill_refs / goal / constraints 字段。"""
import json, os
from pathlib import Path

PERSONAS_DIR = Path(os.environ.get('SESSION_ROLES_ROOT', str(Path.home() / 'hermes-session-roles'))) / 'personas' / 'session-roles'
SKILLS_ROOT = Path(os.environ.get('HERMES_SKILLS_ROOT', str(Path.home() / 'shared-skills' / 'hermes-origin')))

# 角色 -> 技能映射（基于职责定义对标 MetaGPT actions）
ROLE_SKILLS = {
    "maintainer": ["health_check", "diagnose", "auto_fix", "verify_fix"],
    "scout": ["github_scan", "trend_analysis", "opportunity_eval", "report_write"],
    "curator": ["skill_audit", "skill_sync", "category_map", "quality_gate"],
    "coordinator": ["cluster_monitor", "sentinel_audit", "cross_role_dispatch", "escalation", "brief_write"],
    "engineer": ["write_code", "write_tests", "refactor", "debug", "git_commit"],
    "closer": ["backlog_scan", "close_loop", "close_report"],
    "optimizer": ["profile_analysis", "bottleneck_identify", "optimization_apply", "benchmark"],
    "codex-dev": ["goal_manage", "bus_poll", "code_write", "verify_commit", "budget_wrap"],
    "debate_verifier": ["argument_parse", "evidence_check", "verdict_write", "escalation"],
    "product_architect": ["intake_analysis", "prd_write", "system_design", "task_spec", "adr_write"],
    "knowledge_curator": ["knowledge_extract", "knowledge_organize", "knowledge_verify", "knowledge_publish"],
    "security_auditor": ["owasp_scan", "threat_model", "vuln_assess", "compliance_check"],
    "pm": ["requirement_analysis", "user_story_write", "priority_rank", "acceptance_verify"],
    "reviewer": ["d1_correctness", "d2_security", "d3_maintainability", "d4_performance", "d5_consistency", "d6_testability"],
    "qa": ["test_plan", "test_case_write", "test_execute", "test_report"],
    "devops": ["deploy_plan", "infra_provision", "monitor_setup", "incident_response", "rollback"],
    "writer": ["doc_structure", "api_doc_write", "changelog_write", "readme_write", "version_bump"],
    "lr": ["tech_selection", "redline_check", "decision_record", "tradeoff_analysis"],
    "pg": ["decision_ladder", "impl_plan", "risk_assess", "redline_enforce"],
    "investigator_python": ["evidence_chain", "stack_trace_analysis", "root_cause_identify", "fix_propose"],
    "investigator_senior": ["cross_stack_correlation", "architecture_review", "systemic_root_cause", "fix_propose"],
    "investigator_general": ["triage_decision", "log_analysis", "escalation_rule", "fix_propose"],
    "ccs-monitor": ["ccs_health_check", "log_anomaly_detect", "alert_write"],
}

# 技能 -> 子目录映射
SKILL_DIR_MAP = {
    "write_code": "code", "write_tests": "code", "refactor": "code", "debug": "code", "git_commit": "code",
    "d1_correctness": "review", "d2_security": "review", "d3_maintainability": "review",
    "d4_performance": "review", "d5_consistency": "review", "d6_testability": "review",
    "intake_analysis": "arch", "prd_write": "arch", "system_design": "arch", "task_spec": "arch", "adr_write": "arch",
    "requirement_analysis": "pm", "user_story_write": "pm", "priority_rank": "pm", "acceptance_verify": "pm",
    "test_plan": "qa", "test_case_write": "qa", "test_execute": "qa", "test_report": "qa",
    "deploy_plan": "devops", "infra_provision": "devops", "monitor_setup": "devops",
    "incident_response": "devops", "rollback": "devops",
    "doc_structure": "writer", "api_doc_write": "writer", "changelog_write": "writer",
    "readme_write": "writer", "version_bump": "writer",
    "tech_selection": "lr", "redline_check": "lr", "decision_record": "lr", "tradeoff_analysis": "lr",
    "decision_ladder": "pg", "impl_plan": "pg", "risk_assess": "pg", "redline_enforce": "pg",
    "evidence_chain": "investigator", "stack_trace_analysis": "investigator", "root_cause_identify": "investigator",
    "fix_propose": "investigator", "cross_stack_correlation": "investigator", "architecture_review": "investigator",
    "systemic_root_cause": "investigator", "triage_decision": "investigator", "log_analysis": "investigator",
    "escalation_rule": "investigator",
    "owasp_scan": "security", "threat_model": "security", "vuln_assess": "security", "compliance_check": "security",
    "cluster_monitor": "coordination", "sentinel_audit": "coordination", "cross_role_dispatch": "coordination",
    "escalation": "coordination", "brief_write": "coordination",
    "backlog_scan": "closing", "close_loop": "closing", "close_report": "closing",
    "profile_analysis": "optimization", "bottleneck_identify": "optimization",
    "optimization_apply": "optimization", "benchmark": "optimization",
    "goal_manage": "codex", "bus_poll": "codex", "code_write": "codex",
    "verify_commit": "codex", "budget_wrap": "codex",
    "argument_parse": "debate", "evidence_check": "debate", "verdict_write": "debate",
    "knowledge_extract": "knowledge", "knowledge_organize": "knowledge",
    "knowledge_verify": "knowledge", "knowledge_publish": "knowledge",
    "health_check": "maintenance", "diagnose": "maintenance", "auto_fix": "maintenance", "verify_fix": "maintenance",
    "skill_audit": "curation", "skill_sync": "curation", "category_map": "curation", "quality_gate": "curation",
    "github_scan": "research", "trend_analysis": "research", "opportunity_eval": "research", "report_write": "research",
    "ccs_health_check": "monitor", "log_anomaly_detect": "monitor", "alert_write": "monitor",
}


def inject():
    count = 0
    for f in sorted(PERSONAS_DIR.glob("*.json")):
        if f.name.startswith("_"):
            continue
        data = json.loads(f.read_text())
        name = data.get("name", "")
        skills = ROLE_SKILLS.get(name, [])
        if not skills:
            print(f"  SKIP {name} ({f.name}): no skills mapping")
            continue

        data["skills"] = skills
        data["skill_refs"] = {
            s: f"skills/{SKILL_DIR_MAP.get(s, 'misc')}/{s}.md" for s in skills
        }
        if not data.get("goal"):
            data["goal"] = data.get("description", "")
        if not data.get("constraints"):
            cat = data.get("category", "通用")
            data["constraints"] = [
                f"遵循 {cat} 角色红线",
                "不做超出职责范围的事",
                "输出必须可验证",
            ]

        f.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        count += 1
        print(f"  OK {name} ({f.name}): +{len(skills)} skills")

    print(f"\n共注入 {count} 个角色")


if __name__ == "__main__":
    inject()
