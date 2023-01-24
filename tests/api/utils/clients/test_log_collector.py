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

import unittest.mock

import fastapi.testclient
import pytest
import sqlalchemy.orm.session

import mlrun
import mlrun.api.schemas
import mlrun.api.utils.clients.log_collector


class StartLogResponse:
    def __init__(self, success, error):
        self.success = success
        self.error = error


class GetLogsResponse:
    def __init__(self, success, error, logs, total_calls):
        self.success = success
        self.error = error
        self.logs = logs
        self.total_calls = total_calls
        self.current_calls = 0

    # the following methods are required for the async iterator protocol
    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.current_calls < self.total_calls:
            self.current_calls += 1
            return self
        raise StopAsyncIteration


mlrun.mlconf.log_collector.address = "http://localhost:8080"
mlrun.mlconf.log_collector.mode = mlrun.api.schemas.LogsCollectorMode.sidecar


class TestLogCollector:
    @pytest.mark.asyncio
    async def test_start_log(
        self,
        db: sqlalchemy.orm.session.Session,
        client: fastapi.testclient.TestClient,
        monkeypatch,
    ):
        run_uid = "123"
        project_name = "some-project"
        selector = f"mlrun/project={project_name},mlrun/uid={run_uid}"
        log_collector = mlrun.api.utils.clients.log_collector.LogCollectorClient()

        log_collector._call = unittest.mock.AsyncMock(
            return_value=StartLogResponse(True, "")
        )
        success, error = await log_collector.start_logs(
            run_uid=run_uid, project=project_name, selector=selector
        )
        assert success is True and not error

        log_collector._call = unittest.mock.AsyncMock(
            return_value=StartLogResponse(False, "Failed to start logs")
        )
        with pytest.raises(mlrun.errors.MLRunInternalServerError):
            await log_collector.start_logs(
                run_uid=run_uid, project=project_name, selector=selector
            )

        success, error = await log_collector.start_logs(
            run_uid=run_uid,
            project=project_name,
            selector=selector,
            raise_on_error=False,
        )
        assert success is False and error == "Failed to start logs"

    @pytest.mark.asyncio
    async def test_get_logs(
        self, db: sqlalchemy.orm.session.Session, client: fastapi.testclient.TestClient
    ):
        run_uid = "123"
        project_name = "some-project"
        log_collector = mlrun.api.utils.clients.log_collector.LogCollectorClient()

        log_collector._call_stream = unittest.mock.MagicMock(
            return_value=GetLogsResponse(True, "", b"some log", 1)
        )

        log = await log_collector.get_logs(run_uid=run_uid, project=project_name)
        assert log == b"some log"

        # mock failed response for 5 calls for the next 2 tests, because get_logs retries 4 times
        log_collector._call_stream = unittest.mock.MagicMock(
            return_value=GetLogsResponse(False, "Failed to get logs", b"", 5),
        )
        with pytest.raises(mlrun.errors.MLRunInternalServerError):
            await log_collector.get_logs(run_uid=run_uid, project=project_name)

        log = await log_collector.get_logs(
            run_uid=run_uid, project=project_name, raise_on_error=False
        )
        assert log == b""
