---
id: 20251203-002
title: Add tech stack and development principles to constitution
stage: constitution
date: 2025-12-03
surface: CLI
model: claude-sonnet-4-5-20250929
feature:
branch: 001-ch2-embodied-intelligence
user: system
command: /sp.constitution
labels: [docs, constitution, update]
links:
  spec:
  ticket:
  adr:
  pr:
files:
- .specify/memory/constitution.md
- .specify/templates/plan-template.md
- .specify/templates/spec-template.md
- .specify/templates/tasks-template.md
- .specify/templates/commands/sp.constitution.md
tests:

---

## Prompt

```text
also add this rule in constitution.

Project Vision:

Build an "Physical AI & Humanoid Robotics" using Docusaurus (Frontend) and FastAPI (Backend).
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
```

## Response snapshot

Updated `.specify/memory/constitution.md` to version 2.1.0. Refined project vision and added new core principles for tech stack, SDD, Matrix Protocol, and Deployment Standards. Noted pending updates for plan, spec, and tasks templates.

## Outcome

- ✅ Impact: Updated project constitution with new core principles and refined project vision.
- 🧪 Tests: N/A
- 📁 Files: Updated 1 file: `.specify/memory/constitution.md`. 4 templates marked for pending updates.
- 🔁 Next prompts:
- 🧠 Reflection: Successfully updated the constitution based on user input, including a minor version bump and a sync impact report. Manual PHR creation was required due to script failure.

## Evaluation notes (flywheel)

- Failure modes observed: `create-phr.sh` script failed.
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Investigate `create-phr.sh` script execution path or permission issues.
