"""Deterministic review flags; flags never authorize account or payment actions."""


def assess_risks(*, intent: str, has_order: bool, grounded: bool) -> list[str]:
    flags: list[str] = []
    if intent in {"order", "refund"} and not has_order:
        flags.append("verify_order_link")
    if intent in {"refund", "policy"} and not grounded:
        flags.append("policy_not_verified")
    if intent == "refund":
        flags.append("human_refund_review")
    if intent == "escalation":
        flags.append("human_escalation_required")
    return flags
