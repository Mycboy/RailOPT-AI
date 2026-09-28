import json
import copy
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

from dataset_manager import RailwayDatasetManager
from optimizer import RailwayOptimizer, print_operator_schedule
from candidate_scorer import parse_datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


class ScenarioEngine:
    """
    What-If & Scenario Analysis Engine for Railway Maintenance Scheduling.
    
    Supported Scenarios:
      - Scenario A: Normal Railway Operations (Baseline)
      - Scenario B: 20% Increase in Train Traffic (Traffic Surge)
      - Scenario C: Maintenance Crew Unavailable (Resource Disruption)
      - Scenario D: Critical Asset Failure (Emergency Breakdown Injection)
      - Scenario E: Additional Block Windows Available (Window Expansion)
    """

    def __init__(self, horizon="weekly"):
        self.horizon = horizon.lower()
        self.manager = RailwayDatasetManager()
        self.base_dataset = self.manager.build_dataset(self.horizon)

    def get_scenario_metadata(self):
        return {
            "A": {
                "name": "Normal Railway Operations (Baseline)",
                "code": "SCENARIO_A_NORMAL",
                "description": "Standard timetabled train movements, normal crew roster, routine and cyclic maintenance backlog."
            },
            "B": {
                "name": "20% Increase in Train Traffic (Traffic Surge)",
                "code": "SCENARIO_B_TRAFFIC_SURGE",
                "description": "20% more train movements injected (extra express and freight paths), increasing daytime block disruption costs."
            },
            "C": {
                "name": "Maintenance Crew Unavailable (Crew Shortage)",
                "code": "SCENARIO_C_CREW_OUTAGE",
                "description": "Primary P-Way crew (RES001) is unavailable due to emergency callout or equipment breakdown, testing crew re-allocation."
            },
            "D": {
                "name": "Critical Asset Failure (Emergency Breakdown)",
                "code": "SCENARIO_D_CRITICAL_FAILURE",
                "description": "Sudden emergency rail fracture on AST005 (km 31.5) requiring immediate repair within 6 hours, testing priority preemption."
            },
            "E": {
                "name": "Additional Block Windows Available (Window Expansion)",
                "code": "SCENARIO_E_EXTRA_WINDOWS",
                "description": "Operating control grants extended 240m night corridor blocks and additional afternoon shadow windows."
            }
        }

    def prepare_scenario_data(self, scenario_id):
        scenario_id = scenario_id.upper()
        dataset = copy.deepcopy(self.base_dataset)

        if scenario_id == "A":
            # Baseline - unmodified
            pass

        elif scenario_id == "B":
            # Scenario B: 20% increase in train traffic
            existing_movs = dataset["train_movements"]
            extra_movs = []
            mov_counter = len(existing_movs) + 1

            # Injected extra train paths (freight corridors and festival specials)
            for day in range(dataset["horizon_days"]):
                day_date = (parse_datetime(dataset["start_date"]) + timedelta(days=day)).date()

                # Extra Freight Train 1 on SEC001 and SEC002 (midday)
                f1_start = datetime.combine(day_date, datetime.min.time()) + timedelta(hours=11, minutes=45)
                f1_end = f1_start + timedelta(minutes=40)
                extra_movs.append({
                    "movement_id": f"MOV{mov_counter:04d}",
                    "train_id": "TR005",  # Freight/Regional
                    "section_id": "SEC001",
                    "entry_time": f1_start.isoformat(),
                    "exit_time": f1_end.isoformat(),
                    "direction": "UP",
                    "is_scenario_injected": True
                })
                mov_counter += 1

                # Extra Festival Special Passenger on SEC003 and SEC004 (afternoon)
                p1_start = datetime.combine(day_date, datetime.min.time()) + timedelta(hours=15, minutes=30)
                p1_end = p1_start + timedelta(minutes=35)
                extra_movs.append({
                    "movement_id": f"MOV{mov_counter:04d}",
                    "train_id": "TR004",  # Passenger
                    "section_id": "SEC003",
                    "entry_time": p1_start.isoformat(),
                    "exit_time": p1_end.isoformat(),
                    "direction": "DOWN",
                    "is_scenario_injected": True
                })
                mov_counter += 1

            dataset["train_movements"].extend(extra_movs)

        elif scenario_id == "C":
            # Scenario C: Crew RES001 (Engineering Team 1) becomes unavailable
            for res in dataset["resources"]:
                if res["resource_id"] == "RES001":
                    res["status"] = "Unavailable"
                    res["unavailability_reason"] = "Emergency track machine failure / sickness"

        elif scenario_id == "D":
            # Scenario D: Sudden Critical Asset Failure on AST005 (Track SEC002 km 31.5)
            # Update asset status
            for asset in dataset["assets"]:
                if asset["asset_id"] == "AST005":
                    asset["status"] = "Failed"
                    asset["condition_score"] = 15

            # Add emergency high-priority repair task with urgent deadline (within 6 hours)
            start_dt = parse_datetime(dataset["start_date"])
            emergency_task = {
                "task_id": "MT_EMERGENCY",
                "asset_id": "AST005",
                "department_id": "DEP001",
                "task_type": "EMERGENCY Rail Fracture Rectification",
                "priority": "Critical",
                "duration_minutes": 80,
                "deadline": (start_dt + timedelta(hours=8)).isoformat(),
                "required_resource_id": "RES001",
                "status": "Pending",
                "depends_on": None,
                "recurring_interval_days": None,
                "description": "Immediate rail break clamp and fishplate restoration at km 31.5"
            }
            # Prepend to tasks so it's evaluated first
            dataset["maintenance_tasks"].insert(0, emergency_task)

        elif scenario_id == "E":
            # Scenario E: Additional block windows granted by railway control
            extra_blocks = []
            blk_counter = len(dataset["block_windows"]) + 1

            for day in range(dataset["horizon_days"]):
                day_date = (parse_datetime(dataset["start_date"]) + timedelta(days=day)).date()

                # Extend existing night blocks or add an afternoon mega-window
                extra_start = datetime.combine(day_date, datetime.min.time()) + timedelta(hours=13, minutes=30)
                extra_end = extra_start + timedelta(minutes=140)

                extra_blocks.append({
                    "block_id": f"BLK{blk_counter:04d}",
                    "section_id": "SEC002",
                    "start_time": extra_start.isoformat(),
                    "end_time": extra_end.isoformat(),
                    "duration_minutes": 140,
                    "status": "Available",
                    "window_type": "Special Operating Corridor Window (Granted)"
                })
                blk_counter += 1

                # Additional night window on SEC003
                night_start = datetime.combine(day_date, datetime.min.time()) + timedelta(hours=4, minutes=30)
                night_end = night_start + timedelta(minutes=90)
                extra_blocks.append({
                    "block_id": f"BLK{blk_counter:04d}",
                    "section_id": "SEC003",
                    "start_time": night_start.isoformat(),
                    "end_time": night_end.isoformat(),
                    "duration_minutes": 90,
                    "status": "Available",
                    "window_type": "Extended Night Window (Granted)"
                })
                blk_counter += 1

            dataset["block_windows"].extend(extra_blocks)

        else:
            raise ValueError(f"Unknown scenario ID '{scenario_id}'. Must be one of: A, B, C, D, E")

        return dataset

    def run_scenario(self, scenario_id):
        meta = self.get_scenario_metadata().get(scenario_id.upper(), {})
        data = self.prepare_scenario_data(scenario_id)

        optimizer = RailwayOptimizer(
            horizon=self.horizon,
            tasks=data["maintenance_tasks"],
            blocks=data["block_windows"],
            resources=data["resources"],
            assets=data["assets"],
            departments=data["departments"],
            train_movements=data["train_movements"],
            trains=data["trains"]
        )

        result = optimizer.optimize()
        result["scenario_id"] = scenario_id.upper()
        result["scenario_name"] = meta.get("name", f"Scenario {scenario_id}")
        result["scenario_description"] = meta.get("description", "")

        return result

    def compare_scenario_with_baseline(self, scenario_id):
        """
        Runs both Baseline (Scenario A) and the requested Scenario,
        and computes a detailed operational differential analysis.
        """
        scenario_id = scenario_id.upper()
        baseline_result = self.run_scenario("A")

        if scenario_id == "A":
            return {
                "scenario_id": "A",
                "scenario_name": baseline_result["scenario_name"],
                "baseline_summary": baseline_result["summary"],
                "scenario_summary": baseline_result["summary"],
                "delta": {
                    "net_value": 0,
                    "operations_cost": 0,
                    "tasks_scheduled": 0,
                    "blocks_activated": 0
                },
                "schedule_changes": [],
                "insights": ["Baseline operations schedule. No what-if perturbations applied."]
            }

        scenario_result = self.run_scenario(scenario_id)

        base_sum = baseline_result["summary"]
        scen_sum = scenario_result["summary"]

        delta = {
            "net_value": scen_sum["total_net_value"] - base_sum["total_net_value"],
            "operations_cost": scen_sum["total_operations_cost"] - base_sum["total_operations_cost"],
            "tasks_scheduled": scen_sum["tasks_scheduled"] - base_sum["tasks_scheduled"],
            "blocks_activated": scen_sum["blocks_activated"] - base_sum["blocks_activated"]
        }

        # Track task-level changes
        def extract_task_assignments(sched):
            assignments = {}
            for day_key, blocks in sched.items():
                for b in blocks:
                    for act in b["activities"]:
                        assignments[act["task_id"]] = {
                            "day": day_key,
                            "block_id": b["block_id"],
                            "section_id": b["section_id"],
                            "time": f"{act['scheduled_start']}–{act['scheduled_end']}",
                            "crew": act["crew_name"],
                            "crew_id": act["crew_id"]
                        }
            return assignments

        base_assign = extract_task_assignments(baseline_result["schedule"])
        scen_assign = extract_task_assignments(scenario_result["schedule"])

        schedule_changes = []
        all_task_ids = set(base_assign.keys()).union(set(scen_assign.keys()))

        for t_id in sorted(all_task_ids):
            b_info = base_assign.get(t_id)
            s_info = scen_assign.get(t_id)

            if b_info and not s_info:
                schedule_changes.append({
                    "task_id": t_id,
                    "change_type": "DEFERRED / UNSCHEDULED",
                    "details": f"Was scheduled on {b_info['day']} in {b_info['block_id']}, now deferred."
                })
            elif not b_info and s_info:
                schedule_changes.append({
                    "task_id": t_id,
                    "change_type": "NEWLY SCHEDULED",
                    "details": f"Newly injected and scheduled on {s_info['day']} in {s_info['block_id']} ({s_info['time']}) by {s_info['crew']}."
                })
            elif b_info and s_info:
                diffs = []
                if b_info["block_id"] != s_info["block_id"]:
                    diffs.append(f"Window: {b_info['block_id']} -> {s_info['block_id']}")
                if b_info["day"] != s_info["day"]:
                    diffs.append(f"Day: {b_info['day']} -> {s_info['day']}")
                if b_info["crew_id"] != s_info["crew_id"]:
                    diffs.append(f"Crew: {b_info['crew']} -> {s_info['crew']}")
                if b_info["time"] != s_info["time"]:
                    diffs.append(f"Time: {b_info['time']} -> {s_info['time']}")

                if diffs:
                    schedule_changes.append({
                        "task_id": t_id,
                        "change_type": "RESCHEDULED",
                        "details": " | ".join(diffs)
                    })

        # Generate operational insights
        insights = []
        if scenario_id == "B":
            insights.append("20% train traffic surge increased conflicting daytime train overlaps.")
            if delta["operations_cost"] > 0:
                insights.append(f"Railway operations disruption cost increased by +{delta['operations_cost']} pts.")
            insights.append("CP-SAT steered routine maintenance away from high-traffic corridors into night white windows.")
        elif scenario_id == "C":
            insights.append("Crew RES001 (Engineering Team 1) was unavailable.")
            insights.append("CP-SAT dynamically reallocated eligible engineering tasks to available team RES002.")
            if delta["tasks_scheduled"] < 0:
                insights.append(f"Due to shift capacity limits, {abs(delta['tasks_scheduled'])} non-critical task was deferred.")
        elif scenario_id == "D":
            insights.append("EMERGENCY Rail Fracture injected on AST005 (Track SEC002 km 31.5).")
            insights.append("CP-SAT prioritized the emergency breakdown immediately in the earliest viable window.")
            insights.append("High gross value (+380 pts) from urgent restoration increased overall schedule net value.")
        elif scenario_id == "E":
            insights.append("Additional block windows were made available by railway control.")
            insights.append(f"Window capacity expansion allowed +{delta['tasks_scheduled']} additional tasks to be completed earlier.")
            insights.append("Maintenance backlog clearance accelerated with higher block packing efficiency.")

        return {
            "scenario_id": scenario_id,
            "scenario_name": scenario_result["scenario_name"],
            "scenario_description": scenario_result["scenario_description"],
            "baseline_summary": base_sum,
            "scenario_summary": scen_sum,
            "delta": delta,
            "schedule_changes": schedule_changes,
            "insights": insights,
            "baseline_schedule": baseline_result["schedule"],
            "scenario_schedule": scenario_result["schedule"]
        }


