"""Bound untrusted workflow runtime to avoid unlimited model/database waits."""
from __future__ import annotations
import os
from fastapi import HTTPException


def workflow_timeout_seconds() -> int:
    raw = os.getenv("GRAPH_TIMEOUT_SECONDS", "30")
    try:
        seconds = int(raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(503, "Invalid GRAPH_TIMEOUT_SECONDS configuration") from exc
    if not 5 <= seconds <= 120:
        raise HTTPException(503, "GRAPH_TIMEOUT_SECONDS must be between 5 and 120")
    return seconds
