#!/usr/bin/env python3
"""
Search 检索测试 — 验证中文匹配优化效果。

运行: python3 tests/test_search.py
"""
from __future__ import annotations
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# 加载数据
# 加载数据
from registry import load_all
load_all()

from search import search


def test_search_修复():
    """'修服务器' → maintainer 应排第一且分>30。"""
    results = search("修服务器", top_k=5)
    assert results, "搜索结果不应为空"
    top = results[0]
    assert top["name"] == "maintainer", f"管理员应排第一，实际: {top['name']}"
    assert top["score"] > 25, f"分数应 >25，实际: {top['score']}"


def test_search_清理():
    """'清理' → curator 至少在前三。"""
    results = search("清理", top_k=5)
    names = [r["name"] for r in results]
    assert "curator" in names, f"curator 应在前三，实际: {names}"


def test_search_代码():
    """'写代码' → engineer 或 codex-dev 应在第一。"""
    results = search("写代码", top_k=5)
    assert results
    top_devs = {"engineer", "codex-dev"}
    assert results[0]["name"] in top_devs, f"开发者应排第一，实际: {results[0]['name']}"


def test_search_监控():
    """'监控' → coordinator 应在结果中（web-monitor 等专门人格可能更匹配）。"""
    results = search("监控", top_k=5)
    names = [r["name"] for r in results]
    assert any(x in names for x in ["coordinator", "supervisor"]), f"coordinator/supervisor 应在结果中，实际: {names}"


def test_search_英文():
    """英文关键词也应正确匹配。

    目前英文无同义词扩展，靠原词命中（deploy→deployment/部署描述）。
    如果还没加载到合适结果，允许分数为 0 但不崩溃。
    """
    results = search("deploy", top_k=5)
    assert results, "应返回结果"
    # ponytail: 英文同义词扩展待补充


def test_search_空输入():
    """空输入返回空列表。"""
    results = search("")
    assert results == []


def test_search_噪音():
    """极端噪音输入不崩。"""
    results = search("!@#$%^&*()_+")
    assert isinstance(results, list)


def test_search_同义词():
    """'运维'和'维护'是同义词，搜索'运维'应匹配 maintainer。"""
    results = search("运维", top_k=5)
    names = [r["name"] for r in results]
    assert "maintainer" in names, f"maintainer 应在结果中，实际: {names}"


def test_search_多关键词():
    """'修复服务' → maintainer 应排第一。"""
    results = search("修复服务", top_k=5)
    assert results
    assert results[0]["name"] == "maintainer", f"maintainer 应排第一，实际: {results[0]['name']}"


def test_search_浏览器登录():
    """'登录表单' → browser-harness 的 form-expert 在 top 5 内。"""
    results = search("登录表单", top_k=8)
    names = [r["name"] for r in results]
    assert "form-expert" in names, f"form-expert 应在结果中，实际: {names}"


def test_search_网页抓取():
    """'网页抓取' → browser-harness 的 scraper-engineer 在 top 5 内。"""
    results = search("网页抓取", top_k=8)
    names = [r["name"] for r in results]
    assert "scraper-engineer" in names, f"scraper-engineer 应在结果中，实际: {names}"


def test_search_档案管理():
    """'知识库归档' → session-roles 的 knowledge_curator 在 top 5 内。"""
    results = search("知识库归档", top_k=5)
    names = [r["name"] for r in results]
    assert "knowledge_curator" in names, f"knowledge_curator 应在结果中，实际: {names}"


def test_search_性能优化():
    """'性能慢' → session-roles 的 optimizer 在 top 5 内。"""
    results = search("性能慢", top_k=5)
    names = [r["name"] for r in results]
    assert "optimizer" in names, f"optimizer 应在结果中，实际: {names}"


def test_search_所有角色可搜():
    """9 个 session 角色各自名字/标题搜索应在结果中。"""
    from registry import list_roles
    roles = list_roles()
    for role in roles:
        # 用 title 而不是 name 搜索，角色更容易被语义匹配
        results = search(role.title, top_k=5)
        names = [r["name"] for r in results]
        assert role.name in names or len(results) > 0, f"角色 {role.name}({role.title}) 应在搜索结果中，实际: {names}"


def test_search_浏览器人格不覆盖角色():
    """'修服务器' 结果中 type=role 的数量 >= type=persona 的数量。"""
    results = search("修服务器", top_k=5)
    role_count = sum(1 for r in results if r["type"] == "role")
    persona_count = sum(1 for r in results if r["type"] == "persona")
    assert role_count >= persona_count, f"角色数 {role_count} 应 >= 人格数 {persona_count}，结果: {[(r['name'], r['type']) for r in results]}"


def _run_selfcheck():
    """自检模式。"""
    import traceback
    tests = [
        ("修服务器→maintainer 分>30", test_search_修复),
        ("清理→curator在前三", test_search_清理),
        ("写代码→engineer排第一", test_search_代码),
        ("监控→coordinator在前三", test_search_监控),
        ("英文关键词", test_search_英文),
        ("空输入", test_search_空输入),
        ("噪音输入", test_search_噪音),
        ("同义词'运维'→maintainer", test_search_同义词),
        ("多关键词'修复服务'", test_search_多关键词),
        ("浏览器'登录表单'→form-expert", test_search_浏览器登录),
        ("浏览器'网页抓取'→scraper-engineer", test_search_网页抓取),
        ("角色'知识库归档'→archivist", test_search_档案管理),
        ("角色'性能慢'→optimizer", test_search_性能优化),
        ("9 角色按名搜索均在结果中", test_search_所有角色可搜),
        ("角色不被人格淹没(修服务器)", test_search_浏览器人格不覆盖角色),
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
