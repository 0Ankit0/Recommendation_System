from __future__ import annotations

from fastapi import FastAPI

from .engine import RecommendationEngine
from .models import RecommendationRequest, RecommendationResult

app = FastAPI(
    title="Recommendation System API",
    version="1.1.0",
    description="Hybrid recommendation service that can be embedded or consumed over HTTP.",
)
engine = RecommendationEngine()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/recommendations", response_model=list[RecommendationResult])
def recommend(payload: RecommendationRequest) -> list[RecommendationResult]:
    return engine.recommend(payload)
