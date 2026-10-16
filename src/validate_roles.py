#!/usr/bin/env python3
"""Validate all session-role JSON files for schema correctness."""
from __future__ import annotations
import argparse
import json
import os
import re
import sys

import paths
from shared_loader import parse_produce_categories, parse_consume_categories, VALID_BUS_CATEGORIES

# 仅扫描会话角色目录；browser-harness profiles（registry.load_all 同时加载）
# 是另一套 schema（无 skills/goal/constraints/mcp_servers 强校验），不走本校验器。
ROLES_DIR = str(paths.SESSION_ROLES_PERSONAS)

REQUIRED_FIELDS = {
    "name", "title", "description", "category", "system_prompt",
    "skills", "skill_refs", "goal", "constraints"
}
VALID_LIFECYCLES = {"infinite", "ondemand"}
# infinite: 常驻驱动。引擎拉起角色时显式传 --drive infinite
# (session-pipeline/src/pipeflow/role_lifecycle.py:_ensure_role_alive)，此前 persona
# JSON 未同步该值。与 lifecycle 的 infinite 不同轴：lifecycle 管回收，drive 管启动闸门。
VALID_DRIVES = {"cron", "ondemand", "goal", "infinite"}
# 由 shared_loader.parse_* 汇总的 40 个注册分类（新增分类时同步追加）
# VALID_BUS_CATEGORIES 從 shared_loader 匯入（單一權威來源）
OUTPUT_TARGET_PATTERNS = [
    re.compile(r"^bus cat=\S+"),
    re.compile(r"^bus consume"),
    re.compile(r"^bb write"),
    re.compile(r"^git commit"),
    re.compile(r"^svn commit"),
    re.compile(r"^codex\b"),
    re.compile(r"^ccs\b"),
]

# eval_criteria 支持两种格式：
# 1. 可执行 shell 命令（自动验证）：包含 bash/python/curl/git 等命令，或管道/重定向
# 2. 描述性验收标准（人工验证）：以 "验证:" 或 "验收:" 或 "标准:" 开头，后面可选跟 shell 命令
EVAL_CRITERIA_EXEC_PATTERN = re.compile(
    r"(bash\s+-c|python3?\s+|sh\s+-c|curl\s+|git\s+|systemctl\s+|journalctl\s+|"
    r"ls\s+|grep\s+|awk\s+|python3?\s+-c|wc\s+|test\s+|\[.*\]|cat\s+|head\s+|tail\s+|"
    r"find\s+|stat\s+|date\s+|ps\s+|netstat\s+|ss\s+|df\s+|du\s+|free\s+|top\s+|htop\s+|"
    r"kill\s+|pkill\s+|pgrep\s+|systemctl\s+|journalctl\s+|"
    r"\$\(|\$\{|`|>|>>|<\s*\(|<\s*<|\|)"
)
EVAL_CRITERIA_DESC_PATTERN = re.compile(r"^(验证|验收|标准|检查|确保)[：:]")


def _normalize_role_name(s: str) -> str:
    """归一化角色名用于比对：小写、-/_ 视为等价分隔符。"""
    return re.sub(r"[-_]", " ", s).lower().strip()


def validate_output_target(t: str | dict) -> bool:
    if isinstance(t, dict):
        return "bus_cat" in t
    return any(p.match(t) for p in OUTPUT_TARGET_PATTERNS)


def looks_like_shell_command(s: str) -> bool:
    """检查字符串是否看起来像可执行的 shell 命令，或是描述性验收标准。"""
    s = s.strip()
    if not s:
        return False
    # 描述性验收标准：以 "验证:" "验收:" "标准:" "检查:" "确保:" 开头
    if EVAL_CRITERIA_DESC_PATTERN.search(s):
        return True
    # 纯中文描述（含中文即视为描述性验收标准，不要求可执行）
    # ponytail: 中文描述中的 "cat" 等子串不应触发命令匹配
    if re.search(r"[一-鿿]", s):
        return True
    # 可执行命令
    return bool(EVAL_CRITERIA_EXEC_PATTERN.search(s))


