"""Offline regression tests for conservative Phase 4 intent classification."""
import pytest
from app.agents.intent import classify_intent, suggested_action


@pytest.mark.parametrize(("message","expected"),[
    ("Refund my order, please", "refund"),
    ("I need my MONEY back for a late package", "refund"),
    ("The item was returned", "refund"),
    ("I want reimbursement", "refund"),
    ("Please escalate this to a supervisor", "escalation"),
    ("Can a manager help with this?", "escalation"),
    ("Where is my order?", "order"),
    ("Can you check my tracking number?", "order"),
    ("What does the warranty cover?", "policy"),
    ("How long am I eligible?", "policy"),
    ("Hello", "general"),
])
def test_intent_categories(message,expected):
    assert classify_intent(message) == expected


def test_sensitive_refund_intent_overrides_other_categories():
    assert classify_intent("Refund my package and escalate to a manager") == "refund"


@pytest.mark.parametrize("question", [
    "resolve the ticket", "Close this ticket", "mark ticket resolved",
])
def test_ticket_closing_phrases_require_review(question):
    assert suggested_action("general", question) == "resolve_ticket"


def test_refund_and_escalation_always_request_review():
    assert suggested_action("refund", "where is it") == "refund_review"
    assert suggested_action("escalation", "help") == "send_reply"


def test_non_actionable_messages_do_not_create_actions():
    assert suggested_action("order", "where is my order") is None
    assert suggested_action("general", "Can you help?") is None
