from onboarding.service import process_hire
from onboarding.database import get_session
from onboarding.models import Employee, AccessGrant, AuditLog, WebhookEvent
from sqlalchemy import select


def test_valid_hire():
    payload = {
        "event_id": "test_hire_004",
        "event_type": "employee.hired",
        "email": "test.user@example.com",
        "full_name": "Test User",
        "role": "engineer",
    }

    result = process_hire(payload)

    assert result["status"] == "completed"
    assert result["idempotent"] is False

    session = get_session()

    try:
        employee = session.scalar(
            select(Employee).where(Employee.email == payload["email"])
        )
        assert employee is not None

        grants = session.scalars(
            select(AccessGrant).where(
                AccessGrant.employee_id == employee.id
            )
        ).all()

        assert len(grants) == 3

        audit_log = session.scalar(
            select(AuditLog).order_by(AuditLog.id.desc())
        )

        assert audit_log is not None
        assert audit_log.action == "employee_provisioned"

        webhook_event = session.scalar(
            select(WebhookEvent).where(
                WebhookEvent.event_id == payload["event_id"]
            )
        )

        assert webhook_event is not None
        assert webhook_event.status == "completed"

    finally:
        session.close()