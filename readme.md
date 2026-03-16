# Recommendation System (FastAPI)

This repository now contains a **FastAPI-based recommendation system** that is designed to be:
- deployable as an HTTP service, and
- embeddable as a Python module in another project.

## ✅ What is implemented

A hybrid recommendation engine that combines:
1. **Recency-aware interaction scoring** (`view`, `click`, `search`, `comment`, `cart`, `purchase`)
2. **Category affinity** (user preference per category)
3. **Item co-occurrence** (users who interacted with A also interacted with B)
4. **Global popularity fallback** (cold-start safe)

It also supports:
- excluding already purchased/carted products automatically
- explicit `exclude_product_ids`
- limiting candidate pool via `candidate_product_ids`
- deterministic tie-breaking for stable output

## Project layout

- `fastapi_recommendation/main.py` - FastAPI app
- `fastapi_recommendation/models.py` - API + engine schemas
- `fastapi_recommendation/engine.py` - `RecommendationEngine` and `EngineConfig`
- `fastapi_recommendation/service.py` - integration wrapper (`RecommendationService`) and data-source protocol
- `tests/test_recommender.py` - endpoint + engine + integration wrapper tests

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn fastapi_recommendation.main:app --host 0.0.0.0 --port 8000 --reload
```

Open:
- Swagger: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

## API usage

### `POST /v1/recommendations`

```json
{
  "user_id": 10,
  "top_k": 5,
  "candidate_product_ids": [2, 3, 4, 5],
  "exclude_product_ids": [4],
  "products": [
    { "id": 1, "name": "Phone", "category_id": 1, "tags": ["mobile"], "is_active": true },
    { "id": 2, "name": "Case", "category_id": 1, "tags": ["accessory"], "is_active": true }
  ],
  "interactions": [
    { "user_id": 10, "product_id": 1, "event_type": "view", "created_at": "2026-01-01T10:00:00Z" }
  ],
  "cart_items": [],
  "order_items": []
}
```

## Plug into another project (recommended)

Implement the `RecommendationDataSource` protocol in your app and call `RecommendationService`.

```python
from fastapi_recommendation import RecommendationEngine, RecommendationService
from fastapi_recommendation.models import Product, UserEvent, CartItem, OrderItem


class MyDataSource:
    def list_products(self) -> list[Product]:
        # map from your DB entities -> Product
        ...

    def list_user_interactions(self, user_id: int) -> list[UserEvent]:
        ...

    def list_cart_items(self, user_id: int) -> list[CartItem]:
        ...

    def list_order_items(self, user_id: int) -> list[OrderItem]:
        ...


service = RecommendationService(
    engine=RecommendationEngine(),
    data_source=MyDataSource(),
)

results = service.recommend_for_user(user_id=42, top_k=10)
```

This is the easiest path to integrating with another backend project because only the data-source adapter is project-specific.
