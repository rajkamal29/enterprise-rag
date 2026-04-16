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

## ADR-3: Azure AI Search for Production Retrieval
Decision: Use Azure AI Search hybrid query (keyword + vector + semantic reranker) as the retrieval layer.  
Reason: Hybrid outperforms pure vector by 20-40% on enterprise datasets. Semantic reranker is managed, not DIY.

## ADR-4: LangGraph for Agent Orchestration
Decision: Use LangGraph over bare LangChain chains or AutoGen.  
Reason: LangGraph provides explicit stateful nodes, branching, and cycles. Agent steps are testable individually. AutoGen is less deterministic for production use cases.

## ADR-5: OpenTelemetry for Observability
Decision: Instrument every LangGraph node as an OpenTelemetry span. Export to Azure Application Insights.  
Reason: Standard protocol, vendor-neutral, works with Azure Monitor. You cannot debug an agent you cannot trace.

## ADR-6: RAGAS as a CI Evaluation Gate
Decision: Run RAGAS (faithfulness, answer relevance, context precision) as a CI step that fails on score regression.  
Reason: Retrieval quality is a functional requirement, not a nice-to-have. Treat it like a test suite.

## ADR-7: Azure Container Apps over AKS
Decision: Deploy to Azure Container Apps, not Azure Kubernetes Service.  
Reason: ACA provides KEDA autoscaling, built-in ingress, and Managed Identity without cluster management overhead. AKS is appropriate when GPU nodes, custom networking, or multi-tenant isolation is needed.

## ADR-8: Multi-Agent Planner Pattern
Decision: Use a Planner + Specialist agent pattern for complex queries.  
Reason: Single ReAct agents hit reasoning limits on multi-part enterprise queries. Specialisation improves accuracy and parallel execution reduces latency.

## ADR-9: Azure Document Intelligence for Ingestion
Decision: Use Azure Document Intelligence SDK for document parsing, not raw PDF libraries.  
Reason: Handles tables, forms, multi-column layouts, and mixed-media documents that break naive text extractors.

## ADR-10: Cost Governance per Agent Step
Decision: Track token usage and estimated cost at every tool call and LLM invocation.  
Reason: Agentic loops with multiple LLM calls can produce unbounded costs. Token budgets and per-step cost alerts are required in enterprise deployments.
