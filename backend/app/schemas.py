from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from backend.app.models import Product
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

