from __future__ import annotations

import hashlib
import json
import uuid
from collections import defaultdict
from datetime import UTC, datetime, timezone
from decimal import Decimal
from math import log2

from sqlalchemy import func
from sqlalchemy.orm import Session

from fastapi_recommendation import RecommendationEngine
from fastapi_recommendation.models import RecommendationRequest as EngineRecommendationRequest
from fastapi_recommendation.models import Product as EngineProduct
from fastapi_recommendation.models import RecommendationResult
from fastapi_recommendation.models import UserEvent as EngineUserEvent

from .models import Cart, Category, Experiment, MLModel, Order, Product, UserInteraction, UserPreference
from .schemas import UserPreferenceRequest


def _json_loads(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _json_dumps(value) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


class SQLRecommendationService:
    def __init__(self, db: Session, engine: RecommendationEngine | None = None) -> None:
        self.db = db
        self.engine = engine or RecommendationEngine()

    def recommend(
        self,
        user_id: str,
        *,
        top_k: int,
        algorithm: str | None = None,
        explain: bool = True,
    ) -> tuple[list[RecommendationResult], dict]:
        preference = self.get_or_create_preferences(user_id)
        active_experiment = self._get_active_experiment()
        selected_model = None
        experiment_metadata: dict[str, str] = {}

        if active_experiment and active_experiment.variants:
            selected_model, variant_name = self._select_experiment_model(active_experiment, user_id)
            algorithm = selected_model.algorithm
            experiment_metadata = {
                "experimentId": active_experiment.experiment_id,
                "variant": variant_name,
            }

        resolved_algorithm = algorithm or preference.algorithm or "hybrid"
        latest_model = selected_model or self._get_latest_model(resolved_algorithm)
        if latest_model:
            latest_model.last_used_at = datetime.now(UTC).replace(tzinfo=None)
            self.db.commit()

        payload = EngineRecommendationRequest(
            user_id=user_id,
            top_k=top_k,
            products=self._list_products(),
            interactions=self._list_interactions(),
            cart_items=self._list_cart_items(),
            order_items=self._list_order_items(),
            algorithm=resolved_algorithm,
            explain=explain,
            category_preferences=self._resolve_category_preferences(preference.categories_json),
            exclude_viewed=preference.exclude_viewed,
            recency_bias=preference.recency_bias,
            max_per_category=preference.max_per_category,
            exploration_rate=max(0.05, min(preference.diversity, 0.5)),
            model_version=latest_model.version if latest_model else "heuristic-live",
        )
        results = self.engine.recommend(payload)
        metadata = {
            "algorithm": resolved_algorithm,
            "modelVersion": latest_model.version if latest_model else "heuristic-live",
            **experiment_metadata,
        }
        return results, metadata

    def get_or_create_preferences(self, user_id: str) -> UserPreference:
        preference = self.db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if preference:
            return preference
        preference = UserPreference(user_id=user_id)
        self.db.add(preference)
        self.db.commit()
        self.db.refresh(preference)
        return preference

    def update_preferences(self, user_id: str, request: UserPreferenceRequest) -> UserPreference:
        preference = self.get_or_create_preferences(user_id)
        preference.categories_json = _json_dumps(request.categories)
        preference.diversity = request.diversity
        preference.recency_bias = request.recency_bias
        preference.exclude_viewed = request.exclude_viewed
        preference.algorithm = request.algorithm
        preference.max_per_category = request.max_per_category
        self.db.commit()
        self.db.refresh(preference)
        return preference

    def train_model(
        self,
        algorithm: str,
        hyperparameters: dict,
        data_range: dict | None = None,
    ) -> tuple[MLModel, dict]:
        interactions = self.db.query(UserInteraction).order_by(UserInteraction.interaction_time.asc()).all()
        metrics = self._evaluate_model(algorithm, interactions)
        version = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        model = MLModel(
            algorithm=algorithm,
            version=f"{algorithm}-{version}",
            hyperparameters_json=_json_dumps(hyperparameters),
            metrics_json=_json_dumps(metrics),
            status="registered",
        )
        self.db.add(model)
        self.db.flush()
        metadata = {"dataRange": data_range or {}, "interactionCount": len(interactions)}
        return model, metadata

    def _evaluate_model(self, algorithm: str, interactions: list[UserInteraction]) -> dict[str, float | int]:
        total_events = len(interactions)
        unique_users = len({row.user_id for row in interactions})
        unique_items = len({row.product_id for row in interactions})
        if total_events == 0 or unique_users == 0 or unique_items == 0:
            return {"precision@10": 0.0, "recall@10": 0.0, "ndcg@10": 0.0, "diversity": 0.0, "coverage": 0.0}

        grouped: dict[str, list[UserInteraction]] = defaultdict(list)
        for interaction in interactions:
            grouped[interaction.user_id].append(interaction)

        hits = 0.0
        ndcg_total = 0.0
        diversity_total = 0.0
        evaluated_users = 0
        total_recommended = 0
        covered_items: set[int] = set()
        products = self._list_products()

        for user_id, rows in grouped.items():
            if len(rows) < 2:
                continue
            holdout = rows[-1]
            historical_rows = rows[:-1]
            payload = EngineRecommendationRequest(
                user_id=user_id,
                top_k=10,
                products=products,
                interactions=[
                    EngineUserEvent(
                        user_id=row.user_id,
                        product_id=row.product_id,
                        event_type=_to_engine_event_type(row.interaction_type.value),
                        created_at=row.interaction_time,
                    )
                    for row in historical_rows
                ],
                cart_items=[],
                order_items=[],
                algorithm=algorithm,
            )
            recommendations = self.engine.recommend(payload)
            if not recommendations:
                continue
            evaluated_users += 1
            covered_items.update(result.product_id for result in recommendations)
            diversity_total += self._category_diversity(recommendations)
            total_recommended += len(recommendations)
            ranked_ids = [result.product_id for result in recommendations]
            if holdout.product_id in ranked_ids:
                hits += 1
                rank = ranked_ids.index(holdout.product_id) + 1
                ndcg_total += 1 / log2(rank + 1)

        if evaluated_users == 0:
            return {"precision@10": 0.0, "recall@10": 0.0, "ndcg@10": 0.0, "diversity": 0.0, "coverage": 0.0}

        return {
            "precision@10": round(hits / max(total_recommended, 1), 4),
            "recall@10": round(hits / evaluated_users, 4),
            "ndcg@10": round(ndcg_total / evaluated_users, 4),
            "diversity": round(diversity_total / evaluated_users, 4),
            "coverage": round(len(covered_items) / unique_items, 4),
        }

    def _category_diversity(self, recommendations: list[RecommendationResult]) -> float:
        category_map = {
            product_id: category_id
            for product_id, category_id in self.db.query(Product.product_id, Product.category_id).all()
        }
        category_ids = [category_map[row.product_id] for row in recommendations if row.product_id in category_map]
        if not category_ids:
            return 0.0
        return len(set(category_ids)) / len(category_ids)

    def _list_products(self) -> list[EngineProduct]:
        products = self.db.query(Product).all()
        return [
            EngineProduct(
                id=product.product_id,
                name=product.name,
                category_id=product.category_id,
                tags=self._product_tags(product),
                is_active=product.stock_quantity > 0,
                metadata_completeness=self._metadata_completeness(product),
            )
            for product in products
        ]

    def _list_interactions(self) -> list[EngineUserEvent]:
        interactions = self.db.query(UserInteraction).all()
        return [
            EngineUserEvent(
                user_id=interaction.user_id,
                product_id=interaction.product_id,
                event_type=_to_engine_event_type(interaction.interaction_type.value),
                created_at=interaction.interaction_time.replace(tzinfo=timezone.utc)
                if interaction.interaction_time.tzinfo is None
                else interaction.interaction_time,
                context=_json_loads(interaction.interaction_metadata, {}),
            )
            for interaction in interactions
        ]

    def _list_cart_items(self):
        carts = self.db.query(Cart).all()
        items = []
        for cart in carts:
            for item in cart.items:
                items.append(
                    {
                        "user_id": cart.user_id,
                        "product_id": item.product_id,
                        "created_at": cart.created_at,
                    }
                )
        return items

    def _list_order_items(self):
        orders = self.db.query(Order).all()
        items = []
        for order in orders:
            for item in order.order_items:
                items.append(
                    {
                        "user_id": order.user_id,
                        "product_id": item.product_id,
                        "created_at": order.order_date,
                    }
                )
        return items

    def _product_tags(self, product: Product) -> list[str]:
        tokens = [product.name]
        if product.description:
            tokens.extend(product.description.split())
        return sorted({token.lower().strip(".,") for token in tokens if token})

    def _metadata_completeness(self, product: Product) -> float:
        checks = [
            bool(product.name),
            bool(product.description),
            Decimal(product.price) > 0,
            product.stock_quantity >= 0,
            bool(product.category_id),
        ]
        return sum(checks) / max(len(checks), 1)

    def _resolve_category_preferences(self, categories_json: str) -> list[int]:
        category_names = [name.lower() for name in _json_loads(categories_json, [])]
        if not category_names:
            return []
        rows = (
            self.db.query(Category.category_id)
            .filter(func.lower(Category.name).in_(category_names))
            .all()
        )
        return sorted({row.category_id for row in rows})

    def _get_latest_model(self, algorithm: str) -> MLModel | None:
        return (
            self.db.query(MLModel)
            .filter(MLModel.algorithm == algorithm)
            .order_by(MLModel.trained_at.desc())
            .first()
        )

    def _get_active_experiment(self) -> Experiment | None:
        return (
            self.db.query(Experiment)
            .filter(Experiment.status == "running")
            .order_by(Experiment.started_at.desc())
            .first()
        )

    def _select_experiment_model(self, experiment: Experiment, user_id: str) -> tuple[MLModel, str]:
        variants = {variant.variant_name: variant for variant in experiment.variants}
        config = _json_loads(experiment.config_json, {})
        bucket = self._bucket_user(user_id, config.get("salt", experiment.experiment_id))
        variant_name = "control" if bucket < variants["control"].traffic_percent else "variant"
        selected_variant = variants[variant_name]
        model = self.db.query(MLModel).filter(MLModel.model_id == selected_variant.model_id).first()
        return model, variant_name

    def _bucket_user(self, user_id: str, salt: str) -> float:
        digest = hashlib.sha256(f"{salt}:{user_id}".encode("utf-8")).hexdigest()
        return int(digest[:8], 16) / (0xFFFFFFFF + 1)


def generate_experiment_salt() -> str:
    return uuid.uuid4().hex


def _to_engine_event_type(value: str) -> str:
    mapping = {
        "View": "view",
        "Click": "click",
        "AddToCart": "cart",
        "Purchase": "purchase",
        "Search": "search",
        "Review": "comment",
    }
    return mapping.get(value, value.lower())
