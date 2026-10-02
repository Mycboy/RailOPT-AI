import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from optimizer import RailwayOptimizer, optimize_schedule
from dataset_manager import RailwayDatasetManager
from scenario_engine import ScenarioEngine
from benchmark_engine import BenchmarkEngine
from candidate_scorer import parse_datetime
from railway_operations_cost import calculate_operations_cost
from auth import (
    LoginRequest, SwitchRoleRequest, TokenResponse,
    create_access_token, verify_password, USERS_DB,
    get_user_profile, get_current_user, require_roles, require_permission,
    RailwayRoles
)

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
    custom_submitted_tasks: List[Dict[str, Any]] = []

state = State()


def initialize_state(horizon="weekly"):
    state.active_horizon = horizon
    state.dataset_manager = RailwayDatasetManager()
    state.active_dataset = state.dataset_manager.build_dataset(horizon)
    state.scenario_engine = ScenarioEngine(horizon=horizon)

    # Re-inject user-submitted custom tasks so they survive re-optimization across horizons
    existing_ids = {t["task_id"] for t in state.active_dataset.get("maintenance_tasks", [])}
    for custom_task in state.custom_submitted_tasks:
        if custom_task["task_id"] not in existing_ids:
            state.active_dataset["maintenance_tasks"].append(custom_task)

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


class CreateTaskRequest(BaseModel):
    asset_id: str = Field(..., description="Target Asset ID e.g. AST001")
    task_type: str = Field(..., description="e.g. Ultrasonic Flaw Detection (USFD)")
    department_id: str = Field(..., description="DEP001 (P-Way), DEP002 (OHE), or DEP003 (S&T)")
    duration_minutes: int = Field(default=60, description="Duration in minutes")
    priority: int = Field(default=2, description="1=Critical, 2=High, 3=Medium")
    deadline_hours: int = Field(default=48, description="Hours until deadline")
    description: Optional[str] = "Routine maintenance block request"


# -------------------------------------------------------------
# AUTHENTICATION & RBAC ENDPOINTS
# -------------------------------------------------------------

@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest):
    """
    Authenticates railway personnel via username and password.
    Returns signed JWT access token and user role profile.
    """
    user = USERS_DB.get(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password. Please verify credentials.")
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": get_user_profile(user)
    }


@app.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """
    Returns active user profile, division, and permissions from JWT token.
    """
    return {"user": current_user}


@app.get("/auth/demo-users")
def get_demo_users():
    """
    Returns pre-configured Indian Railways personas with instantaneous demo tokens
    for one-click switching during hackathon / executive presentations.
    """
    demo_list = []
    for uname, u in USERS_DB.items():
        token = create_access_token({"sub": uname, "role": u["role"]})
        profile = get_user_profile(u)
        profile["token"] = token
        demo_list.append(profile)
    return {"demo_users": demo_list}


