"""Unit tests for the Azure AI Foundry RAG agent (Track A).

All Azure SDK calls are mocked — these tests run fully offline with no
Azure credentials required.

Test coverage
-------------
- ``FoundryRagAgent.from_settings()`` — config validation
- ``FoundryRagAgent.ask()`` — happy path, run failure path
- ``FoundryRagAgent.reset_conversation()`` — thread lifecycle
- ``FoundryRagAgent._extract_response()`` — citation parsing
- ``evaluate_response()`` — has_citation, relevance heuristic
"""

from __future__ import annotations

from typing import Any  # noqa: F401
from unittest.mock import MagicMock, patch

import pytest

from foundry.evaluation import (
    answer_relevance_heuristic,
    evaluate_response,
    has_citation,
)
from foundry.rag_agent import AgentResponse, Citation, FoundryRagAgent

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_agent(
    index_connection_id: str = "test-connection",
    index_name: str = "rag-chunks",
) -> tuple[FoundryRagAgent, MagicMock]:
    """Return a FoundryRagAgent with a mocked AgentsClient."""
    mock_client = MagicMock()
    agent = FoundryRagAgent(
        agents_client=mock_client,
        model="gpt-4o",
        index_connection_id=index_connection_id,
        index_name=index_name,
        top_k=5,
    )
    return agent, mock_client


def _make_message(content_text: str, annotations: list[Any] | None = None) -> MagicMock:
    """Build a mock assistant message with text content."""
    from azure.ai.agents.models import MessageRole

    ann_list = annotations or []

    text_val = MagicMock()
    text_val.value = content_text
    text_val.annotations = ann_list

    content_block = MagicMock()
    content_block.text = text_val
    # Make sure hasattr(content_block, "text") is True
    del content_block.image_file  # remove image_file attr so only text is present

    msg = MagicMock()
    msg.role = MessageRole.AGENT
    msg.content = [content_block]
    return msg


# ── from_settings tests ───────────────────────────────────────────────────────


class TestFoundryRagAgentFromSettings:
    def test_raises_when_foundry_not_configured(self) -> None:
        from config.settings import AzureSettings

        settings = AzureSettings(
            azure_ai_foundry_project_connection_string="",
            azure_ai_search_connection_id="conn",
        )
        credential = MagicMock()
        with pytest.raises(RuntimeError, match="AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING"):
            FoundryRagAgent.from_settings(settings, credential)

    def test_raises_when_search_connection_not_configured(self) -> None:
        from config.settings import AzureSettings

        settings = AzureSettings(
            azure_ai_foundry_project_connection_string=(
                "eastus.api.azureml.ms;sub-123;rg-dev;proj-dev"
            ),
            azure_ai_search_connection_id="",
        )
        credential = MagicMock()
        with pytest.raises(RuntimeError, match="AZURE_AI_SEARCH_CONNECTION_ID"):
            FoundryRagAgent.from_settings(settings, credential)

    def test_raises_on_malformed_connection_string(self) -> None:
        from config.settings import AzureSettings

        settings = AzureSettings(
            azure_ai_foundry_project_connection_string="only-two;parts",
            azure_ai_search_connection_id="conn",
        )
        credential = MagicMock()
        with pytest.raises(ValueError, match="invalid format"):
            FoundryRagAgent.from_settings(settings, credential)

    def test_builds_client_with_correct_endpoint(self) -> None:
        from config.settings import AzureSettings

        settings = AzureSettings(
            azure_ai_foundry_project_connection_string=(
                "eastus.api.azureml.ms;sub-123;rg-dev;proj-erag2-dev"
            ),
            azure_ai_search_connection_id="srch-connection",
            azure_openai_chat_deployment="gpt-4o",
            azure_search_index_name="rag-chunks",
        )
        credential = MagicMock()
        with patch("foundry.rag_agent.AgentsClient") as mock_cls:
            mock_cls.return_value = MagicMock()
            agent = FoundryRagAgent.from_settings(settings, credential)

        mock_cls.assert_called_once_with(
            endpoint="https://eastus.api.azureml.ms/api/projects/proj-erag2-dev",
            credential=credential,
        )
        assert agent._model == "gpt-4o"
        assert agent._index_name == "rag-chunks"
        assert agent._index_connection_id == "srch-connection"


# ── ask() tests ───────────────────────────────────────────────────────────────


