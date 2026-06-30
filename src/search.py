"""人格语义检索 — 基于关键词和描述的智能人格匹配。

零外部依赖，仅用 stdlib。

算法:
1. 中文单字+双字组分词 + 汉语同义词扩展
2. 字段加权评分（标题/描述权重远高于 system_prompt）
3. 关键词完整覆盖加成 + 偏序匹配加成
"""

from __future__ import annotations
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import PersonaDef, RoleDef

# ── 同义词表（手动维护：运维/修复/维护/诊断/部署 等常见操作词） ──
_SYNONYM_GROUPS: list[set[str]] = [
    # ── 中文同义词 ──
    # 修复/运维组（中英打通）
    {"修", "修复", "维护", "维", "运维", "恢复", "救", "诊断", "修理", "维修",
     "fix", "repair", "patch", "hotfix", "maintain", "fixer", "bugfix"},
    # 服务/系统组
    {"服务器", "服务", "系统", "机器", "节点", "主机", "守护", "daemon",
     "server", "service", "system", "host", "daemon"},
    # 监控/检查组（中英打通）
    {"监控", "监测", "检查", "审查", "扫描", "探测", "查看", "巡检", "跟踪",
     "monitor", "observe", "watch", "check", "scan", "track", "supervise", "detect", "probe", "surveil"},
    # 部署/更新组
    {"部署", "发布", "发布", "更新", "升级", "安装", "配置",
     "deploy", "release", "publish", "update", "upgrade", "install", "setup"},
    # 清理组
    {"清理", "删除", "清除", "去重", "压缩", "熵增", "回收",
     "clean", "purge", "prune", "dedup", "compress", "gc"},
    # 安全组（中英打通）
    {"安全", "漏洞", "风险", "防护", "保护", "告警", "审计", "入侵",
     "security", "secure", "safe", "vuln", "cve", "audit", "alert"},
    # 开发组
    {"开发", "代码", "编码", "实现", "编程", "写代码", "构建",
     "developer", "develop", "code", "program", "implement", "dev"},
    # 搜索组
    {"搜索", "检索", "查找", "查询", "探测", "发掘", "发现",
     "search", "find", "query", "hunt", "survey"},
    # 智能/自动化组
    {"自动", "自动化", "智能", "自愈", "自适应", "机器人",
     "auto", "automatic", "intelligent", "robot", "agent"},
    # 优化组
    {"优化", "改进", "提升", "增强", "重构", "精简",
     "optimize", "improve", "upgrade", "refactor", "enhance"},
    # 测试组
    {"测试", "验证", "检测", "检查", "确认", "校对",
     "test", "verify", "validate", "check", "assert"},
    # 角色/人格组
    {"角色", "人格", "身份", "职责", "职能",
     "role", "profile", "identity", "persona"},
    # ── 英文同义词 ──
    {"deploy", "release", "publish", "update", "upgrade", "install"},
    {"fix", "repair", "patch", "hotfix", "resolve", "bugfix", "correct"},
    {"maintain", "maintainer", "guard", "protect", "safeguard"},
    {"scout", "explore", "discover", "hunt", "survey", "recon"},
    {"clean", "purge", "prune", "compress", "dedup", "garbage"},
    {"coordinator", "manager", "supervisor", "orchestrator", "scheduler"},
    {"consumer", "digest", "process", "absorb", "validate"},
    {"curator", "tidy", "organize", "archive"},
    {"closer", "finish", "complete", "close", "finalize"},
    {"performance", "perf", "speed", "latency", "throughput", "optimize"},
    {"architecture", "arch", "design", "structure", "framework", "system"},
    {"reflexion", "reflect", "retrospect", "review", "lesson", "retro"},
]

# ── 字段权重：标题/描述为主，system_prompt 为辅 ──
_WEIGHTS: dict[str, float] = {
    "title": 30.0,
    "description": 30.0,
    "category": 15.0,
    "name": 10.0,
    "prompt": 5.0,
}


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


def _expand_synonyms(tokens: list[str]) -> set[str]:
    """展开同义词：对每个 token 查找同义词组，返回扩展后的 token 集。"""
    expanded = set(tokens)
    for t in tokens:
        for group in _SYNONYM_GROUPS:
            if t in group:
                expanded.update(group)
                break
    return expanded


def _field_score(query_tokens: list[str], text: str, use_synonyms: bool = True) -> float:
    """单字段匹配度 (0-1)。

    支持同义词扩展：query token 和 target token 各自动展开同义词集，
    若两个扩展集有交集则视为命中。

    这样"fix"↔"维护"、deploy↔"部署" 等跨语言同义词都能匹配。
    """
    if not text:
        return 0.0
    target_tokens = _tokenize(text)
    if not target_tokens:
        return 0.0

    if use_synonyms:
        # 两边同时展开，取交集判断命中
        query_expanded = _expand_synonyms(query_tokens)
        target_expanded = _expand_synonyms(target_tokens)
        hits = 0
        for qt in query_tokens:
            qt_expanded = _expand_synonyms([qt])
            if qt_expanded & target_expanded:
                hits += 1
        return hits / len(query_tokens) if query_tokens else 0.0
    else:
        target_set = set(target_tokens)
        hits = sum(1 for qt in query_tokens if qt in target_set)
        return hits / len(query_tokens) if query_tokens else 0.0


def _score_ordered_match(query_chars: list[str], target_text: str) -> float:
    """偏序匹配加成。

    检查 query 中的字是否按顺序出现在 target 中。
    "修服务器" → 检查 '修'→'服'→'务'→'器' 是否按此顺序出现。
    加成 0-20 分。
    """
    if not query_chars or not target_text:
        return 0.0
    target_lower = target_text.lower()
    pos = -1
    matched = 0
    for c in query_chars:
        pos = target_lower.find(c, pos + 1)
        if pos >= 0:
            matched += 1
        else:
            break
    ratio = matched / len(query_chars) if query_chars else 0
    return ratio * 20.0


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

        # 字段加权评分（带同义词扩展）
        score = (
            _field_score(query_tokens, item.title) * _WEIGHTS["title"]
            + _field_score(query_tokens, item.description) * _WEIGHTS["description"]
            + _field_score(query_tokens, item.category) * _WEIGHTS["category"]
            + _field_score(query_tokens, item.name) * _WEIGHTS["name"]
            + _field_score(query_tokens, item.system_prompt) * _WEIGHTS["prompt"]
        )

        # 关键词完整覆盖加成：query 所有单字都在标题+描述+prompt 中
        if query_chars:
            key_text = item.title + item.description + item.system_prompt[:500]
            key_chars = set(re.findall(r'[一-鿿]', key_text))
            if all(c in key_chars for c in query_chars):
                score += 25.0

        # 偏序匹配加成："修服务器" → 检查字序
        if query_chars and len(query_chars) >= 3:
            ordered = _score_ordered_match(query_chars, item.title + item.description + item.system_prompt[:500])
            score += ordered

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