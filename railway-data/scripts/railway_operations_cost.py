import json
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename):
    file_path = DATA_DIR / filename
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


train_movements = load_json("train_movements.json")
trains = load_json("trains.json")

# Build train map for faster lookup
train_map = {
    train["train_id"]: train
    for train in trains
}


def parse_datetime(value):
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def calculate_overlap_minutes(
    train_start,
    train_end,
    block_start,
    block_end
):
    overlap_start = max(train_start, block_start)
    overlap_end = min(train_end, block_end)

    if overlap_start >= overlap_end:
        return 0

    return int(
        (overlap_end - overlap_start).total_seconds() / 60
    )


def find_affected_trains(block, train_movements_data=None):
    if train_movements_data is None:
        train_movements_data = train_movements

    affected = []
    block_section = block["section_id"]
    block_start = parse_datetime(block["start_time"])
    block_end = parse_datetime(block["end_time"])

    for movement in train_movements_data:
        if movement["section_id"] != block_section:
            continue

        train_start = parse_datetime(movement["entry_time"])
        train_end = parse_datetime(movement["exit_time"])

        overlap_minutes = calculate_overlap_minutes(
            train_start,
            train_end,
            block_start,
            block_end
        )

        if overlap_minutes > 0:
            affected.append({
                "movement": movement,
                "overlap_minutes": overlap_minutes
            })

    return affected


def get_train_details(movement, train_map_data=None):
    if train_map_data is None:
        train_map_data = train_map
    train_id = movement["train_id"]
    return train_map_data.get(train_id)


def get_train_type(movement, train_map_data=None):
    train = get_train_details(movement, train_map_data)
    if train is None:
        return "unknown"
    return train.get("train_type", "unknown").lower()


def train_type_weight(train_type):
    weights = {
        "superfast": 25,
        "express": 18,
        "passenger": 10,
        "freight": 6,
        "goods": 6
    }
    return weights.get(train_type, 10)


def get_train_priority(movement, train_map_data=None):
    train = get_train_details(movement, train_map_data)
    if train is None:
        return "unknown"
    return train.get("priority", "unknown").lower()


def train_priority_weight(movement, train_map_data=None):
    priority = get_train_priority(movement, train_map_data)
    priority_weights = {
        "critical": 25,
        "high": 18,
        "medium": 10,
        "low": 5
    }
    return priority_weights.get(priority, 8)


def calculate_train_cost(
    movement,
    overlap_minutes,
    train_map_data=None
):
    train_type = get_train_type(movement, train_map_data)
    priority = get_train_priority(movement, train_map_data)

    type_cost = train_type_weight(train_type)
    priority_cost = train_priority_weight(movement, train_map_data)
    # Overlap duration cost (1 point per minute of train regulation)
    duration_cost = overlap_minutes

    total_cost = type_cost + priority_cost + duration_cost

    return {
        "train_type": train_type,
        "priority": priority,
        "type_cost": type_cost,
        "priority_cost": priority_cost,
        "duration_cost": duration_cost,
        "total_cost": total_cost
    }


def calculate_operations_cost(
    block,
    train_movements_data=None,
    train_map_data=None,
    fixed_possession_cost=10
):
    """
    Calculates total railway operations disruption cost for taking a block.
    
    Formula:
      Fixed Block Possession Overhead (PTW, OHE de-energization, route clearance)
      + Sum of (Train Type Weight + Priority Weight + Overlap Delay Minutes)
        for each conflicting train movement.
    """
    affected_trains = find_affected_trains(block, train_movements_data)

    total_train_cost = 0
    details = []

    for affected in affected_trains:
        movement = affected["movement"]
        overlap_minutes = affected["overlap_minutes"]

        cost_details = calculate_train_cost(
            movement,
            overlap_minutes,
            train_map_data
        )

        train_id = movement["train_id"]
        total_train_cost += cost_details["total_cost"]

        details.append({
            "train_id": train_id,
            "train_type": cost_details["train_type"],
            "priority": cost_details["priority"],
            "overlap_minutes": overlap_minutes,
            "type_cost": cost_details["type_cost"],
            "priority_cost": cost_details["priority_cost"],
            "duration_cost": cost_details["duration_cost"],
            "total_cost": cost_details["total_cost"]
        })

    # Fixed block possession cost is incurred only when activating a block
    # If no trains are affected, total cost is just the fixed possession cost
    total_cost = fixed_possession_cost + total_train_cost

    return {
        "fixed_possession_cost": fixed_possession_cost,
        "train_disruption_cost": total_train_cost,
        "total_cost": total_cost,
        "affected_trains": details
    }


if __name__ == "__main__":
    block_windows_data = load_json("block_windows.json")

    for block in block_windows_data:
        result = calculate_operations_cost(block)
        print("\n================================")
        print(f"BLOCK: {block['block_id']} ({block['section_id']})")
        print(f"Window: {block['start_time']} -> {block['end_time']}")
        print("================================")

        if not result["affected_trains"]:
            print(f"Affected trains: None (White Window / Shadow Block)")
            print(f"Fixed possession cost: {result['fixed_possession_cost']}")
            print(f"Total Operations Cost: {result['total_cost']}")
            continue

        print(f"Affected trains ({len(result['affected_trains'])}):")
        for train in result["affected_trains"]:
            print(
                f"  - {train['train_id']} | Type: {train['train_type']} | "
                f"Priority: {train['priority']} | Overlap: {train['overlap_minutes']}m | "
                f"Cost: {train['total_cost']}"
            )

        print(f"Fixed possession cost: {result['fixed_possession_cost']}")
        print(f"Train disruption cost: {result['train_disruption_cost']}")
        print(f"TOTAL OPERATIONS COST: {result['total_cost']}")