"""Authenticated investigation, human approval, and analytics API."""
from __future__ import annotations

import asyncio
import logging
from time import perf_counter
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.agents.resolution_graph import investigate
from app.agents.settings import workflow_timeout_seconds
from app.core.supabase import CurrentUser, get_current_user
from app.models.operations import ApprovalCreate, ApprovalDecision, InvestigationCreate
from app.services.postgrest import owner_filter, query, rpc

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/workspace/operations", tags=["Agent Operations"])


def require_one(rows: list[dict], detail: str = "Record not found") -> dict:
    if not rows:
        raise HTTPException(status_code=404, detail=detail)
    return rows[0]


async def owned_ticket(user: CurrentUser, ticket_id: UUID) -> dict:
    return require_one(await query(
        user, "tickets",
        params=owner_filter(user, id=f"eq.{ticket_id}",
                            select="id,owner_id,customer_id,order_id", limit=1),
    ), "Ticket not found")


@router.post("/investigations", status_code=201)
async def start_investigation(payload: InvestigationCreate, user: CurrentUser = Depends(get_current_user)):
    await owned_ticket(user, payload.ticket_id)
    start = perf_counter()
    try:
        state = await asyncio.wait_for(
            investigate(user, payload.ticket_id, payload.question),
            timeout=workflow_timeout_seconds(),
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Investigation timed out; please retry") from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Agent graph failed")
        raise HTTPException(status_code=502, detail="Agent investigation failed") from exc

    duration_ms = min(3600000, max(0, round((perf_counter() - start) * 1000)))
    record = require_one(await query(user, "agent_runs", method="POST", data={
        "owner_id": user.id,
        "ticket_id": str(payload.ticket_id),
        "question": payload.question,
        "intent": state["intent"],
        "response": state["draft"][:10000],
        "order_snapshot": state.get("order") or {},
        "sources": state.get("sources", []),
        "requires_approval": state.get("requires_approval", False),
        "status": "pending_approval" if state.get("requires_approval") else "completed",
        "duration_ms": duration_ms,
    }))
    return {"run": record, "suggested_action": state.get("suggested_action"),
            "steps": state.get("steps", [])}


@router.get("/investigations")
async def list_investigations(limit: int = Query(50, ge=1, le=100),
                              offset: int = Query(0, ge=0),
                              user: CurrentUser = Depends(get_current_user)):
    return {"items": await query(user, "agent_runs", params=owner_filter(
        user, select="id,ticket_id,intent,question,response,sources,requires_approval,status,duration_ms,created_at",
        order="created_at.desc", limit=limit, offset=offset
    ))}


@router.get("/investigations/{run_id}")
async def get_investigation(run_id: UUID, user: CurrentUser = Depends(get_current_user)):
    return require_one(await query(user, "agent_runs", params=owner_filter(user, id=f"eq.{run_id}", limit=1)))


@router.post("/approvals", status_code=201)
async def create_approval(payload: ApprovalCreate, user: CurrentUser = Depends(get_current_user)):
    await owned_ticket(user, payload.ticket_id)
    if payload.run_id:
        run = require_one(await query(user, "agent_runs", params=owner_filter(
            user, id=f"eq.{payload.run_id}", ticket_id=f"eq.{payload.ticket_id}",
            select="id,requires_approval", limit=1
        )), "Investigation not found")
        if not run.get("requires_approval"):
            raise HTTPException(status_code=422, detail="This investigation does not require approval")
    return require_one(await query(user, "approval_requests", method="POST", data={
        "owner_id": user.id, "ticket_id": str(payload.ticket_id),
        "run_id": str(payload.run_id) if payload.run_id else None,
        "action_type": payload.action_type,
        "draft_reply": payload.draft_reply, "reason": payload.reason,
        "status": "pending",
    }))


@router.get("/approvals")
async def list_approvals(status: str | None = Query(default=None, pattern="^(pending|approved|rejected)$"),
                         limit: int = Query(50, ge=1, le=100),
                         user: CurrentUser = Depends(get_current_user)):
    filters = {"status": f"eq.{status}"} if status else {}
    return {"items": await query(user, "approval_requests", params=owner_filter(
        user, **filters, order="created_at.desc", limit=limit
    ))}


@router.post("/approvals/{approval_id}/decision")
async def decide(approval_id: UUID, payload: ApprovalDecision, user: CurrentUser = Depends(get_current_user)):
    # RPC checks auth.uid, takes an exclusive row lock and appends one audit record.
    return require_one(await rpc(user, "decide_approval", {
        "p_approval_id": str(approval_id),
        "p_decision": payload.decision,
        "p_note": payload.note,
    }), "Approval not found")


@router.get("/audit")
async def audit(limit: int = Query(50, ge=1, le=100), user: CurrentUser = Depends(get_current_user)):
    return {"items": await query(user, "operation_audit_events", params=owner_filter(
        user, select="id,approval_id,action_type,decision,actor_id,created_at",
        order="created_at.desc", limit=limit,
    ))}


@router.get("/analytics")
async def analytics(user: CurrentUser = Depends(get_current_user)):
    # Capped, owner-scoped aggregates. Not a complete data warehouse.
    tickets = await query(user, "tickets", params=owner_filter(user, select="id,status", limit=500))
    runs = await query(user, "agent_runs", params=owner_filter(
        user, select="id,duration_ms", order="created_at.desc", limit=500
    ))
    approvals = await query(user, "approval_requests", params=owner_filter(
        user, select="id,status,action_type", limit=500
    ))
    total_ms = sum(int(run.get("duration_ms") or 0) for run in runs)
    return {
        "scanned_limit": 500,
        "tickets": len(tickets),
        "open_tickets": sum(ticket["status"] in ("open", "in_progress") for ticket in tickets),
        "resolved_tickets": sum(ticket["status"] in ("resolved", "closed") for ticket in tickets),
        "investigations": len(runs),
        "avg_run_ms": round(total_ms / len(runs)) if runs else 0,
        "pending_approvals": sum(row["status"] == "pending" for row in approvals),
        "approved_actions": sum(row["status"] == "approved" for row in approvals),
        "refunds_issued": 0,
        "real_email_sent": 0,
        "notice": "Approved records are not real payment refunds or outgoing emails.",
    }