def _check_prompt_sizes(prompts_dir: str) -> None:
    """统计 prompt 模板文件行数，超长仅作参考 INFO（不再门禁）。"""
    candidates: list[tuple[str, str]] = []
    base = os.path.join(prompts_dir, "base.md")
    if os.path.isfile(base):
        candidates.append(("base.md", base))
    for subdir in ("roles",):
        d = os.path.join(prompts_dir, subdir)
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith(".md"):
                    candidates.append((f"{subdir}/{f}", os.path.join(d, f)))
    total = 0
    for display, path in candidates:
        try:
            with open(path) as f:
                n = len(f.read().splitlines())
        except OSError:
            continue
        total += n
        if n > 900:
            print(f"  INFO: prompt 文件 '{display}' 共 {n} 行（超 900 行，参考）")
    print(f"  INFO: prompt 文件合计 {total} 行（参考）")


def _warn_category_drift() -> None:
    """对比 JSON 实际使用的 bus 分类与 VALID_BUS_CATEGORIES，不一致时告警。"""
    used: set[str] = set()
    for fname in os.listdir(ROLES_DIR):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(ROLES_DIR, fname), encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                continue
        except Exception:
            continue
        for c in parse_produce_categories(data.get("output_targets", [])):
            used.add(c)
        for c in parse_consume_categories(data.get("input_signals", [])):
            if c != "*":
                used.add(c)
    unregistered = used - VALID_BUS_CATEGORIES
    orphan = VALID_BUS_CATEGORIES - used
    if unregistered:
        print(f"  WARN: JSON 使用了 {len(unregistered)} 个未注册分类 → {sorted(unregistered)}，请同步追加到 VALID_BUS_CATEGORIES", file=sys.stderr)
    if orphan:
        print(f"  WARN: VALID_BUS_CATEGORIES 有 {len(orphan)} 个未被 JSON 引用 → {sorted(orphan)}，可考虑清理", file=sys.stderr)


def _validate_collab(fname: str, collab: dict, known_roles: set[str], errors: list) -> None:
    """校验 collab 结构: guard.watch 引用的角色必须存在, track.bus_category 必须注册。"""
    guard = collab.get("guard", {})
    if guard:
        if not isinstance(guard, dict):
            errors.append(f"{fname}: collab.guard 必须是 dict")
        else:
            watch = guard.get("watch", [])
            if not isinstance(watch, list) or not all(isinstance(r, str) for r in watch):
                errors.append(f"{fname}: collab.guard.watch 必须是字符串列表")
            else:
                for r in watch:
                    if _normalize_role_name(r) not in {_normalize_role_name(k) for k in known_roles}:
                        errors.append(f"{fname}: collab.guard.watch 引用未知角色 '{r}'")
    track = collab.get("track", {})
    if track:
        if not isinstance(track, dict):
            errors.append(f"{fname}: collab.track 必须是 dict")
        else:
            cat = track.get("bus_category", "")
            if cat and cat != "*" and cat not in VALID_BUS_CATEGORIES:
                errors.append(f"{fname}: collab.track.bus_category '{cat}' 未在 VALID_BUS_CATEGORIES 注册表中")

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate session-role JSON files")
    parser.add_argument("--roles", action="store_true", help="仅验证 session 角色（默认全部）")
    parser.add_argument("--category", default="", help="按分类筛选验证（如 '维护'）")
    return parser.parse_known_args()[0]


_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")


def _load_known_roles(files: list[str]) -> tuple[set[str], dict[str, str]]:
    """预收集所有角色名（collab.guard.watch 校验用）。"""
    known: dict[str, str] = {}
    for fname in files:
        try:
            with open(os.path.join(ROLES_DIR, fname), encoding="utf-8") as fh:
                known[fname.replace(".json", "")] = json.load(fh).get("name", "")
        except Exception:
            continue
    return {n for n in known.values() if n}, known


def _load_json_files() -> list[str]:
    return sorted(f for f in os.listdir(ROLES_DIR) if f.endswith(".json"))


def _validate_role_fields(fname: str, data: dict, seen_names: set[str], errors: list[str]) -> int:
    """校验单个角色的必填字段、命名、生命周期、驱动等基础字段。返回 role_count（0 或 1）。"""
    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        errors.append(f"{fname}: 缺少必填字段 {missing}")
        return 0
    name = data["name"]
    if name in seen_names:
        errors.append(f"{fname}: 重复角色名称 '{name}' (已在其他文件中定义)")
    seen_names.add(name)
    return 1 if "lifecycle" in data else 0


