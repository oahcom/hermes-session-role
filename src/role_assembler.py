#!/usr/bin/env python3
"""Role Prompt Assembler — 动态组装 System Prompt
对标 MetaGPT: profile + goal + constraints + skills -> 完整 prompt"""
from __future__ import annotations
import json, sys
import os
from pathlib import Path
from typing import Any

from paths import SESSION_ROLES_PERSONAS as PERSONAS_DIR, PROMPTS_DIR, SKILLS_ROOT


def load_role_json(role_name: str) -> dict[str, Any]:
    """按名称加载角色 JSON（委托 registry.get + shared_loader 实现）。"""
    # 优先通过 registry 获取，避免重复 IO
    try:
        from registry import get
        obj = get(role_name)
        if obj is not None:
            return obj.to_dict()
    except (KeyError, FileNotFoundError):
        pass
    # fallback: 直接读文件
    for f in sorted(PERSONAS_DIR.glob('*.json')):
        if f.name.startswith('_'): continue
        data = json.loads(f.read_text())
        if data.get('name') == role_name:
            return data
    raise ValueError(f'Role {role_name} not found')


def read_skill(skill_path: str) -> str:
    """读取 skill 内容。"""
    full = SKILLS_ROOT / skill_path
    # Trust boundary: skill_path may originate from persona JSON skill_refs.
    # Defend against path traversal regardless of JSON validation trust.
    real_root = os.path.realpath(SKILLS_ROOT)
    real_full = os.path.realpath(full)
    if not real_full.startswith(real_root + os.sep) and real_full != real_root:
        raise PermissionError(f'PATH ESCAPE: skill_path {skill_path!r} resolves outside SKILLS_ROOT')
    if full.exists():
        return full.read_text()
    # skills 实际存储为 dir/SKILL.md 而非 dir.md（skill_refs 的路径如 skills/code/write_code.md → skills/code/write_code/SKILL.md）
    alt = SKILLS_ROOT / skill_path.replace(".md", "") / "SKILL.md"
    if alt.exists():
        return alt.read_text()
    for fallback in [PROMPTS_DIR / 'skills' / skill_path, PROMPTS_DIR / skill_path]:
        if fallback.exists():
            return fallback.read_text()
    # 第 4 条回退路径（仅限 base.md 悬挂引用修复）
    if skill_path == "base.md":
        ws_base = Path.home() / "ccs-workspaces" / "base.md"
        if ws_base.exists():
            return ws_base.read_text()
    return f'[SKILL NOT FOUND: {skill_path}]'


