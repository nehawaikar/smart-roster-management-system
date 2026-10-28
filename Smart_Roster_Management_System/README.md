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

- 
- ## Question and Answers
1. How did you model employees, brands, processes, pods, and their relationships?

I designed the system using a Flask application with SQLite for persistent data storage. The data model includes employee records, pods, brands, processes, weekly-off settings, date-specific leave and comp-off, holidays, working rules, and generated roster entries. Each employee has a primary brand and process assignment. Pods help organize employees, while brand and process rules define the staffing requirements. This structure keeps employee information, scheduling rules, and roster records organized and manageable.

2. How does your system generate a roster and determine whether it satisfies the required constraints?

The system generates monthly rosters using employee assignments, configured weekly offs, date-specific leave and comp-off, holidays, and brand/process operating rules. It checks whether the minimum staffing requirements are met for each brand and process on the applicable operating days. If the available staffing does not meet the required minimum, the system reports the shortage. This allows users to review the roster and identify coverage gaps.

3. How did you handle the difference between single-resource brands and brands with multiple employees?

The current implementation uses a primary brand and process assignment for each employee and checks staffing coverage for each brand and process. A single-resource brand can therefore show a shortage when its assigned employee is unavailable. Brands with multiple assigned employees can meet their minimum staffing requirements when enough eligible employees are available. The current system does not automatically optimize or redistribute assignments between brands and processes. Supporting employees with multiple simultaneous brand or process assignments would require a separate assignment table and additional conflict checking.

4. What happens when an employee manages all processes for a brand but is unavailable on a required working day?

The system considers employee availability, including configured weekly offs and date-specific leave or comp-off, when generating the roster. If the absence results in insufficient coverage for a required brand or process, the system reports the shortage. It does not automatically select and reassign a replacement employee. The user can review employee availability, update the relevant records, and regenerate the roster to check the resulting coverage.

5. How does your system handle conflicting requirements or insufficient staffing?

The system validates minimum staffing requirements for brands and processes on their configured operating days. When the available staffing is insufficient, it reports the shortage instead of silently treating the coverage requirement as satisfied. Users can review the affected roster, update employee availability or working rules, and generate the roster again. Automatic conflict resolution and staff reassignment are not implemented in the current version.

6. Which parts of the process did you automate, and which did you leave under human control? Why?

I automated monthly roster generation, staffing coverage checks, roster filtering, and CSV export. I also implemented forms for employee management, leave and comp-off, holidays, and working-rule updates. Human intervention is still required to review reported shortages, decide how to resolve staffing conflicts, and update the relevant records. I chose this approach because roster generation and validation are repetitive tasks, while resolving staffing shortages may require business decisions that should remain under human control.

7. If the company doubled its team and brand count, what would you change about your solution?

If the company doubled its team and brand count, I would first improve the data model to support multiple employee assignments across brands and processes through a separate assignment table. I would also optimize roster-generation and coverage-checking queries, add automated tests for larger datasets, and strengthen validation and error handling. I would consider introducing a constraint-based scheduling solver to improve staff allocation and resolve conflicts more efficiently. These changes would make the system more scalable, reliable, and adaptable to more complex business requirements.

8. If you had one additional week to work on this, what would you improve first?

I would first implement stronger automated tests for roster generation, employee unavailability, holidays, weekly offs, and minimum staffing requirements. Next, I would improve conflict reporting so users can easily identify the brand, process, and date associated with a shortage. I would also work on multi-brand employee assignments and automatic staff reassignment as future enhancements. Finally, I would improve deployment configuration and documentation to make the application safer and easier to maintain.
