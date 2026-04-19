"""LangGraph agent state model — Track B."""

from __future__ import annotations

from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State that flows through every node in the ReAct graph.

    Fields
    ------
    messages:
        Full conversation history. ``add_messages`` is the LangGraph
        reducer — it appends new messages rather than replacing the list.
    citations:
        Source references collected by the search tool during this request.
    request_id:
        Trace ID for the whole request (set by the caller).
    tool_call_ids:
        Individual tool call trace IDs accumulated during the run.
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]
    citations: list[str]
    request_id: str
    tool_call_ids: list[str]