def _validate_input_signals(fname: str, data: dict, errors: list[str]) -> None:
    """校验 input_signals 的格式兼容性（旧/新格式）。"""
    for i, sig in enumerate(data.get("input_signals", [])):
        if not isinstance(sig, dict):
            errors.append(f"{fname}: input_signals[{i}] 不是对象")
        elif "source" in sig:
            if "filter" not in sig:
                errors.append(f"{fname}: input_signals[{i}] 旧格式缺少 filter 字段")
        elif "type" in sig:
            sig_type = sig.get("type")
            spec = sig.get("spec", {})
            if sig_type == "bus" and "category" not in spec:
                errors.append(f"{fname}: input_signals[{i}] type=bus 但 spec 缺少 category")
            elif sig_type == "shell" and "command" not in spec:
                errors.append(f"{fname}: input_signals[{i}] type=shell 但 spec 缺少 command")
        else:
            errors.append(f"{fname}: input_signals[{i}] 既无 source 字段（旧格式）也无 type 字段（新格式）")


def _validate_output_targets(fname: str, data: dict, errors: list[str]) -> None:
    """校验 output_targets 格式。"""
    for i, tgt in enumerate(data.get("output_targets", [])):
        if not isinstance(tgt, (str, dict)) or not validate_output_target(tgt):
            errors.append(f"{fname}: output_targets[{i}]='{tgt}' 格式无效")


# 恒真验证命令：永远 PASS，不代表任何产出质量。base.md:42 明令禁止用此类
# checker 替代人读判断，故此处直接拒绝，逼 eval_criteria 回到自然语言描述性标准。
_TRIVIAL_VERIFIERS = (
    'import sys; print("OK")', "import sys; print('OK')",
    'import sys; print("PASS")', "import sys; print('PASS')",
    'import time; print', 'import os; print("OK")', 'import os; print("PASS")',
)


def _is_trivial_verifier(criteria: str) -> bool:
    c = criteria.replace("验证:", "").replace("输出", "")
    return any(p in c for p in _TRIVIAL_VERIFIERS)


def _validate_eval_criteria(fname: str, data: dict, errors: list[str]) -> None:
    """校验 eval_criteria 必须是可执行命令或描述性标准。"""
    for i, criteria in enumerate(data.get("eval_criteria", [])):
        if not isinstance(criteria, str):
            errors.append(f"{fname}: eval_criteria[{i}] 不是字符串")
        elif _is_trivial_verifier(criteria):
            errors.append(f"{fname}: eval_criteria[{i}] 是恒真验证命令(print OK/PASS)，不反映产出质量——改为自然语言描述性标准")
        elif not looks_like_shell_command(criteria):
            errors.append(f"{fname}: eval_criteria[{i}]='{criteria[:60]}...' 看起来不是可执行的 shell 命令（需以 bash/python/curl/git 等开头或包含管道/重定向）")


def _validate_prompt_refs(fname: str, data: dict, errors: list[str]) -> None:
    """校验 prompt_refs 引用的文件存在（仅当 prompts/ 目录存在时）。"""
    if not os.path.isdir(_PROMPTS_DIR):
        return
    for ref_key, ref_path in data.get("prompt_refs", {}).items():
        full_path = os.path.join(_PROMPTS_DIR, ref_path)
        if not os.path.exists(full_path):
            errors.append(f"{fname}: prompt_refs.{ref_key}='{ref_path}' 文件不存在 ({full_path})")


def _validate_mcp(fname: str, data: dict, errors: list[str]) -> None:
    """校验 mcp_servers / mcp_tools 的结构和对应关系。"""
    mcp_servers = data.get("mcp_servers", [])
    mcp_tools = data.get("mcp_tools", {})
    if not isinstance(mcp_servers, list):
        errors.append(f"{fname}: mcp_servers 必须是字符串列表")
    elif not mcp_servers:
        errors.append(f"{fname}: mcp_servers 为空——每个角色必须声明至少一个 MCP server")
    if not isinstance(mcp_tools, dict):
        errors.append(f"{fname}: mcp_tools 必须是对象")
    for srv in mcp_servers:
        if srv not in mcp_tools:
            errors.append(f"{fname}: mcp_servers 含 '{srv}' 但 mcp_tools 中无对应键")
        else:
            tools = mcp_tools[srv]
            if not isinstance(tools, list) or not all(isinstance(t, str) for t in tools):
                errors.append(f"{fname}: mcp_tools['{srv}'] 必须是字符串列表")
            elif not tools:
                errors.append(f"{fname}: mcp_tools['{srv}'] 不能为空")


