"""skills_discovery.py — 动态技能发现（open-skills 模式）

自动扫描 session-roles JSON 文件中的 skills/skill_refs，
提供技能发现、生命周期管理和版本验证。

用法:
    from skills_discovery import discover_skills, get_role_skills, validate_skill_refs
"""

import json
import os
from pathlib import Path
from typing import Optional

_SESSION_ROLES_DIR = Path(__file__).resolve().parent.parent / "personas" / "session-roles"
_SKILLS_BASE = Path(os.environ.get(
    "HERMES_SKILLS_ROOT",
    str(Path.home() / "shared-skills" / "hermes-origin")
))


def discover_skills() -> dict[str, list[dict]]:
    """扫描所有角色 JSON，返回 {role: [skill_names]}"""
    result: dict[str, list[dict]] = {}
    if not _SESSION_ROLES_DIR.exists():
        return result
    for f in sorted(_SESSION_ROLES_DIR.glob("persona_*.json")):
        try:
            data = json.loads(f.read_text())
            name = data.get("name", f.stem)
            skills = data.get("skills", [])
            skill_refs = data.get("skill_refs", {})
            result[name] = [
                {"name": s, "ref": skill_refs.get(s, ""), "exists": ( _SKILLS_BASE / skill_refs.get(s, "") ).exists() if skill_refs.get(s) else False}
                for s in skills
            ]
        except (json.JSONDecodeError, KeyError):
            pass
    return result


def get_role_skills(role: str) -> list[str]:
    """获取角色具备的技能列表。"""
    registry = __import__("registry", fromlist=[""])
    registry.load_all()
    obj = registry.get(role)
    if not obj:
        return []
    skills_data = getattr(obj, "skills", [])
    return list(skills_data) if skills_data else []


def validate_skill_refs() -> list[dict]:
    """验证所有 skill_refs 是否指向真实文件。"""
    issues = []
    for role, sklist in discover_skills().items():
        for sk in sklist:
            if sk["ref"] and not sk["exists"]:
                issues.append({
                    "role": role,
                    "skill": sk["name"],
                    "ref": sk["ref"],
                    "status": "missing",
                })
    if not issues:
        return [{"status": "all_valid", "count": sum(len(v) for v in discover_skills().values())}]
    return issues


def skill_stats() -> dict:
    """技能统计摘要。"""
    all_skills = discover_skills()
    total_roles = len(all_skills)
    total_skills = sum(len(v) for v in all_skills.values())
    valid = sum(1 for v in all_skills.values() for s in v if s["exists"])
    return {
        "total_roles": total_roles,
        "total_skills": total_skills,
        "valid_refs": valid,
        "invalid_refs": total_skills - valid,
        "roles": sorted(all_skills.keys()),
    }

# Quick verify on import
def _self_check():
    stats = skill_stats()
    print(f"  ✅ {stats['total_roles']} roles, {stats['total_skills']} skills, {stats['valid_refs']}/{stats['total_skills']} refs valid")
    return stats

_self_check()
