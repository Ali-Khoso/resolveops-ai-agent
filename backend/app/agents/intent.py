"""Conservative, deterministic intent and suggested-action rules.

Intent routing only recommends internal review, never authorizes actions.
"""
from __future__ import annotations
import re

_REFUND = re.compile(r"\b(?:refund(?:s|ed|ing)?|reimburs\w*|money\s+back|chargeback|return(?:s|ed|ing)?)\b", re.I)
_ESCALATE = re.compile(r"\b(?:escalat\w*|supervisor|manager|complain\w*|urgent)\b", re.I)
_ORDER = re.compile(r"\b(?:order|delivery|shipment|tracking|package|where\s+is)\b", re.I)
_POLICY = re.compile(r"\b(?:policy|policies|terms|warranty|how\s+long|eligible|rules?)\b", re.I)
_RESOLVE = re.compile(r"\b(?:resolve\s+(?:the\s+|this\s+)?ticket|close\s+(?:the\s+|this\s+)?ticket|mark\s+(?:the\s+|this\s+)?ticket\s+resolved)\b", re.I)


def classify_intent(message: str) -> str:
    """Financial review takes precedence over tracking and informational requests."""
    if _REFUND.search(message):
        return "refund"
    if _ESCALATE.search(message):
        return "escalation"
    if _ORDER.search(message):
        return "order"
    if _POLICY.search(message):
        return "policy"
    return "general"


def suggested_action(intent: str, question: str) -> str | None:
    """Return a reviewer-action category, never execute it automatically."""
    if intent == "refund":
        return "refund_review"
    if intent == "escalation":
        return "send_reply"
    if _RESOLVE.search(question):
        return "resolve_ticket"
    return None


def needs_policy_retrieval(intent: str) -> bool:
    """Only run vector search for intents that can benefit from policy evidence."""
    return intent in {"refund", "policy", "general"}
