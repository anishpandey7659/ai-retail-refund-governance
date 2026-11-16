import uuid
from decimal import Decimal

from worker.pipeline.db import _rows
from worker.pipeline.nodes.base import (
    Case,
    CustomerHistory,
    OrderInfo,
    PhotoInfo,
    ProductInfo,
)
from worker.pipeline.query import ML_CONTEXT_QUERY, RETURN_QUERY

MONEY_FIELDS = ("amount", "price_at_purchase", "current_product_price")


class ReturnNotFound(Exception):
    pass


def build_case(data: dict) -> Case:
    history = data.get("customer_history") or {}
    orders = int(history.get("orders") or 0)
    returns = int(history.get("returns") or 0)

    return Case(
        # Identity
        case_id=str(data["return_id"]),
        order_id=int(data["order_id"]),
        customer_id=str(data["customer_id"]),
        return_request_at=str(data["created_at"]),
        # Customer submission
        item_name=data["name_at_purchase"],
        reason_code=data["reason_code"],
        description=data["reason_text"],
        photos=[
            PhotoInfo(
                id=str(photo["id"]),
                object_key=photo["object_key"],
                content_type=photo["content_type"],
                bytes=int(photo["bytes"]),
            )
            for photo in (data.get("photos") or [])
        ],
        # Backend product information
        product_info=ProductInfo(
            product_id=str(data["product_id"]),
            title=data["product_name"],
            description=data["product_description"],
            category=data["product_category"],
            current_price=float(data["current_product_price"]),
            image_key=data["product_image_key"],
        ),
        # Customer history (prior returns only; excludes this one)
        customer_history=CustomerHistory(
            orders=orders,
            returns=returns,
            approved=int(data.get("approved") or 0),
            denied=int(data.get("denied") or 0),
            return_rate=round(returns / orders, 4) if orders else 0.0,
        ),
        # Backend order information
        order_info=OrderInfo(
            order_item_id=int(data["order_item_id"]),
            quantity=int(data["quantity"]),
            price_at_purchase=float(data["price_at_purchase"]),
            return_amount=float(data["amount"]),
            delivered_at=str(data["delivered_at"])
            if data.get("delivered_at") is not None
            else None,
        ),
        # Pipeline state
        status=data["status"].lower(),
    )


async def load_return_context(return_id: str) -> dict:
    """Fetch a return with its order item, product, and photo details."""
    uuid.UUID(return_id)  # fail fast on malformed IDs

    rows = await _rows(RETURN_QUERY, {"return_id": return_id})
    if not rows:
        raise ReturnNotFound(return_id)

    context = dict(rows[0])

    for field in MONEY_FIELDS:
        if isinstance(context.get(field), Decimal):
            context[field] = float(context[field])  # or str()/cents; see notes

    if context.get("created_at") is not None:
        context["created_at"] = context["created_at"].isoformat()

    if context.get("delivered_at") is not None:
        context["delivered_at"] = context["delivered_at"].isoformat()

    return context


async def load_ml_context(return_id: str) -> dict:
    """Fetch the ordered behavior-model feature values for a return."""
    uuid.UUID(return_id)  # fail fast on malformed IDs

    rows = await _rows(ML_CONTEXT_QUERY, {"return_id": return_id})
    if not rows:
        raise ReturnNotFound(return_id)

    context = dict(rows[0])
    for field in (
        "return_rate_pct",
        "refund_to_order_ratio",
        "refund_amount_requested_usd",
    ):
        if isinstance(context.get(field), Decimal):
            context[field] = float(context[field])

    for field in ("customer_support_contacts", "previous_dispute_count"):
        if context.get(field) is not None:
            context[field] = int(context[field])

    return context
