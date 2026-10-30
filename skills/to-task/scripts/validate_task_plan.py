#!/usr/bin/env python3
"""只读校验任务计划；仅使用 Python 3.9+ 标准库，不执行计划中的内容。

退出码：0 检查通过；1 数据或更新错误；2 参数或文件访问错误。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from decimal import Decimal
from pathlib import Path


PLAN_KEYS = {
    "version", "plan_id", "revision", "project", "goal", "requirements",
    "scope", "out_of_scope", "tasks", "open_questions", "assumptions",
}
TASK_KEYS = {
    "id", "title", "type", "priority", "status", "goal", "requirement_ids",
    "scope", "out_of_scope", "inputs", "references", "outputs", "constraints", "acceptance",
    "verification", "depends_on", "blocks", "related_to",
}
EXECUTION_FIELDS = {"evidence", "result", "execution", "started_at", "completed_at"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"重复的 JSON 对象键：{key!r}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"不允许非标准 JSON 数值：{value}")


def load_plan(path):
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=unique_object,
        parse_constant=reject_constant,
        parse_float=Decimal,
    )


def same_value(left, right):
    """迭代比较 JSON 值，保留类型且不消耗深层扩展数据的递归栈。"""
    pending = [(left, right)]
    while pending:
        current_left, current_right = pending.pop()
        if type(current_left) is not type(current_right):
            return False
        if isinstance(current_left, dict):
            if current_left.keys() != current_right.keys():
                return False
            pending.extend((value, current_right[key]) for key, value in current_left.items())
        elif isinstance(current_left, list):
            if len(current_left) != len(current_right):
                return False
            pending.extend(zip(current_left, current_right))
        elif current_left != current_right:
            return False
    return True


def has_execution_record(task, fields):
    """空占位不代表已执行；False 和 0 等实际结果仍属于记录。"""
    return any(
        key in task and not any(
            same_value(task[key], empty) for empty in (None, "", [], {})
        )
        for key in fields
    )


def has_acceptance_links(task):
    """仅用于已通过字段形状检查的任务。"""
    return any("id" in criterion for criterion in task["acceptance"])


class Checks:
    def __init__(self):
        self.errors = []

    def error(self, location, message):
        self.errors.append(f"{location}: {message}")

    def string(self, value, location):
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            self.error(location, "应为非空且无首尾空白的字符串")

    def strings(self, value, location, nonempty=False, unique=False):
        if not isinstance(value, list):
            self.error(location, "应为数组")
            return
        if nonempty and not value:
            self.error(location, "数组不能为空")
        for index, item in enumerate(value):
            self.string(item, f"{location}[{index}]")
        if unique and all(isinstance(item, str) for item in value):
            if len(value) != len(set(value)):
                self.error(location, "不能包含重复项")

    def objects(self, value, location, nonempty=False):
        if not isinstance(value, list):
            self.error(location, "应为对象数组")
            return []
        if nonempty and not value:
            self.error(location, "数组不能为空")
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                self.error(f"{location}[{index}]", "应为对象")
        return [item for item in value if isinstance(item, dict)]

    def index(self, items, location):
        result = {}
        for item in items:
            key = item["id"]
            if key in result:
                self.error(location, f"重复 ID：{key!r}")
            result[key] = item
        return result


def has_prerequisite(task_id, prerequisite, graph):
    pending = list(graph[task_id])
    visited = set()
    while pending:
        current = pending.pop()
        if current == prerequisite:
            return True
        if current not in visited:
            visited.add(current)
            pending.extend(graph[current])
    return False


def validate_plan(plan, new_plan=False):
    checks = Checks()
    if not isinstance(plan, dict):
        return ["顶层应为 JSON 对象"]

    for key in ("version", "project", "goal"):
        checks.string(plan.get(key), key)
    for key in ("scope", "out_of_scope"):
        if key in plan:
            checks.strings(plan[key], key)
    if plan.get("version") != "1.0":
        checks.error("version", "仅支持格式 1.0；旧格式须保留原数据并显式适配")
    if "plan_id" in plan or "revision" in plan:
        checks.string(plan.get("plan_id"), "plan_id")
        revision = plan.get("revision")
        if type(revision) is not int or revision < 1:
            checks.error("revision", "与 plan_id 一起提供正整数修订号，不能使用布尔值")
        elif new_plan and revision != 1:
            checks.error("revision", "新计划启用修订字段时，初始值应为 1")

    requirements = (
        checks.objects(plan["requirements"], "requirements", nonempty=True)
        if "requirements" in plan else []
    )
    tasks = checks.objects(plan.get("tasks"), "tasks")
    questions = checks.objects(plan.get("open_questions"), "open_questions")
    assumptions = checks.objects(plan.get("assumptions"), "assumptions")

    for index, requirement in enumerate(requirements):
        location = f"requirements[{index}]"
        for key in ("id", "text", "source"):
            checks.string(requirement.get(key), f"{location}.{key}")
        if "exclusion_reason" in requirement:
            checks.string(requirement["exclusion_reason"], f"{location}.exclusion_reason")

    for index, task in enumerate(tasks):
        location = f"tasks[{index}]"
        for key in ("id", "title", "type", "priority", "status", "goal"):
            checks.string(task.get(key), f"{location}.{key}")
        if task.get("type") not in ("implementation", "coordination", "integration", "human"):
            checks.error(f"{location}.type", "不支持的任务类型")
        if task.get("priority") not in ("P1", "P2", "P3"):
            checks.error(f"{location}.priority", "应为 P1、P2 或 P3")
        if new_plan and task.get("status") != "pending":
            checks.error(f"{location}.status", "新任务应初始化为 pending")
        for key in ("scope", "inputs", "outputs", "out_of_scope", "constraints"):
            checks.strings(task.get(key), f"{location}.{key}", key in ("scope", "inputs", "outputs"))
        if "references" in task:
            references = checks.objects(task["references"], f"{location}.references")
            for number, reference in enumerate(references):
                reference_location = f"{location}.references[{number}]"
                for key in ("title", "uri", "summary"):
                    checks.string(reference.get(key), f"{reference_location}.{key}")
                for key in ("section", "version"):
                    if key in reference:
                        checks.string(reference[key], f"{reference_location}.{key}")
        if "requirements" in plan or "requirement_ids" in task:
            checks.strings(task.get("requirement_ids"), f"{location}.requirement_ids", True, True)
            if "requirements" not in plan:
                checks.error(f"{location}.requirement_ids", "启用需求关联时须提供顶层 requirements")
        checks.strings(task.get("depends_on"), f"{location}.depends_on", unique=True)
        for key in ("blocks", "related_to"):
            if key in task:
                checks.strings(task[key], f"{location}.{key}", unique=True)
        acceptance = checks.objects(task.get("acceptance"), f"{location}.acceptance", True)
        verification = checks.objects(task.get("verification"), f"{location}.verification", True)
        linked = any("id" in item for item in acceptance) or any(
            "acceptance_ids" in item for item in verification
        )
        for number, criterion in enumerate(acceptance):
            checks.string(criterion.get("condition"), f"{location}.acceptance[{number}].condition")
            if linked:
                checks.string(criterion.get("id"), f"{location}.acceptance[{number}].id")
        for number, method in enumerate(verification):
            checks.string(method.get("method"), f"{location}.verification[{number}].method")
            if linked:
                checks.strings(method.get("acceptance_ids"), f"{location}.verification[{number}].acceptance_ids", True, True)

    for index, question in enumerate(questions):
        location = f"open_questions[{index}]"
        for key in ("id", "question"):
            checks.string(question.get(key), f"{location}.{key}")
        if type(question.get("blocking")) is not bool:
            checks.error(f"{location}.blocking", "应为布尔值")
        blocking = question.get("blocking") is True
        checks.strings(question.get("affected_tasks"), f"{location}.affected_tasks", blocking, True)
        if blocking:
            checks.string(question.get("decision_task"), f"{location}.decision_task")
        elif "decision_task" in question:
            checks.error(f"{location}.decision_task", "非阻塞问题不填写此字段")

    for index, assumption in enumerate(assumptions):
        checks.string(assumption.get("statement"), f"assumptions[{index}].statement")
        checks.strings(assumption.get("affected_tasks"), f"assumptions[{index}].affected_tasks", unique=True)

    # 字段形状合法后再检查引用，避免损坏输入导致类型异常。
    if checks.errors:
        return checks.errors
    requirement_map = checks.index(requirements, "requirements")
    task_map = checks.index(tasks, "tasks")
    checks.index(questions, "open_questions")
    covered = set()
    graph = {task["id"]: set(task["depends_on"]) for task in tasks}
    reverse = {task_id: set() for task_id in task_map}

    for task in tasks:
        location = f"task[{task['id']!r}]"
        for requirement_id in task.get("requirement_ids", []):
            if requirement_id not in requirement_map:
                checks.error(location, f"需求不存在：{requirement_id!r}")
            elif "exclusion_reason" in requirement_map[requirement_id]:
                checks.error(location, f"不能分配已排除的需求：{requirement_id!r}")
            covered.add(requirement_id)
        for key in ("depends_on", "blocks", "related_to"):
            for target in task.get(key, []):
                if target not in task_map:
                    checks.error(f"{location}.{key}", f"任务不存在：{target!r}")
                elif target == task["id"]:
                    checks.error(f"{location}.{key}", "不能引用自身")
                elif key == "depends_on":
                    reverse[target].add(task["id"])
        if has_acceptance_links(task):
            acceptance = checks.index(task["acceptance"], f"{location}.acceptance")
            verified = {ref for method in task["verification"] for ref in method["acceptance_ids"]}
            for ref in sorted(verified - acceptance.keys()):
                checks.error(location, f"验证引用不存在的验收 ID：{ref!r}")
            for ref in sorted(acceptance.keys() - verified):
                checks.error(location, f"验收缺少验证方法：{ref!r}")

    for requirement in requirements:
        if requirement["id"] not in covered and "exclusion_reason" not in requirement:
            checks.error("requirements", f"需求既未覆盖也未排除：{requirement['id']!r}")
    for task in tasks:
        if "blocks" in task and set(task["blocks"]) != reverse[task["id"]]:
            checks.error(f"task[{task['id']!r}].blocks", "与 depends_on 的完整反向关系不一致")
    for collection, items in (("open_questions", questions), ("assumptions", assumptions)):
        for index, item in enumerate(items):
            for ref in item["affected_tasks"]:
                if ref not in task_map:
                    checks.error(f"{collection}[{index}].affected_tasks", f"任务不存在：{ref!r}")
    for question in questions:
        if question["blocking"]:
            decision = question["decision_task"]
            if decision not in task_map or task_map[decision]["type"] != "human":
                checks.error(f"question[{question['id']!r}]", "decision_task 必须指向已有 human 任务")
            if decision in question["affected_tasks"]:
                checks.error(f"question[{question['id']!r}]", "决策任务不能阻塞自身")
    if checks.errors:
        return checks.errors

    # 使用迭代拓扑检查，长依赖链不消耗 Python 递归栈。
    counts = {key: len(dependencies) for key, dependencies in graph.items()}
    ready = deque(key for key, count in counts.items() if count == 0)
    visited = 0
    while ready:
        current = ready.popleft()
        visited += 1
        for dependent in reverse[current]:
            counts[dependent] -= 1
            if counts[dependent] == 0:
                ready.append(dependent)
    if visited != len(tasks):
        checks.error("depends_on", "依赖图存在环")
        return checks.errors

    for question in questions:
        if question["blocking"]:
            for task_id in question["affected_tasks"]:
                if not has_prerequisite(task_id, question["decision_task"], graph):
                    checks.error(f"question[{question['id']!r}]", f"受影响任务 {task_id!r} 未依赖决策任务")
    return checks.errors


def validate_update(plan, previous, execution_fields=()):
    """调用前，两份计划都必须已通过 validate_plan。"""
    checks = Checks()
    if plan["project"] != previous["project"]:
        checks.error("project", "与旧快照不一致；不是同一计划的更新")
    if "plan_id" in previous:
        if plan.get("plan_id") != previous["plan_id"]:
            checks.error("plan_id", "不得改写或删除已有计划 ID")
        if plan.get("revision") != previous["revision"] + 1:
            checks.error("revision", "应在旧快照基础上恰好增加一")
    elif "revision" in plan and plan["revision"] != 1:
        checks.error("revision", "首次启用修订字段应从 1 开始")
    if "requirements" in previous and "requirements" not in plan:
        checks.error("requirements", "不得在普通更新中移除已有需求映射")
    for key in ("scope", "out_of_scope"):
        if key in previous and key not in plan:
            checks.error(key, "不得在普通更新中删除已有计划级范围字段；无额外条目时保留空数组")
    for key in previous.keys() - PLAN_KEYS:
        if key not in plan or not same_value(previous[key], plan[key]):
            checks.error(key, "不得删除或改写计划扩展字段")

    tasks = {task["id"]: task for task in plan["tasks"]}
    old_tasks = {task["id"]: task for task in previous["tasks"]}
    protected_requirements = set()
    execution_fields = EXECUTION_FIELDS | set(execution_fields)
    for task_id, old in old_tasks.items():
        location = f"task[{task_id!r}]"
        if task_id not in tasks:
            checks.error(location, "原任务缺失；替换或撤销请另存变更提案并保留旧快照")
            continue
        current = tasks[task_id]
        if current["status"] != old["status"]:
            checks.error(location, "不得修改已有运行状态")
        extensions = old.keys() - TASK_KEYS
        for key in extensions:
            if key not in current or not same_value(old[key], current[key]):
                checks.error(f"{location}.{key}", "不得删除或改写任务扩展字段")
        if has_acceptance_links(old) and not has_acceptance_links(current):
            checks.error(location, "不得在普通更新中移除已有验收关联")
        if "references" in old and "references" not in current:
            checks.error(location, "不得在普通更新中删除已有 references 字段；没有相关资料时保留空数组")
        if old["status"] != "pending" or has_execution_record(old, execution_fields):
            protected_requirements.update(old.get("requirement_ids", []))
            old_core = {key: value for key, value in old.items() if key != "blocks"}
            current_core = {key: value for key, value in current.items() if key != "blocks"}
            if not same_value(old_core, current_core):
                checks.error(location, "已开始或含执行记录的任务需保留定义；新增工作请建立后续任务")
    for task_id in tasks.keys() - old_tasks.keys():
        if tasks[task_id]["status"] != "pending":
            checks.error(f"task[{task_id!r}].status", "新增任务应初始化为 pending")

    requirements = {item["id"]: item for item in plan.get("requirements", [])}
    old_requirements = {item["id"]: item for item in previous.get("requirements", [])}
    for requirement_id in sorted(protected_requirements):
        if not same_value(old_requirements[requirement_id], requirements.get(requirement_id)):
            checks.error(f"requirement[{requirement_id!r}]", "受保护任务的需求快照不得改写")
    return checks.errors


def main():
    parser = argparse.ArgumentParser(description="只读校验任务计划结构及可选的更新保护。")
    parser.add_argument("plan", type=Path, help="待校验的 tasks.json")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--new-plan", action="store_true", help="要求 pending 状态；如有修订号则须为 1")
    mode.add_argument("--previous", type=Path, help="同一计划保留下来的旧 JSON 快照")
    parser.add_argument(
        "--execution-field", action="append", default=[], metavar="NAME",
        help="消费者自定义的任务顶层执行字段，可重复指定，仅用于 --previous",
    )
    args = parser.parse_args()
    if args.execution_field and not args.previous:
        parser.error("--execution-field 需与 --previous 一起使用")
    if any(not name.strip() or name != name.strip() or name in TASK_KEYS for name in args.execution_field):
        parser.error("--execution-field 应为非空的扩展字段名，不能指定基础任务字段")
    plans = []
    paths = [args.plan] + ([args.previous] if args.previous else [])
    for path in paths:
        try:
            plans.append(load_plan(path))
        except OSError as error:
            print(f"文件访问失败：{path}: {error}", file=sys.stderr)
            return 2
        except (ValueError, UnicodeError, RecursionError) as error:
            print(f"JSON 读取失败：{path}: {error}", file=sys.stderr)
            return 1

    errors = []
    for index, plan in enumerate(plans):
        errors.extend(f"{paths[index]}: {error}" for error in validate_plan(
            plan, new_plan=args.new_plan and index == 0
        ))
    if not errors and args.previous:
        errors.extend(validate_update(plans[0], plans[1], args.execution_field))
    if errors:
        for error in errors:
            print(f"错误：{error}", file=sys.stderr)
        return 1
    print(f"结构校验通过：{args.plan}（{len(plans[0]['tasks'])} 个任务）")
    if any(question["blocking"] for question in plans[0]["open_questions"]):
        print("计划仍含阻塞性问题，属于草案；检查通过不代表决策已解决。")
    manual_checks = []
    if "requirements" not in plans[0]:
        manual_checks.append("需求覆盖")
    if any(not has_acceptance_links(task) for task in plans[0]["tasks"]):
        manual_checks.append("验收与验证的逐项对应")
    if args.previous and "plan_id" not in plans[1]:
        manual_checks.append("两份文件是否属于同一需求")
    if manual_checks:
        print("未启用相应扩展，需人工复核：" + "、".join(manual_checks) + "。")
    print("未检查 Markdown 语义、来源完整性、执行结果或消费者兼容性。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
