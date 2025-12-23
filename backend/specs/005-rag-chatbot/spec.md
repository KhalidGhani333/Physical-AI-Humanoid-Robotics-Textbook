# Feature Specification: Integrated RAG Chatbot for Digital Book / Website (Gemini-based)

**Feature Branch**: `005-rag-chatbot`
**Created**: 2025-12-14
**Status**: Draft
**Input**: User description: "Integrated RAG Chatbot for Digital Book / Website (Gemini-based)

Target audience:
- Engineers and AI developers implementing an embedded RAG chatbot
- Product teams integrating contextual AI assistance inside a digital book or website

Project focus:
- Design and specification of an Integrated RAG Chatbot that answers user questions strictly from:
  1) the full book/content corpus
  2) ONLY the text explicitly selected by the user (hard constraint)
- Chatbot will be embedded inside a published digital book or website UI
- LLM provider: Gemini (via Gemini API key), NOT OpenAI models

Success criteria:
- Chatbot never answers outside the provided or selected text context
- Clear separation between full-content RAG mode and selected-text-only mode
- End-to-end architecture is implementable without ambiguity
- Specification is detailed enough for immediate engineering execution
- All components, data flows, and constraints are explicitly defined

Technical stack (must be reflected in the specification):
- Backend: FastAPI (Python)
- LLM: Gemini (Google Gemini API)
- Vector DB: Qdrant Cloud (Free Tier)
  - Cluster ID: 14fb50c8-7092-4dac-b4bb-0307eba15694
  - Endpoint: https://14fb50c8-7092-4dac-b4bb-0307eba15694.us-east-1-1.aws.cloud.qdrant.io
  - QDRANT_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.lfXmYTU5jvExx52sbt8o3d0xnFzAZ2i987Cgg0TTFkk
- Relational DB: Neon Serverless Postgres
  - Neon DB URL:
    postgresql://neondb_owner:npg_kJBYfVSFI40o@ep-fragrant-king-ahlrdz58-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
- Embeddings provider: Cohere
  - COHERE_KEY: QjAOzx3HgGOOKjrY2mYgq9tCLnvQ5Emoi8UrjnSj

Functional requirements:
- Text ingestion pipeline for book / website content
- Chunking strategy and embedding generation
- Storage of vectors in Qdrant and metadata in Neon Postgres
- Retrieval logic based on:
  - full content search
  - user-selected text only (strict isolation)
- Prompt construction logic enforcing context boundaries
- Conversation state handling (session-based)
- API endpoints for:
  - ingestion
  - retrieval
  - chat completion
- Frontend embedding assumptions (API-driven, UI-agnostic)

Non-functional requirements:
- Low latency suitable for in-page chatbot
- Deterministic behavior when selected-text mode is active
- Secure handling of API keys and user input
- Rate limiting and basic abuse protection
- Scalable design compatible with serverless deployment

Architecture & documentation expectations:
- High-level system architecture diagram (described in text)
- Component-level breakdown
- Clear data flow from user input → retrieval → Gemini → response
- Explicit constraints, assumptions, and open questions
- Clear separation of responsibilities between services

Not building:
- No book authoring or publishing system
- No recommendation engine
- No analytics or user tracking beyond basic logging
- No OpenAI-based models or SDKs

Output format:
- Structured technical specification
- Clear section headings
- Precise, unambiguous language
- Ready for direct engineering implementation"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Basic Chatbot Interaction (Priority: P1)

A reader is browsing a digital book or website and wants to ask a question about the content. They can type their question into the embedded chatbot, and receive an answer based on the book's content. The chatbot ensures the answer comes only from the available content and properly cites sources.

**Why this priority**: This is the core value proposition - enabling readers to get answers from the content they're consuming, which improves engagement and comprehension.

**Independent Test**: Can be fully tested by ingesting sample book content, asking questions, and verifying responses are grounded in the provided text with proper citations.

**Acceptance Scenarios**:

1. **Given** book content has been ingested and indexed, **When** user asks a question related to the content, **Then** chatbot returns an answer based on the content with source citations
2. **Given** user asks a question outside the content scope, **When** chatbot processes the query, **Then** chatbot responds that it cannot answer based on the provided content

---

### User Story 2 - Selected Text Only Mode (Priority: P2)

A reader selects specific text in the digital book and asks a question about only that text. The chatbot must provide answers exclusively based on the selected text, ignoring the broader content corpus.

