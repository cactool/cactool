"""Store user emails

Revision ID: c12d86b089b8
Revises: 7226d855d8ec
Create Date: 2022-11-12 14:09:25.540638

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c12d86b089b8"
down_revision = "7226d855d8ec"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(length=50), nullable=True))


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("email")

