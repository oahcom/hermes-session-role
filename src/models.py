"""
Session Role Definition — PersonaDef + RoleDef.

复用 Browser Harness 的 PersonaDef 结构。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
import os
import re

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
    prompt_refs: dict[str, str] = field(default_factory=dict)  # 模块化 prompt 引用
    skills: list[str] = field(default_factory=list)  # 技能列表
    skill_refs: dict[str, str] = field(default_factory=dict)  # 技能引用路径
    goal: str = ""  # 角色目标
    constraints: list[str] = field(default_factory=list)  # 红线约束

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in (
            "name", "title", "description", "category",
            "system_prompt", "config_overrides", "eval_criteria",
            "prompt_refs", "skills", "skill_refs", "goal", "constraints",
        )}

    @classmethod
    def from_dict(cls, d: dict) -> PersonaDef:
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})

    def render_system_prompt(self, **kwargs: str) -> str:
        """渲染系统提示词，替换已知占位符，保留未知 {} 文本原样。"""
        defaults = {"persona_name": self.name, "persona_title": self.title}
        defaults.update(kwargs)
        # 只替换已知占位符，用正则匹配 {known_key} 避免误伤 curl 格式串
        result = self.system_prompt
        for key, val in defaults.items():
            result = result.replace("{" + key + "}", val)
        return result


def render_prompt_from_refs(
    prompt_refs: dict[str, str],
    base_dir: str | None = None,
    **kwargs: str,
) -> str:
    """从 prompt_refs 渲染完整 system_prompt。

    prompt_refs 格式：
    - base: base.md 的相对路径
    - role: roles/xxx.md 的相对路径
    - driver: mixins/xxx_driver.md 的相对路径

    拼接顺序：base -> role -> driver

    当 prompts/ 目录不存在时（迁移后），回退到 role_assembler 组装。
    """
    if not prompt_refs:
        return ""

    if base_dir is None:
        base_dir = os.path.join(os.path.dirname(__file__), "..", "prompts")

    # prompts/ 不可用时回退到 role_assembler
    if not os.path.isdir(base_dir):
        try:
            from role_assembler import assemble_role_prompt
            name = kwargs.get("persona_name", "")
            if name:
                prompt = assemble_role_prompt(name)
                if prompt:
                    return prompt
        except (FileNotFoundError, ImportError):
            pass
        return ""

    # 默认占位符：persona_name/persona_title/cron_schedule + 源角色
    defaults = {
        "源角色": kwargs.get("persona_name", ""),
    }
    defaults.update(kwargs)

    parts = []
    for key in ["base", "role", "driver"]:
        if key in prompt_refs:
            file_path = os.path.join(base_dir, prompt_refs[key])
            if os.path.exists(file_path):
                with open(file_path, encoding="utf-8") as f:
                    content = f.read().strip()
                    for k, val in defaults.items():
                        # Use replace for known keys to avoid KeyError on curl format strings
                        content = content.replace("{" + k + "}", val)
                    parts.append(content)

    return "\n\n---\n\n".join(parts)

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
        persona_fields = {k: d[k] for k in PersonaDef.__dataclass_fields__ if k in d}
        role_fields = {k: d[k] for k in cls.__dataclass_fields__ if k in d and k not in PersonaDef.__dataclass_fields__}
        role = cls(**persona_fields, **role_fields)
        # 补丁：to_dict 时确保 skills/skill_refs 等 BaseDef 字段存在
        for extra_field in ['skills', 'skill_refs', 'goal', 'constraints']:
            if extra_field in d and extra_field not in PersonaDef.__dataclass_fields__:
                pass  # 已在 PersonaDef 初始化时处理
        return role
