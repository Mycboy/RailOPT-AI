import json
from pathlib import Path
from datetime import datetime
from railway_operations_cost import (
    calculate_operations_cost
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename):
    file_path = DATA_DIR / filename

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def parse_datetime(value):
    return datetime.fromisoformat(value)


# -----------------------------
# LOAD DATA
# -----------------------------

maintenance_tasks = load_json("maintenance_tasks.json")
block_windows = load_json("block_windows.json")
assets = load_json("assets.json")
train_movements = load_json("train_movements.json")
resources = load_json("resources.json")


# -----------------------------
# CREATE LOOKUP MAPS
# -----------------------------

asset_map = {
    asset["asset_id"]: asset
    for asset in assets
}

resource_map = {
    resource["resource_id"]: resource
    for resource in resources
}


# -----------------------------
# TASK → ASSET → SECTION
# -----------------------------

def get_task_asset(task):
    return asset_map.get(task["asset_id"])

def score_train_disruption(block):

    result = calculate_operations_cost(
        block
    )

    cost = result["total_cost"]

    if cost == 0:
        return 100

    if cost <= 20:
        return 80

    if cost <= 50:
        return 60

    if cost <= 100:
        return 40

    return 10

def get_task_section(task):
    asset = get_task_asset(task)

    if asset:
        return asset["section_id"]

    return None

def check_time_overlap(
    train_start,
    train_end,
    block_start,
    block_end
):
    return (
        train_start < block_end
        and train_end > block_start
    )

def get_required_resource(task):
    resource_id = task.get("required_resource_id")

    if not resource_id:
        return None

    return resource_map.get(resource_id)

def resource_is_available(task):

    resource = get_required_resource(task)

    if resource is None:
        return False

    return resource.get("status") == "Available"

def find_conflicts(block):
    conflicts = []

    block_section = block["section_id"]

    block_start = parse_datetime(
        block["start_time"]
    )

    block_end = parse_datetime(
        block["end_time"]
    )

    for movement in train_movements:

        if movement["section_id"] != block_section:
            continue

        train_start = parse_datetime(
            movement["entry_time"]
        )

        train_end = parse_datetime(
            movement["exit_time"]
        )

        if check_time_overlap(
            train_start,
            train_end,
            block_start,
            block_end
        ):
            conflicts.append(movement)

    return conflicts

def is_feasible(task, block):

    task_section = get_task_section(task)

    if task_section is None:
        return False

    # Section must match
    if task_section != block["section_id"]:
        return False

    # Resource must be available
    if not resource_is_available(task):
        return False

    # Block must be available
    if block["status"] != "Available":
        return False

    # Block must be long enough
    if task["duration_minutes"] > block["duration_minutes"]:
        return False

    # No train conflicts
    conflicts = find_conflicts(block)

    if conflicts:
        return False

    # Block must finish before deadline
    deadline = parse_datetime(task["deadline"])

    block_end = parse_datetime(
        block["end_time"]
    )

    if block_end > deadline:
        return False

    return True

def score_maintenance_priority(task):

    priority_scores = {
        "Critical": 100,
        "High": 75,
        "Medium": 50
    }

    return priority_scores.get(
        task["priority"],
        0
    )

def score_asset_criticality(task):

    asset = get_task_asset(task)

    if asset is None:
        return 0

    criticality_scores = {
        "Critical": 100,
        "High": 75,
        "Medium": 50
    }

    return criticality_scores.get(
        asset["criticality"],
        0
    )

def score_deadline_urgency(task, block):

    deadline = parse_datetime(
        task["deadline"]
    )

    block_end = parse_datetime(
        block["end_time"]
    )

    slack_minutes = (
        deadline - block_end
    ).total_seconds() / 60

    if slack_minutes <= 60:
        return 100

    if slack_minutes <= 180:
        return 80

    if slack_minutes <= 360:
        return 60

    if slack_minutes <= 720:
        return 40

    return 20

def score_block_efficiency(task, block):

    task_duration = task["duration_minutes"]
    block_duration = block["duration_minutes"]

    slack = block_duration - task_duration

    if slack <= 15:
        return 100

    if slack <= 30:
        return 80

    if slack <= 60:
        return 60

    if slack <= 120:
        return 40

    return 20

def score_resource_availability(task):

    resource_id = task.get(
        "required_resource_id"
    )

    if not resource_id:
        return 50

    resource = resource_map.get(
        resource_id
    )

    if resource is None:
        return 0

    if resource.get("status", "Available") == "Available":
        return 100

    return 0

def calculate_score(task, block):

    maintenance_score = (
        score_maintenance_priority(task)
    )

    criticality_score = (
        score_asset_criticality(task)
    )

    deadline_score = (
        score_deadline_urgency(
            task,
            block
        )
    )

    efficiency_score = (
        score_block_efficiency(
            task,
            block
        )
    )

    disruption_score = (
        score_train_disruption(block)
    )

    resource_score = (
        score_resource_availability(task)
    )

    final_score = (
        maintenance_score * 0.25
        + criticality_score * 0.25
        + deadline_score * 0.20
        + efficiency_score * 0.10
        + disruption_score * 0.10
        + resource_score * 0.10
    )

    return round(final_score, 2)

def rank_candidates(task):

    candidates = []

    for block in block_windows:

        if not is_feasible(task, block):
            continue

        score = calculate_score(
            task,
            block
        )

        candidates.append({
            "block": block,
            "score": score
        })

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return candidates

def print_ranked_candidates(task):

    candidates = rank_candidates(task)

    print("\n================================")
    print("CANDIDATE WINDOW SCORING")
    print("================================")

    print(f"Task: {task['task_id']}")
    print(f"Asset: {task['asset_id']}")
    print(f"Section: {get_task_section(task)}")
    print(f"Priority: {task['priority']}")
    print(f"Duration: {task['duration_minutes']} minutes")
    print(f"Deadline: {task['deadline']}")

    print("\nRANKED CANDIDATE BLOCKS")
    print("--------------------------------")

    if not candidates:
        print("No feasible blocks found.")
        return

    for rank, candidate in enumerate(
        candidates,
        start=1
    ):
        block = candidate["block"]

        print(
            f"{rank}. {block['block_id']} "
            f"-> SCORE: {candidate['score']}"
        )

        print(
            f"   Time: "
            f"{block['start_time']} -> "
            f"{block['end_time']}"
        )

    print("\nRECOMMENDED WINDOW")
    print("--------------------------------")

    best = candidates[0]

    print(
        f"Block: {best['block']['block_id']}"
    )

    print(
        f"Score: {best['score']}"
    )

    print(
        f"Time: "
        f"{best['block']['start_time']} -> "
        f"{best['block']['end_time']}"
    )


# -----------------------------
task = maintenance_tasks[0]

print_ranked_candidates(task)