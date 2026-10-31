from knowledge.ingestion import PolicyKnowledgeBase
from fastmcp import FastMCP

import os
from typing import Any, LiteralString

from psycopg_pool import ConnectionPool

_pool = ConnectionPool(
    conninfo=os.environ["DATABASE_SYNC_URL"].replace("postgresql+psycopg://", "postgresql://"),
    min_size=1,
    max_size=4,
    open=True,
)

def _rows(sql: LiteralString, params: dict) -> list[dict[str, Any]]:
    with _pool.connection() as conn:
        cur = conn.execute(sql, params)
        if cur.description is None:
            return []
        cols = [c.name for c in cur.description]
        return [dict(zip(cols, r, strict=True)) for r in cur.fetchall()]


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
    def get_order(order_id: str) -> dict[str, Any]:
        """Return the order header + line items for an order id."""

        orders = _rows(
            "SELECT id::text, user_id::text, status, total_amount, card_last4, placed_at "
            "FROM orders WHERE id = %(oid)s",
            {"oid": order_id},
        )
        if not orders:
            return {"found": False, "order_id": order_id}
        items = _rows(
            "SELECT product_id::text, name_at_purchase, price_at_purchase, quantity "
            "FROM order_items WHERE order_id = %(oid)s",
            {"oid": order_id},
        )
        o = orders[0]
        o["total_amount"] = float(o["total_amount"])
        o["placed_at"] = o["placed_at"].isoformat()
        for it in items:
            it["price_at_purchase"] = float(it["price_at_purchase"])
        return {"found": True, "order": o, "items": items}


    @mcp.tool
    def get_customer_history(user_id: str) -> dict[str, Any]:
        """Order/return counts + prior denied returns + return rate for a customer."""
        h = _rows(
            """
            SELECT
            (SELECT count(*) FROM orders  WHERE user_id = %(u)s) AS orders,
            (SELECT count(*) FROM returns WHERE user_id = %(u)s) AS returns,
            (SELECT count(*) FROM returns WHERE user_id = %(u)s AND final_decision='deny') AS denied,
            (SELECT count(*) FROM returns WHERE user_id = %(u)s AND final_decision='approve') AS approved
            """,
            {"u": user_id},
        )[0]
        orders = max(int(h["orders"]), 1)
        return {
            "user_id": user_id,
            "lifetime_orders": int(h["orders"]),
            "lifetime_returns": int(h["returns"]),
            "denied_returns": int(h["denied"]),
            "approved_returns": int(h["approved"]),
            "return_rate": round(int(h["returns"]) / orders, 3),
        }

