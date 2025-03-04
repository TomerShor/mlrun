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
import datetime
import uuid
from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Query, Request, Response
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

import mlrun.common.formatters
import mlrun.common.runtimes.constants
import mlrun.common.schemas
from mlrun.utils import logger

import framework.utils.auth.verifier
import framework.utils.background_tasks
import framework.utils.notifications
import framework.utils.pagination
import framework.utils.singletons.db as db_singleton
import framework.utils.singletons.project_member
import services.api.crud
from framework.api import deps
from framework.api.utils import log_and_raise

router = APIRouter()


@router.post("/projects/{project}/runs/{uid}")
async def store_run(
    request: Request,
    project: str,
    uid: str,
    iter: int = 0,
    auth_info: mlrun.common.schemas.AuthInfo = Depends(deps.authenticate_request),
    db_session: Session = Depends(deps.get_db_session),
):
    await run_in_threadpool(
        framework.utils.singletons.project_member.get_project_member().ensure_project,
        db_session,
        project,
        auth_info=auth_info,
    )
    await (
        framework.utils.auth.verifier.AuthVerifier().query_project_resource_permissions(
            mlrun.common.schemas.AuthorizationResourceTypes.run,
            project,
            uid,
            mlrun.common.schemas.AuthorizationAction.store,
            auth_info,
        )
    )
    data = None
    try:
        data = await request.json()
    except ValueError:
        log_and_raise(HTTPStatus.BAD_REQUEST.value, reason="bad JSON body")

    await run_in_threadpool(
        services.api.crud.Runs().store_run,
        db_session,
        data,
        uid,
        iter,
        project,
    )
    return {}


@router.patch("/projects/{project}/runs/{uid}")
async def update_run(
    request: Request,
    project: str,
    uid: str,
    iter: int = 0,
    auth_info: mlrun.common.schemas.AuthInfo = Depends(deps.authenticate_request),
    db_session: Session = Depends(deps.get_db_session),
):
    await (
        framework.utils.auth.verifier.AuthVerifier().query_project_resource_permissions(
            mlrun.common.schemas.AuthorizationResourceTypes.run,
            project,
            uid,
            mlrun.common.schemas.AuthorizationAction.update,
            auth_info,
        )
    )
    data = None
    try:
        data = await request.json()
    except ValueError:
        log_and_raise(HTTPStatus.BAD_REQUEST.value, reason="bad JSON body")

    await run_in_threadpool(
        services.api.crud.Runs().update_run,
        db_session,
        project,
        uid,
        iter,
        data,
    )
    return {}


@router.get("/projects/{project}/runs/{uid}")
async def get_run(
    project: str,
    uid: str,
    iter: int = 0,
    auth_info: mlrun.common.schemas.AuthInfo = Depends(deps.authenticate_request),
    db_session: Session = Depends(deps.get_db_session),
    format_: mlrun.common.formatters.RunFormat = Query(
        mlrun.common.formatters.RunFormat.full, alias="format"
    ),
):
    data = await run_in_threadpool(
        services.api.crud.Runs().get_run, db_session, uid, iter, project, format_
    )
    await (
        framework.utils.auth.verifier.AuthVerifier().query_project_resource_permissions(
            mlrun.common.schemas.AuthorizationResourceTypes.run,
            project,
            uid,
            mlrun.common.schemas.AuthorizationAction.read,
            auth_info,
        )
    )
    return {
        "data": data,
    }


@router.delete("/projects/{project}/runs/{uid}")
async def delete_run(
    project: str,
    uid: str,
    iter: int = 0,
    auth_info: mlrun.common.schemas.AuthInfo = Depends(deps.authenticate_request),
    db_session: Session = Depends(deps.get_db_session),
):
    await (
        framework.utils.auth.verifier.AuthVerifier().query_project_resource_permissions(
            mlrun.common.schemas.AuthorizationResourceTypes.run,
            project,
            uid,
            mlrun.common.schemas.AuthorizationAction.delete,
            auth_info,
        )
    )
    await services.api.crud.Runs().delete_run(
        db_session,
        uid,
        iter,
        project,
    )
    return {}


