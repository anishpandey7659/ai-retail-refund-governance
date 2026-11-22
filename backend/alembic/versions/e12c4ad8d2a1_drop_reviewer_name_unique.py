"""Allow reviewers to share display names.

Revision ID: e12c4ad8d2a1
Revises:
"""

from alembic import op

revision = "e12c4ad8d2a1"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('public.reviewers') IS NOT NULL
               AND EXISTS (
                   SELECT 1
                   FROM pg_constraint
                   WHERE conrelid = to_regclass('public.reviewers')
                     AND conname = 'reviewers_name_key'
               )
            THEN
                ALTER TABLE public.reviewers
                    DROP CONSTRAINT reviewers_name_key;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('public.reviewers') IS NOT NULL
               AND NOT EXISTS (
                   SELECT 1
                   FROM pg_constraint
                   WHERE conrelid = to_regclass('public.reviewers')
                     AND conname = 'reviewers_name_key'
               )
            THEN
                ALTER TABLE public.reviewers
                    ADD CONSTRAINT reviewers_name_key UNIQUE (name);
            END IF;
        END
        $$;
        """
    )
