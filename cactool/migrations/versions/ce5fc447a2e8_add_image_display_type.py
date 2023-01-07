"""Add image display type

Revision ID: ce5fc447a2e8
Revises: 51ed49d3ed75
Create Date: 2023-01-07 09:33:12.978213

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ce5fc447a2e8"
down_revision = "51ed49d3ed75"
branch_labels = None
depends_on = None

old_data_types = sa.Enum(
    "STRING",
    "NUMBER",
    "LIST",
    "BOOLEAN",
    "SOCIAL_MEDIA",
    "HIDDEN",
    "LIKERT",
    "ONE_TO_SEVEN",
    "ONE_TO_FIVE",
    "ONE_TO_THREE",
    "DISPLAY",
    name="type",
)

new_data_types = sa.Enum(
    "STRING",
    "NUMBER",
    "LIST",
    "BOOLEAN",
    "SOCIAL_MEDIA",
    "HIDDEN",
    "LIKERT",
    "ONE_TO_SEVEN",
    "ONE_TO_FIVE",
    "ONE_TO_THREE",
    "DISPLAY",
    "IMAGE",
    name="type",
)


def upgrade():
    with op.batch_alter_table("dataset_column") as batch_op:
        batch_op.alter_column(
            "type", existing_type=old_data_types, type_=new_data_types
        )


def downgrade():
    pass
