"""Multi-agent planner for Enterprise Agentic RAG — Day 8.

Architecture
------------
::

    Caller ──► PlannerAgent.ask()
                    │
                    ▼
             ┌─── StateGraph ───────────────────────────────────┐
             │                                                   │
             │  [plan] ──► [retrieve] ──► (loop N tasks)        │
             │                  │                               │
             │                  └──► [summarise] ──► [cite] ──► END
             │                                                   │
             └───────────────────────────────────────────────────┘

Nodes
-----
plan        LLM decomposes the user question into 2-3 retrieval sub-queries.
retrieve    Azure AI Search runs the current sub-query.  Loops until all
            sub-queries are exhausted.
summarise   LLM condenses all retrieved context into a focused summary.
cite        LLM writes the final answer from the summary + source list.

Routing
-------
After ``plan``: always go to ``retrieve``.
After ``retrieve``:
  - ``current_task_index < len(tasks)`` → ``retrieve`` (more sub-queries)
  - otherwise → ``summarise``
After ``summarise``: direct edge to ``cite``.
After ``cite``: END.

Comparison vs single ReAct agent
----------------------------------
| Dimension    | Single ReAct (Track B)       | Planner + Specialists (Day 8)         |
|---|---|---|
| Control flow | Implicit (LLM decides)        | Explicit (graph routing)              |
| Visibility   | Hard to inspect mid-run       | Each node's output is observable      |
| Cost         | Fewer LLM calls for simple Qs | More calls — justified for complex Qs |
| Testability  | Mock graph only               | Each node testable in isolation       |
| Best for     | Single-hop factual questions  | Multi-hop, multi-source questions     |
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)

# Max tasks the planner may produce (guards against LLM over-splitting).
_MAX_TASKS = 3


def make_planner_node(llm: Any) -> Any:
    """Return a planner node bound to *llm*.

    Decomposes the user question into up to ``_MAX_TASKS`` specific search
    queries and seeds the task list in the shared state.
    """

    def planner_node(state: dict[str, Any]) -> dict[str, Any]:
        from langchain_core.messages import HumanMessage

        question: str = state.get("question", "")
        logger.info("[plan] decomposing question: %s", question[:120])

        prompt = (
            f"You are a query planning assistant.\n\n"
            f"Break the following question into {_MAX_TASKS} or fewer specific "
            f"search queries. Each query should target a different aspect of the "
            f"question so that together they provide enough information to answer it.\n\n"
            f"Question: {question}\n\n"
            f"Rules:\n"
            f"- One query per line.\n"
            f"- No numbering, bullets, or extra text.\n"
            f"- Keep each query short and focused.\n"
        )

        response = llm.invoke([HumanMessage(content=prompt)])
        raw: str = getattr(response, "content", "") or ""
        tasks = [line.strip() for line in raw.splitlines() if line.strip()]
        tasks = tasks[:_MAX_TASKS]
        if not tasks:
            tasks = [question]

        logger.info("[plan] decomposed into %d tasks: %s", len(tasks), tasks)
        return {"tasks": tasks, "current_task_index": 0}

    return planner_node


def _retrieve_router(state: dict[str, Any]) -> str:
    """Route after a retrieval step: loop if more tasks, else summarise."""
    if state.get("current_task_index", 0) < len(state.get("tasks", [])):
        return "retrieve"
    return "summarise"


def build_planner_graph(llm: Any, search_client: Any) -> Any:
    """Build and compile the planner + specialists graph.

    Args:
        llm:           LangChain-compatible chat model (e.g. AzureChatOpenAI).
        search_client: Azure AI Search ``SearchClient`` (or any object with a
                       ``.search(query, top=N)`` method for testing).

    Returns:
        A compiled LangGraph runnable.
    """
    from langgraph.graph import END, StateGraph

    from multi_agent.specialists import (
        make_citation_node,
        make_retrieval_node,
        make_summarisation_node,
    )
    from multi_agent.state import PlannerState

    graph: Any = StateGraph(PlannerState)

    graph.add_node("plan", make_planner_node(llm))
    graph.add_node("retrieve", make_retrieval_node(search_client))
    graph.add_node("summarise", make_summarisation_node(llm))
    graph.add_node("cite", make_citation_node(llm))

    graph.set_entry_point("plan")
    graph.add_edge("plan", "retrieve")
    graph.add_conditional_edges(
        "retrieve",
        _retrieve_router,
        {"retrieve": "retrieve", "summarise": "summarise"},
    )
    graph.add_edge("summarise", "cite")
    graph.add_edge("cite", END)

    return graph.compile()


class PlannerAgent:
    """High-level facade over the planner graph.

    Mirrors the ``LangGraphRagAgent.ask()`` interface so the same evaluation
    harness works on all three: Track A (Foundry), Track B (ReAct), and
    the Day 8 planner.
    """

    def __init__(self, graph: Any) -> None:
        self._graph = graph

    @classmethod
    def from_settings(cls, settings: Any, credential: Any) -> "PlannerAgent":
        """Build a ``PlannerAgent`` from ``AzureSettings`` and a credential."""
        from azure.identity import get_bearer_token_provider
        from azure.search.documents import SearchClient
        from langchain_openai import AzureChatOpenAI

        _OPENAI_SCOPE = "https://cognitiveservices.azure.com/.default"
        token_provider = get_bearer_token_provider(credential, _OPENAI_SCOPE)

        llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            azure_deployment=settings.azure_openai_chat_deployment,
            api_version=settings.azure_openai_api_version,
            azure_ad_token_provider=token_provider,
            temperature=0,
        )

        search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.azure_search_index_name,
            credential=credential,
        )

        graph = build_planner_graph(llm, search_client)
        return cls(graph)

    def ask(self, question: str) -> dict[str, Any]:
        """Run the planner graph and return the full state.

        Returns a dict with at minimum:
            ``final_answer`` — the LLM-written answer with citations.
            ``citations``    — list of source titles found.
            ``tasks``        — the sub-queries the planner produced.
            ``request_id``   — trace ID for this invocation.
        """
        request_id = str(uuid.uuid4())
        initial: dict[str, Any] = {
            "question": question,
            "tasks": [],
            "current_task_index": 0,
            "completed_tasks": [],
            "retrieved_context": "",
            "summary": "",
            "final_answer": "",
            "citations": [],
            "request_id": request_id,
        }
        result: dict[str, Any] = self._graph.invoke(initial)
        result["request_id"] = request_id
        logger.info(
            "PlannerAgent run complete [request_id=%s, tasks=%d, citations=%d]",
            request_id,
            len(result.get("tasks", [])),
            len(result.get("citations", [])),
        )
        return result
