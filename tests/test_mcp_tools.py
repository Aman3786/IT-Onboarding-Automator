from mcp_server.server import (
    get_employee_access,
    list_failed_events,
)
from onboarding.service import process_hire


def test_get_employee_access():
    payload = {
        "event_id": "mcp_test_001",
        "event_type": "employee.hired",
        "email": "mcp@example.com",
        "full_name": "MCP User",
        "role": "engineer",
    }

    process_hire(payload)

    result = get_employee_access("mcp@example.com")

    assert result["email"] == "mcp@example.com"
    assert result["role"] == "engineer"
    assert len(result["grants"]) == 3


def test_list_failed_events():
    try:
        process_hire(
            {
                "event_id": "mcp_failed_004",
                "event_type": "employee.hired",
                "email": "bad@example.com",
                "full_name": "Bad User",
                "role": "bad_role",
            }
        )
    except ValueError:
        pass

    result = list_failed_events()

    assert "events" in result
    assert len(result["events"]) >= 1