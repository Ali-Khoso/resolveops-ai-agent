"""FastAPI entrypoint for ResolveOps Phase 1."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.knowledge import router as knowledge_router
from app.api.workspace import router as workspace_router
from app.core.config import agent_mode

app = FastAPI(title="ResolveOps AI Agent", version="0.1.0", description="Local Phase 1 demo; no real order or refund actions")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)
app.include_router(knowledge_router)
app.include_router(workspace_router)

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "ResolveOps API", "agent_mode": agent_mode(), "demo_data": True}
