from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.dependency import get_db_session    
from backend.app.models import Order, OrderItem, Product
from backend.app.ratelimit import limiter
from backend.app.schemas import CheckoutIn, OrderItemOut, OrderOut
from backend.app.security.auth import Principal, current_user
from backend.app.services import mail
from backend.app.services.payment import charge

order_router = APIRouter(prefix="/orders", tags=["orders"])

def _out(o: Order) -> OrderOut:
    return OrderOut(
        id=str(o.id), status=o.status, total=o.total_amount, payment_last4=o.card_last4,
        placed_at=o.placed_at,
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
    p: Principal = Depends(current_user),
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
        user_id=p.user_id, status="placed", total_amount=total,
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
    p: Principal = Depends(current_user), session: AsyncSession = Depends(get_db_session)
) -> list[OrderOut]:
    rows = (
        await session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == p.user_id)
            .order_by(Order.placed_at.desc())
        )
    ).scalars().all()
    return [_out(o) for o in rows]


@order_router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: str,
    p: Principal = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> OrderOut:
    o = (
        await session.execute(
            select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        )
    ).scalar_one_or_none()
    if o is None or str(o.user_id) != p.user_id:
        raise HTTPException(404, "order not found")
    return _out(o)