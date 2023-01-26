# Copyright 2018 Iguazio
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
import asyncio
import http
import typing

import mlrun.api.utils.clients.protocols.grpc
import mlrun.errors
import mlrun.utils.singleton
from mlrun.config import config
from mlrun.utils import logger


class LogCollectorClient(
    mlrun.api.utils.clients.protocols.grpc.BaseGRPCClient,
    metaclass=mlrun.utils.singleton.Singleton,
):
    name = "log_collector"

    def __init__(self, address: str = None):
        self._initialize_proto_client_imports()
        self.stub_class = self._log_collector_pb2_grpc.LogCollectorStub
        super().__init__(address=address or mlrun.mlconf.log_collector.address)

    def _initialize_proto_client_imports(self):
        # Importing the proto client classes here and not at the top of the file to avoid raising an import error
        # when the log_collector service is not enabled / the proto client wasn't compiled
        import mlrun.api.proto.log_collector_pb2
        import mlrun.api.proto.log_collector_pb2_grpc

        self._log_collector_pb2 = mlrun.api.proto.log_collector_pb2
        self._log_collector_pb2_grpc = mlrun.api.proto.log_collector_pb2_grpc

    async def start_logs(
        self,
        run_uid: str,
        selector: str,
        project: str = "",
        verbose: bool = True,
        raise_on_error: bool = True,
    ) -> (bool, str):
        """
        Start logs streaming from the log collector service
        :param run_uid: The run uid
        :param selector: The selector to filter the logs by (e.g. "application=mlrun,job-name=job")
            format is key1=value1,key2=value2
        :param project: The project name
        :param verbose: Whether to log errors
        :param raise_on_error: Whether to raise an exception on error
        :return: A tuple of (success, error)
        """
        request = self._log_collector_pb2.StartLogRequest(
            runUID=run_uid, selector=selector, projectName=project
        )
        logger.debug(
            "Starting logs", run_uid=run_uid, selector=selector, project=project
        )
        response = await self._call("StartLog", request)
        if not response.success:
            msg = f"Failed to start logs for run {run_uid}"
            if raise_on_error:
                raise mlrun.errors.MLRunInternalServerError(
                    f"{msg},error= {response.error}"
                )
            if verbose:
                logger.warning(msg, error=response.error)
        return response.success, response.error

    async def get_logs(
        self,
        run_uid: str,
        project: str,
        offset: int = 0,
        size: int = -1,
        verbose: bool = True,
        raise_on_error: bool = True,
    ) -> typing.AsyncIterable[bytes]:
        """
        Get logs from the log collector service
        :param run_uid: The run uid
        :param project: The project name
        :param offset: The offset to start reading from
        :param size: The number of bytes to read (-1 for all)
        :param verbose: Whether to log errors
        :param raise_on_error: Whether to raise an exception on error
        :return: The logs bytes
        """
        request = self._log_collector_pb2.GetLogsRequest(
            runUID=run_uid,
            projectName=project,
            offset=offset,
            size=size,
        )

        # TODO: make a request to ensure file exists, return 404 if not
        # otherwise, the first requests will return 500

        # retry calling the server, it can fail in case the log-collector hasn't started collecting logs for this yet
        # TODO: add async retry function
        try_count = 0
        while True:
            try:
                response_stream = self._call_stream("GetLogs", request)
                async for chunk in response_stream:
                    if not chunk.success:
                        msg = f"Failed to get logs for run {run_uid}"
                        if raise_on_error:
                            raise mlrun.errors.MLRunInternalServerError(
                                f"{msg},error= {chunk.error}"
                            )
                        if verbose:
                            logger.warning(msg, error=chunk.error)
                    yield chunk.logs
                return
            except Exception as exc:
                try_count += 1
                logger.warning(
                    "Failed to get logs, retrying",
                    try_count=try_count,
                    exc=mlrun.errors.err_to_str(exc),
                )
                if try_count == config.log_collector.get_logs.max_retries:
                    raise mlrun.errors.raise_for_status_code(
                        http.HTTPStatus.INTERNAL_SERVER_ERROR.value,
                        mlrun.errors.err_to_str(exc),
                    )
                await asyncio.sleep(3)
