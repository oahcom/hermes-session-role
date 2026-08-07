#!/usr/bin/env python3
"""Validate all session-role JSON files for schema correctness."""
from __future__ import annotations
import json
import os
import re
import sys

import paths
from shared_loader import parse_produce_categories, parse_consume_categories

# 仅扫描会话角色目录；browser-harness profiles（registry.load_all 同时加载）
# 是另一套 schema（无 skills/goal/constraints/mcp_servers 强校验），不走本校验器。
ROLES_DIR = str(paths.SESSION_ROLES_PERSONAS)

REQUIRED_FIELDS = {
    "name", "title", "description", "category", "system_prompt",
    "skills", "skill_refs", "goal", "constraints"
}
VALID_LIFECYCLES = {"infinite", "ondemand"}
VALID_DRIVES = {"cron", "loop", "ondemand", "goal"}
# 由 shared_loader.parse_* 汇总的 40 个注册分类（新增分类时同步追加）
VALID_BUS_CATEGORIES = {
    "approval", "architecture", "blocker", "bug_report", "ccs_health",
    "changelog", "cleanup", "code_fix", "code_review", "debate",
    "deployment_plan", "deployment_report", "design_issue", "documentation",
    "evolution_report", "feedback", "knowledge_distill", "memory_store",
    "monitor_dashboard", "notice", "optimization", "prd", "product_design",
    "research", "root_cause_analysis", "scheduler", "security",
    "security_audit", "session_log", "skill_audit", "system",
    "system_design", "task_spec", "tech_decision", "test_plan",
    "test_report", "threat_model", "user_story", "verification", "workflow",
}
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
    for subdir in ("roles", "mixins"):
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


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Validate session-role JSON files")
    parser.add_argument("--roles", action="store_true", help="仅验证 session 角色（默认全部）")
    parser.add_argument("--category", default="", help="按分类筛选验证（如 '维护'）")
    args, _ = parser.parse_known_args()

    if not os.path.isdir(ROLES_DIR):
        print(f"  FAIL: 目录不存在 {ROLES_DIR}")
        return 1

    _warn_category_drift()

    files = sorted(f for f in os.listdir(ROLES_DIR) if f.endswith(".json"))
    if not files:
        print("  FAIL: 未找到 JSON 文件")
        return 1

    seen_names: set[str] = set()
    _prompt_size_done = False
    errors: list[str] = []
    dead_warnings: list[str] = []
    checked = 0
    role_count = 0

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

        # 筛选
        if args.category and data.get("category", "") != args.category:
            continue

        checked += 1

        missing = REQUIRED_FIELDS - set(data.keys())
        if missing:
            errors.append(f"{fname}: 缺少必填字段 {missing}")
            continue

        name = data["name"]
        if name in seen_names:
            errors.append(f"{fname}: 重复角色名称 '{name}' (已在其他文件中定义)")
        seen_names.add(name)

        if "lifecycle" in data:
            role_count += 1
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

            # P1: drive=cron 时必须有 cron_schedule
            if drive == "cron" and not data.get("cron_schedule"):
                errors.append(f"{fname}: drive='cron' 但缺少 cron_schedule 字段")

            for i, sig in enumerate(data.get("input_signals", [])):
                if not isinstance(sig, dict):
                    errors.append(f"{fname}: input_signals[{i}] 不是对象")
                elif "source" in sig:
                    # 旧格式: {"source": "...", "filter": "..."}
                    if "filter" not in sig:
                        errors.append(f"{fname}: input_signals[{i}] 旧格式缺少 filter 字段")
                elif "type" in sig:
                    # 新格式: {"type": "...", "spec": {...}, "filter": "..."}
                    sig_type = sig.get("type")
                    spec = sig.get("spec", {})
                    if sig_type == "bus" and "category" not in spec:
                        errors.append(f"{fname}: input_signals[{i}] type=bus 但 spec 缺少 category")
                    elif sig_type == "shell" and "command" not in spec:
                        errors.append(f"{fname}: input_signals[{i}] type=shell 但 spec 缺少 command")
                    # journalctl 和 custom 类型暂不强制验证 spec 字段
                else:
                    errors.append(f"{fname}: input_signals[{i}] 既无 source 字段（旧格式）也无 type 字段（新格式）")

            for i, tgt in enumerate(data.get("output_targets", [])):
                if not isinstance(tgt, (str, dict)) or not validate_output_target(tgt):
                    errors.append(f"{fname}: output_targets[{i}]='{tgt}' 格式无效")

            # P1: eval_criteria 必须是可执行的 shell 命令
            for i, criteria in enumerate(data.get("eval_criteria", [])):
                if not isinstance(criteria, str):
                    errors.append(f"{fname}: eval_criteria[{i}] 不是字符串")
                elif not looks_like_shell_command(criteria):
                    errors.append(f"{fname}: eval_criteria[{i}]='{criteria[:60]}...' 看起来不是可执行的 shell 命令（需以 bash/python/curl/git 等开头或包含管道/重定向）")

            # P1: prompt_refs 引用的文件必须存在（仅当 prompts/ 目录存在时检查）
            prompts_dir = os.path.join(os.path.dirname(__file__), "..", "prompts")
            if os.path.isdir(prompts_dir):
                for ref_key, ref_path in data.get("prompt_refs", {}).items():
                    full_path = os.path.join(prompts_dir, ref_path)
                    if not os.path.exists(full_path):
                        errors.append(f"{fname}: prompt_refs.{ref_key}='{ref_path}' 文件不存在 ({full_path})")

            # ── P2: 新增校验 ────────────────────────────────────────────────

            # mcp_servers: list[str]（models.py 定义），mcp_tools: dict
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

            # prompt 模板文件大小门禁（仅执行一次）
            if not _prompt_size_done:
                _check_prompt_sizes(os.path.join(os.path.dirname(__file__), "..", "prompts"))
                _prompt_size_done = True

            # produce/consume 分类注册表校验
            produce_cats = parse_produce_categories(data.get("output_targets", []))
            consume_cats = parse_consume_categories(data.get("input_signals", []))
            for cat in produce_cats:
                if cat not in VALID_BUS_CATEGORIES:
                    errors.append(f"{fname}: bus 产出分类 '{cat}' 未在 VALID_BUS_CATEGORIES 注册表中")
            for cat in consume_cats:
                if cat == "*":
                    continue  # 通配符无需注册
                if cat not in VALID_BUS_CATEGORIES:
                    errors.append(f"{fname}: bus 消费分类 '{cat}' 未在 VALID_BUS_CATEGORIES 注册表中")

            # Dead field warnings (not errors — schema compat)
            # NOTE: constraints/goal/skill_refs 被 role_assembler.py 和本文件消费，不是死字段
            DEAD_FIELDS = {"output_schema", "session_hint",
                          "_evolution_version", "_evolved_at", "version"}
            present = [f for f in DEAD_FIELDS if f in data]
            if present:
                dead_warnings.append(f"{fname}: 包含死字段(无代码消费): {', '.join(present)}")

            # 对于 RoleDef 角色，至少要有 input_signals 或 drive 之一
            has_input_signals = bool(data.get("input_signals"))
            has_drive = bool(data.get("drive"))
            if not has_input_signals and not has_drive:
                errors.append(f"{fname}: RoleDef 角色缺少 input_signals 和 drive，必须至少有一个")

            # ── P3: skills / skill_refs / goal / constraints 校验 ──────────
            # skills 必须是非空数组
            skills = data.get("skills", [])
            if not isinstance(skills, list) or len(skills) == 0:
                errors.append(f"{fname}: skills 必须是非空数组")
            elif not all(isinstance(s, str) and s for s in skills):
                errors.append(f"{fname}: skills 元素必须是非空字符串")

            # skill_refs 必须包含所有 skills 的路径（文件存在性由 Claude Code 管理）
            skill_refs = data.get("skill_refs", {})
            if not isinstance(skill_refs, dict):
                errors.append(f"{fname}: skill_refs 必须是对象")
            else:
                for skill in skills:
                    if skill not in skill_refs:
                        errors.append(f"{fname}: skill_refs 缺少 '{skill}' 的路径")

            # goal 必须非空
            if not data.get("goal"):
                errors.append(f"{fname}: goal 字段不能为空")

            # constraints 必须是非空数组
            constraints = data.get("constraints", [])
            if not isinstance(constraints, list) or len(constraints) == 0:
                errors.append(f"{fname}: constraints 必须是非空数组")

    # ── R3-13: Prompt 质量检查 ──────────────────────────────
    prompts_dir = os.path.join(os.path.dirname(__file__), "..", "prompts", "roles")
    prompt_files = []
    if os.path.isdir(prompts_dir):
        prompt_files = sorted(f for f in os.listdir(prompts_dir) if f.endswith(".md"))

    # 检查 1: 每个角色引用的 prompt 文件存在（已有）
    # 检查 2: 每个 prompt 文件包含 ## 参考来源
    for pf in prompt_files:
        full_path = os.path.join(prompts_dir, pf)
        try:
            with open(full_path) as fh:
                content = fh.read()
            if "## 参考来源" not in content:
                errors.append(f"{pf}: 缺少 '## 参考来源' 章节")
        except Exception as e:
            errors.append(f"{pf}: 读取失败 — {e}")

    # 检查 3: 非新角色（非 lr/pg/investigator_*）必须引用至少 1 个外部来源
    for pf in prompt_files:
        name_stem = pf.replace(".md", "")
        if name_stem in ("lr", "pg", "investigator_python", "investigator_senior", "investigator_general"):
            continue  # 原创设计，不强制外部引用
        full_path = os.path.join(prompts_dir, pf)
        try:
            with open(full_path) as fh:
                content = fh.read()
            # 提取 ## 参考来源 后的文本
            ref_section = content.split("## 参考来源")[-1] if "## 参考来源" in content else ""
            # 检查是否有 URL (http:// 或 https://)
            if not re.search(r"https?://", ref_section):
                errors.append(f"{pf}: 非原创角色但 ## 参考来源 无外部 URL 引用")
        except Exception:
            pass

    # 检查 4: 首行必须包含本角色名，不能混入其他角色名
    # 候选名 = md 文件名 stem ∪ 对应 JSON 的 name 字段（persona_00_maintainer → maintainer）
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
    # 首行是中文标题的 md（## 定位/## 红线约束/## PM Prompt）：自身命中放宽，不判失败
    _loose_first_line = {"reviewer", "scout", "writer", "pm"}
    for pf in prompt_files:
        name_stem = pf.replace(".md", "")
        full_path = os.path.join(prompts_dir, pf)
        try:
            with open(full_path) as fh:
                lines = fh.read().splitlines()
            if not lines:
                continue
            first_line = lines[0].strip()
            # 候选名：md stem ∪ 对应 JSON 的 name 字段
            candidates = {name_stem}
            for stem, jname in role_name_map.items():
                if stem == name_stem or jname == name_stem:
                    if jname:
                        candidates.add(jname)
            norm_cands = {_normalize_role_name(c) for c in candidates}
            if first_line == "<identity>":
                # <identity>…</identity> 块内首行是 "你是 <名>，CCS 角色。"
                ident_lines: list[str] = []
                for ln in lines:
                    if ln.strip() == "</identity>":
                        break
                    ident_lines.append(ln)
                own_text = " ".join(ident_lines)
                mix_text = own_text
            elif name_stem in _loose_first_line:
                # 放宽：整文件扫描兜底（scout.md 全文亦无 scout，命中与否都不判失败）
                own_text = " ".join(lines)
                mix_text = first_line
            else:
                own_text = first_line
                mix_text = first_line
            norm_own = _normalize_role_name(own_text.replace("#", ""))
            if name_stem not in _loose_first_line and not any(c in norm_own for c in norm_cands):
                errors.append(f"{pf}: 首行未包含角色名 '{name_stem}'")
            # 混入检测（限定首行/identity 块，避免整文件扫描误报）
            clean_mix = mix_text.replace("#", "").strip().lower()
            for r in known_roles:
                if _normalize_role_name(r) in norm_cands:
                    continue
                patterns: set[str] = set()
                for v in {r, _normalize_role_name(r)}:
                    patterns.update([f"({v})", f"-{v}", f"/{v}"])
                for p in patterns:
                    if p in clean_mix:
                        errors.append(f"{pf}: 首行混入其他角色名 '{r}'")
                        break
        except Exception:
            pass

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
    sys.exit(main())