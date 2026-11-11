"""Validated models for agent investigations and human review."""
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class InvestigationCreate(StrictModel):
    ticket_id: UUID
    question: str = Field(min_length=3, max_length=1500)

class ApprovalCreate(StrictModel):
    ticket_id: UUID
    run_id: UUID | None = None
    action_type: Literal["send_reply", "resolve_ticket", "refund_review"]
    draft_reply: str = Field(min_length=1, max_length=4000)
    reason: str = Field(min_length=3, max_length=1000)

class ApprovalDecision(StrictModel):
    decision: Literal["approved", "rejected"]
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def require_rejection_reason(self) -> "ApprovalDecision":
        if self.note is not None:
            self.note = self.note.strip() or None
        if self.decision == "rejected" and not self.note:
            raise ValueError("A rejection reason is required")
        return self
