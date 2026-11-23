from __future__ import annotations

import os
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from worker.pipeline.db import _rows
from worker.pipeline.nodes import base
from worker.pipeline.nodes.base import (
    Case,
    CustomerHistory,
    OrderInfo,
    PhotoInfo,
    ProductInfo,
)
from worker.pipeline.query import ML_CONTEXT_QUERY, RETURN_QUERY
from worker.pipeline.config import get_settings
if TYPE_CHECKING:
    from worker.pipeline.workflow import WorkflowState

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

    for field in (
        "item_returned_opened",
        "multiple_accounts_flag",
        "refund_to_different_account",
        "address_change_before_delivery",
    ):
        if context.get(field) is not None:
            context[field] = int(context[field])

    return context

from psycopg.types.json import Jsonb


def _extract_decision(case: Case) -> tuple[str, str | None]:
    # TODO: adjust to where your workflow stores the decision/explanation.
    # Example if the decision is in case.status and the explanation in an agent result:
    decision = case.status
    explanation = None
    # e.g. explanation = case.agent_results["explanation"].summary
    return decision, explanation


async def add_to_queue(pool, return_id: str, case: Case) -> bool:
    """Insert into review_queue. Returns False if already queued (safe for arq retries)."""
    decision, explanation = _extract_decision(case)

    query = """
        INSERT INTO review_queue
            (order_id, decision, explanation, payload, status, created_at)
        VALUES
            (%s, %s, %s, %s, 'pending', now())
        ON CONFLICT (order_id) DO NOTHING
    """
    async with pool.connection() as conn:
        cur = await conn.execute(
            query,
            (
                return_id,
                decision,
                explanation,
                Jsonb(case.model_dump(mode="json")),  # handles enums, datetimes, nested models
            ),
        )
        return cur.rowcount == 1


def customer_message(result: WorkflowState) -> str:
    """Build the customer-facing message from workflow results."""
    case = result["case"]
    product = (
        case.product_info.title
        if case.product_info is not None
        else case.item_name
    )
    explanation = case.agent_results.get("explanation")
    if (
        explanation is not None
        and isinstance(explanation.output, base.ExplanationResult)
    ):
        return explanation.output.message

    intake = case.agent_results.get("intake")
    if intake is not None and isinstance(intake.output, base.IntakeResult):
        reason = result.get("skip_reason") or intake.output.notes
        if intake.output.status == "missing_info":
            return (
                f"We need more information to review your return request for "
                f"{product}. Please provide the missing details: {reason}"
            )
        return (
            f"We couldn't approve your return request for {product} because "
            f"the return details could not be verified: {reason}"
        )

    policy = case.agent_results.get("policy")
    if policy is not None and isinstance(policy.output, base.PolicyResult):
        reason = result.get("skip_reason") or policy.output.reason
        if policy.output.eligible is False:
            return (
                f"Your return request for {product} was not approved because "
                f"it does not meet the return policy requirements: {reason}"
            )
        return (
            f"We need additional time to review your return request for "
            f"{product}. The policy check needs clarification: {reason}"
        )

    gate = case.agent_results.get("gate")
    if gate is not None and isinstance(gate.output, base.GateResult):
        return (
            f"We need more information before we can review your return "
            f"request for {product}: "
            f"{result.get('skip_reason') or gate.output.reason}"
        )

    if result.get("skip_reason"):
        return (
            f"We couldn't complete the review of your return request for "
            f"{product}. {result['skip_reason']}"
        )
    return (
        f"We need additional time to review your return request for {product}. "
        "We’ll update you when the review is complete."
    )

def is_kill_switch_on() -> bool:
    value = get_settings().human_review_kill_switch
    if value is None:
        return True  # fail safe: default to human review
    return value

def human_review_message(return_id: str) -> str:
    return f"""
A return request requires human review.

Return ID: {return_id}

The automated review process has routed this return
for manual assessment.

Please review the AI assessment, agent results,
and supporting evidence in the ReturnGuard dashboard.

Required action:
Approve or reject the return after reviewing the case.

— ReturnGuard
"""