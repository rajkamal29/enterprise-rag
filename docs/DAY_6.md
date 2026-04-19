# Day 6 - Evaluation Gate and Quality Thresholds

Goal: enforce minimum response quality in CI using comparison outputs from Track A vs Track B.

## Outcomes
- Added a gate script: `src/evaluation_gate.py`.
- Added automated checks in CI against `data/track_compare.json`.
- Defined minimum thresholds for citation rate and relevance.

## Commands
1. Generate comparison output:
	`uv run python src/compare_tracks.py --json-out data/track_compare.json --csv-out data/track_compare.csv`
2. Run gate locally:
	`uv run python src/evaluation_gate.py --input data/track_compare.json`

## Default Thresholds
- `min_records`: 3 records per track
- `min_citation_rate`: 0.60 per track
- `min_avg_relevance`: 0.70 per track

## Exit Criteria
- CI fails when any track drops below thresholds.
- Gate output clearly shows per-track stats and failing checks.
- Team can tune thresholds without code changes via CLI flags.

## Suggested Commit
feat(day-6): add evaluation gate and CI threshold checks

## LinkedIn Prompt
Best practice #6 for Agentic RAG on Azure: treat evaluation as a release gate, not a dashboard. If citation and relevance thresholds are not met, the build should fail.
