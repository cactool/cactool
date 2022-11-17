"""Add "Show" data type

Revision ID: 07d73859b99c
Revises: 7226d855d8ec
Create Date: 2022-07-06 19:16:21.156928

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "07d73859b99c"
down_revision = "7226d855d8ec"
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
    "ONE_TO_THREE",
    "ONE_TO_FIVE",
    "ONE_TO_SEVEN",
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
    "ONE_TO_THREE",
    "ONE_TO_FIVE",
    "ONE_TO_SEVEN",
    "DISPLAY",
    name="type",
)


def upgrade():
    with op.batch_alter_table("dataset_column") as batch_op:
        batch_op.alter_column(
            "type", existing_type=old_data_types, type_=new_data_types
        )


def downgrade():
    pass
