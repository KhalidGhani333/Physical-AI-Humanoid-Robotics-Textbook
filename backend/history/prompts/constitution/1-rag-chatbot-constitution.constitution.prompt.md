---
id: 1
title: RAG Chatbot Constitution
stage: constitution
date: 2025-12-14
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: main
user: claude
command: /sp.constitution
labels: [constitution, rag, chatbot, grounding, security]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - .specify/memory/constitution.md
tests:
 - none
---

## Prompt

```
/sp.constitution Project: Integrated RAG Chatbot for Embedded Digital Content

Purpose:
Define a stable, project-wide constitution for building an embedded Retrieval-Augmented Generation (RAG) chatbot that answers user questions strictly from authorized book content or user-selected text.

Core Principles:
- Grounded Responses: The chatbot must only answer using retrieved content; no hallucinations.
- Selection-Bound Reasoning: When user-selected text is provided, answers must be strictly limited to that text.
- Model Independence: Agent logic must remain model-agnostic, using Gemini via API as the LLM provider.
- Transparency: Retrieval sources must be traceable and debuggable.
- Security by Design: User data, content boundaries, and access controls must be enforced.

Scope:
- Ingestion and indexing of book content
- Text chunking, embedding, and vector storage
- Query-time retrieval and answer synthesis
- Selected-text-only answering mode
- Embedded chatbot UX within a digital book or website

Out of Scope:
- Content authoring or editing
- Training custom foundation models
- Non-book or external internet search
- Analytics beyond basic usage metrics

Technical Standards:
- Backend: FastAPI (async, modular architecture)
- LLM: Gemini API (no OpenAI model usage)
- Agents: OpenAI Agents / ChatKit SDK for orchestration only
- Metadata Storage: Neon Serverless Postgres
- Vector Search: Qdrant Cloud Free Tier
- Embeddings must be deterministic and reproducible
- Clear separation between ingestion, retrieval, and generation layers

RAG Rules:
- All responses must cite retrieved chunks internally
- Zero-response policy if retrieval returns no relevant content
- Selected-text mode overrides all other retrieval sources
- Context window limits must be enforced explicitly

Data & Security:
- No storage of user queries beyond session scope
- Environment-based API key management
- Rate limiting and input validation required
- No cross-book or cross-user data leakage

Quality & Validation:
- Accuracy: Answers must be verifiable against source text
- Consistency: Same input yields same retrieval set
- Latency: Optimized for near real-time interaction
- UX: Clear indication of answer source and limits

Success Criteria:
- Chatbot never answers outside retrieved context
- Selected-text-only queries are fully respected
- System is production-deployable and maintainable
- Specification is sufficient for direct engineering implementation
```

## Response snapshot

Created a comprehensive constitution for the RAG chatbot project that captures all specified principles and requirements. The constitution defines six core principles (Grounded Responses, Selection-Bound Reasoning, Model Independence, Transparency, Security by Design, and Deterministic Processing), along with sections for Technical Standards, RAG Implementation Rules, Data & Security Requirements, Quality & Validation Standards, and Governance. The constitution ensures the system adheres to the grounding requirements and security constraints while maintaining deterministic behavior and transparency.

## Outcome

- ✅ Impact: Created foundational constitution document that will guide all future development of the RAG chatbot system
- 🧪 Tests: none
- 📁 Files: Updated .specify/memory/constitution.md with the new constitution
- 🔁 Next prompts: Implementation planning and task breakdown can now proceed based on this constitution
- 🧠 Reflection: The constitution successfully captures all specified requirements and provides clear guidance for implementation

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Begin implementation planning based on the established constitution