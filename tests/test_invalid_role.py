from sqlalchemy import select

from onboarding.database import get_session
from onboarding.models import WebhookEvent
from onboarding.service import process_hire


def test_unknown_role_creates_failed_webhook_event():
    payload = {
        "event_id": "test_unknown_role_004",
        "event_type": "employee.hired",
        "email": "unknown@example.com",
        "full_name": "Unknown User",
        "role": "super_admin",
    }

    try:
        process_hire(payload)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Unknown role" in str(exc)

    session = get_session()

    try:
        event = session.scalar(
            select(WebhookEvent).where(
                WebhookEvent.event_id == payload["event_id"]
            )
        )

        assert event is not None
        assert event.status == "failed"
        assert event.error_message is not None

    finally:
        session.close()