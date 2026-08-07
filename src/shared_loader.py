#!/usr/bin/env python3
"""
共享角色加载器 — 三个项目的统一角色数据入口。

职责：
1. 从 JSON 文件加载所有角色定义（单一权威来源）
2. 提取 produce/consume 路由信息
3. 输出 JSON 供其他项目消费，无需重复 parse

用法:
  python3 src/shared_loader.py --list            # 列出角色摘要
  python3 src/shared_loader.py --export           # 输出 roles_export.json
  python3 src/shared_loader.py --validate         # 调用 validate_roles 校验
"""
from __future__ import annotations
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# ── 路径 ──
ROLES_DIR = Path(os.environ.get(
    "SESSION_ROLES_ROOT",
    str(Path.home() / "hermes-session-roles")
)) / "personas" / "session-roles"

EXPORT_DIR = Path(os.environ.get(
    "HERMES_DATA_DIR",
    str(Path.home() / ".hermes" / "data")
))

EXPORT_PATH = EXPORT_DIR / "roles_export.json"


# ── 数据模型 ──
@dataclass
class RoleRouting:
    produce: list[str] = field(default_factory=list)
    consume: list[str] = field(default_factory=list)
    consume_all: bool = False  # True if consume includes "*"


@dataclass
class RoleExport:
    name: str
    title: str
    category: str
    description: str
    lifecycle: str
    drive: str
    cron_schedule: str
    routing: RoleRouting
    workgroup: list[dict]  # [{role, mode, round_limit?}]，与 models.RoleDef.workgroup 一致
    auto_send_messages: list[str]
    raw: dict | None = None  # original JSON (excluded from --export)


# ── 解析函数（单一权威实现） ──

def parse_produce_categories(output_targets: list) -> list[str]:
    """从 output_targets 提取 bus 产出分类。

    兼容两种格式：
    - 旧格式字符串: "bus cat=architecture 归档清理方案"
    - 新格式 dict:   {"bus_cat": "architecture", "label": "..."}
    """
    cats: list[str] = []
    for target in output_targets:
        if isinstance(target, dict):
            cat = target.get("bus_cat", "")
            if cat and cat not in cats:
                cats.append(cat)
            continue
        m = re.search(r"bus cat=(\w+)", target)
        if m:
            cat = m.group(1)
            if cat not in cats:
                cats.append(cat)
    return cats


def parse_consume_categories(input_signals: list[dict]) -> list[str]:
    """从 input_signals 提取消费分类。"""
    cats: list[str] = []
    for signal in input_signals:
        # 新格式
        if signal.get("type") == "bus":
            category = signal.get("spec", {}).get("category", "")
            if category:
                if category == "*":
                    if "*" not in cats:
                        cats.append("*")
                elif category not in cats:
                    cats.append(category)
                continue
        # 旧格式
        source = signal.get("source", "")
        if "bus cat=*" in source or "unread --all" in source:
            if "*" not in cats:
                cats.append("*")
            continue
        for m in re.finditer(r"bus cat=(\w+)", source):
            cat = m.group(1)
            if cat not in cats:
                cats.append(cat)
        for m in re.finditer(r"--cat (\w+)", source):
            cat = m.group(1)
            if cat not in cats:
                cats.append(cat)
    return cats


def load_roles() -> list[dict]:
    """加载所有角色 JSON（委托 registry.load_all → list_roles，返回原始 dict）。"""
    from registry import load_all, list_roles
    # ponytail: 环境变量 SESSION_ROLES_ROOT 可覆盖默认路径；
    # 加载器用 ROLES_DIR.parent.parent（项目根目录），
    # registry 内部再拼接 "personas/session-roles" 子目录。
    load_all(base_dir=str(ROLES_DIR.parent.parent))
    return [r.to_dict() for r in list_roles()]


def load_role(name: str) -> Optional[dict]:
    """按名称查找角色（复用 load_roles）。"""
    for r in load_roles():
        if r.get("name") == name:
            return r
    return None


def export_role(role: dict) -> RoleExport:
    """将原始角色 dict 转为 RoleExport。"""
    name = role.get("name", "")
    input_signals = role.get("input_signals", [])
    output_targets = role.get("output_targets", [])
    produce = parse_produce_categories(output_targets)
    consume = parse_consume_categories(input_signals)
    return RoleExport(
        name=name,
        title=role.get("title", ""),
        category=role.get("category", ""),
        description=role.get("description", ""),
        lifecycle=role.get("lifecycle", "infinite"),
        drive=role.get("drive", "ondemand"),
        cron_schedule=role.get("cron_schedule", ""),
        routing=RoleRouting(
            produce=produce,
            consume=consume,
            consume_all="*" in consume,
        ),
        workgroup=role.get("workgroup", []),
        auto_send_messages=role.get("auto_send_messages", []),
    )


def export_all() -> list[dict]:
    """导出所有角色为可序列化 dict 列表。"""
    return [
        asdict(export_role(r)) for r in load_roles()
    ]


def write_export() -> str:
    """写入 ~/.hermes/data/roles_export.json。"""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "exported_at": time.time(),
        "roles": export_all(),
    }
    EXPORT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(EXPORT_PATH)


# ── CLI ──

def _format_table(roles: list[dict]) -> str:
    lines = [
        f"{'name':<20} {'title':<20} {'lifecycle':<10} {'drive':<10} {'produce':<30} {'consume':<30}"
    ]
    lines.append("─" * 120)
    for r in roles:
        e = export_role(r)
        p = ", ".join(e.routing.produce) or "-"
        c = ", ".join(e.routing.consume) if not e.routing.consume_all else "ALL"
        lines.append(
            f"{e.name:<20} {e.title:<20} {e.lifecycle:<10} {e.drive:<10} "
            f"{p:<30} {c:<30}"
        )
    return "\n".join(lines)


def main():
    args = set(sys.argv[1:])
    if "--export" in args:
        path = write_export()
        print(json.dumps({"ok": True, "path": path, "count": len(load_roles())}))
        return
    if "--list" in args:
        roles = load_roles()
        print(_format_table(roles))
        return
    if "--validate" in args:
        # Delegate to validate_roles
        from validate_roles import main as _val_main
        rc = _val_main()
        sys.exit(rc)
    # Default: export JSON to stdout
    print(json.dumps(export_all(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
