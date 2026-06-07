from __future__ import annotations

import json
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


from mcp.server.fastmcp import FastMCP
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from onboarding.database import get_session, init_db
from onboarding.models import AccessGrant, Employee, WebhookEvent
from onboarding.seed import seed_database
from onboarding.service import process_hire



logger = logging.getLogger("mcp_server")


def _configure_logging() -> None:
    if logger.handlers:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


@asynccontextmanager
async def server_lifespan(_server: FastMCP):
    init_db()
    seed_database()
    logger.info("MCP server initialized database and seed data")
    yield


mcp = FastMCP(
    name="it-onboarding-automator",
    instructions=(
        "Tools for reviewing employee access, inspecting failed HR webhook events, "
        "and retrying failed onboarding provisioning."
    ),
    lifespan=server_lifespan,
)


@mcp.tool(
    name="get_employee_access",
    description=(
        "Look up an employee by email address and return their profile plus the list "
        "of provisioned application grants."
    ),
)
def get_employee_access(email: str) -> dict[str, Any]:
    session = get_session()
    try:
        employee = session.scalar(
            select(Employee)
            .where(Employee.email == email)
            .options(
                joinedload(Employee.access_grants).joinedload(AccessGrant.app),
            )
        )
        if employee is None:
            raise ValueError(f"Employee not found: {email!r}")

        grants = sorted(grant.app.name for grant in employee.access_grants)
        return {
            "email": employee.email,
            "full_name": employee.full_name,
            "role": employee.role,
            "grants": grants,
        }
    finally:
        session.close()


@mcp.tool(
    name="list_failed_events",
    description=(
        "List webhook events that failed provisioning. Optionally filter to events "
        "created on or after the provided ISO 8601 timestamp (since)."
    ),
)
def list_failed_events(since: str | None = None) -> dict[str, Any]:
    session = get_session()
    try:
        query = select(WebhookEvent).where(WebhookEvent.status == "failed")
        if since is not None:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            query = query.where(WebhookEvent.created_at >= since_dt)

        events = session.scalars(query.order_by(WebhookEvent.created_at.desc())).all()
        return {
            "events": [
                {
                    "event_id": event.event_id,
                    "status": event.status,
                    "error_message": event.error_message,
                    "created_at": event.created_at.isoformat(),
                    "payload": json.loads(event.payload_json),
                }
                for event in events
            ]
        }
    finally:
        session.close()


@mcp.tool(
    name="retry_provision",
    description=(
        "Retry provisioning for a previously failed webhook event by event_id. "
        "Reloads the stored payload and runs the hire provisioning flow again."
    ),
)
def retry_provision(event_id: str) -> dict[str, Any]:
    session = get_session()
    try:
        event = session.scalar(
            select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        )
        if event is None:
            raise ValueError(f"Webhook event not found: {event_id!r}")
        if event.status != "failed":
            raise ValueError(
                f"Webhook event {event_id!r} is not failed (status={event.status!r})"
            )

        payload = json.loads(event.payload_json)
    finally:
        session.close()

    logger.info("Retrying provisioning for event_id=%s", event_id)
    return process_hire(payload)


def main() -> None:
    _configure_logging()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
