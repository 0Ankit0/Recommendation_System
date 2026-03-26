from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fastapi.testclient import TestClient

from backend_fastapi.app.database import Base, get_db
from backend_fastapi.app.main import app
from backend_fastapi.app.models import Address, Category, InteractionType, Product, UserInteraction


def _seed(session):
    electronics = Category(category_id=1, name="Electronics")
    sports = Category(category_id=2, name="Sports")
    session.add_all([electronics, sports])
    session.add_all(
        [
            Product(product_id=1, name="Phone", description="electronics mobile phone", price=699.0, stock_quantity=10, category_id=1),
            Product(product_id=2, name="Case", description="electronics phone case", price=29.0, stock_quantity=20, category_id=1),
            Product(product_id=3, name="Shoes", description="sports running shoes", price=99.0, stock_quantity=15, category_id=2),
            Product(product_id=4, name="Headset", description="electronics audio headset", price=199.0, stock_quantity=8, category_id=1),
        ]
    )
    session.add(Address(address_id=1, street="1 Main St", city="Metropolis", state="CA", postal_code="90001", country="US", user_id="demo-user"))
    session.add_all(
        [
            UserInteraction(user_id="demo-user", product_id=1, interaction_type=InteractionType.View),
            UserInteraction(user_id="demo-user", product_id=1, interaction_type=InteractionType.Click),
            UserInteraction(user_id="demo-user", product_id=2, interaction_type=InteractionType.AddToCart),
            UserInteraction(user_id="other-user", product_id=1, interaction_type=InteractionType.Purchase),
            UserInteraction(user_id="other-user", product_id=4, interaction_type=InteractionType.Purchase),
            UserInteraction(user_id="third-user", product_id=1, interaction_type=InteractionType.Purchase),
            UserInteraction(user_id="third-user", product_id=2, interaction_type=InteractionType.Purchase),
        ]
    )
    session.commit()


def _build_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    _seed(session)

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), session


def test_event_preferences_and_recommendations_flow():
    client, session = _build_client()

    event_payload = {
        "eventId": "evt-demo-1",
        "userId": "demo-user",
        "itemId": 4,
        "actionType": "view",
        "context": {"source": "test"}
    }
    first = client.post("/v1/events", json=event_payload)
    duplicate = client.post("/v1/events", json=event_payload)
    assert first.status_code == 202
    assert duplicate.status_code == 202
    assert session.query(UserInteraction).filter(UserInteraction.external_event_id == "evt-demo-1").count() == 1

    preference_response = client.put(
        "/v1/users/demo-user/preferences",
        json={
            "categories": ["Electronics"],
            "diversity": 0.4,
            "recency_bias": 0.6,
            "excludeViewed": True,
            "algorithm": "hybrid",
            "maxPerCategory": 2
        },
    )
    assert preference_response.status_code == 200
    assert preference_response.json()["categories"] == ["Electronics"]

    recommendation_response = client.get("/v1/recommendations/demo-user?limit=3&explain=true")
    assert recommendation_response.status_code == 200
    payload = recommendation_response.json()
    assert payload["userId"] == "demo-user"
    assert payload["metadata"]["algorithm"] == "hybrid"
    assert len(payload["recommendations"]) >= 1
    assert all(row["itemId"] != 2 for row in payload["recommendations"])

    batch_response = client.post(
        "/v1/recommendations/batch",
        json={"userIds": ["demo-user", "other-user"], "limit": 2, "algorithm": "collaborative", "explain": False},
    )
    assert batch_response.status_code == 200
    assert len(batch_response.json()["results"]) == 2


def test_training_metrics_and_experiment_support():
    client, _session = _build_client()

    collaborative = client.post(
        "/v1/models/train",
        json={"algorithm": "collaborative", "hyperparameters": {"neighbors": 20}},
    )
    content_based = client.post(
        "/v1/models/train",
        json={"algorithm": "content_based", "hyperparameters": {"topTags": 10}},
    )
    assert collaborative.status_code == 201
    assert content_based.status_code == 201

    collaborative_model_id = collaborative.json()["modelId"]
    metrics_response = client.get(f"/v1/models/{collaborative_model_id}/metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()["metrics"]
    assert "precision@10" in metrics
    assert "diversity" in metrics

    experiment_response = client.post(
        "/v1/experiments",
        json={
            "name": "docs-aligned-test",
            "controlModelId": collaborative_model_id,
            "variantModelId": content_based.json()["modelId"],
            "trafficSplit": {"control": 0.5, "variant": 0.5},
            "metrics": ["ctr", "conversion_rate"]
        },
    )
    assert experiment_response.status_code == 201

    recommendation_response = client.get("/v1/recommendations/demo-user?limit=3")
    assert recommendation_response.status_code == 200
    metadata = recommendation_response.json()["metadata"]
    assert metadata["experimentId"] == experiment_response.json()["experimentId"]
    assert metadata["variant"] in {"control", "variant"}
