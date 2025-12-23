<!-- SYNC IMPACT REPORT:
Version change: N/A → 1.0.0
Modified principles: N/A (new constitution)
Added sections: All sections (new constitution)
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ updated
  - .specify/templates/spec-template.md ✅ updated
  - .specify/templates/tasks-template.md ✅ updated
  - .specify/templates/commands/*.md ⚠ pending
Follow-up TODOs: None
-->

# RAG Chatbot Constitution

## Core Principles

### I. Grounded Responses
The chatbot must only answer using retrieved content from authorized book content or user-selected text; no hallucinations or generation beyond provided context. This ensures factual accuracy and prevents the system from fabricating information.

### II. Selection-Bound Reasoning
When user-selected text is provided, answers must be strictly limited to that text, overriding all other retrieval sources. This creates a bounded reasoning environment where the system cannot draw from broader knowledge.

### III. Model Independence
Agent logic must remain model-agnostic, using Gemini via API as the LLM provider. Implementation should abstract LLM provider details to enable potential future model changes while maintaining current Gemini API requirement.

### IV. Transparency
Retrieval sources must be traceable and debuggable. All responses must cite retrieved chunks internally, allowing users and developers to understand the origin of answers and verify accuracy against source material.

### V. Security by Design
User data, content boundaries, and access controls must be enforced at all system layers. No storage of user queries beyond session scope, environment-based API key management, rate limiting, and input validation are required.

### VI. Deterministic Processing
Embeddings must be deterministic and reproducible, ensuring consistent retrieval behavior. Text chunking, preprocessing, and vector generation processes must produce identical results for identical inputs across system restarts.

## Technical Standards

Backend: FastAPI (async, modular architecture) with clear separation between ingestion, retrieval, and generation layers. LLM: Gemini API exclusively (no OpenAI model usage). Agents: OpenAI Agents / ChatKit SDK for orchestration only. Metadata Storage: Neon Serverless Postgres. Vector Search: Qdrant Cloud Free Tier. All architectural decisions must maintain these technology constraints.

## RAG Implementation Rules

All responses must cite retrieved chunks internally with source attribution. Zero-response policy if retrieval returns no relevant content - the system must not generate answers without adequate context. Selected-text mode overrides all other retrieval sources. Context window limits must be enforced explicitly to prevent token overflow errors.

## Data & Security Requirements

No storage of user queries beyond session scope. Environment-based API key management with secure vault integration. Rate limiting and input validation required at all entry points. No cross-book or cross-user data leakage - strict isolation between different content sets and user sessions.

## Quality & Validation Standards

Accuracy: Answers must be verifiable against source text with clear citation. Consistency: Same input yields same retrieval set with deterministic behavior. Latency: Optimized for near real-time interaction with sub-second response targets. UX: Clear indication of answer source and limits, with transparent communication about system boundaries.

## Governance

This constitution supersedes all other development practices for the RAG chatbot project. All implementation must comply with these principles. Amendments require formal documentation and team approval with migration plan for existing code. All PRs and reviews must verify compliance with grounding, security, and transparency requirements.

**Version**: 1.0.0 | **Ratified**: 2025-12-14 | **Last Amended**: 2025-12-14
