import uuid

from knowledge.ingestion import PolicyKnowledgeBase
from typing import Any, LiteralString
from psycopg.rows import dict_row
from fastmcp import FastMCP
import os

from psycopg_pool import AsyncConnectionPool

_pool = AsyncConnectionPool(
    conninfo=os.environ["DATABASE_PSYCOPG_URL"],
    min_size=1,
    max_size=4,
    open=False, # Don't open connections until first use
)

async def _rows(sql: LiteralString, params: dict):
    async with _pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()



def register_tools(mcp: FastMCP):

    knowledge_base = PolicyKnowledgeBase()

    @mcp.tool
    async def search_policy(query: str, limit: int = 5):
        """
        Search ReturnGuard refund policies.

        Args:
            query: The user's question about return or refund policies.
            limit: Maximum number of relevant policy chunks to retrieve.
        """

        return await knowledge_base.search_policy(
            query=query,
            limit=limit,
        )

    @mcp.tool
    async def get_return_context(return_id: uuid.UUID) -> dict[str, Any]:
        """Return complete context for a return, including order item and product details."""

        rows = await _rows(
            """
        SELECT
        r.id::text AS return_id,
        r.order_id,
        r.user_id::text AS customer_id,

        COALESCE(
            (
                SELECT JSON_AGG(
                    JSON_BUILD_OBJECT(
                        'id', rp.id::text,
                        'object_key', rp.object_key,
                        'content_type', rp.content_type,
                        'bytes', rp.bytes
                    )
                )
                FROM return_photos rp
                WHERE rp.return_id = r.id
            ),
            '[]'::json
        ) AS photos,

        r.created_at,
        r.reason_code,
        r.reason_text,
        r.amount,
        r.status,

        oi.id::text AS order_item_id,
        oi.product_id::text AS product_id,
        oi.quantity,
        oi.price_at_purchase,
        oi.name_at_purchase,

        p.name AS product_name,
        p.description AS product_description,
        p.category AS product_category,
        p.price AS current_product_price,
        p.image_key AS product_image_key

    FROM returns r

    JOIN order_items oi
        ON oi.id = r.order_item_id
        AND oi.order_id = r.order_id

    JOIN products p
        ON p.id = oi.product_id

    WHERE r.id = %(return_id)s
    """,
            {"return_id": return_id},
        )

        if not rows:
            return {
                "found": False,
                "return_id": return_id,
            }

        context = rows[0]

        # Convert Decimal values to JSON-compatible floats.
        for field in (
            "amount",
            "price_at_purchase",
            "current_product_price",
        ):
            if context[field] is not None:
                context[field] = float(context[field])

        # Convert datetime to ISO 8601.
        if context["created_at"] is not None:
            context["created_at"] = context["created_at"].isoformat()

        return {
            "found": True,
            "return": context,
        }


    @mcp.tool
    async def get_customer_history(user_id: str) -> dict[str, Any]:
        """Order/return counts + prior denied returns + return rate."""

        rows = await _rows(
            """
            SELECT
                (SELECT count(*) FROM orders WHERE user_id = %(u)s) AS orders,
                (SELECT count(*) FROM returns WHERE user_id = %(u)s) AS returns,
                (SELECT count(*) FROM returns
                WHERE user_id = %(u)s AND final_decision = 'deny') AS denied,
                (SELECT count(*) FROM returns
                WHERE user_id = %(u)s AND final_decision = 'approve') AS approved
            """,
            {"u": user_id},
        )

        h = rows[0]
        lifetime_orders = int(h["orders"])
        lifetime_returns = int(h["returns"])

        return {
            "user_id": user_id,
            "lifetime_orders": lifetime_orders,
            "lifetime_returns": lifetime_returns,
            "denied_returns": int(h["denied"]),
            "approved_returns": int(h["approved"]),
            "return_rate": (
                round(lifetime_returns / lifetime_orders, 3)
                if lifetime_orders > 0
                else 0.0
            ),
        }
