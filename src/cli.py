#!/usr/bin/env python3
"""CLI — persona list/show/load/search。

复用 Browser Harness CLI 设计。
"""
import argparse
import json
import sys
import os
from typing import Any

from paths import ensure_paths
ensure_paths()

from registry import load_all, get, list_roles, list_personas, list_categories
from search import search as semantic_search


def cmd_list(args: Any) -> int:
    """List all personas/roles."""
    load_all()
    cats = list_categories()

    if args.roles:
        roles = list_roles()
        print(f"Session 角色 ({len(roles)}个):")
        for r in roles:
            print(f"  {r.name:<25} {r.title:<10} [{r.lifecycle}] {r.description}")
        return

    if args.category:
        personas = list_personas(args.category)
        print(f"分类: {args.category} ({len(personas)}个)")
    else:
        personas = list_personas()
        print(f"共 {len(personas)} 个人格/角色，分 {len(cats)} 个分类:")
        for cat, count in sorted(cats.items()):
            print(f"  {cat}: {count}")

    for p in personas:
        print(f"  {p.name:<30} {p.title:<15} {p.description}")


def cmd_show(args: Any) -> int:
    """Show details of a persona/role."""
    load_all()
    obj = get(args.name)
    if not obj:
        print(f"未找到: {args.name}")
        return
    print(json.dumps(obj.to_dict(), ensure_ascii=False, indent=2))


def cmd_search(args: Any) -> int:
    """Semantic search for personas/roles."""
    load_all()
    results = semantic_search(args.query, top_k=args.top)
    if not results:
        print("未找到匹配")
        return
    print(f"任务: {args.query}")
    print(f"匹配结果 (前{args.top}个):\n")
    for i, hit in enumerate(results, 1):
        t = "角色" if hit["type"] == "role" else "人格"
        print(f"  {i}. [{t}] {hit['name']:<25} {hit['score']:5.1f}分  {hit['description']}")


def cmd_load(args: Any) -> int:
    """Load a persona — output system prompt."""
    load_all()
    obj = get(args.name)
    if not obj:
        print(f"未找到: {args.name}")
        return
    context = {}
    if args.extra:
        for item in args.extra:
            if "=" in item:
                k, v = item.split("=", 1)
                context[k] = v
    prompt = obj.render_system_prompt(**context)
    if args.json:
        print(json.dumps({
            "persona": obj.name,
            "title": obj.title,
            "system_prompt": prompt,
            "config_overrides": obj.config_overrides if hasattr(obj, 'config_overrides') else {},
            "eval_criteria": obj.eval_criteria if hasattr(obj, 'eval_criteria') else [],
        }, ensure_ascii=False, indent=2))
    else:
        print(prompt)


def main() -> int:
    parser = argparse.ArgumentParser(description="Session Roles CLI")
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="列出人格/角色")
    p_list.add_argument("--category", "-c", help="按分类筛选")
    p_list.add_argument("--roles", "-r", action="store_true", help="只显示角色")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="查看详情")
    p_show.add_argument("name")
    p_show.set_defaults(func=cmd_show)

    p_load = sub.add_parser("load", help="加载提示词")
    p_load.add_argument("name")
    p_load.add_argument("--json", action="store_true")
    p_load.add_argument("--extra", "-e", action="append")
    p_load.set_defaults(func=cmd_load)

    p_search = sub.add_parser("search", help="语义搜索")
    p_search.add_argument("query")
    p_search.add_argument("--top", "-n", type=int, default=5)
    p_search.set_defaults(func=cmd_search)

    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
