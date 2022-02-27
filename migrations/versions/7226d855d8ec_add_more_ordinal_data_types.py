"""Add more ordinal data types

Revision ID: 7226d855d8ec
Revises: d1b66364eeb3
Create Date: 2022-02-27 16:24:17.410544

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7226d855d8ec'
down_revision = 'd1b66364eeb3'
branch_labels = None
depends_on = None

old_data_types = sa.Enum(
    'STRING',
    'NUMBER',
    'LIST',
    'BOOLEAN',
    'SOCIAL_MEDIA',
    'HIDDEN',
    'LIKERT',
    name='type'
)

new_data_types = sa.Enum(
    'STRING',
    'NUMBER',
    'LIST',
    'BOOLEAN',
    'SOCIAL_MEDIA',
    'HIDDEN',
    'LIKERT',
    'ONE_TO_THREE',
    'ONE_TO_FIVE',
    'ONE_TO_SEVEN',
    name='type'
)

def upgrade():
    with op.batch_alter_table("dataset_column") as batch_op:
        batch_op.alter_column(
            "type",
            existing_type=old_data_types,
            type_=new_data_types
        )


def downgrade():
    pass
