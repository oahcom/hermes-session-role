#!/usr/bin/env python3
"""Extract unique system_prompt parts from persona JSONs, strip common base.md content."""
import json, os, re

PERSONA_DIR = "/home/administrator/hermes-session-roles/personas/session-roles"
OUT_DIR = "/home/administrator/hermes-session-roles/prompts/roles"
os.makedirs(OUT_DIR, exist_ok=True)

# Mapping: persona filename stem -> output filename
MAPPING = {
    "persona_00_maintainer": "maintainer.md",
    "persona_01_scout": "scout.md",
    "persona_03_curator": "curator.md",
    "persona_04_coordinator": "coordinator.md",
    "persona_05_developer": "developer.md",
    "persona_06_closer": "closer.md",
    "persona_08_optimizer": "optimizer.md",
    "persona_10_codex_dev": "codex_dev.md",
    "persona_11_ccs_monitor": "ccs_monitor.md",
    "persona_12_debate_verifier": "debate_verifier.md",
    "persona_13_product_architect": "product_architect.md",
}

# The common sections to strip (everything from these headers onward)
COMMON_MARKERS = [
    "## CORRECTIVE DIRECTIVE: 永不停止",
    "## 团队协作协议 (Bus Inter-session Communication)",
]

def strip_common(text):
    """Remove from the first common marker to end."""
    # Find the earliest occurrence of any common marker
    earliest = len(text)
    for marker in COMMON_MARKERS:
        pos = text.find(marker)
        if pos != -1 and pos < earliest:
            earliest = pos
    if earliest < len(text):
        text = text[:earliest]
    return text.rstrip() + "\n"

for stem, out_name in MAPPING.items():
    in_path = os.path.join(PERSONA_DIR, f"{stem}.json")
    with open(in_path) as f:
        data = json.load(f)
    prompt = data["system_prompt"]
    unique = strip_common(prompt)
    out_path = os.path.join(OUT_DIR, out_name)
    with open(out_path, "w") as f:
        f.write(unique)
    print(f"{out_name}: {len(prompt)} -> {len(unique)} chars")

print("Done.")
