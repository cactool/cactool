"""Initial migration

Revision ID: d1b66364eeb3
Revises: 
Create Date: 2022-02-27 15:56:53.693525

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d1b66364eeb3"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dataset",
        sa.Column("id", sa.String(length=512), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_table(
        "project",
        sa.Column("id", sa.String(length=512), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=True),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_table(
        "user",
        sa.Column("id", sa.String(length=512), nullable=False),
        sa.Column("admin", sa.Boolean(), nullable=True),
        sa.Column("username", sa.String(length=20), nullable=True),
        sa.Column("password", sa.String(length=1024), nullable=True),
        sa.Column("firstname", sa.String(length=50), nullable=True),
        sa.Column("surname", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "dataset_access",
        sa.Column("user_id", sa.String(length=512), nullable=False),
        sa.Column("dataset_id", sa.String(length=512), nullable=False),
        sa.Column(
            "access_level",
            sa.Enum("NONE", "CODE", "EXPORT", "ADMIN", name="accesslevel"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["dataset.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "dataset_id"),
    )
    op.create_table(
        "dataset_column",
        sa.Column("id", sa.String(length=512), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=True),
        sa.Column(
            "type",
            sa.Enum(
                "STRING",
                "NUMBER",
                "LIST",
                "BOOLEAN",
                "SOCIAL_MEDIA",
                "HIDDEN",
                "LIKERT",
                name="type",
            ),
            nullable=True,
        ),
        sa.Column("dataset_id", sa.String(length=512), nullable=True),
        sa.Column("prompt", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["dataset.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_id", "name"),
        sa.UniqueConstraint("id"),
    )
    op.create_table(
        "dataset_row",
        sa.Column("dataset_id", sa.String(length=512), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("coded", sa.Boolean(), nullable=True),
        sa.Column("coder_id", sa.String(length=512), nullable=True),
        sa.Column("skip", sa.Boolean(), nullable=True),
        sa.Column("post_unavailable", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["coder_id"],
            ["user.id"],
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["dataset.id"],
        ),
        sa.PrimaryKeyConstraint("dataset_id", "row_number"),
        sa.UniqueConstraint("dataset_id", "row_number"),
    )
    op.create_table(
        "project_access",
        sa.Column("user_id", sa.String(length=512), nullable=False),
        sa.Column("project_id", sa.String(length=512), nullable=False),
        sa.Column(
            "access_level",
            sa.Enum("NONE", "CODE", "EXPORT", "ADMIN", name="accesslevel"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "project_id"),
    )
    op.create_table(
        "project_datasets",
        sa.Column("project_id", sa.String(length=512), nullable=True),
        sa.Column("dataset_id", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["dataset.id"],
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
        ),
    )
    op.create_table(
        "dataset_row_value",
        sa.Column("dataset_id", sa.String(length=512), nullable=False),
        sa.Column("dataset_row_number", sa.Integer(), nullable=False),
        sa.Column("column_id", sa.String(length=512), nullable=False),
        sa.Column("value", sa.String(length=65535), nullable=True),
        sa.ForeignKeyConstraint(
            ["column_id"],
            ["dataset_column.id"],
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id", "dataset_row_number"],
            ["dataset_row.dataset_id", "dataset_row.row_number"],
        ),
        sa.PrimaryKeyConstraint("dataset_id", "dataset_row_number", "column_id"),
        sa.UniqueConstraint("dataset_id", "dataset_row_number", "column_id"),
    )


def downgrade():
    op.drop_table("dataset_row_value")
    op.drop_table("project_datasets")
    op.drop_table("project_access")
    op.drop_table("dataset_row")
    op.drop_table("dataset_column")
    op.drop_table("dataset_access")
    op.drop_table("user")
    op.drop_table("project")
    op.drop_table("dataset")
