import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from optimizer import RailwayOptimizer, optimize_schedule
from dataset_manager import RailwayDatasetManager
from scenario_engine import ScenarioEngine
from candidate_scorer import parse_datetime
from railway_operations_cost import calculate_operations_cost

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

app = FastAPI(
    title="OptRail-AI Railway Maintenance Scheduling API",
    description="Intelligent AI-powered railway maintenance scheduling and what-if analysis engine for Indian Railways.",
    version="2.0.0"
)

# Enable CORS for all frontends (React / Next.js / Vite / Vue / Mobile)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------
# GLOBAL IN-MEMORY CACHE
# -------------------------------------------------------------
class State:
    active_horizon: str = "weekly"
    dataset_manager: RailwayDatasetManager = RailwayDatasetManager()
    active_dataset: Dict[str, Any] = {}
    latest_schedule_result: Dict[str, Any] = {}
    scenario_engine: ScenarioEngine = ScenarioEngine(horizon="weekly")

state = State()


def initialize_state(horizon="weekly"):
    state.active_horizon = horizon
    state.dataset_manager = RailwayDatasetManager()
    state.active_dataset = state.dataset_manager.build_dataset(horizon)
    state.scenario_engine = ScenarioEngine(horizon=horizon)

    # Pre-run baseline optimization
    optimizer = RailwayOptimizer(
        horizon=horizon,
        tasks=state.active_dataset["maintenance_tasks"],
        blocks=state.active_dataset["block_windows"],
        resources=state.active_dataset["resources"],
        assets=state.active_dataset["assets"],
        departments=state.active_dataset["departments"],
        train_movements=state.active_dataset["train_movements"],
        trains=state.active_dataset["trains"]
    )
    state.latest_schedule_result = optimizer.optimize()


# Initialize baseline state at startup
initialize_state("weekly")


@app.on_event("startup")
def startup_event():
    if not state.latest_schedule_result:
        initialize_state("weekly")


# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
class OptimizeRequest(BaseModel):
    horizon: str = Field(default="weekly", description="Planning horizon: 'daily', 'weekly', or 'monthly'")
    bundling_bonus: Optional[int] = Field(default=15, description="Incentive points for bundling multiple tasks in one window")
    setup_buffer: Optional[int] = Field(default=10, description="Setup safety buffer in minutes")
    teardown_buffer: Optional[int] = Field(default=10, description="Teardown safety buffer in minutes")


class ScenarioRequest(BaseModel):
    scenario_id: str = Field(default="B", description="Scenario ID: 'A' (Normal), 'B' (+20% Traffic), 'C' (Crew Outage), 'D' (Asset Failure), 'E' (Extra Windows)")
    horizon: Optional[str] = Field(default="weekly", description="Planning horizon: 'daily', 'weekly', or 'monthly'")


# -------------------------------------------------------------
# 1. CORE ENDPOINTS
# -------------------------------------------------------------

@app.get("/")
def get_root():
    """
    Health check and system status.
    """
    return {
        "system": "OptRail-AI Maintenance Scheduling Engine",
        "status": "Online",
        "version": "2.0.0",
        "active_horizon": state.active_horizon,
        "kpis": {
            "tasks_scheduled": state.latest_schedule_result.get("summary", {}).get("tasks_scheduled", 0),
            "total_net_value": state.latest_schedule_result.get("summary", {}).get("total_net_value", 0),
            "operations_cost": state.latest_schedule_result.get("summary", {}).get("total_operations_cost", 0),
            "solve_time_sec": state.latest_schedule_result.get("summary", {}).get("solve_time_seconds", 0)
        },
        "endpoints": {
            "optimize": "POST /optimize",
            "schedule": "GET /schedule",
            "blocks": "GET /blocks",
            "assets": "GET /assets",
            "tasks": "GET /tasks",
            "conflicts": "GET /conflicts",
            "scenario": "POST /scenario",
            "scenarios_list": "GET /scenarios",
            "resources": "GET /resources",
            "kpi": "GET /kpi"
        }
    }


