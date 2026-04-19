# Multi-Agent Patterns for Agentic RAG on Azure

This reference documents the seven most relevant multi-agent patterns for enterprise RAG systems.  
Each pattern is assessed for control, cost, testability, and the scenarios where it is the right choice.

---

## Pattern 1 — Single ReAct Agent

**What it is:** One agent runs a Reason + Act loop, calling tools as needed to answer a question.  
This is the Track B baseline (Day 5).

```
User ──► ReAct Agent ──► [search tool] ──► [search tool] ──► Answer
```

**State model:** `messages` list grows with each tool call and LLM response.

**Strengths**
- Lowest implementation cost — one graph, one agent.
- LLM decides how many tool calls are needed — adapts to question complexity.
- Easiest to debug: full message trace shows every reasoning step.

**Weaknesses**
- All reasoning in one prompt → harder to enforce grounding for complex multi-hop questions.
- Token cost grows with every tool call appended to the message list.
- Hard to parallelise or distribute.

**When to use**
- Single-hop factual questions.
- Prototypes and MVPs.
- When you need the fastest path to a working agent.

**Azure implementation**  
`LangGraphRagAgent` in `src/langgraph_agent/` — LangGraph `StateGraph` with `model_node` and `tool_node`.

---

## Pattern 2 — Planner + Specialists ✅ (Day 8)

**What it is:** A planner LLM call decomposes the user question into sub-queries, then specialist nodes execute each sub-query in sequence and synthesise the results.

```
User ──► Planner ──► Retrieve₁ ──► Retrieve₂ ──► Retrieve₃
                                                      │
                                              Summarise ──► Cite ──► Answer
```

**State model:** `PlannerState` with `tasks[]`, `current_task_index`, `retrieved_context`, `summary`, `final_answer`, `citations[]`.

**Strengths**
- Explicit routing — every step is observable and testable in isolation.
- Each specialist can be replaced or upgraded independently.
- No implicit tool-call loop — cost is predictable (N retrieve + 1 summarise + 1 cite LLM calls).

**Weaknesses**
- More LLM calls than a single ReAct agent for simple questions.
- Planner quality directly affects retrieval coverage.
- Sequential execution — no parallelism in the base pattern.

**When to use**
- Multi-hop questions that need facts from multiple sources.
- When you need explainable intermediate steps for audit or compliance.
- When retrieval and generation concerns must be separated for governance.

**Azure implementation**  
`PlannerAgent` in `src/multi_agent/` — LangGraph `StateGraph` with `plan`, `retrieve`, `summarise`, `cite` nodes and conditional routing.

---

## Pattern 3 — Supervisor / Router

**What it is:** A supervisor LLM receives the user question and routes it to the most appropriate specialist agent.  Specialists do not know about each other.

```
User ──► Supervisor ──┬──► Domain A Agent ──► Answer
                      ├──► Domain B Agent ──► Answer
                      └──► Domain C Agent ──► Answer
```

**State model:** Supervisor holds routing decision; each specialist has its own state.

**Strengths**
- Clean separation of domain knowledge into specialist agents.
- Easy to add new domains without changing existing agents.
- Routing decision is auditable.

**Weaknesses**
- The supervisor is a single point of failure.
- Routing errors are hard to recover from mid-run.
- Difficult for cross-domain questions — supervisor must route to one agent only.

**When to use**
- Multi-domain knowledge bases (HR, Finance, Legal, Engineering) where questions rarely cross domains.
- When domain specialists need different tools, prompts, or retrieval indexes.
- Enterprise portals with topic-partitioned corpora.

**Azure implementation**  
Supervisor: a single LangGraph node calling the LLM with a routing prompt and returning the domain label.  
Specialists: separate `LangGraphRagAgent` or `PlannerAgent` instances bound to domain-specific AI Search indexes.

---

## Pattern 4 — Sequential Pipeline

**What it is:** A fixed chain of agents where each agent processes the output of the previous one.  No routing logic — all agents run every time.

```
User ──► Retrieval Agent ──► Extraction Agent ──► Synthesis Agent ──► Answer
```

**State model:** Output of one agent is the input to the next; shared context object grows.

**Strengths**
- Fully deterministic execution order — easy to reason about.
- Each stage can be unit tested with its specific input/output contract.
- Simple to implement with LangGraph edges (no conditional routing).

**Weaknesses**
- All stages run regardless of whether they are needed.
- Highest latency of all patterns — strictly serial.
- Hard to skip stages for simpler questions.

**When to use**
- Document processing pipelines (extract → classify → index → answer).
- Compliance workflows where every stage must always produce a documented output.
- When the question type is fixed and always requires all stages.

**Azure implementation**  
LangGraph `StateGraph` with `add_edge("a", "b")` chaining all nodes and no `add_conditional_edges`.

---

## Pattern 5 — Parallel Fan-Out

**What it is:** A dispatcher sends the question to multiple agents simultaneously; an aggregator merges their results.

```
                    ┌──► Agent A (keyword search)  ──┐
User ──► Dispatcher ├──► Agent B (vector search)   ──┼──► Aggregator ──► Answer
                    └──► Agent C (semantic rerank)  ──┘
```

**State model:** Dispatcher fans out to N branches; aggregator receives all N responses.

**Strengths**
- Lowest latency for N-way retrieval when branches are independent.
- Different retrieval strategies can run in parallel and be merged by relevance.
- Failure of one branch does not block the others (with proper error handling).

**Weaknesses**
- Hardest pattern to implement correctly in LangGraph (requires async or thread-based execution).
- Aggregation logic can be complex (how do you merge conflicting answers?).
- Cost is N× higher than a single agent.

