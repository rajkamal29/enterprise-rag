"""Azure AI Foundry RAG Agent — Track A.

This module wraps ``azure-ai-agents`` ``AgentsClient`` and wires it to the
Azure AI Search index built during Day 3 ingestion.

Architecture
------------
::

    Caller ──► FoundryRagAgent.ask()
                    │
                    ▼
              AgentsClient (Azure AI Foundry)
                    │  creates thread + run
                    ▼
              GPT-4o  ◄──► AzureAISearchTool
                                 │
                                 ▼
                          rag-chunks index
                          (HNSW + BM25 hybrid)

The agent is stateless across instances but maintains per-instance thread
state so that a single ``FoundryRagAgent`` object holds a conversation.
Call ``reset_conversation()`` to start a new thread.

Key design decisions
---------------------
- ``vector_semantic_hybrid`` query type: best retrieval quality from the
  hybrid index created in Day 3 (BM25 + HNSW + semantic reranker).
- ``top_k=5``: returns top 5 chunks to GPT-4o; tunable.
- Citations are extracted from ``MessageTextAnnotation`` objects returned by
  the agents API — these are grounding references to the retrieved chunks.
- Agent is created once (lazy) and reused across calls to avoid per-call
  creation latency and cost.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Sequence

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import (
    AzureAISearchQueryType,
    AzureAISearchTool,
    MessageRole,
    RunStatus,
    ToolDefinition,
)
from azure.core.credentials import TokenCredential

from config.settings import AzureSettings

logger = logging.getLogger(__name__)

# System prompt: instruct the agent to ground answers in retrieved content
# and always cite its sources.
_SYSTEM_PROMPT = """\
You are an enterprise knowledge assistant. Answer questions using ONLY the
information retrieved from the knowledge base. If the answer is not in the
retrieved documents, say so clearly — do not hallucinate.

Always end your answer with a numbered list of citations in this exact format:
  [1] <document title or source>
  [2] <document title or source>
  ...