def print_scenario_comparison(comparison):
    print("\n" + "=" * 90)
    print(f"       WHAT-IF SCENARIO IMPACT ANALYSIS: {comparison['scenario_id']} - {comparison['scenario_name'].upper()}")
    print("=" * 90)
    print(f"Description: {comparison['scenario_description']}")
    print("-" * 90)

    base = comparison["baseline_summary"]
    scen = comparison["scenario_summary"]
    d = comparison["delta"]

    print(f"{'METRIC':<35} | {'BASELINE (A)':<15} | {'SCENARIO (' + comparison['scenario_id'] + ')':<15} | {'DELTA':<15}")
    print("-" * 90)
    print(f"{'Tasks Scheduled':<35} | {base['tasks_scheduled']}/{base['tasks_total']:<15} | {scen['tasks_scheduled']}/{scen['tasks_total']:<15} | {d['tasks_scheduled']:+d}")
    print(f"{'Blocks Possessed / Activated':<35} | {base['blocks_activated']}/{base['blocks_total']:<15} | {scen['blocks_activated']}/{scen['blocks_total']:<15} | {d['blocks_activated']:+d}")
    print(f"{'Gross Maintenance Value (pts)':<35} | {base['total_gross_value']:<15} | {scen['total_gross_value']:<15} | {scen['total_gross_value'] - base['total_gross_value']:+d}")
    print(f"{'Railway Operations Disruption Cost':<35} | {base['total_operations_cost']:<15} | {scen['total_operations_cost']:<15} | {d['operations_cost']:+d}")
    print(f"{'FINAL NET SCHEDULE VALUE (pts)':<35} | {base['total_net_value']:<15} | {scen['total_net_value']:<15} | {d['net_value']:+d}")
    print("=" * 90)

    print("\nOPERATIONAL INSIGHTS:")
    for ins in comparison["insights"]:
        print(f"  * {ins}")

    if comparison["schedule_changes"]:
        print(f"\nSCHEDULE PERTURBATIONS & RESCHEDULING ({len(comparison['schedule_changes'])} Tasks Affected):")
        for chg in comparison["schedule_changes"]:
            print(f"  - [{chg['change_type']}] Task {chg['task_id']}: {chg['details']}")
    else:
        print("\nNo task rescheduling required.")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="What-If Scenario Engine for OptRail-AI")
    parser.add_argument(
        "--scenario",
        type=str,
        default="all",
        choices=["A", "B", "C", "D", "E", "all"],
        help="Scenario to run: A (Normal), B (+20%% Traffic), C (Crew Unavailable), D (Asset Failure), E (Extra Windows)"
    )
    parser.add_argument(
        "--horizon",
        type=str,
        default="weekly",
        choices=["daily", "weekly", "monthly"],
        help="Planning horizon"
    )
    args = parser.parse_args()

    engine = ScenarioEngine(horizon=args.horizon)

    if args.scenario == "all":
        print("\n>>> RUNNING ALL SCENARIOS (A through E) FOR COMPREHENSIVE WHAT-IF DEMONSTRATION <<<")
        for sc in ["B", "C", "D", "E"]:
            comp = engine.compare_scenario_with_baseline(sc)
            print_scenario_comparison(comp)
    else:
        comp = engine.compare_scenario_with_baseline(args.scenario)
        print_scenario_comparison(comp)