@app.post("/optimize")
def post_optimize(req: OptimizeRequest):
    """
    Triggers the CP-SAT optimization engine for the requested horizon.
    """
    if req.horizon.lower() not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Invalid horizon. Must be 'daily', 'weekly', or 'monthly'.")

    initialize_state(req.horizon.lower())

    optimizer = RailwayOptimizer(
        horizon=req.horizon.lower(),
        tasks=state.active_dataset["maintenance_tasks"],
        blocks=state.active_dataset["block_windows"],
        resources=state.active_dataset["resources"],
        assets=state.active_dataset["assets"],
        departments=state.active_dataset["departments"],
        train_movements=state.active_dataset["train_movements"],
        trains=state.active_dataset["trains"],
        setup_buffer=req.setup_buffer,
        teardown_buffer=req.teardown_buffer,
        bundling_bonus=req.bundling_bonus
    )

    result = optimizer.optimize()
    state.latest_schedule_result = result

    # Save to disk as well
    output_path = DATA_DIR / "optimized_schedule.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return {
        "status": result["status"],
        "horizon": req.horizon.lower(),
        "summary": result["summary"],
        "schedule": result["schedule"],
        "unassigned_tasks": result["unassigned_tasks"]
    }


@app.get("/schedule")
def get_schedule(
    day: Optional[str] = Query(None, description="Filter by day name or date (e.g. 'Monday', '2026-09-28')"),
    section_id: Optional[str] = Query(None, description="Filter by section ID (e.g. 'SEC001')"),
    department_id: Optional[str] = Query(None, description="Filter by department ID (e.g. 'DEP001')")
):
    """
    Retrieves the current optimized maintenance schedule with optional filtering.
    """
    if not state.latest_schedule_result or "schedule" not in state.latest_schedule_result:
        raise HTTPException(status_code=404, detail="No schedule generated yet. Call POST /optimize first.")

    raw_schedule = state.latest_schedule_result["schedule"]
    filtered = {}

    for day_key, blocks in raw_schedule.items():
        if day and day.lower() not in day_key.lower():
            continue

        matched_blocks = []
        for b in blocks:
            if section_id and b["section_id"] != section_id:
                continue

            # Filter activities by department
            filtered_activities = b["activities"]
            if department_id:
                filtered_activities = [
                    a for a in filtered_activities if a.get("department_id") == department_id
                ]

            if not department_id or filtered_activities:
                b_copy = dict(b)
                b_copy["activities"] = filtered_activities
                matched_blocks.append(b_copy)

        if matched_blocks:
            filtered[day_key] = matched_blocks

    return {
        "horizon": state.active_horizon,
        "summary": state.latest_schedule_result.get("summary", {}),
        "days_count": len(filtered),
        "schedule": filtered
    }


@app.get("/blocks")
def get_blocks(
    section_id: Optional[str] = Query(None, description="Filter by section ID"),
    status: Optional[str] = Query(None, description="Filter by block status (Available, Reserved, etc.)"),
    limit: int = Query(100, description="Max blocks to return")
):
    """
    Lists available and possessed block windows with train conflict and operational cost details.
    """
    blocks = state.active_dataset.get("block_windows", [])
    result = []

    for b in blocks:
        if section_id and b["section_id"] != section_id:
            continue
        if status and b.get("status") != status:
            continue

        ops_res = calculate_operations_cost(
            b,
            train_movements_data=state.active_dataset.get("train_movements"),
            train_map_data={t["train_id"]: t for t in state.active_dataset.get("trains", [])}
        )

        b_entry = dict(b)
        b_entry["operations_cost"] = ops_res["total_cost"]
        b_entry["affected_trains_count"] = len(ops_res["affected_trains"])
        b_entry["affected_trains"] = ops_res["affected_trains"]
        result.append(b_entry)

        if len(result) >= limit:
            break

    return {
        "total_blocks": len(blocks),
        "returned_count": len(result),
        "blocks": result
    }


@app.get("/assets")
def get_assets(
    section_id: Optional[str] = Query(None, description="Filter by section ID"),
    criticality: Optional[str] = Query(None, description="Filter by criticality (Critical, High, Medium)"),
    department_id: Optional[str] = Query(None, description="Filter by department ID")
):
    """
    Returns asset registry with condition scores, status, and section location.
    """
    assets = state.active_dataset.get("assets", [])
    result = []

    for a in assets:
        if section_id and a["section_id"] != section_id:
            continue
        if criticality and a.get("criticality", "").lower() != criticality.lower():
            continue
        if department_id and a.get("department_id") != department_id:
            continue
        result.append(a)

    return {
        "total_assets": len(assets),
        "returned_count": len(result),
        "assets": result
    }


