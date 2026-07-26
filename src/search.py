#!/usr/bin/env python3
"""Chinese semantic search using bigram tokenization."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry import load_all, list_roles, list_personas

def _tokenize(text: str) -> list[str]:
    text = text.lower().strip()
    if not text:
        return []
    chinese = re.findall(r'[一-鿿]', text)
    english = re.findall(r'[a-zA-Z][a-zA-Z0-9\-]*', text)
    tokens = []
    for i in range(len(chinese) - 1):
        tokens.append(chinese[i] + chinese[i+1])
    if len(chinese) <= 2:
        tokens.extend(chinese)
    tokens.extend(english)
    return [t for t in tokens if len(t) > 0]

def search(query: str, top_k: int = 5) -> list[dict]:
    if not query or not query.strip():
        return []
    load_all()
    all_items = list_roles()  # RoleDef includes all persona fields
    query_tokens = _tokenize(query)
    scored = []
    for item in all_items:
        search_text = f"{item.title} {item.description} {item.category} {item.name} {item.system_prompt[:200]}"
        target_tokens = _tokenize(search_text)
        score = sum(10 for qt in query_tokens if qt in target_tokens)
        if all(c in search_text for c in re.findall(r'[一-鿿]', query)):
            score += 25
        if score > 0:
            scored.append({"name": item.name, "title": item.title, "score": score})
    scored.sort(key=lambda x: -x["score"])
    return scored[:top_k]

def main():
    if len(sys.argv) < 2:
        print("Usage: search.py <query> [--top N]")
        return 1
    query = sys.argv[1]
    top_k = 5
    if "--top" in sys.argv:
        idx = sys.argv.index("--top")
        if idx + 1 < len(sys.argv):
            top_k = int(sys.argv[idx + 1])
    results = search(query, top_k)
    for r in results:
        print(f"  {r['name']:20} {r['title']:10} {r['score']}分")
    return 0

if __name__ == "__main__":
    sys.exit(main())
