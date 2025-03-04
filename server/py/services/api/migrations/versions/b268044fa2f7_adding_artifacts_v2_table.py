# Copyright 2023 Iguazio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""adding artifacts_v2 table

Revision ID: b268044fa2f7
Revises: b899cbf87203
Create Date: 2023-11-22 20:04:18.402025

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

from framework.utils.db.sql_types import SQLTypesUtil

# revision identifiers, used by Alembic.
revision = "b268044fa2f7"
down_revision = "b899cbf87203"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "artifacts_v2",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "uid",
            sa.String(length=255, collation=SQLTypesUtil.collation()),
            nullable=True,
        ),
        sa.Column(
            "project",
            sa.String(length=255, collation=SQLTypesUtil.collation()),
            nullable=True,
        ),
        sa.Column(
            "key",
            sa.String(length=255, collation=SQLTypesUtil.collation()),
            nullable=True,
        ),
        sa.Column(
            "kind",
            sa.String(length=255, collation=SQLTypesUtil.collation()),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "producer_id",
            sa.String(length=255, collation=SQLTypesUtil.collation()),
            nullable=True,
        ),
        sa.Column("iteration", sa.Integer(), nullable=True),
        sa.Column("best_iteration", sa.BOOLEAN(), nullable=True, index=True),
        sa.Column("object", mysql.MEDIUMBLOB(), nullable=True),
        sa.Column("created", mysql.TIMESTAMP(fsp=3), nullable=True),
        sa.Column("updated", mysql.TIMESTAMP(fsp=3), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uid", "project", "key", name="_artifacts_v2_uc"),
    )
    op.create_table(
        "artifacts_v2_labels",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "name",
            sa.String(255, collation=SQLTypesUtil.collation()),
            nullable=True,
        ),
        sa.Column(
            "value",
            sa.String(255, collation=SQLTypesUtil.collation()),
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
            sa.String(255, collation=SQLTypesUtil.collation()),
            nullable=True,
        ),
        sa.Column(
            "name",
            sa.String(255, collation=SQLTypesUtil.collation()),
            nullable=True,
        ),
        sa.Column("obj_id", sa.Integer(), nullable=True),
        sa.Column(
            "obj_name",
            sa.String(255, collation=SQLTypesUtil.collation()),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["obj_id"],
            ["artifacts_v2.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project", "name", "obj_id", name="_artifacts_v2_tags_uc"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("artifacts_v2_tags")
    op.drop_table("artifacts_v2_labels")
    op.drop_table("artifacts_v2")
    # ### end Alembic commands ###
