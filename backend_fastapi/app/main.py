from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session, joinedload

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
    UserInteraction,
)
from .schemas import *

app = FastAPI(title="Recommendation System API (FastAPI)")
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/categories", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    roots = db.query(Category).filter(Category.parent_category_id.is_(None)).all()
    return [
        CategoryResponse(
            id=c.category_id,
            name=c.name,
            sub_categories=[
                CategoryResponse(id=s.category_id, name=s.name, sub_categories=[])
                for s in db.query(Category).filter(Category.parent_category_id == c.category_id).all()
            ],
        )
        for c in roots
    ]


@app.get("/api/categories/{category_id}")
def get_category(category_id: int, db: Session = Depends(get_db)):
    c = db.query(Category).filter(Category.category_id == category_id).first()
    if not c:
        raise HTTPException(404, "Category not found")
    subs = db.query(Category).filter(Category.parent_category_id == c.category_id).all()
    return CategoryResponse(id=c.category_id, name=c.name, sub_categories=[CategoryResponse(id=s.category_id, name=s.name, sub_categories=[]) for s in subs])


@app.post("/api/categories", response_model=CategoryResponse, status_code=201)
def create_category(req: CategoryRequest, db: Session = Depends(get_db)):
    c = Category(name=req.name, parent_category_id=req.parent_category_id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return CategoryResponse(id=c.category_id, name=c.name, sub_categories=[])


@app.put("/api/categories/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, req: CategoryRequest, db: Session = Depends(get_db)):
    c = db.query(Category).filter(Category.category_id == category_id).first()
    if not c:
        raise HTTPException(404, "Category not found")
    c.name = req.name
    c.parent_category_id = req.parent_category_id
    db.commit()
    subs = db.query(Category).filter(Category.parent_category_id == c.category_id).all()
    return CategoryResponse(id=c.category_id, name=c.name, sub_categories=[CategoryResponse(id=s.category_id, name=s.name, sub_categories=[]) for s in subs])


@app.delete("/api/categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    c = db.query(Category).filter(Category.category_id == category_id).first()
    if not c:
        raise HTTPException(404, "Category not found")
    db.delete(c)
    db.commit()


@app.get("/api/products", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    rows = db.query(Product).options(joinedload(Product.images)).all()
    return [serialize_product(p) for p in rows]


@app.get("/api/products/{product_id}", response_model=ProductResponse | None)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(Product).options(joinedload(Product.images)).filter(Product.product_id == product_id).first()
    return serialize_product(p) if p else None


@app.post("/api/products", response_model=ProductResponse, status_code=201)
def create_product(req: ProductRequest, db: Session = Depends(get_db)):
    p = Product(**req.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return serialize_product(p)


@app.get("/api/products/{product_id}/images", response_model=list[ProductImageResponse])
def get_product_images(product_id: int, db: Session = Depends(get_db)):
    return [serialize_image(i) for i in db.query(ProductImage).filter(ProductImage.product_id == product_id).all()]


@app.get("/api/products/{product_id}/images/{image_id}", response_model=ProductImageResponse | None)
def get_product_image(product_id: int, image_id: int, db: Session = Depends(get_db)):
    i = db.query(ProductImage).filter(ProductImage.product_id == product_id, ProductImage.image_id == image_id).first()
    return serialize_image(i) if i else None


@app.post("/api/products/{product_id}/images", response_model=ProductImageResponse, status_code=201)
def create_product_image(product_id: int, req: ProductImageRequest, db: Session = Depends(get_db)):
    i = ProductImage(url=req.url, is_primary=req.is_primary, product_id=product_id)
    db.add(i)
    db.commit()
    db.refresh(i)
    return serialize_image(i)


@app.put("/api/products/{product_id}/images/{image_id}", response_model=ProductImageResponse)
def update_product_image(product_id: int, image_id: int, req: ProductImageRequest, db: Session = Depends(get_db)):
    i = db.query(ProductImage).filter(ProductImage.product_id == product_id, ProductImage.image_id == image_id).first()
    if not i:
        raise HTTPException(404, "Image not found")
    i.url = req.url
    i.is_primary = req.is_primary
    db.commit()
    return serialize_image(i)


@app.delete("/api/products/{product_id}/images/{image_id}", status_code=204)
def delete_product_image(product_id: int, image_id: int, db: Session = Depends(get_db)):
    i = db.query(ProductImage).filter(ProductImage.product_id == product_id, ProductImage.image_id == image_id).first()
    if not i:
        raise HTTPException(404, "Image not found")
    db.delete(i)
    db.commit()


@app.get("/api/addresses", response_model=list[AddressResponse])
def get_addresses(db: Session = Depends(get_db)):
    return [AddressResponse(**{"address_id": a.address_id, **to_camel_address(a)}) for a in db.query(Address).all()]


@app.get("/api/addresses/{address_id}", response_model=AddressResponse | None)
def get_address(address_id: int, db: Session = Depends(get_db)):
    a = db.query(Address).filter(Address.address_id == address_id).first()
    return AddressResponse(**{"address_id": a.address_id, **to_camel_address(a)}) if a else None


@app.post("/api/addresses", response_model=AddressResponse, status_code=201)
def create_address(req: AddressRequest, db: Session = Depends(get_db)):
    a = Address(**req.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return AddressResponse(**{"address_id": a.address_id, **to_camel_address(a)})


@app.get("/api/payments", response_model=list[PaymentResponse])
def get_payments(db: Session = Depends(get_db)):
    return [PaymentResponse(payment_id=p.payment_id, amount=float(p.amount), provider=p.provider, order_id=p.order_id) for p in db.query(Payment).all()]


@app.get("/api/payments/{payment_id}", response_model=PaymentResponse | None)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    p = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    return PaymentResponse(payment_id=p.payment_id, amount=float(p.amount), provider=p.provider, order_id=p.order_id) if p else None


@app.post("/api/payments", response_model=PaymentResponse, status_code=201)
def create_payment(req: PaymentRequest, db: Session = Depends(get_db)):
    p = Payment(**req.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return PaymentResponse(payment_id=p.payment_id, amount=float(p.amount), provider=p.provider, order_id=p.order_id)


@app.post("/api/cart/add", response_model=CartResponse)
def add_cart_item(req: AddCartItemRequest, db: Session = Depends(get_db)):
    cart = db.query(Cart).options(joinedload(Cart.items)).filter(Cart.user_id == req.user_id).first()
    if not cart:
        cart = Cart(user_id=req.user_id)
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


@app.post("/api/cart/remove", response_model=CartResponse)
def remove_cart_item(req: RemoveCartItemRequest, db: Session = Depends(get_db)):
    cart = db.query(Cart).options(joinedload(Cart.items)).filter(Cart.user_id == req.user_id).first()
    if not cart:
        raise HTTPException(404, "Cart not found")
    item = next((i for i in cart.items if i.product_id == req.product_id), None)
    if not item:
        raise HTTPException(404, "Item not found")
    db.delete(item)
    db.commit()
    db.refresh(cart)
    return serialize_cart(cart)


@app.post("/api/cart/change-quantity", response_model=CartResponse)
def change_cart_quantity(req: AddCartItemRequest, db: Session = Depends(get_db)):
    cart = db.query(Cart).options(joinedload(Cart.items)).filter(Cart.user_id == req.user_id).first()
    if not cart:
        raise HTTPException(404, "Cart not found")
    item = next((i for i in cart.items if i.product_id == req.product_id), None)
    if not item:
        raise HTTPException(404, "Item not found")
    if req.quantity <= 0:
        db.delete(item)
    else:
        item.quantity = req.quantity
    db.commit()
    db.refresh(cart)
    return serialize_cart(cart)


@app.get("/api/cart/user/{user_id}", response_model=CartResponse)
def get_cart(user_id: str, db: Session = Depends(get_db)):
    cart = db.query(Cart).options(joinedload(Cart.items)).filter(Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(404, "Cart not found")
    return serialize_cart(cart)


@app.get("/api/orders", response_model=list[OrderResponse])
def get_orders(db: Session = Depends(get_db)):
    return [serialize_order(o) for o in db.query(Order).options(joinedload(Order.order_items), joinedload(Order.payment)).all()]


@app.get("/api/orders/{order_id}", response_model=OrderResponse | None)
def get_order(order_id: str, db: Session = Depends(get_db)):
    o = db.query(Order).options(joinedload(Order.order_items), joinedload(Order.payment)).filter(Order.order_id == order_id).first()
    return serialize_order(o) if o else None


@app.post("/api/orders", response_model=OrderResponse, status_code=201)
def create_order(req: OrderRequest, db: Session = Depends(get_db)):
    o = Order(user_id=req.user_id, total_amount=req.total_amount, shipping_address_id=req.shipping_address_id)
    db.add(o)
    db.flush()
    for item in req.order_items:
        db.add(OrderItem(order_id=o.order_id, quantity=item.quantity, unit_price=item.unit_price, product_id=item.product_id))
    db.commit()
    return serialize_order(db.query(Order).options(joinedload(Order.order_items), joinedload(Order.payment)).filter(Order.order_id == o.order_id).first())


@app.get("/api/orders/{order_id}/items", response_model=list[OrderItemResponse])
def get_order_items(order_id: str, db: Session = Depends(get_db)):
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    return [OrderItemResponse(order_item_id=i.order_item_id, quantity=i.quantity, unit_price=float(i.unit_price), product_id=i.product_id) for i in items]


@app.get("/api/orders/{order_id}/items/{item_id}", response_model=OrderItemResponse | None)
def get_order_item(order_id: str, item_id: int, db: Session = Depends(get_db)):
    i = db.query(OrderItem).filter(OrderItem.order_id == order_id, OrderItem.order_item_id == item_id).first()
    return OrderItemResponse(order_item_id=i.order_item_id, quantity=i.quantity, unit_price=float(i.unit_price), product_id=i.product_id) if i else None


@app.post("/api/orders/{order_id}/items", response_model=OrderItemResponse, status_code=201)
def create_order_item(order_id: str, req: OrderItemRequest, db: Session = Depends(get_db)):
    i = OrderItem(order_id=order_id, quantity=req.quantity, unit_price=req.unit_price, product_id=req.product_id)
    db.add(i)
    db.commit()
    db.refresh(i)
    return OrderItemResponse(order_item_id=i.order_item_id, quantity=i.quantity, unit_price=float(i.unit_price), product_id=i.product_id)


@app.put("/api/orders/{order_id}/items/{item_id}", response_model=OrderItemResponse)
def update_order_item(order_id: str, item_id: int, req: OrderItemRequest, db: Session = Depends(get_db)):
    i = db.query(OrderItem).filter(OrderItem.order_id == order_id, OrderItem.order_item_id == item_id).first()
    if not i:
        raise HTTPException(404, "Order item not found")
    i.quantity = req.quantity
    i.unit_price = req.unit_price
    i.product_id = req.product_id
    db.commit()
    return OrderItemResponse(order_item_id=i.order_item_id, quantity=i.quantity, unit_price=float(i.unit_price), product_id=i.product_id)


@app.delete("/api/orders/{order_id}/items/{item_id}", status_code=204)
def delete_order_item(order_id: str, item_id: int, db: Session = Depends(get_db)):
    i = db.query(OrderItem).filter(OrderItem.order_id == order_id, OrderItem.order_item_id == item_id).first()
    if not i:
        raise HTTPException(404, "Order item not found")
    db.delete(i)
    db.commit()


@app.get("/api/userinteractions", response_model=list[UserInteractionResponse])
def get_interactions(db: Session = Depends(get_db)):
    return [UserInteractionResponse(id=u.id, user_id=u.user_id, product_id=u.product_id, interaction_type=u.interaction_type.value, metadata=u.metadata) for u in db.query(UserInteraction).all()]


@app.get("/api/userinteractions/{interaction_id}", response_model=UserInteractionResponse | None)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    u = db.query(UserInteraction).filter(UserInteraction.id == interaction_id).first()
    return UserInteractionResponse(id=u.id, user_id=u.user_id, product_id=u.product_id, interaction_type=u.interaction_type.value, metadata=u.metadata) if u else None


@app.post("/api/userinteractions", response_model=UserInteractionResponse, status_code=201)
def create_interaction(req: UserInteractionRequest, db: Session = Depends(get_db)):
    interaction_type = InteractionType[req.interaction_type] if req.interaction_type in InteractionType.__members__ else InteractionType(req.interaction_type)
    u = UserInteraction(user_id=req.user_id, product_id=req.product_id, interaction_type=interaction_type, metadata=req.metadata)
    db.add(u)
    db.commit()
    db.refresh(u)
    return UserInteractionResponse(id=u.id, user_id=u.user_id, product_id=u.product_id, interaction_type=u.interaction_type.value, metadata=u.metadata)


# Compatibility endpoints
@app.get("/api/productimages", response_model=list[ProductImageResponse])
def list_product_images(db: Session = Depends(get_db)):
    return [serialize_image(i) for i in db.query(ProductImage).all()]


@app.get("/api/productimages/{image_id}", response_model=ProductImageResponse | None)
def get_product_images_legacy(image_id: int, db: Session = Depends(get_db)):
    i = db.query(ProductImage).filter(ProductImage.image_id == image_id).first()
    return serialize_image(i) if i else None


@app.post("/api/productimages", response_model=ProductImageResponse, status_code=201)
def create_product_images_legacy(req: ProductImageRequest, db: Session = Depends(get_db)):
    if req.product_id is None:
        raise HTTPException(422, "product_id is required")
    i = ProductImage(url=req.url, is_primary=req.is_primary, product_id=req.product_id)
    db.add(i)
    db.commit()
    db.refresh(i)
    return serialize_image(i)


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
        status=o.status.value,
        total_amount=float(o.total_amount),
        user_id=o.user_id,
        shipping_address_id=o.shipping_address_id,
        order_items=[OrderItemResponse(order_item_id=i.order_item_id, quantity=i.quantity, unit_price=float(i.unit_price), product_id=i.product_id) for i in o.order_items],
        payment=PaymentResponse(payment_id=o.payment.payment_id, amount=float(o.payment.amount), provider=o.payment.provider, order_id=o.payment.order_id) if o.payment else None,
    )


def to_camel_address(a: Address) -> dict:
    return {
        "street": a.street,
        "city": a.city,
        "state": a.state,
        "postal_code": a.postal_code,
        "country": a.country,
        "user_id": a.user_id,
    }
