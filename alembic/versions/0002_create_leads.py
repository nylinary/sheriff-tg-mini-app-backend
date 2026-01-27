from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_create_leads'
down_revision = '0001_create_users'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'leads',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('tg_user_id', sa.BigInteger, index=True, nullable=False),
        sa.Column('username', sa.String, index=True, nullable=True),
        sa.Column('city', sa.String, nullable=False),
        sa.Column('exchange_type', sa.String, nullable=False),
        sa.Column('receive_type', sa.String, nullable=False),
        sa.Column('sum', sa.String, nullable=False),
        sa.Column('wallet_address', sa.String, nullable=False),
        sa.Column('meta', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table('leads')
