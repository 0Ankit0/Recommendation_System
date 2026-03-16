# FastAPI Backend

Production-style FastAPI backend for the recommendation system.

## Features implemented

- Full FastAPI migration for core commerce endpoints.
- SQLAlchemy models for catalog, cart, orders, payments, interactions, and users.
- JWT authentication (`/api/auth/register`, `/api/auth/login`, `/api/auth/me`).
- Role-based authorization (admin-only write operations for catalog endpoints).
- User-scoped access controls for cart, orders, interactions, and addresses.
- Input validation with Pydantic constraints.
- Security middleware:
  - CORS allow-list via environment config
  - Trusted host middleware
  - GZip compression
- Configurable environment-driven settings with `pydantic-settings`.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Environment variables

- `DATABASE_URL` (default: `sqlite:///./recommendation.db`)
- `JWT_SECRET_KEY` (required in production)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (default: `60`)
- `ALLOWED_ORIGINS` (JSON list, e.g. `["http://localhost:3000"]`)
- `ENVIRONMENT` (default: `development`)
