from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_create_users'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('tg_user_id', sa.BigInteger, unique=True, index=True, nullable=False),
        sa.Column('username', sa.String, index=True),
    )

def downgrade():
    op.drop_table('users')
