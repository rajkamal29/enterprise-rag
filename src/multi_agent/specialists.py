"""Specialist agent nodes for the multi-agent planner graph.

Each specialist is a factory function that closes over its dependencies
(LLM or search client) and returns a plain callable that LangGraph can
register as a node.

Nodes
-----
make_retrieval_node(search_client)
    Runs Azure AI Search for the current task query and appends retrieved
    text and source titles to the shared state.

make_summarisation_node(llm)
    Calls the LLM to summarise all accumulated retrieved context into a
    focused answer skeleton for the citation node.

make_citation_node(llm)
    Calls the LLM to produce a final, citied answer from the summary and
    the collected source list.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Maximum characters of retrieved context passed to the summarisation LLM.
_CONTEXT_WINDOW = 4000


def make_retrieval_node(search_client: Any) -> Any:
    """Return a retrieval node bound to *search_client*.

    The node picks the current task query from ``state["tasks"]`` at index
    ``state["current_task_index"]``, searches Azure AI Search, and appends
    the chunk text and source titles to the shared state.
    """

    def retrieval_node(state: dict[str, Any]) -> dict[str, Any]:
        tasks: list[str] = state.get("tasks", [])
        idx: int = state.get("current_task_index", 0)
        query = tasks[idx] if idx < len(tasks) else state.get("question", "")

        logger.info(
            "[retrieval] task %d/%d: %s",
            idx + 1,
            len(tasks),
            query[:80],
        )

        results = list(search_client.search(query, top=5))

        context_pieces: list[str] = []
        new_citations: list[str] = list(state.get("citations", []))

        for r in results:
            title: str = (
                r.get("document_title") or r.get("title") or "unknown"
            )
            text: str = r.get("chunk_text") or r.get("content") or ""
            context_pieces.append(f"[{title}]\n{text}")
            if title not in new_citations:
                new_citations.append(title)

        existing_context: str = state.get("retrieved_context", "")
        separator = "\n\n" if existing_context else ""
        new_context = existing_context + separator + "\n\n".join(context_pieces)

        completed = list(state.get("completed_tasks", []))
        completed.append(query)

        logger.info(
            "[retrieval] got %d chunks, %d unique sources so far",
            len(results),
            len(new_citations),
        )

        return {
            "retrieved_context": new_context,
            "current_task_index": idx + 1,
            "citations": new_citations,
            "completed_tasks": completed,
        }

    return retrieval_node


def make_summarisation_node(llm: Any) -> Any:
    """Return a summarisation node bound to *llm*.

    Condenses all retrieved context into a focused summary that the
    citation node can use to write the final answer.
    """

    def summarisation_node(state: dict[str, Any]) -> dict[str, Any]:
        from langchain_core.messages import HumanMessage

        question: str = state.get("question", "")
        context: str = state.get("retrieved_context", "")[:_CONTEXT_WINDOW]

        prompt = (
            f"You are a summarisation assistant.\n\n"
            f"Question: {question}\n\n"
            f"Retrieved context:\n{context}\n\n"
            f"Write a concise summary that captures all the facts needed "
            f"to answer the question. Do not answer yet — only summarise."
        )

        logger.info("[summarise] condensing %d chars of context", len(context))
        response = llm.invoke([HumanMessage(content=prompt)])
        summary: str = getattr(response, "content", "") or ""

        logger.info("[summarise] summary length: %d chars", len(summary))
        return {"summary": summary}

    return summarisation_node


def make_citation_node(llm: Any) -> Any:
    """Return a citation node bound to *llm*.

    Produces the final answer from the summary and formats citations.
    """

    def citation_node(state: dict[str, Any]) -> dict[str, Any]:
        from langchain_core.messages import HumanMessage

        question: str = state.get("question", "")
        summary: str = state.get("summary", "")
        citations: list[str] = state.get("citations", [])

        citations_text = "\n".join(
            f"[{i + 1}] {c}" for i, c in enumerate(citations)
        )

        prompt = (
            f"You are an enterprise knowledge assistant.\n\n"
            f"Question: {question}\n\n"
            f"Summary of retrieved information:\n{summary}\n\n"
            f"Using ONLY the information in the summary, write a clear and "
            f"concise answer.\n\n"
            f"End your answer with this exact citation list:\n{citations_text}"
        )

        logger.info("[cite] generating final answer with %d citations", len(citations))
        response = llm.invoke([HumanMessage(content=prompt)])
        final_answer: str = getattr(response, "content", "") or ""

        logger.info("[cite] final answer length: %d chars", len(final_answer))
        return {"final_answer": final_answer}

    return citation_node
