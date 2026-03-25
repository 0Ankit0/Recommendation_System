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
            "like": 3.0,
            "save": 2.5,
            "share": 2.0,
        }
    )
    co_occurrence_weight: float = 0.35
    content_weight: float = 0.45
    popularity_weight: float = 0.20
    recency_half_life_days: int = 14
    preference_boost: float = 0.3
    metadata_completeness_threshold: float = 0.4


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
        products_by_id = {
            p.id: p
            for p in request.products
            if p.is_active and p.metadata_completeness >= self.config.metadata_completeness_threshold
        }
        if not products_by_id:
            return []

        candidate_ids = set(request.candidate_product_ids or products_by_id.keys())
        candidate_ids &= set(products_by_id.keys())

        all_events = self._normalize_events(request.interactions, request.cart_items, request.order_items)
        filtered_events = [e for e in all_events if e.product_id in products_by_id]
        user_events = [e for e in filtered_events if e.user_id == request.user_id]

        auto_excluded = {e.product_id for e in user_events if e.event_type in {"cart", "purchase"}}
        if request.exclude_viewed:
            auto_excluded.update(e.product_id for e in user_events if e.event_type in {"view", "click", "search"})
        excluded_ids = set(request.exclude_product_ids) | auto_excluded

        if len(user_events) < request.min_personalization_events:
            return self._popularity_fallback(
                filtered_events,
                candidate_ids,
                excluded_ids,
                request.top_k,
                products_by_id,
                request,
            )

        category_affinity = self._category_affinity(user_events, products_by_id)
        tag_affinity = self._tag_affinity(user_events, products_by_id)
        co_matrix = self._co_occurrence(filtered_events)
        popularity = self._popularity_scores(filtered_events)

        scores: dict[int, float] = defaultdict(float)
        reasons: dict[int, list[str]] = defaultdict(list)

        for event in user_events:
            source_product = products_by_id.get(event.product_id)
            if source_product is None:
                continue

            base_event_weight = self.config.event_weights[event.event_type] * event.value
            recency_multiplier = self._recency_decay(event.created_at)
            source_strength = base_event_weight * recency_multiplier

            if request.algorithm in {"collaborative", "hybrid"}:
                for target_pid, normalized_co_score in co_matrix.get(source_product.id, {}).items():
                    if target_pid not in candidate_ids:
                        continue
                    scores[target_pid] += normalized_co_score * source_strength * self.config.co_occurrence_weight
                    reasons[target_pid].append(f"similar-to-{source_product.id}")

        for candidate_pid in candidate_ids:
            product = products_by_id[candidate_pid]
            content_score = 0.0
            popularity_score = 0.0
            novelty_score = 0.0

            if request.algorithm in {"content_based", "hybrid"}:
                content_score = (
                    category_affinity[product.category_id] + self._tag_overlap_score(product, tag_affinity)
                ) * self.config.content_weight
            if request.algorithm in {"collaborative", "hybrid", "content_based"}:
                popularity_score = popularity.get(candidate_pid, 0.0) * self.config.popularity_weight
                novelty_score = (1.0 - popularity.get(candidate_pid, 0.0)) * request.exploration_rate * 0.1

            scores[candidate_pid] += content_score + popularity_score + novelty_score
            if product.category_id in request.category_preferences:
                scores[candidate_pid] += self.config.preference_boost
                reasons[candidate_pid].append("matches-user-preference")

            if content_score > 0:
                reasons[candidate_pid].append(f"category-{product.category_id}-affinity")
            if popularity_score > 0:
                reasons[candidate_pid].append("globally-popular")
            if novelty_score > 0:
                reasons[candidate_pid].append("exploration-boost")

        ranked = sorted(
            (
                RecommendationResult(
                    product_id=pid,
                    score=round(score, 6),
                    reasons=sorted(set(reasons[pid])) or ["hybrid-score"],
                    explanation=self._build_explanation(sorted(set(reasons[pid])) or ["hybrid-score"], request.explain),
                )
                for pid, score in scores.items()
                if pid not in excluded_ids
            ),
            key=lambda row: (-row.score, row.product_id),
        )
        ranked = self._apply_diversity(ranked, products_by_id, request.max_per_category)

        if ranked:
            return ranked[: request.top_k]
        return self._popularity_fallback(
            filtered_events,
            candidate_ids,
            excluded_ids,
            request.top_k,
            products_by_id,
            request,
        )

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
            affinity[product.category_id] += (
                self.config.event_weights[event.event_type]
                * event.value
                * self._recency_decay(event.created_at)
            )
        return affinity

    def _tag_affinity(self, user_events: list[UserEvent], products: dict[int, Product]) -> Counter:
        affinity = Counter()
        for event in user_events:
            product = products.get(event.product_id)
            if not product:
                continue
            weight = self.config.event_weights[event.event_type] * event.value * self._recency_decay(event.created_at)
            for tag in product.tags:
                affinity[tag.lower()] += weight
        return affinity

    def _co_occurrence(self, events: list[UserEvent]) -> dict[int, dict[int, float]]:
        by_user: dict[str, set[int]] = defaultdict(set)
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
            scores[event.product_id] += (
                self.config.event_weights[event.event_type]
                * event.value
                * self._recency_decay(event.created_at)
            )
        total = sum(scores.values()) or 1.0
        return {pid: score / total for pid, score in scores.items()}

    def _popularity_fallback(
        self,
        events: list[UserEvent],
        candidate_ids: set[int],
        excluded_ids: set[int],
        top_k: int,
        products_by_id: dict[int, Product],
        request: RecommendationRequest,
    ) -> list[RecommendationResult]:
        popularity = self._popularity_scores(events)
        ranked_ids = sorted(
            candidate_ids,
            key=lambda pid: (
                -(
                    popularity.get(pid, 0.0)
                    + (self.config.preference_boost if products_by_id[pid].category_id in request.category_preferences else 0.0)
                ),
                pid,
            ),
        )
        results = [
            RecommendationResult(
                product_id=pid,
                score=round(popularity.get(pid, 0.0), 6),
                reasons=["popularity-fallback"],
                explanation=self._build_explanation(["popularity-fallback"], request.explain),
            )
            for pid in ranked_ids
            if pid not in excluded_ids
        ]
        diversified = self._apply_diversity(results, products_by_id, request.max_per_category)
        return diversified[:top_k]

    def _recency_decay(self, created_at: datetime) -> float:
        now = datetime.now(timezone.utc)
        timestamp = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
        elapsed_days = max((now - timestamp).days, 0)
        decay_factor = exp(-elapsed_days / max(self.config.recency_half_life_days, 1))
        return max(decay_factor, 0.05)

    def _tag_overlap_score(self, product: Product, tag_affinity: Counter) -> float:
        if not product.tags:
            return 0.0
        return sum(tag_affinity[tag.lower()] for tag in product.tags) / len(product.tags)

    def _apply_diversity(
        self,
        ranked: list[RecommendationResult],
        products_by_id: dict[int, Product],
        max_per_category: int,
    ) -> list[RecommendationResult]:
        category_counts: Counter = Counter()
        diversified: list[RecommendationResult] = []
        overflow: list[RecommendationResult] = []

        for result in ranked:
            category_id = products_by_id[result.product_id].category_id
            if category_counts[category_id] < max_per_category:
                diversified.append(result)
                category_counts[category_id] += 1
            else:
                overflow.append(result)

        diversified.extend(overflow)
        return diversified

    def _build_explanation(self, reasons: list[str], explain: bool) -> str | None:
        if not explain:
            return None
        normalized = set(reasons)
        fragments: list[str] = []
        if any(reason.startswith("similar-to-") for reason in normalized):
            fragments.append("Similar users engaged with related items.")
        if any(reason.startswith("category-") for reason in normalized):
            fragments.append("It matches categories you recently engaged with.")
        if "globally-popular" in normalized:
            fragments.append("It is trending across the catalog.")
        if "matches-user-preference" in normalized:
            fragments.append("It aligns with your saved preferences.")
        if "exploration-boost" in normalized:
            fragments.append("It broadens your feed with less common items.")
        if "popularity-fallback" in normalized:
            fragments.append("It is popular while we learn more about your interests.")
        return " ".join(fragments) or "Recommended from your recent activity."
