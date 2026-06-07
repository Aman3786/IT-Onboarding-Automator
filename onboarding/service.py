from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .database import get_session
from .models import AccessGrant, AuditLog, Employee, RoleAppGrant, WebhookEvent

logger = logging.getLogger("onboarding.service")

REQUIRED_FIELDS = ("event_id", "event_type", "email", "full_name", "role")
ALLOWED_EVENT_TYPE = "employee.hired"


def _ensure_logger_configured() -> None:
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def _validate_payload(payload: dict[str, Any]) -> str | None:
    missing = [field for field in REQUIRED_FIELDS if not payload.get(field)]
    if missing:
        return f"Missing required fields: {', '.join(missing)}"
    if payload["event_type"] != ALLOWED_EVENT_TYPE:
        return f"Unsupported event_type: {payload['event_type']!r}"
    return None


def _payload_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload)


def _record_failed_webhook(
    session: Session,
    payload: dict[str, Any],
    event_id: str,
    error_message: str,
) -> None:
    existing = session.scalar(
        select(WebhookEvent).where(WebhookEvent.event_id == event_id)
    )
    serialized_payload = _payload_json(payload)
    if existing is not None:
        existing.payload_json = serialized_payload
        existing.status = "failed"
        existing.error_message = error_message
    else:
        session.add(
            WebhookEvent(
                event_id=event_id,
                payload_json=serialized_payload,
                status="failed",
                error_message=error_message,
            )
        )
    session.commit()


def _get_or_create_employee(
    session: Session,
    *,
    email: str,
    full_name: str,
    role: str,
) -> Employee:
    employee = session.scalar(select(Employee).where(Employee.email == email))
    if employee is None:
        employee = Employee(email=email, full_name=full_name, role=role)
        session.add(employee)
        session.flush()
    return employee


def _ensure_access_grants(
    session: Session,
    employee: Employee,
    role_grants: list[RoleAppGrant],
) -> list[str]:
    granted_apps: list[str] = []
    for role_grant in role_grants:
        app = role_grant.app
        granted_apps.append(app.name)
        existing_grant = session.scalar(
            select(AccessGrant).where(
                AccessGrant.employee_id == employee.id,
                AccessGrant.app_id == app.id,
            )
        )
        if existing_grant is None:
            session.add(AccessGrant(employee_id=employee.id, app_id=app.id))
    return granted_apps


def _record_completed_webhook(
    session: Session,
    payload: dict[str, Any],
    event_id: str,
) -> None:
    existing = session.scalar(
        select(WebhookEvent).where(WebhookEvent.event_id == event_id)
    )
    serialized_payload = _payload_json(payload)
    if existing is not None:
        existing.payload_json = serialized_payload
        existing.status = "completed"
        existing.error_message = None
    else:
        session.add(
            WebhookEvent(
                event_id=event_id,
                payload_json=serialized_payload,
                status="completed",
            )
        )


def _record_audit_log(
    session: Session,
    *,
    event_id: str,
    role: str,
    granted_apps: list[str],
) -> None:
    session.add(
        AuditLog(
            action="employee_provisioned",
            details_json=json.dumps(
                {
                    "event_id": event_id,
                    "role": role,
                    "granted_apps": granted_apps,
                    "idempotent": False,
                }
            ),
        )
    )


def process_hire(payload: dict[str, Any]) -> dict[str, Any]:
    session = get_session()
    try:
        validation_error = _validate_payload(payload)
        if validation_error is not None:
            event_id = payload.get("event_id")
            if event_id:
                _record_failed_webhook(session, payload, event_id, validation_error)
            raise ValueError(validation_error)

        event_id = payload["event_id"]
        email = payload["email"]
        full_name = payload["full_name"]
        role = payload["role"]

        existing_event = session.scalar(
            select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        )
        if existing_event is not None and existing_event.status == "completed":
            return {
                "event_id": event_id,
                "status": "completed",
                "idempotent": True,
            }

        role_grants = list(
            session.scalars(
                select(RoleAppGrant)
                .where(RoleAppGrant.role == role)
                .options(joinedload(RoleAppGrant.app))
            ).unique()
        )
        if not role_grants:
            error_message = f"Unknown role: {role!r}"
            _record_failed_webhook(session, payload, event_id, error_message)
            raise ValueError(error_message)

        employee = _get_or_create_employee(
            session,
            email=email,
            full_name=full_name,
            role=role,
        )
        granted_apps = _ensure_access_grants(session, employee, role_grants)
        _record_completed_webhook(session, payload, event_id)
        _record_audit_log(
            session,
            event_id=event_id,
            role=role,
            granted_apps=granted_apps,
        )
        session.commit()

        _ensure_logger_configured()
        logger.info(
            json.dumps(
                {
                    "event_id": event_id,
                    "granted_app_count": len(granted_apps),
                }
            )
        )

        return {
            "event_id": event_id,
            "status": "completed",
            "idempotent": False,
            "employee": {
                "email": email,
                "role": role,
            },
            "granted_apps": granted_apps,
        }
    except ValueError:
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
