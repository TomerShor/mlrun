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
#
import typing

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import mlrun.common.schemas
import mlrun.errors
import mlrun.runtimes.nuclio.function
import mlrun.runtimes.pod

import services.api.crud.runtimes.nuclio.function
import services.api.crud.runtimes.nuclio.helpers
from services.api.tests.unit.runtimes.base import TestRuntimeBase


class TestApplicationRuntime(TestRuntimeBase):
    @property
    def runtime_kind(self):
        # enables extending classes to run the same tests with different runtime
        return "application"

    @property
    def class_name(self):
        # enables extending classes to run the same tests with different class
        return "application"

    def test_compile_function_config_skipped_spec(
        self, db: Session, client: TestClient
    ):
        """
        Test that compiling function configuration with requirements and base image are skipped
        """
        function = self._generate_runtime(self.runtime_kind)
        requirements = ["requests", "numpy"]
        function.with_requirements(requirements=requirements)
        function.spec.build.base_image = "my-base-image"
        (
            _,
            _,
            config,
        ) = services.api.crud.runtimes.nuclio.function._compile_function_config(
            function
        )
        assert not mlrun.utils.get_in(
            config,
            "spec.build.commands",
        )
        assert not mlrun.utils.get_in(
            config,
            "spec.build.baseImage",
        )

    def test_create_function_validate_min_nuclio_version(
        self, db: Session, client: TestClient
    ):
        """Verify that the nuclio min version is validated by the ApplicationRuntime constructor"""
        mlrun.mlconf.nuclio_version = "1.12.14"
        with pytest.raises(mlrun.errors.MLRunIncompatibleVersionError) as exc:
            self._generate_runtime(self.runtime_kind)
        assert (
            str(exc.value)
            == "'Application Runtime' function requires Nuclio v1.13.1 or higher"
        )

    def _execute_run(self, runtime, **kwargs):
        # deploy_nuclio_function doesn't accept watch, so we need to remove it
        kwargs.pop("watch", None)
        services.api.crud.runtimes.nuclio.function.deploy_nuclio_function(
            runtime, **kwargs
        )

    def _generate_runtime(
        self, kind=None
    ) -> typing.Union[mlrun.runtimes.ApplicationRuntime]:
        runtime = mlrun.new_function(
            name=self.name,
            project=self.project,
            kind=kind or self.runtime_kind,
        )
        runtime._ensure_reverse_proxy_configurations(runtime)
        runtime._configure_application_sidecar()
        return runtime
