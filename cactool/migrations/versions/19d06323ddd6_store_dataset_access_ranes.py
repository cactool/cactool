"""Store coder dataset access ranges

Revision ID: 19d06323ddd6
Revises: 28e8811a530d
Create Date: 2023-01-13 14:54:14.868396

"""
import sqlalchemy as sa
from alembic import op

revision = "19d06323ddd6"
down_revision = "28e8811a530d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("dataset_access", schema=None) as batch_op:
        batch_op.add_column(sa.Column("start_index", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("end_index", sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table("dataset_access", schema=None) as batch_op:
        batch_op.drop_column("end_index")
        batch_op.drop_column("start_index")
