"""
Persona/Role 注册表 — load_all, get, list_*, register。

从 models.py 拆分，职责：加载 JSON + 管理注册表索引。
"""

from __future__ import annotations
import json
import os
import sys
from typing import Any

from models import PersonaDef, RoleDef, render_prompt_from_refs


_ROLES: dict[str, RoleDef] = {}
_PERSONAS: dict[str, PersonaDef] = {}


def register(obj: PersonaDef | RoleDef) -> None:
    """注册一个人格/角色。"""
    if isinstance(obj, RoleDef):
        _ROLES[obj.name] = obj
    _PERSONAS[obj.name] = obj  # RoleDef 是 PersonaDef 子类，只需注册一次


def get(name: str) -> PersonaDef | RoleDef | None:
    """按名称获取。"""
    return _ROLES.get(name) or _PERSONAS.get(name)


def list_roles() -> list[RoleDef]:
    """列出所有 Session 角色。"""
    return list(_ROLES.values())


def list_personas(category: str | None = None) -> list[PersonaDef]:
    """列出人格，可筛选分类。"""
    if category:
        return [p for p in _PERSONAS.values() if p.category == category]
    return list(_PERSONAS.values())


def list_categories() -> dict[str, int]:
    """返回 {分类: 数量} 统计。"""
    cats: dict[str, int] = {}
    for p in _PERSONAS.values():
        cats[p.category] = cats.get(p.category, 0) + 1
    return cats


def load_all(base_dir: str | None = None) -> int:
    """从目录加载所有人格/角色定义文件，返回加载的数量。"""
    if base_dir is None:
        base_dir = os.path.join(os.path.dirname(__file__), "..")

    count = 0
    prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
    for root, _, files in os.walk(base_dir):
        for fname in sorted(files):
            if not fname.startswith("persona_") or not fname.endswith(".json"):
                continue
            path = os.path.join(root, fname)
            try:
                with open(path, encoding="utf-8") as f:
                    raw = f.read()
                data = json.loads(raw)
                items = data if isinstance(data, list) else [data]
                # Handle browser-harness profiles format: {profiles: {name: {...}}}
                if isinstance(data, dict) and 'profiles' in data and isinstance(data['profiles'], dict):
                    items = list(data['profiles'].values())
                for item in items:
                    if item.get("category") == "测试":
                        continue
                    if "lifecycle" in item or "input_signals" in item:
                        obj = RoleDef.from_dict(item)
                    else:
                        obj = PersonaDef.from_dict(item)

                    # 渲染 prompt_refs → system_prompt（若 system_prompt 为空）
                    if not obj.system_prompt and obj.prompt_refs:
                        render_kwargs = {
                            "persona_name": obj.name,
                            "persona_title": obj.title,
                        }
                        if isinstance(obj, RoleDef):
                            render_kwargs["cron_schedule"] = obj.cron_schedule
                        obj.system_prompt = render_prompt_from_refs(
                            obj.prompt_refs, prompts_dir, **render_kwargs
                        )

                    register(obj)
                    count += 1
            except json.JSONDecodeError as e:
                print(f"  [registry] JSON 解析失败 {fname}: {e}")
            except (OSError, IOError) as e:
                print(f"  [registry] 文件读写失败 {fname}: {e}")
            except Exception as e:
                print(f"  [registry] 未知错误加载 {fname}: {type(e).__name__}: {e}", file=sys.stderr)
    return count
