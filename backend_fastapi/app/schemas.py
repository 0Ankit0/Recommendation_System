from datetime import datetime
from pydantic import BaseModel


class AddressRequest(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    user_id: str


class AddressResponse(AddressRequest):
    address_id: int


class CategoryRequest(BaseModel):
    name: str
    parent_category_id: int | None = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    sub_categories: list["CategoryResponse"] = []


class ProductImageRequest(BaseModel):
    url: str
    is_primary: bool = False
    product_id: int | None = None


class ProductImageResponse(ProductImageRequest):
    image_id: int
    product_id: int


class ProductRequest(BaseModel):
    name: str
    description: str | None = None
    price: float
    stock_quantity: int
    category_id: int


class ProductResponse(ProductRequest):
    product_id: int
    created_at: datetime
    images: list[ProductImageResponse] = []


class AddCartItemRequest(BaseModel):
    user_id: str
    product_id: int
    quantity: int


class RemoveCartItemRequest(BaseModel):
    user_id: str
    product_id: int


class CartItemResponse(BaseModel):
    product_id: int
    quantity: int


class CartResponse(BaseModel):
    cart_id: str
    user_id: str
    created_at: datetime
    items: list[CartItemResponse] = []


class OrderItemRequest(BaseModel):
    quantity: int
    unit_price: float
    product_id: int


class OrderItemResponse(OrderItemRequest):
    order_item_id: int


class PaymentRequest(BaseModel):
    amount: float
    provider: str
    order_id: str


class PaymentResponse(PaymentRequest):
    payment_id: int


class OrderRequest(BaseModel):
    user_id: str
    total_amount: float
    shipping_address_id: int
    order_items: list[OrderItemRequest]


class OrderResponse(BaseModel):
    order_id: str
    order_date: datetime
    status: str
    total_amount: float
    user_id: str
    shipping_address_id: int
    order_items: list[OrderItemResponse]
    payment: PaymentResponse | None = None


class UserInteractionRequest(BaseModel):
    user_id: str
    product_id: int
    interaction_type: str
    metadata: str | None = None


class UserInteractionResponse(UserInteractionRequest):
    id: int


CategoryResponse.model_rebuild()
