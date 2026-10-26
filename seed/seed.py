import json
from decimal import Decimal
from pathlib import Path
import asyncio

from sqlalchemy import select

# ---- change these imports to match your project ----
from backend.app.services.storage import get_postgresql_db,put_bytes
from backend.app.models import Product


BASE_DIR = Path(__file__).resolve().parent
EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]


async def upload_image(code: str, images_dir: Path) -> str:
    """Upload <images_dir>/<code>.<ext> to MinIO and return the object key."""
    for ext in EXTENSIONS:
        file = images_dir / f"{code}{ext}"
        if file.exists():
            key = f"products/{code}{ext}"
            content_type = "image/jpeg" if ext in (".jpg", ".jpeg") else f"image/{ext[1:]}"
            # put_bytes is a normal (blocking) function, so run it in a thread
            await asyncio.to_thread(put_bytes, key, file.read_bytes(), content_type)
            return key
    print(f"  image not found for {code}")
    return f"products/{code}.jpg"


async def seed_products(
    db,
    json_path: Path = BASE_DIR / "products.json",
    images_dir: Path = BASE_DIR / "images",
) -> int:
    """Insert or update all products from the JSON file. Returns how many were processed."""
    items = json.loads(Path(json_path).read_text(encoding="utf-8"))

    async with db.get_session() as session:
        for item in items:
            result = await session.execute(
                select(Product).where(Product.name == item["name"])
            )
            product = result.scalar_one_or_none()

            if product is None:
                product = Product(name=item["name"])
                session.add(product)

            product.description = item["description"]
            product.category = item["category"]
            product.price = Decimal(item["price"])
            product.stock = item["stock"]
            product.image_key = await upload_image(item["image"], Path(images_dir))

        await session.commit()  # get_session() does not commit for you

    return len(items)

async def main():
    db = get_postgresql_db()
    await db.startup()
    try:
        count = await seed_products(db)
        print(f"Seeded {count} products")
    finally:
        await db.teardown()


if __name__ == "__main__":
    asyncio.run(main())