"""Tests for the multi-agent planner — Day 8.

Strategy: inject fake LLM and fake search client so no Azure calls are made.
Tests cover:
- planner_node produces tasks from LLM output
- retrieval_node accumulates context and increments index
- summarisation_node calls LLM with context
- citation_node produces final_answer with citations
- _retrieve_router routes correctly
- build_planner_graph returns a runnable graph
- PlannerAgent.ask() returns expected keys via end-to-end mock run
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from multi_agent.planner import (
    PlannerAgent,
    _retrieve_router,
    build_planner_graph,
    make_planner_node,
)
from multi_agent.specialists import (
    make_citation_node,
    make_retrieval_node,
    make_summarisation_node,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_llm(response_text: str) -> MagicMock:
    """Return a mock LLM whose invoke() always returns *response_text*."""
    llm = MagicMock()
    msg = MagicMock()
    msg.content = response_text
    llm.invoke.return_value = msg
    return llm


def _make_search_client(chunks: list[dict[str, Any]]) -> MagicMock:
    """Return a mock SearchClient whose search() always returns *chunks*."""
    client = MagicMock()
    client.search.return_value = iter(chunks)
    return client


def _empty_state(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "question": "How do I deploy Azure OpenAI?",
        "tasks": [],
        "current_task_index": 0,
        "completed_tasks": [],
        "retrieved_context": "",
        "summary": "",
        "final_answer": "",
        "citations": [],
        "request_id": "test-req-1",
    }
    base.update(overrides)
    return base


# ── planner_node ──────────────────────────────────────────────────────────────


def test_planner_node_sets_tasks() -> None:
    llm = _make_llm("deploy Azure OpenAI endpoint\nOpenAI REST API authentication\n")
    node = make_planner_node(llm)
    result = node(_empty_state())
    assert len(result["tasks"]) == 2
    assert result["current_task_index"] == 0


def test_planner_node_caps_at_three_tasks() -> None:
    llm = _make_llm("query1\nquery2\nquery3\nquery4\nquery5\n")
    node = make_planner_node(llm)
    result = node(_empty_state())
    assert len(result["tasks"]) <= 3


def test_planner_node_fallback_when_empty_response() -> None:
    llm = _make_llm("   ")  # blank response
    node = make_planner_node(llm)
    result = node(_empty_state())
    # Should fall back to the original question as a single task.
    assert result["tasks"] == ["How do I deploy Azure OpenAI?"]


# ── retrieval_node ────────────────────────────────────────────────────────────


def test_retrieval_node_accumulates_context() -> None:
    chunks = [
        {
            "document_title": "Azure Docs",
            "chunk_text": "Deploy via portal.",
            "source_document": "az.pdf",
        },
    ]
    client = _make_search_client(chunks)
    node = make_retrieval_node(client)
    state = _empty_state(tasks=["deploy OpenAI"], current_task_index=0)
    result = node(state)
    assert "Azure Docs" in result["retrieved_context"]
    assert "Deploy via portal." in result["retrieved_context"]
    assert result["current_task_index"] == 1
    assert "Azure Docs" in result["citations"]
    assert "deploy OpenAI" in result["completed_tasks"]


def test_retrieval_node_deduplicates_citations() -> None:
    chunks = [
        {"document_title": "Azure Docs", "chunk_text": "chunk1", "source_document": "az.pdf"},
        {"document_title": "Azure Docs", "chunk_text": "chunk2", "source_document": "az.pdf"},
    ]
    client = _make_search_client(chunks)
    node = make_retrieval_node(client)
    state = _empty_state(tasks=["query1"], current_task_index=0)
    result = node(state)
    assert result["citations"].count("Azure Docs") == 1


def test_retrieval_node_fallback_field_names() -> None:
    """Node should work with both 'title'/'content' and 'document_title'/'chunk_text'."""
    chunks = [{"title": "Other Docs", "content": "some text"}]
    client = _make_search_client(chunks)
    node = make_retrieval_node(client)
    state = _empty_state(tasks=["query"], current_task_index=0)
    result = node(state)
    assert "Other Docs" in result["citations"]


# ── summarisation_node ────────────────────────────────────────────────────────


def test_summarisation_node_returns_summary() -> None:
    llm = _make_llm("Summary: deploy using REST API.")
    node = make_summarisation_node(llm)
    state = _empty_state(retrieved_context="[Azure Docs]\nDeploy via portal.")
    result = node(state)
    assert result["summary"] == "Summary: deploy using REST API."
    llm.invoke.assert_called_once()


# ── citation_node ─────────────────────────────────────────────────────────────


def test_citation_node_returns_final_answer() -> None:
    llm = _make_llm("You can deploy Azure OpenAI via the portal.\n\n[1] Azure Docs")
    node = make_citation_node(llm)
    state = _empty_state(
        summary="Deploy via portal.",
        citations=["Azure Docs"],
    )
    result = node(state)
    assert result["final_answer"] == "You can deploy Azure OpenAI via the portal.\n\n[1] Azure Docs"
    llm.invoke.assert_called_once()


# ── _retrieve_router ──────────────────────────────────────────────────────────


def test_router_returns_retrieve_when_tasks_remain() -> None:
    state = _empty_state(tasks=["q1", "q2"], current_task_index=1)
    assert _retrieve_router(state) == "retrieve"


def test_router_returns_summarise_when_all_done() -> None:
    state = _empty_state(tasks=["q1", "q2"], current_task_index=2)
    assert _retrieve_router(state) == "summarise"


def test_router_returns_summarise_on_empty_tasks() -> None:
    state = _empty_state(tasks=[], current_task_index=0)
    assert _retrieve_router(state) == "summarise"


# ── build_planner_graph (integration with mocks) ──────────────────────────────


def _make_sequential_llm(responses: list[str]) -> MagicMock:
    """LLM whose invoke() returns responses in sequence."""
    llm = MagicMock()
    msgs = [MagicMock(content=r) for r in responses]
    llm.invoke.side_effect = msgs
    return llm


def test_build_planner_graph_returns_runnable() -> None:
    llm = _make_llm("query1")
    client = _make_search_client([])
    graph = build_planner_graph(llm, client)
    assert hasattr(graph, "invoke")


def test_planner_agent_ask_returns_expected_keys() -> None:
    # 1 call: planner (→ 1 task), 1 call: summarise, 1 call: cite
    llm = _make_sequential_llm([
        "Azure OpenAI deployment steps",    # planner
        "Summary of Azure deployment.",     # summarise
        "Deploy via portal.\n\n[1] Docs",   # cite
    ])
    chunks = [
        {
            "document_title": "Docs",
            "chunk_text": "Deploy via portal.",
            "source_document": "d.pdf",
        }
    ]
    client = _make_search_client(chunks)
    # reset search mock to return same chunks each call
    client.search.return_value = iter(chunks)

    graph = build_planner_graph(llm, client)
    agent = PlannerAgent(graph)
    result = agent.ask("How do I deploy Azure OpenAI?")

    assert "final_answer" in result
    assert "citations" in result
    assert "tasks" in result
    assert "request_id" in result
    assert isinstance(result["final_answer"], str)
    assert len(result["final_answer"]) > 0
