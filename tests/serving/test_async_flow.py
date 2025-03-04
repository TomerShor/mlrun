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
from typing import Optional

import pytest

import mlrun
from mlrun.errors import MLRunInvalidArgumentError
from mlrun.serving import Model, ModelRunnerStep, ModelSelector
from mlrun.utils import logger
from tests.conftest import results

from .demo_states import *  # noqa


class _DummyStreamRaiser:
    def push(self, data):
        raise ValueError("DummyStreamRaiser raises an error")


def test_async_basic():
    function = mlrun.new_function("tests", kind="serving")
    flow = function.set_topology("flow", engine="async")
    queue = flow.to(name="s1", class_name="ChainWithContext").to(
        "$queue", "q1", path=""
    )

    s2 = queue.to(name="s2", class_name="ChainWithContext", function="some_function")
    s2.to(name="s4", class_name="ChainWithContext")
    s2.to(
        name="s5", class_name="ChainWithContext"
    ).respond()  # this state returns the resp

    queue.to(name="s3", class_name="ChainWithContext", function="some_other_function")

    # plot the graph for test & debug
    flow.plot(f"{results}/serving/async.png")

    server = function.to_mock_server()
    server.context.visits = {}
    logger.info(f"\nAsync Flow:\n{flow.to_yaml()}")
    resp = server.test(body=[])

    server.wait_for_completion()
    assert resp == ["s1", "s2", "s5"], "flow result is incorrect"
    assert server.context.visits == {
        "s1": 1,
        "s2": 1,
        "s4": 1,
        "s3": 1,
        "s5": 1,
    }, "flow didnt visit expected states"


def test_async_error_on_missing_function_parameter():
    function = mlrun.new_function("tests", kind="serving")
    flow = function.set_topology("flow", engine="async")
    queue = flow.to(name="s1", class_name="ChainWithContext").to(
        "$queue", "q1", path=""
    )

    with pytest.raises(
        MLRunInvalidArgumentError,
        match="step 's2' must specify a function, because it follows a queue step",
    ):
        queue.to(name="s2", class_name="ChainWithContext")


def test_async_nested():
    function = mlrun.new_function("tests", kind="serving")
    graph = function.set_topology("flow", engine="async")
    graph.add_step(name="s1", class_name="Echo")
    graph.add_step(name="s2", handler="multiply_input", after="s1")
    graph.add_step(name="s3", class_name="Echo", after="s2")

    router_step = graph.add_step("*", name="ensemble", after="s2")
    router_step.add_route("m1", class_name="ModelClass", model_path=".", multiplier=100)
    router_step.add_route("m2", class_name="ModelClass", model_path=".", multiplier=200)
    router_step.add_route(
        "m3:v1", class_name="ModelClass", model_path=".", multiplier=300
    )

    graph.add_step(name="final", class_name="Echo", after="ensemble").respond()

    server = function.to_mock_server()

    # plot the graph for test & debug
    graph.plot(f"{results}/serving/nested.png")
    resp = server.test("/v2/models/m2/infer", body={"inputs": [5]})
    server.wait_for_completion()
    # resp should be input (5) * multiply_input (2) * m2 multiplier (200)
    assert resp["outputs"] == 5 * 2 * 200, f"wrong health response {resp}"


def test_on_error():
    function = mlrun.new_function("tests", kind="serving")
    graph = function.set_topology("flow", engine="async")
    chain = graph.to("Chain", name="s1")
    chain.to("Raiser").error_handler(
        name="catch", class_name="EchoError", full_event=True
    ).to("Chain", name="s3")

    function.verbose = True
    server = function.to_mock_server()

    # plot the graph for test & debug
    graph.plot(f"{results}/serving/on_error.png")
    resp = server.test(body=[])
    server.wait_for_completion()
    if isinstance(resp, dict):
        assert (
            resp["error"] and resp["origin_state"] == "Raiser"
        ), f"error wasn't caught, resp={resp}"
    else:
        assert (
            resp.error and resp.origin_state == "Raiser"
        ), f"error wasn't caught, resp={resp}"


def test_push_error():
    function = mlrun.new_function("tests", kind="serving")
    graph = function.set_topology("flow", engine="async")
    chain = graph.to("Chain", name="s1")
    chain.to("Raiser")

    function.verbose = True
    server = function.to_mock_server()
    server.error_stream = "dummy:///nothing"
    # Force an error inside push_error itself
    server._error_stream_object = _DummyStreamRaiser()

    server.test(body=[])
    server.wait_for_completion()


class MyModel(Model):
    execution_mechanism = "naive"

    def __init__(self, *args, inc: int, gpu_number: Optional[int] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.inc = inc
        self.gpu_number = gpu_number

    def predict(self, body):
        body["n"] += self.inc
        body.pop("models", None)
        if self.gpu_number is not None:
            body["gpu"] = self.gpu_number
        return body

    async def predict_async(self, body):
        return self.predict(body)


def test_model_runner():
    function = mlrun.new_function("tests", kind="serving")
    graph = function.set_topology("flow", engine="async")
    model_runner_step = ModelRunnerStep(name="my_model_runner")
    model_runner_step.add_model(MyModel(name="my_model", inc=1))
    graph.to(model_runner_step).respond()

    server = function.to_mock_server()
    try:
        resp = server.test(body={"n": 1})
        assert resp == {"n": 2}
    finally:
        server.wait_for_completion()


class MyModelSelector(ModelSelector):
    def select(self, event, available_models: list[Model]) -> Optional[list[str]]:
        return event.body.get("models")


@pytest.mark.parametrize(
    "execution_mechanism",
    ("process_pool", "dedicated_process", "thread_pool", "asyncio", "naive"),
)
def test_model_runner_with_selector(execution_mechanism: str):
    m1 = MyModel(name="m1", inc=1)
    m2 = MyModel(name="m2", inc=2)
    # Normally, this is set at the class level, but for testing purposes, we set it on the instance
    m2.execution_mechanism = execution_mechanism

    function = mlrun.new_function("tests", kind="serving")
    graph = function.set_topology("flow", engine="async")
    model_runner_step = ModelRunnerStep(
        name="my_model_runner",
        model_selector="MyModelSelector",
    )
    model_runner_step.add_model(m1)
    model_runner_step.add_model(m2)
    graph.to(model_runner_step).respond()

    server = function.to_mock_server()
    try:
        # both models
        resp = server.test(body={"n": 1})
        assert resp == {"m1": {"n": 2}, "m2": {"n": 3}}

        # only m2
        resp = server.test(body={"n": 1, "models": ["m2"]})
        assert resp == {"m2": {"n": 3}}
    finally:
        server.wait_for_completion()


def test_model_runner_with_gpu_allocation():
    m1 = MyModel(name="m1", inc=1, gpu_number=1)
    m2 = MyModel(name="m2", inc=2, gpu_number=2)

    m1.execution_mechanism = m2.execution_mechanism = "dedicated_process"

    function = mlrun.new_function("tests", kind="serving")
    graph = function.set_topology("flow", engine="async")
    model_runner_step = ModelRunnerStep(
        name="my_model_runner",
    )
    model_runner_step.add_model(m1)
    model_runner_step.add_model(m2)
    graph.to(model_runner_step).respond()

    server = function.to_mock_server()
    try:
        for n in range(10):
            resp = server.test(body={"n": n})
            assert resp == {"m1": {"n": n + 1, "gpu": 1}, "m2": {"n": n + 2, "gpu": 2}}
    finally:
        server.wait_for_completion()
