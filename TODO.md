# TODO

## Priority Plan

### Must Do This Week

- [ ] Finalize resume project section with quantified outcomes and architecture bullets.
- [ ] Prepare and rehearse 30-second and 2-minute interview pitches.
- [ ] Practice answers for top architecture tradeoff questions (Foundry vs LangGraph, ACA/APIM vs AKS, RBAC fixes, CI/smoke risk controls).
- [ ] Publish first 3 LinkedIn posts:
  - [ ] Project launch story
  - [ ] Why two tracks: Foundry vs custom
  - [ ] Deployment reality: failures and fixes
- [ ] Collect and store portfolio evidence links/screenshots (CI pass, APIM health/ask validation, ADR references).

### Nice to Have Later

- [ ] Complete full 6-week LinkedIn content calendar (remaining 15 posts).
- [ ] Run additional mock interviews focused on incident/debugging scenarios.
- [ ] Iterate LinkedIn content based on engagement metrics.
- [ ] Keep optional operational follow-through evidence up to date after each infra change.

## 7-Day Execution Checklist

### Day 1 - Resume Foundation

- [ ] Finalize project title and one-line summary for resume.
- [ ] Add 4-6 quantified bullets (tests, CI gates, deployment, architecture decisions).
- [ ] Tailor keywords for Solution Architect roles.

### Day 2 - Interview Pitch and Storyline

- [ ] Rehearse 30-second elevator pitch 5 times.
- [ ] Rehearse 2-minute deep-dive pitch 3 times.
- [ ] Prepare STAR examples for 2 incidents (deployment failure and RBAC auth failure).

### Day 3 - LinkedIn Post 1 + Evidence

- [ ] Publish: Project launch story.
- [ ] Attach one architecture visual or concise outcomes screenshot.
- [ ] Save engagement notes (comments/questions to answer later).

### Day 4 - LinkedIn Post 2 + Mock Interview

- [ ] Publish: Foundry vs LangGraph tradeoff post.
- [ ] Run one architecture-focused mock interview.
- [ ] Record weak answers and improve them in TODO.

### Day 5 - LinkedIn Post 3 + Ops Proof

- [ ] Publish: Deployment reality/fixes post.
- [ ] Capture CI and APIM validation evidence links/screenshots.
- [ ] Prepare concise explanation of APIM + ACA + Managed Identity design choices.

### Day 6 - Incident and System Design Readiness

- [ ] Practice incident/debugging Q&A (auth, gateway policy, scaling, rollout).
- [ ] Practice NFR/DR explanation using Day 10 matrix and ADR decisions.
- [ ] Prepare one whiteboard-style architecture walkthrough.

### Day 7 - Final Polish + Application Pack

- [ ] Final resume proofread and role-specific versioning.
- [ ] Final LinkedIn profile update with project and key outcomes.
- [ ] Compile "interview quick sheet" (pitch + top 10 Q&A + architecture decision highlights).

## Interview Preparation

- [ ] Prepare a 30-second project pitch (problem, approach, outcome).
- [ ] Prepare a 2-minute deep-dive version for architecture interviews.
- [ ] Practice answers for:
  - [ ] Why Azure AI Foundry vs custom LangGraph?
  - [ ] Why ACA + APIM over AKS?
  - [ ] How identity/RBAC issues were diagnosed and fixed.
  - [ ] How quality gates and smoke tests reduce production risk.
- [ ] Run one mock interview focused on architecture tradeoffs.
- [ ] Run one mock interview focused on incident/debugging scenarios.

## Resume Updates

- [ ] Add project entry: Enterprise Agentic RAG on Azure.
- [ ] Include quantified outcomes (103 tests passing, CI gates, secured APIM/ACA deployment).
- [ ] Add architecture bullets (dual-track strategy, ADRs, NFR/DR baselines).
- [ ] Tailor resume bullets for Solution Architect role keywords.
- [ ] Create a concise 4-line project summary for recruiter scans.

## LinkedIn Content Backlog

- [ ] Project launch story (10-day dual-track build and objective).
- [ ] Why two tracks: Azure AI Foundry vs custom LangGraph.
- [ ] Azure foundation architecture decisions.
- [ ] Ingestion design tradeoffs (chunking, embedding, indexing).
- [ ] Agent orchestration evolution (single-agent to planner-router).
- [ ] Evaluation gate as CI quality control.
- [ ] Observability design with OpenTelemetry.
- [ ] Responsible AI guardrails in runtime.
- [ ] Deployment reality: failures, fixes, and lessons learned.
- [ ] Managed Identity and RBAC troubleshooting playbook.
- [ ] APIM for AI workloads (auth, throttling, quota, policy).
- [ ] Production hardening checklist (probes, autoscale, smoke checks).
- [ ] NFRs for Agentic RAG (latency, availability, error budget).
- [ ] DR options (single-region vs active-passive vs active-active).
- [ ] Cost optimization levers (model choice, top-k, caching).
- [ ] Final architecture synthesis (when-to-use-what matrix).
- [ ] Interview reflection post (top architect questions answered).
- [ ] Portfolio wrap-up post with final outcomes.

## LinkedIn Publishing Plan

- [ ] Post 3 times/week for 6 weeks (Tue/Thu/Sat).
- [ ] Use this structure for each post:
  - [ ] Hook
  - [ ] Problem
  - [ ] Approach
  - [ ] Tradeoff
  - [ ] Evidence
  - [ ] CTA
- [ ] Track engagement and iterate topic order.

## Portfolio Evidence Checklist

- [ ] Capture screenshot/link of successful CI run.
- [ ] Capture screenshot/link of APIM `/rag/health` and `/rag/ask` validation.
- [ ] Capture deployment evidence for ACA/APIM hardening update.
- [ ] Keep ADR references ready for interviews.

## Optional Operational Follow-through

- [ ] Apply latest infrastructure hardening to Azure runtime if not already applied.
- [ ] Trigger `Post-Deploy Smoke Test` workflow from GitHub Actions.
- [ ] Store workflow run URL in tracker for final evidence.
