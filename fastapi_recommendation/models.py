from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


EventType = Literal["view", "click", "search", "comment", "cart", "purchase"]


class Product(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    category_id: int = Field(gt=0)
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True


class UserEvent(BaseModel):
    user_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    event_type: EventType
    created_at: datetime


class CartItem(BaseModel):
    user_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    created_at: datetime


class OrderItem(BaseModel):
    user_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    created_at: datetime


class RecommendationRequest(BaseModel):
    user_id: int = Field(gt=0)
    products: list[Product] = Field(min_length=1)
    interactions: list[UserEvent] = Field(default_factory=list)
    cart_items: list[CartItem] = Field(default_factory=list)
    order_items: list[OrderItem] = Field(default_factory=list)
    top_k: int = Field(default=10, ge=1, le=100)
    candidate_product_ids: list[int] | None = None
    exclude_product_ids: list[int] = Field(default_factory=list)

    @field_validator("candidate_product_ids")
    @classmethod
    def _validate_candidates(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return value
        unique = sorted(set(value))
        if any(pid <= 0 for pid in unique):
            raise ValueError("candidate_product_ids must contain positive integers")
        return unique


class RecommendationResult(BaseModel):
    product_id: int
    score: float
    reasons: list[str] = Field(default_factory=list)
