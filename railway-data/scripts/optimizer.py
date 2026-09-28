import json
from pathlib import Path
from datetime import datetime

from ortools.sat.python import cp_model

import railway_operations_cost
from candidate_scorer import (
    maintenance_tasks,
    block_windows,
    rank_candidates,
    resource_map
)
from railway_operations_cost import (
    calculate_operations_cost
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename):
    file_path = DATA_DIR / filename
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


MAINTENANCE_SCORE_WEIGHT = 100
OPERATIONS_COST_WEIGHT = 100
UTILIZATION_WEIGHT = 10

assets = load_json("assets.json")

asset_map = {
    asset["asset_id"]: asset
    for asset in assets
}


def get_asset_criticality(task):
    asset_id = task["asset_id"]
    asset = asset_map.get(asset_id)
    if asset is None:
        return "Unknown"
    return asset.get("criticality", "Medium")


def asset_criticality_weight(task):
    criticality = get_asset_criticality(task).lower()
    weights = {
        "critical": 40,
        "high": 30,
        "medium": 20,
        "low": 10
    }
    return weights.get(criticality, 20)


def asset_availability_weight(task):
    asset_id = task["asset_id"]
    asset = asset_map.get(asset_id)
    if asset is None:
        return 0

    status = asset.get("status", "Operational").lower()
    weights = {
        "failed": 50,
        "unavailable": 50,
        "degraded": 35,
        "restricted": 30,
        "operational": 0
    }
    return weights.get(status, 0)


def get_deadline_urgency(task, reference_time=None):
    deadline = datetime.fromisoformat(task["deadline"])
    if reference_time is None:
        # Default to the simulation/schedule planning horizon start
        reference_time = datetime.fromisoformat("2026-09-25T00:00:00")

    hours_remaining = (deadline - reference_time).total_seconds() / 3600
    if hours_remaining <= 0:
        return 100
    if hours_remaining <= 24:
        return 50
    if hours_remaining <= 72:
        return 35
    if hours_remaining <= 168:
        return 20
    return 5


def calculate_block_utilization(block_id, selected_tasks):
    block = next(
        (b for b in block_windows if b["block_id"] == block_id),
        None
    )
    if not block:
        return 0.0

    capacity = block["duration_minutes"]
    used_minutes = sum(task["duration_minutes"] for task in selected_tasks)
    if capacity == 0:
        return 0.0

    return (used_minutes / capacity) * 100.0


def build_candidate_map(tasks):
    candidate_map = {}
    for task in tasks:
        candidates = rank_candidates(task)
        candidate_map[task["task_id"]] = candidates
    return candidate_map


def tasks_share_resource(task1, task2):
    resource1 = task1.get("required_resource_id")
    resource2 = task2.get("required_resource_id")
    if not resource1 or not resource2:
        return False
    return resource1 == resource2


def time_overlap(block1, block2):
    start1 = datetime.fromisoformat(block1["start_time"])
    end1 = datetime.fromisoformat(block1["end_time"])
    start2 = datetime.fromisoformat(block2["start_time"])
    end2 = datetime.fromisoformat(block2["end_time"])
    return start1 < end2 and start2 < end1


def resource_can_perform_task(task):
    resource_id = task.get("required_resource_id")
    if not resource_id:
        return True
    resource = resource_map.get(resource_id)
    if resource is None:
        return False
    return resource["status"] == "Available"


def task_priority_weight(task):
    priority = task.get("priority")
    if priority == "Critical":
        return 10000
    if priority == "High":
        return 5000
    if priority == "Medium":
        return 1000
    return 100


