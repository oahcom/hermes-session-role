# Search Algorithm — 中文语义检索

## Overview
Zero-dependency Chinese search using bigram tokenization + field-weighted scoring.

## Tokenization (`_tokenize`)
```python
def _tokenize(text: str) -> list[str]:
    text = text.lower().strip()
    if not text: return []
    
    # Chinese chars
    chinese = re.findall(r'[一-鿿]', text)
    # English words
    english = re.findall(r'[a-zA-Z][a-zA-Z0-9\-]*', text)
    
    tokens = []
    # Bigrams: "修服务器" → ["修服", "务器", "服务", "务器"]
    for i in range(len(chinese) - 1):
        tokens.append(chinese[i] + chinese[i+1])
    # Singles: keep for short queries
    if len(chinese) <= 2:
        tokens.extend(chinese)
    tokens.extend(english)
    return [t for t in tokens if len(t) > 0]
```

## Scoring (`_field_score`)
Each item (role/persona) has 5 fields with different weights:

| Field | Weight | Rationale |
|-------|--------|-----------|
| title | 30 | 角色名称，最高语义密度 |
| description | 30 | 简短描述，直接匹配任务意图 |
| category | 15 | 分类如"维护/生产/管理"，辅助筛选 |
| name | 10 | 内部标识符 |
| system_prompt | 5 | 长文本，降权防噪音 |

Score = sum over fields of: `exact*10 + coverage*30 + weight*30`

- **exact**: query token ∈ target tokens (10 pts each)
- **coverage**: target token coverage by query (0-30)
- **weight**: query token coverage by target (0-30)

**Bonus**: +25 if ALL query Chinese chars appear in title+description.

## Search Function
```python
def search(query: str, top_k: int = 5) -> list[dict]:
    load_all()
    all_items = list_roles() + list_personas()
    query_tokens = _tokenize(query)
    for item in all_items:
        search_text = f"{item.title} {item.description} {item.category} {item.name} {item.system_prompt[:200]}"
        target_tokens = _tokenize(search_text)
        score = sum(_field_score(q, t, w) for q,t,w in zip_fields)
        if bonus_condition: score += 25
    sort by score desc, return top_k
```

## Test Suite (tests/test_search.py)
```bash
python3 tests/test_search.py
# 9 tests, all must pass
```

### Key Test Cases
| Query | Expected #1 | Min Score |
|-------|-------------|-----------|
| "修服务器" | maintainer | 30 |
| "清理" | curator (top 3) | — |
| "写代码" | developer | — |
| "翻译文档" | i18n-localizer | — |
| "监控" | maintainer | — |
| "扫描" | scout | — |
| "部署" | maintainer | — |
| "审查" | developer | — |
| "关闭" | closer | — |

## Known Limitations
- No synonym expansion (维修 ≠ 修)
- No stemming for English
- Bigram may miss 3-char phrases
- system_prompt weight is low — can miss deep semantic matches