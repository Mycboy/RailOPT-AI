import sys
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_fastapi_endpoints():
    print("=" * 80)
    print("               TESTING FASTA-PI BACKEND ENDPOINTS")
    print("=" * 80)

    # 1. Root Health Check
    res = client.get("/")
    assert res.status_code == 200, f"Root failed: {res.text}"
    data = res.json()
    print(f"[PASS] GET / -> Status: {data['status']}, Version: {data['version']}")

    # 2. GET /kpi
    res = client.get("/kpi")
    assert res.status_code == 200, f"KPI failed: {res.text}"
    kpis = res.json()["kpis"]
    print(f"[PASS] GET /kpi -> Scheduled: {kpis['tasks_scheduled']}/{kpis['tasks_total']}, Net Value: {kpis['total_net_value']} pts")

    # 3. GET /schedule
    res = client.get("/schedule")
    assert res.status_code == 200, f"Schedule failed: {res.text}"
    sched = res.json()
    print(f"[PASS] GET /schedule -> Returned {sched['days_count']} days of scheduled blocks")

    # 4. GET /blocks
    res = client.get("/blocks?section_id=SEC001")
    assert res.status_code == 200, f"Blocks failed: {res.text}"
    blocks = res.json()
    print(f"[PASS] GET /blocks?section_id=SEC001 -> Returned {blocks['returned_count']} blocks on SEC001")

    # 5. GET /assets
    res = client.get("/assets?criticality=Critical")
    assert res.status_code == 200, f"Assets failed: {res.text}"
    assets = res.json()
    print(f"[PASS] GET /assets?criticality=Critical -> Returned {assets['returned_count']} critical assets")

    # 6. GET /tasks
    res = client.get("/tasks?priority=Critical")
    assert res.status_code == 200, f"Tasks failed: {res.text}"
    tasks = res.json()
    print(f"[PASS] GET /tasks?priority=Critical -> Returned {tasks['returned_count']} critical tasks")

    # 7. GET /conflicts
    res = client.get("/conflicts")
    assert res.status_code == 200, f"Conflicts failed: {res.text}"
    conflicts = res.json()
    print(f"[PASS] GET /conflicts -> Detected {conflicts['conflicting_blocks_count']} conflicting windows, Total cost: {conflicts['total_disruption_cost']}")

    # 8. GET /resources
    res = client.get("/resources?department_id=DEP001")
    assert res.status_code == 200, f"Resources failed: {res.text}"
    resources = res.json()
    print(f"[PASS] GET /resources?department_id=DEP001 -> Returned {len(resources['resources'])} Engineering crews/machines")

    # 9. GET /scenarios
    res = client.get("/scenarios")
    assert res.status_code == 200, f"Scenarios failed: {res.text}"
    scenarios = res.json()["available_scenarios"]
    print(f"[PASS] GET /scenarios -> Listed {len(scenarios)} what-if scenarios (A, B, C, D, E)")

    # 10. POST /scenario (Testing Scenario D: Critical Asset Failure)
    res = client.post("/scenario", json={"scenario_id": "D", "horizon": "weekly"})
    assert res.status_code == 200, f"Scenario D failed: {res.text}"
    scen_d = res.json()
    print(f"[PASS] POST /scenario (Scenario D: Critical Asset Failure) ->")
    print(f"       Delta Net Value: {scen_d['delta']['net_value']:+d} pts | New Tasks: {len(scen_d['schedule_changes'])}")

    # 11. POST /scenario (Testing Scenario B: +20% Traffic)
    res = client.post("/scenario", json={"scenario_id": "B", "horizon": "weekly"})
    assert res.status_code == 200, f"Scenario B failed: {res.text}"
    scen_b = res.json()
    print(f"[PASS] POST /scenario (Scenario B: +20% Traffic) ->")
    print(f"       Rescheduled Tasks: {len(scen_b['schedule_changes'])} | Delta Ops Cost: {scen_b['delta']['operations_cost']:+d} pts")

    # 12. POST /optimize (Testing re-optimization on Daily horizon)
    res = client.post("/optimize", json={"horizon": "daily", "bundling_bonus": 20})
    assert res.status_code == 200, f"Optimize daily failed: {res.text}"
    opt_data = res.json()
    print(f"[PASS] POST /optimize (Daily horizon) -> Status: {opt_data['status']}, Scheduled: {opt_data['summary']['tasks_scheduled']}/{opt_data['summary']['tasks_total']}")

    print("\n" + "=" * 80)
    print("      ALL 12 FASTAPI ENDPOINT TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 80 + "\n")
    return True

if __name__ == "__main__":
    success = test_fastapi_endpoints()
    sys.exit(0 if success else 1)
