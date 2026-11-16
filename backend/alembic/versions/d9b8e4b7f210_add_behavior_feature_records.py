"""add behavior prediction feature records

Revision ID: d9b8e4b7f210
Revises: ba975ddcd202
Create Date: 2026-11-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d9b8e4b7f210"
down_revision: Union[str, Sequence[str], None] = "ba975ddcd202"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "payment_method_fingerprint",
            sa.String(length=64),
            nullable=True,
            comment="Keyed payment-provider fingerprint; never raw payment data",
        ),
    )

    op.create_table(
        "order_address_changes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "order_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_order_address_changes_order_changed",
        "order_address_changes",
        ["order_id", "changed_at"],
        unique=False,
    )

    op.create_table(
        "return_inspections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("return_id", sa.UUID(), nullable=False),
        sa.Column("item_received", sa.Boolean(), nullable=True),
        sa.Column("item_opened", sa.Boolean(), nullable=True),
        sa.Column("inspected_by", sa.UUID(), nullable=True),
        sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["inspected_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["return_id"], ["returns.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("return_id"),
    )

    op.create_table(
        "return_refunds",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("return_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "destination_fingerprint",
            sa.String(length=64),
            nullable=True,
            comment="Keyed fingerprint for comparison; never raw payment data",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_return_refunds_amount_positive"),
        sa.CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed')",
            name="ck_return_refunds_status",
        ),
        sa.ForeignKeyConstraint(["return_id"], ["returns.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_return_refunds_return_id"),
        "return_refunds",
        ["return_id"],
        unique=False,
    )

    op.create_table(
        "support_contacts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("return_id", sa.UUID(), nullable=True),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column(
            "contacted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["return_id"], ["returns.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_support_contacts_user_contacted",
        "support_contacts",
        ["user_id", "contacted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_support_contacts_user_contacted", table_name="support_contacts")
    op.drop_table("support_contacts")
    op.drop_index(op.f("ix_return_refunds_return_id"), table_name="return_refunds")
    op.drop_table("return_refunds")
    op.drop_table("return_inspections")
    op.drop_index(
        "ix_order_address_changes_order_changed",
        table_name="order_address_changes",
    )
    op.drop_table("order_address_changes")
    op.drop_column("orders", "payment_method_fingerprint")
