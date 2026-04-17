# Architecture Decision Records (ADR)

## ADR-0: Guardrails First
Decision: Build input/output validation and safety checks before any agent or retrieval features.  
Reason: Prevents prompt injection, bad context, and unsafe responses from entering the system.

## ADR-1: Azure AI Content Safety over Custom Filters
Decision: Use Azure AI Content Safety for harmful content screening on inputs and outputs.  
Reason: Microsoft-managed, regularly updated harm categories. Do not build bespoke profanity filters.

## ADR-2: Managed Identity, Zero Secrets in Code
Decision: Use DefaultAzureCredential everywhere. All connection strings in Azure Key Vault.  
Reason: Eliminates secret rotation risk, works identically in local dev, CI, and Azure Container Apps.

## ADR-3: Dual-Track Delivery
Decision: Build both an Azure AI Foundry end-to-end workflow and an Azure-based custom Agentic RAG path in the same portfolio plan.  
Reason: The two approaches solve different enterprise needs. Foundry accelerates managed delivery and governance; the custom path demonstrates deeper orchestration and runtime control.

## ADR-4: Azure AI Search for Production Retrieval
Decision: Use Azure AI Search hybrid query (keyword + vector + semantic reranker) as the retrieval layer.  
Reason: Hybrid outperforms pure vector by 20-40% on enterprise datasets. Semantic reranker is managed, not DIY.

## ADR-5: LangGraph for the Custom Orchestration Path
Decision: Use LangGraph as the primary framework for the custom Azure-based track.  
Reason: LangGraph provides explicit stateful nodes, branching, and cycles. It complements the AI Foundry managed path by exposing the orchestration tradeoffs directly in code.

## ADR-6: OpenTelemetry for Observability
Decision: Instrument every LangGraph node as an OpenTelemetry span. Export to Azure Application Insights.  
Reason: Standard protocol, vendor-neutral, works with Azure Monitor. You cannot debug an agent you cannot trace.

## ADR-7: Dual Evaluation Strategy
Decision: Use AI Foundry evaluation features for the managed path and RAGAS or custom CI gates for the custom path.  
Reason: Evaluation should be native to each orchestration surface so tradeoffs are measured fairly.

## ADR-8: Azure Container Apps over AKS
Decision: Deploy to Azure Container Apps, not Azure Kubernetes Service.  
Reason: ACA provides KEDA autoscaling, built-in ingress, and Managed Identity without cluster management overhead. AKS is appropriate when GPU nodes, custom networking, or multi-tenant isolation is needed.

## ADR-9: Multi-Agent Planner Pattern
Decision: Use a Planner + Specialist agent pattern for complex queries.  
Reason: Single ReAct agents hit reasoning limits on multi-part enterprise queries. Specialisation improves accuracy and parallel execution reduces latency.

## ADR-10: Azure Document Intelligence for Ingestion
Decision: Use Azure Document Intelligence SDK for document parsing, not raw PDF libraries.  
Reason: Handles tables, forms, multi-column layouts, and mixed-media documents that break naive text extractors.

## ADR-11: Cost Governance per Agent Step
Decision: Track token usage and estimated cost at every tool call and LLM invocation.  
Reason: Agentic loops with multiple LLM calls can produce unbounded costs. Token budgets and per-step cost alerts are required in enterprise deployments.

## ADR-12: Day 10 as the Architecture Synthesis Day
Decision: Reserve the final day for a full topic refresh and tradeoff compendium across both tracks.  
Reason: Senior architecture interviews and stakeholder reviews require decision guidance, not just implementation artifacts.
