from app.agents.risks import assess_risks


def test_refund_without_evidence_is_high_review():
    assert assess_risks(intent="refund", has_order=False, grounded=False) == [
        "verify_order_link", "policy_not_verified", "human_refund_review"
    ]


def test_verified_order_tracking_has_no_unnecessary_flags():
    assert assess_risks(intent="order", has_order=True, grounded=False) == []


def test_policy_question_needs_evidence():
    assert assess_risks(intent="policy", has_order=False, grounded=False) == ["policy_not_verified"]
    assert assess_risks(intent="policy", has_order=False, grounded=True) == []


def test_escalation_is_still_human_reviewed():
    assert assess_risks(intent="escalation", has_order=True, grounded=True) == [
        "human_escalation_required"
    ]