class TestFoundryRagAgentAsk:
    def test_creates_agent_and_thread_on_first_ask(self) -> None:
        from azure.ai.agents.models import RunStatus

        agent, client = _make_agent()

        # Mock agent creation
        mock_ai_agent = MagicMock()
        mock_ai_agent.id = "agent-001"
        client.create_agent.return_value = mock_ai_agent

        # Mock thread creation
        mock_thread = MagicMock()
        mock_thread.id = "thread-001"
        client.threads.create.return_value = mock_thread

        # Mock run
        mock_run = MagicMock()
        mock_run.id = "run-001"
        mock_run.status = RunStatus.COMPLETED
        client.runs.create_and_process.return_value = mock_run

        # Mock message list
        client.messages.list.return_value = [_make_message("Test answer. [1] Source")]

        response = agent.ask("What is Azure AI Foundry?")

        client.create_agent.assert_called_once()
        client.threads.create.assert_called_once()
        client.messages.create.assert_called_once()
        assert "Test answer" in response.content
        assert response.run_id == "run-001"
        assert response.thread_id == "thread-001"

    def test_reuses_thread_on_second_ask(self) -> None:
        from azure.ai.agents.models import RunStatus

        agent, client = _make_agent()
        agent._agent_id = "agent-001"
        agent._thread_id = "thread-001"

        mock_run = MagicMock()
        mock_run.id = "run-002"
        mock_run.status = RunStatus.COMPLETED
        client.runs.create_and_process.return_value = mock_run
        client.messages.list.return_value = [_make_message("Second answer.")]

        agent.ask("Follow-up question?")

        # Thread should NOT be re-created
        client.threads.create.assert_not_called()

    def test_raises_on_failed_run(self) -> None:
        from azure.ai.agents.models import RunStatus

        agent, client = _make_agent()
        agent._agent_id = "agent-001"
        agent._thread_id = "thread-001"

        mock_run = MagicMock()
        mock_run.id = "run-fail"
        mock_run.status = RunStatus.FAILED
        mock_run.last_error = "Rate limit exceeded"
        client.runs.create_and_process.return_value = mock_run

        with pytest.raises(RuntimeError, match="did not complete"):
            agent.ask("This will fail")

    def test_citation_markers_stripped_from_content(self) -> None:
        from azure.ai.agents.models import RunStatus

        agent, client = _make_agent()
        agent._agent_id = "agent-001"
        agent._thread_id = "thread-001"

        mock_run = MagicMock()
        mock_run.id = "run-003"
        mock_run.status = RunStatus.COMPLETED
        client.runs.create_and_process.return_value = mock_run

        raw = "Azure AI Foundry【3:0†source】 is a managed platform."
        client.messages.list.return_value = [_make_message(raw)]

        response = agent.ask("What is Foundry?")
        assert "【" not in response.content
        assert "Azure AI Foundry" in response.content
        assert response.raw_text == raw


# ── reset_conversation() tests ────────────────────────────────────────────────


class TestFoundryRagAgentReset:
    def test_reset_deletes_thread_and_clears_id(self) -> None:
        agent, client = _make_agent()
        agent._thread_id = "thread-to-delete"

        agent.reset_conversation()

        client.threads.delete.assert_called_once_with("thread-to-delete")
        assert agent._thread_id is None

    def test_reset_with_no_thread_does_not_fail(self) -> None:
        agent, client = _make_agent()
        agent._thread_id = None
        agent.reset_conversation()  # should not raise

    def test_close_deletes_agent(self) -> None:
        agent, client = _make_agent()
        agent._agent_id = "agent-to-delete"

        agent.close()

        client.delete_agent.assert_called_once_with("agent-to-delete")
        assert agent._agent_id is None


# ── evaluation tests ──────────────────────────────────────────────────────────


class TestEvaluation:
    def _response(
        self,
        content: str,
        citations: list[Citation] | None = None,
    ) -> AgentResponse:
        return AgentResponse(content=content, citations=citations or [])

    def test_has_citation_with_structured_citations(self) -> None:
        r = self._response("Some answer.", [Citation(text="ref", source="doc1")])
        assert has_citation(r) is True

    def test_has_citation_with_inline_marker(self) -> None:
        r = self._response("The answer is here [1] according to the docs.")
        assert has_citation(r) is True

    def test_has_citation_false_when_empty(self) -> None:
        r = self._response("I don't know the answer.")
        assert has_citation(r) is False

    def test_relevance_score_high_when_keywords_present(self) -> None:
        r = self._response("Azure AI Foundry is a managed platform for AI workflows.")
        score = answer_relevance_heuristic("What is Azure AI Foundry?", r)
        assert score >= 0.5

    def test_relevance_score_low_when_off_topic(self) -> None:
        r = self._response("The weather today is sunny and warm.")
        score = answer_relevance_heuristic("What is Azure AI Foundry?", r)
        assert score < 0.4

    def test_evaluate_response_warns_on_no_citation(self) -> None:
        r = self._response("Some answer with no citation.")
        result = evaluate_response("What is X?", r)
        assert result["has_citation"] is False
        assert "WARN" in str(result["warning"])

    def test_evaluate_response_ok_when_cited_and_relevant(self) -> None:
        content = "Azure AI Foundry provides managed AI infrastructure [1]."
        r = self._response(content, [Citation(text="[1]", source="doc1")])
        result = evaluate_response("What does Azure AI Foundry provide?", r)
        assert result["has_citation"] is True
        assert result["warning"] == ""
