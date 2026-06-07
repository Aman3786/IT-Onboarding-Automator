# Mock IT Onboarding Automator

## Project Overview

The Mock IT Onboarding Automator is a backend service that automates employee onboarding based on HR webhook events.

When a new employee is hired, the HR system sends an onboarding event to the service. The system validates the event, determines which applications the employee should receive based on their role, provisions access records, records audit information, and ensures duplicate events are handled safely through idempotent processing.

The project also exposes an MCP (Model Context Protocol) server that allows AI assistants and operators to inspect employee access, review failed onboarding events, and retry failed provisioning operations.

---

# Features

## Webhook Processing

Supports HR onboarding events via:

```http
POST /webhooks/hris
```

Supported event type:

```text
employee.hired
```

## Role-Based Access Provisioning

Application access is automatically assigned based on employee role.

### engineer

* slack
* google_workspace
* jira

### sales

* slack
* google_workspace
* salesforce

### it_admin

* slack
* google_workspace
* jira
* salesforce

## Idempotent Event Processing

Duplicate webhook deliveries using the same `event_id` are safely ignored.

The system guarantees:

* No duplicate employees
* No duplicate access grants
* No duplicate provisioning actions

## Audit Logging

Every successful provisioning operation creates an audit log containing:

* event_id
* role
* granted applications
* idempotency status

## MCP Server

The MCP server exposes the following tools:

### get_employee_access

Retrieve employee details and provisioned application access.

### list_failed_events

List failed onboarding events.

### retry_provision

Retry a previously failed onboarding event.

---

# Architecture Summary

```mermaid
flowchart TB
    HR[HR System]

    HR -->|POST /webhooks/hris| WEBHOOK[FastAPI Webhook]
    WEBHOOK --> PROV[Provisioning Service]

    PROV --> EMP[Employees]
    PROV --> ACCESS[Access Grants]
    PROV --> AUDIT[Audit Log]

    DB[(SQLite Database)]

    EMP --> DB
    ACCESS --> DB
    AUDIT --> DB

    MCP[MCP Server<br/>(stdio)]

    MCP --> TOOL1[get_employee_access]
    MCP --> TOOL2[list_failed_events]
    MCP --> TOOL3[retry_provision]

    TOOL1 --> DB
    TOOL2 --> DB
    TOOL3 --> DB
```


---

# Technology Stack

| Component          | Technology              |
| ------------------ | ----------------------- |
| Language           | Python 3.12+            |
| API Framework      | FastAPI                 |
| ORM                | SQLAlchemy 2.0          |
| Database           | SQLite                  |
| MCP                | Official Python MCP SDK |
| Testing            | pytest                  |
| Package Management | uv                      |

---

# Prerequisites

Install:

* Python 3.12+
* uv
* Git

Verify installation:

```bash
python --version
uv --version
git --version
```

---

# Installation

Clone repository:

```bash
git clone https://github.com/Aman3786/IT-Onboarding-Automator.git
cd IT-Onboarding-Automator
```

Install dependencies:

```bash
uv sync
```

OR

```bash
uv install -r requirements.txt
```

---

# Initialize Database

Create tables and seed initial role mappings:

```bash
uv run python setup_db.py
```

Expected output:

```text
Database initialized successfully
```

Database location:

```text
data/onboarding.db
```

---

# Run API

Start FastAPI server:

```bash
uv run uvicorn api.main:app --reload
```

API available at:

```text
http://localhost:8000
```

Interactive documentation:

```text
http://localhost:8000/docs
```

---

# Run MCP Server

Start MCP server:

```bash
npx @modelcontextprotocol/inspector uv run python -m mcp_server.server
```

OR 

```bash
uv run mcp dev mcp_server/server.py
```

The MCP server uses stdio transport and is intended to be consumed by MCP Inspector, cursor and other MCP-compatible clients.

---

# Configure Cursor MCP

Create:

```text
.cursor/mcp.json
```

Configuration:

```json
{
  "mcpServers": {
    "onboarding-automator": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "mcp_server.server"
      ]
    }
  }
}
```

Restart Cursor after creating the configuration.



The following tools should become available through MCP Inspector/Cursor:

* get_employee_access
* list_failed_events
* retry_provision


---

# Run Tests

Run all tests:

```bash
uv run pytest
```

Run verbose output:

```bash
uv run pytest -v
```

Run a specific test file:

```bash
uv run pytest tests/test_webhook.py -v
```

---

# Example Requests

## Successful Employee Onboarding

```bash
curl -X POST http://localhost:8000/webhooks/hris \
-H "Content-Type: application/json" \
-d '{
  "event_id":"evt_hire_001",
  "event_type":"employee.hired",
  "email":"alex.chen@example.com",
  "full_name":"Alex Chen",
  "role":"engineer"
}'
```

Example response:

```json
{
  "event_id": "evt_hire_001",
  "status": "completed",
  "idempotent": false,
  "employee": {
    "email": "alex.chen@example.com",
    "role": "engineer"
  },
  "granted_apps": [
    "slack",
    "google_workspace",
    "jira"
  ]
}
```

---

## Duplicate Event

Submitting the same request again:

```json
{
  "event_id": "evt_hire_001",
  "status": "completed",
  "idempotent": true
}
```

---

## Invalid Role

```bash
curl -X POST http://localhost:8000/webhooks/hris \
-H "Content-Type: application/json" \
-d '{
  "event_id":"evt_invalid_role",
  "event_type":"employee.hired",
  "email":"bad@example.com",
  "full_name":"Bad User",
  "role":"unknown_role"
}'
```

Response:

```json
{ 
  "event_id":"evt_invalid_role",
  "status":"failed",
  "error":"Unknown role: 'unknown_role'"
}
```

---

# Assumptions

1. Employee email addresses are unique.
2. Roles are predefined and managed internally.
3. Application provisioning is simulated through database records.
4. SQLite is sufficient for local execution and evaluation.
5. Duplicate webhook deliveries reuse the same event_id.

