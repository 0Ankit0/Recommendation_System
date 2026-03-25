from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .engine import RecommendationEngine
from .models import CartItem, OrderItem, Product, RecommendationRequest, RecommendationResult, UserEvent


class RecommendationDataSource(Protocol):
    """Interface to integrate engine into another project.

    Implement this in your app (Django, Flask, FastAPI, .NET gateway, etc.)
    and pass it to RecommendationService.
    """

    def list_products(self) -> list[Product]: ...

    def list_user_interactions(self, user_id: str) -> list[UserEvent]: ...

    def list_cart_items(self, user_id: str) -> list[CartItem]: ...

    def list_order_items(self, user_id: str) -> list[OrderItem]: ...


@dataclass
class RecommendationService:
    engine: RecommendationEngine
    data_source: RecommendationDataSource

    def recommend_for_user(
        self,
        user_id: str | int,
        top_k: int = 10,
        candidate_product_ids: list[int] | None = None,
        exclude_product_ids: list[int] | None = None,
        **kwargs,
    ) -> list[RecommendationResult]:
        payload = RecommendationRequest(
            user_id=str(user_id),
            top_k=top_k,
            products=self.data_source.list_products(),
            interactions=self.data_source.list_user_interactions(str(user_id)),
            cart_items=self.data_source.list_cart_items(str(user_id)),
            order_items=self.data_source.list_order_items(str(user_id)),
            candidate_product_ids=candidate_product_ids,
            exclude_product_ids=exclude_product_ids or [],
            **kwargs,
        )
        return self.engine.recommend(payload)
