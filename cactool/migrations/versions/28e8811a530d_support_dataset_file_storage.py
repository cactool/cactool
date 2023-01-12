"""Support dataset file storage

Revision ID: 28e8811a530d
Revises: ce5fc447a2e8
Create Date: 2023-01-10 17:48:31.477603

"""
import sqlalchemy as sa
from alembic import op

revision = "28e8811a530d"
down_revision = "ce5fc447a2e8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dataset_file",
        sa.Column("dataset_id", sa.String(length=512), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["dataset.id"],
        ),
        sa.PrimaryKeyConstraint("dataset_id", "file_name"),
    )


def downgrade():
    op.drop_table("dataset_file")
