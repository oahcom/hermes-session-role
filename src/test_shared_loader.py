#!/usr/bin/env python3
"""
test_shared_loader.py — shared_loader.py 自检/测试
纯 stdlib，可直接运行: python3 test_shared_loader.py
"""

import json
import os
import sys
import tempfile
import unittest.mock as mock
from pathlib import Path

# 将 src 加入路径以便导入 shared_loader
sys.path.insert(0, str(Path(__file__).parent))

import shared_loader as sl


def test_parse_produce_categories():
    """测试 parse_produce_categories 解析 produce 分类"""
    # 旧格式字符串
    targets_old = ["bus cat=architecture 归档清理方案", "bus cat=code_fix 修复Bug"]
    result = sl.parse_produce_categories(targets_old)
    assert result == ["architecture", "code_fix"], f"旧格式失败: {result}"

    # 新格式 dict
    targets_new = [{"bus_cat": "architecture", "label": "归档"}, {"bus_cat": "security", "label": "安全"}]
    result = sl.parse_produce_categories(targets_new)
    assert result == ["architecture", "security"], f"新格式失败: {result}"

    # 混合格式
    targets_mixed = ["bus cat=bug_report 报告", {"bus_cat": "performance", "label": "优化"}]
    result = sl.parse_produce_categories(targets_mixed)
    assert result == ["bug_report", "performance"], f"混合格式失败: {result}"

    # 去重
    targets_dup = ["bus cat=architecture A", "bus cat=architecture B", {"bus_cat": "architecture", "label": "C"}]
    result = sl.parse_produce_categories(targets_dup)
    assert result == ["architecture"], f"去重失败: {result}"

    # 空输入
    result = sl.parse_produce_categories([])
    assert result == [], f"空输入失败: {result}"

    print("  ✓ parse_produce_categories 全部通过")


def test_parse_consume_categories():
    """测试 parse_consume_categories 解析 consume 分类"""
    # 新格式 bus 类型
    signals_new = [
        {"type": "bus", "spec": {"category": "architecture"}},
        {"type": "bus", "spec": {"category": "code_fix"}},
    ]
    result = sl.parse_consume_categories(signals_new)
    assert result == ["architecture", "code_fix"], f"新格式失败: {result}"

    # consume_all "*"
    signals_all = [{"type": "bus", "spec": {"category": "*"}}]
    result = sl.parse_consume_categories(signals_all)
    assert result == ["*"], f"consume_all 失败: {result}"

    # 旧格式 source 字符串
    signals_old = [
        {"source": "bus cat=bug_report --cat security"},
        {"source": "unread --all"},
    ]
    result = sl.parse_consume_categories(signals_old)
    assert set(result) == {"bug_report", "security", "*"}, f"旧格式失败: {result}"

    # 混合
    signals_mixed = [
        {"type": "bus", "spec": {"category": "task_spec"}},
        {"source": "bus cat=code_review --cat documentation"},
    ]
    result = sl.parse_consume_categories(signals_mixed)
    assert set(result) == {"task_spec", "code_review", "documentation"}, f"混合失败: {result}"

    # 去重
    signals_dup = [
        {"type": "bus", "spec": {"category": "architecture"}},
        {"source": "bus cat=architecture"},
    ]
    result = sl.parse_consume_categories(signals_dup)
    assert result == ["architecture"], f"去重失败: {result}"

    # 空输入
    result = sl.parse_consume_categories([])
    assert result == [], f"空输入失败: {result}"

    print("  ✓ parse_consume_categories 全部通过")


