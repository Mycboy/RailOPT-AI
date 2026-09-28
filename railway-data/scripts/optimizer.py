import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

from ortools.sat.python import cp_model

from candidate_scorer import (
    get_maintenance_benefit,
    get_asset_criticality_value,
    get_asset_availability_value,
    get_deadline_urgency_value,
    get_railway_operations_cost_value,
    get_net_value_breakdown,
    DEFAULT_SETUP_BUFFER,
    DEFAULT_TEARDOWN_BUFFER,
    DEFAULT_INTRA_BUFFER,
    parse_datetime
)
from railway_operations_cost import (
    calculate_operations_cost,
    find_affected_trains
)
from dataset_manager import RailwayDatasetManager

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename, directory=DATA_DIR):
    file_path = directory / filename
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


class RailwayOptimizer:
    """
    CP-SAT Optimization Engine for Railway Maintenance Scheduling.
    
    Objective:
      Net Value = Maintenance Benefit + Asset Criticality + Asset Availability 
                  + Deadline Urgency - Railway Operations Cost + Bundling Bonus
    
    Constraints:
      1. Single Block Assignment (at most 1 block per task)
      2. Block Activation Linkage (block is active if any task is assigned)
      3. Multi-Activity Packing with Setup, Teardown, and Intra-Task Safety Buffers
      4. Maintenance Crew & Department-Specific Assignment (non-overlap, shift capacity)
      5. Section / Track Exclusivity (no overlapping blocks on same section)
      6. Task Precedence & Dependencies (inspection before repair)
      7. Deadline & Planning Horizon Compliance
    """

    def __init__(
        self,
        horizon="weekly",
        tasks=None,
        blocks=None,
        resources=None,
        assets=None,
        departments=None,
        train_movements=None,
        trains=None,
        setup_buffer=DEFAULT_SETUP_BUFFER,
        teardown_buffer=DEFAULT_TEARDOWN_BUFFER,
        intra_buffer=DEFAULT_INTRA_BUFFER,
        bundling_bonus=15
    ):
        self.horizon = horizon.lower()
        self.setup_buffer = setup_buffer
        self.teardown_buffer = teardown_buffer
        self.intra_buffer = intra_buffer
        self.bundling_bonus = bundling_bonus

        # Load or generate dataset for selected horizon
        if tasks is not None and blocks is not None:
            self.tasks = tasks
            self.blocks = blocks
            self.resources = resources or load_json("resources.json")
            self.assets = assets or load_json("assets.json")
            self.departments = departments or load_json("departments.json")
            self.train_movements = train_movements or load_json("train_movements.json")
            self.trains = trains or load_json("trains.json")
        else:
            manager = RailwayDatasetManager()
            dataset = manager.build_dataset(self.horizon)
            self.tasks = dataset["maintenance_tasks"]
            self.blocks = dataset["block_windows"]
            self.resources = dataset["resources"]
            self.assets = dataset["assets"]
            self.departments = dataset["departments"]
            self.train_movements = dataset["train_movements"]
            self.trains = dataset["trains"]

        # Build lookup tables
        self.asset_map = {a["asset_id"]: a for a in self.assets}
        self.resource_map = {r["resource_id"]: r for r in self.resources}
        self.department_map = {d["department_id"]: d for d in self.departments}
        self.train_map = {t["train_id"]: t for t in self.trains}
        self.block_map = {b["block_id"]: b for b in self.blocks}
        self.task_map = {t["task_id"]: t for t in self.tasks}

        # Precompute operational costs for each block
        self.block_ops_costs = {}
        for block in self.blocks:
            res = calculate_operations_cost(
                block,
                train_movements_data=self.train_movements,
                train_map_data=self.train_map
            )
            self.block_ops_costs[block["block_id"]] = res

    def get_candidate_blocks_for_task(self, task):
        """
        Determines feasible candidate blocks for a task based on physical section,
        duration + safety buffers, and task deadline.
        """
        asset = self.asset_map.get(task["asset_id"])
        if not asset:
            return []

        section_id = asset["section_id"]
        deadline = parse_datetime(task["deadline"])
        min_required_duration = task["duration_minutes"] + self.setup_buffer + self.teardown_buffer

        candidates = []
        for block in self.blocks:
            if block["section_id"] != section_id:
                continue

            if block.get("status", "Available") != "Available":
                continue

            if block["duration_minutes"] < min_required_duration:
                continue

            block_end = parse_datetime(block["end_time"])
            if block_end > deadline:
                continue

            candidates.append(block)

        return candidates

    def get_eligible_resources_for_task(self, task):
        """
        Returns eligible resources/crews for a task based on department and required skills.
        """
        req_res_id = task.get("required_resource_id")
        if req_res_id and req_res_id in self.resource_map:
            res = self.resource_map[req_res_id]
            if res.get("status", "Available") == "Available":
                return [res]
            # If specified resource is unavailable, return empty unless flexible
            return []

        # Find any available resource matching department
        dep_id = task.get("department_id")
        matching = [
            r for r in self.resources
            if r.get("department_id") == dep_id and r.get("status", "Available") == "Available"
        ]
        return matching

    def optimize(self):
        """
        Builds and solves the CP-SAT model.
        """
        model = cp_model.CpModel()

        # -------------------------------------------------------------
        # 1. Candidate Generation & Decision Variables
        # -------------------------------------------------------------
        candidate_map = {}
        # x[task_id, block_id] = 1 if task is scheduled in block
        x = {}
        task_candidates = {}

        for task in self.tasks:
            t_id = task["task_id"]
            candidates = self.get_candidate_blocks_for_task(task)
            task_candidates[t_id] = candidates

            x[t_id] = {}
            for block in candidates:
                b_id = block["block_id"]
                x[t_id][b_id] = model.NewBoolVar(f"x_{t_id}_{b_id}")

        # y[block_id] = 1 if block is activated (possessed for maintenance)
        y = {}
        for block in self.blocks:
            b_id = block["block_id"]
            y[b_id] = model.NewBoolVar(f"y_{b_id}")

        # -------------------------------------------------------------
        # 2. Constraints
        # -------------------------------------------------------------

        # Constraint 1: At most one block assignment per task
        for task in self.tasks:
            t_id = task["task_id"]
            task_vars = list(x[t_id].values())
            if task_vars:
                model.Add(sum(task_vars) <= 1)

        # Constraint 2: Link Task Assignment to Block Activation
        # If any task is scheduled in block b, then y[b] must be 1.
        for block in self.blocks:
            b_id = block["block_id"]
            tasks_in_block = [
                x[t["task_id"]][b_id]
                for t in self.tasks
                if b_id in x[t["task_id"]]
            ]

            if tasks_in_block:
                # y[b] >= x[t, b] for each task
                for t_var in tasks_in_block:
                    model.Add(t_var <= y[b_id])
                # y[b] <= sum(tasks_in_block)
                model.Add(y[b_id] <= sum(tasks_in_block))
            else:
                model.Add(y[b_id] == 0)

        # Constraint 3: Multi-Activity Packing with Safety Buffers
        # Effective working window formulation:
        # (Setup + Teardown - Intra) * y[b] + sum((duration + Intra) * x[t, b]) <= Capacity * y[b]
        for block in self.blocks:
            b_id = block["block_id"]
            capacity = block["duration_minutes"]

            tasks_in_block = [
                (t, x[t["task_id"]][b_id])
                for t in self.tasks
                if b_id in x[t["task_id"]]
            ]

            if tasks_in_block:
                fixed_overhead = (self.setup_buffer + self.teardown_buffer - self.intra_buffer)
                task_terms = [
                    (t["duration_minutes"] + self.intra_buffer) * var
                    for (t, var) in tasks_in_block
                ]
                model.Add(
                    fixed_overhead * y[b_id] + sum(task_terms) <= capacity * y[b_id]
                )

        # Constraint 4: Maintenance Crew Exclusivity & Department Availability
        # A single crew/resource cannot be assigned to overlapping tasks
        # Group tasks by assigned/required resource
        resource_task_map = defaultdict(list)
        for task in self.tasks:
            req_res = task.get("required_resource_id")
            if req_res:
                resource_task_map[req_res].append(task)
            else:
                # Assign to primary departmental crew
                dep_res = self.get_eligible_resources_for_task(task)
                if dep_res:
                    resource_task_map[dep_res[0]["resource_id"]].append(task)

        for res_id, res_tasks in resource_task_map.items():
            # Pairwise non-overlap check across blocks
            for i in range(len(res_tasks)):
                for j in range(i + 1, len(res_tasks)):
                    t1 = res_tasks[i]
                    t2 = res_tasks[j]
                    t1_id = t1["task_id"]
                    t2_id = t2["task_id"]

                    for b1 in task_candidates[t1_id]:
                        for b2 in task_candidates[t2_id]:
                            b1_id = b1["block_id"]
                            b2_id = b2["block_id"]

                            # If different blocks overlap in time, cannot schedule both
                            if b1_id != b2_id:
                                start1 = parse_datetime(b1["start_time"])
                                end1 = parse_datetime(b1["end_time"])
                                start2 = parse_datetime(b2["start_time"])
                                end2 = parse_datetime(b2["end_time"])

                                if start1 < end2 and start2 < end1:
                                    var1 = x[t1_id][b1_id]
                                    var2 = x[t2_id][b2_id]
                                    model.Add(var1 + var2 <= 1)

            # Daily shift capacity limit for each resource (max 480 min per day)
            res_info = self.resource_map.get(res_id, {})
            max_daily_min = res_info.get("daily_capacity_minutes", 480)

            # Group blocks by day
            day_blocks = defaultdict(list)
            for b in self.blocks:
                day_key = parse_datetime(b["start_time"]).date().isoformat()
                day_blocks[day_key].append(b["block_id"])

            for day_key, b_ids in day_blocks.items():
                daily_duration_terms = []
                for t in res_tasks:
                    t_id = t["task_id"]
                    dur = t["duration_minutes"]
                    for b_id in b_ids:
                        if b_id in x[t_id]:
                            daily_duration_terms.append(dur * x[t_id][b_id])
                if daily_duration_terms:
                    model.Add(sum(daily_duration_terms) <= max_daily_min)

        # Constraint 5: Section / Track Exclusivity
        # Two maintenance blocks on the same section cannot overlap in time
        for i in range(len(self.blocks)):
            for j in range(i + 1, len(self.blocks)):
                b1 = self.blocks[i]
                b2 = self.blocks[j]
                if b1["section_id"] == b2["section_id"]:
                    s1 = parse_datetime(b1["start_time"])
                    e1 = parse_datetime(b1["end_time"])
                    s2 = parse_datetime(b2["start_time"])
                    e2 = parse_datetime(b2["end_time"])
                    if s1 < e2 and s2 < e1:
                        model.Add(y[b1["block_id"]] + y[b2["block_id"]] <= 1)

        # Constraint 6: Task Dependencies (Precedence)
        # If task B depends on task A: A must finish before B can start
        for task in self.tasks:
            dep_id = task.get("depends_on")
            if not dep_id or dep_id not in self.task_map:
                continue

            t_succ_id = task["task_id"]
            t_pred_id = dep_id

            # Successor can only be scheduled if predecessor is scheduled
            pred_vars = list(x[t_pred_id].values())
            succ_vars = list(x[t_succ_id].values())
            if pred_vars and succ_vars:
                model.Add(sum(succ_vars) <= sum(pred_vars))

            # Temporal ordering across blocks:
            # If b1.end_time > b2.start_time, t_pred cannot be in b1 if t_succ is in b2
            for b_pred in task_candidates[t_pred_id]:
                for b_succ in task_candidates[t_succ_id]:
                    b_pred_id = b_pred["block_id"]
                    b_succ_id = b_succ["block_id"]

                    pred_end = parse_datetime(b_pred["end_time"])
                    succ_start = parse_datetime(b_succ["start_time"])

                    if b_pred_id != b_succ_id and pred_end > succ_start:
                        var_pred = x[t_pred_id][b_pred_id]
                        var_succ = x[t_succ_id][b_succ_id]
                        model.Add(var_pred + var_succ <= 1)

        # -------------------------------------------------------------
        # 3. Objective Function Formulation
        # -------------------------------------------------------------
        # Net Value = Maintenance Benefit + Asset Criticality + Asset Availability
        #             + Deadline Urgency - Railway Operations Cost + Bundling Bonus
        objective_terms = []

        # A) Task Value Terms
        task_metrics_cache = {}
        for task in self.tasks:
            t_id = task["task_id"]
            task_metrics_cache[t_id] = {}

            for block in task_candidates[t_id]:
                b_id = block["block_id"]
                var = x[t_id][b_id]

                mb = get_maintenance_benefit(task, self.asset_map)
                ac = get_asset_criticality_value(task, self.asset_map)
                aa = get_asset_availability_value(task, self.asset_map)
                du = get_deadline_urgency_value(task, block)

                gross_value = mb + ac + aa + du
                task_metrics_cache[t_id][b_id] = {
                    "maintenance_benefit": mb,
                    "asset_criticality": ac,
                    "asset_availability": aa,
                    "deadline_urgency": du,
                    "gross_value": gross_value
                }

                objective_terms.append(gross_value * var)

        # B) Railway Operations Cost Terms (penalized once per activated block)
        for block in self.blocks:
            b_id = block["block_id"]
            ops_cost = self.block_ops_costs[b_id]["total_cost"]
            if ops_cost > 0:
                objective_terms.append(-ops_cost * y[b_id])

        # C) Bundling Bonus: Reward packing multiple tasks in a single block
        # Bonus = bundling_bonus * (sum(x[t, b]) - y[b])
        for block in self.blocks:
            b_id = block["block_id"]
            tasks_in_block = [
                x[t["task_id"]][b_id]
                for t in self.tasks
                if b_id in x[t["task_id"]]
            ]
            if len(tasks_in_block) > 1:
                objective_terms.append(
                    self.bundling_bonus * (sum(tasks_in_block) - y[b_id])
                )

        model.Maximize(sum(objective_terms))

        # -------------------------------------------------------------
        # 4. Solve
        # -------------------------------------------------------------
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 60.0
        solver.parameters.num_workers = 4

        status = solver.Solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(f"Solver terminated with status: {solver.StatusName(status)}")
            return {
                "status": "Infeasible",
                "schedule": [],
                "unassigned_tasks": self.tasks,
                "summary": {}
            }

        # -------------------------------------------------------------
        # 5. Extract & Structure Proper Schedule
        # -------------------------------------------------------------
        raw_scheduled_tasks = []
        for task in self.tasks:
            t_id = task["task_id"]
            for block in task_candidates[t_id]:
                b_id = block["block_id"]
                var = x[t_id][b_id]
                if solver.Value(var) == 1:
                    metrics = task_metrics_cache[t_id][b_id]
                    raw_scheduled_tasks.append({
                        "task": task,
                        "block": block,
                        "metrics": metrics
                    })

        scheduled_task_ids = {item["task"]["task_id"] for item in raw_scheduled_tasks}
        unassigned_tasks = [t for t in self.tasks if t["task_id"] not in scheduled_task_ids]

        # Group assigned tasks by block
        block_to_tasks = defaultdict(list)
        for item in raw_scheduled_tasks:
            b_id = item["block"]["block_id"]
            block_to_tasks[b_id].append(item)

        # Intra-block Chronological Sequencing
        structured_schedule = self.generate_chronological_schedule(block_to_tasks)

        # Summary KPIs
        total_benefit = sum(item["metrics"]["maintenance_benefit"] for item in raw_scheduled_tasks)
        total_criticality = sum(item["metrics"]["asset_criticality"] for item in raw_scheduled_tasks)
        total_availability = sum(item["metrics"]["asset_availability"] for item in raw_scheduled_tasks)
        total_urgency = sum(item["metrics"]["deadline_urgency"] for item in raw_scheduled_tasks)
        total_gross = sum(item["metrics"]["gross_value"] for item in raw_scheduled_tasks)

        activated_blocks_count = sum(1 for b in self.blocks if solver.Value(y[b["block_id"]]) == 1)
        total_ops_cost = sum(
            self.block_ops_costs[b["block_id"]]["total_cost"]
            for b in self.blocks
            if solver.Value(y[b["block_id"]]) == 1
        )
        total_net_value = total_gross - total_ops_cost

        summary = {
            "horizon": self.horizon,
            "tasks_scheduled": len(raw_scheduled_tasks),
            "tasks_total": len(self.tasks),
            "tasks_unassigned": len(unassigned_tasks),
            "blocks_activated": activated_blocks_count,
            "blocks_total": len(self.blocks),
            "total_maintenance_benefit": total_benefit,
            "total_asset_criticality": total_criticality,
            "total_asset_availability": total_availability,
            "total_deadline_urgency": total_urgency,
            "total_gross_value": total_gross,
            "total_operations_cost": total_ops_cost,
            "total_net_value": total_net_value,
            "objective_value": solver.ObjectiveValue(),
            "solve_time_seconds": round(solver.WallTime(), 2)
        }

        return {
            "status": "Optimal" if status == cp_model.OPTIMAL else "Feasible",
            "schedule": structured_schedule,
            "unassigned_tasks": unassigned_tasks,
            "summary": summary
        }

    def generate_chronological_schedule(self, block_to_tasks):
        """
        Creates the operator-consumable timetable grouped by Day -> Block -> Tasks
        with exact intra-window start/end timestamps and safety buffers.
        """
        days_schedule = defaultdict(list)

        for b_id, task_items in block_to_tasks.items():
            block = self.block_map[b_id]
            b_start = parse_datetime(block["start_time"])
            b_end = parse_datetime(block["end_time"])

            # Sort tasks inside block:
            # 1. Tasks that are prerequisites first
            # 2. Priority: Critical first, then High, etc.
            def task_sort_key(item):
                t = item["task"]
                # If another task in this block depends on t, t comes first
                is_prereq = any(
                    other["task"].get("depends_on") == t["task_id"]
                    for other in task_items
                )
                priority_weight = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}.get(t.get("priority"), 4)
                return (0 if is_prereq else 1, priority_weight)

            sorted_items = sorted(task_items, key=task_sort_key)

            # Intra-block timeline layout
            # 1. Setup Phase
            setup_start = b_start
            setup_end = setup_start + timedelta(minutes=self.setup_buffer)

            # 2. Sequential Task Executions with Intra-Buffers
            current_time = setup_end
            scheduled_activities = []

            for idx, item in enumerate(sorted_items):
                t = item["task"]
                dur = t["duration_minutes"]

                t_start = current_time
                t_end = t_start + timedelta(minutes=dur)

                # Determine assigned crew
                req_res_id = t.get("required_resource_id")
                crew_info = self.resource_map.get(req_res_id) if req_res_id else None
                if not crew_info:
                    el = self.get_eligible_resources_for_task(t)
                    crew_info = el[0] if el else {"resource_id": "RES_GENERIC", "name": "General Duty Crew"}

                # Attribute share of operations cost for transparency
                ops_cost_share = round(
                    self.block_ops_costs[b_id]["total_cost"] / len(sorted_items), 1
                )
                net_val = item["metrics"]["gross_value"] - ops_cost_share

                activity_entry = {
                    "task_id": t["task_id"],
                    "task_type": t.get("task_type", "Maintenance"),
                    "description": t.get("description", ""),
                    "asset_id": t["asset_id"],
                    "asset_code": self.asset_map.get(t["asset_id"], {}).get("asset_code", "N/A"),
                    "asset_location_km": self.asset_map.get(t["asset_id"], {}).get("location_km", 0.0),
                    "department_id": t.get("department_id"),
                    "department_name": self.department_map.get(t.get("department_id"), {}).get("name", "Engineering"),
                    "crew_id": crew_info["resource_id"],
                    "crew_name": crew_info["name"],
                    "priority": t.get("priority", "Medium"),
                    "criticality": self.asset_map.get(t["asset_id"], {}).get("criticality", "Medium"),
                    "status": self.asset_map.get(t["asset_id"], {}).get("status", "Operational"),
                    "scheduled_start": t_start.strftime("%H:%M"),
                    "scheduled_end": t_end.strftime("%H:%M"),
                    "scheduled_start_iso": t_start.isoformat(),
                    "scheduled_end_iso": t_end.isoformat(),
                    "duration_minutes": dur,
                    "metrics": {
                        "maintenance_benefit": item["metrics"]["maintenance_benefit"],
                        "asset_criticality": item["metrics"]["asset_criticality"],
                        "asset_availability": item["metrics"]["asset_availability"],
                        "deadline_urgency": item["metrics"]["deadline_urgency"],
                        "gross_value": item["metrics"]["gross_value"],
                        "allocated_ops_cost": ops_cost_share,
                        "net_value": net_val
                    }
                }
                scheduled_activities.append(activity_entry)

                # Move current_time
                if idx < len(sorted_items) - 1:
                    current_time = t_end + timedelta(minutes=self.intra_buffer)
                else:
                    current_time = t_end

            # 3. Teardown Phase
            teardown_start = current_time
            teardown_end = b_end

            block_ops = self.block_ops_costs[b_id]
            used_maintenance_min = sum(a["duration_minutes"] for a in scheduled_activities)
            buffer_min = self.setup_buffer + (len(scheduled_activities) - 1) * self.intra_buffer
            total_utilized_min = (
                used_maintenance_min
                + self.setup_buffer
                + (len(scheduled_activities) - 1) * self.intra_buffer
                + int((teardown_end - teardown_start).total_seconds() / 60)
            )

            block_entry = {
                "block_id": b_id,
                "section_id": block["section_id"],
                "start_time": block["start_time"],
                "end_time": block["end_time"],
                "window_display": f"{b_start.strftime('%H:%M')}–{b_end.strftime('%H:%M')}",
                "duration_minutes": block["duration_minutes"],
                "window_type": block.get("window_type", "Standard Corridor"),
                "setup_phase": {
                    "start": setup_start.strftime("%H:%M"),
                    "end": setup_end.strftime("%H:%M"),
                    "duration_minutes": self.setup_buffer,
                    "description": "OHE Isolation & Track Clamping / Line Possession Memo"
                },
                "activities": scheduled_activities,
                "teardown_phase": {
                    "start": teardown_start.strftime("%H:%M"),
                    "end": teardown_end.strftime("%H:%M"),
                    "duration_minutes": max(0, int((teardown_end - teardown_start).total_seconds() / 60)),
                    "description": "Track Clearance Inspection & OHE Re-energization Memo"
                },
                "operations_cost": block_ops["total_cost"],
                "affected_trains": block_ops["affected_trains"],
                "maintenance_time_used": used_maintenance_min,
                "utilization_pct": round((used_maintenance_min / block["duration_minutes"]) * 100, 1)
            }

            day_key = b_start.strftime("%A, %Y-%m-%d")
            days_schedule[day_key].append(block_entry)

        # Sort blocks within each day chronologically
        for day in days_schedule:
            days_schedule[day].sort(key=lambda b: b["start_time"])

        return dict(days_schedule)


