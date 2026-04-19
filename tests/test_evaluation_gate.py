"""Unit tests for Day 6 evaluation gate logic."""

from __future__ import annotations

from pathlib import Path

from evaluation_gate import evaluate, load_records, summarize


def test_load_records_reads_list(tmp_path: Path) -> None:
    file_path = tmp_path / "records.json"
    file_path.write_text('[{"track_name":"A","has_citation":true,"relevance_score":1.0}]')

    records = load_records(file_path)
    assert len(records) == 1


def test_summarize_and_evaluate_pass() -> None:
    records = [
        {"track_name": "A", "has_citation": True, "relevance_score": 1.0},
        {"track_name": "A", "has_citation": False, "relevance_score": 0.8},
        {"track_name": "B", "has_citation": True, "relevance_score": 0.9},
        {"track_name": "B", "has_citation": True, "relevance_score": 0.9},
    ]

    stats = summarize(records)
    failures = evaluate(
        stats,
        min_records=2,
        min_citation_rate=0.5,
        min_avg_relevance=0.7,
    )
    assert failures == []


def test_evaluate_fails_when_threshold_not_met() -> None:
    records = [
        {"track_name": "A", "has_citation": False, "relevance_score": 0.4},
        {"track_name": "A", "has_citation": False, "relevance_score": 0.5},
        {"track_name": "B", "has_citation": True, "relevance_score": 0.9},
    ]

    stats = summarize(records)
    failures = evaluate(
        stats,
        min_records=2,
        min_citation_rate=0.6,
        min_avg_relevance=0.7,
    )
    assert failures
