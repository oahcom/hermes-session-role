"""
Session Role Definition — PersonaDef + RoleDef.

复用 Browser Harness 的 PersonaDef 结构，
扩展 lifecycle/input_signals/output_targets 供 session 启动控制。
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PersonaDef:
    """一个人格定义（Browser Harness 兼容）。"""
    name: str
    title: str
    description: str
    category: str
    system_prompt: str
    config_overrides: dict[str, Any] = field(default_factory=dict)
    eval_criteria: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in (
            "name", "title", "description", "category",
            "system_prompt", "config_overrides", "eval_criteria"
        )}

    @classmethod
    def from_dict(cls, d: dict) -> PersonaDef:
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})

    def render_system_prompt(self, **kwargs: str) -> str:
        """渲染系统提示词，替换占位符。"""
        defaults = {"persona_name": self.name, "persona_title": self.title}
        defaults.update(kwargs)
        return self.system_prompt.format(**defaults)


@dataclass
class RoleDef(PersonaDef):
    """Session 角色定义（PersonaDef 扩展）。

    扩展字段：
      lifecycle: 生命周期策略
      drive: 驱动方式
      cron_schedule: Cron 表达式（drive="cron" 时）
      idle_action: 空闲时行为
      input_signals: 输入信号列表
      output_targets: 产出目标列表
      session_hint: session 提示（cron/interactive/background）
    """
    lifecycle: str = "infinite"  # infinite | ondemand
    drive: str = "cron"  # cron | loop | ondemand
    cron_schedule: str = ""
    idle_action: str = "exit"
    input_signals: list[dict] = field(default_factory=list)
    output_targets: list[str] = field(default_factory=list)
    session_hint: str = "cron"

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update({
            "lifecycle": self.lifecycle,
            "drive": self.drive,
            "cron_schedule": self.cron_schedule,
            "idle_action": self.idle_action,
            "input_signals": self.input_signals,
            "output_targets": self.output_targets,
            "session_hint": self.session_hint,
        })
        return base

    @classmethod
    def from_dict(cls, d: dict) -> RoleDef:
        # 先提取 PersonaDef 字段
        persona_fields = {k: d[k] for k in PersonaDef.__dataclass_fields__ if k in d}
        role_fields = {k: d[k] for k in cls.__dataclass_fields__ if k in d and k not in PersonaDef.__dataclass_fields__}
        return cls(**persona_fields, **role_fields)


_ROLES: dict[str, RoleDef] = {}
_PERSONAS: dict[str, PersonaDef] = {}


def register(obj: PersonaDef | RoleDef) -> None:
    """注册一个人格/角色。"""
    if isinstance(obj, RoleDef):
        _ROLES[obj.name] = obj
        _PERSONAS[obj.name] = obj  # Role 也注册到 Persona 索引，但标记避免重复搜索
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
    """从目录加载所有人格/角色定义文件。

    返回加载的数量。
    """
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
                    # 判断是 RoleDef 还是 PersonaDef
                    if "lifecycle" in item or "input_signals" in item:
                        register(RoleDef.from_dict(item))
                    else:
                        register(PersonaDef.from_dict(item))
                    count += 1
            except Exception as e:
                print(f"  [models] 加载 {fname} 失败: {e}")
    return count
