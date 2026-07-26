#!/usr/bin/env python3
"""validate_roles 反向测试——错误→预期失败。"""

import json, os, sys, tempfile
from pathlib import Path

# 加路径
_roles_src = str(Path.home() / "hermes-session-roles" / "src")
if _roles_src not in sys.path:
    sys.path.insert(0, _roles_src)

import validate_roles

# 创建一个最小合法角色 JSON -> main() 返回 0
_MINIMAL_OK = {
    "name": "test_role", "title": "Test", "category": "测试",
    "system_prompt": "x", "drive": "ondemand",
    "output_targets": ["bus cat=code_fix x"],
    "input_signals": [{"type": "bus", "spec": {"category": "architecture"}}],
    "workgroup": [], "skills": ["test"],
    "skill_refs": {"test": "skills/test.md"},
    "goal": "test", "constraints": ["c1"],
    "eval_criteria": ["bash -c 'echo ok'"],
    "mcp_servers": ["hex-line"], "mcp_tools": {"hex-line": ["read_file"]},
    "prompt_refs": {},
}


def _write_validate(data):
    """写临时 JSON → validate_roles.main() → 返回 rc"""
    fd, path = tempfile.mkstemp(suffix=".json")
    old = None
    try:
        os.write(fd, json.dumps(data, ensure_ascii=False).encode())
        os.close(fd)
        old = validate_roles.ROLES_DIR
        p = Path(path)
        validate_roles.ROLES_DIR = p.parent
        return validate_roles.main()
    finally:
        if old is not None:
            validate_roles.ROLES_DIR = old
        os.unlink(path)


# 测试：均期望返回非 0


def test_empty_mcp_servers_fails():
    """mcp_servers 为空→应失败"""
    d = dict(_MINIMAL_OK, mcp_servers=[], mcp_tools={})
    rc = _write_validate(d)
    assert rc != 0


def test_mcp_servers_not_list_fails():
    """mcp_servers 不是列表→应失败"""
    d = dict(_MINIMAL_OK, mcp_servers="hex-line", mcp_tools={})
    rc = _write_validate(d)
    assert rc != 0


def test_mcp_tools_missing_key_fails():
    """mcp_servers 声明 server 但 mcp_tools 无对应键→应失败"""
    d = dict(_MINIMAL_OK, mcp_servers=["hex-line"], mcp_tools={"other": ["x"]})
    rc = _write_validate(d)
    assert rc != 0


def test_mcp_tools_empty_list_fails():
    """mcp_tools[server] 为空列表→应失败"""
    d = dict(_MINIMAL_OK, mcp_servers=["hex-line"], mcp_tools={"hex-line": []})
    rc = _write_validate(d)
    assert rc != 0


def test_unknown_bus_category_fails():
    """产出分类未注册→应失败"""
    d = dict(_MINIMAL_OK, output_targets=["bus cat=unknown_xxx_category"])
    rc = _write_validate(d)
    assert rc != 0


def test_no_eval_criteria_fails():
    """eval_criteria 为空→应失败（当前未报错，记录在此）"""
    d = dict(_MINIMAL_OK, eval_criteria=[])
    rc = _write_validate(d)
    assert rc != 0


if __name__ == "__main__":
    tests = [n for n in dir() if n.startswith("test_")]
    passed, failed = 0, 0
    for name in sorted(tests):
        try:
            globals()[name]()
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            failed += 1
    print(f"\n{passed}/{passed+failed} 通过")
    raise SystemExit(0 if failed == 0 else 1)
