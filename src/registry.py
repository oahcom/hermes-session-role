"""
Persona/Role 注册表 — load_all, get, list_*, register。

从 models.py 拆分，职责：加载 JSON + 管理注册表索引。
"""

from __future__ import annotations
import json
import os
from typing import Any

from models import PersonaDef, RoleDef


_ROLES: dict[str, RoleDef] = {}
_PERSONAS: dict[str, PersonaDef] = {}


def register(obj: PersonaDef | RoleDef) -> None:
    """注册一个人格/角色。"""
    if isinstance(obj, RoleDef):
        _ROLES[obj.name] = obj
        _PERSONAS[obj.name] = obj
    if isinstance(obj, PersonaDef):
        _PERSONAS[obj.name] = obj


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
    for root, _, files in os.walk(base_dir):
        for fname in sorted(files):
            if not fname.startswith("persona_") or not fname.endswith(".json"):
                continue
            path = os.path.join(root, fname)
            try:
                with open(path) as f:
                    data = json.load(f)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if "lifecycle" in item or "input_signals" in item:
                        register(RoleDef.from_dict(item))
                    else:
                        register(PersonaDef.from_dict(item))
                    count += 1
            except Exception as e:
                print(f"  [registry] 加载 {fname} 失败: {e}")
    return count
