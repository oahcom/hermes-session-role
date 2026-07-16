#!/usr/bin/env python3
"""create_skill_library.py — 创建技能库（SKILL.md 目录格式）

自动生成所有技能文件的 SKILL.md 格式 + YAML frontmatter。
"""
import json, os, re
from pathlib import Path

SKILLS_ROOT = Path(os.environ.get('HERMES_SKILLS_ROOT',
    str(Path.home() / 'shared-skills' / 'hermes-origin'))) / 'skills'

# SKILL.md contents keyed by relative path (e.g. "code/write_code/SKILL.md")
SKILLS = {
    "code/write_code/SKILL.md": """---
description: >-
  编写、修改或审查代码。用户需要编码实现时触发。这是流程工具，非行为约束。
models: []
visibility: auto
---
# write_code — 编码

单轮单任务、编辑后必验证、留痕(commit+bus)
""",
    "code/write_tests/SKILL.md": """---
description: >-
  为代码编写测试用例。用户说"加测试"或"测试覆盖"时触发。
models: []
visibility: auto
---
# write_tests — 测试编写

边界、异常、正常路径、覆盖率
""",
    "code/refactor/SKILL.md": """---
description: >-
  重构代码，改善结构不改变行为。用户说"重构"或"优化代码"时触发。
models: []
visibility: auto
---
# refactor — 重构

提取函数、重命名、消除重复、降低圈复杂度
""",
    "code/debug/SKILL.md": """---
description: >-
  调试和修复代码缺陷。用户说"修bug"或"出错了"时触发。
models: []
visibility: auto
---
# debug — 调试

复现→二分→定位→修复→验证
""",
    "code/git_commit/SKILL.md": """---
description: >-
  提交代码变更到 git。用户说"提交"或"commit"时触发。
models: []
visibility: auto
---
# git_commit — 提交

feat/fix/refactor: 中文描述
""",
    "pg/impl_plan/SKILL.md": """---
description: >-
  编码前将任务拆分为可独立验证的步骤（E1-E5）。用户说"写代码"或"实现"时触发。
models: []
visibility: auto
---
# impl_plan — 实施计划

编码前将任务拆为可独立验证的步骤。
""",
    "pg/risk_assess/SKILL.md": """---
description: >-
  编码前对每个步骤做风险矩阵评估（概率×影响）。用户说"评估风险"时触发。
models: []
visibility: auto
---
# risk_assess — 风险评估

编码前对每个步骤做风险矩阵评估。
""",
    # 其余见 convert_skills_to_skillmd.py 的批量转换脚本
}

def create_all():
    written = 0
    for relpath, content in sorted(SKILLS.items()):
        full = SKILLS_ROOT / relpath
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
        written += 1
    print(f"创建 {written} 个 SKILL.md 在 {SKILLS_ROOT}")

if __name__ == "__main__":
    create_all()
