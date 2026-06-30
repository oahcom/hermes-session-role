"""人格语义检索 — 基于关键词和描述的智能人格匹配。

零外部依赖，仅用 stdlib 的 difflib 实现。

直接复用 Browser Harness 的 search.py 算法：
1. 中文双字组(bigram)分词（不依赖 jieba）
2. 4 维评分：精确匹配 + 序列相似度 + 覆盖率 + 权重匹配
"""

from __future__ import annotations
import re
from difflib import SequenceMatcher
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import PersonaDef, RoleDef


def _tokenize(text: str) -> list[str]:
    """分词 + 中文双字组（bigram）。

    不依赖 jieba，用滑窗双字组捕获中文语义。
    英文单词保持原样。
    """
    text = text.lower().strip()
    if not text:
        return []

    chinese_chars = re.findall(r'[一-鿿]', text)
    english_words = re.findall(r'[a-zA-Z][a-zA-Z0-9\-]*', text)

    tokens = []
    # 中文双字组 (bigram)
    for i in range(len(chinese_chars) - 1):
        tokens.append(chinese_chars[i] + chinese_chars[i + 1])
    if len(chinese_chars) <= 2:
        tokens.extend(chinese_chars)
    tokens.extend(english_words)

    return [t for t in tokens if len(t) > 0]


def _compute_score(query_tokens: list[str], target_tokens: list[str]) -> float:
    """计算两个 token 列表之间的匹配分数 (0-100)。"""
    if not query_tokens or not target_tokens:
        return 0.0

    query_str = ' '.join(query_tokens)
    target_str = ' '.join(target_tokens)

    # 1. 精确匹配
    exact_score = sum(10.0 for qt in query_tokens if qt in target_tokens)

    # 2. 序列相似度
    seq_ratio = SequenceMatcher(None, query_str, target_str).ratio()
    seq_score = seq_ratio * 30.0

    # 3. 覆盖率
    target_in_query = sum(
        1 for tt in target_tokens
        if any(tt.startswith(qt) or qt.startswith(tt) for qt in query_tokens)
    )
    coverage = target_in_query / len(target_tokens) if target_tokens else 0
    coverage_score = coverage * 30.0

    # 4. 权重匹配
    query_in_target = sum(
        1 for qt in query_tokens
        if any(t.startswith(qt) or qt.startswith(t) for t in target_tokens)
    )
    weight_ratio = query_in_target / len(query_tokens) if query_tokens else 0
    weight_score = weight_ratio * 30.0

    return min(exact_score + seq_score + coverage_score + weight_score, 100.0)


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

    seen = set()
    results = []
    for item in all_items:
        if item.name in seen:
            continue
        seen.add(item.name)
        search_text = f"{item.title} {item.description} {item.category} {item.name} {item.system_prompt[:200]}"
        target_tokens = _tokenize(search_text)
        score = _compute_score(query_tokens, target_tokens)
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