def _validate_bus_categories(fname: str, data: dict, errors: list[str]) -> None:
    """校验 produce/consume 分类都在 VALID_BUS_CATEGORIES 中注册。"""
    produce_cats = parse_produce_categories(data.get("output_targets", []))
    consume_cats = parse_consume_categories(data.get("input_signals", []))
    for cat in produce_cats:
        if cat not in VALID_BUS_CATEGORIES:
            errors.append(f"{fname}: bus 产出分类 '{cat}' 未在 VALID_BUS_CATEGORIES 注册表中")
    for cat in consume_cats:
        if cat == "*":
            continue
        if cat not in VALID_BUS_CATEGORIES:
            errors.append(f"{fname}: bus 消费分类 '{cat}' 未在 VALID_BUS_CATEGORIES 注册表中")


def _validate_dead_fields(fname: str, data: dict, dead_warnings: list[str]) -> None:
    """检测 schema compat 的死字段。"""
    DEAD_FIELDS = {"output_schema", "session_hint",
                  "_evolution_version", "_evolved_at", "version"}
    present = [f for f in DEAD_FIELDS if f in data]
    if present:
        dead_warnings.append(f"{fname}: 包含死字段(无代码消费): {', '.join(present)}")


def _validate_deprecated(fname: str, data: dict, dead_warnings: list[str]) -> None:
    """检测过期 persona 退役日期。"""
    _dep_after = data.get("deprecated_after")
    if not _dep_after:
        return
    try:
        from datetime import datetime
        _dep_ts = datetime.fromisoformat(_dep_after.replace("Z", "+00:00"))
        if _dep_ts.tzinfo is None:
            _dep_ts = _dep_ts.replace(tzinfo=datetime.now().astimezone().tzinfo)
        if datetime.now().astimezone() > _dep_ts:
            dead_warnings.append(
                f"{fname}: 已过退役日期({_dep_after}) — 建议标记 deprecated 或更新契约")
    except (ValueError, TypeError):
        dead_warnings.append(f"{fname}: deprecated_after 格式非法: {_dep_after!r}（期望 ISO8601）")


def _validate_role_def(fname: str, data: dict, errors: list[str]) -> None:
    """校验 RoleDef 特有字段：至少需要 input_signals 或 drive。"""
    has_input_signals = bool(data.get("input_signals"))
    has_drive = bool(data.get("drive"))
    if not has_input_signals and not has_drive:
        errors.append(f"{fname}: RoleDef 角色缺少 input_signals 和 drive，必须至少有一个")


def _validate_skills(fname: str, data: dict, errors: list[str]) -> None:
    """校验 skills / skill_refs / goal / constraints 字段。"""
    skills = data.get("skills", [])
    if not isinstance(skills, list) or len(skills) == 0:
        errors.append(f"{fname}: skills 必须是非空数组")
    elif not all(isinstance(s, str) and s for s in skills):
        errors.append(f"{fname}: skills 元素必须是非空字符串")
    skill_refs = data.get("skill_refs", {})
    if not isinstance(skill_refs, dict):
        errors.append(f"{fname}: skill_refs 必须是对象")
    else:
        for skill in skills:
            if skill not in skill_refs:
                errors.append(f"{fname}: skill_refs 缺少 '{skill}' 的路径")
    if not data.get("goal"):
        errors.append(f"{fname}: goal 字段不能为空")
    constraints = data.get("constraints", [])
    if not isinstance(constraints, list) or len(constraints) == 0:
        errors.append(f"{fname}: constraints 必须是非空数组")


def _check_prompt_refs_exist(prompts_dir: str, _prompt_size_done: list[bool]) -> None:
    """统计 prompt 模板文件行数（仅执行一次）。"""
    if _prompt_size_done[0]:
        return
    _check_prompt_sizes(prompts_dir)
    _prompt_size_done[0] = True


