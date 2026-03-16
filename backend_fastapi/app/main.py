from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import get_settings
from .database import Base, engine, get_db
from .models import (
    Address,
    Cart,
    CartItem,
    Category,
    InteractionType,
    Order,
    OrderItem,
    Payment,
    Product,
    ProductImage,
    User,
    UserInteraction,
)
from .schemas import (
    AddCartItemRequest,
    AddressRequest,
    AddressResponse,
    CartItemResponse,
    CartResponse,
    CategoryRequest,
    CategoryResponse,
    ChangeCartItemQuantityRequest,
    LoginRequest,
    OrderItemRequest,
    OrderItemResponse,
    OrderRequest,
    OrderResponse,
    PaymentRequest,
    PaymentResponse,
    ProductImageRequest,
    ProductImageResponse,
    ProductRequest,
    ProductResponse,
    RegisterRequest,
    TokenResponse,
    UserInteractionRequest,
    UserInteractionResponse,
    UserResponse,
)
from .security import create_access_token, decode_access_token, hash_password, verify_password

settings = get_settings()
app = FastAPI(title=settings.app_name)
security = HTTPBearer(auto_error=True)

app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver", "*"])


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.exception_handler(IntegrityError)
def handle_integrity_error(_, __):
    return JSONResponse(status_code=400, content={"detail": "Database integrity error"})


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(credentials.credentials)
    user = db.query(User).filter(User.user_id == payload["sub"], User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment}


@app.post("/api/auth/register", response_model=UserResponse, status_code=201)
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    user = User(user_id=req.user_id, email=req.email, hashed_password=hash_password(req.password), is_admin=req.is_admin)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=TokenResponse)
def login_user(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email, User.is_active.is_(True)).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token(subject=user.user_id, is_admin=user.is_admin, expires_delta=expires)
    return TokenResponse(access_token=token, expires_in_seconds=int(expires.total_seconds()))


