"""Search regression tests."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from search import search

def test_search_修复():
    results = search("修服务器", top_k=5)
    assert len(results) > 0
    assert results[0]["score"] >= 5

def test_search_清理():
    results = search("清理", top_k=5)
    assert len(results) > 0

def test_search_代码():
    results = search("写代码", top_k=5)
    assert len(results) > 0

def test_search_监控():
    results = search("监控", top_k=5)
    assert len(results) > 0

def test_search_英文():
    results = search("git commit", top_k=5)
    assert isinstance(results, list)

def test_search_空输入():
    results = search("", top_k=5)
    assert results == [], f"空查询应返回空列表, got {results}"

def test_search_噪音():
    results = search("@#$%^&*", top_k=5)
    assert isinstance(results, list)

def test_search_多关键词():
    results = search("修复服务", top_k=5)
    assert len(results) > 0

def test_search_所有角色可搜():
    results = search("维护", top_k=10)
    assert len(results) >= 1
