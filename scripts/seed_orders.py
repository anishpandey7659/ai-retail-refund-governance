
import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Adjust these imports to your project structure.
from backend.app.services.storage import get_postgresql_db
from backend.app.models import Order, OrderItem,Product,User


async def seed_orders(session: AsyncSession) -> None:
    # Find an existing user and products.
    user = await session.scalar(select(User).order_by(User.id).offset(2).limit(1)) # offset 0=>1st user 1=>2nd ..
    products = list(
        (
            await session.scalars(
                select(Product).order_by(Product.name).limit(5)
            )
        ).all()
    )

    if user is None:
        raise RuntimeError("No users found. Seed users first.")

    if len(products) < 2:
        raise RuntimeError("At least two products are required.")

    # Avoid inserting the same seed data repeatedly.
    marker = "[SEED-ORDER]"
    existing = await session.scalar(
        select(Order.id).where(
            Order.user_id == user.id,
            Order.shipping_address.startswith(marker),
        ).limit(1)
    )

    if existing is not None:
        print("Seed orders already exist. Nothing to do.")
        return

    # Three sample orders with different products and quantities.
    scenarios = [
        [(products[0], 1), (products[1], 2)],
        [(products[1], 1)],
        [(products[0], 2), (products[1], 1)],
    ]

    try:
        for index, lines in enumerate(scenarios, start=1):
            total = Decimal("0.00")

            # Validate stock before changing it.
            for product, qty in lines:
                if product.stock < qty:
                    raise RuntimeError(
                        f"Insufficient stock for {product.name}"
                    )
                total += product.price * qty

            order = Order(
                user_id=user.id,
                status="placed",
                total_amount=total,
                shipping_address=(
                    f"{marker} Sample customer address {index}"
                ),
                card_last4="4242",
            )

            session.add(order)
            await session.flush()  # Generate order.id.

            for product, qty in lines:
                session.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        name_at_purchase=product.name,
                        price_at_purchase=product.price,
                        quantity=qty,
                    )
                )

                # Keep inventory consistent with the seeded purchases.
                product.stock -= qty

            print(f"Prepared order {order.id}: ${total}")

        await session.commit()
        print("Successfully seeded 3 orders.")

    except Exception:
        await session.rollback()
        raise


async def main() -> None:
    db = get_postgresql_db()

    await db.startup()
    try:
        async with db.get_session() as session:
            await seed_orders(session)
    finally:
        await db.teardown()


if __name__ == "__main__":
    asyncio.run(main())