def test_export_role():
    """测试 export_role 转换单个角色"""
    role_dict = {
        "name": "test_role",
        "title": "Test Role",
        "category": "test",
        "description": "A test role",
        "lifecycle": "infinite",
        "drive": "cron",
        "cron_schedule": "0 * * * *",
        "input_signals": [{"type": "bus", "spec": {"category": "architecture"}}],
        "output_targets": [{"bus_cat": "code_fix", "label": "修复"}],
        "workgroup": [{"role": "other", "mode": "peer"}],
        "auto_send_messages": ["hello"],
    }

    exported = sl.export_role(role_dict)

    assert exported.name == "test_role"
    assert exported.title == "Test Role"
    assert exported.category == "test"
    assert exported.description == "A test role"
    assert exported.lifecycle == "infinite"
    assert exported.drive == "cron"
    assert exported.cron_schedule == "0 * * * *"
    assert exported.routing.produce == ["code_fix"]
    assert exported.routing.consume == ["architecture"]
    assert exported.routing.consume_all is False
    assert exported.workgroup == [{"role": "other", "mode": "peer"}]
    assert exported.auto_send_messages == ["hello"]

    # 测试 consume_all 为 True
    role_dict2 = {
        "name": "test_role2",
        "title": "Test Role 2",
        "category": "test",
        "description": "Test",
        "lifecycle": "ondemand",
        "drive": "ondemand",
        "cron_schedule": "",
        "input_signals": [{"type": "bus", "spec": {"category": "*"}}],
        "output_targets": [],
        "workgroup": [],
        "auto_send_messages": [],
    }
    exported2 = sl.export_role(role_dict2)
    assert exported2.routing.consume_all is True
    assert "*" in exported2.routing.consume

    print("  ✓ export_role 全部通过")


def test_load_roles():
    """测试 load_roles 加载所有角色（mock registry 模块）"""
    import sys
    # 构造 mock registry 模块（load_roles 内用 `from registry import load_all, list_roles`）
    mock_registry = mock.MagicMock()
    mock_role1 = mock.MagicMock()
    mock_role1.to_dict.return_value = {"name": "role1", "title": "Role 1"}
    mock_role2 = mock.MagicMock()
    mock_role2.to_dict.return_value = {"name": "role2", "title": "Role 2"}
    mock_registry.list_roles.return_value = [mock_role1, mock_role2]
    mock_registry.load_all.return_value = 2

    original = sys.modules.get("registry")
    sys.modules["registry"] = mock_registry
    try:
        roles = sl.load_roles()
    finally:
        if original is None:
            sys.modules.pop("registry", None)
        else:
            sys.modules["registry"] = original

    assert len(roles) == 2
    assert roles[0]["name"] == "role1"
    assert roles[1]["name"] == "role2"
    mock_registry.load_all.assert_called_once()
    mock_registry.list_roles.assert_called_once()

    print("  ✓ load_roles 全部通过")


def test_export_all():
    """测试 export_all 导出所有角色"""
    import sys
    mock_registry = mock.MagicMock()
    mock_role1 = mock.MagicMock()
    mock_role1.to_dict.return_value = {
        "name": "role1",
        "title": "Role 1",
        "category": "cat1",
        "description": "Desc 1",
        "lifecycle": "infinite",
        "drive": "cron",
        "cron_schedule": "0 * * * *",
        "input_signals": [],
        "output_targets": [],
        "workgroup": [],
        "auto_send_messages": [],
    }
    mock_role2 = mock.MagicMock()
    mock_role2.to_dict.return_value = {
        "name": "role2",
        "title": "Role 2",
        "category": "cat2",
        "description": "Desc 2",
        "lifecycle": "ondemand",
        "drive": "ondemand",
        "cron_schedule": "",
        "input_signals": [],
        "output_targets": [],
        "workgroup": [],
        "auto_send_messages": [],
    }

    mock_registry.list_roles.return_value = [mock_role1, mock_role2]
    mock_registry.load_all.return_value = 2

    original = sys.modules.get("registry")
    sys.modules["registry"] = mock_registry
    try:
        exported = sl.export_all()
    finally:
        if original is None:
            sys.modules.pop("registry", None)
        else:
            sys.modules["registry"] = original

    assert len(exported) == 2
    assert exported[0]["name"] == "role1"
    assert exported[1]["name"] == "role2"
    assert "routing" in exported[0]
    assert "produce" in exported[0]["routing"]
    assert "consume" in exported[0]["routing"]

    print("  ✓ export_all 全部通过")


