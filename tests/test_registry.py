#!/usr/bin/env python3
"""Registry 操作测试 — 数据加载、角色/人格增删查。

运行: python3 tests/test_registry.py
"""
from __future__ import annotations
import os
import sys
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from registry import load_all, get, list_roles, list_personas, list_categories, register
from models import PersonaDef, RoleDef

EXPECTED_ROLES = 26  # session-roles + test roles
# Total personas loaded: 56 (26 session-roles + 30 browser-harness non-test)
EXPECTED_TOTAL = 56


def test_load_all_count():
    """加载后检查总数（动态计算而非硬编码）。"""
    n = load_all()
    personas = list_personas()
    assert n >= 50, f"load_all 返回 {n}，期望 >= 50"
    assert len(personas) == n, f"list_personas 返回 {len(personas)}，load_all 返回 {n}"


def test_list_roles():
    """list_roles 返回 >= 20 角色，包含关键名称。"""
    roles = list_roles()
    assert len(roles) >= 20, f"角色数 {len(roles)}，期望 >= 20"
    names = {r.name for r in roles}
    for required in ("maintainer", "scout", "curator", "coordinator", "engineer", "closer",
                     "optimizer", "codex-dev", "ccs-monitor", "debate_verifier",
                     "product_architect", "knowledge_curator", "security_auditor",
                     "pm", "reviewer", "qa", "devops", "writer", "lr", "pg",
                     "investigator_python", "investigator_senior", "investigator_general"):
        assert required in names, f"缺少角色 '{required}'"


def test_list_personas():
    """list_personas 返回所有人格（含角色）。"""
    all_p = list_personas()
    assert len(all_p) >= 50, f"人格总数 {len(all_p)}，期望 >= 50"


def test_get_by_name():
    """get('maintainer') 返回正确角色。"""
    r = get("maintainer")
    assert r is not None, "maintainer 不应为 None"
    assert r.name == "maintainer"
    assert r.title == "运维者"


def test_get_by_name_nonexistent():
    """get('nonexistent') 返回 None。"""
    assert get("nonexistent") is None


def test_categories():
    """list_categories 返回正确的分类统计（总量 = 加载总数）。"""
    all_p = list_personas()
    cats = list_categories()
    assert isinstance(cats, dict)
    assert len(cats) >= 5, f"分类数 {len(cats)} 过少"
    assert sum(cats.values()) == len(all_p), f"分类人数和 {sum(cats.values())} != 人格数 {len(all_p)}"


def test_register_role():
    """注册一个新角色后能查到。"""
    r = RoleDef(
        name="test-role",
        title="测试角色",
        description="临时测试用",
        category="测试",
        system_prompt="你是 {persona_name}",
        lifecycle="ondemand",
        drive="ondemand",
    )
    register(r)
    loaded = get("test-role")
    assert loaded is not None, "注册后应能查到"
    assert loaded.name == "test-role"
    assert isinstance(loaded, RoleDef)


def test_register_persona():
    """注册一个人格，在 personas 中但在 roles 中不可见。"""
    p = PersonaDef(
        name="test-persona-only",
        title="纯人格",
        description="非角色人格",
        category="测试",
        system_prompt="你是 {persona_name}",
    )
    register(p)
    all_p = list_personas()
    names = {x.name for x in all_p}
    assert "test-persona-only" in names, "新人格应在 list_personas 中"
    roles = list_roles()
    role_names = {r.name for r in roles}
    assert "test-persona-only" not in role_names, "纯人格不应在 list_roles 中"


def test_load_all_script_validates():
    """validate_roles.py 语法通过（忽略 eval_criteria 预期警告）。"""
    script = os.path.join(os.path.dirname(__file__), "..", "src", "validate_roles.py")
    result = subprocess.run(
        [sys.executable, script],
        capture_output=True, text=True, cwd=os.path.dirname(script)
    )
    assert result.returncode == 0, (
        f"validate_roles.py 应返回 0，实际 {result.returncode}\n"
        f"stdout: {result.stdout}"
    )
    assert "角色数:" in result.stdout or "个角色" in result.stdout


def _run_selfcheck():
    """自检模式。"""
    import traceback
    tests = [
        ("load_all 总数正确", test_load_all_count),
        ("list_roles 返回 14 角色含关键名称", test_list_roles),
        ("list_personas 返回所有人格", test_list_personas),
        ("get('maintainer') 正确", test_get_by_name),
        ("get('nonexistent') 返回 None", test_get_by_name_nonexistent),
        ("list_categories 正确", test_categories),
        ("register_role 注册并查询", test_register_role),
        ("register_persona 注册纯人格", test_register_persona),
        ("validate_roles.py 通过", test_load_all_script_validates),
    ]
    passed, failed = 0, 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ✅ {name}")
            passed += 1
        except Exception:
            print(f"  ❌ {name}")
            traceback.print_exc()
            failed += 1
    print(f"\n结果: {passed}/{passed + failed} 通过")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_selfcheck())
