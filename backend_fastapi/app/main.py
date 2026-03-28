from __future__ import annotations

import json
import uuid
from decimal import Decimal, ROUND_HALF_UP

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from .config import get_settings
from .database import Base, engine, get_db
from .models import (
    Address,
    Cart,
    CartItem,
    Category,
    Experiment,
    InteractionType,
    MLModel,
    ModelVariant,
    Order,
    OrderItem,
    Payment,
    Product,
    ProductImage,
    TrainingJob,
    UserInteraction,
    UserPreference,
    utc_now,
)
from .recommendation_service import SQLRecommendationService, generate_experiment_salt
from .security import create_access_token, decode_access_token, hash_password, verify_password
from .schemas import (
    AddCartItemRequest,
    AddressRequest,
    AddressResponse,
    BatchRecommendationRequest,
    BatchRecommendationResponse,
    CartItemResponse,
    CartResponse,
    CategoryRequest,
    CategoryResponse,
    EventAcceptedResponse,
    EventRequest,
    ExperimentRequest,
    ExperimentResponse,
    LoginRequest,
    ModelMetricsResponse,
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
    RecommendationEnvelope,
    RecommendationItemResponse,
    RegisterRequest,
    RemoveCartItemRequest,
    TokenResponse,
    TrainModelRequest,
    TrainModelResponse,
    UserInteractionRequest,
    UserInteractionResponse,
    UserPreferenceRequest,
    UserPreferenceResponse,
)

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)
auth_scheme = HTTPBearer(auto_error=True)
users_by_email: dict[str, dict[str, str | bool]] = {}
users_by_id: dict[str, dict[str, str | bool]] = {}


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> dict[str, str | bool]:
    payload = decode_access_token(credentials.credentials)
    user_id = str(payload["sub"])
    user = users_by_id.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_admin(current_user: dict[str, str | bool] = Depends(get_current_user)) -> dict[str, str | bool]:
    if not bool(current_user.get("is_admin")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}


@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    email = req.email.strip().lower()
    if email in users_by_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = {
        "user_id": req.user_id.strip(),
        "email": email,
        "password_hash": hash_password(req.password),
        "is_admin": req.is_admin,
    }
    users_by_email[email] = user
    users_by_id[str(user["user_id"])] = user
    return {"user_id": user["user_id"], "email": email, "is_admin": req.is_admin}


@app.post("/api/auth/login", response_model=TokenResponse)
def login(req: LoginRequest):
    email = req.email.strip().lower()
    user = users_by_email.get(email)
    if not user or not verify_password(req.password, str(user["password_hash"])):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(subject=str(user["user_id"]), is_admin=bool(user["is_admin"]))
    return TokenResponse(access_token=access_token)


@app.get("/api/categories", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.name.asc()).all()
    children: dict[int | None, list[Category]] = {}
    for category in categories:
        children.setdefault(category.parent_category_id, []).append(category)
    return [_serialize_category_tree(category, children) for category in children.get(None, [])]


