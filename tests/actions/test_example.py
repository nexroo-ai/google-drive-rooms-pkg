from unittest.mock import Mock, patch

import pytest

from template_rooms_pkg.actions.base import ActionResponse
from template_rooms_pkg.actions.example import example


class TestExampleAction:
    def test_example_action_returns_action_response(self):
        config = {"test_config": "value"}

        result = example(config, param1="test1", param2="test2")

        assert isinstance(result, ActionResponse)
        assert result.message == "Action executed successfully"
        assert result.code == 200
        assert result.tokens.stepAmount == 2000
        assert result.output.data["processed"] == "test1- processed -"

    def test_example_action_with_empty_config(self):
        config = {}

        result = example(config, param1="hello", param2="world")

        assert isinstance(result, ActionResponse)
        assert result.code == 200
        assert result.output.data["processed"] == "hello- processed -"

    def test_example_action_processes_parameters(self):
        config = None

        result = example(config, param1="input", param2="param")

        assert isinstance(result, ActionResponse)
        assert result.output.data["processed"] == "input- processed -"
