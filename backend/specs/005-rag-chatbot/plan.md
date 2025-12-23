# Implementation Plan: Integrated RAG Chatbot for Digital Book / Website (Gemini-based)

**Branch**: `005-rag-chatbot` | **Date**: 2025-12-14 | **Spec**: [specs/005-rag-chatbot/spec.md](D:\Textbook-Physical-AI-Humanoid-Robotics\backend\specs\005-rag-chatbot\spec.md)
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implementation of a RAG chatbot system that enables users to ask questions about digital book content with strict content boundary enforcement. The system will support both full-content RAG mode and a selected-text-only mode where responses are constrained to user-selected text only. Built with FastAPI backend, Qdrant vector database, and Google Gemini API.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastAPI, Qdrant client, Cohere embeddings, Neon Postgres driver, Google Gemini API
**Storage**: Qdrant Cloud (vector DB), Neon Serverless Postgres (metadata)
**Testing**: pytest with integration and unit tests
**Target Platform**: Linux server (cloud deployment)
**Project Type**: Backend API service (web)
**Performance Goals**: <3 seconds response time for chat queries, 95% success rate for content retrieval
**Constraints**: Must use Gemini API (not OpenAI), strict content boundary enforcement, selected-text-only mode capability
**Scale/Scope**: Support 100+ concurrent users, handle book-sized content corpora, maintain conversation state

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on the constitution (D:\Textbook-Physical-AI-Humanoid-Robotics\.specify\memory\constitution.md):
- ✅ Uses mandated tech stack: Python 3.10+, FastAPI (from 2.5)
- ✅ Uses Qdrant Cloud for vector storage (from 2.5)
- ✅ Uses Gemini API as required (from spec and 2.5)
- ✅ Follows SDD mandate (from 2.6)
- ✅ Content boundary enforcement aligns with project purpose (1.1)

## Project Structure

### Documentation (this feature)

```text
specs/005-rag-chatbot/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── content.py      # Content chunk and metadata models
│   │   ├── conversation.py # Conversation session models
│   │   └── chat.py         # Chat message models
│   ├── services/
│   │   ├── ingestion.py    # Content ingestion and processing
│   │   ├── retrieval.py    # Vector search and retrieval
│   │   ├── chat.py         # Chat completion service
│   │   ├── embedding.py    # Embedding generation service
│   │   └── storage.py      # Database interaction services
│   ├── api/
│   │   ├── v1/
│   │   │   ├── content.py  # Content ingestion endpoints
│   │   │   ├── chat.py     # Chat completion endpoints
│   │   │   └── retrieval.py # Retrieval endpoints
│   │   └── deps.py         # Dependency injection
│   └── main.py             # Application entry point
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── requirements.txt
```

**Structure Decision**: Backend API service with clear separation of concerns between models, services, and API layers following FastAPI best practices.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |