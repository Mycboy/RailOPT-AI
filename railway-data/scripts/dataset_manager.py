import json
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BENCHMARK_DIR = DATA_DIR / "benchmark"


def load_json(filename, directory=DATA_DIR):
    file_path = directory / filename
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data, filename, directory=BENCHMARK_DIR):
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / filename
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


class RailwayDatasetManager:
    """
    Manages and generates consistent, realistic railway datasets for:
      - Daily (1 day, 24 hours)
      - Weekly (7 days, 168 hours)
      - Monthly (30 days, 720 hours)
    
    Includes recurring train movements, cyclic maintenance blocks,
    department-specific crew rosters, task dependencies, and recurring inspection schedules.
    """

    def __init__(self, start_date_str="2026-09-28T00:00:00"):
        self.start_date = datetime.fromisoformat(start_date_str)
        self.base_assets = load_json("assets.json")
        self.base_sections = load_json("sections.json")
        self.base_stations = load_json("stations.json")
        self.base_departments = load_json("departments.json")
        self.base_trains = load_json("trains.json")

    def get_resources(self):
        """
        Returns full multi-crew department roster for Engineering, Traction, and S&T.
        """
        return [
            # Engineering (DEP001)
            {
                "resource_id": "RES001",
                "name": "Engineering Team 1 (P-Way)",
                "resource_type": "Maintenance Team",
                "department_id": "DEP001",
                "capacity": 1,
                "status": "Available",
                "daily_capacity_minutes": 480
            },
            {
                "resource_id": "RES002",
                "name": "Engineering Team 2 (P-Way)",
                "resource_type": "Maintenance Team",
                "department_id": "DEP001",
                "capacity": 1,
                "status": "Available",
                "daily_capacity_minutes": 480
            },
            {
                "resource_id": "RES005",
                "name": "Track Tamping Machine 01",
                "resource_type": "Machine",
                "department_id": "DEP001",
                "capacity": 1,
                "status": "Available",
                "daily_capacity_minutes": 360
            },
            {
                "resource_id": "RES006",
                "name": "Rail Welding Unit 01",
                "resource_type": "Machine",
                "department_id": "DEP001",
                "capacity": 1,
                "status": "Available",
                "daily_capacity_minutes": 360
            },
            # Traction (DEP002)
            {
                "resource_id": "RES003",
                "name": "Traction Team 1 (OHE)",
                "resource_type": "Maintenance Team",
                "department_id": "DEP002",
                "capacity": 1,
                "status": "Available",
                "daily_capacity_minutes": 480
            },
            {
                "resource_id": "RES007",
                "name": "Traction Team 2 (OHE)",
                "resource_type": "Maintenance Team",
                "department_id": "DEP002",
                "capacity": 1,
                "status": "Available",
                "daily_capacity_minutes": 480
            },
            {
                "resource_id": "RES008",
                "name": "OHE Tower Wagon 01",
                "resource_type": "Machine",
                "department_id": "DEP002",
                "capacity": 1,
                "status": "Available",
                "daily_capacity_minutes": 360
            },
            # Signalling and Telecom (DEP003)
            {
                "resource_id": "RES004",
                "name": "S&T Team 1 (Signals)",
                "resource_type": "Maintenance Team",
                "department_id": "DEP003",
                "capacity": 1,
                "status": "Available",
                "daily_capacity_minutes": 480
            },
            {
                "resource_id": "RES009",
                "name": "S&T Team 2 (Interlocking)",
                "resource_type": "Maintenance Team",
                "department_id": "DEP003",
                "capacity": 1,
                "status": "Available",
                "daily_capacity_minutes": 480
            },
            {
                "resource_id": "RES010",
                "name": "S&T Telecom Testing Crew",
                "resource_type": "Maintenance Team",
                "department_id": "DEP003",
                "capacity": 1,
                "status": "Available",
                "daily_capacity_minutes": 480
            }
        ]

    def generate_block_windows(self, horizon_days):
        """
        Generates realistic maintenance block windows for each section:
          - Night Corridor Block: 01:30 to 04:30 (180m, minimal train traffic)
          - Afternoon Shadow Window: 11:30 to 13:30 (120m, off-peak midday)
          - Late Afternoon Window: 16:30 to 18:30 (120m, on alternating sections)
        """
        blocks = []
        block_id_counter = 1

        sections = ["SEC001", "SEC002", "SEC003", "SEC004"]

        for day in range(horizon_days):
            day_date = (self.start_date + timedelta(days=day)).date()

            for sec_idx, section_id in enumerate(sections):
                # 1. Night Corridor Window (Prime track possession slot)
                # Staggered slightly per section to model realistic corridor possession
                night_start = datetime.combine(day_date, datetime.min.time()) + timedelta(hours=1, minutes=30 + sec_idx * 15)
                night_end = night_start + timedelta(minutes=150)
                dur = int((night_end - night_start).total_seconds() / 60)

                blocks.append({
                    "block_id": f"BLK{block_id_counter:04d}",
                    "section_id": section_id,
                    "start_time": night_start.isoformat(),
                    "end_time": night_end.isoformat(),
                    "duration_minutes": dur,
                    "status": "Available",
                    "window_type": "Night Corridor (White Window)"
                })
                block_id_counter += 1

                # 2. Midday Shadow Window (Between morning and evening peak traffic)
                if (day + sec_idx) % 2 == 0:  # Alternate days per section
                    mid_start = datetime.combine(day_date, datetime.min.time()) + timedelta(hours=11, minutes=30 + sec_idx * 20)
                    mid_end = mid_start + timedelta(minutes=100)
                    mid_dur = int((mid_end - mid_start).total_seconds() / 60)

                    blocks.append({
                        "block_id": f"BLK{block_id_counter:04d}",
                        "section_id": section_id,
                        "start_time": mid_start.isoformat(),
                        "end_time": mid_end.isoformat(),
                        "duration_minutes": mid_dur,
                        "status": "Available",
                        "window_type": "Midday Shadow Window"
                    })
                    block_id_counter += 1

                # 3. Afternoon Off-Peak Window
                if (day + sec_idx) % 3 == 0:
                    aft_start = datetime.combine(day_date, datetime.min.time()) + timedelta(hours=15, minutes=0 + sec_idx * 15)
                    aft_end = aft_start + timedelta(minutes=90)
                    aft_dur = int((aft_end - aft_start).total_seconds() / 60)

                    blocks.append({
                        "block_id": f"BLK{block_id_counter:04d}",
                        "section_id": section_id,
                        "start_time": aft_start.isoformat(),
                        "end_time": aft_end.isoformat(),
                        "duration_minutes": aft_dur,
                        "status": "Available",
                        "window_type": "Afternoon Off-Peak"
                    })
                    block_id_counter += 1

        return blocks

    def generate_train_movements(self, horizon_days):
        """
        Generates recurring daily train movements based on standard timetable.
        """
        movements = []
        mov_id_counter = 1

        # Timetable templates for each day: (train_id, section, entry_hour, entry_min, transit_min, dir)
        daily_timetable = [
            # Morning Express (TR001)
            ("TR001", "SEC001", 8, 30, 30, "UP"),
            ("TR001", "SEC002", 9, 2, 30, "UP"),
            ("TR001", "SEC003", 9, 34, 30, "UP"),
            ("TR001", "SEC004", 10, 6, 30, "UP"),

            # Capital Express (TR002)
            ("TR002", "SEC001", 9, 45, 35, "UP"),
            ("TR002", "SEC002", 10, 22, 35, "UP"),

            # Western Express (TR003)
            ("TR003", "SEC004", 10, 15, 35, "DOWN"),
            ("TR003", "SEC003", 10, 52, 35, "DOWN"),
            ("TR003", "SEC002", 11, 30, 35, "DOWN"),

            # Intercity Passenger (TR004)
            ("TR004", "SEC002", 12, 0, 35, "UP"),
            ("TR004", "SEC003", 12, 40, 35, "UP"),

            # Regional Express (TR005)
            ("TR005", "SEC003", 13, 0, 30, "UP"),
            ("TR005", "SEC004", 13, 35, 30, "UP"),

            # Superfast Express (TR006) - High Priority evening train
            ("TR006", "SEC001", 17, 30, 25, "UP"),
            ("TR006", "SEC002", 17, 58, 25, "UP"),
            ("TR006", "SEC003", 18, 25, 25, "UP"),
            ("TR006", "SEC004", 18, 52, 25, "UP"),

            # Local Passenger (TR007)
            ("TR007", "SEC003", 15, 0, 40, "DOWN"),
            ("TR007", "SEC002", 15, 45, 40, "DOWN"),

            # Regional Passenger (TR008)
            ("TR008", "SEC004", 16, 0, 40, "UP"),
            ("TR008", "SEC003", 16, 45, 40, "UP"),
        ]

        for day in range(horizon_days):
            day_date = (self.start_date + timedelta(days=day)).date()

            for (tr_id, sec_id, h, m, dur, direction) in daily_timetable:
                entry = datetime.combine(day_date, datetime.min.time()) + timedelta(hours=h, minutes=m)
                exit_t = entry + timedelta(minutes=dur)

                movements.append({
                    "movement_id": f"MOV{mov_id_counter:04d}",
                    "train_id": tr_id,
                    "section_id": sec_id,
                    "entry_time": entry.isoformat(),
                    "exit_time": exit_t.isoformat(),
                    "direction": direction
                })
                mov_id_counter += 1

        return movements

    def generate_maintenance_tasks(self, horizon_days):
        """
        Generates realistic task backlog for the specified horizon:
          - Immediate Corrective / Urgent defects (deadlines day 1-2)
          - Weekly Cyclic Inspections (deadlines days 3-7, recurring interval 7)
          - Fortnightly & Monthly Overhauls (deadlines days 10-30, recurring interval 14 or 30)
          - Task dependencies (e.g. Ultrasonic inspection precedes track repair)
        """
        tasks = []
        task_id_counter = 1

        # 1. Day 1 & Day 2 Urgent Corrective Maintenance
        urgent_tasks = [
            {
                "task_id": f"MT{task_id_counter:03d}",
                "asset_id": "AST005",  # Critical Track on SEC002
                "department_id": "DEP001",
                "task_type": "Track Emergency Repair",
                "priority": "Critical",
                "duration_minutes": 90,
                "deadline": (self.start_date + timedelta(days=1, hours=14)).isoformat(),
                "required_resource_id": "RES001",
                "status": "Pending",
                "depends_on": None,
                "recurring_interval_days": None,
                "description": "Rail surface weld defect rectification at km 31.5"
            },
            {
                "task_id": f"MT{task_id_counter+1:03d}",
                "asset_id": "AST003",  # High OHE on SEC001
                "department_id": "DEP002",
                "task_type": "OHE Contact Wire Adjustment",
                "priority": "High",
                "duration_minutes": 60,
                "deadline": (self.start_date + timedelta(days=1, hours=18)).isoformat(),
                "required_resource_id": "RES003",
                "status": "Pending",
                "depends_on": None,
                "recurring_interval_days": None,
                "description": "Dropper slack and contact wire height re-profiling at km 12.4"
            },
            {
                "task_id": f"MT{task_id_counter+2:03d}",
                "asset_id": "AST004",  # High Signal on SEC001
                "department_id": "DEP003",
                "task_type": "Signal Point Machine Overhaul",
                "priority": "High",
                "duration_minutes": 45,
                "deadline": (self.start_date + timedelta(days=1, hours=20)).isoformat(),
                "required_resource_id": "RES004",
                "status": "Pending",
                "depends_on": None,
                "recurring_interval_days": None,
                "description": "Switch point motor obstacle test and lubrication at km 20.1"
            },
            {
                "task_id": f"MT{task_id_counter+3:03d}",
                "asset_id": "AST001",  # Track SEC001
                "department_id": "DEP001",
                "task_type": "Track Joint Inspection",
                "priority": "High",
                "duration_minutes": 50,
                "deadline": (self.start_date + timedelta(days=2, hours=4)).isoformat(),
                "required_resource_id": "RES002",
                "status": "Pending",
                "depends_on": None,
                "recurring_interval_days": 7,
                "description": "Fishplate bolt tightening and visual clearance at km 8.5"
            }
        ]
        tasks.extend(urgent_tasks)
        task_id_counter += len(urgent_tasks)

        # 2. Dependent Task Pair: USFD Rail Flaw Inspection -> Subsequent Repair
        insp_task_id = f"MT{task_id_counter:03d}"
        rep_task_id = f"MT{task_id_counter+1:03d}"

        tasks.append({
            "task_id": insp_task_id,
            "asset_id": "AST008",  # High Track SEC003
            "department_id": "DEP001",
            "task_type": "USFD Ultrasonic Rail Inspection",
            "priority": "High",
            "duration_minutes": 60,
            "deadline": (self.start_date + timedelta(days=min(3, horizon_days), hours=12)).isoformat(),
            "required_resource_id": "RES001",
            "status": "Pending",
            "depends_on": None,
            "recurring_interval_days": 7,
            "description": "Ultrasonic flaw detection testing of rail section at km 59.3"
        })

        tasks.append({
            "task_id": rep_task_id,
            "asset_id": "AST008",
            "department_id": "DEP001",
            "task_type": "Track Thermit Welding Repair",
            "priority": "High",
            "duration_minutes": 75,
            "deadline": (self.start_date + timedelta(days=min(4, horizon_days), hours=18)).isoformat(),
            "required_resource_id": "RES006",
            "status": "Pending",
            "depends_on": insp_task_id,  # Must follow inspection
            "recurring_interval_days": None,
            "description": "Execution of weld repair conditional on USFD inspection findings"
        })
        task_id_counter += 2

        # 3. Weekly Cyclic Tasks (Days 2 to 7)
        if horizon_days >= 3:
            weekly_cyclic = [
                {
                    "asset_id": "AST006", "dep": "DEP002", "type": "OHE Insulator Cleaning",
                    "pri": "Medium", "dur": 60, "res": "RES007", "day": 3, "recur": 7,
                    "desc": "High voltage neutral section insulator washing at km 40.2"
                },
                {
                    "asset_id": "AST007", "dep": "DEP003", "type": "Axle Counter Calibration",
                    "pri": "Medium", "dur": 45, "res": "RES004", "day": 3, "recur": 7,
                    "desc": "Digital axle counter sensor head alignment at km 47.8"
                },
                {
                    "asset_id": "AST010", "dep": "DEP003", "type": "Signal Interlocking Testing",
                    "pri": "High", "dur": 60, "res": "RES009", "day": 4, "recur": 7,
                    "desc": "Route release and interlocking relay cross-talk testing at km 73.4"
                },
                {
                    "asset_id": "AST011", "dep": "DEP001", "type": "Track Gauge & Cross-Level Check",
                    "pri": "Medium", "dur": 55, "res": "RES002", "day": 5, "recur": 7,
                    "desc": "Digital track gauge measurement along 27km stretch at km 86.2"
                },
                {
                    "asset_id": "AST012", "dep": "DEP002", "type": "OHE Catenary Wire Inspection",
                    "pri": "High", "dur": 70, "res": "RES008", "day": 5, "recur": 7,
                    "desc": "Tower wagon catenary tensioner and dropper inspection at km 96.5"
                },
                {
                    "asset_id": "AST002", "dep": "DEP001", "type": "Track Fastener Replacement",
                    "pri": "Medium", "dur": 65, "res": "RES001", "day": 6, "recur": 7,
                    "desc": "ERC clip and rubber pad replacement at km 18.2"
                },
                {
                    "asset_id": "AST009", "dep": "DEP002", "type": "OHE Isolator Switch Maintenance",
                    "pri": "Medium", "dur": 50, "res": "RES003", "day": 6, "recur": 7,
                    "desc": "Section insulator blade contact resistance test at km 66.7"
                }
            ]

            for item in weekly_cyclic:
                target_day = min(item["day"], horizon_days)
                deadline_dt = self.start_date + timedelta(days=target_day, hours=22)
                tasks.append({
                    "task_id": f"MT{task_id_counter:03d}",
                    "asset_id": item["asset_id"],
                    "department_id": item["dep"],
                    "task_type": item["type"],
                    "priority": item["pri"],
                    "duration_minutes": item["dur"],
                    "deadline": deadline_dt.isoformat(),
                    "required_resource_id": item["res"],
                    "status": "Pending",
                    "depends_on": None,
                    "recurring_interval_days": item["recur"],
                    "description": item["desc"]
                })
                task_id_counter += 1

        # 4. Monthly Heavy Cyclic Tasks (Days 8 to 30)
        if horizon_days > 7:
            num_weeks = (horizon_days - 7) // 7 + 1
            monthly_templates = [
                {
                    "asset_id": "AST005", "dep": "DEP001", "type": "Mechanized Track Tamping",
                    "pri": "Critical", "dur": 120, "res": "RES005", "week": 2, "recur": 30,
                    "desc": "Heavy track packing and alignment by tamping machine at km 31.5"
                },
                {
                    "asset_id": "AST003", "dep": "DEP002", "type": "OHE Contact Wire Renewal",
                    "pri": "High", "dur": 110, "res": "RES008", "week": 2, "recur": 30,
                    "desc": "Tower wagon assisted replacement of 500m worn contact wire at km 12.4"
                },
                {
                    "asset_id": "AST004", "dep": "DEP003", "type": "Electronic Interlocking Software Health Check",
                    "pri": "High", "dur": 75, "res": "RES009", "week": 3, "recur": 30,
                    "desc": "Solid State Interlocking diagnostics and memory dump validation at km 20.1"
                },
                {
                    "asset_id": "AST001", "dep": "DEP001", "type": "Turnout Diamond Crossing Overhaul",
                    "pri": "Critical", "dur": 105, "res": "RES005", "week": 3, "recur": 30,
                    "desc": "Tongue rail wear check and CMS crossing weld build-up at km 8.5"
                },
                {
                    "asset_id": "AST008", "dep": "DEP001", "type": "Track Deep Ballast Screening",
                    "pri": "High", "dur": 130, "res": "RES005", "week": 4, "recur": 30,
                    "desc": "Ballast cleaning machine deployment for foul ballast recovery at km 59.3"
                },
                {
                    "asset_id": "AST012", "dep": "DEP002", "type": "OHE Auto-Tensioning Device Overhaul",
                    "pri": "High", "dur": 85, "res": "RES008", "week": 4, "recur": 30,
                    "desc": "Three-pulley balance weight adjustment and stainless steel rope check at km 96.5"
                },
                {
                    "asset_id": "AST010", "dep": "DEP003", "type": "Audio Frequency Track Circuit Tuning",
                    "pri": "Medium", "dur": 55, "res": "RES010", "week": 4, "recur": 30,
                    "desc": "AFTC transmitter shunt sensitivity and receiver bonding check at km 73.4"
                }
            ]

            for item in monthly_templates:
                target_day = min(7 * item["week"] - 2, horizon_days)
                deadline_dt = self.start_date + timedelta(days=target_day, hours=20)
                tasks.append({
                    "task_id": f"MT{task_id_counter:03d}",
                    "asset_id": item["asset_id"],
                    "department_id": item["dep"],
                    "task_type": item["type"],
                    "priority": item["pri"],
                    "duration_minutes": item["dur"],
                    "deadline": deadline_dt.isoformat(),
                    "required_resource_id": item["res"],
                    "status": "Pending",
                    "depends_on": None,
                    "recurring_interval_days": item["recur"],
                    "description": item["desc"]
                })
                task_id_counter += 1

        return tasks

    def build_dataset(self, horizon="weekly"):
        """
        Builds a complete, coordinated railway dataset for the chosen horizon:
          - 'daily'   -> 1 Day (Tactical / Immediate 24h)
          - 'weekly'  -> 7 Days (Tactical possession plan)
          - 'monthly' -> 30 Days (Cyclic & heavy overhaul calendar)
        """
        horizon_map = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30
        }
        horizon_days = horizon_map.get(horizon.lower(), 7)

        blocks = self.generate_block_windows(horizon_days)
        movements = self.generate_train_movements(horizon_days)
        tasks = self.generate_maintenance_tasks(horizon_days)
        resources = self.get_resources()

        dataset = {
            "horizon": horizon.lower(),
            "horizon_days": horizon_days,
            "start_date": self.start_date.isoformat(),
            "end_date": (self.start_date + timedelta(days=horizon_days)).isoformat(),
            "sections": self.base_sections,
            "stations": self.base_stations,
            "departments": self.base_departments,
            "assets": self.base_assets,
            "trains": self.base_trains,
            "resources": resources,
            "block_windows": blocks,
            "train_movements": movements,
            "maintenance_tasks": tasks
        }

        return dataset

    def export_benchmark_datasets(self):
        """
        Pre-generates and saves benchmark datasets for daily, weekly, and monthly planning.
        """
        for horizon in ["daily", "weekly", "monthly"]:
            data = self.build_dataset(horizon)
            folder = BENCHMARK_DIR / horizon
            folder.mkdir(parents=True, exist_ok=True)

            save_json(data["block_windows"], "block_windows.json", folder)
            save_json(data["train_movements"], "train_movements.json", folder)
            save_json(data["maintenance_tasks"], "maintenance_tasks.json", folder)
            save_json(data["resources"], "resources.json", folder)
            save_json(data["assets"], "assets.json", folder)
            save_json(data["sections"], "sections.json", folder)
            save_json(data["trains"], "trains.json", folder)
            save_json(data["departments"], "departments.json", folder)
            save_json(data["stations"], "stations.json", folder)

            print(
                f"Generated {horizon.upper()} benchmark dataset: "
                f"{len(data['maintenance_tasks'])} tasks, "
                f"{len(data['block_windows'])} blocks, "
                f"{len(data['train_movements'])} train movements."
            )


if __name__ == "__main__":
    manager = RailwayDatasetManager()
    manager.export_benchmark_datasets()
