"""Azure AI Foundry agent package — Track A Agentic RAG workflow.

Exposes a single ``FoundryRagAgent`` that:
- Creates an AI Foundry Agent backed by GPT-4o
- Attaches the Day 3 Azure AI Search index via ``AzureAISearchTool``
- Runs multi-turn conversations in a managed thread
- Returns structured ``AgentResponse`` objects with content and citations

Usage::

    from foundry import FoundryRagAgent

    agent = FoundryRagAgent.from_settings(settings, factory)
    response = agent.ask("What are the key features of Azure AI Foundry?")
    print(response.content)
    for citation in response.citations:
        print(citation)
"""

from foundry.evaluation import evaluate_response
from foundry.rag_agent import AgentResponse, FoundryRagAgent

__all__ = ["FoundryRagAgent", "AgentResponse", "evaluate_response"]
