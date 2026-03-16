from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from fastapi_recommendation import RecommendationEngine, RecommendationService
from fastapi_recommendation.models import RecommendationRequest
from fastapi_recommendation.service import RecommendationDataSource

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from fastapi_recommendation.main import app


def _now(days_ago: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def _payload() -> dict:
    return {
        "user_id": 1,
        "top_k": 3,
        "products": [
            {"id": 1, "name": "Phone", "category_id": 1, "tags": ["mobile"], "is_active": True},
            {"id": 2, "name": "Case", "category_id": 1, "tags": ["accessory"], "is_active": True},
            {"id": 3, "name": "Shoes", "category_id": 2, "tags": ["sport"], "is_active": True},
            {"id": 4, "name": "Headset", "category_id": 1, "tags": ["audio"], "is_active": True},
        ],
        "interactions": [
            {"user_id": 1, "product_id": 1, "event_type": "view", "created_at": _now(1)},
            {"user_id": 1, "product_id": 1, "event_type": "click", "created_at": _now(1)},
            {"user_id": 2, "product_id": 1, "event_type": "purchase", "created_at": _now(2)},
            {"user_id": 2, "product_id": 2, "event_type": "purchase", "created_at": _now(2)},
            {"user_id": 3, "product_id": 1, "event_type": "cart", "created_at": _now(3)},
            {"user_id": 3, "product_id": 4, "event_type": "cart", "created_at": _now(3)},
        ],
        "cart_items": [],
        "order_items": [{"user_id": 1, "product_id": 1, "created_at": _now(0)}],
    }


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_recommendation_endpoint():
    client = TestClient(app)
    response = client.post("/v1/recommendations", json=_payload())
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(item["product_id"] != 1 for item in data)
    assert data[0]["product_id"] in {2, 4}


def test_candidate_filtering_and_exclusions():
    engine = RecommendationEngine()
    payload = RecommendationRequest(
        **{
            **_payload(),
            "candidate_product_ids": [2, 3],
            "exclude_product_ids": [2],
        }
    )
    results = engine.recommend(payload)
    assert len(results) == 1
    assert results[0].product_id == 3


class _InMemorySource(RecommendationDataSource):
    def list_products(self):
        return RecommendationRequest(**_payload()).products

    def list_user_interactions(self, user_id: int):
        return RecommendationRequest(**_payload()).interactions

    def list_cart_items(self, user_id: int):
        return RecommendationRequest(**_payload()).cart_items

    def list_order_items(self, user_id: int):
        return RecommendationRequest(**_payload()).order_items


def test_service_wrapper_integration():
    service = RecommendationService(engine=RecommendationEngine(), data_source=_InMemorySource())
    results = service.recommend_for_user(user_id=1, top_k=2)
    assert len(results) == 2
    assert all(item.product_id != 1 for item in results)
