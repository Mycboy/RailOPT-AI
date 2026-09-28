from datetime import datetime
import json
from pathlib import Path

errors = []


# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# Load JSON file
def load_json(filename):
    file_path = DATA_DIR / filename

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError:
        errors.append(f"File not found: {filename}")
        return None

    except json.JSONDecodeError:
        errors.append(f"Invalid JSON: {filename}")
        return None


# Check whether IDs are unique
def check_unique_ids(data, id_field, dataset_name):
    if data is None:
        return

    ids = set()

    for item in data:
        item_id = item.get(id_field)

        if item_id is None:
            errors.append(
                f"{dataset_name}: Missing {id_field}"
            )
            continue

        if item_id in ids:
            errors.append(
                f"{dataset_name}: Duplicate {id_field} '{item_id}'"
            )

        ids.add(item_id)

# Check reference 
def check_references(data, field, valid_ids, dataset_name):
    if data is None:
        return

    for item in data:
        value = item.get(field)

        if value is None:
            errors.append(
                f"{dataset_name}: Missing {field}"
            )

        elif value not in valid_ids:
            errors.append(
                f"{dataset_name}: Invalid {field} '{value}'"
            )

# Check allowed values
def check_allowed_values(data, field, allowed_values, dataset_name):
    if data is None:
        return

    for item in data:
        value = item.get(field)

        if value is None:
            errors.append(
                f"{dataset_name}: Missing {field}"
            )

        elif value not in allowed_values:
            errors.append(
                f"{dataset_name}: Invalid {field} '{value}'"
            )

def check_numeric_range(data, field, minimum, maximum, dataset_name):
    if data is None:
        return

    for item in data:
        value = item.get(field)

        if value is None:
            errors.append(
                f"{dataset_name}: Missing {field}"
            )
            continue

        if not isinstance(value, (int, float)):
            errors.append(
                f"{dataset_name}: {field} must be a number"
            )
            continue

        if value < minimum or value > maximum:
            errors.append(
                f"{dataset_name}: {field}={value} "
                f"must be between {minimum} and {maximum}"
            )

def check_positive_number(data, field, dataset_name):
    if data is None:
        return

    for item in data:
        value = item.get(field)

        if value is None:
            errors.append(
                f"{dataset_name}: Missing {field}"
            )
            continue

        if not isinstance(value, (int, float)):
            errors.append(
                f"{dataset_name}: {field} must be a number"
            )
            continue

        if value <= 0:
            errors.append(
                f"{dataset_name}: {field} must be greater than 0"
            )

# Parse ISO date-time
def parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None

# Validate time range (end after start)
def check_time_range(data, start_field, end_field, dataset_name):
    if data is None:
        return

    for item in data:
        start_value = item.get(start_field)
        end_value = item.get(end_field)

        if start_value is None:
            errors.append(
                f"{dataset_name}: Missing {start_field}"
            )
            continue

        if end_value is None:
            errors.append(
                f"{dataset_name}: Missing {end_field}"
            )
            continue

        start_time = parse_datetime(start_value)
        end_time = parse_datetime(end_value)

        if start_time is None:
            errors.append(
                f"{dataset_name}: Invalid {start_field} '{start_value}'"
            )
            continue

        if end_time is None:
            errors.append(
                f"{dataset_name}: Invalid {end_field} '{end_value}'"
            )
            continue

        if end_time <= start_time:
            errors.append(
                f"{dataset_name}: {end_field} must be after "
                f"{start_field}"
            )

def check_datetime_field(data, field, dataset_name):
    if data is None:
        return

    for item in data:
        value = item.get(field)

        if value is None:
            errors.append(
                f"{dataset_name}: Missing {field}"
            )
            continue

        if parse_datetime(value) is None:
            errors.append(
                f"{dataset_name}: Invalid {field} '{value}'"
            )

def check_duration_matches_range(
    data,
    start_field,
    end_field,
    duration_field,
    dataset_name
):
    if data is None:
        return

    for item in data:
        start_value = item.get(start_field)
        end_value = item.get(end_field)
        duration_value = item.get(duration_field)

        if not start_value or not end_value or duration_value is None:
            continue

        start_time = parse_datetime(start_value)
        end_time = parse_datetime(end_value)

        if start_time is None or end_time is None:
            continue

        actual_duration = (
            end_time - start_time
        ).total_seconds() / 60

        if actual_duration != duration_value:
            errors.append(
                f"{dataset_name}: {duration_field}={duration_value} "
                f"does not match actual duration "
                f"{actual_duration:.0f} minutes"
            )



