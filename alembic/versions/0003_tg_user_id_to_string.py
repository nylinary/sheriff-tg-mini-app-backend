"""tg_user_id to string

Revision ID: 0003_tg_user_id_to_string
Revises: 0002_create_leads
Create Date: 2026-01-28

"""

from alembic import op
import sqlalchemy as sa

revision = "0003_tg_user_id_to_string"
down_revision = "0002_create_leads"
branch_labels = None
depends_on = None


def upgrade():
    # Change users.tg_user_id BIGINT -> TEXT
    op.alter_column(
        "users",
        "tg_user_id",
        existing_type=sa.BigInteger(),
        type_=sa.String(),
        postgresql_using="tg_user_id::text",
        existing_nullable=False,
    )

    # Change leads.tg_user_id BIGINT -> TEXT (if leads table has this column)
    # Note: leads migration created tg_user_id as BigInteger.
    op.alter_column(
        "leads",
        "tg_user_id",
        existing_type=sa.BigInteger(),
        type_=sa.String(),
        postgresql_using="tg_user_id::text",
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "leads",
        "tg_user_id",
        existing_type=sa.String(),
        type_=sa.BigInteger(),
        postgresql_using="tg_user_id::bigint",
        existing_nullable=False,
    )

    op.alter_column(
        "users",
        "tg_user_id",
        existing_type=sa.String(),
        type_=sa.BigInteger(),
        postgresql_using="tg_user_id::bigint",
        existing_nullable=False,
    )
