"""
Persona/Role 注册表 — load_all, get, list_*。

从 models.py 拆分，职责：加载 JSON + 管理注册表索引。
"""

from __future__ import annotations
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from models import PersonaDef, RoleDef, render_prompt_from_refs


_ROLES: dict[str, RoleDef] = {}
_PERSONAS: dict[str, PersonaDef] = {}
_LOADED_AT: float = 0.0
_LOADED_COUNT: int = 0
_LOADED_BASE_DIR: str | None = None  # 缓存归属目录：换目录加载不得命中旧缓存
_LOAD_CACHE_TTL: float = 5.0  # load_all 结果 5s 缓存

# 写路径锁（RLock，load_all 在写回缓存时持有）。
# ponytail: 当前单进程使用，读路径（get/list_*) 不加锁；多线程共享此模块时
# 需把读操作也纳入锁，升级路径是把读缓存换成线程安全的 dict 快照。
_WRITE_LOCK = threading.RLock()



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
    """从目录加载所有人格/角色定义文件，返回加载的数量（5s TTL 缓存）。

    快照模式：锁内构建临时 dict，整体替换全局引用，消除读路径空窗期。
    TTL 检查分两层：锁外快速返回（无竞争时零开销），锁内二次确认（防并发重复全量加载）。
    """
    global _LOADED_AT, _LOADED_COUNT, _LOADED_BASE_DIR
    now = time.monotonic()
    # 缓存键必须含 base_dir：否则 5s 窗口内换目录加载会静默返回上一批数据
    # （测试夹具/多根部署实测拿到完整 31 角色而非临时目录的 1 个）。
    if (_LOADED_AT != 0.0 and now - _LOADED_AT < _LOAD_CACHE_TTL
            and _LOADED_BASE_DIR == base_dir):
        return _LOADED_COUNT
    with _WRITE_LOCK:
        # 锁内二次确认：另一线程可能刚完成加载
        now = time.monotonic()
        if (_LOADED_AT != 0.0 and now - _LOADED_AT < _LOAD_CACHE_TTL
                and _LOADED_BASE_DIR == base_dir):
            return _LOADED_COUNT
        _LOADED_BASE_DIR = base_dir
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(__file__), "..")

        # 快照：构建临时 dict，加载完后整体替换（消除读路径空窗）
        new_roles: dict[str, RoleDef] = {}
        new_personas: dict[str, PersonaDef] = {}
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

                        if isinstance(obj, RoleDef):
                            new_roles[obj.name] = obj
                        new_personas[obj.name] = obj
                        count += 1
                    except (json.JSONDecodeError, OSError, KeyError) as e:
                        print(f"  [registry] 加载失败 {subitem.get('name', 'unknown')}: {type(e).__name__}: {e}", file=sys.stderr)
                    except Exception as e:
                        print(f"  [registry] 加载异常 {subitem.get('name', 'unknown')}: {type(e).__name__}: {e}", file=sys.stderr)

        # 整体替换（锁内单次赋值，读路径原子可见）
        _ROLES.clear()
        _ROLES.update(new_roles)
        _PERSONAS.clear()
        _PERSONAS.update(new_personas)
        _LOADED_AT = time.monotonic()
        _LOADED_COUNT = count
        return count
