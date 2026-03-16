import os

os.environ["DATABASE_URL"] = "sqlite:///./test_recommendation.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-123456"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def register_and_login(user_id: str, email: str, password: str, is_admin: bool = False) -> str:
    register_response = client.post(
        "/api/auth/register",
        json={"user_id": user_id, "email": email, "password": password, "is_admin": is_admin},
    )
    assert register_response.status_code == 201

    login_response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def test_admin_only_catalog_write_and_public_read():
    admin_token = register_and_login("admin-user", "admin@example.com", "admin-pass-123", is_admin=True)
    user_token = register_and_login("normal-user", "user@example.com", "user-pass-123")

    category_response = client.post(
        "/api/categories",
        json={"name": "Electronics"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert category_response.status_code == 201
    category_id = category_response.json()["id"]

    denied_response = client.post(
        "/api/products",
        json={
            "name": "Headphones",
            "description": "Noise cancelling",
            "price": 120,
            "stock_quantity": 10,
            "category_id": category_id,
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert denied_response.status_code == 403

    success_response = client.post(
        "/api/products",
        json={
            "name": "Headphones",
            "description": "Noise cancelling",
            "price": 120,
            "stock_quantity": 10,
            "category_id": category_id,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert success_response.status_code == 201

    read_response = client.get("/api/products")
    assert read_response.status_code == 200
    assert len(read_response.json()) >= 1


def test_authentication_required_on_protected_endpoint():
    unauth_response = client.post("/api/cart/add", json={"product_id": 1, "quantity": 2})
    assert unauth_response.status_code == 403
