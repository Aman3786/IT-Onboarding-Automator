# VIBE_LOG

## AI Tools Used

### Cursor AI

Used for project scaffolding, SQLAlchemy model generation, FastAPI endpoint generation, and MCP server implementation.

---

# AI-Generated Code Accepted and Shipped

## Example 1: SQLAlchemy Database Models

AI generated the initial SQLAlchemy 2.0 models including:

* App
* Employee
* AccessGrant
* AuditLog
* WebhookEvent
* RoleAppGrant

This significantly accelerated schema creation and relationship setup.

Verification:

* Database initialization succeeded.
* Tables were created successfully.
* Seed data loaded correctly.

---

## Example 2: MCP Server Scaffolding

AI generated the initial MCP server structure including:

* FastMCP setup
* Tool registration
* Stdio transport configuration
* Tool descriptions

Generated tools:

* get_employee_access
* list_failed_events
* retry_provision

Verification:

* MCP server started successfully.
* Tools were visible in MCP Inspector.
* All tools returned expected results.

---

## Example 3: FastAPI Endpoint Scaffolding

AI generated the initial FastAPI webhook endpoint and request handling flow.

Verification:

* Successful onboarding requests processed correctly.
* Invalid requests returned appropriate errors.
* End-to-end testing completed using curl and pytest

---

# Example Where AI Was Wrong

## Python Package Import Issue

Issue:

The generated MCP implementation initially failed with:

```text
ModuleNotFoundError: No module named 'onboarding'
```

Root Cause:

The generated execution path and package imports did not correctly account for project structure when launching the MCP server.

Fix Applied:

* Added package-aware execution.
* Executed the server using:

```bash
npx npx @modelcontextprotocol/inspector uv run python -m mcp_server.server
```

OR 

```bash
uv run mcp dev mcp_server/server.py
```

* Updated module loading strategy.

Verification:

* MCP server started successfully.
* MCP Inspector detected all tools.
* All tools executed successfully.

---

# MCP Testing From IDE

Testing was performed using MCP Inspector.

Steps:

1. Start MCP server.
2. Connect using MCP Inspector.
3. Verify tool registration.
4. Execute each tool individually.

Validated tools:

### get_employee_access

Verified employee details and application grants.

### list_failed_events

Verified retrieval of failed onboarding events.

### retry_provision

Verified retry execution path using stored webhook payloads.

All tools behaved as expected.

---

# Reflection

## What AI Saved Time On

* SQLAlchemy model generation
* FastAPI scaffolding
* MCP server setup
* Test generation
* Boilerplate documentation

AI accelerated development by generating repetitive and structural code that would otherwise require significant manual effort.

## Where Human Judgment Mattered

* Reviewing generated database schema
* Debugging import and execution issues
* Verifying idempotency behavior
* Validating assignment-specific requirements
* End-to-end testing of webhook and MCP functionality

Human review was essential to ensure correctness, validate assumptions, and confirm that generated code met the requirements of the assignment rather than merely compiling successfully.

## Overall Assessment

AI was highly effective for accelerating implementation and reducing boilerplate work. Human oversight remained necessary for debugging, validation, and ensuring that the final solution satisfied the project requirements.
