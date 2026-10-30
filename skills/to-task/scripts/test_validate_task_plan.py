"""任务计划校验器的针对性回归；不写入仓库或访问外部服务。"""

import copy
import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("validate_task_plan.py")
VALIDATOR = runpy.run_path(str(SCRIPT))
same_value = VALIDATOR["same_value"]
validate_plan = VALIDATOR["validate_plan"]
validate_update = VALIDATOR["validate_update"]


def make_plan():
    return {
        "version": "1.0",
        "plan_id": "export-feedback",
        "revision": 1,
        "project": "记录导出",
        "goal": "为下载失败提供明确反馈",
        "tasks": [{
            "id": "EXP-001",
            "title": "完善下载失败反馈",
            "type": "implementation",
            "priority": "P2",
            "status": "pending",
            "goal": "失败时显示错误且不提示成功",
            "scope": ["处理下载失败反馈"],
            "out_of_scope": ["修改导出字段"],
            "inputs": ["用户要求：下载失败应有错误提示"],
            "outputs": ["页面反馈变更及针对性验证"],
            "constraints": ["沿用现有下载接口"],
            "acceptance": [{"condition": "下载失败时没有成功提示"}],
            "verification": [{"method": "模拟失败并检查反馈"}],
            "depends_on": [],
        }],
        "open_questions": [],
        "assumptions": [],
    }


def nested_value(leaf, depth=500):
    for index in range(depth):
        leaf = {"next": leaf} if index % 2 == 0 else [leaf]
    return leaf


class ValueComparisonTests(unittest.TestCase):
    def test_deep_values_compare_without_recursion(self):
        self.assertTrue(same_value(nested_value("same"), nested_value("same")))
        self.assertFalse(same_value(nested_value("old"), nested_value("new")))

    def test_types_remain_distinct_at_nested_leaves(self):
        for left, right in [(False, 0), (True, 1), (1, Decimal("1")), ([], {})]:
            with self.subTest(left=left, right=right):
                self.assertFalse(same_value(nested_value(left), nested_value(right)))

    def test_dictionary_keys_and_list_order_are_checked(self):
        self.assertTrue(same_value({"a": 1, "b": 2}, {"b": 2, "a": 1}))
        self.assertFalse(same_value({"a": 1}, {"b": 1}))
        self.assertFalse(same_value([1], [1, 2]))
        self.assertFalse(same_value([1, 2], [2, 1]))

    def test_deep_cli_updates_preserve_inputs_and_report_changes(self):
        for leaf, expected_exit in [("original", 0), ("changed", 1)]:
            with self.subTest(leaf=leaf), tempfile.TemporaryDirectory() as directory:
                previous = make_plan()
                current = make_plan()
                current["revision"] = 2
                previous["consumer_metadata"] = nested_value("original")
                current["consumer_metadata"] = nested_value(leaf)
                previous_path = Path(directory) / "previous.json"
                current_path = Path(directory) / "current.json"
                previous_path.write_text(json.dumps(previous), encoding="utf-8")
                current_path.write_text(json.dumps(current), encoding="utf-8")
                before = (previous_path.read_bytes(), current_path.read_bytes())
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), str(current_path), "--previous", str(previous_path)],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, expected_exit, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stdout + result.stderr)
                self.assertEqual(before, (previous_path.read_bytes(), current_path.read_bytes()))
                if expected_exit:
                    self.assertIn("不得删除或改写计划扩展字段", result.stderr)