def optimize_schedule(tasks):
    model = cp_model.CpModel()
    candidate_map = build_candidate_map(tasks)

    # 1. Decision Variables
    # decision_variables[task_id][block_id] = 1 if task is assigned to block
    decision_variables = {}
    for task in tasks:
        task_id = task["task_id"]
        decision_variables[task_id] = {}
        for candidate in candidate_map[task_id]:
            block = candidate["block"]
            block_id = block["block_id"]
            variable = model.NewBoolVar(f"assign_{task_id}_{block_id}")
            decision_variables[task_id][block_id] = variable

    # block_used[block_id] = 1 if at least one task is scheduled in this block
    block_used = {}
    for block in block_windows:
        block_id = block["block_id"]
        block_used[block_id] = model.NewBoolVar(f"block_used_{block_id}")

    # 2. Constraints

    # Constraint 1: A task can use at most one block
    for task in tasks:
        task_id = task["task_id"]
        variables = list(decision_variables[task_id].values())
        if variables:
            model.Add(sum(variables) <= 1)

    # Constraint 2: Link task assignment to block activation
    # If any task is scheduled in a block, block_used must be 1.
    for block in block_windows:
        block_id = block["block_id"]
        task_vars_in_block = []
        for task in tasks:
            task_id = task["task_id"]
            if block_id in decision_variables[task_id]:
                task_var = decision_variables[task_id][block_id]
                task_vars_in_block.append(task_var)
                model.Add(task_var <= block_used[block_id])

        if task_vars_in_block:
            model.Add(block_used[block_id] <= sum(task_vars_in_block))
        else:
            model.Add(block_used[block_id] == 0)

    # Constraint 3: Same resource cannot perform overlapping tasks
    for i in range(len(tasks)):
        for j in range(i + 1, len(tasks)):
            task1 = tasks[i]
            task2 = tasks[j]

            if not tasks_share_resource(task1, task2):
                continue

            task1_id = task1["task_id"]
            task2_id = task2["task_id"]

            for candidate1 in candidate_map[task1_id]:
                for candidate2 in candidate_map[task2_id]:
                    block1 = candidate1["block"]
                    block2 = candidate2["block"]

                    if not time_overlap(block1, block2):
                        continue

                    block1_id = block1["block_id"]
                    block2_id = block2["block_id"]

                    var1 = decision_variables[task1_id][block1_id]
                    var2 = decision_variables[task2_id][block2_id]

                    model.Add(var1 + var2 <= 1)

    # Constraint 4: Block Capacity Constraint
    # Combined duration of all tasks in a block cannot exceed block duration
    for block in block_windows:
        block_id = block["block_id"]
        block_capacity = block["duration_minutes"]
        duration_terms = []

        for task in tasks:
            task_id = task["task_id"]
            if block_id in decision_variables[task_id]:
                variable = decision_variables[task_id][block_id]
                duration = task["duration_minutes"]
                duration_terms.append(duration * variable)

        if duration_terms:
            model.Add(sum(duration_terms) <= block_capacity)

    # 3. Objective Function
    # Maximize total net schedule value = Task Maintenance Benefits - Block Disruption Penalties
    objective_terms = []

    # A) Value of scheduled maintenance tasks
    for task in tasks:
        task_id = task["task_id"]
        for candidate in candidate_map[task_id]:
            block = candidate["block"]
            block_id = block["block_id"]
            score = candidate["score"]
            variable = decision_variables[task_id][block_id]

            criticality_bonus = asset_criticality_weight(task)
            availability_bonus = asset_availability_weight(task)
            deadline_bonus = get_deadline_urgency(task)

            maintenance_value = (
                int(round(score * MAINTENANCE_SCORE_WEIGHT))
                + criticality_bonus * 100
                + availability_bonus * 100
                + deadline_bonus * 100
            )

            objective_terms.append(maintenance_value * variable)

            print(
                f"{task_id} -> {block_id} | "
                f"Score: {score:.2f} | "
                f"Criticality: {get_asset_criticality(task)} | "
                f"Deadline urgency: {deadline_bonus} | "
                f"Net Value: {maintenance_value}"
            )

    # B) Operations Disruption Cost (incurred once per activated block possession)
    for block in block_windows:
        block_id = block["block_id"]
        operations_result = calculate_operations_cost(block)
        operations_cost = operations_result["total_cost"]
        operations_penalty = int(round(operations_cost * OPERATIONS_COST_WEIGHT))

        if operations_penalty > 0:
            objective_terms.append(-operations_penalty * block_used[block_id])

    model.Maximize(sum(objective_terms))

    # 4. Solve
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return []

    # 5. Extract solution
    schedule = []
    for task in tasks:
        task_id = task["task_id"]
        for candidate in candidate_map[task_id]:
            block = candidate["block"]
            block_id = block["block_id"]
            variable = decision_variables[task_id][block_id]

            if solver.Value(variable) == 1:
                schedule.append({
                    "task_id": task_id,
                    "asset_id": task["asset_id"],
                    "block_id": block_id,
                    "section_id": block["section_id"],
                    "start_time": block["start_time"],
                    "end_time": block["end_time"],
                    "duration_minutes": task["duration_minutes"],
                    "score": candidate["score"],
                    "priority": task.get("priority", "Normal"),
                    "criticality": get_asset_criticality(task)
                })

    return schedule


def print_schedule(schedule):
    print("\n================================")
    print("GLOBAL OPTIMIZED SCHEDULE")
    print("================================")

    if not schedule:
        print("No feasible schedule found.")
        return

    total_score = 0
    blocks_used_map = {}

    for item in schedule:
        print(f"\nTask: {item['task_id']}")
        print(f"Asset: {item['asset_id']} (Criticality: {item.get('criticality', 'N/A')})")
        print(f"Priority: {item.get('priority', 'N/A')}")
        print(f"Section: {item['section_id']}")
        print(f"Block: {item['block_id']}")
        print(f"Duration: {item['duration_minutes']} min")
        print(f"Time: {item['start_time']} -> {item['end_time']}")
        print(f"Score: {item['score']}")

        total_score += item["score"]
        block_id = item["block_id"]
        if block_id not in blocks_used_map:
            blocks_used_map[block_id] = []
        blocks_used_map[block_id].append(item)

    print("\n================================")
    print("BLOCK UTILIZATION ANALYSIS")
    print("================================")
    total_utilized_pct = 0
    for block_id, assigned_tasks in blocks_used_map.items():
        utilization_pct = calculate_block_utilization(block_id, assigned_tasks)
        total_utilized_pct += utilization_pct
        block = next((b for b in block_windows if b["block_id"] == block_id), None)
        capacity = block["duration_minutes"] if block else 0
        used_min = sum(t["duration_minutes"] for t in assigned_tasks)
        task_ids = [t["task_id"] for t in assigned_tasks]
        print(
            f"Block {block_id}: {used_min}/{capacity} min "
            f"({utilization_pct:.1f}% utilized) | Tasks: {', '.join(task_ids)}"
        )

    avg_utilization = (
        total_utilized_pct / len(blocks_used_map) if blocks_used_map else 0
    )

    print("\n--------------------------------")
    print(f"TOTAL SCORE: {total_score}")
    print(f"TASKS SCHEDULED: {len(schedule)} / {len(maintenance_tasks)}")
    print(f"BLOCKS ACTIVATED: {len(blocks_used_map)}")
    print(f"AVERAGE BLOCK UTILIZATION: {avg_utilization:.1f}%")


if __name__ == "__main__":
    schedule = optimize_schedule(maintenance_tasks)
    print_schedule(schedule)