from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

from .models import InteractionType, OrderStatus, PaymentStatus

Money = Annotated[float, Field(gt=0)]
Quantity = Annotated[int, Field(gt=0)]
UserId = Annotated[str, Field(min_length=3, max_length=100)]


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class RegisterRequest(APIModel):
    user_id: UserId
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]
    is_admin: bool = False


class LoginRequest(APIModel):
    email: EmailStr
    password: str


class UserResponse(APIModel):
    user_id: str
    email: EmailStr
    is_admin: bool
    is_active: bool
    created_at: datetime


class AddressRequest(APIModel):
    street: Annotated[str, Field(min_length=2, max_length=250)]
    city: Annotated[str, Field(min_length=2, max_length=100)]
    state: Annotated[str, Field(min_length=2, max_length=100)]
    postal_code: Annotated[str, Field(min_length=2, max_length=20)]
    country: Annotated[str, Field(min_length=2, max_length=100)]
    user_id: UserId


class AddressResponse(AddressRequest):
    address_id: int


class CategoryRequest(APIModel):
    name: Annotated[str, Field(min_length=2, max_length=150)]
    parent_category_id: int | None = None


class CategoryResponse(APIModel):
    id: int
    name: str
    sub_categories: list["CategoryResponse"] = Field(default_factory=list)


class ProductImageRequest(APIModel):
    url: HttpUrl
    is_primary: bool = False
    product_id: int | None = None


class ProductImageResponse(APIModel):
    image_id: int
    url: HttpUrl
    is_primary: bool
    product_id: int


class ProductRequest(APIModel):
    name: Annotated[str, Field(min_length=2, max_length=200)]
    description: Annotated[str | None, Field(max_length=1000)] = None
    price: Money
    stock_quantity: Annotated[int, Field(ge=0)]
    category_id: int


class ProductResponse(ProductRequest):
    product_id: int
    created_at: datetime
    images: list[ProductImageResponse] = Field(default_factory=list)


class AddCartItemRequest(APIModel):
    product_id: int
    quantity: Quantity


class ChangeCartItemQuantityRequest(APIModel):
    product_id: int
    quantity: Annotated[int, Field(ge=0)]


class CartItemResponse(APIModel):
    product_id: int
    quantity: int


class CartResponse(APIModel):
    cart_id: str
    user_id: str
    created_at: datetime
    items: list[CartItemResponse] = Field(default_factory=list)


class OrderItemRequest(APIModel):
    quantity: Quantity
    unit_price: Money
    product_id: int


class OrderItemResponse(OrderItemRequest):
    order_item_id: int


class PaymentRequest(APIModel):
    amount: Money
    provider: Annotated[str, Field(min_length=2, max_length=50)]
    order_id: str
    status: PaymentStatus = PaymentStatus.Pending


class PaymentResponse(PaymentRequest):
    payment_id: int


class OrderRequest(APIModel):
    total_amount: Money
    shipping_address_id: int
    order_items: list[OrderItemRequest] = Field(min_length=1)


class OrderResponse(APIModel):
    order_id: str
    order_date: datetime
    status: OrderStatus
    total_amount: float
    user_id: str
    shipping_address_id: int
    order_items: list[OrderItemResponse]
    payment: PaymentResponse | None = None


class UserInteractionRequest(APIModel):
    product_id: int
    interaction_type: InteractionType
    metadata: Annotated[str | None, Field(max_length=2000)] = None


class UserInteractionResponse(UserInteractionRequest):
    id: int
    user_id: str


CategoryResponse.model_rebuild()
