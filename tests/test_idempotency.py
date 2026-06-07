from onboarding.service import process_hire
from onboarding.database import get_session
from onboarding.models import Employee, AccessGrant
from sqlalchemy import select


def test_duplicate_event_is_idempotent():
    payload = {
        "event_id": "test_duplicate_003",
        "event_type": "employee.hired",
        "email": "duplicate@example.com",
        "full_name": "Duplicate User",
        "role": "sales",
    }

    first = process_hire(payload)
    second = process_hire(payload)

    assert first["idempotent"] is False
    assert second["idempotent"] is True

    session = get_session()

    try:
        employee = session.scalar(
            select(Employee).where(Employee.email == payload["email"])
        )

        grants = session.scalars(
            select(AccessGrant).where(
                AccessGrant.employee_id == employee.id
            )
        ).all()

        assert len(grants) == 3

    finally:
        session.close()