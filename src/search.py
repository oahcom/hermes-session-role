"""人格语义检索 — 基于关键词和描述的智能人格匹配。

零外部依赖，仅用 stdlib。

算法:
1. 中文单字+双字组分词（不依赖 jieba）
2. 字段加权评分（标题/描述权重远高于 system_prompt）
3. 关键词完整覆盖加成
"""

from __future__ import annotations
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import PersonaDef, RoleDef


def _tokenize(text: str) -> list[str]:
    """分词：中文单字+双字组+英文单词。

    单字保证每个字可匹配，双字组捕获语义。
    """
    text = text.lower().strip()
    if not text:
        return []

    chinese_chars = re.findall(r'[一-鿿]', text)
    english_words = re.findall(r'[a-zA-Z][a-zA-Z0-9\-]*', text)

    tokens = list(chinese_chars)  # 单字 unigram
    for i in range(len(chinese_chars) - 1):
        tokens.append(chinese_chars[i] + chinese_chars[i + 1])  # 双字 bigram
    tokens.extend(english_words)

    return tokens


def _field_score(query_tokens: list[str], text: str) -> float:
    """单字段匹配度 (0-1)。query token 命中 target 的比例。"""
    if not text:
        return 0.0
    target_tokens = _tokenize(text)
    if not target_tokens:
        return 0.0
    hits = sum(1 for qt in query_tokens if qt in target_tokens)
    return hits / len(query_tokens) if query_tokens else 0.0


# 字段权重：标题/描述为主，system_prompt 为辅
_WEIGHTS: dict[str, float] = {
    "title": 30.0,
    "description": 30.0,
    "category": 15.0,
    "name": 10.0,
    "prompt": 5.0,
}


def search(query: str, top_k: int = 5) -> list[dict]:
    """语义检索最匹配的角色/人格。

    Args:
        query: 用户查询（自然语言描述任务）
        top_k: 返回前N个匹配结果

    Returns:
        按相关度降序排列的列表
    """
    from models import list_roles, list_personas

    all_items = []
    all_items.extend(list_roles())
    all_items.extend(list_personas())

    if not all_items:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    query_chars = re.findall(r'[一-鿿]', query.lower())

    seen = set()
    results = []
    for item in all_items:
        if item.name in seen:
            continue
        seen.add(item.name)

        # 字段加权评分
        score = (
            _field_score(query_tokens, item.title) * _WEIGHTS["title"]
            + _field_score(query_tokens, item.description) * _WEIGHTS["description"]
            + _field_score(query_tokens, item.category) * _WEIGHTS["category"]
            + _field_score(query_tokens, item.name) * _WEIGHTS["name"]
            + _field_score(query_tokens, item.system_prompt[:200]) * _WEIGHTS["prompt"]
        )

        # 关键词完整覆盖加成：query 所有单字都在标题+描述中
        if query_chars:
            key_chars = set(re.findall(r'[一-鿿]', item.title + item.description))
            if all(c in key_chars for c in query_chars):
                score += 25.0

        role_type = "role" if hasattr(item, 'lifecycle') else "persona"
        results.append({
            "name": item.name,
            "title": item.title,
            "type": role_type,
            "score": round(score, 1),
            "category": item.category,
            "description": item.description,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