@router.get("/projects/{project}/runs")
async def list_runs(
    project: Optional[str] = None,
    name: Optional[str] = None,
    uid: list[str] = Query([]),
    labels: list[str] = Query([], alias="label"),
    states: list[str] = Query([], alias="state"),
    sort: bool = True,
    iter: bool = True,
    start_time_from: Optional[str] = None,
    start_time_to: Optional[str] = None,
    last_update_time_from: Optional[str] = None,
    last_update_time_to: Optional[str] = None,
    end_time_from: Optional[str] = None,
    end_time_to: Optional[str] = None,
    partition_by: mlrun.common.schemas.RunPartitionByField = Query(
        None, alias="partition-by"
    ),
    rows_per_partition: int = Query(1, alias="rows-per-partition", gt=0),
    partition_sort_by: mlrun.common.schemas.SortField = Query(
        None, alias="partition-sort-by"
    ),
    partition_order: mlrun.common.schemas.OrderType = Query(
        mlrun.common.schemas.OrderType.desc, alias="partition-order"
    ),
    max_partitions: int = Query(0, alias="max-partitions", ge=0),
    with_notifications: bool = Query(False, alias="with-notifications"),
    page: int = Query(None, gt=0),
    page_size: int = Query(None, alias="page-size", gt=0),
    page_token: str = Query(None, alias="page-token"),
    auth_info: mlrun.common.schemas.AuthInfo = Depends(deps.authenticate_request),
    db_session: Session = Depends(deps.get_db_session),
):
    allowed_project_names = (
        await services.api.crud.Projects().list_allowed_project_names(
            db_session, auth_info, project=project
        )
    )

    paginator = framework.utils.pagination.Paginator()

    async def _filter_runs(_runs):
        return await framework.utils.auth.verifier.AuthVerifier().filter_project_resources_by_permissions(
            mlrun.common.schemas.AuthorizationResourceTypes.run,
            _runs,
            lambda run: (
                run.get("metadata", {}).get("project", mlrun.mlconf.default_project),
                run.get("metadata", {}).get("uid"),
            ),
            auth_info,
        )

    runs, page_info = await paginator.paginate_permission_filtered_request(
        db_session,
        services.api.crud.Runs().list_runs,
        _filter_runs,
        auth_info,
        token=page_token,
        page=page,
        page_size=page_size,
        name=name,
        uid=uid,
        project=allowed_project_names,
        labels=labels,
        states=states,
        sort=sort,
        iter=iter,
        start_time_from=start_time_from,
        start_time_to=start_time_to,
        last_update_time_from=last_update_time_from,
        last_update_time_to=last_update_time_to,
        end_time_from=end_time_from,
        end_time_to=end_time_to,
        partition_by=partition_by,
        rows_per_partition=rows_per_partition,
        partition_sort_by=partition_sort_by,
        partition_order=partition_order,
        max_partitions=max_partitions,
        with_notifications=with_notifications,
    )
    return {
        "runs": runs,
        "pagination": page_info,
    }


