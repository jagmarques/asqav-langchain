"""LangChain callback handler that signs tool:start, tool:end, and tool:error
events via the Asqav API. All signing is fail-open. See README for usage."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from asqav.extras._base import AsqavAdapter

try:
    from langchain_core.callbacks import BaseCallbackHandler
except ImportError as err:
    raise ImportError(
        "asqav-langchain requires langchain-core. "
        "Install with: pip install asqav-langchain"
    ) from err

logger = logging.getLogger("asqav")

_MAX_LEN = 200


class AsqavCallbackHandler(AsqavAdapter, BaseCallbackHandler):
    """Sign LangChain and LangGraph tool call events (tool:start, tool:end,
    tool:error) via the Asqav API. Fail-open: signing errors are logged, not
    raised, so the agent pipeline never breaks because of governance.

    Pass an instance through the ``callbacks`` argument of any LangChain or
    LangGraph runnable. The handler hooks the documented stable observability
    surface (``on_tool_start`` / ``on_tool_end`` / ``on_tool_error`` on
    ``BaseCallbackHandler``).

    Args:
        api_key: Optional API key override (uses ``asqav.init()`` default).
        agent_name: Name for an Asqav agent (calls ``Agent.create``).
        agent_id: ID of an existing Asqav agent (calls ``Agent.get``).
    """

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Sign ``tool:start`` with tool name and input preview."""
        tool_name = (serialized or {}).get("name", "unknown")
        try:
            self._sign_action(
                "tool:start",
                {
                    "tool": tool_name,
                    "input": str(input_str)[:_MAX_LEN],
                    "run_id": str(run_id),
                },
            )
        except Exception as exc:
            logger.warning("asqav tool:start signing failed (fail-open): %s", exc)

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        """Sign ``tool:end`` with output metadata."""
        try:
            self._sign_action(
                "tool:end",
                {
                    "output_type": type(output).__name__,
                    "output_length": len(str(output)),
                    "run_id": str(run_id),
                },
            )
        except Exception as exc:
            logger.warning("asqav tool:end signing failed (fail-open): %s", exc)

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        """Sign ``tool:error`` with error details."""
        try:
            self._sign_action(
                "tool:error",
                {
                    "error_type": type(error).__name__,
                    "error": str(error)[:_MAX_LEN],
                    "run_id": str(run_id),
                },
            )
        except Exception as exc:
            logger.warning("asqav tool:error signing failed (fail-open): %s", exc)
