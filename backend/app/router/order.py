from __future__ import annotations

import datetime as dt
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models import Order, OrderItem, Product, User
from backend.app.ratelimit import limiter
from backend.app.schemas import CheckoutIn, OrderItemOut, OrderOut, OrderReviewOut
from backend.app.security.auth import require_role
from backend.app.services import mail
from backend.app.services.payment import charge
from backend.dependency import get_db_session

order_router = APIRouter(prefix="/orders", tags=["orders"])

def _out(o: Order) -> OrderOut:
    return OrderOut(
        id=str(o.id), status=o.status, total=o.total_amount, payment_last4=o.card_last4,
        placed_at=o.created_at,
        items=[
            OrderItemOut(
                id=str(i.id), product_id=str(i.product_id), name=i.name_at_purchase,
                unit_price=i.price_at_purchase, qty=i.quantity,
            )
            for i in o.items
        ],
    )


@order_router.post("", response_model=OrderOut, status_code=201)
@limiter.limit("60/minute")
async def checkout(
    request: Request,
    body: CheckoutIn,
    p: User = Depends(require_role("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> OrderOut:
    ids = [line.product_id for line in body.lines]
    products = {
        str(pr.id): pr
        for pr in (await session.execute(select(Product).where(Product.id.in_(ids)))).scalars()
    }
    if len(products) != len(set(ids)):
        raise HTTPException(400, "one or more products not found")

    items, total = [], Decimal("0")
    for line in body.lines:
        pr = products[line.product_id]
        if pr.stock < line.qty:
            raise HTTPException(409, f"insufficient stock for {pr.name}")
        total += pr.price * line.qty
        items.append((pr, line.qty))

    last4 = charge(body.card_number, body.card_exp, body.card_cvc)

    order = Order(
        user_id=p.id, status="placed", total_amount=total,
        shipping_address=body.shipping_address, card_last4=last4,
    )
    session.add(order)
    await session.flush()
    for pr, qty in items:
        session.add(
            OrderItem(
                order_id=order.id, product_id=pr.id, name_at_purchase=pr.name,
                price_at_purchase=pr.price, quantity=qty,
            )
        )
        pr.stock -= qty
    await session.commit()

    full = (
        await session.execute(
            select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
        )
    ).scalar_one()
    mail.send(p.email, "Your ReturnGuard order is confirmed",
              f"Order {full.id} placed. Total ${full.total_amount}.")
    return _out(full)


@order_router.get("", response_model=list[OrderOut])
async def my_orders(
    p: User = Depends(require_role("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> list[OrderOut]:
    rows = (
        await session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == p.id)
            .order_by(Order.created_at.desc())
        )
    ).scalars().all()
    return [_out(o) for o in rows]


@order_router.get("/review", response_model=list[OrderReviewOut])
async def review_orders(
    _: User = Depends(require_role("admin", "reviewer")),
    session: AsyncSession = Depends(get_db_session),
) -> list[OrderReviewOut]:
    rows = (
        await session.execute(
            select(Order, User)
            .join(User, Order.user_id == User.id)
            .options(selectinload(Order.items))
            .where(Order.status.in_(("pending", "placed")))
            .order_by(Order.created_at.desc())
        )
    ).all()
    return [
        OrderReviewOut(
            **_out(order).model_dump(),
            customer_name=customer.name,
            customer_email=customer.email,
            shipping_address=order.shipping_address,
        )
        for order, customer in rows
    ]


@order_router.post("/{order_id}/deliver", response_model=OrderOut)
async def mark_order_delivered(
    order_id: int,
    _: User = Depends(require_role("admin", "reviewer")),
    session: AsyncSession = Depends(get_db_session),
) -> OrderOut:
    order = (
        await session.execute(
            select(Order).where(Order.id == order_id).with_for_update()
        )
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(404, "order not found")
    if order.status.lower() not in ("pending", "placed"):
        raise HTTPException(409, "only pending orders can be marked delivered")

    order.status = "delivered"
    order.delivered_at = dt.datetime.now(dt.timezone.utc)
    await session.commit()

    delivered_order = (
        await session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
    ).scalar_one()
    return _out(delivered_order)


@order_router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: str,
    p: User = Depends(require_role("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> OrderOut:
    o = (
        await session.execute(
            select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        )
    ).scalar_one_or_none()
    if o is None or o.user_id != p.id:
        raise HTTPException(404, "order not found")
    return _out(o)