@router.delete("/projects/{project}/runs")
async def delete_runs(
    project: Optional[str] = None,
    name: Optional[str] = None,
    labels: list[str] = Query([], alias="label"),
    state: Optional[str] = None,
    days_ago: Optional[int] = None,
    auth_info: mlrun.common.schemas.AuthInfo = Depends(deps.authenticate_request),
    db_session: Session = Depends(deps.get_db_session),
):
    runs = []

    # TODO: handle project permissions like in the list endpoints
    if not project or project != "*":
        # Currently we don't differentiate between runs permissions inside a project.
        # Meaning there is no reason at the moment to query the permission for each run under the project
        # TODO check for every run when we will manage permission per run inside a project
        await framework.utils.auth.verifier.AuthVerifier().query_project_resource_permissions(
            mlrun.common.schemas.AuthorizationResourceTypes.run,
            project or mlrun.mlconf.default_project,
            "",
            mlrun.common.schemas.AuthorizationAction.delete,
            auth_info,
        )
    else:
        start_time_from = None
        if days_ago:
            start_time_from = datetime.datetime.now(
                datetime.timezone.utc
            ) - datetime.timedelta(days=days_ago)
        runs = await run_in_threadpool(
            services.api.crud.Runs().list_runs,
            db_session,
            name,
            project=project,
            labels=labels,
            state=state,
            start_time_from=start_time_from,
            return_as_run_structs=False,
        )
        projects = set(run.project or mlrun.mlconf.default_project for run in runs)
        for run_project in projects:
            # currently we fail if the user doesn't has permissions to delete runs to one of the projects in the system
            # TODO: Delete only runs from projects that user has permissions to
            await framework.utils.auth.verifier.AuthVerifier().query_project_resource_permissions(
                mlrun.common.schemas.AuthorizationResourceTypes.run,
                run_project,
                "",
                mlrun.common.schemas.AuthorizationAction.delete,
                auth_info,
            )

    # TODO: make a background task?
    await services.api.crud.Runs().delete_runs(
        db_session,
        name,
        project,
        labels,
        state,
        days_ago,
        runs,
    )
    return {}


@router.put(
    "/projects/{project}/runs/{uid}/notifications",
    status_code=HTTPStatus.OK.value,
)
async def set_run_notifications(
    project: str,
    uid: str,
    set_notifications_request: mlrun.common.schemas.SetNotificationRequest = Body(...),
    auth_info: mlrun.common.schemas.AuthInfo = Depends(deps.authenticate_request),
    db_session: Session = Depends(deps.get_db_session),
):
    await run_in_threadpool(
        framework.utils.singletons.project_member.get_project_member().ensure_project,
        db_session,
        project,
        auth_info=auth_info,
    )

    # check permission per object type
    await (
        framework.utils.auth.verifier.AuthVerifier().query_project_resource_permissions(
            mlrun.common.schemas.AuthorizationResourceTypes.run,
            project,
            resource_name=uid,
            action=mlrun.common.schemas.AuthorizationAction.update,
            auth_info=auth_info,
        )
    )

    await run_in_threadpool(
        services.api.crud.Notifications().set_object_notifications,
        db_session,
        auth_info,
        project,
        set_notifications_request.notifications,
        mlrun.common.schemas.RunIdentifier(uid=uid),
    )
    return Response(status_code=HTTPStatus.OK.value)


