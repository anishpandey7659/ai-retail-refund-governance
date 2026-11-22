"""Add the order foreign key back to returns.

Revision ID: 7f4c9d2a1b6e
Revises: e12c4ad8d2a1
"""

from alembic import op
import sqlalchemy as sa

revision = "7f4c9d2a1b6e"
down_revision = "e12c4ad8d2a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("returns", sa.Column("order_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE returns AS r
        SET order_id = oi.order_id
        FROM order_items AS oi
        WHERE oi.id = r.order_item_id
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM returns
                WHERE order_id IS NULL
            ) THEN
                RAISE EXCEPTION
                    'Cannot backfill returns.order_id: one or more order items are missing';
            END IF;
        END
        $$;
        """
    )
    op.alter_column("returns", "order_id", nullable=False)
    op.create_index("ix_returns_order_id", "returns", ["order_id"])
    op.create_foreign_key(
        "fk_returns_order_id_orders",
        "returns",
        "orders",
        ["order_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_returns_order_id_orders", "returns", type_="foreignkey")
    op.drop_index("ix_returns_order_id", table_name="returns")
    op.drop_column("returns", "order_id")
