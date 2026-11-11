"""Phase 5 business policy tests, independent of credentials and network."""
import pytest
from fastapi import HTTPException
from app.services.approval_policy import validate_approval_action


def approved_run(intent="refund"):
    return {"intent": intent, "status": "pending_approval", "requires_approval": True}


@pytest.mark.parametrize("action", ["send_reply", "resolve_ticket", "refund_review"])
def test_closed_tickets_are_not_actionable(action):
    with pytest.raises(HTTPException) as error:
        validate_approval_action(action, {"status": "closed"}, approved_run())
    assert error.value.status_code == 409


def test_already_resolved_ticket_cannot_be_resolved_again():
    with pytest.raises(HTTPException) as error:
        validate_approval_action("resolve_ticket", {"status": "resolved"}, None)
    assert error.value.status_code == 409


def test_refunds_require_matching_investigation():
    for run in (None, approved_run("order"), approved_run("policy")):
        with pytest.raises(HTTPException) as error:
            validate_approval_action("refund_review", {"status": "open"}, run)
        assert error.value.status_code == 422


def test_refund_investigation_cannot_be_short_circuited():
    with pytest.raises(HTTPException) as error:
        validate_approval_action("resolve_ticket", {"status": "open"}, approved_run())
    assert error.value.status_code == 422


def test_escalation_must_not_auto_close():
    with pytest.raises(HTTPException) as error:
        validate_approval_action("resolve_ticket", {"status": "open"}, approved_run("escalation"))
    assert error.value.status_code == 422


def test_non_reviewable_run_is_rejected():
    with pytest.raises(HTTPException) as error:
        validate_approval_action("send_reply", {"status": "open"},
                                 {"intent": "general", "status": "completed", "requires_approval": False})
    assert error.value.status_code == 422


def test_stale_run_is_rejected():
    with pytest.raises(HTTPException) as error:
        validate_approval_action("send_reply", {"status": "open"},
                                 {"intent": "general", "status": "completed", "requires_approval": True})
    assert error.value.status_code == 409


def test_manual_reply_without_agent_run_is_supported():
    validate_approval_action("send_reply", {"status": "open"}, None)


def test_valid_refund_review_is_supported():
    validate_approval_action("refund_review", {"status": "in_progress"}, approved_run())
