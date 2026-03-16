import enum
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text
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


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


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
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.category_id"))
    images: Mapped[list["ProductImage"]] = relationship("ProductImage", cascade="all,delete", back_populates="product")


class ProductImage(Base):
    __tablename__ = "product_images"
    image_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(500))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"))
    product: Mapped[Product] = relationship("Product", back_populates="images")


class Cart(Base):
    __tablename__ = "carts"
    cart_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[str] = mapped_column(String(100), unique=True)
    items: Mapped[list["CartItem"]] = relationship("CartItem", cascade="all,delete", back_populates="cart")


class CartItem(Base):
    __tablename__ = "cart_items"
    cart_item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer)
    cart_id: Mapped[str] = mapped_column(ForeignKey("carts.cart_id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"))
    cart: Mapped[Cart] = relationship("Cart", back_populates="items")


class Order(Base):
    __tablename__ = "orders"
    order_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.Pending)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    user_id: Mapped[str] = mapped_column(String(100))
    shipping_address_id: Mapped[int] = mapped_column(ForeignKey("addresses.address_id"))
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", cascade="all,delete", back_populates="order")
    payment: Mapped["Payment | None"] = relationship("Payment", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"
    order_item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 2))
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"))
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
    user_id: Mapped[str] = mapped_column(String(100))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"))
    interaction_type: Mapped[InteractionType] = mapped_column(Enum(InteractionType))
    interaction_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)
