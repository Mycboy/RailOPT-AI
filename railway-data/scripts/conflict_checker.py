import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def load_json(filename):
    file_path = DATA_DIR / filename

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def parse_datetime(value):
    return datetime.fromisoformat(value)

train_movements = load_json("train_movements.json")
block_windows = load_json("block_windows.json")
maintenance_tasks = load_json("maintenance_tasks.json")
assets = load_json("assets.json")
asset_map = {asset["asset_id"]: asset for asset in assets}

def get_task_section(task):
    asset = asset_map.get(task["asset_id"])
    return asset["section_id"] if asset else None


#Checks if there is a time overlap between the train and the block
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

#Finds all trains that conflict with the given block
def find_conflicts(block):
    conflicts = []

    block_section = block["section_id"]

    block_start = parse_datetime(block["start_time"])
    block_end = parse_datetime(block["end_time"])

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

#Checks if a maintenance task can be performed in a given block
def check_task_block(task, block):
    reasons = []

    #0. Block must be available
    if block["status"] != "Available":
        reasons.append("Block is not available")

    # 1. Section must match
    task_section = get_task_section(task)

    if not task_section:
        reasons.append("Unable to determine asset section")
        return reasons

    if task_section != block["section_id"]:
        reasons.append("Different section")

    # 2. Maintenance duration must fit inside the block
    if task["duration_minutes"] > block["duration_minutes"]:

        reasons.append(
            f"Block too short "
            f"(requires {task['duration_minutes']} min, "
            f"available {block['duration_minutes']} min)"
        )

    # 3. Check train conflicts
    conflicts = find_conflicts(block)

    if conflicts:

        train_ids = [
            movement["train_id"]
            for movement in conflicts
        ]

        reasons.append(
            "Train conflict: "
            + ", ".join(train_ids)
        )

    # 4. Check maintenance deadline
    deadline = parse_datetime(task["deadline"])
    block_end = parse_datetime(block["end_time"])

    if block_end > deadline:
        reasons.append(
            f"Block ends after deadline "
            f"({block['end_time']} > {task['deadline']})"
        )

    return reasons

#Finds all blocks that can be used for the given maintenance task
def find_candidate_blocks(task):
    candidates = []

    for block in block_windows:

        reasons = check_task_block(task, block)

        if not reasons:
            candidates.append(block)

    return candidates

#Analyzes all blocks for a maintenance task and returns detailed results
def analyze_blocks(task):

    results = []

    for block in block_windows:

        reasons = check_task_block(task, block)

        if reasons:
            results.append({
                "block": block,
                "feasible": False,
                "reasons": reasons
            })
        else:
            results.append({
                "block": block,
                "feasible": True,
                "reasons": []
            })

    return results

#Prints the analysis of all blocks for the given maintenance task
def print_block_analysis(task):

    results = analyze_blocks(task)

    task_section = get_task_section(task)

    print("\n================================")
    print("MAINTENANCE TASK")
    print("================================")

    print(f"Task: {task['task_id']}")
    print(f"Asset: {task['asset_id']}")
    print(f"Section: {task_section}")
    print(f"Duration: {task['duration_minutes']} minutes")
    print(f"Deadline: {task['deadline']}")

    print("\nBLOCK ANALYSIS")
    print("--------------------------------")

    for result in results:

        block = result["block"]

        if result["feasible"]:

            print(
                f"{block['block_id']} -> FEASIBLE"
            )

        else:

            print(
                f"{block['block_id']} -> REJECTED"
            )

            for reason in result["reasons"]:

                print(
                    f"          Reason: {reason}"
                )

#Prints the candidates for the given maintenance task
def print_candidates(task):

    candidates = find_candidate_blocks(task)

    task_section = get_task_section(task)

    print("\n================================")
    print("MAINTENANCE TASK")
    print("================================")

    print(f"Task: {task['task_id']}")
    print(f"Asset: {task['asset_id']}")
    print(f"Section: {task_section}")
    print(f"Duration: {task['duration_minutes']} minutes")
    print(f"Deadline: {task['deadline']}")

    print("\nFEASIBLE BLOCKS:")

    if not candidates:
        print("No feasible block found.")
        return

    for block in candidates:
        print(
            f"- {block['block_id']} | "
            f"{block['start_time']} -> "
            f"{block['end_time']}"
        )

#Prints the result of the conflict check
def print_block_result(block):
    conflicts = find_conflicts(block)

    print("\n--------------------------------")
    print(f"Block: {block['block_id']}")
    print(f"Section: {block['section_id']}")
    print(
        f"Time: {block['start_time']} -> "
        f"{block['end_time']}"
    )

    if conflicts:
        print("STATUS: CONFLICT")

        print("\nConflicting trains:")

        for movement in conflicts:
            print(
                f"- {movement['train_id']} "
                f"({movement['entry_time']} -> "
                f"{movement['exit_time']})"
            )

    else:
        print("STATUS: SAFE")
        print("No train conflicts found.")

task = maintenance_tasks[0]

print_block_analysis(task)