**Why this priority**: This provides a powerful feature for focused analysis of specific passages, allowing users to get detailed information about particular content sections.

**Independent Test**: Can be tested by selecting text, asking questions, and verifying responses are constrained to the selected text only.

**Acceptance Scenarios**:

1. **Given** user has selected specific text in the book, **When** user asks a question in selected-text-only mode, **Then** chatbot returns answers based only on the selected text
2. **Given** user has selected text containing insufficient information for the question, **When** user asks a question in selected-text-only mode, **Then** chatbot indicates it cannot answer based on the selected text only

---

### User Story 3 - Content Ingestion and Management (Priority: P2)

A content administrator needs to ingest book content into the system so readers can ask questions about it. The system must process various content formats and make them available for retrieval.

**Why this priority**: Without content ingestion, the chatbot cannot function, making this essential for the system to work.

**Independent Test**: Can be tested by ingesting sample content and verifying it becomes searchable through the chatbot interface.

**Acceptance Scenarios**:

1. **Given** book content in supported format, **When** administrator initiates ingestion process, **Then** content becomes available for chatbot queries after processing
2. **Given** content ingestion is in progress, **When** system encounters processing errors, **Then** system provides clear error feedback to administrator

---

### User Story 4 - Conversation Context Management (Priority: P3)

A reader engages in a multi-turn conversation with the chatbot, expecting the system to maintain context and provide coherent follow-up responses.

**Why this priority**: This enhances user experience by enabling natural conversation flow rather than isolated question-answer interactions.

**Independent Test**: Can be tested by having multi-turn conversations and verifying the chatbot maintains context appropriately.

**Acceptance Scenarios**:

1. **Given** user asks a follow-up question, **When** chatbot processes the query, **Then** chatbot considers previous conversation context in its response
2. **Given** conversation session has expired, **When** user continues conversation, **Then** chatbot appropriately handles the new context

---

### Edge Cases

- What happens when the selected text is too short to answer a complex question?
- How does system handle queries that require information from multiple content sections but user has selected text-only mode?
- What occurs when content has been updated after initial ingestion but before user query?
- How does system handle very long user queries that exceed API limits?
- What happens when the vector database is temporarily unavailable?

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST allow content ingestion from various text formats (Markdown, HTML, PDF text extracts)
- **FR-002**: System MUST generate embeddings for ingested content using the specified embeddings provider
- **FR-003**: System MUST store embeddings in Qdrant vector database with appropriate metadata
- **FR-004**: System MUST store content metadata in Neon Postgres database
- **FR-005**: System MUST retrieve relevant content based on user queries using vector similarity search
- **FR-006**: System MUST enforce content boundaries - responses must only use ingested content
- **FR-007**: System MUST provide selected-text-only mode that restricts responses to user-selected text only
- **FR-008**: System MUST generate appropriate prompts for the Gemini LLM based on retrieval results
- **FR-009**: System MUST maintain conversation state across multiple interactions in a session
- **FR-010**: System MUST provide API endpoints for content ingestion, retrieval, and chat completion
- **FR-011**: System MUST cite sources for information provided in responses
- **FR-012**: System MUST handle user-selected text input and constrain retrieval to that text in selected-text-only mode
- **FR-013**: System MUST validate that responses are grounded in the provided content context
- **FR-014**: System MUST implement proper error handling and return meaningful error messages
- **FR-015**: System MUST implement rate limiting to prevent abuse of the API

### Key Entities *(include if feature involves data)*

- **Content Chunk**: Represents a segment of ingested book content with associated embedding vector and metadata
- **Conversation Session**: Represents a user's ongoing interaction with the chatbot, maintaining context and history
- **Retrieval Result**: Represents the content fragments retrieved from the vector database based on a query
- **Chat Message**: Represents a single turn in a conversation, including user query and system response

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Users can get accurate answers to content-related questions within 3 seconds of submitting their query
- **SC-002**: 95% of user queries result in responses that are properly grounded in the provided content (no hallucinations)
- **SC-003**: In selected-text-only mode, 100% of responses contain information exclusively from the user-selected text
- **SC-004**: Content ingestion process successfully processes 99% of supported content formats without manual intervention
- **SC-005**: System can handle 100 concurrent users with response times under 5 seconds during peak usage
- **SC-006**: 90% of users find the chatbot responses helpful for understanding the content
- **SC-007**: The system correctly identifies and rejects queries that cannot be answered from the provided content