from flask import Flask, render_template, request, redirect, url_for, flash, make_response
import calendar
import csv
import io
import sqlite3
from datetime import date, datetime
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DB_PATH = Path(__file__).with_name("rosterflow.db")

EMPLOYEE_SEED = [
    (1, "Aarav Sharma", "Pod A", "Nova Store", "Customer Support", "Working"),
    (2, "Priya Patel", "Pod A", "Urban Cart", "ACC", "Working"),
    (3, "Rohan Shah", "Pod B", "Glow House", "NDR", "Working"),
    (4, "Sneha Desai", "Pod B", "Nova Store", "Customer Support", "Working"),
    (5, "Ishaan Mehta", "Pod C", "Pure Living", "Retention", "Working"),
    (6, "Ananya Joshi", "Pod A", "Urban Cart", "NDR", "Working"),
    (7, "Vivaan Kulkarni", "Pod B", "Glow House", "ACC", "Working"),
    (8, "Kavya Rao", "Pod C", "Pure Living", "Customer Support", "Working"),
    (9, "Aditya Singh", "Pod A", "Nova Store", "Retention", "Working"),
    (10, "Ira Mehta", "Pod B", "Urban Cart", "Customer Support", "Working"),
    (11, "Arjun Nair", "Pod C", "Glow House", "NDR", "Working"),
    (12, "Diya Shah", "Pod A", "Pure Living", "ACC", "Working"),
    (13, "Reyansh Gupta", "Pod B", "Nova Store", "Retention", "Working"),
    (14, "Myra Iyer", "Pod C", "Urban Cart", "Customer Support", "Working"),
    (15, "Kabir Deshmukh", "Pod A", "Glow House", "NDR", "Working"),
    (16, "Sara Khan", "Pod B", "Pure Living", "ACC", "Working"),
    (17, "Atharv Patil", "Pod C", "Nova Store", "Retention", "Working"),
    (18, "Aadhya Verma", "Pod A", "Urban Cart", "Customer Support", "Working"),
    (19, "Krish Malhotra", "Pod B", "Glow House", "NDR", "Working"),
    (20, "Pari Joshi", "Pod C", "Pure Living", "ACC", "Working"),
    (21, "Dhruv Sinha", "Pod A", "Nova Store", "Retention", "Working"),
    (22, "Avni Rao", "Pod B", "Urban Cart", "Customer Support", "Working"),
    (23, "Samar Kulkarni", "Pod C", "Glow House", "NDR", "Working"),
    (24, "Tara Nair", "Pod A", "Pure Living", "ACC", "Working"),
    (25, "Yash Mehta", "Pod B", "Nova Store", "Customer Support", "Working"),
    (26, "Meera Patil", "Pod C", "Urban Cart", "Retention", "Working"),
    (27, "Dev Shah", "Pod A", "Glow House", "NDR", "Working"),
    (28, "Riya Desai", "Pod B", "Pure Living", "ACC", "Working"),
    (29, "Omkar Joshi", "Pod C", "Nova Store", "Customer Support", "Working"),
    (30, "Saanvi Gupta", "Pod A", "Urban Cart", "Retention", "Working"),
]
PROCESSES = ["Customer Support", "ACC", "NDR", "Retention"]
# Defaults are examples; adjust them to match actual client contracts.
DEFAULT_BRANDS = ["Nova Store", "Urban Cart", "Glow House", "Pure Living"]
POD_LEADS = {"Pod A": "Aarav Sharma", "Pod B": "Rohan Shah", "Pod C": "Ishaan Mehta"}
HOLIDAY_SEED = [
    ("2026-11-08", "Diwali (example date)"),
    ("2026-12-25", "Christmas"),
]

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            pod TEXT NOT NULL,
            brand TEXT NOT NULL,
            process TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Working',
            weekly_off INTEGER NOT NULL DEFAULT 6,
            pod_lead TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS leave_days (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            leave_date TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            approved INTEGER NOT NULL DEFAULT 1,
            note TEXT DEFAULT '',
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE,
            UNIQUE(employee_id, leave_date, leave_type)
        );
        CREATE TABLE IF NOT EXISTS holidays (
            holiday_date TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS process_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            process TEXT NOT NULL,
            operates_sunday INTEGER NOT NULL DEFAULT 0,
            operates_holiday INTEGER NOT NULL DEFAULT 0,
            operates_saturday INTEGER NOT NULL DEFAULT 1,
            min_staff INTEGER NOT NULL DEFAULT 1,
            UNIQUE(brand, process)
        );
        CREATE TABLE IF NOT EXISTS roster_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roster_date TEXT NOT NULL,
            employee_id INTEGER NOT NULL,
            shift TEXT NOT NULL,
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE,
            UNIQUE(roster_date, employee_id)
        );
        """)
        count = db.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        if count == 0:
            for emp in EMPLOYEE_SEED:
                eid, name, pod, brand, process, status = emp
                pod_lead = POD_LEADS.get(pod, "")
                # Distribute weekly off days Monday-Saturday, while Sundays remain rule-driven.
                weekly_off = (eid - 1) % 6
                db.execute(
                    "INSERT INTO employees(id,name,pod,brand,process,status,weekly_off,pod_lead) VALUES(?,?,?,?,?,?,?,?)",
                    (eid, name, pod, brand, process, status, weekly_off, pod_lead)
                )
        for hdate, hname in HOLIDAY_SEED:
            db.execute("INSERT OR IGNORE INTO holidays(holiday_date,name) VALUES(?,?)", (hdate, hname))
        # Create editable rules for every currently used brand/process pair.
        pairs = db.execute("SELECT DISTINCT brand, process FROM employees").fetchall()
        for pair in pairs:
            db.execute(
                "INSERT OR IGNORE INTO process_rules(brand,process,operates_sunday,operates_holiday,operates_saturday,min_staff) VALUES(?,?,?,?,?,?)",
                (pair["brand"], pair["process"], 0, 0, 1, 1)
            )

def get_employees():
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM employees ORDER BY pod, brand, name")]

def get_rules():
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM process_rules ORDER BY brand, process")]

def ensure_rule(brand, process):
    with connect() as db:
        db.execute(
            "INSERT OR IGNORE INTO process_rules(brand,process,min_staff) VALUES(?,?,1)",
            (brand, process)
        )

def parse_month(value):
    try:
        year, month = map(int, value.split("-"))
        if not 1 <= month <= 12 or not 2000 <= year <= 2100:
            raise ValueError
        return year, month
    except (ValueError, AttributeError):
        raise ValueError("Please select a valid month.")

def build_roster(year, month):
    start_day = date(year, month, 1)
    total_days = calendar.monthrange(year, month)[1]
    employees = get_employees()
    with connect() as db:
        holidays = {r["holiday_date"]: r["name"] for r in db.execute("SELECT * FROM holidays")}
        leaves = {
            (r["employee_id"], r["leave_date"]): r["leave_type"]
            for r in db.execute("SELECT * FROM leave_days WHERE approved=1")
        }
        rules = {
            (r["brand"], r["process"]): dict(r)
            for r in db.execute("SELECT * FROM process_rules")
        }

    roster = []
    conflicts = []
    for day_num in range(1, total_days + 1):
        current = date(year, month, day_num)
        key = current.isoformat()
        is_holiday = key in holidays
        for emp in employees:
            rule = rules.get((emp["brand"], emp["process"]), {
                "operates_sunday": 0, "operates_holiday": 0, "operates_saturday": 1, "min_staff": 1
            })
            leave_type = leaves.get((emp["id"], key))
            if leave_type:
                shift = "Comp-Off" if leave_type == "Comp-Off" else "On Leave"
            elif is_holiday and not rule["operates_holiday"]:
                shift = holidays[key]
            elif current.weekday() == 6 and not rule["operates_sunday"]:
                shift = "Sunday Off"
            elif current.weekday() == 5 and not rule["operates_saturday"]:
                shift = "Saturday Off"
            elif current.weekday() == emp["weekly_off"]:
                shift = "Weekly Off"
            elif emp["status"] != "Working":
                shift = emp["status"]
            else:
                shift = "Day Shift"
            roster.append({
                "date_iso": key,
                "date": current.strftime("%d %b %Y"),
                "employee_id": emp["id"],
                "employee": emp["name"],
                "pod": emp["pod"],
                "pod_lead": emp["pod_lead"],
                "brand": emp["brand"],
                "process": emp["process"],
                "shift": shift,
            })

    # Validate staffing for each configured brand/process on dates that require service.
    for day_num in range(1, total_days + 1):
        current = date(year, month, day_num)
        key = current.isoformat()
        is_holiday = key in holidays
        for rule_key, rule in rules.items():
            brand, process = rule_key
            requires_coverage = (
                (current.weekday() != 6 or rule["operates_sunday"]) and
                (current.weekday() != 5 or rule["operates_saturday"]) and
                (not is_holiday or rule["operates_holiday"])
            )
            if not requires_coverage:
                continue
            assigned = [
                r for r in roster
                if r["date_iso"] == key and r["brand"] == brand and r["process"] == process
            ]
            working = [r for r in assigned if r["shift"] == "Day Shift"]
            minimum = int(rule["min_staff"])
            if len(working) < minimum:
                conflicts.append({
                    "employee": f"{brand} — {process}",
                    "issue": f"{current.strftime('%d %b %Y')}: {len(working)} available; {minimum} required.",
                    "pod": ", ".join(sorted({r["pod"] for r in assigned})) or "Unassigned",
                    "date": key,
                    "brand": brand,
                    "process": process,
                })

    # Add a clear warning if an employee has a full-month status other than Working.
    for emp in employees:
        if emp["status"] != "Working":
            conflicts.append({
                "employee": emp["name"],
                "issue": f"Employee master status is '{emp['status']}'. Confirm availability and coverage.",
                "pod": emp["pod"],
                "date": "",
                "brand": emp["brand"],
                "process": emp["process"],
            })

    summary = {
        "working": sum(r["shift"] == "Day Shift" for r in roster),
        "weekly_off": sum(r["shift"] == "Weekly Off" for r in roster),
        "leave": sum(r["shift"] == "On Leave" for r in roster),
        "comp_off": sum(r["shift"] == "Comp-Off" for r in roster),
        "holidays": sum("Holiday" in r["shift"] for r in roster),
        "sunday_off": sum(r["shift"] == "Sunday Off" for r in roster),
        "saturday_off": sum(r["shift"] == "Saturday Off" for r in roster),
    }
    return roster, conflicts, summary

@app.route("/")
def home():
    employees = get_employees()
    brands = sorted({e["brand"] for e in employees})
    processes = sorted({e["process"] for e in employees})
    with connect() as db:
        leave_count = db.execute("SELECT COUNT(*) FROM leave_days WHERE approved=1").fetchone()[0]
        rule_count = db.execute("SELECT COUNT(*) FROM process_rules").fetchone()[0]
        today = date.today()
    return render_template(
        "index.html", employees=employees, brands=brands, processes=processes,
        leave_count=leave_count, rule_count=rule_count, today=today.isoformat(),
        pod_leads=POD_LEADS
    )

@app.route("/generate-roster", methods=["POST"])
def generate_roster():
    try:
        year, month = parse_month(request.form.get("roster_month", ""))
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("home"))
    roster, conflicts, summary = build_roster(year, month)
    # Save generated roster for later review/export.
    with connect() as db:
        db.execute("DELETE FROM roster_entries WHERE roster_date BETWEEN ? AND ?",
                   (date(year, month, 1).isoformat(), date(year, month, calendar.monthrange(year, month)[1]).isoformat()))
        db.executemany(
            "INSERT OR REPLACE INTO roster_entries(roster_date,employee_id,shift) VALUES(?,?,?)",
            [(r["date_iso"], r["employee_id"], r["shift"]) for r in roster]
        )
    return render_template(
        "roster.html", roster=roster, selected_month=date(year, month, 1).strftime("%B %Y"),
        selected_month_value=f"{year:04d}-{month:02d}", summary=summary, conflicts=conflicts
    )

@app.route("/employees/add", methods=["POST"])
def add_employee():
    name = request.form.get("name", "").strip()
    pod = request.form.get("pod", "").strip()
    brand = request.form.get("brand", "").strip()
    process = request.form.get("process", "").strip()
    weekly_off_raw = request.form.get("weekly_off", "6")
    if not all([name, pod, brand, process]):
        flash("Please fill in all employee fields.", "error")
        return redirect(url_for("home"))
    try:
        weekly_off = int(weekly_off_raw)
        if weekly_off not in range(7):
            raise ValueError
    except ValueError:
        flash("Choose a valid weekly off day.", "error")
        return redirect(url_for("home"))
    with connect() as db:
        db.execute(
            "INSERT INTO employees(name,pod,brand,process,status,weekly_off,pod_lead) VALUES(?,?,?,?,?,?,?)",
            (name, pod, brand, process, "Working", weekly_off, POD_LEADS.get(pod, "Not assigned"))
        )
    ensure_rule(brand, process)
    flash(f"Employee {name} added.", "success")
    return redirect(url_for("home"))

@app.route("/employees/<int:employee_id>/status", methods=["POST"])
def update_employee_status(employee_id):
    status = request.form.get("status", "Working")
    if status not in {"Working", "Unavailable"}:
        flash("Invalid employee status.", "error")
        return redirect(url_for("home"))
    with connect() as db:
        db.execute("UPDATE employees SET status=? WHERE id=?", (status, employee_id))
    flash("Employee status updated. Generate the roster again to recalculate coverage.", "success")
    return redirect(url_for("home"))

@app.route("/leave/add", methods=["POST"])
def add_leave():
    try:
        employee_id = int(request.form.get("employee_id", ""))
        leave_date = date.fromisoformat(request.form.get("leave_date", ""))
        leave_type = request.form.get("leave_type", "Leave")
        if leave_type not in {"Leave", "Comp-Off"}:
            raise ValueError
    except (ValueError, TypeError):
        flash("Enter a valid employee, date, and leave type.", "error")
        return redirect(url_for("home"))
    with connect() as db:
        exists = db.execute("SELECT id FROM employees WHERE id=?", (employee_id,)).fetchone()
        if not exists:
            flash("Employee not found.", "error")
            return redirect(url_for("home"))
        db.execute(
            "INSERT OR REPLACE INTO leave_days(employee_id,leave_date,leave_type,approved,note) VALUES(?,?,?,1,?)",
            (employee_id, leave_date.isoformat(), leave_type, request.form.get("note", "").strip())
        )
    flash("Date-specific leave/comp-off saved. Generate the roster again to validate coverage.", "success")
    return redirect(url_for("home"))

@app.route("/rules", methods=["POST"])
def update_rules():
    brand = request.form.get("brand", "").strip()
    process = request.form.get("process", "").strip()
    try:
        min_staff = int(request.form.get("min_staff", "1"))
        if not brand or not process or min_staff < 1 or min_staff > 100:
            raise ValueError
    except ValueError:
        flash("Enter a brand, process, and minimum staffing value between 1 and 100.", "error")
        return redirect(url_for("home"))
    sunday = 1 if request.form.get("operates_sunday") else 0
    saturday = 1 if request.form.get("operates_saturday") else 0
    holiday = 1 if request.form.get("operates_holiday") else 0
    with connect() as db:
        db.execute("""
            INSERT INTO process_rules(brand,process,operates_sunday,operates_holiday,operates_saturday,min_staff)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(brand,process) DO UPDATE SET
            operates_sunday=excluded.operates_sunday,
            operates_holiday=excluded.operates_holiday,
            operates_saturday=excluded.operates_saturday,
            min_staff=excluded.min_staff
        """, (brand, process, sunday, holiday, saturday, min_staff))
    flash(f"Working rule saved for {brand} / {process}.", "success")
    return redirect(url_for("home"))

@app.route("/holidays/add", methods=["POST"])
def add_holiday():
    try:
        holiday_date = date.fromisoformat(request.form.get("holiday_date", ""))
        name = request.form.get("holiday_name", "").strip()
        if not name:
            raise ValueError
    except ValueError:
        flash("Enter a valid holiday date and name.", "error")
        return redirect(url_for("home"))
    with connect() as db:
        db.execute("INSERT OR REPLACE INTO holidays(holiday_date,name) VALUES(?,?)",
                   (holiday_date.isoformat(), name))
    flash("Holiday saved. Regenerate the roster to apply it.", "success")
    return redirect(url_for("home"))

@app.route("/export/<month_value>.csv")
def export_roster(month_value):
    try:
        year, month = parse_month(month_value)
    except ValueError:
        return "Invalid month", 400
    roster, conflicts, summary = build_roster(year, month)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Employee ID", "Employee", "Pod", "Pod Lead", "Brand", "Process", "Shift / Status"])
    for r in roster:
        writer.writerow([r["date"], r["employee_id"], r["employee"], r["pod"], r["pod_lead"], r["brand"], r["process"], r["shift"]])
    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=roster-{month_value}.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response

@app.route("/health")
def health():
    return {"status": "ok"}

init_db()

if __name__ == "__main__":
    app.run(debug=True)
