# Copyright 2024 Iguazio
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

import json
import traceback
from typing import Any, Optional, Union

import mlrun.common.schemas
import mlrun.common.schemas.alert as alert_objects
import mlrun.common.schemas.model_monitoring.constants as mm_constants
import mlrun.model_monitoring.helpers
from mlrun.serving import GraphContext
from mlrun.serving.utils import StepToDict
from mlrun.utils import logger

from .context import MonitoringApplicationContext
from .results import (
    ModelMonitoringApplicationMetric,
    ModelMonitoringApplicationResult,
    _ModelMonitoringApplicationStats,
)


class _PushToMonitoringWriter(StepToDict):
    kind = "monitoring_application_stream_pusher"

    def __init__(self, project: str) -> None:
        """
        Class for pushing application results to the monitoring writer stream.

        :param project: Project name.
        """
        self.project = project
        self.output_stream = None

    def do(
        self,
        event: tuple[
            list[
                Union[
                    ModelMonitoringApplicationResult,
                    ModelMonitoringApplicationMetric,
                    _ModelMonitoringApplicationStats,
                ]
            ],
            MonitoringApplicationContext,
        ],
    ) -> None:
        """
        Push application results to the monitoring writer stream.

        :param event: Monitoring result(s) to push and the original event from the controller.
        """
        self._lazy_init()
        application_results, application_context = event
        writer_event = {
            mm_constants.WriterEvent.ENDPOINT_NAME: application_context.endpoint_name,
            mm_constants.WriterEvent.APPLICATION_NAME: application_context.application_name,
            mm_constants.WriterEvent.ENDPOINT_ID: application_context.endpoint_id,
            mm_constants.WriterEvent.START_INFER_TIME: application_context.start_infer_time.isoformat(
                sep=" ", timespec="microseconds"
            ),
            mm_constants.WriterEvent.END_INFER_TIME: application_context.end_infer_time.isoformat(
                sep=" ", timespec="microseconds"
            ),
        }
        for result in application_results:
            data = result.to_dict()
            if isinstance(result, ModelMonitoringApplicationResult):
                writer_event[mm_constants.WriterEvent.EVENT_KIND] = (
                    mm_constants.WriterEventKind.RESULT
                )
            elif isinstance(result, _ModelMonitoringApplicationStats):
                writer_event[mm_constants.WriterEvent.EVENT_KIND] = (
                    mm_constants.WriterEventKind.STATS
                )
            else:
                writer_event[mm_constants.WriterEvent.EVENT_KIND] = (
                    mm_constants.WriterEventKind.METRIC
                )
            writer_event[mm_constants.WriterEvent.DATA] = json.dumps(data)
            logger.debug(
                "Pushing data to output stream", writer_event=str(writer_event)
            )
            self.output_stream.push([writer_event])
            logger.debug("Pushed data to output stream successfully")

    def _lazy_init(self):
        if self.output_stream is None:
            self.output_stream = mlrun.model_monitoring.helpers.get_output_stream(
                project=self.project,
                function_name=mm_constants.MonitoringFunctionNames.WRITER,
            )


class _PrepareMonitoringEvent(StepToDict):
    def __init__(self, context: GraphContext, application_name: str) -> None:
        """
        Class for preparing the application event for the application step.

        :param application_name: Application name.
        """
        self.graph_context = context
        _ = self.graph_context.project_obj  # Ensure project exists
        self.application_name = application_name
        self.model_endpoints: dict[str, mlrun.common.schemas.ModelEndpoint] = {}

    def do(self, event: dict[str, Any]) -> MonitoringApplicationContext:
        """
        Prepare the application event for the application step.

        :param event: Application event.
        :return: Application context.
        """
        application_context = MonitoringApplicationContext._from_graph_ctx(
            application_name=self.application_name,
            event=event,
            model_endpoint_dict=self.model_endpoints,
            graph_context=self.graph_context,
        )

        self.model_endpoints.setdefault(
            application_context.endpoint_id, application_context.model_endpoint
        )

        return application_context


class _ApplicationErrorHandler(StepToDict):
    def __init__(self, project: str, name: Optional[str] = None):
        self.project = project
        self.name = name or "ApplicationErrorHandler"

    def do(self, event):
        """
        Handle model monitoring application error. This step will generate an event, describing the error.

        :param event: Application event.
        """

        error_data = {
            "Endpoint ID": event.body.endpoint_id,
            "Application Class": event.body.application_name,
            "Error": "".join(
                traceback.format_exception(
                    None, value=event.error, tb=event.error.__traceback__
                )
            ),
            "Timestamp": event.timestamp,
        }
        logger.error("Error in application step", **error_data)

        error_data["Error"] = event.error

        event_data = alert_objects.Event(
            kind=alert_objects.EventKind.MM_APP_FAILED,
            entity=alert_objects.EventEntities(
                kind=alert_objects.EventEntityKind.MODEL_MONITORING_APPLICATION,
                project=self.project,
                ids=[f"{self.project}_{event.body.application_name}"],
            ),
            value_dict=error_data,
        )

        mlrun.get_run_db().generate_event(
            name=alert_objects.EventKind.MM_APP_FAILED, event_data=event_data
        )
        logger.info("Event generated successfully")