If no documents were retrieved, reply: "I could not find relevant information
in the knowledge base for your question."
"""


@dataclass
class Citation:
    """A single grounding reference returned by the agent."""

    text: str
    source: str = ""
    start_index: int = 0
    end_index: int = 0


@dataclass
class AgentResponse:
    """Structured response from the RAG agent.

    Attributes:
        content:    The full answer text (with citation markers replaced).
        citations:  Grounding references extracted from the response.
        run_id:     The AI Foundry run ID for trace lookup in the portal.
        thread_id:  The conversation thread ID.
        raw_text:   The original text before citation marker replacement.
    """

    content: str
    citations: list[Citation] = field(default_factory=list)
    run_id: str = ""
    thread_id: str = ""
    raw_text: str = ""


class FoundryRagAgent:
    """Azure AI Foundry Agent for RAG over the Day 3 search index.

    Parameters
    ----------
    agents_client:
        An authenticated ``AgentsClient`` pointing at your AI Foundry project.
    model:
        Azure OpenAI deployment name (must be deployed in the same Foundry project).
    index_connection_id:
        The Azure AI Foundry connection resource ID or connection name for the
        Azure AI Search service.  Set ``AZURE_AI_SEARCH_CONNECTION_ID`` in .env.
    index_name:
        Name of the AI Search index to query.  Default: ``rag-chunks``.
    top_k:
        Number of search results to return to GPT-4o.  Default: 5.
    """

    def __init__(
        self,
        agents_client: AgentsClient,
        model: str = "gpt-4o",
        index_connection_id: str = "",
        index_name: str = "rag-chunks",
        top_k: int = 5,
    ) -> None:
        self._client = agents_client
        self._model = model
        self._index_connection_id = index_connection_id
        self._index_name = index_name
        self._top_k = top_k

        # Lazily created — set on first call to ask().
        self._agent_id: str | None = None
        self._thread_id: str | None = None

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_settings(
        cls,
        settings: AzureSettings,
        credential: TokenCredential,
    ) -> "FoundryRagAgent":
        """Construct a ``FoundryRagAgent`` from ``AzureSettings``.

        Builds the ``AgentsClient`` endpoint from the AI Foundry project
        connection string (same format used by ``AzureClientFactory``).

        Args:
            settings:   Populated ``AzureSettings`` instance.
            credential: Authenticated credential (e.g. ``DefaultAzureCredential``).

        Raises:
            RuntimeError: If required settings are missing.
        """
        if not settings.foundry_is_configured:
            raise RuntimeError(
                "AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING is not set. "
                "Run infra/deploy.ps1 and source the .env file."
            )
        if not settings.azure_ai_search_connection_id:
            raise RuntimeError(
                "AZURE_AI_SEARCH_CONNECTION_ID is not set. "
                "Create the AI Search connection in AI Foundry portal → "
                "Project Settings → Connections, then set the connection name "
                "in your .env file."
            )

        conn_parts = settings.azure_ai_foundry_project_connection_string.split(";")
        if len(conn_parts) != 4:
            raise ValueError(
                "AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING has invalid format. "
                "Expected '<region>.api.azureml.ms;<subscription>;<rg>;<project>'."
            )
        host, _, _, project_name = conn_parts
        endpoint = f"https://{host}/api/projects/{project_name}"

        agents_client = AgentsClient(endpoint=endpoint, credential=credential)
        return cls(
            agents_client=agents_client,
            model=settings.azure_openai_chat_deployment,
            index_connection_id=settings.azure_ai_search_connection_id,
            index_name=settings.azure_search_index_name,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def ask(self, question: str) -> AgentResponse:
        """Send a question to the agent and return a grounded answer.

        On the first call the agent and a conversation thread are created.
        Subsequent calls continue the same thread (multi-turn conversation).
        Call ``reset_conversation()`` to start a fresh thread.

        Args:
            question: The user's question.

        Returns:
            ``AgentResponse`` with content, citations, run_id, and thread_id.
        """
        self._ensure_agent()
        self._ensure_thread()
        if self._agent_id is None:
            raise RuntimeError("Agent could not be created.")
        if self._thread_id is None:
            raise RuntimeError("Thread could not be created.")

        logger.info("Sending question to agent [thread=%s]: %s", self._thread_id, question)

        # Add the user message to the thread.
        self._client.messages.create(
            thread_id=self._thread_id,
            role=MessageRole.USER,
            content=question,
        )

        # Create a run and wait for it to complete.
        run = self._client.runs.create_and_process(
            thread_id=self._thread_id,
            agent_id=self._agent_id,
        )

        logger.info(
            "Run completed [run_id=%s, status=%s]", run.id, run.status
        )

        if run.status != RunStatus.COMPLETED:
            error_msg = getattr(run, "last_error", None)
            raise RuntimeError(
                f"Agent run did not complete successfully. "
                f"Status: {run.status}. Error: {error_msg}"
            )

        return self._extract_response(run.id, self._thread_id)

    def reset_conversation(self) -> None:
        """Discard the current thread and start a new conversation.

        The agent itself is retained — only the thread (message history)
        is discarded.
        """
        if self._thread_id:
            try:
                self._client.threads.delete(self._thread_id)
                logger.info("Deleted thread %s", self._thread_id)
            except Exception as exc:
                logger.warning("Could not delete thread %s: %s", self._thread_id, exc)
        self._thread_id = None
        logger.info("Conversation reset — next ask() will create a new thread")

    def close(self) -> None:
        """Delete the managed agent and release the client."""
        if self._agent_id:
            try:
                self._client.delete_agent(self._agent_id)
                logger.info("Deleted agent %s", self._agent_id)
            except Exception as exc:
                logger.warning("Could not delete agent %s: %s", self._agent_id, exc)
            self._agent_id = None
        self._client.close()

    def __enter__(self) -> "FoundryRagAgent":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _ensure_agent(self) -> None:
        """Create the AI Foundry agent if it doesn't exist yet."""
        if self._agent_id:
            return

        search_tool = AzureAISearchTool(
            index_connection_id=self._index_connection_id,
            index_name=self._index_name,
            query_type=AzureAISearchQueryType.VECTOR_SEMANTIC_HYBRID,
            top_k=self._top_k,
        )

        tools: Sequence[ToolDefinition] = search_tool.definitions
        tool_resources = search_tool.resources

        agent = self._client.create_agent(
            model=self._model,
            name="enterprise-rag-agent",
            instructions=_SYSTEM_PROMPT,
            tools=tools,
            tool_resources=tool_resources,
        )
        self._agent_id = agent.id
        logger.info("Created agent [id=%s, model=%s]", agent.id, self._model)

    def _ensure_thread(self) -> None:
        """Create a conversation thread if one doesn't exist yet."""
        if self._thread_id:
            return
        thread = self._client.threads.create()
        self._thread_id = thread.id
        logger.info("Created thread [id=%s]", thread.id)

    def _extract_response(self, run_id: str, thread_id: str) -> AgentResponse:
        """Extract the last assistant message and its citations from the thread."""
        messages = self._client.messages.list(thread_id=thread_id)

        # Messages are ordered newest-first; take the first assistant message.
        for msg in messages:
            if msg.role == MessageRole.AGENT:
                raw_text = ""
                citations: list[Citation] = []

                for content_block in msg.content:
                    # Text content block
                    if hasattr(content_block, "text"):
                        text_val = content_block.text
                        raw_text += text_val.value if hasattr(text_val, "value") else str(text_val)

                        # Extract annotations (grounding citations)
                        annotations = getattr(text_val, "annotations", []) or []
                        for ann in annotations:
                            source = ""
                            if hasattr(ann, "file_citation"):
                                source = getattr(ann.file_citation, "file_id", "")
                            elif hasattr(ann, "url_citation"):
                                source = getattr(ann.url_citation, "url", "")
                            citations.append(
                                Citation(
                                    text=getattr(ann, "text", ""),
                                    source=source,
                                    start_index=getattr(ann, "start_index", 0),
                                    end_index=getattr(ann, "end_index", 0),
                                )
                            )

                # Clean up citation marker placeholders in the displayed text
                clean_text = re.sub(r"【\d+:\d+†[^】]*】", "", raw_text).strip()

                logger.info(
                    "Response extracted [run=%s, citations=%d, length=%d chars]",
                    run_id,
                    len(citations),
                    len(clean_text),
                )
                return AgentResponse(
                    content=clean_text,
                    citations=citations,
                    run_id=run_id,
                    thread_id=thread_id,
                    raw_text=raw_text,
                )

        # Should not reach here if run completed successfully.
        logger.warning("No assistant message found after run %s", run_id)
        return AgentResponse(
            content="No response generated.",
            run_id=run_id,
            thread_id=thread_id,
        )