@app.post("/auth/switch-role", response_model=TokenResponse)
def switch_role(req: SwitchRoleRequest):
    """
    Instant role switch helper for live demonstrations.
    """
    user = USERS_DB.get(req.username)
    if not user:
        raise HTTPException(status_code=404, detail="Railway persona not found.")
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": get_user_profile(user)
    }


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
            "auth_login": "POST /auth/login",
            "auth_me": "GET /auth/me",
            "auth_demo_users": "GET /auth/demo-users",
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
def post_optimize(
    req: OptimizeRequest,
    current_user: dict = Depends(require_permission("optimize:run"))
):
    """
    Triggers the CP-SAT optimization engine for the requested horizon.
    Requires 'optimize:run' permission (Section Controller / DOM).
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
    horizon: Optional[str] = Query(None, description="Filter by horizon: 'daily', 'weekly', or 'monthly'"),
    day: Optional[str] = Query(None, description="Filter by day name or date (e.g. 'Monday', '2026-09-28')"),
    section_id: Optional[str] = Query(None, description="Filter by section ID (e.g. 'SEC001')"),
    department_id: Optional[str] = Query(None, description="Filter by department ID (e.g. 'DEP001')")
):
    """
    Retrieves the current optimized maintenance schedule with optional filtering.
    """
    target_h = horizon.lower() if horizon else state.active_horizon
    if target_h not in ("daily", "weekly", "monthly"):
        target_h = "weekly"

    if (
        target_h != state.active_horizon
        or not state.latest_schedule_result
        or "schedule" not in state.latest_schedule_result
    ):
        initialize_state(target_h)

    raw_schedule = state.latest_schedule_result.get("schedule", {})
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

    # Identify scheduled task IDs across all days
    scheduled_task_ids = set()
    for day_key, blocks in raw_schedule.items():
        for b in blocks:
            for act in b.get("activities", []):
                scheduled_task_ids.add(act.get("task_id"))

    # Collect pending / unassigned tasks awaiting possession grant
    pending_tasks = [
        t for t in state.active_dataset.get("maintenance_tasks", [])
        if t.get("task_id") not in scheduled_task_ids
    ]

    return {
        "horizon": state.active_horizon,
        "summary": state.latest_schedule_result.get("summary", {}),
        "days_count": len(filtered),
        "schedule": filtered,
        "pending_tasks": pending_tasks
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


@app.post("/tasks")
def create_task(
    req: CreateTaskRequest,
    current_user: dict = Depends(require_permission("task:create"))
):
    """
    Submits a maintenance block request into the backlog.
    Enforces departmental boundaries:
    - P-Way Engineers can only request Civil/Track maintenance (DEP001)
    - OHE Engineers can only request Electrical/Traction maintenance (DEP002)
    - Controllers can request any department maintenance
    """
    user_role = current_user.get("role")
    if user_role == RailwayRoles.PWAY_ENGINEER and req.department_id != "DEP001":
        raise HTTPException(
            status_code=403,
            detail="P-Way Engineers are restricted to Civil/Track (DEP001) maintenance requests only."
        )
    if user_role == RailwayRoles.OHE_ENGINEER and req.department_id != "DEP002":
        raise HTTPException(
            status_code=403,
            detail="OHE Engineers are restricted to Electrical/Traction (DEP002) maintenance requests only."
        )

    tasks = state.active_dataset.get("maintenance_tasks", [])
    new_id = f"MT{len(tasks) + 1:03d}"
    
    crew_role = "TRK_INSPECTION"
    res_id = "RES001"
    if req.department_id == "DEP002":
        crew_role = "OHE_LINE"
        res_id = "RES003"
    elif req.department_id == "DEP003":
        crew_role = "SIG_CIRCUIT"
        res_id = "RES005"

    prio_str = "Critical" if req.priority == 1 else ("High" if req.priority == 2 else "Medium")
    # Base date is 2026-09-28T00:00:00 (corridor timeline start)
    base_date = datetime(2026, 9, 28, 6, 0, 0)
    computed_deadline = (base_date + timedelta(hours=max(req.deadline_hours, 48))).isoformat()

    new_task = {
        "task_id": new_id,
        "asset_id": req.asset_id,
        "task_type": req.task_type,
        "department_id": req.department_id,
        "duration_minutes": req.duration_minutes,
        "priority": prio_str,
        "deadline": computed_deadline,
        "deadline_hours": req.deadline_hours,
        "required_resource_id": res_id,
        "required_crew_role": crew_role,
        "status": "Pending",
        "submitted_by": f"{current_user.get('full_name')} ({current_user.get('badge_id')})",
        "submission_time": datetime.utcnow().isoformat()
    }
    tasks.append(new_task)
    state.custom_submitted_tasks.append(new_task)
    
    return {
        "status": "Success",
        "message": f"Maintenance block request {new_id} queued for Section Controller review.",
        "task": new_task,
        "total_tasks": len(tasks)
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
def post_scenario(
    req: ScenarioRequest,
    current_user: dict = Depends(require_permission("scenario:run"))
):
    """
    Runs a What-If scenario (A, B, C, D, E) and returns the impact analysis differential
    against Baseline (Scenario A).
    Requires 'scenario:run' permission (Section Controller / DOM).
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


@app.get("/benchmark")
def get_benchmark(horizon: Optional[str] = Query(None, description="Horizon: daily, weekly, monthly")):
    """
    Executes the controlled synthetic scenario comparing the Before (Manual/Uncoordinated)
    plan against the After (CP-SAT Optimized) plan with quantifiable measurable KPIs.
    """
    h = horizon.lower() if horizon else state.active_horizon
    engine = BenchmarkEngine(horizon=h)
    results = engine.run_benchmark()
    return results


if __name__ == "__main__":
    import uvicorn
    print("Starting OptRail-AI FastAPI Server on http://localhost:8000 ...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
