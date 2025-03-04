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
import http

import fastapi
import fastapi.concurrency
import sqlalchemy.orm

import mlrun.common.constants
import mlrun.common.schemas
from mlrun.utils.helpers import tag_name_regex_as_string

import framework.api.deps
import framework.utils.auth.verifier
import framework.utils.singletons.project_member
import services.api.crud.tags

router = fastapi.APIRouter(prefix="/projects/{project}/tags")


@router.post("/{tag}", response_model=mlrun.common.schemas.Tag)
async def overwrite_object_tags_with_tag(
    project: str,
    tag: str = fastapi.Path(..., regex=tag_name_regex_as_string()),
    tag_objects: mlrun.common.schemas.TagObjects = fastapi.Body(...),
    auth_info: mlrun.common.schemas.AuthInfo = fastapi.Depends(
        framework.api.deps.authenticate_request
    ),
    db_session: sqlalchemy.orm.Session = fastapi.Depends(
        framework.api.deps.get_db_session
    ),
):
    await fastapi.concurrency.run_in_threadpool(
        framework.utils.singletons.project_member.get_project_member().ensure_project,
        db_session,
        project,
        auth_info=auth_info,
    )

    # check permission per object type
    await (
        framework.utils.auth.verifier.AuthVerifier().query_project_resource_permissions(
            getattr(mlrun.common.schemas.AuthorizationResourceTypes, tag_objects.kind),
            project,
            resource_name="",
            # not actually overwriting objects, just overwriting the objects tags
            action=mlrun.common.schemas.AuthorizationAction.update,
            auth_info=auth_info,
        )
    )

    _check_reserved_tag(tag)

    await fastapi.concurrency.run_in_threadpool(
        services.api.crud.Tags().overwrite_object_tags_with_tag,
        db_session,
        project,
        tag,
        tag_objects,
    )
    return mlrun.common.schemas.Tag(name=tag, project=project)


@router.put("/{tag}", response_model=mlrun.common.schemas.Tag)
async def append_tag_to_objects(
    project: str,
    tag: str = fastapi.Path(..., regex=tag_name_regex_as_string()),
    tag_objects: mlrun.common.schemas.TagObjects = fastapi.Body(...),
    auth_info: mlrun.common.schemas.AuthInfo = fastapi.Depends(
        framework.api.deps.authenticate_request
    ),
    db_session: sqlalchemy.orm.Session = fastapi.Depends(
        framework.api.deps.get_db_session
    ),
):
    await fastapi.concurrency.run_in_threadpool(
        framework.utils.singletons.project_member.get_project_member().ensure_project,
        db_session,
        project,
        auth_info=auth_info,
    )

    await (
        framework.utils.auth.verifier.AuthVerifier().query_project_resource_permissions(
            getattr(mlrun.common.schemas.AuthorizationResourceTypes, tag_objects.kind),
            project,
            resource_name="",
            action=mlrun.common.schemas.AuthorizationAction.update,
            auth_info=auth_info,
        )
    )

    _check_reserved_tag(tag)

    await fastapi.concurrency.run_in_threadpool(
        services.api.crud.Tags().append_tag_to_objects,
        db_session,
        project,
        tag,
        tag_objects,
    )
    return mlrun.common.schemas.Tag(name=tag, project=project)


@router.delete("/{tag}", status_code=http.HTTPStatus.NO_CONTENT.value)
async def delete_tag_from_objects(
    project: str,
    tag: str,
    tag_objects: mlrun.common.schemas.TagObjects,
    auth_info: mlrun.common.schemas.AuthInfo = fastapi.Depends(
        framework.api.deps.authenticate_request
    ),
    db_session: sqlalchemy.orm.Session = fastapi.Depends(
        framework.api.deps.get_db_session
    ),
):
    await fastapi.concurrency.run_in_threadpool(
        framework.utils.singletons.project_member.get_project_member().ensure_project,
        db_session,
        project,
        auth_info=auth_info,
    )

    await (
        framework.utils.auth.verifier.AuthVerifier().query_project_resource_permissions(
            getattr(mlrun.common.schemas.AuthorizationResourceTypes, tag_objects.kind),
            project,
            resource_name="",
            # not actually deleting objects, just deleting the objects tags
            action=mlrun.common.schemas.AuthorizationAction.update,
            auth_info=auth_info,
        )
    )

    _check_reserved_tag(tag)

    await fastapi.concurrency.run_in_threadpool(
        services.api.crud.Tags().delete_tag_from_objects,
        db_session,
        project,
        tag,
        tag_objects,
    )
    return fastapi.Response(status_code=http.HTTPStatus.NO_CONTENT.value)


def _check_reserved_tag(tag: str):
    if tag == mlrun.common.constants.RESERVED_TAG_NAME_LATEST:
        raise mlrun.errors.MLRunInvalidArgumentError(
            f"`{mlrun.common.constants.RESERVED_TAG_NAME_LATEST}` is a reserved tag name and cannot "
            "be deleted or modified."
        )
