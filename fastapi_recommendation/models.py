from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


AlgorithmType = Literal["collaborative", "content_based", "hybrid"]
EventType = Literal["view", "click", "search", "comment", "cart", "purchase", "like", "save", "share"]


def _normalize_user_id(value: str | int) -> str:
    if value is None:
        raise ValueError("user_id is required")
    text = str(value).strip()
    if not text:
        raise ValueError("user_id must not be blank")
    return text


class Product(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    category_id: int = Field(gt=0)
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True
    metadata_completeness: float = Field(default=1.0, ge=0.0, le=1.0)


class UserEvent(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    user_id: str = Field(min_length=1)
    product_id: int = Field(gt=0)
    event_type: EventType
    created_at: datetime
    value: float = Field(default=1.0, gt=0.0)
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("user_id", mode="before")
    @classmethod
    def _normalize_user_id(cls, value: str | int) -> str:
        return _normalize_user_id(value)


class CartItem(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    user_id: str = Field(min_length=1)
    product_id: int = Field(gt=0)
    created_at: datetime

    @field_validator("user_id", mode="before")
    @classmethod
    def _normalize_user_id(cls, value: str | int) -> str:
        return _normalize_user_id(value)


class OrderItem(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    user_id: str = Field(min_length=1)
    product_id: int = Field(gt=0)
    created_at: datetime

    @field_validator("user_id", mode="before")
    @classmethod
    def _normalize_user_id(cls, value: str | int) -> str:
        return _normalize_user_id(value)


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    user_id: str = Field(min_length=1)
    products: list[Product] = Field(min_length=1)
    interactions: list[UserEvent] = Field(default_factory=list)
    cart_items: list[CartItem] = Field(default_factory=list)
    order_items: list[OrderItem] = Field(default_factory=list)
    top_k: int = Field(default=10, ge=1, le=100)
    candidate_product_ids: list[int] | None = None
    exclude_product_ids: list[int] = Field(default_factory=list)
    algorithm: AlgorithmType = "hybrid"
    explain: bool = True
    min_personalization_events: int = Field(default=5, ge=1, le=100)
    max_per_category: int = Field(default=3, ge=1, le=10)
    exploration_rate: float = Field(default=0.15, ge=0.0, le=1.0)
    category_preferences: list[int] = Field(default_factory=list)
    exclude_viewed: bool = False
    recency_bias: float = Field(default=0.5, ge=0.0, le=1.0)
    model_version: str | None = None

    @field_validator("user_id", mode="before")
    @classmethod
    def _normalize_user_id(cls, value: str | int) -> str:
        return _normalize_user_id(value)

    @field_validator("candidate_product_ids")
    @classmethod
    def _validate_candidates(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return value
        unique = sorted(set(value))
        if any(pid <= 0 for pid in unique):
            raise ValueError("candidate_product_ids must contain positive integers")
        return unique

    @field_validator("category_preferences")
    @classmethod
    def _validate_category_preferences(cls, value: list[int]) -> list[int]:
        unique = sorted(set(value))
        if any(category_id <= 0 for category_id in unique):
            raise ValueError("category_preferences must contain positive integers")
        return unique


class RecommendationResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    product_id: int
    score: float
    reasons: list[str] = Field(default_factory=list)
    explanation: str | None = None