# Load all datasets
stations = load_json("stations.json")
sections = load_json("sections.json")
departments = load_json("departments.json")
assets = load_json("assets.json")
trains = load_json("trains.json")
train_movements = load_json("train_movements.json")
resources = load_json("resources.json")
maintenance_tasks = load_json("maintenance_tasks.json")
block_windows = load_json("block_windows.json")

#set of valid ids
station_ids = {item["station_id"] for item in stations}
section_ids = {item["section_id"] for item in sections}
department_ids = {item["department_id"] for item in departments}
asset_ids = {item["asset_id"] for item in assets}
train_ids = {item["train_id"] for item in trains}
resource_ids = {item["resource_id"] for item in resources}

# Validate IDs
check_unique_ids(stations, "station_id", "Stations")
check_unique_ids(sections, "section_id", "Sections")
check_unique_ids(departments, "department_id", "Departments")
check_unique_ids(assets, "asset_id", "Assets")
check_unique_ids(trains, "train_id", "Trains")
check_unique_ids(train_movements, "movement_id", "Train Movements")
check_unique_ids(resources, "resource_id", "Resources")
check_unique_ids(maintenance_tasks, "task_id", "Maintenance Tasks")
check_unique_ids(block_windows, "block_id", "Block Windows")

check_references(
    sections,
    "from_station",
    station_ids,
    "Sections"
)

check_references(
    sections,
    "to_station",
    station_ids,
    "Sections"
)
check_references(
    assets,
    "department_id",
    department_ids,
    "Assets"
)

check_references(
    assets,
    "section_id",
    section_ids,
    "Assets"
)
check_references(
    train_movements,
    "train_id",
    train_ids,
    "Train Movements"
)

check_references(
    train_movements,
    "section_id",
    section_ids,
    "Train Movements"
)
check_references(
    resources,
    "department_id",
    department_ids,
    "Resources"
)
check_references(
    maintenance_tasks,
    "asset_id",
    asset_ids,
    "Maintenance Tasks"
)

check_references(
    maintenance_tasks,
    "department_id",
    department_ids,
    "Maintenance Tasks"
)

check_references(
    maintenance_tasks,
    "required_resource_id",
    resource_ids,
    "Maintenance Tasks"
)
check_references(
    block_windows,
    "section_id",
    section_ids,
    "Block Windows"
)

check_allowed_values(
    assets,
    "asset_type",
    { "Track", "OHE", "Signal"},
    "Assets"
)

check_allowed_values(
    assets,
    "criticality",
    {"Critical","High","Medium"},
    "Assets"
)

check_allowed_values(
    assets,
    "status",
    {"Operational","Under Maintenance","Out of Service"},
    "Assets"
)

check_allowed_values(
    sections,
    "traffic_level",
    {"High","Medium","Low"},
    "Sections"
)

check_allowed_values(
    trains,
    "train_type",
    {"Passenger","Express","Superfast"},
    "Trains"
)

check_allowed_values(
    trains,
    "priority",
    {"High","Medium","Low"},
    "Trains"
)

check_allowed_values(
    train_movements,
    "direction",
    {"UP","DOWN"},
    "Train Movements"
)

check_allowed_values(
    maintenance_tasks,
    "priority",
    {"Critical", "High", "Medium"},
    "Maintenance Tasks"
)

check_allowed_values(
    maintenance_tasks,
    "status",
    {"Pending", "In Progress", "Completed", "Cancelled"},
    "Maintenance Tasks"
)

check_allowed_values(
    block_windows,
    "status",
    {"Available", "Reserved", "Used", "Unavailable"},
    "Block Windows"
)

check_numeric_range(
    assets,
    "condition_score",
    0,
    100,
    "Assets"
)

check_positive_number(
    maintenance_tasks,
    "duration_minutes",
    "Maintenance Tasks"
)

check_positive_number(
    block_windows,
    "duration_minutes",
    "Block Windows"
)

check_positive_number(
    sections,
    "length_km",
    "Sections"
)

check_numeric_range(
    stations,
    "km_from_origin",
    0,
    10000,
    "Stations"
)

check_time_range(
    train_movements,
    "entry_time",
    "exit_time",
    "Train Movements"
)

check_time_range(
    block_windows,
    "start_time",
    "end_time",
    "Block Windows"
)

check_datetime_field(
    maintenance_tasks,
    "deadline",
    "Maintenance Tasks"
)

check_duration_matches_range(
    block_windows,
    "start_time",
    "end_time",
    "duration_minutes",
    "Block Windows"
)

# Final result
if errors:
    print("\nDATA VALIDATION FAILED")

    for error in errors:
        print(f"- {error}")

else:
    print("\nDATA VALIDATION PASSED")