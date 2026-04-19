"""Evaluation helpers for the Azure AI Foundry RAG agent.

Provides lightweight evaluation utilities that can be run locally
without the full RAGAS framework (Day 7). These serve as smoke-test
metrics to validate the agent is grounding its answers.

Metrics implemented
--------------------
``has_citation``
    Checks whether the response contains at least one citation marker or
    citation source in the structured ``AgentResponse.citations`` list.
    A response with no citations is a hallucination risk.

``answer_relevance_heuristic``
    Counts how many query keywords appear in the response content.
    Low overlap suggests the answer may not address the question.
    Not a substitute for semantic evaluation — use RAGAS on Day 7.
"""

from __future__ import annotations

import logging

from foundry.rag_agent import AgentResponse

logger = logging.getLogger(__name__)


def has_citation(response: AgentResponse) -> bool:
    """Return True if the response contains at least one grounding citation.

    Checks both structured ``citations`` list and citation number patterns
    (``[1]``, ``[2]``, ...) in the response text as a fallback.

    Args:
        response: ``AgentResponse`` from ``FoundryRagAgent.ask()``.

    Returns:
        True if at least one citation is present.
    """
    if response.citations:
        return True
    import re
    # Fallback: look for inline citation markers like [1] or [1, 2]
    return bool(re.search(r"\[\d+\]", response.content))


def answer_relevance_heuristic(question: str, response: AgentResponse) -> float:
    """Return a keyword overlap score between question and response (0.0–1.0).

    Splits the question into lowercase tokens and counts how many appear
    in the response content.  Stop words are excluded.

    Args:
        question: The original user question.
        response: ``AgentResponse`` from ``FoundryRagAgent.ask()``.

    Returns:
        Float between 0.0 (no overlap) and 1.0 (all keywords present).
    """
    _STOP_WORDS = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "shall", "should", "may", "might", "can", "could",
        "what", "how", "why", "when", "where", "who", "which", "that",
        "this", "these", "those", "of", "in", "on", "at", "to", "for",
        "with", "by", "from", "and", "or", "but", "not",
    }

    tokens = [
        t.strip("?.,!:;\"'()[]")
        for t in question.lower().split()
        if t.strip("?.,!:;\"'()[]") not in _STOP_WORDS
        and len(t.strip("?.,!:;\"'()[]")) > 2
    ]

    if not tokens:
        return 1.0  # no meaningful keywords to check

    response_lower = response.content.lower()
    matched = sum(1 for t in tokens if t in response_lower)
    score = matched / len(tokens)

    logger.debug(
        "Relevance heuristic: %d/%d keywords matched (%.2f)",
        matched,
        len(tokens),
        score,
    )
    return score


def evaluate_response(question: str, response: AgentResponse) -> dict[str, object]:
    """Run all local evaluation metrics and return a summary dict.

    Args:
        question: The original user question.
        response: ``AgentResponse`` from ``FoundryRagAgent.ask()``.

    Returns:
        Dict with keys: ``has_citation``, ``relevance_score``, ``warning``.
    """
    cited = has_citation(response)
    relevance = answer_relevance_heuristic(question, response)

    warning = ""
    if not cited:
        warning = "WARN: no citations — response may not be grounded"
    elif relevance < 0.4:
        warning = (
            f"WARN: low relevance score ({relevance:.2f})"
            " — answer may not address the question"
        )

    result: dict[str, object] = {
        "has_citation": cited,
        "relevance_score": round(relevance, 3),
        "warning": warning,
    }

    if warning:
        logger.warning(warning)
    else:
        logger.info("Evaluation OK — cited=%s, relevance=%.2f", cited, relevance)

    return result
