# Day 8 - Multi-Agent Planner Pattern

Goal: Build a planner agent that routes sub-tasks to specialist agents and compare single-agent vs multi-agent tradeoffs.

## Outcomes
- Planner agent decomposes a complex user query into sub-tasks.
- Specialist agents (retrieval, summarisation, citation) handle individual sub-tasks.
- State is handed off cleanly between agents via `AgentState`.
- Planner-vs-single-agent tradeoffs documented for Day 10.

## Why this day matters
- Most enterprise workloads require more than one reasoning step.
- A planner pattern lets you scale agent complexity without making any single agent unmanageable.
- Documenting the tradeoffs now creates the evidence base for Day 10 guidance.

## 6-Hour Plan
1. Design planner state schema — task list, current task, completed tasks, final answer.
2. Implement `src/multi_agent/planner.py` — LangGraph planner node with task decomposition.
3. Implement specialist nodes: `retrieval_agent`, `summarisation_agent`, `citation_agent`.
4. Wire nodes into a `StateGraph` with conditional routing.
5. Run the same 3 sample questions through the planner and compare output quality vs single-agent.
6. Document when multi-agent adds value and when it adds cost without benefit.

## Files to create
| File | Purpose |
|---|---|
| `src/multi_agent/__init__.py` | Package marker |
| `src/multi_agent/planner.py` | Planner node + `build_planner_graph()` |
| `src/multi_agent/specialists.py` | Retrieval, summarisation, and citation nodes |
| `src/multi_agent/state.py` | `PlannerState` TypedDict |
| `tests/multi_agent/test_planner.py` | Unit tests |

## Exit Criteria
- Planner graph returns grounded answers with intermediate task traces.
- Single-agent vs multi-agent comparison evidence committed.
- All tests pass, ruff/mypy/bandit clean.

## Shipped
- Added `src/multi_agent/state.py` with `PlannerState` to model planner and specialist handoff.
- Added `src/multi_agent/specialists.py` with retrieval, summarisation, and citation specialist node factories.
- Added `src/multi_agent/planner.py` with planner node, retrieval router, `build_planner_graph()`, and `PlannerAgent` facade.
- Added `src/multi_agent/__init__.py` exports for package-level imports.
- Added `tests/multi_agent/test_planner.py` with 13 unit tests covering planner decomposition, retrieval accumulation, router transitions, and `PlannerAgent.ask()` flow.
- Added `docs/MULTI_AGENT_PATTERNS.md` documenting available patterns: Single ReAct, Planner+Specialists, Supervisor/Router, Sequential Pipeline, Parallel Fan-Out, Critic/Verifier, and Hierarchical.
- Quality gate result for this increment: `ruff` clean, `mypy` clean, `pytest` 99 passed, `bandit` clean.

## Suggested Commit
feat(day-8): add multi-agent planner pattern with specialist routing

## LinkedIn Prompt
Best practice #8 for Agentic RAG on Azure: know when to split agents. A planner pattern is justified when the answer requires multiple distinct reasoning steps with different retrieval contexts. If a single ReAct loop handles it, keep it simple.
