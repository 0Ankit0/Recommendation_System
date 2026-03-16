from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import combinations
from math import exp

from .models import CartItem, OrderItem, Product, RecommendationRequest, RecommendationResult, UserEvent


@dataclass(frozen=True)
class EngineConfig:
    event_weights: dict[str, float] = field(
        default_factory=lambda: {
            "view": 1.0,
            "click": 2.0,
            "search": 1.5,
            "comment": 2.5,
            "cart": 3.0,
            "purchase": 4.0,
        }
    )
    co_occurrence_weight: float = 0.35
    category_weight: float = 0.45
    popularity_weight: float = 0.20
    recency_half_life_days: int = 14


class RecommendationEngine:
    """Production-oriented hybrid recommendation engine.

    Strategy:
    1) Normalize all signals into events.
    2) Build user category affinity and item co-occurrence graph.
    3) Score candidates with weighted blend of:
       - personalized item similarity
       - category affinity
       - global popularity
    4) Exclude already-purchased/carted items unless explicitly requested.
    """

    def __init__(self, config: EngineConfig | None = None) -> None:
        self.config = config or EngineConfig()

    def recommend(self, request: RecommendationRequest) -> list[RecommendationResult]:
        products_by_id = {p.id: p for p in request.products if p.is_active}
        if not products_by_id:
            return []

        candidate_ids = set(request.candidate_product_ids or products_by_id.keys())
        candidate_ids &= set(products_by_id.keys())

        all_events = self._normalize_events(request.interactions, request.cart_items, request.order_items)
        filtered_events = [e for e in all_events if e.product_id in products_by_id]
        user_events = [e for e in filtered_events if e.user_id == request.user_id]

        auto_excluded = {e.product_id for e in user_events if e.event_type in {"cart", "purchase"}}
        excluded_ids = set(request.exclude_product_ids) | auto_excluded

        if not user_events:
            return self._popularity_fallback(filtered_events, candidate_ids, excluded_ids, request.top_k)

        category_affinity = self._category_affinity(user_events, products_by_id)
        co_matrix = self._co_occurrence(filtered_events)
        popularity = self._popularity_scores(filtered_events)

        scores: dict[int, float] = defaultdict(float)
        reasons: dict[int, list[str]] = defaultdict(list)

        for event in user_events:
            source_product = products_by_id.get(event.product_id)
            if source_product is None:
                continue

            base_event_weight = self.config.event_weights[event.event_type]
            recency_multiplier = self._recency_decay(event.created_at)
            source_strength = base_event_weight * recency_multiplier

            for target_pid, normalized_co_score in co_matrix.get(source_product.id, {}).items():
                if target_pid not in candidate_ids:
                    continue
                scores[target_pid] += normalized_co_score * source_strength * self.config.co_occurrence_weight
                reasons[target_pid].append(f"similar-to-{source_product.id}")

        for candidate_pid in candidate_ids:
            product = products_by_id[candidate_pid]
            category_score = category_affinity[product.category_id] * self.config.category_weight
            popularity_score = popularity.get(candidate_pid, 0.0) * self.config.popularity_weight
            scores[candidate_pid] += category_score + popularity_score

            if category_score > 0:
                reasons[candidate_pid].append(f"category-{product.category_id}-affinity")
            if popularity_score > 0:
                reasons[candidate_pid].append("globally-popular")

        ranked = sorted(
            (
                RecommendationResult(
                    product_id=pid,
                    score=round(score, 6),
                    reasons=sorted(set(reasons[pid])) or ["hybrid-score"],
                )
                for pid, score in scores.items()
                if pid not in excluded_ids
            ),
            key=lambda row: (-row.score, row.product_id),
        )

        if ranked:
            return ranked[: request.top_k]
        return self._popularity_fallback(filtered_events, candidate_ids, excluded_ids, request.top_k)

    def _normalize_events(
        self,
        interactions: list[UserEvent],
        cart_items: list[CartItem],
        order_items: list[OrderItem],
    ) -> list[UserEvent]:
        events = list(interactions)

        events.extend(
            UserEvent(
                user_id=item.user_id,
                product_id=item.product_id,
                event_type="cart",
                created_at=item.created_at,
            )
            for item in cart_items
        )
        events.extend(
            UserEvent(
                user_id=item.user_id,
                product_id=item.product_id,
                event_type="purchase",
                created_at=item.created_at,
            )
            for item in order_items
        )
        return events

    def _category_affinity(self, user_events: list[UserEvent], products: dict[int, Product]) -> Counter:
        affinity = Counter()
        for event in user_events:
            product = products.get(event.product_id)
            if not product:
                continue
            affinity[product.category_id] += self.config.event_weights[event.event_type] * self._recency_decay(event.created_at)
        return affinity

    def _co_occurrence(self, events: list[UserEvent]) -> dict[int, dict[int, float]]:
        by_user: dict[int, set[int]] = defaultdict(set)
        for event in events:
            by_user[event.user_id].add(event.product_id)

        matrix: dict[int, dict[int, float]] = defaultdict(lambda: defaultdict(float))
        for products in by_user.values():
            for a, b in combinations(sorted(products), 2):
                matrix[a][b] += 1.0
                matrix[b][a] += 1.0

        for source_pid, neighbors in matrix.items():
            total = sum(neighbors.values()) or 1.0
            for neighbor_pid in list(neighbors):
                neighbors[neighbor_pid] = neighbors[neighbor_pid] / total
        return matrix

    def _popularity_scores(self, events: list[UserEvent]) -> dict[int, float]:
        scores = defaultdict(float)
        for event in events:
            scores[event.product_id] += self.config.event_weights[event.event_type]
        total = sum(scores.values()) or 1.0
        return {pid: score / total for pid, score in scores.items()}

    def _popularity_fallback(
        self,
        events: list[UserEvent],
        candidate_ids: set[int],
        excluded_ids: set[int],
        top_k: int,
    ) -> list[RecommendationResult]:
        popularity = self._popularity_scores(events)
        ranked_ids = sorted(candidate_ids, key=lambda pid: (-popularity.get(pid, 0.0), pid))
        return [
            RecommendationResult(
                product_id=pid,
                score=round(popularity.get(pid, 0.0), 6),
                reasons=["popularity-fallback"],
            )
            for pid in ranked_ids
            if pid not in excluded_ids
        ][:top_k]

    def _recency_decay(self, created_at: datetime) -> float:
        now = datetime.now(timezone.utc)
        timestamp = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
        elapsed_days = max((now - timestamp).days, 0)
        decay_factor = exp(-elapsed_days / max(self.config.recency_half_life_days, 1))
        return max(decay_factor, 0.05)
