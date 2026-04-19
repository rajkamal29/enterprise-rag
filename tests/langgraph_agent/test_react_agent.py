"""Unit tests for the LangGraph ReAct agent (Track B)."""

from __future__ import annotations

from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from foundry.rag_agent import AgentResponse
from langgraph_agent.search_tool import init_search_tool

# ---------------------------------------------------------------------------
# search_tool tests
# ---------------------------------------------------------------------------


def test_search_tool_returns_error_when_not_initialised():
    """search_knowledge_base returns an error string if client is None."""
    import langgraph_agent.search_tool as st

    st._search_client = None  # reset
    from langgraph_agent.search_tool import search_knowledge_base

    result = search_knowledge_base.invoke({"query": "test"})
    assert "ERROR" in result


def test_search_tool_formats_results():
    """search_knowledge_base formats chunks into numbered passages."""
    mock_client = MagicMock()
    mock_client.search.return_value = [
        {
            "title": "openai-deployment",
            "content": "Deploy using TPK quota.",
            "source_file": "openai-deployment.txt",
        },
    ]
    init_search_tool(mock_client, top_k=1)

    from langgraph_agent.search_tool import search_knowledge_base

    result = search_knowledge_base.invoke({"query": "deploy Azure OpenAI"})
    assert "[1] openai-deployment" in result
    assert "Deploy using TPK quota." in result


def test_search_tool_returns_no_results_message():
    """search_knowledge_base returns a clear message when index has no hits."""
    mock_client = MagicMock()
    mock_client.search.return_value = []
    init_search_tool(mock_client)

    from langgraph_agent.search_tool import search_knowledge_base

    result = search_knowledge_base.invoke({"query": "something obscure"})
    assert "No relevant documents found" in result


# ---------------------------------------------------------------------------
# LangGraphRagAgent.ask() tests
# ---------------------------------------------------------------------------


def _make_agent_with_mock_graph(graph_output: dict) -> object:
    from langgraph_agent.agent import LangGraphRagAgent

    mock_graph = MagicMock()
    mock_graph.invoke.return_value = graph_output
    return LangGraphRagAgent(graph=mock_graph)


def test_ask_returns_agent_response():
    """ask() wraps graph output in an AgentResponse."""
    ai_msg = AIMessage(content="Azure OpenAI is deployed via the portal.\n[1] openai-deployment")
    agent = _make_agent_with_mock_graph({
        "messages": [ai_msg],
        "citations": ["[1] openai-deployment (source: openai-deployment.txt)"],
    })

    response = agent.ask("How do I deploy Azure OpenAI?")

    assert isinstance(response, AgentResponse)
    assert "Azure OpenAI" in response.content
    assert len(response.citations) == 1


def test_ask_sets_run_id():
    """ask() always populates run_id with a UUID."""
    ai_msg = AIMessage(content="Answer here.")
    agent = _make_agent_with_mock_graph({"messages": [ai_msg], "citations": []})

    response = agent.ask("test question")

    assert response.run_id != ""
    assert len(response.run_id) == 36  # UUID format


def test_ask_with_no_citations():
    """ask() returns empty citations list when graph returns none."""
    ai_msg = AIMessage(content="No relevant info found.")
    agent = _make_agent_with_mock_graph({"messages": [ai_msg], "citations": []})

    response = agent.ask("What is XYZ?")

    assert response.citations == []