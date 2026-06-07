# SQLAlchemy database models for project
_Exported on 6/7/2026 at 22:52:11 GMT+5:30 from Cursor (3.7.12)_

---

**User**

Implement SQLAlchemy database models for this project.

Requirements:

Database: SQLite

Create models:

1. App

* id
* name (unique)

2. RoleAppGrant

* id
* role
* app_id

3. Employee

* id
* email (unique)
* full_name
* role

4. AccessGrant

* id
* employee_id
* app_id
* created_at

5. AuditLog

* id
* action
* details_json
* created_at

6. WebhookEvent

* id
* event_id (unique)
* payload_json
* status
* error_message
* created_at

Create:

* onboarding/database.py
* onboarding/models.py

Use SQLAlchemy 2.0 style.

Create helper functions:

* get_session()
* init_db()


Use onboarding.db SQLite file inside data folder.


---

**Cursor**

I'll review the project spec and layout, then add SQLAlchemy 2.0 models and database helpers under `onboarding/`.


Creating the `onboarding` package with SQLAlchemy 2.0 models and database helpers.


SQLAlchemy 2.0 models and database helpers are in place. Summary:

### `onboarding/models.py`
Six models using `DeclarativeBase`, `Mapped`, and `mapped_column`:

| Model | Table | Notes |
|-------|-------|-------|
| `App` | `apps` | `name` unique |
| `RoleAppGrant` | `role_app_grants` | FK → `apps.id` |
| `Employee` | `employees` | `email` unique |
| `AccessGrant` | `access_grants` | FKs + `created_at` (server default) |
| `AuditLog` | `audit_log` | JSON stored as `Text` |
| `WebhookEvent` | `webhook_events` | `event_id` unique, optional `error_message` |

Relationships are wired between `App`, `RoleAppGrant`, `Employee`, and `AccessGrant`.

### `onboarding/database.py`
- SQLite at `data/onboarding.db` (relative to project root)
- `get_session()` — returns a new ORM session
- `init_db()` — creates the `data/` directory and all tables

### Usage

```python
from onboarding.database import get_session, init_db
from onboarding.models import App, Employee

init_db()

with get_session() as session:
    session.add(App(name="slack"))
    session.commit()
```

Verified: `init_db()` creates all six expected tables. An `onboarding/__init__.py` was added so the package imports cleanly.

---

**User**

Create onboarding/seed.py.

Seed the following apps:

slack
google_workspace
jira
salesforce

Seed role mappings:

engineer:

* slack
* google_workspace
* jira

sales:

* slack
* google_workspace
* salesforce

it_admin:

* slack
* google_workspace
* jira
* salesforce

Create a function:

seed_database()

that can safely run multiple times without duplicates.


---

**Cursor**

Reviewing the models and database setup so the seed script matches existing patterns.


Created `onboarding/seed.py` with an idempotent `seed_database()` function.

### Behavior
1. Calls `init_db()` so tables exist before seeding.
2. **Apps** — looks up each app by unique `name`; inserts only if missing.
3. **Role mappings** — looks up each `(role, app_id)` pair; inserts only if missing.
4. Commits once at the end; rolls back on error.

### Seeded data
- **4 apps:** `slack`, `google_workspace`, `jira`, `salesforce`
- **10 role grants:** engineer (3), sales (3), it_admin (4)

### Usage

```python
from onboarding.seed import seed_database

seed_database()
```

Running it twice was verified — counts stay at 4 apps and 10 grants with no duplicates.

---

**User**

Create onboarding/service.py.

Implement:

process_hire(payload: dict)

Validation requirements:

Required fields:

* event_id
* event_type
* email
* full_name
* role

Only allow:
event_type == "employee.hired"

If validation fails:

* create WebhookEvent record
* status = "failed"
* save error message
* raise ValueError

Idempotency:

Check webhook_events table.

If event_id already exists and status == "completed":

Return:

{
"event_id": "...",
"status": "completed",
"idempotent": true
}

Do not create employees.
Do not create grants.
Do not create audit logs.

Role validation:

If role does not exist in role_app_grants:

* create failed webhook event
* status = failed
* save error message
* raise ValueError

Successful flow:

1. Create employee if not already present.

2. Load all apps assigned to the role.

3. Create access grants.

Requirements:

* No duplicate grants.
* Respect unique constraints.

4. Create webhook_events record:

status = "completed"

5. Create audit log.

action:

"employee_provisioned"

details_json MUST contain:

{
"event_id": "...",
"role": "...",
"granted_apps": [...],
"idempotent": false
}

6. Write structured log to stderr.

Example:

{
"event_id": "...",
"granted_app_count": 3
}

Use Python logging.

Return:

{
"event_id": "...",
"status": "completed",
"idempotent": false,
"employee": {
"email": "...",
"role": "..."
},
"granted_apps": [...]
}

Use SQLAlchemy session management.

Code should be production quality and readable.


---

**Cursor**

Reviewing models, seed data, and existing onboarding code to implement `process_hire`.


Implementing `process_hire` with validation, idempotency, and session management, matching existing import patterns.


Created `onboarding/service.py` with `process_hire(payload: dict)`.

### Flow

1. **Validation** — Requires `event_id`, `event_type`, `email`, `full_name`, and `role`; only `employee.hired` is allowed. On failure, records a failed `WebhookEvent` (when `event_id` is present) and raises `ValueError`.

2. **Idempotency** — If `event_id` already exists with `status == "completed"`, returns early with no side effects:
   ```python
   {"event_id": "...", "status": "completed", "idempotent": True}
   ```

