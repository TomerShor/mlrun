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
import os
import unittest.mock
from typing import Optional

import pytest
from fastapi.testclient import TestClient
from pytest import fail
from sqlalchemy.orm import Session
from v3io.dataplane import RaiseForStatus
from v3io_frames import CreateError
from v3io_frames import frames_pb2 as fpb2

import mlrun.common.schemas
import mlrun.common.schemas.model_monitoring.constants
from mlrun.common.model_monitoring.helpers import parse_model_endpoint_store_prefix
from mlrun.config import config
from mlrun.errors import MLRunBadRequestError
from mlrun.utils.v3io_clients import get_frames_client, get_v3io_client

import framework.utils.clients.iguazio
from services.api.crud.model_monitoring.grafana import (
    parse_query_parameters,
    validate_query_parameters,
)
from services.api.tests.unit.api.test_model_endpoints import _mock_random_endpoint

ENV_PARAMS = {"V3IO_ACCESS_KEY", "V3IO_API", "V3IO_FRAMESD"}
TEST_PROJECT = "test3"


def _build_skip_message():
    return f"One of the required environment params is not initialized ({', '.join(ENV_PARAMS)})"


def _is_env_params_dont_exist() -> bool:
    return not all(os.environ.get(r, False) for r in ENV_PARAMS)


def test_grafana_proxy_model_endpoints_check_connection(
    db: Session, client: TestClient
):
    mlrun.mlconf.httpdb.authentication.mode = "iguazio"
    framework.utils.clients.iguazio.AsyncClient().verify_request_session = (
        unittest.mock.AsyncMock(
            return_value=(
                mlrun.common.schemas.AuthInfo(
                    username=None,
                    session="some-session",
                    data_session="some-session",
                    user_id=None,
                    user_unix_id=0,
                    user_group_ids=[],
                )
            )
        )
    )
    response = client.get(
        url="grafana-proxy/model-endpoints",
    )
    assert response.status_code == 200


@pytest.mark.skipif(
    _is_env_params_dont_exist(),
    reason=_build_skip_message(),
)
def test_grafana_list_endpoints(db: Session, client: TestClient):
    endpoints_in = [_mock_random_endpoint("active") for _ in range(5)]

    # Initialize endpoint store target object
    store_type_object = mlrun.model_monitoring.db.ObjectStoreFactory(value="v3io-nosql")
    endpoint_store = store_type_object.to_object_store(
        project=TEST_PROJECT, access_key=_get_access_key()
    )

    for endpoint in endpoints_in:
        endpoint_store.write_model_endpoint(endpoint.flat_dict())

    response = client.post(
        url="grafana-proxy/model-endpoints/query",
        headers={"X-V3io-Session-Key": _get_access_key()},
        json={
            "targets": [
                {"target": f"project={TEST_PROJECT};target_endpoint=list_endpoints"}
            ]
        },
    )

    response_json = response.json()
    if not response_json:
        fail(f"Empty response, expected list of dictionaries. {response_json}")

    response_json = response_json[0]
    if not response_json:
        fail(
            f"Empty dictionary, expected dictionary with 'columns', 'rows' and 'type' fields. {response_json}"
        )

    if "columns" not in response_json:
        fail(f"Missing 'columns' key in response dictionary. {response_json}")

    if "rows" not in response_json:
        fail(f"Missing 'rows' key in response dictionary. {response_json}")

    if "type" not in response_json:
        fail(f"Missing 'type' key in response dictionary. {response_json}")

    assert len(response_json["rows"]) == 5


def test_parse_query_parameters_failure():
    # No 'targets' in body
    with pytest.raises(MLRunBadRequestError):
        parse_query_parameters({})

    # No 'target' list in 'targets' dictionary
    with pytest.raises(MLRunBadRequestError):
        parse_query_parameters({"targets": []})

    # Target query not separated by equals ('=') char
    with pytest.raises(MLRunBadRequestError):
        parse_query_parameters({"targets": [{"target": "test"}]})


def test_parse_query_parameters_success():
    # Target query separated by equals ('=') char
    params = parse_query_parameters({"targets": [{"target": "test=some_test"}]})
    assert params["test"] == "some_test"

    # Target query separated by equals ('=') char (multiple queries)
    params = parse_query_parameters(
        {"targets": [{"target": "test=some_test;another_test=some_other_test"}]}
    )
    assert params["test"] == "some_test"
    assert params["another_test"] == "some_other_test"

    params = parse_query_parameters(
        {"targets": [{"target": "test=some_test;another_test=some_other_test;"}]}
    )
    assert params["test"] == "some_test"
    assert params["another_test"] == "some_other_test"


def test_validate_query_parameters_failure():
    # No 'target_endpoint' in query parameters
    with pytest.raises(MLRunBadRequestError):
        validate_query_parameters({})

    # target_endpoint unsupported
    with pytest.raises(MLRunBadRequestError):
        validate_query_parameters(
            {"target_endpoint": "unsupported_endpoint"}, {"supported_endpoint"}
        )


def test_validate_query_parameters_success():
    validate_query_parameters({"target_endpoint": "list_endpoints"}, {"list_endpoints"})


def _get_access_key() -> Optional[str]:
    return os.environ.get("V3IO_ACCESS_KEY")


@pytest.fixture(autouse=True)
def cleanup_endpoints(db: Session, client: TestClient):
    if not _is_env_params_dont_exist():
        kv_path = config.model_endpoint_monitoring.store_prefixes.default.format(
            project=TEST_PROJECT,
            kind=mlrun.common.schemas.model_monitoring.ModelMonitoringStoreKinds.ENDPOINTS,
        )
        _, kv_container, kv_path = parse_model_endpoint_store_prefix(kv_path)

        tsdb_path = config.model_endpoint_monitoring.store_prefixes.default.format(
            project=TEST_PROJECT,
            kind=mlrun.common.schemas.model_monitoring.ModelMonitoringStoreKinds.EVENTS,
        )
        _, tsdb_container, tsdb_path = parse_model_endpoint_store_prefix(tsdb_path)

        v3io = get_v3io_client(endpoint=config.v3io_api, access_key=_get_access_key())

        frames = get_frames_client(
            token=_get_access_key(),
            container=tsdb_container,
            address=config.v3io_framesd,
        )

        try:
            all_records = v3io.kv.new_cursor(
                container=kv_container,
                table_path=kv_path,
                raise_for_status=RaiseForStatus.never,
            ).all()

            all_records = [r["__name"] for r in all_records]

            # Cleanup KV
            for record in all_records:
                v3io.kv.delete(
                    container=kv_container,
                    table_path=kv_path,
                    key=record,
                    raise_for_status=RaiseForStatus.never,
                )
        except RuntimeError:
            pass

        try:
            # Cleanup TSDB
            frames.delete(
                backend="tsdb",
                table=tsdb_path,
                if_missing=fpb2.IGNORE,
            )
        except CreateError:
            pass
