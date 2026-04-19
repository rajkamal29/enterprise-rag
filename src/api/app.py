"""FastAPI runtime for Track B (LangGraph) RAG agent."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Annotated, Any, AsyncIterator

from azure.identity import DefaultAzureCredential
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from config.logging_config import (
    clear_correlation_id,
    configure_logging,
    set_correlation_id,
)
from config.settings import AzureSettings
from langgraph_agent.agent import LangGraphRagAgent

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    logger.info("FastAPI runtime started")
    yield

app = FastAPI(
    title="Enterprise Agentic RAG API",
    version="0.1.0",
    description="Track B runtime deployed on Azure Container Apps",
    lifespan=_lifespan,
)


class AskRequest(BaseModel):
    """Request body for the /ask endpoint."""

    question: str = Field(min_length=1, max_length=4000)


class AskResponse(BaseModel):
    """Response body for the /ask endpoint."""

    answer: str
    citations: list[str]
    run_id: str


@lru_cache(maxsize=1)
def _get_agent() -> LangGraphRagAgent:
    """Create and cache a single agent instance for the process lifetime."""
    settings = AzureSettings()
    credential = DefaultAzureCredential()
    return LangGraphRagAgent.from_settings(settings, credential)


def _extract_citations(response: Any) -> list[str]:
    """Normalize AgentResponse citations into plain strings for API output."""
    citations: list[str] = []
    for citation in response.citations:
        source = (citation.source or citation.text).strip()
        if source and source not in citations:
            citations.append(source)
    return citations


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness endpoint for ACA health probes."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(
    payload: AskRequest,
    x_request_id: Annotated[str | None, Header()] = None,
) -> AskResponse:
    """Answer a user question via the LangGraph RAG agent."""
    correlation_id = set_correlation_id(x_request_id)
    try:
        logger.info("Received /ask request")
        response = _get_agent().ask(payload.question)
        return AskResponse(
            answer=response.content,
            citations=_extract_citations(response),
            run_id=response.run_id,
        )
    except ValueError as exc:
        logger.warning("Bad request: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive runtime boundary
        logger.exception("Unhandled error in /ask")
        raise HTTPException(status_code=500, detail="Internal server error") from exc
    finally:
        clear_correlation_id()
        logger.info("Completed /ask request [request_id=%s]", correlation_id)
