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
import unittest.mock

import fastapi.testclient
import httpx
import pytest
import sqlalchemy.orm

import mlrun
import mlrun.common.schemas
from tests.common_fixtures import aioresponses_mock

import framework.utils.auth.verifier
import services.api.tests.unit.api.utils
import services.api.utils.singletons.scheduler
from framework.utils.singletons.db import get_db
from services.api.daemon import daemon

ORIGINAL_VERSIONED_API_PREFIX = daemon.service.base_versioned_service_prefix


async def do_nothing():
    pass


def test_list_schedules(
    db: sqlalchemy.orm.Session, client: fastapi.testclient.TestClient
) -> None:
    project_names = [
        mlrun.mlconf.default_project,
        "another-project",
        "yet-another-project",
    ]

    framework.utils.auth.verifier.AuthVerifier().filter_projects_by_permissions = (
        unittest.mock.AsyncMock(return_value=project_names)
    )

    for project in project_names:
        resp = client.get(f"projects/{project}/schedules")
        assert resp.status_code == http.HTTPStatus.OK.value, "status"
        assert "schedules" in resp.json(), "no schedules"

    schedule_name = "schedule-name"
    schedule_name_2 = "schedule-name-2"

    for project in project_names:
        labels_1 = {
            "label1": "value1",
        }
        cron_trigger = mlrun.common.schemas.ScheduleCronTrigger(year="1999")
        get_db().create_schedule(
            db,
            project,
            schedule_name,
            mlrun.common.schemas.ScheduleKinds.local_function,
            do_nothing,
            cron_trigger,
            mlrun.mlconf.httpdb.scheduling.default_concurrency_limit,
            labels_1,
        )

        labels_2 = {
            "label2": "value2",
            "label3": "value3",
        }
        get_db().create_schedule(
            db,
            project,
            schedule_name_2,
            mlrun.common.schemas.ScheduleKinds.local_function,
            do_nothing,
            cron_trigger,
            mlrun.mlconf.httpdb.scheduling.default_concurrency_limit,
            labels_2,
        )

        _get_and_assert_single_schedule(
            client, {"labels": "label1"}, schedule_name, project
        )
        _get_and_assert_single_schedule(
            client, {"label": "label1"}, schedule_name, project
        )
        _get_and_assert_single_schedule(
            client, {"labels": "label2"}, schedule_name_2, project
        )
        _get_and_assert_single_schedule(
            client, {"label": ["label2"]}, schedule_name_2, project
        )
        _get_and_assert_single_schedule(
            client, {"label": ["label2", "label3"]}, schedule_name_2, project
        )
        _get_and_assert_single_schedule(
            client, {"labels": "label1=value1"}, schedule_name, project
        )
        _get_and_assert_single_schedule(
            client, {"labels": "label2=value2"}, schedule_name_2, project
        )
        _get_and_assert_single_schedule(
            client, {"label": "label2=value2"}, schedule_name_2, project
        )
        _get_and_assert_single_schedule(
            client, {"label": ["label2=value2"]}, schedule_name_2, project
        )
        _get_and_assert_single_schedule(
            client,
            {"labels": ["label2=value2", "label3=value3"]},
            schedule_name_2,
            project,
        )

    # Validate multi-project query
    resp = client.get("projects/*/schedules", params={"labels": "label1"})
    assert resp.status_code == http.HTTPStatus.OK.value, "status"
    result = resp.json()["schedules"]
    assert len(result) == len(project_names)
    for result_schedule in result:
        assert result_schedule["name"] == schedule_name
        # Each project name should appear exactly once
        assert result_schedule["project"] in project_names
        project_names.remove(result_schedule["project"])


@pytest.mark.parametrize(
    "method, body, expected_status, expected_body",
    [
        # deleting schedule failed for unknown reason
        [
            "DELETE",
            None,
            http.HTTPStatus.INTERNAL_SERVER_ERROR.value,
            {"detail": "Unknown error"},
        ],
        # deleting schedule succeeded
        [
            "DELETE",
            None,
            http.HTTPStatus.NOT_FOUND.value,
            {},
        ],
        # we don't check if the project exists in update schedule, but rather query from the db and raise exception
        # if schedule doesn't exist
        [
            "PUT",
            services.api.tests.unit.api.utils.compile_schedule(),
            http.HTTPStatus.NOT_FOUND.value,
            {
                "detail": "MLRunNotFoundError('Schedule not found: project={project_name}, name={schedule_name}')"
            },
        ],
        # updating schedule failed for unknown reason
        [
            "PUT",
            services.api.tests.unit.api.utils.compile_schedule(),
            http.HTTPStatus.NOT_FOUND.value,
            {
                "detail": "MLRunNotFoundError('Schedule not found: project={project_name}, name={schedule_name}')"
            },
        ],
        # project exists, expecting to create
        [
            "PUT",
            services.api.tests.unit.api.utils.compile_schedule(),
            http.HTTPStatus.OK.value,
            {},
        ],
    ],
)
@pytest.mark.asyncio
async def test_redirection_from_worker_to_chief_schedule(
    db: sqlalchemy.orm.Session,
    async_client: httpx.AsyncClient,
    aioresponses_mock: aioresponses_mock,
    method: str,
    body: dict,
    expected_status: int,
    expected_body: dict,
):
    project_name = "test-project"
    schedule_name = "test_schedule"
    endpoint, chief_mocked_url = _prepare_test_redirection_from_worker_to_chief(
        project=project_name, endpoint_suffix=schedule_name
    )

    # template the expected body
    _format_expected_body(
        expected_body, project_name=project_name, schedule_name=schedule_name
    )

    # what the chief will return
    aioresponses_mock.add(
        chief_mocked_url,
        method,
        status=expected_status,
        payload=expected_body,
    )
    response = await async_client.request(method, endpoint, data=body)
    assert response.status_code == expected_status
    assert response.json() == expected_body
    aioresponses_mock.assert_called_once()


@pytest.mark.parametrize(
    "expected_status, expected_body",
    [
        [
            # invoking schedule failed for unknown reason
            http.HTTPStatus.INTERNAL_SERVER_ERROR.value,
            {"detail": {"reason": "Unknown error"}},
        ],
        [
            # expecting to succeed
            http.HTTPStatus.NOT_FOUND.value,
            {},
        ],
    ],
)
@pytest.mark.asyncio
async def test_redirection_from_worker_to_chief_delete_schedules(
    db: sqlalchemy.orm.Session,
    async_client: httpx.AsyncClient,
    aioresponses_mock: aioresponses_mock,
    expected_status: int,
    expected_body: dict,
):
    # so get_scheduler().list_schedules, which is called in the delete_schedules endpoint, will return something
    services.api.utils.singletons.scheduler.ensure_scheduler()
    endpoint, chief_mocked_url = _prepare_test_redirection_from_worker_to_chief(
        project="test-project",
    )

    aioresponses_mock.delete(
        chief_mocked_url,
        status=expected_status,
        payload=expected_body,
    )

    response = await async_client.delete(endpoint)
    assert response.status_code == expected_status
    assert response.json() == expected_body


@pytest.mark.parametrize(
    "expected_status, expected_body",
    [
        [
            # invoking schedule failed for unknown reason
            http.HTTPStatus.INTERNAL_SERVER_ERROR.value,
            {"detail": {"reason": "unknown error"}},
        ],
        [
            # expecting to succeed
            http.HTTPStatus.OK.value,
            {},
        ],
    ],
)
@pytest.mark.asyncio
async def test_redirection_from_worker_to_chief_invoke_schedule(
    db: sqlalchemy.orm.Session,
    async_client: httpx.AsyncClient,
    aioresponses_mock: aioresponses_mock,
    expected_status: int,
    expected_body: dict,
):
    endpoint, chief_mocked_url = _prepare_test_redirection_from_worker_to_chief(
        project="test-project", endpoint_suffix="test_scheduler/invoke"
    )

    aioresponses_mock.post(
        chief_mocked_url,
        status=expected_status,
        payload=expected_body,
    )

    response = await async_client.post(endpoint)
    assert response.status_code == expected_status
    assert response.json() == expected_body


def _prepare_test_redirection_from_worker_to_chief(project, endpoint_suffix=""):
    mlrun.mlconf.httpdb.clusterization.chief.url = "http://chief:8080"
    mlrun.mlconf.httpdb.clusterization.role = "worker"
    mlrun.mlconf.httpdb.clusterization.worker.request_timeout = 3
    endpoint = f"projects/{project}/schedules"
    if endpoint_suffix:
        endpoint = f"{endpoint}/{endpoint_suffix}"
    chief_mocked_url = f"{mlrun.mlconf.httpdb.clusterization.chief.url}{ORIGINAL_VERSIONED_API_PREFIX}/{endpoint}"
    return endpoint, chief_mocked_url


def _get_and_assert_single_schedule(
    client: fastapi.testclient.TestClient,
    get_params: dict,
    schedule_name: str,
    project: str,
):
    resp = client.get(f"projects/{project}/schedules", params=get_params)
    assert resp.status_code == http.HTTPStatus.OK.value, "status"
    result = resp.json()["schedules"]
    assert len(result) == 1
    assert result[0]["name"] == schedule_name


def _format_expected_body(expected_body: dict, **kwargs):
    if "detail" in expected_body:
        expected_body["detail"] = expected_body["detail"].format(**kwargs)
    return expected_body
