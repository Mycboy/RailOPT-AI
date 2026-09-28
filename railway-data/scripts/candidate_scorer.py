import json
from pathlib import Path
from datetime import datetime
from railway_operations_cost import (
    calculate_operations_cost,
    find_affected_trains
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename):
    file_path = DATA_DIR / filename
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def parse_datetime(value):
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


# Default dataset loads
maintenance_tasks = load_json("maintenance_tasks.json")
block_windows = load_json("block_windows.json")
assets = load_json("assets.json")
train_movements = load_json("train_movements.json")
resources = load_json("resources.json")
departments = load_json("departments.json")

asset_map = {asset["asset_id"]: asset for asset in assets}
resource_map = {res["resource_id"]: res for res in resources}
department_map = {dep["department_id"]: dep for dep in departments}

DEFAULT_SETUP_BUFFER = 10
DEFAULT_TEARDOWN_BUFFER = 10
DEFAULT_INTRA_BUFFER = 5


# -------------------------------------------------------------
# TASK & ASSET ATTRIBUTES
# -------------------------------------------------------------

def get_task_asset(task, asset_map_data=None):
    if asset_map_data is None:
        asset_map_data = asset_map
    return asset_map_data.get(task["asset_id"])


def get_task_section(task, asset_map_data=None):
    asset = get_task_asset(task, asset_map_data)
    return asset["section_id"] if asset else None


def get_required_resource(task, resource_map_data=None):
    if resource_map_data is None:
        resource_map_data = resource_map
    resource_id = task.get("required_resource_id")
    if not resource_id:
        return None
    return resource_map_data.get(resource_id)


def resource_is_available(task, resource_map_data=None):
    resource = get_required_resource(task, resource_map_data)
    if resource is None:
        # If no specific resource required, general department pool can be used
        return True
    return resource.get("status", "Available") == "Available"


# -------------------------------------------------------------
# 1. OPTIMIZATION OBJECTIVE COMPONENTS
# -------------------------------------------------------------

def get_maintenance_benefit(task, asset_map_data=None):
    """
    Evaluates the intrinsic benefit of executing this maintenance activity.
    Combines priority, task type impact, and asset condition recovery.
    """
    priority = task.get("priority", "Medium")
    priority_scores = {
        "Critical": 80,
        "High": 60,
        "Medium": 40,
        "Low": 20
    }
    base_benefit = priority_scores.get(priority, 40)

    # Condition delta recovery: if asset condition is degraded, repairing it yields high benefit
    asset = get_task_asset(task, asset_map_data)
    condition_bonus = 0
    if asset:
        cond = asset.get("condition_score", 100)
        condition_bonus = int(round((100 - cond) * 0.25))

    # Task type weight (repairs restore assets more than basic inspections)
    task_type = task.get("task_type", "").lower()
    type_bonus = 5
    if "repair" in task_type or "renewal" in task_type or "overhaul" in task_type:
        type_bonus = 20
    elif "inspection" in task_type or "usfd" in task_type or "testing" in task_type:
        type_bonus = 10

    return base_benefit + condition_bonus + type_bonus


def get_asset_criticality_value(task, asset_map_data=None):
    """
    Returns asset criticality value weight.
    Mainline critical track/OHE has higher schedule priority than yard tracks.
    """
    asset = get_task_asset(task, asset_map_data)
    if asset is None:
        return 20

    criticality = asset.get("criticality", "Medium").capitalize()
    criticality_weights = {
        "Critical": 80,
        "High": 60,
        "Medium": 40,
        "Low": 20
    }
    return criticality_weights.get(criticality, 40)


def get_asset_availability_value(task, asset_map_data=None):
    """
    Urgency/Bonus due to current operating status of asset.
    Failed/Out-of-service assets have top restoration value.
    """
    asset = get_task_asset(task, asset_map_data)
    if asset is None:
        return 20

    status = asset.get("status", "Operational").lower()
    if status in ("out of service", "failed", "unavailable"):
        return 100
    elif status in ("under maintenance", "degraded", "restricted"):
        return 60
    return 20


def get_deadline_urgency_value(task, block):
    """
    Calculates deadline urgency score based on remaining slack between block end and deadline.
    """
    deadline = parse_datetime(task["deadline"])
    block_end = parse_datetime(block["end_time"])

    slack_hours = (deadline - block_end).total_seconds() / 3600.0

    if slack_hours < 0:
        return 120  # Overdue / emergency window
    elif slack_hours <= 12:
        return 90
    elif slack_hours <= 24:
        return 70
    elif slack_hours <= 48:
        return 50
    elif slack_hours <= 168:  # 7 days
        return 30
    return 15


def get_railway_operations_cost_value(
    block,
    train_movements_data=None,
    train_map_data=None
):
    """
    Calculates total railway operations disruption cost for activating this block.
    """
    ops_result = calculate_operations_cost(
        block,
        train_movements_data=train_movements_data,
        train_map_data=train_map_data
    )
    return ops_result["total_cost"]