def test_write_export():
    """测试 write_export 写入导出文件"""
    import sys
    with tempfile.TemporaryDirectory() as tmpdir:
        # 临时修改 EXPORT_DIR 和 EXPORT_PATH
        original_export_dir = sl.EXPORT_DIR
        original_export_path = sl.EXPORT_PATH

        sl.EXPORT_DIR = Path(tmpdir)
        sl.EXPORT_PATH = Path(tmpdir) / "roles_export.json"

        mock_registry = mock.MagicMock()
        mock_role = mock.MagicMock()
        mock_role.to_dict.return_value = {
            "name": "test_role",
            "title": "Test",
            "category": "test",
            "description": "Desc",
            "lifecycle": "infinite",
            "drive": "cron",
            "cron_schedule": "0 * * * *",
            "input_signals": [],
            "output_targets": [],
            "workgroup": [],
            "auto_send_messages": [],
        }
        mock_registry.list_roles.return_value = [mock_role]
        mock_registry.load_all.return_value = 1

        original_mod = sys.modules.get("registry")
        sys.modules["registry"] = mock_registry
        try:
            path = sl.write_export()
        finally:
            sl.EXPORT_DIR = original_export_dir
            sl.EXPORT_PATH = original_export_path
            if original_mod is None:
                sys.modules.pop("registry", None)
            else:
                sys.modules["registry"] = original_mod

        assert os.path.exists(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert "exported_at" in data
        assert "roles" in data
        assert len(data["roles"]) == 1
        assert data["roles"][0]["name"] == "test_role"

    print("  ✓ write_export 全部通过")


def test_valid_bus_categories():
    """测试 VALID_BUS_CATEGORIES 常量完整性"""
    assert isinstance(sl.VALID_BUS_CATEGORIES, set)
    assert len(sl.VALID_BUS_CATEGORIES) > 30  # 至少有 30 多个分类
    # 关键分类必须存在
    for cat in ["architecture", "code_fix", "security", "performance", "bug_report", "task_spec"]:
        assert cat in sl.VALID_BUS_CATEGORIES, f"缺少关键分类: {cat}"

    print("  ✓ VALID_BUS_CATEGORIES 全部通过")


def test_role_export_dataclass():
    """测试 RoleExport / RoleRouting dataclass 结构"""
    routing = sl.RoleRouting(produce=["a", "b"], consume=["c"], consume_all=False)
    assert routing.produce == ["a", "b"]
    assert routing.consume == ["c"]
    assert routing.consume_all is False

    # 默认值
    routing2 = sl.RoleRouting()
    assert routing2.produce == []
    assert routing2.consume == []
    assert routing2.consume_all is False

    exported = sl.RoleExport(
        name="test",
        title="Test",
        category="cat",
        description="Desc",
        lifecycle="infinite",
        drive="cron",
        cron_schedule="0 * * * *",
        routing=routing,
        workgroup=[],
        auto_send_messages=[],
    )
    assert exported.name == "test"
    assert exported.routing.produce == ["a", "b"]

    print("  ✓ RoleExport/RoleRouting dataclass 全部通过")


def run_all_tests():
    """运行所有测试"""
    print("=== 运行 shared_loader 自检测试 ===\n")

    test_parse_produce_categories()
    test_parse_consume_categories()
    test_export_role()
    test_load_roles()
    test_export_all()
    test_write_export()
    test_valid_bus_categories()
    test_role_export_dataclass()

    print("\n=== 所有测试通过 ✓ ===")
    return True


if __name__ == "__main__":
    try:
        run_all_tests()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 测试异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)