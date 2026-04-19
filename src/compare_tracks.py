"""Compare Track A (Foundry) vs Track B (LangGraph) side-by-side.

Usage:
    uv run python src/compare_tracks.py

This script asks the same questions to both agents and prints:
- answer preview
- citation count
- local evaluation summary (has_citation, relevance_score)
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime

from azure.identity import DefaultAzureCredential

from config.settings import AzureSettings
from foundry.evaluation import evaluate_response
from foundry.rag_agent import AgentResponse, FoundryRagAgent
from langgraph_agent.agent import LangGraphRagAgent


@dataclass
class TrackResult:
    """Container for one track's output for a single question."""

    track_name: str
    response: AgentResponse
    evaluation: dict[str, object]


@dataclass
class ComparisonRecord:
    """Flattened record for one question/track pair."""

    timestamp_utc: str
    question_index: int
    question: str
    track_name: str
    run_id: str
    citation_count: int
    has_citation: bool
    relevance_score: float
    warning: str
    answer: str


def _run_foundry(
    question: str,
    settings: AzureSettings,
    credential: DefaultAzureCredential,
) -> TrackResult:
    """Run a question through Track A (AI Foundry agent)."""
    with FoundryRagAgent.from_settings(settings, credential) as agent:
        response = agent.ask(question)
    evaluation = evaluate_response(question, response)
    return TrackResult(track_name="Track A (Foundry)", response=response, evaluation=evaluation)


def _run_langgraph(
    question: str,
    settings: AzureSettings,
    credential: DefaultAzureCredential,
) -> TrackResult:
    """Run a question through Track B (LangGraph ReAct agent)."""
    agent = LangGraphRagAgent.from_settings(settings, credential)
    response = agent.ask(question)
    evaluation = evaluate_response(question, response)
    return TrackResult(track_name="Track B (LangGraph)", response=response, evaluation=evaluation)


def _print_result(result: TrackResult) -> None:
    """Print one track's result in a compact, comparable format."""
    preview = result.response.content.strip().replace("\n", " ")
    if len(preview) > 400:
        preview = preview[:400] + "..."

    print(f"{result.track_name}")
    print(f"  run_id          : {result.response.run_id}")
    print(f"  citations       : {len(result.response.citations)}")
    print(f"  has_citation    : {result.evaluation['has_citation']}")
    print(f"  relevance_score : {result.evaluation['relevance_score']}")

    warning = str(result.evaluation.get("warning", "")).strip()
    if warning:
        print(f"  warning         : {warning}")

    print(f"  answer_preview  : {preview}")


def _to_record(
    *,
    timestamp_utc: str,
    question_index: int,
    question: str,
    result: TrackResult,
) -> ComparisonRecord:
    """Convert a track result to a serializable flat record."""
    has_citation = bool(result.evaluation.get("has_citation", False))
    relevance_raw = result.evaluation.get("relevance_score", 0.0)
    relevance_score = float(relevance_raw) if isinstance(relevance_raw, int | float) else 0.0

    return ComparisonRecord(
        timestamp_utc=timestamp_utc,
        question_index=question_index,
        question=question,
        track_name=result.track_name,
        run_id=result.response.run_id,
        citation_count=len(result.response.citations),
        has_citation=has_citation,
        relevance_score=relevance_score,
        warning=str(result.evaluation.get("warning", "")),
        answer=result.response.content,
    )


def _write_json(path: str, records: list[ComparisonRecord]) -> None:
    """Write comparison records to a JSON file."""
    payload = [r.__dict__ for r in records]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _write_csv(path: str, records: list[ComparisonRecord]) -> None:
    """Write comparison records to a CSV file."""
    if not records:
        return

    fieldnames = list(records[0].__dict__.keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record.__dict__)


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Compare Foundry (Track A) vs LangGraph (Track B) on fixed questions.",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional path to write JSON results.",
    )
    parser.add_argument(
        "--csv-out",
        default="",
        help="Optional path to write CSV results.",
    )
    return parser.parse_args()



def main() -> None:
    """Run a fixed comparison set for both tracks."""
    args = _parse_args()
    settings = AzureSettings()
    credential = DefaultAzureCredential()
    timestamp_utc = datetime.now(UTC).isoformat()
    records: list[ComparisonRecord] = []

    questions = [
        "How do I deploy Azure OpenAI?",
        "What is LangGraph and when should I use it?",
        "How does Azure AI Search help in RAG?",
    ]

    print("=" * 90)
    print("Enterprise RAG Track Comparison")
    print("=" * 90)

    for idx, question in enumerate(questions, start=1):
        print()
        print("-" * 90)
        print(f"Q{idx}: {question}")
        print("-" * 90)

        foundry_result = _run_foundry(question, settings, credential)
        langgraph_result = _run_langgraph(question, settings, credential)

        _print_result(foundry_result)
        print()
        _print_result(langgraph_result)

        records.append(
            _to_record(
                timestamp_utc=timestamp_utc,
                question_index=idx,
                question=question,
                result=foundry_result,
            )
        )
        records.append(
            _to_record(
                timestamp_utc=timestamp_utc,
                question_index=idx,
                question=question,
                result=langgraph_result,
            )
        )

    if args.json_out:
        _write_json(args.json_out, records)
        print(f"\nWrote JSON results to: {args.json_out}")

    if args.csv_out:
        _write_csv(args.csv_out, records)
        print(f"Wrote CSV results to: {args.csv_out}")


if __name__ == "__main__":
    main()
