---
id: 20251203-001
title: Amend Constitution v1.1.0
stage: constitution
date: 2025-12-03
surface: CLI
model: claude-sonnet-4-5-20250929
feature: constitution
branch: 001-ch2-embodied-intelligence
user: user
command: /sp.constitution
labels: [docs, constitution, update]
links:
  spec:
  ticket:
  adr:
  pr:
files:
  - path: .specify/memory/constitution.md
    action: modified
tests:

---

## Prompt

```text
Here are the Rules for the Constitution:

Project Vision:

Build an "AI-Native Interactive Book" using Docusaurus (Frontend) and FastAPI (Backend).
The system MUST include a RAG Chatbot powered by OpenAI Agents SDK and Qdrant Vector DB.
Users must be able to select text on the book to ask context-aware questions.
Mandatory Tech Stack (No Deviations):

Frontend: Docusaurus 3.9 (Classic Template), React for Chat Widget.
Backend: Python 3.10+, FastAPI, Uvicorn.
AI/Logic: OpenAI Agents SDK (or ChatKit), Gemini 1.5 Flash (via Router) for generation.
Database: Qdrant Cloud (Free Tier) for Vector Storage.
Spec-Driven Development (SDD) Mandate:

Workflow: Always ask "Have we specified this?" -> Run sp.specify -> Run sp.plan -> Run sp.implement.
The "Matrix" Protocol (Bonus Marks Strategy):

Prioritize "Reusable Intelligence" over hardcoded logic.
Whenever a repetitive task is identified (e.g., Ingesting books to DB, Deploying to GitHub), you must create a reusable Python script in the skills/ folder (e.g., skills/librarian.py, skills/publisher.py).
These skills should be treated as "Agent Skills" that can be invoked via CLI.
Deployment Standards:

The book must be deployable to GitHub Pages.
Code must be modular and clean.
Please generate the full content of .specify/memory/constitution.md now.
```

## Response snapshot

```text
The project constitution has been updated to version 1.1.0. This is a minor version bump due to significant changes, including a new project vision, mandatory tech stack, and development principles.

Files requiring manual follow-up for consistency include:
*   `.specify/templates/plan-template.md`
*   `.specify/templates/spec-template.md`
*   `.specify/templates/tasks-template.md`

Additionally, the `RATIFICATION_DATE` in the constitution still needs to be set.
```

## Outcome

- ✅ Impact: Constitution updated successfully with new project vision and principles.
- 🧪 Tests: N/A
- 📁 Files: 1 file modified: .specify/memory/constitution.md
- 🔁 Next prompts: User should review the updated constitution and proceed with spec-driven development.
- 🧠 Reflection: PHR script not found, manually created PHR file.

## Evaluation notes (flywheel)

- Failure modes observed: PHR script not found.
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