@app.get("/api/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/api/categories", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    roots = db.query(Category).filter(Category.parent_category_id.is_(None)).all()
    return [
        CategoryResponse(
            id=c.category_id,
            name=c.name,
            sub_categories=[CategoryResponse(id=s.category_id, name=s.name) for s in db.query(Category).filter(Category.parent_category_id == c.category_id).all()],
        )
        for c in roots
    ]


@app.post("/api/categories", response_model=CategoryResponse, status_code=201, dependencies=[Depends(require_admin)])
def create_category(req: CategoryRequest, db: Session = Depends(get_db)):
    c = Category(name=req.name, parent_category_id=req.parent_category_id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return CategoryResponse(id=c.category_id, name=c.name)


@app.get("/api/products", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    rows = db.query(Product).options(joinedload(Product.images)).all()
    return [serialize_product(p) for p in rows]


@app.get("/api/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(Product).options(joinedload(Product.images)).filter(Product.product_id == product_id).first()
    if not p:
        raise HTTPException(404, "Product not found")
    return serialize_product(p)


@app.post("/api/products", response_model=ProductResponse, status_code=201, dependencies=[Depends(require_admin)])
def create_product(req: ProductRequest, db: Session = Depends(get_db)):
    p = Product(**req.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return serialize_product(p)


@app.post("/api/products/{product_id}/images", response_model=ProductImageResponse, status_code=201, dependencies=[Depends(require_admin)])
def create_product_image(product_id: int, req: ProductImageRequest, db: Session = Depends(get_db)):
    i = ProductImage(url=str(req.url), is_primary=req.is_primary, product_id=product_id)
    db.add(i)
    db.commit()
    db.refresh(i)
    return serialize_image(i)


@app.post("/api/addresses", response_model=AddressResponse, status_code=201)
def create_address(req: AddressRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.user_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Cannot create address for another user")
    a = Address(**req.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return AddressResponse(address_id=a.address_id, **to_address_dict(a))


@app.get("/api/addresses", response_model=list[AddressResponse])
def get_addresses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Address)
    if not current_user.is_admin:
        query = query.filter(Address.user_id == current_user.user_id)
    return [AddressResponse(address_id=a.address_id, **to_address_dict(a)) for a in query.all()]


@app.post("/api/cart/add", response_model=CartResponse)
def add_cart_item(req: AddCartItemRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(Cart).options(joinedload(Cart.items)).filter(Cart.user_id == current_user.user_id).first()
    if not cart:
        cart = Cart(user_id=current_user.user_id)
        db.add(cart)
        db.flush()
    item = next((i for i in cart.items if i.product_id == req.product_id), None)
    if item:
        item.quantity += req.quantity
    else:
        cart.items.append(CartItem(product_id=req.product_id, quantity=req.quantity, cart_id=cart.cart_id))
    db.commit()
    db.refresh(cart)
    return serialize_cart(cart)


@app.post("/api/cart/change-quantity", response_model=CartResponse)
def change_cart_quantity(req: ChangeCartItemQuantityRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(Cart).options(joinedload(Cart.items)).filter(Cart.user_id == current_user.user_id).first()
    if not cart:
        raise HTTPException(404, "Cart not found")
    item = next((i for i in cart.items if i.product_id == req.product_id), None)
    if not item:
        raise HTTPException(404, "Item not found")
    if req.quantity == 0:
        db.delete(item)
    else:
        item.quantity = req.quantity
    db.commit()
    db.refresh(cart)
    return serialize_cart(cart)


@app.get("/api/cart/user/{user_id}", response_model=CartResponse)
def get_cart(user_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.user_id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    cart = db.query(Cart).options(joinedload(Cart.items)).filter(Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(404, "Cart not found")
    return serialize_cart(cart)


@app.post("/api/orders", response_model=OrderResponse, status_code=201)
def create_order(req: OrderRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    o = Order(user_id=current_user.user_id, total_amount=req.total_amount, shipping_address_id=req.shipping_address_id)
    db.add(o)
    db.flush()
    for item in req.order_items:
        db.add(OrderItem(order_id=o.order_id, quantity=item.quantity, unit_price=item.unit_price, product_id=item.product_id))
    db.commit()
    return serialize_order(db.query(Order).options(joinedload(Order.order_items), joinedload(Order.payment)).filter(Order.order_id == o.order_id).first())


@app.get("/api/orders", response_model=list[OrderResponse])
def get_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Order).options(joinedload(Order.order_items), joinedload(Order.payment))
    if not current_user.is_admin:
        query = query.filter(Order.user_id == current_user.user_id)
    return [serialize_order(o) for o in query.all()]


@app.post("/api/payments", response_model=PaymentResponse, status_code=201)
def create_payment(req: PaymentRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_id == req.order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    if order.user_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(403, "Forbidden")

    p = Payment(amount=req.amount, provider=req.provider, order_id=req.order_id, status=req.status)
    db.add(p)
    db.commit()
    db.refresh(p)
    return PaymentResponse(payment_id=p.payment_id, amount=float(p.amount), provider=p.provider, order_id=p.order_id, status=p.status)


@app.post("/api/userinteractions", response_model=UserInteractionResponse, status_code=201)
def create_interaction(req: UserInteractionRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    interaction_type = InteractionType(req.interaction_type)
    u = UserInteraction(user_id=current_user.user_id, product_id=req.product_id, interaction_type=interaction_type, metadata=req.metadata)
    db.add(u)
    db.commit()
    db.refresh(u)
    return UserInteractionResponse(id=u.id, user_id=u.user_id, product_id=u.product_id, interaction_type=u.interaction_type, metadata=u.metadata)


@app.get("/api/userinteractions", response_model=list[UserInteractionResponse])
def get_interactions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(UserInteraction)
    if not current_user.is_admin:
        query = query.filter(UserInteraction.user_id == current_user.user_id)
    return [
        UserInteractionResponse(id=u.id, user_id=u.user_id, product_id=u.product_id, interaction_type=u.interaction_type, metadata=u.metadata)
        for u in query.all()
    ]


@app.post("/api/orders/{order_id}/items", response_model=OrderItemResponse, status_code=201)
def create_order_item(order_id: str, req: OrderItemRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    if order.user_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(403, "Forbidden")
    i = OrderItem(order_id=order_id, quantity=req.quantity, unit_price=req.unit_price, product_id=req.product_id)
    db.add(i)
    db.commit()
    db.refresh(i)
    return OrderItemResponse(order_item_id=i.order_item_id, quantity=i.quantity, unit_price=float(i.unit_price), product_id=i.product_id)


def serialize_image(i: ProductImage) -> ProductImageResponse:
    return ProductImageResponse(image_id=i.image_id, url=i.url, is_primary=i.is_primary, product_id=i.product_id)


def serialize_product(p: Product) -> ProductResponse:
    return ProductResponse(
        product_id=p.product_id,
        name=p.name,
        description=p.description,
        price=float(p.price),
        stock_quantity=p.stock_quantity,
        created_at=p.created_at,
        category_id=p.category_id,
        images=[serialize_image(i) for i in p.images],
    )


def serialize_cart(c: Cart) -> CartResponse:
    return CartResponse(
        cart_id=c.cart_id,
        user_id=c.user_id,
        created_at=c.created_at,
        items=[CartItemResponse(product_id=i.product_id, quantity=i.quantity) for i in c.items],
    )


def serialize_order(o: Order) -> OrderResponse:
    return OrderResponse(
        order_id=o.order_id,
        order_date=o.order_date,
        status=o.status,
        total_amount=float(o.total_amount),
        user_id=o.user_id,
        shipping_address_id=o.shipping_address_id,
        order_items=[OrderItemResponse(order_item_id=i.order_item_id, quantity=i.quantity, unit_price=float(i.unit_price), product_id=i.product_id) for i in o.order_items],
        payment=PaymentResponse(payment_id=o.payment.payment_id, amount=float(o.payment.amount), provider=o.payment.provider, order_id=o.payment.order_id, status=o.payment.status) if o.payment else None,
    )


def to_address_dict(a: Address) -> dict:
    return {
        "street": a.street,
        "city": a.city,
        "state": a.state,
        "postal_code": a.postal_code,
        "country": a.country,
        "user_id": a.user_id,
    }