# -------------------------------------------------------------
# OPERATOR-CONSUMABLE PRINT FORMATTER
# -------------------------------------------------------------

def print_operator_schedule(result):
    """
    Renders the schedule in the exact human/operator-readable timetable format
    matching Indian Railways operational practice.
    """
    summary = result.get("summary", {})
    schedule = result.get("schedule", {})
    unassigned = result.get("unassigned_tasks", [])

    print("\n" + "=" * 90)
    print("                    RAILWAY MAINTENANCE MASTER TIMETABLE")
    print("=" * 90)
    print(f"PLANNING HORIZON: {summary.get('horizon', 'N/A').upper()} | STATUS: {result.get('status')}")
    print(f"SOLVE TIME: {summary.get('solve_time_seconds', 0)}s | CP-SAT OBJECTIVE NET VALUE: {summary.get('total_net_value', 0):+d} pts")
    print(f"TASKS SCHEDULED: {summary.get('tasks_scheduled')}/{summary.get('tasks_total')} | BLOCKS ACTIVATED: {summary.get('blocks_activated')}/{summary.get('blocks_total')}")
    print("=" * 90)

    if not schedule:
        print("\nNo maintenance blocks scheduled.")
        return

    for day_str, blocks in schedule.items():
        print(f"\n{'#' * 90}")
        print(f"  {day_str.upper()}")
        print(f"{'#' * 90}")

        for b in blocks:
            ops_info = "White Window (Ops Cost: 10)" if not b["affected_trains"] else f"Disrupts {len(b['affected_trains'])} Trains (Ops Cost: {b['operations_cost']})"
            print(f"\n  --------------------------------------------------------------------------------------")
            print(f"  WINDOW: {b['window_display']} ({b['duration_minutes']} min) | Section: {b['section_id']} | Block: {b['block_id']}")
            print(f"  Type: {b['window_type']} | Traffic Impact: {ops_info}")
            print(f"  --------------------------------------------------------------------------------------")

            # Setup Phase
            sp = b["setup_phase"]
            print(f"    [{sp['start']}–{sp['end']}] Safety/Setup Buffer ({sp['duration_minutes']} min): {sp['description']}")

            # Activities
            for idx, act in enumerate(b["activities"]):
                m = act["metrics"]
                print(f"\n    {act['scheduled_start']}–{act['scheduled_end']}")
                print(f"    Task:       {act['task_id']} - {act['task_type']}")
                print(f"    Asset:      {act['asset_id']} ({act['asset_code']} @ km {act['asset_location_km']})")
                print(f"    Department: {act['department_name']} ({act['department_id']})")
                print(f"    Crew:       {act['crew_id']} ({act['crew_name']})")
                print(f"    Priority:   {act['priority']} | Criticality: {act['criticality']} | Condition: {act['status']}")
                print(
                    f"    Net Value:  {m['net_value']:+.1f} pts  "
                    f"[Benefit: +{m['maintenance_benefit']} | "
                    f"Criticality: +{m['asset_criticality']} | "
                    f"Avail: +{m['asset_availability']} | "
                    f"Urgency: +{m['deadline_urgency']} | "
                    f"Ops Share: -{m['allocated_ops_cost']}]"
                )

                if idx < len(b["activities"]) - 1:
                    print(f"    [{act['scheduled_end']}–{b['activities'][idx+1]['scheduled_start']}] [Inter-task Safety Buffer: 5 min]")

            # Teardown Phase
            tp = b["teardown_phase"]
            print(f"\n    [{tp['start']}–{tp['end']}] Safety/Teardown Buffer ({tp['duration_minutes']} min): {tp['description']}")
            print(f"    >>> Utilization: {b['maintenance_time_used']}/{b['duration_minutes']} min ({b['utilization_pct']}%) | Tasks Bundled: {len(b['activities'])}")

    # Unassigned Tasks Section
    if unassigned:
        print(f"\n{'=' * 90}")
        print(f"UNASSIGNED / DEFERRED TASKS ({len(unassigned)})")
        print("-" * 90)
        for t in unassigned:
            print(
                f"  - {t['task_id']}: {t.get('task_type')} on {t['asset_id']} "
                f"| Priority: {t.get('priority')} | Deadline: {t.get('deadline')} "
                f"| Required: {t.get('required_resource_id', 'Any')}"
            )

    # Executive KPI Summary
    print(f"\n{'=' * 90}")
    print("                    EXECUTIVE OPTIMIZATION KPI REPORT")
    print("=" * 90)
    print(f"  Total Maintenance Benefit Generated:    +{summary.get('total_maintenance_benefit', 0)} pts")
    print(f"  Asset Criticality Priority Factor:      +{summary.get('total_asset_criticality', 0)} pts")
    print(f"  Asset Availability Restoration Value:   +{summary.get('total_asset_availability', 0)} pts")
    print(f"  Deadline Urgency Schedule Factor:       +{summary.get('total_deadline_urgency', 0)} pts")
    print(f"  Gross Schedule Maintenance Value:       +{summary.get('total_gross_value', 0)} pts")
    print(f"  Railway Operations Disruption Cost:     -{summary.get('total_operations_cost', 0)} pts")
    print(f"  -------------------------------------------------------------")
    print(f"  FINAL NET SCHEDULE VALUE:               +{summary.get('total_net_value', 0)} pts")
    print("=" * 90 + "\n")


def optimize_schedule(tasks=None, horizon="weekly", output_file="optimized_schedule.json"):
    """
    Main function to run optimization, print operator timetable, and export JSON.
    """
    optimizer = RailwayOptimizer(horizon=horizon, tasks=tasks)
    result = optimizer.optimize()

    print_operator_schedule(result)

    # Save to JSON
    output_path = DATA_DIR / output_file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Optimized schedule exported to: {output_path}")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Railway Maintenance Schedule Optimizer (OptRail-AI)")
    parser.add_argument(
        "--horizon",
        type=str,
        default="weekly",
        choices=["daily", "weekly", "monthly"],
        help="Planning horizon (daily = 1 day, weekly = 7 days, monthly = 30 days)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="optimized_schedule.json",
        help="Output filename for schedule JSON"
    )
    args = parser.parse_args()

    optimize_schedule(horizon=args.horizon, output_file=args.output)