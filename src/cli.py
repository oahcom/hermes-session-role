#!/usr/bin/env python3
"""CLI for hermes-session-roles — list/show/load/search."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry import load_all, list_roles, get

def main():
    load_all()
    if len(sys.argv) < 2:
        print("Usage: cli.py {list|show|load|search}")
        return 1
    cmd = sys.argv[1]
    if cmd == "list":
        roles = list_roles()
        print(f"角色数: {len(roles)}")
        for r in roles:
            print(f"  {r.name}: {r.title}")
    elif cmd == "show" and len(sys.argv) > 2:
        obj = get(sys.argv[2])
        if obj:
            print(json.dumps(obj.to_dict() if hasattr(obj, 'to_dict') else obj.__dict__, indent=2, ensure_ascii=False))
        else:
            print(f"未找到: {sys.argv[2]}")
    elif cmd == "load" and len(sys.argv) > 2:
        obj = get(sys.argv[2])
        if obj:
            print(obj.system_prompt[:2000] if obj.system_prompt else "(empty)")
        else:
            print(f"未找到: {sys.argv[2]}")
    elif cmd == "search" and len(sys.argv) > 2:
        query = sys.argv[2]
        roles = list_roles()
        results = []
        for r in roles:
            text = f"{r.title} {r.description}"
            if query in text:
                results.append(r)
        for r in results[:5]:
            print(f"  {r.name}: {r.title}")
    else:
        print("Usage: cli.py {list|show|load|search}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