# 行为约束 skill 清单（仅这些会注入 KNOWLEDGE 块，其余通过原生 SKILL.md 按需加载）
# 基于 JSON 中定义的 skills 字段自动生成，包含所有定义了 skills 的角色
_BEHAVIORAL_SKILLS = {
    "maintainer": {"health_check", "diagnose", "auto_fix", "verify_fix"},
    "scout": {"github_scan", "trend_analysis", "opportunity_eval", "report_write"},
    "curator": {"skill_audit", "skill_sync", "category_map", "quality_gate"},
    "coordinator": {"cluster_monitor", "sentinel_audit", "cross_role_dispatch", "escalation", "brief_write"},
    "engineer": {"write_code", "write_tests", "refactor", "debug", "git_commit"},
    "closer": {"backlog_scan", "close_loop", "close_report"},
    "optimizer": {"profile_analysis", "bottleneck_identify", "optimization_apply", "benchmark"},
    "codex-dev": {"goal_manage", "bus_poll", "code_write", "verify_commit", "budget_wrap"},
    "ccs-monitor": {"ccs_health_check", "log_anomaly_detect", "alert_write"},
    "debate_verifier": {"argument_parse", "evidence_check", "verdict_write", "escalation"},
    "product_architect": {"intake_analysis", "prd_write", "system_design", "task_spec", "adr_write"},
    "knowledge_curator": {"knowledge_extract", "knowledge_organize", "knowledge_verify", "knowledge_publish"},
    "security_auditor": {"owasp_scan", "threat_model", "vuln_assess", "compliance_check"},
    "pm": {"requirement_analysis", "user_story_write", "priority_rank", "acceptance_verify"},
    "reviewer": {"d1_correctness", "d2_security", "d3_maintainability", "d4_performance", "d5_consistency", "d6_testability"},
    "qa": {"test_plan", "test_case_write", "test_execute", "test_report"},
    "devops": {"deploy_plan", "infra_provision", "monitor_setup", "incident_response", "rollback"},
    "writer": {"doc_structure", "api_doc_write", "changelog_write", "readme_write", "version_bump"},
    "lr": {"tech_selection", "redline_check", "decision_record", "tradeoff_analysis"},
    "pg": {"decision_ladder", "impl_plan", "risk_assess", "redline_enforce"},
    "investigator_python": {"evidence_chain", "stack_trace_analysis", "root_cause_identify", "fix_propose"},
    "investigator_senior": {"cross_stack_correlation", "architecture_review", "systemic_root_cause", "fix_propose"},
    "investigator_general": {"triage_decision", "log_analysis", "escalation_rule", "fix_propose"},
    "archivist": {"shell_scripts", "scheduler"},
    "ccs-coordinator": {"ccs_ops", "monitor"},
    "consumer": {"bus_ops", "workflow"},
    "public": {"communication", "routing"},
    "rebutter": {"debate", "analysis"},
    "regression_test_return": {"testing", "reporting"},
    "research": ["research", "writing"],
    "test": ["health_check", "diagnose", "auto_fix", "verify_fix"],
}


def is_behavioral(role_name: str, skill_name: str) -> bool:
    return skill_name in _BEHAVIORAL_SKILLS.get(role_name, set())


def assemble_role_prompt(role_name: str) -> str:
    role = load_role_json(role_name)
    parts = []

    parts.append(f"# {role['name']} - {role.get('title', role['name'])}")
    parts.append(f"## 定位\n{role.get('description', '')}")

    prompt_refs = role.get('prompt_refs', {})
    # base.md 修复：read_skill 已有第4回退路径
    if prompt_refs.get('base'):
        base_content = read_skill(prompt_refs['base'])
        if base_content and "[SKILL NOT FOUND" not in base_content:
            parts.append("## 通用红线\n" + base_content)

    # 加载角色专用 prompt (如 roles/lr.md)
    if prompt_refs.get('role'):
        role_content = read_skill(prompt_refs['role'])
        if role_content and "[SKILL NOT FOUND" not in role_content:
            parts.append("## 角色系统提示词\n" + role_content)

    # 驱动方式 — 按角色适配生成（不再使用静态 mixin）
    drive = role.get('drive', 'ondemand')
    drive_lines = [f"## 驱动方式: {drive.title()}"]
    if drive == 'ondemand':
        drive_lines.extend([
            "由 `ccs start` 或上游 `ccs send` 唤醒，常驻 tmux 等待任务。",
            "",
            "### 等待信号",
        ])
        sigs = role.get('input_signals', [])
        for sig in sigs:
            cat = sig.get('spec', {}).get('category', '') if sig.get('type') == 'bus' else sig.get('source', '')
            flt = sig.get('filter', '')
            drive_lines.append(f"- `cat={cat}` filter={flt}" if flt else f"- `cat={cat}`")
        drive_lines.extend([
            "",
            "### 产出物",
        ])
        for t in role.get('output_targets', []):
            drive_lines.append(f"- {t}")
        drive_lines.extend([
            "",
            "### 工作循环",
            "1. 接收任务（上游 ccs send 或 bus 消息）",
            "2. 执行任务",
            "3. 验证结果",
            "4. 通知完成（bus 通知下游或 wf complete）",
            "5. 进入待机，等待下一轮任务",
            "",
            "### 注意事项",
            "- 每个任务完成后不得退出 tmux session（lifecycle=infinite）",
            "- 没有待办时等待上游驱动，不自行巡检",
        ])
    elif drive == 'cron':
        cron = role.get('cron_schedule', '')
        drive_lines.append(f"由 cron-worker 按计划唤醒: `{cron}`。每次唤醒后执行检查任务，完成后退出等待下次唤醒。")
    elif drive == 'goal':
        drive_lines.append("由 goal/agentic-loop 驱动，主动执行直至目标达成。")
    else:
        drive_lines.append(f"驱动模式: {drive}")
    parts.append("\n".join(drive_lines))

    if role.get('goal'):
        parts.append(f"## 目标\n{role['goal']}")

    constraints = role.get('constraints', [])
    if constraints:
        parts.append("## 红线约束\n" + "\n".join(f"- {c}" for c in constraints))

    skills = role.get('skills', [])
    skill_refs = role.get('skill_refs', {})
    behavioral_skills = [s for s in skills if is_behavioral(role_name, s)]
    if behavioral_skills:
        skill_parts = []
        for skill in behavioral_skills:
            skill_doc = read_skill(skill_refs.get(skill, f'skills/{skill}.md'))
            skill_parts.append(f"### 技能: {skill}\n{skill_doc}")
        parts.append("## 行为约束\n" + "\n\n".join(skill_parts))

    input_sigs = role.get('input_signals', [])
    if input_sigs:
        lines = ["## 输入信号"]
        for sig in input_sigs:
            if 'type' in sig:
                spec = sig.get('spec', {})
                cat = spec.get('category', 'custom')
                flt = sig.get('filter', '')
                lines.append(f"- **{sig['type']}** cat={cat} filter={flt}")
            elif 'source' in sig:
                lines.append(f"- **bus** cat={sig['source']} filter={sig.get('filter', '')}")
        parts.append("\n".join(lines))

    outputs = role.get('output_targets', [])
    if outputs:
        parts.append("## 输出目标\n" + "\n".join(f"- {t}" for t in outputs))

    eval_criteria = role.get('eval_criteria', [])
    if eval_criteria:
        parts.append("## 评估标准\n" + "\n".join(f"- {c}" for c in eval_criteria))

    mistakes = role.get('mistakes', [])
    if mistakes:
        parts.append("## 历史教训\n" + "\n".join(str(m) for m in mistakes))

    return "\n\n".join(parts)


def main():
    if len(sys.argv) < 2:
        print("Usage: role_assembler.py <role_name> [--output <path>] [--inject <claude.md path>]")
        sys.exit(1)
    role_name = sys.argv[1]
    output = sys.argv[sys.argv.index('--output') + 1] if '--output' in sys.argv else None
    inject_path = sys.argv[sys.argv.index('--inject') + 1] if '--inject' in sys.argv else None
    prompt = assemble_role_prompt(role_name)
    if inject_path:
        path = Path(inject_path)
        content = path.read_text()
        start_marker = '<!-- KNOWLEDGE:START -->'
        end_marker = '<!-- KNOWLEDGE:END -->'
        if start_marker in content and end_marker in content:
            start = content.index(start_marker)
            end = content.index(end_marker) + len(end_marker)
            new_block = f'{start_marker}\n{prompt}\n{end_marker}'
            path.write_text(content[:start] + new_block + content[end:])
            print(f"Injected into {inject_path}")
        else:
            print(f"ERROR: {inject_path} missing KNOWLEDGE markers", file=sys.stderr)
            sys.exit(1)
    elif output:
        Path(output).write_text(prompt)
        print(f"Written to {output}")
    else:
        print(prompt)


if __name__ == '__main__':
    # Inline self-check: path traversal must be blocked
    _ = read_skill('base.md')  # normal call still works
    try:
        read_skill('../../etc/passwd')
    except PermissionError as e:
        assert 'PATH ESCAPE' in str(e), f"Expected PATH ESCAPE in error, got: {e}"
    else:
        raise AssertionError('read_skill should reject path traversal')
    main()
