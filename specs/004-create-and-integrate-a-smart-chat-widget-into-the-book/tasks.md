# Task Checklist: Smart Chat Widget

**Feature**: Smart Chat Widget
**Branch**: 004-create-and-integrate-a-smart-chat-widget-into-the-book
**Spec**: D:\Textbook-Physical-AI-Humanoid-Robotics\specs\004-create-and-integrate-a-smart-chat-widget-into-the-book\spec.md
**Plan**: D:\Textbook-Physical-AI-Humanoid-Robotics\specs\004-create-and-integrate-a-smart-chat-widget-into-the-book\plan.md

**Generated**: 2025-12-16
**Status**: TODO

**Implementation Strategy**: MVP approach focusing on User Story 1 (core chat functionality) first, then enhancing with context features (User Story 2) and history (User Story 3).

## Dependencies

- User Story 2 [US2] depends on User Story 1 [US1] completion (text selection logic)
- User Story 3 [US3] depends on User Story 1 [US1] completion (message handling)

## Parallel Execution Examples

- UI implementation [US1] and API integration [US1] can run in parallel
- Backend CORS update can run in parallel with frontend development
- CSS module styling can run in parallel with component logic implementation

---

## Phase 1: Setup

- [X] T001 Create component directory structure at website/src/components/chatUI/
- [X] T002 Create utility directory structure at website/src/utils/
- [X] T003 Verify Docusaurus project exists at website/ directory

---

## Phase 2: Foundational

- [X] T004 [P] Create text selection utility at website/src/utils/textSelection.ts
- [X] T005 [P] Create CSS module file at website/src/components/chatUI/chatWidget.module.css
- [X] T006 [P] Create main ChatWidget component file at website/src/components/chatUI/ChatWidget.tsx
- [X] T007 Update backend/main.py to enable CORS for localhost:3000

---

## Phase 3: User Story 1 - Access Chat Widget (Priority: P1)

**Goal**: Implement core chat widget functionality with floating button and chat window

**Independent Test**: Can be fully tested by clicking the floating button and verifying the chat window opens and closes properly, delivering the ability to interact with the chat interface.

**Tasks**:

- [X] T008 [US1] Implement ChatWidget component structure with floating button and hidden chat window
- [X] T009 [US1] Add state management for chat window open/close in ChatWidget.tsx
- [X] T010 [US1] Implement click handler for floating chat button to toggle chat window visibility
- [X] T011 [US1] Add keyboard accessibility for chat widget (ESC to close, Enter to submit)
- [X] T012 [US1] Style floating action button with chat icon (💬) using CSS module
- [X] T013 [US1] Style chat window with input field and message history area using CSS module
- [X] T014 [US1] Implement close functionality for chat window (X button, click outside)
- [X] T015 [US1] Test chat widget visibility toggling on different pages

---

## Phase 4: User Story 2 - Send Messages with Context (Priority: P1)

**Goal**: Implement selected text detection and context sending functionality

**Independent Test**: Can be fully tested by selecting text on the page, opening the chat, and verifying that the context badge appears and the selected text is sent to the backend.

**Tasks**:

- [X] T016 [US2] Enhance textSelection.ts to detect and return selected text using window.getSelection()
- [X] T017 [US2] Add state management for selected text in ChatWidget.tsx
- [X] T018 [US2] Implement effect to check for selected text when component mounts and on selection change
- [X] T019 [US2] Add "Context found" badge to chat window UI when text is selected
- [X] T020 [US2] Create API service function to communicate with backend chat API
- [X] T021 [US2] Implement message sending functionality with selected_context parameter
- [X] T022 [US2] Style context badge to indicate selected text is available
- [X] T023 [US2] Test text selection detection and context badge display
- [X] T024 [US2] Test sending messages with selected context to backend

---

## Phase 5: User Story 3 - View Chat History and Responses (Priority: P2)

**Goal**: Implement message history display with distinct styling and loading indicators

**Independent Test**: Can be fully tested by sending messages and verifying that user messages appear in one style, bot responses appear in another style, and loading states are properly indicated.

**Tasks**:

- [X] T025 [US3] Define ChatMessage interface based on data model in ChatWidget.tsx
- [X] T026 [US3] Add message history state management in ChatWidget.tsx
- [X] T027 [US3] Implement message display UI with distinct styling for user vs bot messages
- [X] T028 [US3] Add loading state management for "Thinking..." indicator
- [X] T029 [US3] Display "Thinking..." indicator when waiting for backend response
- [X] T030 [US3] Implement message history scroll to bottom on new messages
- [X] T031 [US3] Style user messages with right alignment and different background
- [X] T032 [US3] Style bot messages with left alignment and different background
- [X] T033 [US3] Test message history display with user and bot messages
- [X] T034 [US3] Test loading indicator during message processing

---

## Phase 6: Integration

- [X] T035 Import and use <ChatWidget /> in the Docusaurus Layout/Root component
- [X] T036 Verify chat widget appears on all documentation pages
- [X] T037 Test chat functionality across different documentation pages
- [X] T038 Verify no CSS conflicts with existing Docusaurus theme

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T039 Add error handling for API communication failures
- [X] T040 Implement error display in chat interface
- [X] T041 Add input validation for message text
- [X] T042 Implement rate limiting to prevent spam requests
- [X] T043 Add accessibility attributes (ARIA labels) to chat components
- [X] T044 Test chat functionality and text selection on different browsers
- [X] T045 Test responsive design on mobile and tablet devices
- [X] T046 Add loading states for initial component rendering
- [X] T047 Implement session management for chat continuity
- [X] T048 Test edge cases: very long selected text, API timeouts, etc.
- [X] T049 Update docusaurus.config.js if needed for proper integration
- [X] T050 Final verification of all user stories and acceptance criteria