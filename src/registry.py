"""
Persona/Role 注册表 — load_all, get, list_*, register。

从 models.py 拆分，职责：加载 JSON + 管理注册表索引。
"""

from __future__ import annotations
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from models import PersonaDef, RoleDef, render_prompt_from_refs


_ROLES: dict[str, RoleDef] = {}
_PERSONAS: dict[str, PersonaDef] = {}
_LOADED_AT: float = 0.0
_LOADED_COUNT: int = 0
_LOAD_CACHE_TTL: float = 5.0  # load_all 结果 5s 缓存，register() 时失效


def _notify_bus_contract_change(name: str, obj_type: str) -> None:
    """契约变更时写 bus 通知，失败静默。"""
    try:
        from paths import BUS_CLIENT
        bus_py = os.fspath(BUS_CLIENT)
        if os.path.isfile(bus_py):
            subprocess.run(
                [sys.executable, bus_py, "write", "architecture",
                 f"\u5951\u7ea6\u53d8\u66f4: {name} \u88ab\u8986\u76d6",
                 "--evidence", f"\u7c7b\u522b={obj_type}",
                 "--src", "registry"],
                timeout=10, capture_output=True,
            )
    except Exception:
        pass


def register(obj: PersonaDef | RoleDef) -> None:
    """注册一个人格/角色（注册即失效缓存，保证新数据可见）。"""
    global _LOADED_AT
    _LOADED_AT = 0.0
    conflict = False
    if isinstance(obj, RoleDef):
        if obj.name in _ROLES:
            conflict = True
        _ROLES[obj.name] = obj
    if obj.name in _PERSONAS:
        conflict = True
    _PERSONAS[obj.name] = obj  # RoleDef 是 PersonaDef 子类，只需注册一次
    if conflict:
        _notify_bus_contract_change(obj.name, type(obj).__name__)


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


def _load_roles_json(roles_dir: Path) -> list[dict]:
    """从目录加载角色 JSON（单一权威路径同 shared_loader）。"""
    if not roles_dir.exists():
        return []
    result: list[dict] = []
    for f in sorted(roles_dir.glob("persona_*.json")):
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
                if isinstance(data, list):
                    result.extend(data)
                else:
                    result.append(data)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  [registry] WARNING: 跳过 {f}: {e}", file=sys.stderr)
            continue
    return result


def load_all(base_dir: str | None = None) -> int:
    """从目录加载所有人格/角色定义文件，返回加载的数量（5s TTL 缓存）。"""
    global _LOADED_AT, _LOADED_COUNT
    now = time.monotonic()
    if _LOADED_AT != 0.0 and now - _LOADED_AT < _LOAD_CACHE_TTL:
        return _LOADED_COUNT
    if base_dir is None:
        base_dir = os.path.join(os.path.dirname(__file__), "..")

    count = 0
    prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

    for roles_subdir in ("personas/session-roles", "personas/browser-harness"):
        roles_path = os.path.join(base_dir, roles_subdir)
        if not os.path.isdir(roles_path):
            continue
        raw_items = _load_roles_json(Path(roles_path))
        for item in raw_items:
            # 兼容 browser-harness profiles 格式
            if isinstance(item, dict) and 'profiles' in item and isinstance(item['profiles'], dict):
                items = list(item['profiles'].values())
            else:
                items = [item] if isinstance(item, dict) else item
            for subitem in items:
                if subitem.get("category") == "测试" and "browser-harness" in roles_path:
                    continue
                try:
                    if "lifecycle" in subitem or "input_signals" in subitem:
                        obj = RoleDef.from_dict(subitem)
                    else:
                        obj = PersonaDef.from_dict(subitem)

                    # 渲染 prompt_refs → system_prompt
                    # prompt_refs 是权威源，system_prompt 是缓存
                    # 两者都存在时仍以 prompt_refs 为准，并告警
                    if obj.prompt_refs:
                        render_kwargs = {
                            "persona_name": obj.name,
                            "persona_title": obj.title,
                        }
                        if isinstance(obj, RoleDef):
                            render_kwargs["cron_schedule"] = obj.cron_schedule
                        rendered = render_prompt_from_refs(
                            obj.prompt_refs, prompts_dir, **render_kwargs
                        )
                        if rendered:
                            if obj.system_prompt and obj.system_prompt != rendered:
                                print(f"  [registry] WARNING: {obj.name} 同时有 system_prompt 和 prompt_refs，以 prompt_refs 为准", file=sys.stderr)
                            obj.system_prompt = rendered

                    register(obj)
                    count += 1
                except (json.JSONDecodeError, OSError, KeyError) as e:
                    print(f"  [registry] 加载失败 {subitem.get('name', 'unknown')}: {type(e).__name__}: {e}", file=sys.stderr)
                except Exception as e:
                    print(f"  [registry] 加载异常 {subitem.get('name', 'unknown')}: {type(e).__name__}: {e}", file=sys.stderr)
    _LOADED_AT = time.monotonic()
    _LOADED_COUNT = count
    return count