3. **Role validation** — Loads apps from `role_app_grants`. Unknown roles record a failed webhook and raise `ValueError`.

4. **Successful provisioning**
   - Gets or creates `Employee` by email
   - Ensures `AccessGrant` rows exist (no duplicates per employee/app)
   - Marks webhook `completed` (updates prior failed records if retrying)
   - Writes audit log with action `employee_provisioned` and the required JSON shape
   - Logs structured JSON to stderr via Python logging

### Session handling

Uses `get_session()` with commit on success, rollback on unexpected errors, and `session.close()` in `finally`.

### Verified behavior

- Engineer hire → 3 grants, audit log, structured log output
- Duplicate `event_id` → idempotent return, no extra employees/grants/audit rows
- Validation and unknown role failures → failed webhook records with error messages

---

**User**

Create api/main.py.

Requirements:

Use FastAPI.

Create POST /webhooks/hris

Call process_hire(payload).

Success:
Return HTTP 202.

Validation failures:
Return HTTP 400.

Response body should be the dictionary returned by process_hire.

Add FastAPI startup event:

* init_db()
* seed_database()

Provide uvicorn entrypoint.


---

**Cursor**

Reviewing the project structure and existing modules to wire up the FastAPI app.


Fixing `seed.py` package imports so startup works, then creating the FastAPI app.


Created `api/main.py` with the FastAPI webhook endpoint.

### `api/main.py`

- **`POST /webhooks/hris`** — accepts JSON payload, calls `process_hire(payload)`
- **202** — success; body is the dict returned by `process_hire`
- **400** — validation failures (`ValueError`); body includes `event_id`, `status: "failed"`, and `error` (since `process_hire` raises rather than returning on failure)
- **Startup** — runs `init_db()` then `seed_database()`
- **Uvicorn entrypoint** — run with `python api/main.py` or `uvicorn api.main:app`

### Run the server

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Or:

```bash
python api/main.py
```

Also updated `onboarding/seed.py` to use package imports (`onboarding.database`, `onboarding.models`) so startup seeding works when the app is loaded as `api.main:app`.

Verified:
- Hire event → **202** with employee and granted apps
- Duplicate event → **202** with `"idempotent": true`
- Invalid payload → **400** with error details

---

**User**

<system_notification>
The following task has finished. If you were already aware, ignore this notification and do not restate prior responses.

<task>
kind: shell
status: aborted
task_id: 525255
title: Start uvicorn server for testing
output_path: C:\Users\Aman Shaikh\.cursor\projects\c-Users-Aman-Shaikh-OneDrive-Desktop-ItOnboardingAutomator\terminals\525255.txt
</task>
</system_notification>
<user_query>Briefly inform the user about the task result and perform any follow-up actions (if needed). If there's no follow-ups needed, don't explicitly say that.</user_query>

---

**Cursor**

The FastAPI app is in place at `api/main.py`.

**What works**
- `POST /webhooks/hris` calls `process_hire` and returns **202** with its result on success
- Validation failures return **400** with `event_id`, `status: "failed"`, and an `error` message
- On startup, the app runs `init_db()` and `seed_database()`
- You can start it with `uvicorn api.main:app` or `python api/main.py`

**Also fixed:** `onboarding/seed.py` imports were updated to package-style imports so startup seeding works when the app loads as `api.main:app`.

**Verified:** successful hire (202), idempotent replay (202), and invalid payload (400) all behaved as expected during testing.

---

**User**

Create a Python MCP server using the official MCP SDK.

File:

mcp_server/server.py

Requirements:

Implement exactly these 3 MCP tools:

1. get_employee_access(email: str)

Return:

{
"email": "...",
"full_name": "...",
"role": "...",
"grants": [...]
}

2. list_failed_events(since: str | None = None)

Return failed webhook events.

If since is provided, filter by created_at >= since.

3. retry_provision(event_id: str)

Requirements:

* Find failed webhook event
* Load original payload_json
* Call process_hire(payload)
* Return result

Use existing SQLAlchemy models.

Use existing process_hire() service.

Do not print anything to stdout.

Use stderr logging only.

Add clear MCP tool descriptions.

Use the official Python MCP SDK stdio transport.


---

**Cursor**

Reviewing the project and MCP SDK setup before implementing the stdio MCP server.


Implementing the MCP server with FastMCP and verifying tool behavior.


Created `mcp_server/server.py` using the official MCP SDK (`FastMCP`) with stdio transport.

### Tools

1. **`get_employee_access(email)`** — Looks up employee by email; returns `email`, `full_name`, `role`, and `grants` (sorted app names).

2. **`list_failed_events(since=None)`** — Returns failed webhook events; optional ISO 8601 `since` filters `created_at >= since`.

3. **`retry_provision(event_id)`** — Loads a failed event’s `payload_json`, calls `process_hire(payload)`, and returns its result.

### Other details

- Uses existing SQLAlchemy models and `process_hire()` from `onboarding.service`
- Startup lifespan runs `init_db()` and `seed_database()`
- Logging goes to stderr only (no stdout output)
- Each tool has a clear description for MCP clients

### Run

```bash
python -m mcp_server.server
```

Or configure your MCP client to run:

```bash
python mcp_server/server.py
```

---

**User**

I'm getting ModuleNotFoundError: No module named 'onboarding' when running:

uv run mcp dev mcp_server/server.py

Analyze the project structure and fix Python package imports correctly.




#### Note: From here, free limit over for Cursor AI, so debugging of above issue and test case code done without Cursor AI. Hope it is ok!

