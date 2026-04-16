# Day 4 - Agent Foundation: LangGraph ReAct Loop + Tool Calling

Goal: Build the core agentic reasoning loop using LangGraph and Azure OpenAI tool-calling.

## Outcomes
- LangGraph ReAct agent that reasons before acting.
- Azure OpenAI function/tool calling wired to first tool: document search.
- Agent state schema (messages, tool calls, context, trace_id).
- Agent responds with cited sources, not bare LLM completions.

## What Makes This "Agentic"
```
User Query
    │
    ▼
┌─────────────────────────────┐
│       LangGraph Agent       │
│                             │
│  [Think] What do I need?    │
│  [Act]   Call search tool   │
│  [Observe] Got 5 chunks     │
│  [Think] Is this enough?    │
│  [Act]   Call search again  │  ← Multi-step, not single-shot
│  [Observe] Got more context │
│  [Generate] Final answer    │
└─────────────────────────────┘
```

## 6-Hour Plan
1. Install LangGraph, define agent state dataclass.
2. Implement `DocumentSearchTool` — calls Azure AI Search, returns ranked chunks.
3. Implement ReAct agent graph: reason → tool_call → observe → generate nodes.
4. Wire Azure OpenAI tool-calling (function definitions from tool schemas).
5. Enforce citation: agent must reference source document in final answer.
6. Add tests: agent calls tool when query requires retrieval; agent cites sources.

## Key Code Pattern
```python
from langgraph.graph import StateGraph
from langchain_openai import AzureChatOpenAI

# Tools are declared as typed functions — Azure OpenAI generates the JSON schema
@tool
def search_documents(query: str, top_k: int = 5) -> list[SearchResult]:
    """Search the enterprise knowledge base for relevant document chunks."""
    return azure_search_client.search(query, top_k=top_k)

agent = create_react_agent(llm, tools=[search_documents])
```

## Exit Criteria
- Agent performs at least 2 reasoning steps for a multi-part question.
- Every answer includes at least one cited source.
- Tool call inputs and outputs are logged with trace_id.

## Suggested Commit
feat(day-4): LangGraph ReAct agent with Azure OpenAI tool-calling

## LinkedIn Prompt
Best practice #4 for Enterprise Agentic RAG on Azure: The shift from RAG pipeline to Agentic RAG is the reasoning loop. LangGraph lets you define nodes for Think → Act → Observe with full state visibility. Azure OpenAI tool-calling is the bridge between the agent's reasoning and your retrieval layer.
