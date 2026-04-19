"""OpenTelemetry tracer factory for Enterprise Agentic RAG.

This module provides a single, lazily-configured tracer that both Track A
(FoundryRagAgent) and Track B (LangGraphRagAgent) import.  Call
``configure_tracing()`` once at application start-up — typically from a
CLI entry point or a FastAPI lifespan handler.

Exporter selection
------------------
- If ``connection_string`` is provided (or ``APPLICATIONINSIGHTS_CONNECTION_STRING``
  is set in the environment), traces are exported to Azure Application Insights
  via ``AzureMonitorTraceExporter``.
- Otherwise a ``SimpleSpanProcessor`` with a ``ConsoleSpanExporter`` is used so
  that spans are visible during local development without any Azure dependency.
- Tests can pass ``exporter=InMemorySpanExporter()`` to capture spans for
  assertions.

Span schema
-----------
Both agents emit spans with a consistent set of attributes:

``rag.ask``
    - ``rag.track``          — ``"foundry"`` or ``"langgraph"``
    - ``rag.question_length`` — character count of the question
    - ``rag.run_id``          — unique request/run identifier
    - ``rag.citation_count``  — number of citations in the final response

``rag.retrieve`` (set by the search tool or agent internals when available)
    - ``rag.track``
    - ``rag.result_count``

``rag.generate``
    - ``rag.track``
    - ``rag.model``
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
    SpanExporter,
)

logger = logging.getLogger(__name__)

_TRACER_PROVIDER: Optional[TracerProvider] = None
_SERVICE = "enterprise-rag"


def configure_tracing(
    connection_string: Optional[str] = None,
    *,
    exporter: Optional[SpanExporter] = None,
) -> TracerProvider:
    """Initialise the global OTel ``TracerProvider``.

    Call this once at start-up.  Subsequent calls are idempotent — the same
    provider is returned without re-initialising.

    Args:
        connection_string:
            Azure Application Insights connection string.  Falls back to the
            ``APPLICATIONINSIGHTS_CONNECTION_STRING`` environment variable.
            When neither is set and *exporter* is ``None``, a
            ``ConsoleSpanExporter`` is used instead.
        exporter:
            Override the exporter entirely.  Useful for passing an
            ``InMemorySpanExporter`` in tests.

    Returns:
        The configured ``TracerProvider`` (also set as the global OTel provider).
    """
    global _TRACER_PROVIDER  # noqa: PLW0603
    if _TRACER_PROVIDER is not None:
        return _TRACER_PROVIDER

    resource = Resource(attributes={SERVICE_NAME: _SERVICE})
    provider = TracerProvider(resource=resource)

    resolved_exporter: SpanExporter
    if exporter is not None:
        resolved_exporter = exporter
        provider.add_span_processor(SimpleSpanProcessor(resolved_exporter))
        logger.debug("OTel tracing: using provided exporter (%s)", type(exporter).__name__)
    else:
        cs = connection_string or os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if cs:
            try:
                from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

                az_exporter = AzureMonitorTraceExporter(connection_string=cs)
                provider.add_span_processor(BatchSpanProcessor(az_exporter))
                logger.info("OTel tracing: exporting to Azure Application Insights")
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to configure Azure Monitor exporter: %s", exc)
                _add_console_exporter(provider)
        else:
            _add_console_exporter(provider)

    trace.set_tracer_provider(provider)
    _TRACER_PROVIDER = provider
    return provider


def _add_console_exporter(provider: TracerProvider) -> None:
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    logger.debug("OTel tracing: exporting to console (no App Insights connection string set)")



def get_tracer(name: str) -> trace.Tracer:
    """Return a tracer for *name*.

    Uses the module-level ``_TRACER_PROVIDER`` when configured so that tests
    using ``configure_tracing(exporter=...)`` get isolated spans.  Falls back
    to the global OTel provider (no-op) when called before ``configure_tracing``.
    """
    if _TRACER_PROVIDER is not None:
        return _TRACER_PROVIDER.get_tracer(name)
    return trace.get_tracer(name)


def reset_for_testing() -> None:
    """Reset the module-level provider reference.  Call this in test teardown.

    Only resets the module variable — does not touch the global OTel registry,
    which cannot be replaced once set.
    """
    global _TRACER_PROVIDER  # noqa: PLW0603
    _TRACER_PROVIDER = None
