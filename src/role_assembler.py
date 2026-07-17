#!/usr/bin/env python3
"""Role Prompt Assembler — 动态组装 System Prompt
对标 MetaGPT: profile + goal + constraints + skills -> 完整 prompt"""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path
from typing import Any

SKILLS_ROOT = Path(os.environ.get('HERMES_SKILLS_ROOT',
    str(Path.home() / 'shared-skills' / 'hermes-origin')))
PERSONAS_DIR = Path(os.environ.get('SESSION_ROLES_ROOT', str(Path.home() / 'hermes-session-roles'))) / 'personas' / 'session-roles'
PROMPTS_DIR = Path(os.environ.get('SESSION_ROLES_ROOT', str(Path.home() / 'hermes-session-roles'))) / 'prompts'


def load_role_json(role_name: str) -> dict[str, Any]:
    for f in sorted(PERSONAS_DIR.glob('*.json')):
        if f.name.startswith('_'): continue
        data = json.loads(f.read_text())
        if data.get('name') == role_name:
            return data
    raise ValueError(f'Role {role_name} not found')


def read_skill(skill_path: str) -> str:
    """读取 skill 内容。"""
    full = SKILLS_ROOT / skill_path
    if full.exists():
        return full.read_text()
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
_BEHAVIORAL_SKILLS = {
    "pg": {"redline_enforce", "decision_ladder"},
    "coordinator": {"cluster_monitor"},
    "lr": {"redline_check"},
    # 其余角色无行为约束 skill → KNOWLEDGE 块不含技能全文
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

    if role.get('goal'):
        parts.append(f"## 目标\n{role['goal']}")

    constraints = role.get('constraints', [])
    if constraints:
        parts.append("## 红线约束\n" + "\n".join(f"- {c}" for c in constraints))

    # 仅注入行为约束 skill，其余通过原生 SKILL.md 按需加载
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
        print("Usage: role_assembler.py <role_name>")
        sys.exit(1)
    role_name = sys.argv[1]
    output = sys.argv[sys.argv.index('--output') + 1] if '--output' in sys.argv else None
    prompt = assemble_role_prompt(role_name)
    if output:
        Path(output).write_text(prompt)
        print(f"Written to {output}")
    else:
        print(prompt)


if __name__ == '__main__':
    main()
