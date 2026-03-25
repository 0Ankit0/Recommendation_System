from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


AlgorithmType = Literal["collaborative", "content_based", "hybrid"]
EventActionType = Literal["view", "click", "search", "comment", "cart", "purchase", "like", "save", "share"]


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())


class AddressRequest(BaseModel):
    street: str = Field(min_length=1, max_length=250)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(min_length=1, max_length=100)
    user_id: str = Field(min_length=1, max_length=100)


class AddressResponse(AddressRequest):
    address_id: int


class CategoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    parent_category_id: int | None = Field(default=None, gt=0)


class CategoryResponse(BaseModel):
    id: int
    name: str
    sub_categories: list["CategoryResponse"] = Field(default_factory=list)


class ProductImageRequest(BaseModel):
    url: str = Field(min_length=1, max_length=500)
    is_primary: bool = False
    product_id: int | None = Field(default=None, gt=0)


class ProductImageResponse(ProductImageRequest):
    image_id: int
    product_id: int


class ProductRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    price: float = Field(ge=0.0)
    stock_quantity: int = Field(ge=0)
    category_id: int = Field(gt=0)


class ProductResponse(ProductRequest):
    product_id: int
    created_at: datetime
    images: list[ProductImageResponse] = Field(default_factory=list)


class AddCartItemRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=100)


class RemoveCartItemRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    product_id: int = Field(gt=0)


class CartItemResponse(BaseModel):
    product_id: int
    quantity: int


class CartResponse(BaseModel):
    cart_id: str
    user_id: str
    created_at: datetime
    items: list[CartItemResponse] = Field(default_factory=list)


class OrderItemRequest(BaseModel):
    quantity: int = Field(ge=1, le=100)
    unit_price: float = Field(ge=0.0)
    product_id: int = Field(gt=0)


class OrderItemResponse(OrderItemRequest):
    order_item_id: int


class PaymentRequest(BaseModel):
    amount: float = Field(ge=0.0)
    provider: str = Field(min_length=1, max_length=50)
    order_id: str = Field(min_length=1, max_length=36)


class PaymentResponse(PaymentRequest):
    payment_id: int


class OrderRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    total_amount: float = Field(ge=0.0)
    shipping_address_id: int = Field(gt=0)
    order_items: list[OrderItemRequest] = Field(min_length=1)


class OrderResponse(BaseModel):
    order_id: str
    order_date: datetime
    status: str
    total_amount: float
    user_id: str
    shipping_address_id: int
    order_items: list[OrderItemResponse] = Field(default_factory=list)
    payment: PaymentResponse | None = None


class UserInteractionRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    product_id: int = Field(gt=0)
    interaction_type: str = Field(min_length=1, max_length=30)
    metadata: str | None = None


class UserInteractionResponse(UserInteractionRequest):
    id: int


class EventRequest(CamelModel):
    event_id: str | None = Field(default=None, alias="eventId", min_length=1, max_length=64)
    user_id: str = Field(alias="userId", min_length=1, max_length=100)
    item_id: int = Field(alias="itemId", gt=0)
    action_type: EventActionType = Field(alias="actionType")
    value: float = Field(default=1.0, gt=0.0)
    timestamp: datetime | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class EventAcceptedResponse(CamelModel):
    event_id: str = Field(alias="eventId")
    status: str


class RecommendationItemResponse(CamelModel):
    item_id: int = Field(alias="itemId")
    score: float
    rank: int
    explanation: str | None = None


class RecommendationEnvelope(CamelModel):
    user_id: str = Field(alias="userId")
    recommendations: list[RecommendationItemResponse] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchRecommendationRequest(CamelModel):
    user_ids: list[str] = Field(alias="userIds", min_length=1, max_length=100)
    algorithm: AlgorithmType | None = None
    limit: int = Field(default=10, ge=1, le=50)
    explain: bool = True

    @field_validator("user_ids")
    @classmethod
    def _normalize_user_ids(cls, value: list[str]) -> list[str]:
        normalized = [user_id.strip() for user_id in value if user_id and user_id.strip()]
        unique = list(dict.fromkeys(normalized))
        if not unique:
            raise ValueError("userIds must contain at least one user id")
        return unique


class BatchRecommendationResponse(CamelModel):
    results: list[RecommendationEnvelope] = Field(default_factory=list)


class UserPreferenceRequest(CamelModel):
    categories: list[str] = Field(default_factory=list)
    diversity: float = Field(default=0.3, ge=0.0, le=1.0)
    recency_bias: float = Field(default=0.5, ge=0.0, le=1.0)
    exclude_viewed: bool = Field(default=False, alias="excludeViewed")
    algorithm: AlgorithmType | None = None
    max_per_category: int = Field(default=3, alias="maxPerCategory", ge=1, le=10)


class UserPreferenceResponse(UserPreferenceRequest):
    user_id: str = Field(alias="userId")
    updated_at: datetime = Field(alias="updatedAt")


class TrainingRangeRequest(CamelModel):
    start: datetime | None = None
    end: datetime | None = None


class TrainModelRequest(CamelModel):
    algorithm: AlgorithmType
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    data_range: TrainingRangeRequest | None = Field(default=None, alias="dataRange")


class TrainModelResponse(CamelModel):
    job_id: str = Field(alias="jobId")
    status: str
    model_id: str = Field(alias="modelId")


class ModelMetricsResponse(CamelModel):
    model_id: str = Field(alias="modelId")
    metrics: dict[str, float | int]


class TrafficSplit(CamelModel):
    control: float = Field(ge=0.0, le=1.0)
    variant: float = Field(ge=0.0, le=1.0)

    @field_validator("variant")
    @classmethod
    def _validate_split(cls, value: float, info) -> float:
        control = info.data.get("control", 0.0)
        if abs((control + value) - 1.0) > 1e-9:
            raise ValueError("trafficSplit must sum to 1.0")
        return value


class ExperimentRequest(CamelModel):
    name: str = Field(min_length=1, max_length=100)
    control_model_id: str = Field(alias="controlModelId", min_length=1, max_length=36)
    variant_model_id: str = Field(alias="variantModelId", min_length=1, max_length=36)
    traffic_split: TrafficSplit = Field(alias="trafficSplit")
    metrics: list[str] = Field(default_factory=list)


class ExperimentResponse(CamelModel):
    experiment_id: str = Field(alias="experimentId")
    status: str


CategoryResponse.model_rebuild()
