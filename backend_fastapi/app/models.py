import enum
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class OrderStatus(str, enum.Enum):
    Pending = "Pending"
    Processing = "Processing"
    Shipped = "Shipped"
    Delivered = "Delivered"
    Cancelled = "Cancelled"


class PaymentStatus(str, enum.Enum):
    Pending = "Pending"
    Completed = "Completed"
    Failed = "Failed"
    Refunded = "Refunded"


class InteractionType(str, enum.Enum):
    View = "View"
    Click = "Click"
    AddToCart = "AddToCart"
    Purchase = "Purchase"
    Search = "Search"
    Review = "Review"


class Address(Base):
    __tablename__ = "addresses"
    address_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    street: Mapped[str] = mapped_column(String(250))
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[str] = mapped_column(String(100))


class Category(Base):
    __tablename__ = "categories"
    category_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    parent_category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.category_id"), nullable=True)


class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    price: Mapped[float] = mapped_column(Numeric(18, 2))
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.category_id"), index=True)
    images: Mapped[list["ProductImage"]] = relationship("ProductImage", cascade="all,delete", back_populates="product")


class ProductImage(Base):
    __tablename__ = "product_images"
    image_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(500))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), index=True)
    product: Mapped[Product] = relationship("Product", back_populates="images")


class Cart(Base):
    __tablename__ = "carts"
    cart_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[str] = mapped_column(String(100), unique=True)
    items: Mapped[list["CartItem"]] = relationship("CartItem", cascade="all,delete", back_populates="cart")


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "product_id", name="uq_cart_item_cart_product"),)
    cart_item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer)
    cart_id: Mapped[str] = mapped_column(ForeignKey("carts.cart_id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), index=True)
    cart: Mapped[Cart] = relationship("Cart", back_populates="items")


class Order(Base):
    __tablename__ = "orders"
    order_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.Pending)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    shipping_address_id: Mapped[int] = mapped_column(ForeignKey("addresses.address_id"), index=True)
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", cascade="all,delete", back_populates="order")
    payment: Mapped["Payment | None"] = relationship("Payment", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"
    order_item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 2))
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), index=True)
    order: Mapped[Order] = relationship("Order", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"
    payment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    amount: Mapped[float] = mapped_column(Numeric(18, 2))
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.Pending)
    provider: Mapped[str] = mapped_column(String(50))
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"), unique=True)
    order: Mapped[Order] = relationship("Order", back_populates="payment")


class UserInteraction(Base):
    __tablename__ = "user_interactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), index=True)
    interaction_type: Mapped[InteractionType] = mapped_column(Enum(InteractionType))
    interaction_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    interaction_metadata: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_event_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)


class UserPreference(Base):
    __tablename__ = "user_preferences"
    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    categories_json: Mapped[str] = mapped_column(Text, default="[]")
    diversity: Mapped[float] = mapped_column(Float, default=0.3)
    recency_bias: Mapped[float] = mapped_column(Float, default=0.5)
    exclude_viewed: Mapped[bool] = mapped_column(Boolean, default=False)
    algorithm: Mapped[str | None] = mapped_column(String(50), nullable=True)
    max_per_category: Mapped[int] = mapped_column(Integer, default=3)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MLModel(Base):
    __tablename__ = "ml_models"
    model_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    algorithm: Mapped[str] = mapped_column(String(50), index=True)
    version: Mapped[str] = mapped_column(String(50))
    hyperparameters_json: Mapped[str] = mapped_column(Text, default="{}")
    metrics_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(20), default="registered")
    trained_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class TrainingJob(Base):
    __tablename__ = "training_jobs"
    job_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id: Mapped[str | None] = mapped_column(ForeignKey("ml_models.model_id"), nullable=True, index=True)
    algorithm: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="queued")
    message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Experiment(Base):
    __tablename__ = "experiments"
    experiment_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="running")
    config_json: Mapped[str] = mapped_column(Text, default="{}")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    variants: Mapped[list["ModelVariant"]] = relationship("ModelVariant", cascade="all,delete", back_populates="experiment")


class ModelVariant(Base):
    __tablename__ = "model_variants"
    variant_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[str] = mapped_column(ForeignKey("experiments.experiment_id"), index=True)
    model_id: Mapped[str] = mapped_column(ForeignKey("ml_models.model_id"), index=True)
    variant_name: Mapped[str] = mapped_column(String(30))
    traffic_percent: Mapped[float] = mapped_column(Float)
    metrics_json: Mapped[str] = mapped_column(Text, default="{}")
    experiment: Mapped[Experiment] = relationship("Experiment", back_populates="variants")