@app.get("/api/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = _get_category_or_404(db, category_id)
    sub_categories = db.query(Category).filter(Category.parent_category_id == category.category_id).all()
    return CategoryResponse(
        id=category.category_id,
        name=category.name,
        sub_categories=[CategoryResponse(id=item.category_id, name=item.name) for item in sub_categories],
    )


@app.post("/api/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    req: CategoryRequest,
    db: Session = Depends(get_db),
    _admin: dict[str, str | bool] = Depends(require_admin),
):
    if req.parent_category_id:
        _get_category_or_404(db, req.parent_category_id)
    category = Category(name=req.name.strip(), parent_category_id=req.parent_category_id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return CategoryResponse(id=category.category_id, name=category.name)


@app.put("/api/categories/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, req: CategoryRequest, db: Session = Depends(get_db)):
    category = _get_category_or_404(db, category_id)
    if req.parent_category_id == category_id:
        raise HTTPException(status_code=400, detail="Category cannot be its own parent")
    if req.parent_category_id:
        _get_category_or_404(db, req.parent_category_id)
    category.name = req.name.strip()
    category.parent_category_id = req.parent_category_id
    db.commit()
    db.refresh(category)
    return get_category(category_id, db)


@app.delete("/api/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = _get_category_or_404(db, category_id)
    has_children = db.query(Category).filter(Category.parent_category_id == category_id).first()
    has_products = db.query(Product).filter(Product.category_id == category_id).first()
    if has_children or has_products:
        raise HTTPException(status_code=409, detail="Category is still in use")
    db.delete(category)
    db.commit()


@app.get("/api/products", response_model=list[ProductResponse])
def get_products(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Product)
        .options(joinedload(Product.images))
        .order_by(Product.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [serialize_product(product) for product in rows]


@app.get("/api/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .options(joinedload(Product.images))
        .filter(Product.product_id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_product(product)


@app.post("/api/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    req: ProductRequest,
    db: Session = Depends(get_db),
    _admin: dict[str, str | bool] = Depends(require_admin),
):
    _get_category_or_404(db, req.category_id)
    product = Product(**req.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return serialize_product(product)


@app.get("/api/products/{product_id}/images", response_model=list[ProductImageResponse])
def get_product_images(product_id: int, db: Session = Depends(get_db)):
    _get_product_or_404(db, product_id)
    images = db.query(ProductImage).filter(ProductImage.product_id == product_id).all()
    return [serialize_image(image) for image in images]


@app.get("/api/products/{product_id}/images/{image_id}", response_model=ProductImageResponse)
def get_product_image(product_id: int, image_id: int, db: Session = Depends(get_db)):
    _get_product_or_404(db, product_id)
    image = (
        db.query(ProductImage)
        .filter(ProductImage.product_id == product_id, ProductImage.image_id == image_id)
        .first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return serialize_image(image)


@app.post("/api/products/{product_id}/images", response_model=ProductImageResponse, status_code=status.HTTP_201_CREATED)
def create_product_image(product_id: int, req: ProductImageRequest, db: Session = Depends(get_db)):
    _get_product_or_404(db, product_id)
    image = ProductImage(url=req.url, is_primary=req.is_primary, product_id=product_id)
    db.add(image)
    db.commit()
    db.refresh(image)
    return serialize_image(image)


@app.put("/api/products/{product_id}/images/{image_id}", response_model=ProductImageResponse)
def update_product_image(product_id: int, image_id: int, req: ProductImageRequest, db: Session = Depends(get_db)):
    _get_product_or_404(db, product_id)
    image = (
        db.query(ProductImage)
        .filter(ProductImage.product_id == product_id, ProductImage.image_id == image_id)
        .first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image.url = req.url
    image.is_primary = req.is_primary
    db.commit()
    db.refresh(image)
    return serialize_image(image)


@app.delete("/api/products/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_image(product_id: int, image_id: int, db: Session = Depends(get_db)):
    _get_product_or_404(db, product_id)
    image = (
        db.query(ProductImage)
        .filter(ProductImage.product_id == product_id, ProductImage.image_id == image_id)
        .first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    db.delete(image)
    db.commit()


@app.get("/api/addresses", response_model=list[AddressResponse])
def get_addresses(db: Session = Depends(get_db)):
    rows = db.query(Address).order_by(Address.address_id.desc()).all()
    return [serialize_address(address) for address in rows]


@app.get("/api/addresses/{address_id}", response_model=AddressResponse)
def get_address(address_id: int, db: Session = Depends(get_db)):
    return serialize_address(_get_address_or_404(db, address_id))


@app.post("/api/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(req: AddressRequest, db: Session = Depends(get_db)):
    address = Address(**req.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return serialize_address(address)


@app.get("/api/payments", response_model=list[PaymentResponse])
def get_payments(db: Session = Depends(get_db)):
    rows = db.query(Payment).order_by(Payment.paid_at.desc()).all()
    return [serialize_payment(payment) for payment in rows]


@app.get("/api/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return serialize_payment(payment)


@app.post("/api/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(req: PaymentRequest, db: Session = Depends(get_db)):
    order = _get_order_or_404(db, req.order_id)
    payment_amount = _money_decimal(req.amount)
    order_amount = _money_decimal(order.total_amount)
    if abs(payment_amount - order_amount) >= Decimal("0.01"):
        raise HTTPException(status_code=400, detail="Payment amount must match the order total exactly")
    payment = Payment(**req.model_dump())
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return serialize_payment(payment)


@app.post("/api/cart/add", response_model=CartResponse)
def add_cart_item(
    req: AddCartItemRequest,
    db: Session = Depends(get_db),
    current_user: dict[str, str | bool] = Depends(get_current_user),
):
    if str(current_user["user_id"]) != req.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify another user's cart")
    product = _get_product_or_404(db, req.product_id)
    cart = db.query(Cart).options(joinedload(Cart.items)).filter(Cart.user_id == req.user_id).first()
    if not cart:
        cart = Cart(user_id=req.user_id)
        db.add(cart)
        db.flush()
    item = next((row for row in cart.items if row.product_id == req.product_id), None)
    new_quantity = (item.quantity if item else 0) + req.quantity
    if new_quantity > product.stock_quantity:
        raise HTTPException(status_code=400, detail="Requested quantity exceeds stock")
    if item:
        item.quantity = new_quantity
    else:
        cart.items.append(CartItem(product_id=req.product_id, quantity=req.quantity, cart_id=cart.cart_id))
    db.commit()
    db.refresh(cart)
    return serialize_cart(cart)


@app.post("/api/cart/remove", response_model=CartResponse)
def remove_cart_item(req: RemoveCartItemRequest, db: Session = Depends(get_db)):
    cart = db.query(Cart).options(joinedload(Cart.items)).filter(Cart.user_id == req.user_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    item = next((row for row in cart.items if row.product_id == req.product_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    db.refresh(cart)
    return serialize_cart(cart)


@app.post("/api/cart/change-quantity", response_model=CartResponse)
def change_cart_quantity(req: AddCartItemRequest, db: Session = Depends(get_db)):
    cart = db.query(Cart).options(joinedload(Cart.items)).filter(Cart.user_id == req.user_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    item = next((row for row in cart.items if row.product_id == req.product_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    product = _get_product_or_404(db, req.product_id)
    if req.quantity > product.stock_quantity:
        raise HTTPException(status_code=400, detail="Requested quantity exceeds stock")
    item.quantity = req.quantity
    db.commit()
    db.refresh(cart)
    return serialize_cart(cart)


@app.get("/api/cart/user/{user_id}", response_model=CartResponse)
def get_cart(user_id: str, db: Session = Depends(get_db)):
    cart = db.query(Cart).options(joinedload(Cart.items)).filter(Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    return serialize_cart(cart)


@app.get("/api/orders", response_model=list[OrderResponse])
def get_orders(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Order)
        .options(joinedload(Order.order_items), joinedload(Order.payment))
        .order_by(Order.order_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [serialize_order(order) for order in rows]


@app.get("/api/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, db: Session = Depends(get_db)):
    return serialize_order(_get_order_or_404(db, order_id))


@app.post("/api/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(req: OrderRequest, db: Session = Depends(get_db)):
    address = _get_address_or_404(db, req.shipping_address_id)
    if address.user_id != req.user_id:
        raise HTTPException(status_code=400, detail="Address does not belong to the user")

    line_total = Decimal("0.00")
    for item in req.order_items:
        product = _get_product_or_404(db, item.product_id)
        if item.quantity > product.stock_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product {product.product_id}: {item.quantity} requested, {product.stock_quantity} available",
            )
        expected_price = _money_decimal(product.price)
        provided_price = _money_decimal(item.unit_price)
        if provided_price != expected_price:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unit price mismatch for product {product.product_id}: "
                    f"expected {expected_price}, got {provided_price}"
                ),
            )
        line_total += expected_price * item.quantity

    if line_total != _money_decimal(req.total_amount):
        raise HTTPException(status_code=400, detail="Order total does not match order items")

    order = Order(user_id=req.user_id, total_amount=req.total_amount, shipping_address_id=req.shipping_address_id)
    db.add(order)
    db.flush()
    for item in req.order_items:
        db.add(OrderItem(order_id=order.order_id, quantity=item.quantity, unit_price=item.unit_price, product_id=item.product_id))
        product = _get_product_or_404(db, item.product_id)
        product.stock_quantity -= item.quantity
    cart = db.query(Cart).filter(Cart.user_id == req.user_id).first()
    if cart:
        db.delete(cart)
    db.commit()
    return serialize_order(_get_order_or_404(db, order.order_id))


@app.get("/api/orders/{order_id}/items", response_model=list[OrderItemResponse])
def get_order_items(order_id: str, db: Session = Depends(get_db)):
    _get_order_or_404(db, order_id)
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    return [serialize_order_item(item) for item in items]


@app.get("/api/orders/{order_id}/items/{item_id}", response_model=OrderItemResponse)
def get_order_item(order_id: str, item_id: int, db: Session = Depends(get_db)):
    _get_order_or_404(db, order_id)
    item = db.query(OrderItem).filter(OrderItem.order_id == order_id, OrderItem.order_item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")
    return serialize_order_item(item)


@app.post("/api/orders/{order_id}/items", response_model=OrderItemResponse, status_code=status.HTTP_201_CREATED)
def create_order_item(order_id: str, req: OrderItemRequest, db: Session = Depends(get_db)):
    _get_order_or_404(db, order_id)
    product = _get_product_or_404(db, req.product_id)
    if req.quantity > product.stock_quantity:
        raise HTTPException(status_code=400, detail="Requested quantity exceeds stock")
    item = OrderItem(order_id=order_id, quantity=req.quantity, unit_price=req.unit_price, product_id=req.product_id)
    db.add(item)
    product.stock_quantity -= req.quantity
    db.commit()
    db.refresh(item)
    return serialize_order_item(item)


@app.put("/api/orders/{order_id}/items/{item_id}", response_model=OrderItemResponse)
def update_order_item(order_id: str, item_id: int, req: OrderItemRequest, db: Session = Depends(get_db)):
    _get_order_or_404(db, order_id)
    item = db.query(OrderItem).filter(OrderItem.order_id == order_id, OrderItem.order_item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")
    _get_product_or_404(db, req.product_id)
    item.quantity = req.quantity
    item.unit_price = req.unit_price
    item.product_id = req.product_id
    db.commit()
    db.refresh(item)
    return serialize_order_item(item)


@app.delete("/api/orders/{order_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order_item(order_id: str, item_id: int, db: Session = Depends(get_db)):
    _get_order_or_404(db, order_id)
    item = db.query(OrderItem).filter(OrderItem.order_id == order_id, OrderItem.order_item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")
    db.delete(item)
    db.commit()


@app.get("/api/userinteractions", response_model=list[UserInteractionResponse])
def get_interactions(db: Session = Depends(get_db)):
    rows = db.query(UserInteraction).order_by(UserInteraction.interaction_time.desc()).all()
    return [serialize_interaction(interaction) for interaction in rows]


@app.get("/api/userinteractions/{interaction_id}", response_model=UserInteractionResponse)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(UserInteraction).filter(UserInteraction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return serialize_interaction(interaction)


@app.post("/api/userinteractions", response_model=UserInteractionResponse, status_code=status.HTTP_201_CREATED)
def create_interaction(req: UserInteractionRequest, db: Session = Depends(get_db)):
    _get_product_or_404(db, req.product_id)
    interaction_type = _parse_interaction_type(req.interaction_type)
    interaction = UserInteraction(
        user_id=req.user_id,
        product_id=req.product_id,
        interaction_type=interaction_type,
        interaction_metadata=req.metadata,
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return serialize_interaction(interaction)


@app.post("/v1/events", response_model=EventAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def ingest_event(req: EventRequest, db: Session = Depends(get_db)):
    _get_product_or_404(db, req.item_id)
    event_id = req.event_id or _new_event_id(req.user_id, req.item_id)
    existing = db.query(UserInteraction).filter(UserInteraction.external_event_id == event_id).first()
    if existing:
        return EventAcceptedResponse(eventId=event_id, status="accepted")

    interaction = UserInteraction(
        user_id=req.user_id,
        product_id=req.item_id,
        interaction_type=_parse_interaction_type(req.action_type),
        interaction_time=req.timestamp or utc_now(),
        interaction_metadata=json.dumps(req.context),
        external_event_id=event_id,
    )
    db.add(interaction)
    db.commit()
    return EventAcceptedResponse(eventId=event_id, status="accepted")


@app.get("/v1/recommendations/{user_id}", response_model=RecommendationEnvelope)
def get_recommendations(
    user_id: str,
    algorithm: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    explain: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    service = SQLRecommendationService(db)
    recommendations, metadata = service.recommend(user_id, top_k=limit, algorithm=algorithm, explain=explain)
    return RecommendationEnvelope(
        userId=user_id,
        recommendations=[
            RecommendationItemResponse(
                itemId=result.product_id,
                score=result.score,
                rank=index + 1,
                explanation=result.explanation,
            )
            for index, result in enumerate(recommendations)
        ],
        metadata=metadata,
    )


@app.post("/v1/recommendations/batch", response_model=BatchRecommendationResponse)
def get_batch_recommendations(req: BatchRecommendationRequest, db: Session = Depends(get_db)):
    service = SQLRecommendationService(db)
    results = []
    for user_id in req.user_ids:
        recommendations, metadata = service.recommend(
            user_id,
            top_k=req.limit,
            algorithm=req.algorithm,
            explain=req.explain,
        )
        results.append(
            RecommendationEnvelope(
                userId=user_id,
                recommendations=[
                    RecommendationItemResponse(
                        itemId=result.product_id,
                        score=result.score,
                        rank=index + 1,
                        explanation=result.explanation,
                    )
                    for index, result in enumerate(recommendations)
                ],
                metadata=metadata,
            )
        )
    return BatchRecommendationResponse(results=results)


@app.get("/v1/users/{user_id}/preferences", response_model=UserPreferenceResponse)
def get_user_preferences(user_id: str, db: Session = Depends(get_db)):
    preference = SQLRecommendationService(db).get_or_create_preferences(user_id)
    return serialize_preference(preference)


@app.put("/v1/users/{user_id}/preferences", response_model=UserPreferenceResponse)
def update_user_preferences(user_id: str, req: UserPreferenceRequest, db: Session = Depends(get_db)):
    preference = SQLRecommendationService(db).update_preferences(user_id, req)
    return serialize_preference(preference)


@app.post("/v1/models/train", response_model=TrainModelResponse, status_code=status.HTTP_201_CREATED)
def train_model(req: TrainModelRequest, db: Session = Depends(get_db)):
    service = SQLRecommendationService(db)
    model, metadata = service.train_model(
        req.algorithm,
        req.hyperparameters,
        req.data_range.model_dump() if req.data_range else None,
    )
    db.add(model)
    db.flush()
    job = TrainingJob(
        model_id=model.model_id,
        algorithm=req.algorithm,
        status="completed",
        message=json.dumps(metadata),
        completed_at=utc_now(),
    )
    db.add(job)
    db.commit()
    return TrainModelResponse(jobId=job.job_id, status=job.status, modelId=model.model_id)


@app.get("/v1/models/{model_id}/metrics", response_model=ModelMetricsResponse)
def get_model_metrics(model_id: str, db: Session = Depends(get_db)):
    model = db.query(MLModel).filter(MLModel.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return ModelMetricsResponse(modelId=model.model_id, metrics=json.loads(model.metrics_json))


@app.post("/v1/experiments", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
def create_experiment(req: ExperimentRequest, db: Session = Depends(get_db)):
    control_model = db.query(MLModel).filter(MLModel.model_id == req.control_model_id).first()
    variant_model = db.query(MLModel).filter(MLModel.model_id == req.variant_model_id).first()
    if not control_model or not variant_model:
        raise HTTPException(status_code=404, detail="Both control and variant models must exist")

    running = db.query(Experiment).filter(Experiment.status == "running").all()
    for experiment in running:
        experiment.status = "concluded"
        experiment.ended_at = utc_now()

    experiment = Experiment(
        name=req.name,
        status="running",
        config_json=json.dumps(
            {
                "metrics": req.metrics,
                "trafficSplit": req.traffic_split.model_dump(),
                "salt": generate_experiment_salt(),
            }
        ),
    )
    db.add(experiment)
    db.flush()
    db.add_all(
        [
            ModelVariant(
                experiment_id=experiment.experiment_id,
                model_id=control_model.model_id,
                variant_name="control",
                traffic_percent=req.traffic_split.control,
            ),
            ModelVariant(
                experiment_id=experiment.experiment_id,
                model_id=variant_model.model_id,
                variant_name="variant",
                traffic_percent=req.traffic_split.variant,
            ),
        ]
    )
    db.commit()
    return ExperimentResponse(experimentId=experiment.experiment_id, status=experiment.status)


@app.get("/api/productimages", response_model=list[ProductImageResponse])
def list_product_images(db: Session = Depends(get_db)):
    return [serialize_image(image) for image in db.query(ProductImage).all()]


@app.get("/api/productimages/{image_id}", response_model=ProductImageResponse)
def get_product_images_legacy(image_id: int, db: Session = Depends(get_db)):
    image = db.query(ProductImage).filter(ProductImage.image_id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return serialize_image(image)


@app.post("/api/productimages", response_model=ProductImageResponse, status_code=status.HTTP_201_CREATED)
def create_product_images_legacy(req: ProductImageRequest, db: Session = Depends(get_db)):
    if req.product_id is None:
        raise HTTPException(status_code=422, detail="product_id is required")
    return create_product_image(req.product_id, req, db)


def serialize_image(image: ProductImage) -> ProductImageResponse:
    return ProductImageResponse(
        image_id=image.image_id,
        url=image.url,
        is_primary=image.is_primary,
        product_id=image.product_id,
    )


def serialize_product(product: Product) -> ProductResponse:
    return ProductResponse(
        product_id=product.product_id,
        name=product.name,
        description=product.description,
        price=_money(product.price),
        stock_quantity=product.stock_quantity,
        created_at=product.created_at,
        category_id=product.category_id,
        images=[serialize_image(image) for image in product.images],
    )


def serialize_address(address: Address) -> AddressResponse:
    return AddressResponse(
        address_id=address.address_id,
        street=address.street,
        city=address.city,
        state=address.state,
        postal_code=address.postal_code,
        country=address.country,
        user_id=address.user_id,
    )


def serialize_payment(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        payment_id=payment.payment_id,
        amount=_money(payment.amount),
        provider=payment.provider,
        order_id=payment.order_id,
    )


def serialize_cart(cart: Cart) -> CartResponse:
    return CartResponse(
        cart_id=cart.cart_id,
        user_id=cart.user_id,
        created_at=cart.created_at,
        items=[CartItemResponse(product_id=item.product_id, quantity=item.quantity) for item in cart.items],
    )


def serialize_order_item(item: OrderItem) -> OrderItemResponse:
    return OrderItemResponse(
        order_item_id=item.order_item_id,
        quantity=item.quantity,
        unit_price=_money(item.unit_price),
        product_id=item.product_id,
    )


def serialize_order(order: Order) -> OrderResponse:
    return OrderResponse(
        order_id=order.order_id,
        order_date=order.order_date,
        status=order.status.value,
        total_amount=_money(order.total_amount),
        user_id=order.user_id,
        shipping_address_id=order.shipping_address_id,
        order_items=[serialize_order_item(item) for item in order.order_items],
        payment=serialize_payment(order.payment) if order.payment else None,
    )


def serialize_interaction(interaction: UserInteraction) -> UserInteractionResponse:
    return UserInteractionResponse(
        id=interaction.id,
        user_id=interaction.user_id,
        product_id=interaction.product_id,
        interaction_type=interaction.interaction_type.value,
        metadata=interaction.interaction_metadata,
    )


def serialize_preference(preference: UserPreference) -> UserPreferenceResponse:
    return UserPreferenceResponse(
        userId=preference.user_id,
        categories=json.loads(preference.categories_json),
        diversity=preference.diversity,
        recency_bias=preference.recency_bias,
        excludeViewed=preference.exclude_viewed,
        algorithm=preference.algorithm,
        maxPerCategory=preference.max_per_category,
        updatedAt=preference.updated_at,
    )


def _serialize_category_tree(category: Category, children: dict[int | None, list[Category]]) -> CategoryResponse:
    return CategoryResponse(
        id=category.category_id,
        name=category.name,
        sub_categories=[_serialize_category_tree(child, children) for child in children.get(category.category_id, [])],
    )


def _parse_interaction_type(value: str) -> InteractionType:
    normalized = value.strip().lower()
    mapping = {
        "view": InteractionType.View,
        "click": InteractionType.Click,
        "cart": InteractionType.AddToCart,
        "addtocart": InteractionType.AddToCart,
        "purchase": InteractionType.Purchase,
        "search": InteractionType.Search,
        "comment": InteractionType.Review,
        "review": InteractionType.Review,
        "like": InteractionType.Click,
        "save": InteractionType.Click,
        "share": InteractionType.Click,
    }
    if normalized not in mapping:
        raise HTTPException(status_code=422, detail="Unsupported interaction type")
    return mapping[normalized]


def _get_category_or_404(db: Session, category_id: int) -> Category:
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


def _get_product_or_404(db: Session, product_id: int) -> Product:
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _get_address_or_404(db: Session, address_id: int) -> Address:
    address = db.query(Address).filter(Address.address_id == address_id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


def _get_order_or_404(db: Session, order_id: str) -> Order:
    order = (
        db.query(Order)
        .options(joinedload(Order.order_items), joinedload(Order.payment))
        .filter(Order.order_id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def _money(value) -> float:
    return float(_money_decimal(value))


def _money_decimal(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _new_event_id(user_id: str, item_id: int) -> str:
    return f"evt-{user_id}-{item_id}-{uuid.uuid4().hex}"
