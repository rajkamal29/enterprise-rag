"""PlannerState — shared state flowing through all multi-agent nodes.

The planner graph uses a single TypedDict that every node reads from and
writes patches back to.  LangGraph merges the patches automatically.

Field lifecycle
---------------
question           Set by the caller before invoking the graph.
tasks              Set by the planner node — a list of search queries derived
                   from the question.
current_task_index Updated by each retrieval node call to track progress.
completed_tasks    Accumulates the queries that have been retrieved.
retrieved_context  Accumulates raw text from every retrieval call.
summary            Set by the summarisation node.
final_answer       Set by the citation node — the answer returned to the caller.
citations          Accumulates source titles found during retrieval.
request_id         Caller-assigned trace ID propagated to all nodes.
"""

from __future__ import annotations

from typing import TypedDict


class PlannerState(TypedDict):
    """State shared across all nodes in the multi-agent planner graph."""

    question: str
    tasks: list[str]
    current_task_index: int
    completed_tasks: list[str]
    retrieved_context: str
    summary: str
    final_answer: str
    citations: list[str]
    request_id: str
