"""LangGraph support investigation. Persist completed runs in Supabase, not RAM.

Graph nodes are scoped to the authenticated user and never take identity
from the model or HTTP request payload. No real refund or email tools exist.
"""
from __future__ import annotations

import os
import re
from typing import Any, TypedDict
from uuid import UUID

from fastapi import HTTPException

from app.core.supabase import CurrentUser
from app.rag.answer import NO_EVIDENCE, PolicyQuestion, answer_policy
from app.services.postgrest import owner_filter, query


class InvestigationState(TypedDict, total=False):
    ticket_id: str
    question: str
    intent: str
    owner_id: str
    order: dict[str, Any] | None
    policy_answer: str
    sources: list[dict[str, Any]]
    grounded: bool
    draft: str
    suggested_action: str | None
    requires_approval: bool
    steps: list[str]


def classify_intent(message: str) -> str:
    text = message.lower()
    if re.search(r"\b(refund|reimburse|money back|chargeback|return)\b", text):
        return "refund"
    if re.search(r"\b(escalat|supervisor|manager|complain|urgent)\w*\b", text):
        return "escalation"
    if re.search(r"\b(order|delivery|shipment|tracking|package|where is)\b", text):
        return "order"
    if re.search(r"\b(policy|terms|warranty|how long|eligible|rule)\b", text):
        return "policy"
    return "general"


def suggested_action(intent: str, question: str) -> str | None:
    if intent == "refund":
        return "refund_review"
    if intent == "escalation":
        return "send_reply"
    if re.search(r"\b(resolve|close ticket|mark resolved)\b", question, re.I):
        return "resolve_ticket"
    return None


def make_workflow(user: CurrentUser):
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Install langgraph in the backend") from exc

    async def classify(state: InvestigationState) -> dict:
        intent = classify_intent(state["question"])
        return {"intent": intent, "steps": ["classified:" + intent]}

    async def lookup(state: InvestigationState) -> dict:
        tickets = await query(user, "tickets", params=owner_filter(
            user, id=f"eq.{state['ticket_id']}", select="id,order_id", limit=1
        ))
        if not tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")
        order_id = tickets[0].get("order_id")
        order = None
        if order_id:
            rows = await query(user, "orders", params=owner_filter(
                user, id=f"eq.{order_id}",
                select="id,item,status,tracking_number,estimated_delivery", limit=1
            ))
            order = rows[0] if rows else None
        return {"order": order, "steps": state["steps"] + ["looked_up_owned_order"]}

    async def policy(state: InvestigationState) -> dict:
        if not os.getenv("GOOGLE_API_KEY"):
            return {
                "policy_answer": "Policy retrieval not performed: GOOGLE_API_KEY is not configured.",
                "sources": [], "grounded": False,
                "steps": state["steps"] + ["policy_not_configured"],
            }
        try:
            result = await answer_policy(user, PolicyQuestion(question=state["question"], top_k=4))
        except HTTPException as exc:
            if exc.status_code in (404, 422):
                raise
            return {
                "policy_answer": "Policy search unavailable. Human review is required.",
                "sources": [], "grounded": False,
                "steps": state["steps"] + ["policy_unavailable"],
            }
        return {
            "policy_answer": result.answer,
            "sources": [source.model_dump() for source in result.sources],
            "grounded": result.grounded,
            "steps": state["steps"] + ["policy_retrieved"],
        }

    async def draft(state: InvestigationState) -> dict:
        order = state.get("order")
        lines = ["INTERNAL DRAFT — human review required before customer use."]
        if order:
            lines.append(f"Recorded status of {order.get('item','item')}: {order.get('status','unknown')}.")
            if order.get("tracking_number"):
                lines.append("Tracking number: " + str(order["tracking_number"]))
            if order.get("estimated_delivery"):
                lines.append("Recorded ETA: " + str(order["estimated_delivery"]))
        else:
            lines.append("No attached owned order found. Confirm details with the customer.")
        if state.get("grounded"):
            lines.append("Policy evidence: " + state.get("policy_answer", NO_EVIDENCE))
        else:
            lines.append("No verified policy evidence; do not promise a refund or outcome.")
        if state["intent"] == "refund":
            lines.append("Refund requested. Human eligibility and payment review required. No refund issued.")
        if state["intent"] == "escalation":
            lines.append("Escalation requested. Human supervisor review required.")
        recommendation = suggested_action(state["intent"], state["question"])
        return {
            "draft": "\n\n".join(lines),
            "suggested_action": recommendation,
            "requires_approval": recommendation is not None,
            "steps": state["steps"] + ["drafted_internal_response"],
        }

    graph = StateGraph(InvestigationState)
    for name, node in (("classify", classify), ("lookup", lookup), ("policy", policy), ("draft", draft)):
        graph.add_node(name, node)
    graph.add_edge(START, "classify")
    graph.add_edge("classify", "lookup")
    graph.add_edge("lookup", "policy")
    graph.add_edge("policy", "draft")
    graph.add_edge("draft", END)
    return graph.compile()


async def investigate(user: CurrentUser, ticket_id: UUID, question: str) -> InvestigationState:
    return await make_workflow(user).ainvoke({
        "ticket_id": str(ticket_id), "question": question,
        "owner_id": user.id, "steps": [],
    })