@router.post(
    "/projects/{project}/runs/{uid}/abort",
    response_model=mlrun.common.schemas.BackgroundTask,
    status_code=HTTPStatus.ACCEPTED.value,
)
async def abort_run(
    request: Request,
    project: str,
    uid: str,
    background_tasks: BackgroundTasks,
    iter: int = 0,
    auth_info: mlrun.common.schemas.AuthInfo = Depends(deps.authenticate_request),
    db_session: Session = Depends(deps.get_db_session),
):
    # check permission per object type
    await (
        framework.utils.auth.verifier.AuthVerifier().query_project_resource_permissions(
            mlrun.common.schemas.AuthorizationResourceTypes.run,
            project,
            resource_name=uid,
            action=mlrun.common.schemas.AuthorizationAction.update,
            auth_info=auth_info,
        )
    )

    data = None
    try:
        data = await request.json()
    except ValueError:
        log_and_raise(HTTPStatus.BAD_REQUEST.value, reason="bad JSON body")

    run = await run_in_threadpool(
        services.api.crud.Runs().get_run, db_session, uid, iter, project
    )

    current_run_state = run.get("status", {}).get("state")
    if current_run_state in [
        mlrun.common.runtimes.constants.RunStates.aborting,
        mlrun.common.runtimes.constants.RunStates.aborted,
    ]:
        background_task_id = run.get("status", {}).get("abort_task_id")
        if background_task_id:
            # get the background task and check if it's still running
            try:
                background_task = await run_in_threadpool(
                    framework.utils.background_tasks.ProjectBackgroundTasksHandler().get_background_task,
                    db_session,
                    background_task_id,
                    project,
                )

                if (
                    background_task.status.state
                    in mlrun.common.schemas.BackgroundTaskState.running
                ):
                    logger.debug(
                        "Abort background task is still running, returning it",
                        background_task_id=background_task_id,
                        project=project,
                        uid=uid,
                    )
                    return background_task

                # if the background task completed, give some grace time before triggering another one
                elif (
                    background_task.status.state
                    == mlrun.common.schemas.BackgroundTaskState.succeeded
                ):
                    grace_timedelta = datetime.timedelta(
                        seconds=int(
                            mlrun.mlconf.background_tasks.default_timeouts.operations.abort_grace_period
                        )
                    )
                    if (
                        datetime.datetime.utcnow() - background_task.metadata.updated
                        < grace_timedelta
                    ):
                        logger.debug(
                            "Abort background task completed, but grace time didn't pass yet, returning it",
                            background_task_id=background_task_id,
                            project=project,
                            uid=uid,
                        )
                        return background_task
                    else:
                        logger.debug(
                            "Abort background task completed, but grace time passed, creating a new one",
                            background_task_id=background_task_id,
                            project=project,
                            uid=uid,
                        )

            except mlrun.errors.MLRunNotFoundError:
                logger.warning(
                    "Abort background task not found, creating a new one",
                    background_task_id=background_task_id,
                    project=project,
                    uid=uid,
                )

    new_background_task_id = str(uuid.uuid4())
    background_task = await run_in_threadpool(
        framework.utils.background_tasks.ProjectBackgroundTasksHandler().create_background_task,
        db_session,
        project,
        background_tasks,
        services.api.crud.Runs().abort_run,
        mlrun.mlconf.background_tasks.default_timeouts.operations.run_abortion,
        new_background_task_id,
        # args for abort_run
        db_session,
        project,
        uid,
        iter,
        run_updates=data,
        run=run,
        new_background_task_id=new_background_task_id,
    )

    return background_task


@router.post(
    "/projects/{project}/runs/{uid}/push-notifications",
    response_model=mlrun.common.schemas.BackgroundTask,
)
async def push_notifications(
    project: str,
    uid: str,
    background_tasks: BackgroundTasks,
    auth_info: mlrun.common.schemas.AuthInfo = Depends(deps.authenticate_request),
    db_session: Session = Depends(deps.get_db_session),
):
    await (
        framework.utils.auth.verifier.AuthVerifier().query_project_resource_permissions(
            mlrun.common.schemas.AuthorizationResourceTypes.run,
            project,
            uid,
            mlrun.common.schemas.AuthorizationAction.update,
            auth_info,
        )
    )
    run = await run_in_threadpool(
        services.api.crud.Runs().get_run,
        db_session,
        uid,
        0,
        project,
        mlrun.common.formatters.RunFormat.notifications,
    )

    background_task = await run_in_threadpool(
        framework.utils.background_tasks.ProjectBackgroundTasksHandler().create_background_task,
        db_session,
        project,
        background_tasks,
        _push_notifications,
        mlrun.mlconf.background_tasks.default_timeouts.push_notifications,
        framework.utils.background_tasks.BackgroundTaskKinds.push_notification.format(
            project, uid
        ),
        db_session,
        run,
    )
    return background_task


def _push_notifications(db_session, run):
    db = db_singleton.get_db()
    run = framework.utils.notifications.unmask_notification_params_secret_on_task(
        db, db_session, run
    )
    run_notification_pusher_class = (
        framework.utils.notifications.notification_pusher.RunNotificationPusher
    )
    run_notification_pusher_class(
        [run],
        run_notification_pusher_class.resolve_notifications_default_params(),
    ).push()
