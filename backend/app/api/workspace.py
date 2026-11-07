"""Authenticated Phase 2 APIs. Supabase RLS is the final authorization boundary."""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel

from app.core.supabase import CurrentUser, get_current_user
from app.models.workspace import (
    CustomerCreate, CustomerUpdate, OrderCreate, OrderUpdate, ProfileUpdate,
    TicketCreate, TicketUpdate, TicketMessageCreate,
)
from app.services.postgrest import owner_filter, query

router = APIRouter(prefix="/api/v1/workspace", tags=["Workspace (authenticated)"])


def require_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise HTTPException(status_code=404, detail="Record not found")
    return rows[0]


def pagination(limit: int, offset: int) -> dict[str, int | str]:
    return {"limit": limit, "offset": offset, "order": "created_at.desc"}


def only_changes(model: BaseModel) -> dict[str, Any]:
    changes = model.model_dump(exclude_unset=True, mode="json")
    if not changes:
        raise HTTPException(status_code=422, detail="At least one field must be provided")
    return changes


@router.get("/me")
async def me(user: CurrentUser = Depends(get_current_user)):
    rows = await query(user, "profiles", params={"id": f"eq.{user.id}", "select": "id,display_name,role,created_at"})
    return {"user": {"id": user.id, "email": user.email}, "profile": require_row(rows)}


@router.patch("/me")
async def update_me(payload: ProfileUpdate, user: CurrentUser = Depends(get_current_user)):
    rows = await query(user, "profiles", method="PATCH", params={"id": f"eq.{user.id}"}, data=payload.model_dump())
    return require_row(rows)


@router.get("/customers")
async def list_customers(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                         user: CurrentUser = Depends(get_current_user)):
    rows = await query(user, "customers", params=owner_filter(user, **pagination(limit, offset)))
    return {"items": rows}


@router.post("/customers", status_code=status.HTTP_201_CREATED)
async def create_customer(payload: CustomerCreate, user: CurrentUser = Depends(get_current_user)):
    body = {**payload.model_dump(mode="json", exclude_none=True), "owner_id": user.id}
    return require_row(await query(user, "customers", method="POST", data=body))


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: UUID, user: CurrentUser = Depends(get_current_user)):
    rows = await query(user, "customers", params=owner_filter(user, id=f"eq.{customer_id}"))
    return require_row(rows)


@router.patch("/customers/{customer_id}")
async def update_customer(customer_id: UUID, payload: CustomerUpdate, user: CurrentUser = Depends(get_current_user)):
    rows = await query(user, "customers", method="PATCH", params=owner_filter(user, id=f"eq.{customer_id}"), data=only_changes(payload))
    return require_row(rows)


@router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: UUID, user: CurrentUser = Depends(get_current_user)):
    rows = await query(user, "customers", method="DELETE", params=owner_filter(user, id=f"eq.{customer_id}"))
    require_row(rows)
    return Response(status_code=204)


@router.get("/orders")
async def list_orders(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                      user: CurrentUser = Depends(get_current_user)):
    return {"items": await query(user, "orders", params=owner_filter(user, **pagination(limit, offset)))}


@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order(payload: OrderCreate, user: CurrentUser = Depends(get_current_user)):
    body = {**payload.model_dump(mode="json", exclude_none=True), "owner_id": user.id}
    return require_row(await query(user, "orders", method="POST", data=body))


@router.get("/orders/{order_id}")
async def get_order(order_id: UUID, user: CurrentUser = Depends(get_current_user)):
    return require_row(await query(user, "orders", params=owner_filter(user, id=f"eq.{order_id}")))


@router.patch("/orders/{order_id}")
async def update_order(order_id: UUID, payload: OrderUpdate, user: CurrentUser = Depends(get_current_user)):
    return require_row(await query(user, "orders", method="PATCH", params=owner_filter(user, id=f"eq.{order_id}"), data=only_changes(payload)))


@router.get("/tickets")
async def list_tickets(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                       user: CurrentUser = Depends(get_current_user)):
    return {"items": await query(user, "tickets", params=owner_filter(user, **pagination(limit, offset)))}


@router.post("/tickets", status_code=status.HTTP_201_CREATED)
async def create_ticket(payload: TicketCreate, user: CurrentUser = Depends(get_current_user)):
    body = {**payload.model_dump(mode="json", exclude_none=True), "owner_id": user.id}
    return require_row(await query(user, "tickets", method="POST", data=body))


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: UUID, user: CurrentUser = Depends(get_current_user)):
    return require_row(await query(user, "tickets", params=owner_filter(user, id=f"eq.{ticket_id}")))


@router.patch("/tickets/{ticket_id}")
async def update_ticket(ticket_id: UUID, payload: TicketUpdate, user: CurrentUser = Depends(get_current_user)):
    return require_row(await query(user, "tickets", method="PATCH", params=owner_filter(user, id=f"eq.{ticket_id}"), data=only_changes(payload)))


@router.get("/tickets/{ticket_id}/messages")
async def list_messages(ticket_id: UUID, user: CurrentUser = Depends(get_current_user)):
    # Explicit parent check avoids exposing a misleading empty list for nonexistent tickets.
    require_row(await query(user, "tickets", params=owner_filter(user, id=f"eq.{ticket_id}")))
    items = await query(user, "ticket_messages", params=owner_filter(user, ticket_id=f"eq.{ticket_id}", order="created_at.asc", limit=100))
    return {"items": items}


@router.post("/tickets/{ticket_id}/messages", status_code=status.HTTP_201_CREATED)
async def add_message(ticket_id: UUID, payload: TicketMessageCreate,
                      user: CurrentUser = Depends(get_current_user)):
    require_row(await query(user, "tickets", params=owner_filter(user, id=f"eq.{ticket_id}")))
    body = {"owner_id": user.id, "ticket_id": str(ticket_id), "author_id": user.id,
            "sender_type": "agent", "content": payload.content}
    return require_row(await query(user, "ticket_messages", method="POST", data=body))
