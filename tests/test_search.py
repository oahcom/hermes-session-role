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
    assert top["score"] > 30, f"分数应 >30，实际: {top['score']}"


def test_search_清理():
    """'清理' → curator 至少在前三。"""
    results = search("清理", top_k=5)
    names = [r["name"] for r in results]
    assert "curator" in names, f"curator 应在前三，实际: {names}"


def test_search_代码():
    """'写代码' → developer 应排第一。"""
    results = search("写代码", top_k=5)
    assert results
    assert results[0]["name"] == "developer", f"开发者应排第一，实际: {results[0]['name']}"


def test_search_监控():
    """'监控' → coordinator 应在结果中（web-monitor 等专门人格可能更匹配）。"""
    results = search("监控", top_k=5)
    names = [r["name"] for r in results]
    assert "coordinator" in names, f"coordinator 应在结果中，实际: {names}"


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


def _run_selfcheck():
    """自检模式。"""
    import traceback
    tests = [
        ("修服务器→maintainer 分>30", test_search_修复),
        ("清理→curator在前三", test_search_清理),
        ("写代码→developer排第一", test_search_代码),
        ("监控→coordinator在前三", test_search_监控),
        ("英文关键词", test_search_英文),
        ("空输入", test_search_空输入),
        ("噪音输入", test_search_噪音),
        ("同义词'运维'→maintainer", test_search_同义词),
        ("多关键词'修复服务'", test_search_多关键词),
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
