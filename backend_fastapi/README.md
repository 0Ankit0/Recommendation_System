# FastAPI Backend

This backend replaces the ASP.NET Core API with FastAPI + SQLAlchemy.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Set `DATABASE_URL` to target PostgreSQL; default is local SQLite (`recommendation.db`).
