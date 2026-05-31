"""Tests for asqav-langchain callback handler. All Asqav calls are mocked;
no network access occurs."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


@pytest.fixture()
def mock_asqav():
    """Mock asqav.init() and Agent so no real API calls are made."""
    mock_agent = MagicMock()
    mock_agent.sign.return_value = MagicMock(signature="mock-sig", timestamp=1.0)
    with (
        patch("asqav.client._api_key", "sk_test_key"),
        patch("asqav.client.Agent.create", return_value=mock_agent),
        patch("asqav.client.Agent.get", return_value=mock_agent),
    ):
        yield mock_agent


class TestAsqavCallbackHandler:
    def test_is_base_callback_handler(self, mock_asqav: MagicMock):
        from langchain_core.callbacks import BaseCallbackHandler

        from asqav_langchain import AsqavCallbackHandler

        handler = AsqavCallbackHandler(agent_name="test-agent")
        assert isinstance(handler, BaseCallbackHandler)

    def test_init_creates_named_agent(self, mock_asqav: MagicMock):
        from asqav.client import Agent

        from asqav_langchain import AsqavCallbackHandler

        AsqavCallbackHandler(agent_name="test-agent")
        Agent.create.assert_called_once_with("test-agent")

    def test_init_with_agent_id(self, mock_asqav: MagicMock):
        from asqav.client import Agent

        from asqav_langchain import AsqavCallbackHandler

        AsqavCallbackHandler(agent_id="existing-agent-id")
        Agent.get.assert_called_once_with("existing-agent-id")

    def test_on_tool_start_signs(self, mock_asqav: MagicMock):
        from asqav_langchain import AsqavCallbackHandler

        handler = AsqavCallbackHandler(agent_name="test-agent")
        with patch.object(handler, "_sign_action", wraps=handler._sign_action) as spy:
            handler.on_tool_start(
                {"name": "search"}, "find news", run_id=uuid4()
            )
            spy.assert_called_once()
            action_type, context = spy.call_args.args[0], spy.call_args.args[1]
            assert action_type == "tool:start"
            assert context["tool"] == "search"
            assert context["input"] == "find news"

    def test_on_tool_end_signs(self, mock_asqav: MagicMock):
        from asqav_langchain import AsqavCallbackHandler

        handler = AsqavCallbackHandler(agent_name="test-agent")
        with patch.object(handler, "_sign_action", wraps=handler._sign_action) as spy:
            handler.on_tool_end("result text", run_id=uuid4())
            spy.assert_called_once()
            assert spy.call_args.args[0] == "tool:end"
            assert spy.call_args.args[1]["output_type"] == "str"

    def test_on_tool_error_signs(self, mock_asqav: MagicMock):
        from asqav_langchain import AsqavCallbackHandler

        handler = AsqavCallbackHandler(agent_name="test-agent")
        with patch.object(handler, "_sign_action", wraps=handler._sign_action) as spy:
            handler.on_tool_error(ValueError("boom"), run_id=uuid4())
            spy.assert_called_once()
            assert spy.call_args.args[0] == "tool:error"
            assert spy.call_args.args[1]["error_type"] == "ValueError"

    def test_fail_open_on_signing_error(self, mock_asqav: MagicMock):
        """A signing error inside the handler must not propagate."""
        from asqav_langchain import AsqavCallbackHandler

        handler = AsqavCallbackHandler(agent_name="test-agent")
        with patch.object(handler, "_sign_action", side_effect=RuntimeError("boom")):
            # Must not raise.
            handler.on_tool_start({"name": "t"}, "x", run_id=uuid4())
            handler.on_tool_end("out", run_id=uuid4())
            handler.on_tool_error(ValueError("e"), run_id=uuid4())

    def test_input_truncated(self, mock_asqav: MagicMock):
        from asqav_langchain import AsqavCallbackHandler

        handler = AsqavCallbackHandler(agent_name="test-agent")
        with patch.object(handler, "_sign_action", wraps=handler._sign_action) as spy:
            handler.on_tool_start({"name": "t"}, "x" * 500, run_id=uuid4())
            assert len(spy.call_args.args[1]["input"]) == 200
