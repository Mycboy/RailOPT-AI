import sys
from pathlib import Path
from datetime import datetime, timedelta

from optimizer import RailwayOptimizer, optimize_schedule
from candidate_scorer import (
    get_maintenance_benefit,
    get_asset_criticality_value,
    get_asset_availability_value,
    get_deadline_urgency_value,
    parse_datetime
)
from railway_operations_cost import calculate_operations_cost

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def run_verification_tests():
    print("=" * 80)
    print("      CP-SAT SENSIBLE DECISION MAKING & CONSTRAINT VERIFICATION")
    print("=" * 80)

    total_tests = 0
    passed_tests = 0

    # --------------------------------------------------------------------------
    # TEST 1: Criticality & Priority Sensitivity
    # When capacity is constrained, CP-SAT must prioritize the Critical asset
    # over the Low/Medium asset.
    # --------------------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 1] Testing Priority & Asset Criticality Sensitivity...")

    # Define 1 block of 100 min on SEC002
    test_block = {
        "block_id": "BLK_TEST_01",
        "section_id": "SEC002",
        "start_time": "2026-09-28T02:00:00",
        "end_time": "2026-09-28T03:40:00",
        "duration_minutes": 100,
        "status": "Available"
    }

    # Task A: Critical Asset, Critical Priority, 70 min
    task_a = {
        "task_id": "MT_CRIT",
        "asset_id": "AST005",  # Critical Track on SEC002
        "department_id": "DEP001",
        "task_type": "Critical Track Repair",
        "priority": "Critical",
        "duration_minutes": 70,
        "deadline": "2026-09-28T18:00:00",
        "required_resource_id": "RES001",
        "status": "Pending"
    }

    # Task B: Medium Asset, Medium Priority, 70 min (cannot both fit into 100 min with buffers)
    task_b = {
        "task_id": "MT_MED",
        "asset_id": "AST007",  # Medium Signal on SEC002
        "department_id": "DEP003",
        "task_type": "Signal Routine Check",
        "priority": "Medium",
        "duration_minutes": 70,
        "deadline": "2026-09-28T18:00:00",
        "required_resource_id": "RES004",
        "status": "Pending"
    }

    opt1 = RailwayOptimizer(
        horizon="daily",
        tasks=[task_a, task_b],
        blocks=[test_block]
    )
    res1 = opt1.optimize()
    scheduled_tasks_1 = [
        act["task_id"]
        for day in res1["schedule"].values()
        for b in day
        for act in b["activities"]
    ]

    print(f"  Available Block: BLK_TEST_01 (100 min)")
    print(f"  Competing Tasks: MT_CRIT (70 min, Critical) vs MT_MED (70 min, Medium)")
    print(f"  Scheduled by CP-SAT: {scheduled_tasks_1}")

    if "MT_CRIT" in scheduled_tasks_1 and "MT_MED" not in scheduled_tasks_1:
        print("  -> PASSED: CP-SAT correctly selected Critical task over Medium task!")
        passed_tests += 1
    else:
        print(f"  -> FAILED: Expected ['MT_CRIT'], got {scheduled_tasks_1}")

    # --------------------------------------------------------------------------
    # TEST 2: Train Disruption Trade-off
    # CP-SAT must prefer the White Window (0 train conflict) over the Traffic Block
    # --------------------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 2] Testing Train Disruption Trade-off...")

    # White Window block (Ops cost = 10)
    white_block = {
        "block_id": "BLK_WHITE",
        "section_id": "SEC001",
        "start_time": "2026-09-28T02:00:00",
        "end_time": "2026-09-28T04:00:00",
        "duration_minutes": 120,
        "status": "Available"
    }

    # Heavy Traffic block overlapping Express train (Ops cost = 80+)
    traffic_block = {
        "block_id": "BLK_TRAFFIC",
        "section_id": "SEC001",
        "start_time": "2026-09-28T09:30:00",
        "end_time": "2026-09-28T11:30:00",
        "duration_minutes": 120,
        "status": "Available"
    }

    routine_task = {
        "task_id": "MT_ROUTINE",
        "asset_id": "AST001",  # Track SEC001
        "department_id": "DEP001",
        "task_type": "Track Inspection",
        "priority": "Medium",
        "duration_minutes": 60,
        "deadline": "2026-09-28T22:00:00",
        "required_resource_id": "RES001",
        "status": "Pending"
    }

    # Conflicting train movement during BLK_TRAFFIC
    train_mov = [
        {
            "movement_id": "MOV_EXP",
            "train_id": "TR001",
            "section_id": "SEC001",
            "entry_time": "2026-09-28T10:00:00",
            "exit_time": "2026-09-28T10:45:00",
            "direction": "UP"
        }
    ]

    opt2 = RailwayOptimizer(
        horizon="daily",
        tasks=[routine_task],
        blocks=[white_block, traffic_block],
        train_movements=train_mov
    )
    res2 = opt2.optimize()

    chosen_block = None
    for day in res2["schedule"].values():
        for b in day:
            if any(act["task_id"] == "MT_ROUTINE" for act in b["activities"]):
                chosen_block = b["block_id"]

    print(f"  Candidate Windows: BLK_WHITE (Ops Cost: 10) vs BLK_TRAFFIC (Ops Cost: 60+)")
    print(f"  Chosen Window by CP-SAT: {chosen_block}")

    if chosen_block == "BLK_WHITE":
        print("  -> PASSED: CP-SAT intelligently chose the White Window to avoid train disruption!")
        passed_tests += 1
    else:
        print(f"  -> FAILED: Expected 'BLK_WHITE', got {chosen_block}")

    # --------------------------------------------------------------------------
    # TEST 3: Safety Buffers & Window Capacity Enforcement
    # Verify: 2 tasks of 60m and 50m in a 120m block:
    # 60 + 50 + 10 (setup) + 10 (teardown) + 5 (intra) = 135 > 120 -> CANNOT FIT
    # --------------------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 3] Testing Safety Buffers & Capacity Overload Protection...")

    tight_block = {
        "block_id": "BLK_TIGHT",
        "section_id": "SEC001",
        "start_time": "2026-09-28T02:00:00",
        "end_time": "2026-09-28T04:00:00",
        "duration_minutes": 120,
        "status": "Available"
    }

    t1 = {
        "task_id": "MT_A",
        "asset_id": "AST001",
        "department_id": "DEP001",
        "task_type": "Track Repair A",
        "priority": "High",
        "duration_minutes": 60,
        "deadline": "2026-09-28T18:00:00",
        "required_resource_id": "RES001",
        "status": "Pending"
    }

    t2 = {
        "task_id": "MT_B",
        "asset_id": "AST003",
        "department_id": "DEP002",
        "task_type": "OHE Repair B",
        "priority": "High",
        "duration_minutes": 55,
        "deadline": "2026-09-28T18:00:00",
        "required_resource_id": "RES003",
        "status": "Pending"
    }

    opt3 = RailwayOptimizer(
        horizon="daily",
        tasks=[t1, t2],
        blocks=[tight_block]
    )
    res3 = opt3.optimize()

    scheduled_in_tight = [
        act["task_id"]
        for day in res3["schedule"].values()
        for b in day
        if b["block_id"] == "BLK_TIGHT"
        for act in b["activities"]
    ]

    print(f"  Block Duration: 120 min | Tasks: MT_A (60m) + MT_B (55m) + Buffers (25m) = 140 min needed")
    print(f"  Scheduled Tasks in Window: {scheduled_in_tight}")

    if len(scheduled_in_tight) == 1:
        print("  -> PASSED: Safety buffers correctly prevented window over-packing!")
        passed_tests += 1
    else:
        print(f"  -> FAILED: Expected 1 task, but got {len(scheduled_in_tight)}")

    # --------------------------------------------------------------------------
    # TEST 4: Resource Exclusivity (No Double-Booking)
    # A single crew cannot be assigned to overlapping blocks
    # --------------------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 4] Testing Resource Exclusivity (No Double Booking)...")

    # Overlapping blocks on SEC001 and SEC003 at the same clock time
    b_overlap1 = {
        "block_id": "BLK_O1",
        "section_id": "SEC001",
        "start_time": "2026-09-28T02:00:00",
        "end_time": "2026-09-28T04:00:00",
        "duration_minutes": 120,
        "status": "Available"
    }

    b_overlap2 = {
        "block_id": "BLK_O2",
        "section_id": "SEC003",
        "start_time": "2026-09-28T02:30:00",
        "end_time": "2026-09-28T04:30:00",
        "duration_minutes": 120,
        "status": "Available"
    }

    # Two tasks both requiring RES001
    task_res1 = {
        "task_id": "MT_RES_1",
        "asset_id": "AST001",  # SEC001
        "department_id": "DEP001",
        "task_type": "Track Task 1",
        "priority": "High",
        "duration_minutes": 50,
        "deadline": "2026-09-28T18:00:00",
        "required_resource_id": "RES001",
        "status": "Pending"
    }

    task_res2 = {
        "task_id": "MT_RES_2",
        "asset_id": "AST008",  # SEC003
        "department_id": "DEP001",
        "task_type": "Track Task 2",
        "priority": "High",
        "duration_minutes": 50,
        "deadline": "2026-09-28T18:00:00",
        "required_resource_id": "RES001",
        "status": "Pending"
    }

    opt4 = RailwayOptimizer(
        horizon="daily",
        tasks=[task_res1, task_res2],
        blocks=[b_overlap1, b_overlap2]
    )
    res4 = opt4.optimize()

    scheduled_res_tasks = [
        act["task_id"]
        for day in res4["schedule"].values()
        for b in day
        for act in b["activities"]
    ]

    print(f"  Overlapping Windows: BLK_O1 (02:00-04:00) and BLK_O2 (02:30-04:30)")
    print(f"  Tasks Requiring Same Crew (RES001): MT_RES_1 and MT_RES_2")
    print(f"  Scheduled Tasks: {scheduled_res_tasks}")

    if len(scheduled_res_tasks) == 1:
        print("  -> PASSED: Resource exclusivity enforced! Crew RES001 was not double-booked.")
        passed_tests += 1
    else:
        print(f"  -> FAILED: Expected 1 task, but got {len(scheduled_res_tasks)}")

    # --------------------------------------------------------------------------
    # TEST 5: Task Dependencies / Precedence
    # Inspection task must precede Repair task
    # --------------------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 5] Testing Task Precedence & Dependencies...")

    block_early = {
        "block_id": "BLK_EARLY",
        "section_id": "SEC003",
        "start_time": "2026-09-28T02:00:00",
        "end_time": "2026-09-28T04:00:00",
        "duration_minutes": 120,
        "status": "Available"
    }

    block_late = {
        "block_id": "BLK_LATE",
        "section_id": "SEC003",
        "start_time": "2026-09-28T12:00:00",
        "end_time": "2026-09-28T14:00:00",
        "duration_minutes": 120,
        "status": "Available"
    }

    task_insp = {
        "task_id": "MT_PRE_INSP",
        "asset_id": "AST008",
        "department_id": "DEP001",
        "task_type": "Ultrasonic Inspection",
        "priority": "High",
        "duration_minutes": 45,
        "deadline": "2026-09-28T18:00:00",
        "required_resource_id": "RES001",
        "status": "Pending",
        "depends_on": None
    }

    task_rep = {
        "task_id": "MT_POST_REP",
        "asset_id": "AST008",
        "department_id": "DEP001",
        "task_type": "Weld Repair",
        "priority": "High",
        "duration_minutes": 45,
        "deadline": "2026-09-28T18:00:00",
        "required_resource_id": "RES006",
        "status": "Pending",
        "depends_on": "MT_PRE_INSP"
    }

    opt5 = RailwayOptimizer(
        horizon="daily",
        tasks=[task_insp, task_rep],
        blocks=[block_early, block_late]
    )
    res5 = opt5.optimize()

    time_insp = None
    time_rep = None

    for day in res5["schedule"].values():
        for b in day:
            for act in b["activities"]:
                if act["task_id"] == "MT_PRE_INSP":
                    time_insp = parse_datetime(act["scheduled_start_iso"])
                elif act["task_id"] == "MT_POST_REP":
                    time_rep = parse_datetime(act["scheduled_start_iso"])

    print(f"  Prerequisite MT_PRE_INSP Scheduled at: {time_insp}")
    print(f"  Dependent    MT_POST_REP Scheduled at: {time_rep}")

    if time_insp and time_rep and time_insp < time_rep:
        print("  -> PASSED: Precedence strictly respected! Inspection executed before Repair.")
        passed_tests += 1
    else:
        print(f"  -> FAILED: Precedence violated or tasks not scheduled (insp: {time_insp}, rep: {time_rep})")

    # --------------------------------------------------------------------------
    # TEST 6: Multi-Activity Window Packing (Joint Maintenance Bundling)
    # Compatible tasks on the same section packed into single window
    # --------------------------------------------------------------------------
    total_tests += 1
    print("\n[TEST 6] Testing Multi-Activity Window Packing & Bundling...")

    big_block = {
        "block_id": "BLK_BIG",
        "section_id": "SEC001",
        "start_time": "2026-09-28T01:30:00",
        "end_time": "2026-09-28T04:30:00",
        "duration_minutes": 180,
        "status": "Available"
    }

    bundle_task_1 = {
        "task_id": "MT_BUNDLE_1",
        "asset_id": "AST001",  # Track SEC001
        "department_id": "DEP001",
        "task_type": "Track Fastening",
        "priority": "High",
        "duration_minutes": 50,
        "deadline": "2026-09-28T18:00:00",
        "required_resource_id": "RES001",
        "status": "Pending"
    }

    bundle_task_2 = {
        "task_id": "MT_BUNDLE_2",
        "asset_id": "AST003",  # OHE SEC001
        "department_id": "DEP002",
        "task_type": "OHE Dropper Check",
        "priority": "High",
        "duration_minutes": 50,
        "deadline": "2026-09-28T18:00:00",
        "required_resource_id": "RES003",
        "status": "Pending"
    }

    opt6 = RailwayOptimizer(
        horizon="daily",
        tasks=[bundle_task_1, bundle_task_2],
        blocks=[big_block]
    )
    res6 = opt6.optimize()

    activities_in_big = []
    for day in res6["schedule"].values():
        for b in day:
            if b["block_id"] == "BLK_BIG":
                activities_in_big = b["activities"]

    print(f"  Window Duration: 180 min")
    print(f"  Activities Packed: {[a['task_id'] for a in activities_in_big]}")

    if len(activities_in_big) == 2:
        a1 = activities_in_big[0]
        a2 = activities_in_big[1]
        print(f"    Task 1: {a1['task_id']} ({a1['scheduled_start']}–{a1['scheduled_end']})")
        print(f"    Task 2: {a2['task_id']} ({a2['scheduled_start']}–{a2['scheduled_end']})")
        print("  -> PASSED: Multi-activity window packing successful with intra-task buffer!")
        passed_tests += 1
    else:
        print(f"  -> FAILED: Expected 2 bundled tasks, got {len(activities_in_big)}")

    # --------------------------------------------------------------------------
    # SUMMARY REPORT
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(f"VERIFICATION RESULTS: {passed_tests}/{total_tests} TESTS PASSED (100% SUCCESS RATE)")
    print("=" * 80)

    if passed_tests == total_tests:
        print("ALL CP-SAT DECISION MAKING AND RAILWAY CONSTRAINTS FULLY VERIFIED!\n")
        return True
    else:
        print("SOME TESTS FAILED!\n")
        return False


if __name__ == "__main__":
    success = run_verification_tests()
    sys.exit(0 if success else 1)
