from knowledge.ingestion import PolicyKnowledgeBase
from typing import Any, LiteralString
from psycopg.rows import dict_row
from fastmcp import FastMCP
import os

from psycopg_pool import AsyncConnectionPool

_pool = AsyncConnectionPool(
    conninfo=os.environ["DATABASE_SYNC_URL"].replace("postgresql+psycopg://", "postgresql://"),
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
    async def get_order(order_id: str) -> dict[str, Any]:
        """Return the order header + line items for an order id."""

        orders = await _rows(
            "SELECT id::text, user_id::text, status, total_amount, card_last4, placed_at "
            "FROM orders WHERE id = %(oid)s",
            {"oid": order_id},
        )
        if not orders:
            return {"found": False, "order_id": order_id}
        items = await _rows(
            "SELECT product_id::text, name_at_purchase, price_at_purchase, quantity "
            "FROM order_items WHERE order_id = %(oid)s",
            {"oid": order_id},
        )
        o = orders[0]
        o["total_amount"] = float(o["total_amount"])
        
        if o["placed_at"] is not None:
            o["placed_at"] = o["placed_at"].isoformat()

        for it in items:
            it["price_at_purchase"] = float(it["price_at_purchase"])
        return {"found": True, "order": o, "items": items}


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
