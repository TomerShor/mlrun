"""adding artifacts_v2 table

Revision ID: 4ce6906ae318
Revises: 28383af526f3
Create Date: 2023-06-27 15:40:19.146907

"""
import sqlalchemy as sa
import sqlalchemy.dialects.mysql
from alembic import op

from mlrun.api.utils.db.sql_collation import SQLCollationUtil

# revision identifiers, used by Alembic.
revision = "4ce6906ae318"
down_revision = "28383af526f3"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "artifacts_v2",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "uid",
            sa.String(length=255, collation=SQLCollationUtil.collation()),
            nullable=True,
        ),
        sa.Column(
            "project",
            sa.String(length=255, collation=SQLCollationUtil.collation()),
            nullable=True,
        ),
        sa.Column(
            "key",
            sa.String(length=255, collation=SQLCollationUtil.collation()),
            nullable=True,
        ),
        sa.Column(
            "kind",
            sa.String(length=255, collation=SQLCollationUtil.collation()),
            nullable=True,
        ),
        sa.Column(
            "producer_id",
            sa.String(length=255, collation=SQLCollationUtil.collation()),
            nullable=True,
        ),
        sa.Column("iteration", sa.Integer(), nullable=True),
        sa.Column(
            "hash",
            sa.String(length=255, collation=SQLCollationUtil.collation()),
            nullable=True,
        ),
        sa.Column("_full_object", sa.JSON(), nullable=True),
        sa.Column("created", sqlalchemy.dialects.mysql.TIMESTAMP(fsp=3), nullable=True),
        sa.Column("updated", sqlalchemy.dialects.mysql.TIMESTAMP(fsp=3), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uid", "project", "key", name="_artifacts_v2_uc"),
    )
    op.create_table(
        "artifacts_v2_labels",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "name",
            sa.String(255, collation=SQLCollationUtil.collation()),
            nullable=True,
        ),
        sa.Column(
            "value",
            sa.String(255, collation=SQLCollationUtil.collation()),
            nullable=True,
        ),
        sa.Column("parent", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent"],
            ["artifacts_v2.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "parent", name="_artifacts_v2_labels_uc"),
    )
    op.create_table(
        "artifacts_v2_tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "project",
            sa.String(255, collation=SQLCollationUtil.collation()),
            nullable=True,
        ),
        sa.Column(
            "name",
            sa.String(255, collation=SQLCollationUtil.collation()),
            nullable=True,
        ),
        sa.Column("obj_id", sa.Integer(), nullable=True),
        sa.Column(
            "obj_name",
            sa.String(255, collation=SQLCollationUtil.collation()),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["obj_id"],
            ["artifacts_v2.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project", "name", "obj_id", "obj_name", name="_artifacts_v2_tags_uc"
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("artifacts_v2")
    op.drop_table("artifacts_v2_labels")
    op.drop_table("artifacts_v2_tags")
    # ### end Alembic commands ###
