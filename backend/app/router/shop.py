import asyncio
import uuid
from decimal import Decimal
from pathlib import PurePosixPath
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas import ProductOut,to_out
from backend.dependency import get_db_session          
from backend.app.models import Product
from backend.app.services.storage import delete_object, put_bytes


router = APIRouter(prefix="/products", tags=["products"])

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("", response_model=ProductOut, status_code=201)
async def create_product(
    name: Annotated[str, Form(min_length=1, max_length=64)],
    description: Annotated[str, Form(min_length=1)],
    category: Annotated[str, Form(min_length=1, max_length=60)],
    price: Annotated[Decimal, Form(gt=0, max_digits=10, decimal_places=2)],
    image: UploadFile = File(...),
    stock: Annotated[int, Form(ge=0)] = 100,
    session: AsyncSession = Depends(get_db_session),
):
    # 1. Validate the image
    content_type = image.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "Image must be JPEG, PNG or WebP")

    data = await image.read()
    if not data:
        raise HTTPException(400, "Image file is empty")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(400, "Image is larger than 5 MB")

    # 2. Reject duplicate names early (name is unique in the table)
    existing = await session.scalar(select(Product.id).where(Product.name == name))
    if existing:
        raise HTTPException(409, f"A product named '{name}' already exists")

    # 3. Upload to MinIO. boto3 is sync, so run it in a worker thread.
    product_id = uuid.uuid4()
    key = f"products/{product_id}{ALLOWED_IMAGE_TYPES[content_type]}"
    await asyncio.to_thread(put_bytes, key, data, content_type)

    # 4. Save the row. If this fails, remove the file so nothing is orphaned.
    product = Product(
        id=product_id,
        name=name,
        description=description,
        category=category,
        price=price,
        stock=stock,
        image_key=key,
    )
    session.add(product)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        await asyncio.to_thread(delete_object, key)
        raise HTTPException(409, f"A product named '{name}' already exists")
    except Exception:
        await session.rollback()
        await asyncio.to_thread(delete_object, key)
        raise

    return to_out(product)


@router.get("", response_model=list[ProductOut])
async def list_products(
    category: str | None = None,
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
):
    query = select(Product).order_by(Product.name).limit(min(limit, 100)).offset(offset)
    if category:
        query = query.where(Product.category == category)
    result = await session.scalars(query)
    return [to_out(p) for p in result.all()]


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
):
    product = await session.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return to_out(product)