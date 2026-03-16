# Recommendation System

This repository has been migrated from **ASP.NET Core + Blazor** to:

- **FastAPI** for the backend (`backend_fastapi/`)
- **Next.js** for the frontend (`frontend_nextjs/`)

## Backend (FastAPI)

```bash
cd backend_fastapi
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Frontend (Next.js)

```bash
cd frontend_nextjs
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL` if backend is not at `http://localhost:8000`.

## Notes

- The FastAPI service keeps endpoint compatibility with existing routes (`/api/products`, `/api/categories`, `/api/orders`, `/api/cart`, etc.).
- The Next.js UI includes a migration demo page that lists categories/products and interacts with cart APIs.
