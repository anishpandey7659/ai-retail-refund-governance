"""Add destination_fingerprint to return_refunds.

Revision ID: 8a1b2c3d4e5f
Revises: 7f4c9d2a1b6e
"""

from alembic import op
import sqlalchemy as sa

revision = "8a1b2c3d4e5f"
down_revision = "7f4c9d2a1b6e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "return_refunds",
        sa.Column(
            "destination_fingerprint",
            sa.String(length=64),
            nullable=True,
            comment="Keyed payment-provider fingerprint for refund destination account",
        ),
    )


def downgrade() -> None:
    op.drop_column("return_refunds", "destination_fingerprint")