def get_net_value_breakdown(
    task,
    block,
    asset_map_data=None,
    train_movements_data=None,
    train_map_data=None
):
    """
    Decomposes the objective into the exact 5 components:
      Maintenance Benefit
      + Asset Criticality
      + Asset Availability
      + Deadline Urgency
      - Railway Operations Cost
      = Net Value
    """
    mb = get_maintenance_benefit(task, asset_map_data)
    ac = get_asset_criticality_value(task, asset_map_data)
    aa = get_asset_availability_value(task, asset_map_data)
    du = get_deadline_urgency_value(task, block)
    roc = get_railway_operations_cost_value(block, train_movements_data, train_map_data)

    gross_value = mb + ac + aa + du
    net_value = gross_value - roc

    return {
        "task_id": task["task_id"],
        "block_id": block["block_id"],
        "maintenance_benefit": mb,
        "asset_criticality": ac,
        "asset_availability": aa,
        "deadline_urgency": du,
        "gross_value": gross_value,
        "operations_cost": roc,
        "net_value": net_value
    }


# -------------------------------------------------------------
# FEASIBILITY & CANDIDATE RANKING
# -------------------------------------------------------------

def is_feasible(
    task,
    block,
    asset_map_data=None,
    resource_map_data=None,
    allow_train_conflicts=True,
    setup_buffer=DEFAULT_SETUP_BUFFER,
    teardown_buffer=DEFAULT_TEARDOWN_BUFFER
):
    """
    Checks if a block is physically and operationally feasible for a task.
    Train conflicts are permitted when allow_train_conflicts=True because their
    impact is traded off in the CP-SAT objective function via Railway Operations Cost.
    """
    task_section = get_task_section(task, asset_map_data)
    if task_section is None or task_section != block["section_id"]:
        return False

    if block.get("status", "Available") != "Available":
        return False

    # Block must accommodate task duration plus setup and teardown buffers
    effective_duration = block["duration_minutes"] - (setup_buffer + teardown_buffer)
    if task["duration_minutes"] > effective_duration:
        return False

    # Deadline constraint: block must finish before task deadline
    deadline = parse_datetime(task["deadline"])
    block_end = parse_datetime(block["end_time"])
    if block_end > deadline:
        return False

    # Resource availability check
    if not resource_is_available(task, resource_map_data):
        return False

    # Train conflict check (if strict mode enabled)
    if not allow_train_conflicts:
        conflicts = find_affected_trains(block)
        if conflicts:
            return False

    return True


def rank_candidates(
    task,
    blocks=None,
    asset_map_data=None,
    resource_map_data=None,
    train_movements_data=None,
    train_map_data=None,
    allow_train_conflicts=True
):
    """
    Finds and ranks all candidate blocks for a maintenance task by Net Value.
    """
    if blocks is None:
        blocks = block_windows

    candidates = []
    for block in blocks:
        if not is_feasible(
            task,
            block,
            asset_map_data=asset_map_data,
            resource_map_data=resource_map_data,
            allow_train_conflicts=allow_train_conflicts
        ):
            continue

        breakdown = get_net_value_breakdown(
            task,
            block,
            asset_map_data=asset_map_data,
            train_movements_data=train_movements_data,
            train_map_data=train_map_data
        )

        candidates.append({
            "block": block,
            "breakdown": breakdown,
            "score": breakdown["net_value"]
        })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates


def print_ranked_candidates(task):
    candidates = rank_candidates(task)
    print("\n================================")
    print(f"CANDIDATE WINDOW SCORING: {task['task_id']}")
    print("================================")
    print(f"Asset: {task['asset_id']} | Section: {get_task_section(task)}")
    print(f"Priority: {task['priority']} | Duration: {task['duration_minutes']} min")
    print(f"Deadline: {task['deadline']}")
    print(f"Resource: {task.get('required_resource_id', 'Any')}")

    if not candidates:
        print("\nNo feasible candidate blocks found.")
        return

    print("\nCANDIDATE BLOCKS (Ranked by Net Value):")
    print("----------------------------------------------------------------------")
    for rank, c in enumerate(candidates, start=1):
        b = c["block"]
        bd = c["breakdown"]
        print(
            f"{rank}. Block {b['block_id']} ({b['start_time']} -> {b['end_time']})\n"
            f"   Benefit: +{bd['maintenance_benefit']} | "
            f"Criticality: +{bd['asset_criticality']} | "
            f"Avail: +{bd['asset_availability']} | "
            f"Urgency: +{bd['deadline_urgency']} | "
            f"Ops Cost: -{bd['operations_cost']} => "
            f"NET VALUE: {bd['net_value']}"
        )


if __name__ == "__main__":
    for task in maintenance_tasks[:3]:
        print_ranked_candidates(task)