"""Azure AI Search retrieval tool for the LangGraph ReAct agent."""

from __future__ import annotations

import logging

from azure.search.documents import SearchClient
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Module-level client — injected once at agent startup via init_search_tool()
_search_client: SearchClient | None = None
_top_k: int = 5


def init_search_tool(client: SearchClient, top_k: int = 5) -> None:
    """Inject the SearchClient before the graph is compiled.

    Args:
        client: Authenticated SearchClient pointing at rag-index.
        top_k:  Number of chunks to return per query.
    """
    global _search_client, _top_k
    _search_client = client
    _top_k = top_k


@tool
def search_knowledge_base(query: str) -> str:
    """Search the enterprise knowledge base and return relevant passages.

    Use this tool whenever you need information to answer a question.
    Always call this before answering — do not rely on prior knowledge.

    Args:
        query: Natural language search query.

    Returns:
        Formatted text of top matching passages with source references.
    """
    if _search_client is None:
        return "ERROR: Search client not initialised. Call init_search_tool() first."

    try:
        results = list(
            _search_client.search(
                search_text=query,
                top=_top_k,
            )
        )
    except Exception as exc:
        logger.error("Search failed: %s", exc)
        return f"ERROR: Search failed — {exc}"

    if not results:
        return "No relevant documents found for this query."

    parts: list[str] = []
    for i, r in enumerate(results, 1):
        title = r.get("document_title") or r.get("title") or "unknown"
        source = r.get("source_document") or r.get("source_file") or "unknown"
        content = (r.get("chunk_text") or r.get("content") or "")[:600]
        parts.append(f"[{i}] {title} (source: {source})\n{content}")

    return "\n\n---\n\n".join(parts)