class PlanScopeTests(unittest.TestCase):
    def test_legacy_plan_without_global_scope_remains_valid(self):
        self.assertEqual(validate_plan(make_plan(), new_plan=True), [])

    def test_global_scope_is_independent_of_task_scope(self):
        plan = make_plan()
        plan["scope"] = ["完整导出体验"]
        plan["out_of_scope"] = ["生产部署"]
        self.assertEqual(validate_plan(plan, new_plan=True), [])
        self.assertNotEqual(plan["out_of_scope"], plan["tasks"][0]["out_of_scope"])

    def test_empty_global_scope_arrays_are_valid(self):
        plan = make_plan()
        plan.update(scope=[], out_of_scope=[])
        self.assertEqual(validate_plan(plan), [])

    def test_global_scope_requires_arrays_of_nonempty_strings(self):
        for key in ("scope", "out_of_scope"):
            for value in (None, "生产部署", True, [False], [""], [" 有空白 "]):
                with self.subTest(key=key, value=value):
                    plan = make_plan()
                    plan[key] = value
                    errors = validate_plan(plan)
                    self.assertTrue(errors)
                    self.assertTrue(any(key in error for error in errors))

    def test_update_cannot_silently_drop_global_scope(self):
        previous = make_plan()
        previous.update(scope=["导出"], out_of_scope=["生产部署"])
        for key in ("scope", "out_of_scope"):
            with self.subTest(key=key):
                current = copy.deepcopy(previous)
                current["revision"] = 2
                del current[key]
                self.assertTrue(any(key in error for error in validate_update(current, previous)))

    def test_pending_plan_can_add_and_revise_explicit_scope(self):
        previous = make_plan()
        current = copy.deepcopy(previous)
        current.update(revision=2, scope=["导出"], out_of_scope=["生产部署"])
        self.assertEqual(validate_update(current, previous), [])
        following = copy.deepcopy(current)
        following.update(revision=3, out_of_scope=[])
        self.assertEqual(validate_update(following, current), [])


class ReferenceTests(unittest.TestCase):
    def make_referenced_plan(self):
        plan = make_plan()
        plan["tasks"][0]["references"] = [{
            "title": "导出功能 PRD",
            "uri": "../../docs/export-prd.md#failure",
            "section": "失败反馈",
            "version": "v1",
            "summary": "下载失败必须提示错误，不能提示成功。",
        }]
        return plan

    def test_optional_references_accept_local_paths_and_urls(self):
        plan = self.make_referenced_plan()
        self.assertEqual(validate_plan(plan), [])
        plan["tasks"][0]["references"][0]["uri"] = "https://example.com/spec#export"
        self.assertEqual(validate_plan(plan), [])
        plan["tasks"][0]["references"] = []
        self.assertEqual(validate_plan(plan), [])

    def test_reference_entries_require_location_and_context(self):
        for key in ("title", "uri", "summary", "section", "version"):
            with self.subTest(key=key):
                plan = self.make_referenced_plan()
                plan["tasks"][0]["references"][0][key] = ""
                self.assertTrue(any(key in error for error in validate_plan(plan)))
        for value in (None, "docs/prd.md", ["docs/prd.md"], [{}]):
            with self.subTest(value=value):
                plan = make_plan()
                plan["tasks"][0]["references"] = value
                self.assertTrue(validate_plan(plan))

    def test_pending_task_can_revise_but_not_silently_drop_references(self):
        previous = self.make_referenced_plan()
        current = copy.deepcopy(previous)
        current["revision"] = 2
        current["tasks"][0]["references"][0]["version"] = "v2"
        self.assertEqual(validate_update(current, previous), [])
        del current["tasks"][0]["references"]
        self.assertTrue(any("references" in error for error in validate_update(current, previous)))

    def test_executed_task_preserves_its_document_reference(self):
        previous = self.make_referenced_plan()
        previous["tasks"][0]["result"] = False
        current = copy.deepcopy(previous)
        current["revision"] = 2
        current["tasks"][0]["references"][0]["uri"] = "../../docs/different-prd.md"
        self.assertTrue(any("保留定义" in error for error in validate_update(current, previous)))


class UpdateProtectionTests(unittest.TestCase):
    def test_false_execution_result_still_protects_task(self):
        previous = make_plan()
        previous["tasks"][0]["result"] = False
        current = copy.deepcopy(previous)
        current["revision"] = 2
        current["tasks"][0]["title"] = "改写已执行任务"
        self.assertTrue(any("保留定义" in error for error in validate_update(current, previous)))

    def test_owner_does_not_freeze_pending_definition(self):
        previous = make_plan()
        previous["tasks"][0]["owner"] = "team"
        current = copy.deepcopy(previous)
        current["revision"] = 2
        current["tasks"][0]["title"] = "补充待办任务说明"
        self.assertEqual(validate_update(current, previous), [])
        current["tasks"][0]["owner"] = "different-team"
        self.assertTrue(any("扩展字段" in error for error in validate_update(current, previous)))


if __name__ == "__main__":
    unittest.main()
