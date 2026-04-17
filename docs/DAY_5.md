# Day 5 - Azure-Based Custom Agent Workflow

Goal: Build the custom Azure-based Agentic RAG path using LangGraph and compare it to the AI Foundry workflow.

## Outcomes
- LangGraph ReAct agent with Azure OpenAI tool-calling.
- Azure AI Search tool integration and citation enforcement.
- Custom runtime state model and trace identifiers.
- First explicit comparison between Track A and Track B orchestration style.

## Why this day follows AI Foundry
- Build the managed path first to understand the baseline.
- Build the custom path next to understand where flexibility and control justify extra engineering.

## 6-Hour Plan
1. Implement LangGraph state model and ReAct loop.
2. Add Azure AI Search tool for retrieval.
3. Enforce citations and grounded response pattern.
4. Add request and tool-call tracing IDs.
5. Compare the same use case across Track A and Track B.
6. Document where custom orchestration wins and where it costs more.

## Exit Criteria
- Custom agent answers grounded questions with citations.
- Same sample workload runs in both AI Foundry and custom LangGraph paths.
- Initial managed-vs-custom tradeoffs are documented.

## Suggested Commit
feat(day-5): build Azure-based custom agent workflow with LangGraph

## LinkedIn Prompt
Best practice #5 for Agentic RAG on Azure: after the managed baseline, build the custom path. LangGraph gives you explicit state, routing, and testability when the managed surface is not enough.
