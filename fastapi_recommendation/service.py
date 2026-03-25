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

    def list_user_interactions(self, user_id: int) -> list[UserEvent]: ...

    def list_cart_items(self, user_id: int) -> list[CartItem]: ...

    def list_order_items(self, user_id: int) -> list[OrderItem]: ...


@dataclass
class RecommendationService:
    engine: RecommendationEngine
    data_source: RecommendationDataSource

    def recommend_for_user(
        self,
        user_id: int,
        top_k: int = 10,
        candidate_product_ids: list[int] | None = None,
        exclude_product_ids: list[int] | None = None,
    ) -> list[RecommendationResult]:
        payload = RecommendationRequest(
            user_id=user_id,
            top_k=top_k,
            products=self.data_source.list_products(),
            interactions=self.data_source.list_user_interactions(user_id),
            cart_items=self.data_source.list_cart_items(user_id),
            order_items=self.data_source.list_order_items(user_id),
            candidate_product_ids=candidate_product_ids,
            exclude_product_ids=exclude_product_ids or [],
        )
        return self.engine.recommend(payload)
