"""Request schemas. Identifiers and status values are strictly validated."""
from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CustomerCreate(StrictModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=32)


class CustomerUpdate(StrictModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=32)


OrderStatus = Literal["processing", "shipped", "delivered", "cancelled"]
TicketStatus = Literal["open", "in_progress", "resolved", "closed"]
Priority = Literal["low", "normal", "high", "urgent"]


class OrderCreate(StrictModel):
    customer_id: UUID
    item: str = Field(min_length=2, max_length=200)
    status: OrderStatus = "processing"
    tracking_number: str | None = Field(default=None, max_length=80)
    estimated_delivery: date | None = None


class OrderUpdate(StrictModel):
    status: OrderStatus | None = None
    tracking_number: str | None = Field(default=None, max_length=80)
    estimated_delivery: date | None = None


class TicketCreate(StrictModel):
    customer_id: UUID
    order_id: UUID | None = None
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=4000)
    priority: Priority = "normal"


class TicketUpdate(StrictModel):
    status: TicketStatus | None = None
    priority: Priority | None = None


class TicketMessageCreate(StrictModel):
    content: str = Field(min_length=1, max_length=4000)


class ProfileUpdate(StrictModel):
    display_name: str = Field(min_length=2, max_length=120)