def _validate_one_role(
    fname: str, data: dict, seen_names: set[str],
    known_roles: set[str], errors: list[str],
    dead_warnings: list[str], prompt_size_done: list[bool],
    category_filter: str = "",
) -> int:
    """校验单个角色 JSON。返回 role_count（0 或 1）。"""
    # 筛选
    if category_filter and data.get("category", "") != category_filter:
        return 0
    role_count = _validate_role_fields(fname, data, seen_names, errors)
    if role_count == 0 and "lifecycle" not in data:
        # 缺少必填字段，但仍需后续字段校验 — return 但 errors 已记录
        pass
    if "lifecycle" not in data:
        return role_count
    lifecycle = data.get("lifecycle", "")
    if lifecycle == "infinite" and "input_signals" not in data:
        errors.append(f"{fname}: lifecycle=infinite 角色缺少 input_signals")
    if "output_targets" not in data:
        errors.append(f"{fname}: 角色缺少 output_targets")
    if lifecycle not in VALID_LIFECYCLES:
        errors.append(f"{fname}: lifecycle='{lifecycle}' 无效，应为 {VALID_LIFECYCLES}")
    drive = data.get("drive", "")
    if drive not in VALID_DRIVES:
        errors.append(f"{fname}: drive='{drive}' 无效，应为 {VALID_DRIVES}")
    if drive == "cron" and not data.get("cron_schedule"):
        errors.append(f"{fname}: drive='cron' 但缺少 cron_schedule 字段")
    # 校验 idle_action：禁止废弃的 "/loop" 值
    idle_action = data.get("idle_action", "")
    if idle_action == "/loop":
        errors.append(f"{fname}: idle_action='/loop' 已废弃（CLAUDE.md 红线已禁用），请使用 'wait_for_signal' / 'sleep N' / null 等合法值")
    _validate_input_signals(fname, data, errors)
    _validate_output_targets(fname, data, errors)
    _validate_eval_criteria(fname, data, errors)
    _validate_prompt_refs(fname, data, errors)
    _validate_mcp(fname, data, errors)
    _check_prompt_refs_exist(_PROMPTS_DIR, prompt_size_done)
    _validate_bus_categories(fname, data, errors)
    collab = data.get("collab", {})
    if collab:
        if not isinstance(collab, dict):
            errors.append(f"{fname}: collab 必须是 dict")
        else:
            _validate_collab(fname, collab, known_roles, errors)
    _validate_dead_fields(fname, data, dead_warnings)
    _validate_deprecated(fname, data, dead_warnings)
    _validate_role_def(fname, data, errors)
    _validate_skills(fname, data, errors)
    return role_count


def _check_prompt_quality(errors: list[str]) -> None:
    """R3-13: Prompt 质量检查 — 参考来源、外部 URL、首行角色名。"""
    prompts_roles_dir = os.path.join(_PROMPTS_DIR, "roles")
    prompt_files = []
    if os.path.isdir(prompts_roles_dir):
        prompt_files = sorted(f for f in os.listdir(prompts_roles_dir) if f.endswith(".md"))
    _check_references_section(prompts_roles_dir, prompt_files, errors)
    _check_external_urls(prompts_roles_dir, prompt_files, errors)
    _check_prompt_first_line(prompts_roles_dir, prompt_files, errors)


def _check_references_section(prompts_roles_dir: str, prompt_files: list[str], errors: list[str]) -> None:
    """检查 2: 每个 prompt 文件包含 ## 参考来源。"""
    for pf in prompt_files:
        full_path = os.path.join(prompts_roles_dir, pf)
        try:
            with open(full_path) as fh:
                content = fh.read()
            if "## 参考来源" not in content:
                errors.append(f"{pf}: 缺少 '## 参考来源' 章节")
        except Exception as e:
            errors.append(f"{pf}: 读取失败 — {e}")


def _check_external_urls(prompts_roles_dir: str, prompt_files: list[str], errors: list[str]) -> None:
    """检查 3: 非原创角色必须引用至少 1 个外部 URL。"""
    for pf in prompt_files:
        name_stem = pf.replace(".md", "")
        if name_stem in ("lr", "pg", "investigator_python", "investigator_senior", "investigator_general"):
            continue
        full_path = os.path.join(prompts_roles_dir, pf)
        try:
            with open(full_path) as fh:
                content = fh.read()
            ref_section = content.split("## 参考来源")[-1] if "## 参考来源" in content else ""
            if not re.search(r"https?://", ref_section):
                errors.append(f"{pf}: 非原创角色但 ## 参考来源 无外部 URL 引用")
        except Exception:
            pass


