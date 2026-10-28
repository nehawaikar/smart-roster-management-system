# RosterFlow — Smart Roster Management System

A Flask + SQLite starter implementation for the DataStraw roster assessment.

## Features implemented
- Seed data for 30 employees with pods, brands, processes and weekly-off settings.
- SQLite persistence for employee records, process rules, date-specific leave/comp-off, holidays and generated roster entries.
- Monthly roster generation.
- Per-brand/per-process minimum staffing checks on configured operating days.
- Configurable Saturday, Sunday and public-holiday operation rules.
- Employee status update, add employee, date-specific leave/comp-off, holiday and working-rule forms.
- Search/filter roster by employee, pod, brand, process, status and date.
- CSV export.
- Dashboard and roster views.

## Run locally
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Create a virtual environment (recommended):
   - Windows: `py -m venv .venv`
   - Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
   - macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Start the app: `python app.py`
6. Open `http://127.0.0.1:5000`.

SQLite database `rosterflow.db` is created automatically at first run.

## Important assumptions / limitations
- The provided employees, brands, holidays and working rules are sample data. Verify all assumptions before relying on them.
- A current employee assignment has one primary brand and process. Employees assigned to multiple brands/processes would need a separate assignment table and conflict checking across all assignments.
- This starter checks coverage by brand/process and reports shortages; it does not automatically optimize or reassign staff to resolve a conflict.
- Weekly offs are generated from each employee's configured weekday. Operating calendars are configured per brand/process.
- Authentication, role permissions, approval workflow, deployment, automated tests, shift-time overlap detection, and an optimized scheduling solver are not included yet.
- Public holiday dates are examples and should be replaced with the relevant client's actual holiday calendar.
- The default `app.secret_key` should be set from an environment variable before deployment. Do not use Flask debug mode in production.

## Assessment submission checklist
- Deploy to a public URL and test the deployed app.
- Push source code to GitHub.
- Record a 3–5 minute walkthrough showing roster generation, different process rules, a coverage conflict and how changing an employee's availability affects the next roster.
- Include your actual LinkedIn profile URL.
- Explain the data model, scheduling logic, single/multi-resource handling, conflict handling, automation boundaries, scalability and next improvements in the final README.
