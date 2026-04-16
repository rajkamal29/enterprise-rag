# Day 1 - Setup, CI/CD, Guardrails

Goal: Establish production-grade repository baseline.

## Outcomes
- Repository initialized with Python tooling.
- CI checks scaffolded (lint, type, test, security).
- Guardrails module created with tests.

## 6-Hour Plan
1. Hour 1: Initialize project and environment.
2. Hour 2: Add quality tooling configuration.
3. Hour 3: Add GitHub Actions workflows.
4. Hour 4: Implement input validation.
5. Hour 5: Implement circuit breaker.
6. Hour 6: Write tests, run checks, push.

## Commands
```powershell
uv init --python 3.12
uv add pydantic langchain
uv add "faiss-cpu; platform_system != 'Windows'"
uv add --dev pytest ruff mypy bandit pip-audit pre-commit
```

## Exit Criteria
- Local tests pass.
- CI pipeline triggers on push.
- First guardrails commit merged.

## Suggested Commit
feat(day-1): setup CI pipeline and guardrails foundation

## LinkedIn Prompt
Started Enterprise RAG with guardrails-first architecture and CI discipline.
