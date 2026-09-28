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
    return datetime.fromisoformat(value)

def calculate_overlap_minutes(
    train_start,
    train_end,
    block_start,
    block_end
):

    overlap_start = max(
        train_start,
        block_start
    )

    overlap_end = min(
        train_end,
        block_end
    )

    if overlap_start >= overlap_end:
        return 0

    return int(
        (overlap_end - overlap_start).total_seconds()
        / 60
    )

def find_affected_trains(block):

    affected = []

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

def get_train_details(movement):

    train_id = movement["train_id"]

    return train_map.get(train_id)

def get_train_type(movement):

    train = get_train_details(movement)

    if train is None:
        return "unknown"

    return train.get(
        "train_type",
        "unknown"
    ).lower()

def train_type_weight(train_type):

    weights = {
        "passenger": 10,
        "express": 12,
        "superfast": 12,
        "freight": 5,
        "goods": 5
    }

    return weights.get(
        train_type,
        7
    )

def get_train_priority(movement):

    train = get_train_details(movement)

    if train is None:
        return "unknown"

    return train.get(
        "priority",
        "unknown"
    ).lower()

def train_priority_weight(movement):

    priority = get_train_priority(
        movement
    )

    priority_weights = {
        "critical": 15,
        "high": 10,
        "medium": 6,
        "low": 3
    }

    return priority_weights.get(
        priority,
        5
    )

def calculate_train_cost(
    movement,
    overlap_minutes
):

    train_type = get_train_type(movement)

    priority = get_train_priority(movement)

    type_cost = train_type_weight(
        train_type
    )

    priority_cost = train_priority_weight(
        movement
    )

    duration_cost = overlap_minutes

    total_cost = (
        type_cost
        + priority_cost
        + duration_cost
    )

    return {
        "train_type": train_type,
        "priority": priority,
        "type_cost": type_cost,
        "priority_cost": priority_cost,
        "duration_cost": duration_cost,
        "total_cost": total_cost
    }

def calculate_operations_cost(block):

    affected_trains = find_affected_trains(
        block
    )

    total_cost = 0
    details = []

    for affected in affected_trains:

        movement = affected["movement"]

        overlap_minutes = affected[
            "overlap_minutes"
        ]

        cost_details = calculate_train_cost(
            movement,
            overlap_minutes
        )

        train_id = movement["train_id"]

        total_cost += cost_details[
            "total_cost"
        ]

        details.append({
            "train_id": train_id,
            "train_type": cost_details[
                "train_type"
            ],
            "priority": cost_details[
                "priority"
            ],
            "overlap_minutes": overlap_minutes,
            "type_cost": cost_details[
                "type_cost"
            ],
            "priority_cost": cost_details[
                "priority_cost"
            ],
            "duration_cost": cost_details[
                "duration_cost"
            ],
            "total_cost": cost_details[
                "total_cost"
            ]
        })

    return {
        "total_cost": total_cost,
        "affected_trains": details
    }

if __name__ == "__main__":

    block_windows = load_json(
        "block_windows.json"
    )

    for block in block_windows:

        result = calculate_operations_cost(
            block
        )

        print("\n================================")
        print(
            f"BLOCK: {block['block_id']}"
        )
        print("================================")

        if not result["affected_trains"]:

            print("Affected trains: None")
            print("Operations cost: 0")

            continue

        print("\nAffected trains:")

        for train in result[
            "affected_trains"
        ]:

            print(
                f"\n{train['train_id']} | "
                f"{train['train_type']} | "
                f"{train['priority']}"
            )

            print(
                f"  Overlap: "
                f"{train['overlap_minutes']} minutes"
            )

            print(
                f"  Type cost: "
                f"{train['type_cost']}"
            )

            print(
                f"  Priority cost: "
                f"{train['priority_cost']}"
            )

            print(
                f"  Duration cost: "
                f"{train['duration_cost']}"
            )

            print(
                f"  Train cost: "
                f"{train['total_cost']}"
            )

        print(
            "\nTOTAL OPERATIONS COST:",
            result["total_cost"]
        )