@app.get("/tasks")
def get_tasks(
    priority: Optional[str] = Query(None, description="Filter by priority (Critical, High, Medium)"),
    department_id: Optional[str] = Query(None, description="Filter by department ID"),
    status: Optional[str] = Query(None, description="Filter by task status")
):
    """
    Returns the maintenance task backlog.
    """
    tasks = state.active_dataset.get("maintenance_tasks", [])
    result = []

    for t in tasks:
        if priority and t.get("priority", "").lower() != priority.lower():
            continue
        if department_id and t.get("department_id") != department_id:
            continue
        if status and t.get("status", "").lower() != status.lower():
            continue
        result.append(t)

    return {
        "total_tasks": len(tasks),
        "returned_count": len(result),
        "tasks": result
    }


@app.get("/conflicts")
def get_conflicts(
    section_id: Optional[str] = Query(None, description="Filter by section ID"),
    block_id: Optional[str] = Query(None, description="Filter by block ID")
):
    """
    Analyzes all conflicting train movements against maintenance block windows
    and computes operations disruption costs.
    """
    blocks = state.active_dataset.get("block_windows", [])
    trains_map = {t["train_id"]: t for t in state.active_dataset.get("trains", [])}
    movements = state.active_dataset.get("train_movements", [])

    conflicts_report = []
    total_network_disruption_cost = 0

    for b in blocks:
        if section_id and b["section_id"] != section_id:
            continue
        if block_id and b["block_id"] != block_id:
            continue

        res = calculate_operations_cost(
            b,
            train_movements_data=movements,
            train_map_data=trains_map
        )

        if res["affected_trains"]:
            total_network_disruption_cost += res["train_disruption_cost"]
            conflicts_report.append({
                "block_id": b["block_id"],
                "section_id": b["section_id"],
                "start_time": b["start_time"],
                "end_time": b["end_time"],
                "duration_minutes": b["duration_minutes"],
                "train_disruption_cost": res["train_disruption_cost"],
                "total_operations_cost": res["total_cost"],
                "affected_trains": res["affected_trains"]
            })

    return {
        "conflicting_blocks_count": len(conflicts_report),
        "total_disruption_cost": total_network_disruption_cost,
        "conflicts": conflicts_report
    }


@app.get("/scenarios")
def get_scenarios():
    """
    Lists all available What-If scenarios and their descriptions.
    """
    meta = state.scenario_engine.get_scenario_metadata()
    return {
        "available_scenarios": [
            {"scenario_id": k, **v}
            for k, v in meta.items()
        ]
    }


@app.post("/scenario")
def post_scenario(req: ScenarioRequest):
    """
    Runs a What-If scenario (A, B, C, D, E) and returns the impact analysis differential
    against Baseline (Scenario A).
    """
    scen_id = req.scenario_id.upper()
    if scen_id not in ("A", "B", "C", "D", "E"):
        raise HTTPException(
            status_code=400,
            detail="Invalid scenario_id. Must be 'A' (Normal), 'B' (+20% Traffic), 'C' (Crew Outage), 'D' (Asset Failure), or 'E' (Extra Windows)."
        )

    engine = ScenarioEngine(horizon=req.horizon.lower())
    diff = engine.compare_scenario_with_baseline(scen_id)

    return diff


@app.get("/resources")
def get_resources(department_id: Optional[str] = Query(None, description="Filter by department")):
    """
    Lists maintenance crews, machines, and their shift capacities.
    """
    resources = state.active_dataset.get("resources", [])
    if department_id:
        resources = [r for r in resources if r.get("department_id") == department_id]

    return {
        "total_resources": len(resources),
        "resources": resources
    }


@app.get("/kpi")
def get_kpi():
    """
    Returns executive optimization KPIs for dashboard visualization.
    """
    summary = state.latest_schedule_result.get("summary", {})
    return {
        "status": state.latest_schedule_result.get("status", "N/A"),
        "horizon": state.active_horizon,
        "kpis": summary
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting OptRail-AI FastAPI Server on http://localhost:8000 ...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
