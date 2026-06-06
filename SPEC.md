# IT Onboarding Automator - Specification

## Problem Statement

Whenever there is a new hire, an event webhook is dispatched from HR to the onboarding system. It validates the event to be processed by determining the applications the user needs depending on their job role, populating the data into a SQLite database, and keeping track of the audit trail.

Idempotence is a crucial feature for webhook delivery so that duplicate delivery does not lead to duplicate access creation.

Furthermore, an MCP server will be providing means for agents and operators to use in reviewing employee access, analyzing failures, and reattempting provisioning.

---

## Goals

### Functional Requirements

1. Accept HR webhook events via HTTP.
2. Support only `employee.hired` events.
3. Validate incoming payloads.
4. Provision application access based on employee role.
5. Persist all data in SQLite.
6. Support idempotent processing using `event_id`.
7. Record audit logs for all provisioning actions.
8. Expose MCP tools:

   * get_employee_access
   * list_failed_events
   * retry_provision

### Non-Functional Requirements

1. Simple local development setup.
2. No external SaaS dependencies.
3. No cloud deployment requirements.
4. Shared business logic between API and MCP server.
5. Testable architecture.

---

## Architecture

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

## Technology Choices

### Language

Python 3.12+

Reason:

* Fast implementation
* Familiar ecosystem
* Official MCP SDK available

### API Framework

FastAPI

Reason:

* Built-in request validation
* Excellent developer experience
* Easy testing

### Database

SQLite

Reason:

* Assignment requirement fits local embedded database
* No infrastructure setup

### ORM

SQLAlchemy

Reason:

* Clean data modeling
* Easy migrations and testing

### Testing

pytest

Reason:

* Industry standard
* Simple test execution

### MCP

Official Python MCP SDK

Reason:

* Assignment requirement
* Native support for stdio MCP servers

---

## Data Model

### apps

Stores available SaaS applications.

Fields:

* id
* name

### role_app_grants

Maps roles to applications.

Fields:

* id
* role
* app_id

### employees

Stores employee records.

Fields:

* id
* email
* full_name
* role

### access_grants

Stores granted applications.

Fields:

* id
* employee_id
* app_id
* created_at

### audit_log

Stores audit history.

Fields:

* id
* action
* details_json
* created_at

### webhook_events

Stores incoming webhook events.

Fields:

* id
* event_id
* payload_json
* status
* error_message
* created_at

---

## Role Mapping

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

---

## Idempotency Strategy

The system will use `event_id` as a unique identifier.

If an event with the same `event_id` has already been successfully processed:

* No additional grants will be created.
* No duplicate employee provisioning will occur.
* Response will indicate idempotent replay.

---

## Shared Business Logic

A single provisioning service will be used by:

1. FastAPI webhook endpoint
2. MCP retry tool

This prevents duplicated provisioning logic.

---

## Error Handling

### Unknown Role

Return HTTP 400.

Webhook event stored as:

```text
status = failed
```

### Invalid Event Type

Return HTTP 400.

Webhook event stored as:

```text
status = failed
```

---

## Testing Strategy

Required:

1. Successful employee onboarding
2. Duplicate event idempotency

Additional:

3. Unknown role failure
4. MCP tool verification

---

## Future Improvements

1. Support additional HR event types
   - Extend the system to handle events such as employee role changes or employee termination.

2. Export audit logs to CSV
   - Allow operators to download provisioning history and failed events for reporting and troubleshooting.