**When to use**
- Hybrid retrieval where keyword, vector, and semantic results are fetched independently.
- A/B evaluation of two retrieval strategies on the same question.
- High-traffic systems where latency is the primary constraint.

**Azure implementation**  
LangGraph `Send` API for parallel branch dispatch.  
Azure AI Search supports hybrid retrieval natively (keyword + vector + semantic reranker) in a single call — often making this pattern unnecessary at the retrieval layer.

---

## Pattern 6 — Critic / Verifier

**What it is:** A main agent produces a draft answer; a separate critic agent evaluates it against grounding criteria and either approves it or sends it back for revision.

```
User ──► Generator ──► Draft ──► Critic ──┬──► (pass) ──► Answer
                          ▲               └──► (fail) ──► Generator (revise)
                          └─────────────────────────────────┘
```

**State model:** Includes `draft_answer`, `critique`, `revision_count`, `approved` flag.

**Strengths**
- Explicit quality gate before the answer reaches the user.
- Critic can enforce grounding, citation completeness, or tone policies.
- Separates "can the LLM answer this?" from "is this answer good enough?".

**Weaknesses**
- At least 2× the LLM token cost per question.
- Revision loops can run indefinitely without a `max_revisions` guard.
- Critic LLM can disagree with the generator for subjective reasons.

**When to use**
- High-stakes domains (legal, medical, financial) where hallucination cost is high.
- When citation completeness must be machine-verifiable before response delivery.
- When response policy (tone, length, format) must be enforced automatically.

**Azure implementation**  
Pair a `generator_node` and a `critic_node` in LangGraph with a conditional edge based on `approved`.  
Set `max_revisions = 2` as a guard in state and in the router.  
Use Azure AI Content Safety as a complementary hard stop (before the generator, not after).

---

## Pattern 7 — Hierarchical Agents

**What it is:** A top-level planner decomposes the question into sub-tasks; each sub-task is handled by its own planner, which further decomposes into specialist calls.  Two or more levels of planning.

```
User ──► Top Planner ──┬──► Sub-Planner A ──► Specialist A1 ──► Specialist A2
                       └──► Sub-Planner B ──► Specialist B1 ──► Specialist B2
                                                        │
                                              Aggregator ──► Answer
```

**State model:** Hierarchical — top planner state contains sub-planner results as nested objects.

**Strengths**
- Handles arbitrarily complex questions with many independent sub-components.
- Each sub-planner is independently testable.
- Scales to large knowledge bases with domain partitioning.

**Weaknesses**
- Highest implementation complexity of all patterns.
- Latency grows multiplicatively with depth.
- Error propagation across levels is hard to handle gracefully.
- Almost always over-engineered for enterprise RAG — prefer Planner + Specialists or Supervisor first.

**When to use**
- Enterprise-wide Q&A spanning multiple business domains, each with its own corpus and toolset.
- Research-style tasks where sub-tasks themselves require multi-step reasoning.
- When a single planner would produce more than 5 sub-tasks.

**Azure implementation**  
Nest `build_planner_graph()` calls.  Each level runs as its own compiled LangGraph runnable.  
Top-level state carries results from sub-planners as a list.

---

## Pattern Selection Guide

| Scenario | Recommended pattern |
|---|---|
| Single-hop factual questions, prototype | Single ReAct Agent (Pattern 1) |
| Multi-hop questions needing 2-3 sources | Planner + Specialists (Pattern 2) |
| Multi-domain knowledge base, clear domain boundaries | Supervisor / Router (Pattern 3) |
| Fixed processing pipeline, compliance audit trail | Sequential Pipeline (Pattern 4) |
| Parallel hybrid retrieval strategies | Parallel Fan-Out (Pattern 5) |
| High-stakes answer validation, citation enforcement | Critic / Verifier (Pattern 6) |
| Enterprise-wide, many domains, complex sub-tasks | Hierarchical Agents (Pattern 7) |

**General rule:** use the simplest pattern that meets the reasoning requirement.  
Complexity adds cost, latency, and failure surface.  Upgrade the pattern only when evidence demands it.

---

## Cost + Latency Comparison (approximate, per question)

| Pattern | LLM calls | Relative cost | Relative latency |
|---|---:|---|---|
| Single ReAct | 2–5 | 1× | 1× |
| Planner + Specialists (3 tasks) | 5 | ~2× | ~2× |
| Supervisor + 1 specialist | 3–6 | ~1.5× | ~1.5× |
| Sequential Pipeline (3 stages) | 3 | ~1.5× | ~3× (serial) |
| Parallel Fan-Out (3 branches) | 3 | ~3× | ~1× (parallel) |
| Critic / Verifier (1 revision) | 4–6 | ~2.5× | ~2× |
| Hierarchical (2 levels, 2 sub) | 8–12 | ~4–5× | ~4× |

---

## Azure-specific notes

- **Azure AI Search** supports hybrid (keyword + vector) + semantic reranker in a single call.  
  This eliminates the need for Parallel Fan-Out at the retrieval layer in most cases.
- **Azure AI Foundry** managed workflows are closest to the Supervisor/Router pattern — AI Foundry handles the routing; you provide the specialist tools.
- **LangGraph on Azure Container Apps** (Day 9) is the deployment target for Patterns 2–7.
- **OpenTelemetry spans** (Day 7) provide per-node latency data to validate pattern choice with real measurements.

---

*See also:* `docs/DAY_8.md` (implementation notes), `src/multi_agent/` (Planner + Specialists implementation), `src/langgraph_agent/` (Single ReAct implementation).
