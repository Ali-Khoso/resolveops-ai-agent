"""Versioned REST endpoints for local Phase 1 testing."""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.agents.support_agent import answer
from app.tools.orders import get_order_status, list_orders

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["ResolveOps"])

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1500)

class ChatResponse(BaseModel):
    answer: str
    mode: str

@router.get("/orders")
def orders():
    return {"orders": list_orders(), "demo_data": True}

@router.get("/orders/{order_id}")
def order_detail(order_id: str):
    result = get_order_status(order_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order": result, "demo_data": True}

@router.post("/agent/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be blank")
    try:
        response, mode = answer(payload.message.strip())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Agent request failed")
        raise HTTPException(status_code=502, detail="Agent is temporarily unavailable") from exc
    return ChatResponse(answer=response, mode=mode)