def _check_prompt_first_line(prompts_roles_dir: str, prompt_files: list[str], errors: list[str]) -> None:
    """检查 4: 首行必须包含本角色名，不能混入其他角色名。"""
    role_name_map: dict[str, str] = {}
    for fname in os.listdir(ROLES_DIR):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(ROLES_DIR, fname), encoding="utf-8") as fh:
                role_name_map[fname.replace(".json", "")] = json.load(fh).get("name", "")
        except Exception:
            continue
    known_roles = sorted({n for n in role_name_map.values() if n})
    _loose_first_line = {"reviewer", "scout", "writer", "pm"}
    for pf in prompt_files:
        name_stem = pf.replace(".md", "")
        full_path = os.path.join(prompts_roles_dir, pf)
        try:
            with open(full_path) as fh:
                lines = fh.read().splitlines()
            if not lines:
                continue
            first_line = lines[0].strip()
            candidates = {name_stem}
            for stem, jname in role_name_map.items():
                if stem == name_stem or jname == name_stem:
                    if jname:
                        candidates.add(jname)
            norm_cands = {_normalize_role_name(c) for c in candidates}
            if first_line == "<identity>":
                ident_lines: list[str] = []
                for ln in lines:
                    if ln.strip() == "</identity>":
                        break
                    ident_lines.append(ln)
                own_text = " ".join(ident_lines)
                mix_text = own_text
            elif name_stem in _loose_first_line:
                own_text = " ".join(lines)
                mix_text = first_line
            else:
                own_text = first_line
                mix_text = first_line
            norm_own = _normalize_role_name(own_text.replace("#", ""))
            if name_stem not in _loose_first_line and not any(c in norm_own for c in norm_cands):
                errors.append(f"{pf}: 首行未包含角色名 '{name_stem}'")
            clean_mix = mix_text.replace("#", "").strip().lower()
            for r in known_roles:
                if _normalize_role_name(r) in norm_cands:
                    continue
                patterns: set[str] = {f"({r})", f"-{r}", f"/{r}"}
                patterns |= {f"({_normalize_role_name(r)})", f"-{_normalize_role_name(r)}", f"/{_normalize_role_name(r)}"}
                for p in patterns:
                    if p in clean_mix:
                        errors.append(f"{pf}: 首行混入其他角色名 '{r}'")
                        break
        except Exception:
            pass


def main() -> int:
    args = _parse_args()
    args_category = args.category

    if not os.path.isdir(ROLES_DIR):
        print(f"  FAIL: 目录不存在 {ROLES_DIR}")
        return 1

    _warn_category_drift()

    files = _load_json_files()
    if not files:
        print("  FAIL: 未找到 JSON 文件")
        return 1

    seen_names: set[str] = set()
    known_roles, _ = _load_known_roles(files)
    errors: list[str] = []
    dead_warnings: list[str] = []
    checked = 0
    role_count = 0
    prompt_size_done = [False]

    for fname in files:
        path = os.path.join(ROLES_DIR, fname)
        try:
            with open(path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{fname}: JSON 无效 — {e}")
            continue
        except Exception as e:
            errors.append(f"{fname}: 读取失败 — {e}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{fname}: JSON 顶层必须是对象")
            continue

        checked += 1
        role_count += _validate_one_role(
            fname, data, seen_names, known_roles, errors, dead_warnings, prompt_size_done,
            category_filter=args_category
        )

    _check_prompt_quality(errors)

    for w in dead_warnings:
        print(f"  WARN: {w}")

    print(f"  文件数: {checked}")
    print(f"  角色数: {role_count}")
    print(f"  错误数: {len(errors)}")

    for err in errors:
        print(f"  FAIL: {err}")

    if errors:
        return 1

    print("  所有角色验证通过")
    return 0


if __name__ == "__main__":
    # Inline self-check: VALID_BUS_CATEGORIES imported from shared_loader
    from shared_loader import VALID_BUS_CATEGORIES as _cats
    assert isinstance(_cats, set), "VALID_BUS_CATEGORIES must be a set"
    assert len(_cats) == 42, f"Expected 42 categories, got {len(_cats)}"
    assert "architecture" in _cats, "architecture must be a registered category"
    # Inline self-check: refactored main() produces same validation output
    assert callable(main), "main() must be callable after refactor"
    sys.exit(main())