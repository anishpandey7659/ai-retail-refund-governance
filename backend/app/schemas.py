from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from backend.app.models import Product
import datetime as dt
from backend.app.services.storage import presigned_get
import uuid


class ProductOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    category: str
    price: Decimal
    stock: int
    image_url: str  # temporary presigned link, NOT stored in the database


def to_out(product: Product) -> ProductOut:
    return ProductOut(
        id=product.id,
        name=product.name,
        description=product.description,
        category=product.category,
        price=product.price,
        stock=product.stock,
        image_url=presigned_get(product.image_key),  # computed locally, no network call
    )


class CartLine(BaseModel):
    product_id: str
    qty: int = Field(ge=1, le=20)

class CheckoutIn(BaseModel):
    lines: list[CartLine] = Field(min_length=1)
    shipping_address: str
    card_number: str          # fake card, Luhn-checked, never stored
    card_exp: str
    card_cvc: str


class OrderItemOut(BaseModel):
    id: str
    product_id: str
    name: str
    unit_price: Decimal
    qty: int


class OrderOut(BaseModel):
    id: str
    status: str
    total: Decimal
    payment_last4: str
    placed_at: dt.datetime
    items: list[OrderItemOut]


class ReturnCreateOut(BaseModel):
    id: str
    status: str
    amount: Decimal


class ReturnOut(BaseModel):
    id: str
    order_id: str
    order_item_id: str
    reason_code: str
    reason_text: str
    status: str
    amount: Decimal
    ai_proposed_decision: str | None
    final_decision: str | None
    created_at: dt.datetime
    photo_urls: list[str] = []