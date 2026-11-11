"""Business guardrails for proposed internal approval actions.

A validated request is NOT an authorization to send mail, refund payment,
or bypass the database's row-level security policies.
"""
from __future__ import annotations
from typing import Any
from fastapi import HTTPException


def validate_approval_action(
    action_type: str,
    ticket: dict[str, Any],
    run: dict[str, Any] | None,
) -> None:
    """Refuse stale tickets or proposals incompatible with their investigation."""
    if ticket.get("status") == "closed":
        raise HTTPException(status_code=409, detail="Closed tickets cannot receive new approvals")
    if action_type == "resolve_ticket" and ticket.get("status") == "resolved":
        raise HTTPException(status_code=409, detail="Ticket is already resolved")

    if run is not None:
        if not run.get("requires_approval"):
            raise HTTPException(status_code=422, detail="This investigation does not require approval")
        if run.get("status") != "pending_approval":
            raise HTTPException(status_code=409, detail="Investigation is not awaiting approval")
        intent = run.get("intent")
        if intent == "refund" and action_type != "refund_review":
            raise HTTPException(status_code=422, detail="Refund investigations require refund review first")
        if intent == "escalation" and action_type == "resolve_ticket":
            raise HTTPException(status_code=422, detail="Escalated tickets require human reply review")

    if action_type == "refund_review" and (run is None or run.get("intent") != "refund"):
        raise HTTPException(status_code=422, detail="Refund review requires a linked refund investigation")
