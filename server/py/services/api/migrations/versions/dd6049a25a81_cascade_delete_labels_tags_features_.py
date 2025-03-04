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
"""Cascade delete labels tags features entities

Revision ID: dd6049a25a81
Revises: fcf2ea01f99a
Create Date: 2024-10-31 11:52:08.927212

"""

import logging

from alembic import op

# revision identifiers, used by Alembic.
revision = "dd6049a25a81"
down_revision = "fcf2ea01f99a"
branch_labels = None
depends_on = None


logger = logging.getLogger("alembic.runtime.migration")


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    logger.info("Dropping constraint: _artifacts_labels_paren_fk")
    op.drop_constraint(
        "_artifacts_labels_paren_fk", "artifacts_labels", type_="foreignkey"
    )
    logger.info("Creating constraint: _artifacts_labels_paren_fk")
    op.create_foreign_key(
        "_artifacts_labels_paren_fk",
        "artifacts_labels",
        "artifacts",
        ["parent"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info("Finished dropping and creating constraint: _artifacts_labels_paren_fk")
    logger.info("Dropping constraint: artifacts_v2_labels_ibfk_1")
    op.drop_constraint(
        "artifacts_v2_labels_ibfk_1", "artifacts_v2_labels", type_="foreignkey"
    )
    logger.info("Creating constraint: artifacts_v2_labels_ibfk_1")
    op.create_foreign_key(
        "artifacts_v2_labels_ibfk_1",
        "artifacts_v2_labels",
        "artifacts_v2",
        ["parent"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info("Finished dropping and creating constraint: artifacts_v2_labels_ibfk_1")
    logger.info("Dropping constraint: artifacts_v2_tags_ibfk_1")
    op.drop_constraint(
        "artifacts_v2_tags_ibfk_1", "artifacts_v2_tags", type_="foreignkey"
    )
    logger.info("Creating constraint: artifacts_v2_tags_ibfk_1")
    op.create_foreign_key(
        "artifacts_v2_tags_ibfk_1",
        "artifacts_v2_tags",
        "artifacts_v2",
        ["obj_id"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info("Finished dropping and creating constraint: artifacts_v2_tags_ibfk_1")
    logger.info("Dropping constraint: _entities_feature_set_id_fk")
    op.drop_constraint("_entities_feature_set_id_fk", "entities", type_="foreignkey")
    logger.info("Creating constraint: _entities_feature_set_id_fk")
    op.create_foreign_key(
        "_entities_feature_set_id_fk",
        "entities",
        "feature_sets",
        ["feature_set_id"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info(
        "Finished dropping and creating constraint: _entities_feature_set_id_fk"
    )
    logger.info("Dropping constraint: _entities_labels_parent_fk")
    op.drop_constraint(
        "_entities_labels_parent_fk", "entities_labels", type_="foreignkey"
    )
    logger.info("Creating constraint: _entities_labels_parent_fk")
    op.create_foreign_key(
        "_entities_labels_parent_fk",
        "entities_labels",
        "entities",
        ["parent"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info("Finished dropping and creating constraint: _entities_labels_parent_fk")
    logger.info("Dropping constraint: _feature_sets_labels_parent_fk")
    op.drop_constraint(
        "_feature_sets_labels_parent_fk", "feature_sets_labels", type_="foreignkey"
    )
    logger.info("Creating constraint: _feature_sets_labels_parent_fk")
    op.create_foreign_key(
        "_feature_sets_labels_parent_fk",
        "feature_sets_labels",
        "feature_sets",
        ["parent"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info(
        "Finished dropping and creating constraint: _feature_sets_labels_parent_fk"
    )
    logger.info("Dropping constraint: _feature_sets_tags_obj_id_fk")
    op.drop_constraint(
        "_feature_sets_tags_obj_id_fk", "feature_sets_tags", type_="foreignkey"
    )
    logger.info("Creating constraint: _feature_sets_tags_obj_id_fk")
    op.create_foreign_key(
        "_feature_sets_tags_obj_id_fk",
        "feature_sets_tags",
        "feature_sets",
        ["obj_id"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info(
        "Finished dropping and creating constraint: _feature_sets_tags_obj_id_fk"
    )
    logger.info("Dropping constraint: _feature_vectors_labels_parent_fk")
    op.drop_constraint(
        "_feature_vectors_labels_parent_fk",
        "feature_vectors_labels",
        type_="foreignkey",
    )
    logger.info("Creating constraint: _feature_vectors_labels_parent_fk")
    op.create_foreign_key(
        "_feature_vectors_labels_parent_fk",
        "feature_vectors_labels",
        "feature_vectors",
        ["parent"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info(
        "Finished dropping and creating constraint: _feature_vectors_labels_parent_fk"
    )
    logger.info("Dropping constraint: _feature_vectors_tags_obj_id_fk")
    op.drop_constraint(
        "_feature_vectors_tags_obj_id_fk", "feature_vectors_tags", type_="foreignkey"
    )
    logger.info("Creating constraint: _feature_vectors_tags_obj_id_fk")
    op.create_foreign_key(
        "_feature_vectors_tags_obj_id_fk",
        "feature_vectors_tags",
        "feature_vectors",
        ["obj_id"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info(
        "Finished dropping and creating constraint: _feature_vectors_tags_obj_id_fk"
    )
    logger.info("Dropping constraint: _features_feature_set_id_fk")
    op.drop_constraint("_features_feature_set_id_fk", "features", type_="foreignkey")
    logger.info("Creating constraint: _features_feature_set_id_fk")
    op.create_foreign_key(
        "_features_feature_set_id_fk",
        "features",
        "feature_sets",
        ["feature_set_id"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info(
        "Finished dropping and creating constraint: _features_feature_set_id_fk"
    )
    logger.info("Dropping constraint: _features_labels_parent_fk")
    op.drop_constraint(
        "_features_labels_parent_fk", "features_labels", type_="foreignkey"
    )
    logger.info("Creating constraint: _features_labels_parent_fk")
    op.create_foreign_key(
        "_features_labels_parent_fk",
        "features_labels",
        "features",
        ["parent"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info("Finished dropping and creating constraint: _features_labels_parent_fk")
    logger.info("Dropping constraint: _functions_labels_parent_fk")
    op.drop_constraint(
        "_functions_labels_parent_fk", "functions_labels", type_="foreignkey"
    )
    logger.info("Creating constraint: _functions_labels_parent_fk")
    op.create_foreign_key(
        "_functions_labels_parent_fk",
        "functions_labels",
        "functions",
        ["parent"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info(
        "Finished dropping and creating constraint: _functions_labels_parent_fk"
    )
    logger.info("Dropping constraint: _functions_tags_obj_id_fk")
    op.drop_constraint(
        "_functions_tags_obj_id_fk", "functions_tags", type_="foreignkey"
    )
    logger.info("Creating constraint: _functions_tags_obj_id_fk")
    op.create_foreign_key(
        "_functions_tags_obj_id_fk",
        "functions_tags",
        "functions",
        ["obj_id"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info("Finished dropping and creating constraint: _functions_tags_obj_id_fk")
    logger.info("Dropping constraint: _projects_labels_parent_fk")
    op.drop_constraint(
        "_projects_labels_parent_fk", "projects_labels", type_="foreignkey"
    )
    logger.info("Creating constraint: _projects_labels_parent_fk")
    op.create_foreign_key(
        "_projects_labels_parent_fk",
        "projects_labels",
        "projects",
        ["parent"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info("Finished dropping and creating constraint: _projects_labels_parent_fk")
    logger.info("Dropping constraint: _runs_labels_parent_fk")
    op.drop_constraint("_runs_labels_parent_fk", "runs_labels", type_="foreignkey")
    logger.info("Creating constraint: _runs_labels_parent_fk")
    op.create_foreign_key(
        "_runs_labels_parent_fk",
        "runs_labels",
        "runs",
        ["parent"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info("Finished dropping and creating constraint: _runs_labels_parent_fk")
    logger.info("Dropping constraint: _schedules_v2_labels_parent_fk")
    op.drop_constraint(
        "_schedules_v2_labels_parent_fk", "schedules_v2_labels", type_="foreignkey"
    )
    logger.info("Creating constraint: _schedules_v2_labels_parent_fk")
    op.create_foreign_key(
        "_schedules_v2_labels_parent_fk",
        "schedules_v2_labels",
        "schedules_v2",
        ["parent"],
        ["id"],
        ondelete="CASCADE",
    )
    logger.info(
        "Finished dropping and creating constraint: _schedules_v2_labels_parent_fk"
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "_schedules_v2_labels_parent_fk", "schedules_v2_labels", type_="foreignkey"
    )
    op.create_foreign_key(
        "_schedules_v2_labels_parent_fk",
        "schedules_v2_labels",
        "schedules_v2",
        ["parent"],
        ["id"],
    )
    op.drop_constraint("_runs_labels_parent_fk", "runs_labels", type_="foreignkey")
    op.create_foreign_key(
        "_runs_labels_parent_fk", "runs_labels", "runs", ["parent"], ["id"]
    )
    op.drop_constraint(
        "_projects_labels_parent_fk", "projects_labels", type_="foreignkey"
    )
    op.create_foreign_key(
        "_projects_labels_parent_fk", "projects_labels", "projects", ["parent"], ["id"]
    )
    op.drop_constraint(
        "_functions_tags_obj_id_fk", "functions_tags", type_="foreignkey"
    )
    op.create_foreign_key(
        "_functions_tags_obj_id_fk", "functions_tags", "functions", ["obj_id"], ["id"]
    )
    op.drop_constraint(
        "_functions_labels_parent_fk", "functions_labels", type_="foreignkey"
    )
    op.create_foreign_key(
        "_functions_labels_parent_fk",
        "functions_labels",
        "functions",
        ["parent"],
        ["id"],
    )
    op.drop_constraint(
        "_features_labels_parent_fk", "features_labels", type_="foreignkey"
    )
    op.create_foreign_key(
        "_features_labels_parent_fk", "features_labels", "features", ["parent"], ["id"]
    )
    op.drop_constraint("_features_feature_set_id_fk", "features", type_="foreignkey")
    op.create_foreign_key(
        "_features_feature_set_id_fk",
        "features",
        "feature_sets",
        ["feature_set_id"],
        ["id"],
    )
    op.drop_constraint(
        "_feature_vectors_tags_obj_id_fk", "feature_vectors_tags", type_="foreignkey"
    )
    op.create_foreign_key(
        "_feature_vectors_tags_obj_id_fk",
        "feature_vectors_tags",
        "feature_vectors",
        ["obj_id"],
        ["id"],
    )
    op.drop_constraint(
        "_feature_vectors_labels_parent_fk",
        "feature_vectors_labels",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "_feature_vectors_labels_parent_fk",
        "feature_vectors_labels",
        "feature_vectors",
        ["parent"],
        ["id"],
    )
    op.drop_constraint(
        "_feature_sets_tags_obj_id_fk", "feature_sets_tags", type_="foreignkey"
    )
    op.create_foreign_key(
        "_feature_sets_tags_obj_id_fk",
        "feature_sets_tags",
        "feature_sets",
        ["obj_id"],
        ["id"],
    )
    op.drop_constraint(
        "_feature_sets_labels_parent_fk", "feature_sets_labels", type_="foreignkey"
    )
    op.create_foreign_key(
        "_feature_sets_labels_parent_fk",
        "feature_sets_labels",
        "feature_sets",
        ["parent"],
        ["id"],
    )
    op.drop_constraint(
        "_entities_labels_parent_fk", "entities_labels", type_="foreignkey"
    )
    op.create_foreign_key(
        "_entities_labels_parent_fk", "entities_labels", "entities", ["parent"], ["id"]
    )
    op.drop_constraint("_entities_feature_set_id_fk", "entities", type_="foreignkey")
    op.create_foreign_key(
        "_entities_feature_set_id_fk",
        "entities",
        "feature_sets",
        ["feature_set_id"],
        ["id"],
    )
    op.drop_constraint(
        "artifacts_v2_tags_ibfk_1", "artifacts_v2_tags", type_="foreignkey"
    )
    op.create_foreign_key(
        "artifacts_v2_tags_ibfk_1",
        "artifacts_v2_tags",
        "artifacts_v2",
        ["obj_id"],
        ["id"],
    )
    op.drop_constraint(
        "artifacts_v2_labels_ibfk_1", "artifacts_v2_labels", type_="foreignkey"
    )
    op.create_foreign_key(
        "artifacts_v2_labels_ibfk_1",
        "artifacts_v2_labels",
        "artifacts_v2",
        ["parent"],
        ["id"],
    )
    op.drop_constraint(
        "_artifacts_labels_paren_fk", "artifacts_labels", type_="foreignkey"
    )
    op.create_foreign_key(
        "_artifacts_labels_paren_fk",
        "artifacts_labels",
        "artifacts",
        ["parent"],
        ["id"],
    )
    # ### end Alembic commands ###
