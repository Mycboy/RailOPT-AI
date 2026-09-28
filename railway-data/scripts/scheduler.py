from candidate_scorer import (
    maintenance_tasks,
    block_windows,
    rank_candidates
)

def schedule_tasks(tasks):

    schedule = []
    used_blocks = set()

    for task in tasks:

        candidates = rank_candidates(task)

        selected = None

        for candidate in candidates:

            block = candidate["block"]

            if block["block_id"] in used_blocks:
                continue

            selected = candidate
            break

        if selected:

            block = selected["block"]

            schedule.append({
                "task_id": task["task_id"],
                "asset_id": task["asset_id"],
                "block_id": block["block_id"],
                "section_id": block["section_id"],
                "start_time": block["start_time"],
                "end_time": block["end_time"],
                "score": selected["score"]
            })

            used_blocks.add(
                block["block_id"]
            )

    return schedule

def print_schedule(schedule):

    print("\n================================")
    print("OPTIMIZED MAINTENANCE SCHEDULE")
    print("================================")

    if not schedule:
        print("No tasks could be scheduled.")
        return

    for item in schedule:

        print(
            f"\nTask: {item['task_id']}"
        )

        print(
            f"Asset: {item['asset_id']}"
        )

        print(
            f"Section: {item['section_id']}"
        )

        print(
            f"Block: {item['block_id']}"
        )

        print(
            f"Time: "
            f"{item['start_time']} -> "
            f"{item['end_time']}"
        )

        print(
            f"Score: {item['score']}"
        )
    
schedule = schedule_tasks(
    maintenance_tasks
)

print_schedule(schedule)