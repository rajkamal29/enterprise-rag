"""LangGraphRagAgent — Track B facade matching the FoundryRagAgent interface."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from azure.core.credentials import TokenCredential
from azure.identity import get_bearer_token_provider
from azure.search.documents import SearchClient
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI

from config.settings import AzureSettings
from foundry.rag_agent import AgentResponse, Citation
from langgraph_agent.react_agent import build_graph
from langgraph_agent.search_tool import init_search_tool
from observability.tracing import get_tracer

logger = logging.getLogger(__name__)
_tracer = get_tracer("langgraph_agent.agent")

_OPENAI_SCOPE = "https://cognitiveservices.azure.com/.default"


class LangGraphRagAgent:
    """ReAct RAG agent built on LangGraph (Track B).

    Mirrors the ``FoundryRagAgent`` interface so the same evaluation
    code works on both tracks without modification.
    """

    def __init__(
        self,
        graph: Any,
        *,
        model: str = "gpt-4o",
    ) -> None:
        self._graph = graph
        self._model = model

    @classmethod
    def from_settings(
        cls,
        settings: AzureSettings,
        credential: TokenCredential,
    ) -> "LangGraphRagAgent":
        """Build a LangGraphRagAgent from AzureSettings.

        Args:
            settings:   Populated AzureSettings instance.
            credential: Authenticated credential (DefaultAzureCredential).
        """
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
        init_search_tool(search_client, top_k=5)

        graph = build_graph(llm)
        return cls(graph, model=settings.azure_openai_chat_deployment)

    def ask(self, question: str) -> AgentResponse:
        """Send a question through the ReAct graph and return a structured response.

        Args:
            question: Natural language question to answer.

        Returns:
            AgentResponse with content, citations, and a request_id trace ID.
        """
        with _tracer.start_as_current_span("rag.ask") as span:
            span.set_attribute("rag.track", "langgraph")
            span.set_attribute("rag.question_length", len(question))

            request_id = str(uuid.uuid4())
            initial_state = {
                "messages": [HumanMessage(content=question)],
                "citations": [],
                "request_id": request_id,
                "tool_call_ids": [],
            }

            with _tracer.start_as_current_span("rag.generate") as gen_span:
                gen_span.set_attribute("rag.track", "langgraph")
                gen_span.set_attribute("rag.model", self._model)
                result = self._graph.invoke(initial_state)

            last_message = result["messages"][-1]
            content: str = getattr(last_message, "content", "") or ""

            citations = [
                Citation(text=c, source=c) for c in result.get("citations", [])
            ]

            logger.info(
                "LangGraph run complete [request_id=%s, citations=%d]",
                request_id,
                len(citations),
            )

            span.set_attribute("rag.run_id", request_id)
            span.set_attribute("rag.citation_count", len(citations))

            return AgentResponse(
                content=content,
                citations=citations,
                run_id=request_id,
                thread_id="",
                raw_text=content,
            )