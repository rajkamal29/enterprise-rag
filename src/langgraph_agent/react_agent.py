"""LangGraph ReAct agent graph — Track B."""

from __future__ import annotations

import logging
from typing import Any, Literal, cast

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import AzureChatOpenAI
from langgraph.graph import END, START, StateGraph

from langgraph_agent.search_tool import search_knowledge_base
from langgraph_agent.state import AgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an enterprise knowledge assistant. Answer questions using ONLY the
information retrieved from the knowledge base via the search_knowledge_base tool.
If the answer is not in the retrieved documents, say so clearly — do not hallucinate.

Always call search_knowledge_base before answering.

Always end your answer with a numbered list of citations in this exact format:
  [1] <document title or source>
  [2] <document title or source>
"""

_TOOLS = [search_knowledge_base]


def build_graph(llm: AzureChatOpenAI) -> Any:
    """Compile and return the ReAct StateGraph.

    Args:
        llm: Authenticated AzureChatOpenAI instance with tool-calling enabled.

    Returns:
        Compiled LangGraph runnable.
    """
    llm_with_tools = llm.bind_tools(_TOOLS)

    def call_llm(state: AgentState) -> dict[str, Any]:
        messages = [SystemMessage(content=_SYSTEM_PROMPT)] + list(state["messages"])
        response = llm_with_tools.invoke(messages)
        tool_calls = cast(list[dict[str, Any]], getattr(response, "tool_calls", []))
        logger.debug("LLM response: tool_calls=%s", bool(tool_calls))
        return {"messages": [response]}

    def call_tools(state: AgentState) -> dict[str, Any]:
        last = state["messages"][-1]
        tool_calls = cast(list[dict[str, Any]], getattr(last, "tool_calls", []))
        tool_messages: list[ToolMessage] = []
        new_citations: list[str] = []

        for tc in tool_calls:
            result = search_knowledge_base.invoke(tc["args"])
            tool_messages.append(
                ToolMessage(content=result, tool_call_id=tc["id"])
            )
            # Extract source lines from formatted output for citations
            for line in result.splitlines():
                if line.startswith("[") and "(source:" in line:
                    new_citations.append(line.strip())

        return {
            "messages": tool_messages,
            "citations": state.get("citations", []) + new_citations,
            "tool_call_ids": state.get("tool_call_ids", [])
            + [tc["id"] for tc in tool_calls],
        }

    def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
        last = state["messages"][-1]
        tool_calls = cast(list[dict[str, Any]], getattr(last, "tool_calls", []))
        if tool_calls:
            return "tools"
        return "__end__"

    graph: Any = StateGraph(AgentState)
    graph.add_node("llm", call_llm)
    graph.add_node("tools", call_tools)
    graph.add_edge(START, "llm")
    graph.add_conditional_edges("llm", should_continue)
    graph.add_edge("tools", "llm")
    graph.add_edge("llm", END)

    return graph.compile()