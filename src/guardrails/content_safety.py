"""Azure AI Content Safety guardrail for Enterprise Agentic RAG.

This module provides ``ContentSafetyGuardrail``, a lightweight wrapper around
the Azure AI Content Safety ``ContentSafetyClient``.  It is designed to run as
a pre-check in both Track A (FoundryRagAgent) and Track B (LangGraphRagAgent)
before any user input reaches the LLM.

Behaviour
---------
- If ``AZURE_CONTENT_SAFETY_ENDPOINT`` is not set (or the guardrail is
  instantiated without an endpoint), the check is a no-op — useful in local
  development and unit tests.
- When enabled, the guardrail screens for **hate**, **violence**, **sexual**,
  and **self-harm** content at or above ``severity_threshold`` (default: 2,
  meaning *low* severity or higher is blocked).
- A blocked input raises ``ContentSafetyError`` (a ``ValueError`` subclass)
  with a descriptive message that includes the category and severity.

Usage
-----
::

    from guardrails.content_safety import ContentSafetyGuardrail

    guard = ContentSafetyGuardrail.from_env()  # reads env vars
    guard.check("user input text")  # raises ContentSafetyError if blocked
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from azure.core.credentials import TokenCredential

logger = logging.getLogger(__name__)

# Severity levels: 0=safe, 2=low, 4=medium, 6=high
_DEFAULT_SEVERITY_THRESHOLD = 2


class ContentSafetyError(ValueError):
    """Raised when input is blocked by Azure AI Content Safety.

    Attributes:
        category:  The safety category that triggered the block
                   (e.g. ``"Hate"``, ``"Violence"``).
        severity:  The detected severity level (2, 4, or 6).
    """

    def __init__(self, category: str, severity: int) -> None:
        self.category = category
        self.severity = severity
        super().__init__(
            f"Input blocked by content safety: category={category}, severity={severity}"
        )


class ContentSafetyGuardrail:
    """Screen text against Azure AI Content Safety before sending to the LLM.

    Parameters
    ----------
    endpoint:
        Azure AI Content Safety resource endpoint.  When ``None`` the guardrail
        runs in no-op mode and every ``check()`` call passes silently.
    credential:
        Azure credential for authentication.  Required when *endpoint* is set.
    severity_threshold:
        Minimum severity level that triggers a block.  Default is 2 (low).
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        credential: Optional[TokenCredential] = None,
        *,
        severity_threshold: int = _DEFAULT_SEVERITY_THRESHOLD,
    ) -> None:
        self._endpoint = endpoint
        self._severity_threshold = severity_threshold
        self._client: Any = None

        if endpoint and credential:
            try:
                from azure.ai.contentsafety import ContentSafetyClient

                self._client = ContentSafetyClient(endpoint=endpoint, credential=credential)
                logger.info("ContentSafetyGuardrail enabled (endpoint=%s)", endpoint)
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to create ContentSafetyClient: %s", exc)
        else:
            logger.debug("ContentSafetyGuardrail running in no-op mode (no endpoint configured)")

    @classmethod
    def from_env(cls, credential: Optional[TokenCredential] = None) -> "ContentSafetyGuardrail":
        """Create a guardrail from environment variables.

        Reads ``AZURE_CONTENT_SAFETY_ENDPOINT`` and optional
        ``CONTENT_SAFETY_SEVERITY_THRESHOLD``.  If the env var is not set,
        returns a no-op guardrail.
        """
        endpoint = os.environ.get("AZURE_CONTENT_SAFETY_ENDPOINT")
        threshold_str = os.environ.get("CONTENT_SAFETY_SEVERITY_THRESHOLD", "")
        threshold = int(threshold_str) if threshold_str.isdigit() else _DEFAULT_SEVERITY_THRESHOLD
        return cls(endpoint=endpoint, credential=credential, severity_threshold=threshold)

    def check(self, text: str) -> None:
        """Screen *text* for harmful content.

        Args:
            text: The user input to screen.

        Raises:
            ContentSafetyError: If *text* is blocked.
        """
        if self._client is None:
            return

        try:
            from azure.ai.contentsafety.models import AnalyzeTextOptions

            request = AnalyzeTextOptions(text=text)
            response = self._client.analyze_text(request)

            categories = getattr(response, "categories_analysis", [])
            for result in categories:
                severity: int = getattr(result, "severity", 0) or 0
                category: str = str(getattr(result, "category", "Unknown"))
                if severity >= self._severity_threshold:
                    logger.warning(
                        "Content safety blocked input: category=%s, severity=%d",
                        category,
                        severity,
                    )
                    raise ContentSafetyError(category=category, severity=severity)

        except ContentSafetyError:
            raise
        except Exception as exc:
            # Treat API errors as non-blocking to avoid availability dependency.
            logger.warning("Content safety check failed (non-blocking): %s", exc)

    @property
    def is_enabled(self) -> bool:
        """``True`` if the guardrail is connected to a live endpoint."""
        return self._client is not None
