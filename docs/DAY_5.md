# Day 5 - Agent Tools and Memory

Goal: Expand the agent's capabilities with a tool library and add short-term and long-term memory.

## Outcomes
- Tool library: search, calculator, date/time, HTTP API caller.
- Short-term memory: sliding conversation window (last N turns).
- Long-term memory: persist important entities to Azure AI Search.
- Tool result caching to avoid redundant LLM + search calls.

## Memory Architecture
```
┌───────────────────────────────────────┐
│              Agent Memory             │
│                                       │
│  Short-term (Redis / in-process)      │
│  └─ Last 10 conversation turns        │
│  └─ Current session context           │
│                                       │
│  Long-term (Azure AI Search)          │
│  └─ User preferences                  │
│  └─ Key facts extracted from sessions │
│  └─ Searchable by future sessions     │
└───────────────────────────────────────┘
```

## Tool Library
| Tool | Purpose |
|---|---|
| `search_documents` | Azure AI Search (from Day 4) |
| `calculate` | Safe math evaluation — never use `eval()` |
| `get_current_date` | Temporal grounding for the agent |
| `call_api` | Generic HTTP tool with allowlist validation |
| `search_memory` | Query long-term memory in Azure AI Search |
| `store_memory` | Persist key fact to long-term memory |

## 6-Hour Plan
1. Implement calculator, date, and HTTP tools with input validation.
2. Implement `ConversationMemory` — sliding window, serialisable.
3. Implement `LongTermMemory` — read/write to dedicated AI Search index.
4. Wire memory into LangGraph agent state (inject on entry, flush on exit).
5. Add tool result cache (TTL-based, keyed on tool + normalised input).
6. Add tests: memory persists across agent turns; cache prevents double search.

## Exit Criteria
- Agent recalls a fact stated 5 turns earlier via short-term memory.
- Long-term memory survives process restart (persisted in AI Search).
- Duplicate tool calls within same session use cache.

## Suggested Commit
feat(day-5): agent tool library and short/long-term memory

## LinkedIn Prompt
Best practice #5 for Enterprise Agentic RAG on Azure: Memory is not optional in enterprise agents. Short-term (sliding window) keeps context in one session. Long-term (vector store) means the agent remembers across sessions. Two different problems — two different solutions.
