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

import typing

import tabulate

import mlrun.common.schemas
import mlrun.lists
import mlrun.utils.helpers

from .base import NotificationBase


class ConsoleNotification(NotificationBase):
    """
    Client only notification for printing run status notifications in console
    """

    def push(
        self,
        message: str,
        severity: typing.Optional[
            typing.Union[mlrun.common.schemas.NotificationSeverity, str]
        ] = mlrun.common.schemas.NotificationSeverity.INFO,
        runs: typing.Optional[typing.Union[mlrun.lists.RunList, list]] = None,
        custom_html: typing.Optional[typing.Optional[str]] = None,
        alert: typing.Optional[mlrun.common.schemas.AlertConfig] = None,
        event_data: typing.Optional[mlrun.common.schemas.Event] = None,
    ):
        severity = self._resolve_severity(severity)
        print(f"[{severity}] {message}")

        if not runs:
            return

        if isinstance(runs, list):
            runs = mlrun.lists.RunList(runs)

        table = []
        for run in runs:
            state = run["status"].get("state", "")
            if state == "error":
                result = run["status"].get("error", "")
            else:
                result = mlrun.utils.helpers.dict_to_str(
                    run["status"].get("results", {})
                )

            table.append(
                [
                    state,
                    run["metadata"]["name"],
                    ".." + run["metadata"]["uid"][-6:],
                    result,
                ]
            )
        print(tabulate.tabulate(table, headers=["status", "name", "uid", "results"]))

    def _resolve_severity(
        self, severity: typing.Union[mlrun.common.schemas.NotificationSeverity, str]
    ):
        if isinstance(severity, mlrun.common.schemas.NotificationSeverity):
            return severity
        elif isinstance(severity, str) and (
            (severity_lowercase := severity.lower())
            in set(mlrun.common.schemas.NotificationSeverity)
        ):
            return mlrun.common.schemas.NotificationSeverity(severity_lowercase)

        return severity.lower()
