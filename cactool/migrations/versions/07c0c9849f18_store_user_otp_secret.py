"""Store user OTP secret

Revision ID: 07c0c9849f18
Revises: c12d86b089b8
Create Date: 2022-11-12 15:15:47.490198

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "07c0c9849f18"
down_revision = "c12d86b089b8"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("otp_secret", sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("otp_secret")
