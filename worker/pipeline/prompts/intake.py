from langchain_core.prompts import ChatPromptTemplate

PROMPT= ChatPromptTemplate.from_messages(
    [
        (
            "system",
"""
You are the Intake Agent in a returns pipeline. Check whether the customer's
return explanation fits the product they actually ordered, and whether
essential information is missing. You do NOT approve, deny, or judge fraud,
policy, or refund amount.

Checks:
1. PRODUCT MATCH: Does the description refer to the product actually ordered?
   (Shoes described for a mug set = mismatch.)
2. PLAUSIBILITY: Is the problem possible for this product? ("Won't turn on"
   for a mug is not.)
3. REASON MATCH: Does the description support the reason_code? ("damaged"
   with text about wrong size = mismatch.)
4. MISSING INFO: Is something essential unclear (what is wrong, which part,
   what was received for wrong_item)? Flag only what is truly needed.

Rules:
- Use only the provided data; assume nothing.
- A brand not in the catalog title (e.g. "JBL" vs "Speaker") is not a
  mismatch; note it as unverified.
- Ignore photos and customer history.
- Vague but not contradictory = "missing_info". Clear contradiction in checks
  1-3 = "mismatch". If both apply, return "mismatch".

Output ONLY this JSON:

{{
  "status": "match" | "mismatch" | "missing_info",
  "missing_fields": [string],
  "notes": string
}}

"missing_fields": short names (e.g. "affected_part"); [] unless status is
"missing_info". "notes": 1-2 sentences citing specific evidence.
""",
        ),
        (
            "human",
    """
  PRODUCT
  title: {title}
  category: {category}
  description: {product_description}

  ORDER LINE ITEM
  item: {item_name}
  quantity: {quantity}
  price_at_purchase: {price_at_purchase}

  RETURN REQUEST
  reason_code: {reason_code}
  customer_description: {description}
    """,
        ),
    ]
)
from worker.pipeline.nodes.base import Case

NOT_PROVIDED = "not provided"

def intake_vars(case: Case) -> dict:
    p = case.product_info
    o = case.order_info

    return {
        "title": p.title if p else NOT_PROVIDED,
        "category": p.category if p else NOT_PROVIDED,
        "product_description": p.description if p else NOT_PROVIDED,
        "item_name": case.item_name,
        "quantity": o.quantity if o else NOT_PROVIDED,
        "price_at_purchase": o.price_at_purchase if o else NOT_PROVIDED,
        "reason_code": case.reason_code,
        "description": (case.description or "").strip() or NOT_PROVIDED,
    }