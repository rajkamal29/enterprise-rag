# Day 8 - Multi-Agent Pattern

Goal: Evolve from a single ReAct agent to a planner + specialist multi-agent architecture.

## Outcomes
- Planner agent decomposes complex queries into sub-tasks.
- Specialist agents: Retriever, Synthesizer, Validator.
- Parallel tool execution where sub-tasks are independent.
- Agent trajectory evaluation: score whether agent took the right steps.

## Multi-Agent Architecture
```
User Query
    │
    ▼
┌──────────────┐
│   Planner    │  Decomposes query → sub-task list
└──────┬───────┘
       │
  ┌────┴─────┐
  │          │
  ▼          ▼
┌──────┐  ┌──────────┐
│Search│  │  Search  │  ← Run in parallel (independent sub-tasks)
│Agent │  │  Agent 2 │
└──┬───┘  └────┬─────┘
   │           │
   └─────┬─────┘
         ▼
   ┌──────────────┐
   │ Synthesizer  │  Merges results
   └──────┬───────┘
          ▼
   ┌──────────────┐
   │  Validator   │  Checks groundedness + citations
   └──────────────┘
```

## Agent Trajectory Evaluation
Don't just score the final answer — score whether the agent took the correct steps:
- Did the planner identify all required sub-tasks?
- Did each specialist use the right tools?
- Were tool calls in the correct order?
- Was the synthesizer's merge faithful to sources?

## 6-Hour Plan
1. Implement `PlannerAgent` — decomposes query into sub-task list using structured output.
2. Implement `RetrieverAgent` — focused search specialist with domain scope.
3. Implement `SynthesizerAgent` — merges multi-source context into coherent answer.
4. Implement `ValidatorAgent` — runs groundedness + citation checks on final answer.
5. Wire LangGraph multi-agent graph with parallel execution for independent sub-tasks.
6. Implement trajectory scorer, add tests for correct planning on benchmark queries.

## Exit Criteria
- Multi-agent pipeline answers a 3-part question better than single agent.
- Trajectory scorer correctly identifies a mis-planned agent run.
- Parallel sub-tasks complete in less time than sequential execution.

## Suggested Commit
feat(day-8): multi-agent planner and specialist architecture with trajectory evaluation

## LinkedIn Prompt
Best practice #8 for Enterprise Agentic RAG on Azure: Single agents hit a reasoning ceiling. The multi-agent pattern — Planner → Specialists → Synthesizer → Validator — handles complex enterprise queries where a single ReAct loop either hallucinates or loops indefinitely. LangGraph makes the handoffs explicit and testable.
