<!--
Sync Impact Report:
Version change: 2.0.0 -> 2.1.0
List of modified principles:
- 1.1. Project Purpose (updated)
- 1.2. Project Capabilities (updated)
Added sections:
- 2.5. Mandatory Tech Stack
- 2.6. Spec-Driven Development (SDD) Mandate
- 2.7. The "Matrix" Protocol
- 2.8. Deployment Standards
Removed sections: None.
Templates requiring updates:
- .specify/templates/plan-template.md ⚠ pending
- .specify/templates/spec-template.md ⚠ pending
- .specify/templates/tasks-template.md ⚠ pending
- .specify/templates/commands/sp.constitution.md ✅ updated
Follow-up TODOs: TODO(RATIFICATION_DATE)
-->
# Textbook for Teaching Physical AI & Humanoid Robotics Course Constitution

## 1. Project Vision

### 1.1. Project Purpose
Build an "Physical AI & Humanoid Robotics" using Docusaurus (Frontend) and FastAPI (Backend).
The system MUST include a RAG Chatbot powered by OpenAI Agents SDK and Qdrant Vector DB.
Users MUST be able to select text on the book to ask context-aware questions.
Rationale: To create an interactive learning platform that leverages AI for context-aware Q&A within the physical AI and humanoid robotics domain.

### 1.2. Project Capabilities
Students will apply AI knowledge to control Humanoid Robots in simulated and real-world environments.
Rationale: Ensures students can practically implement AI concepts in physical systems.

## 2. Core Principles

### 2.1. Module 1: The Robotic Nervous System (ROS 2)
Focus: Middleware for robot control.
- ROS 2 Nodes, Topics, and Services.
- Bridging Python Agents to ROS controllers using rclpy.
- Understanding URDF (Unified Robot Description Format) for humanoids.
Rationale: Establishes the foundational communication and control mechanisms for robotics.

### 2.2. Module 2: The Digital Twin (Gazebo & Unity)
Focus: Physics simulation and environment building.
- Simulating physics, gravity, and collisions in Gazebo.
- High-fidelity rendering and human-robot interaction in Unity.
- Simulating sensors: LiDAR, Depth Cameras, and IMUs.
Rationale: Provides tools for safe and iterative development and testing of robotic systems in virtual environments.

### 2.3. Module 3: The AI-Robot Brain (NVIDIA Isaac™)
Focus: Advanced perception and training.
- NVIDIA Isaac Sim: Photorealistic simulation and synthetic data generation.
- Isaac ROS: Hardware-accelerated VSLAM (Visual SLAM) and navigation.
- Nav2: Path planning for bipedal humanoid movement.
Rationale: Equips students with high-performance tools for developing sophisticated AI capabilities for robots.

### 2.4. Module 4: Vision-Language-Action (VLA)
Focus: The convergence of LLMs and Robotics.
- Voice-to-Action: Using OpenAI Whisper for voice commands.
- Cognitive Planning: Using LLMs to translate natural language ("Clean the room") into a sequence of ROS 2 actions.
- Capstone Project: The Autonomous Humanoid. A final project where a simulated robot receives a voice command, plans a path, navigates obstacles, identifies an object using computer vision, and manipulates it.
Rationale: Integrates cutting-edge AI (LLMs) with robotics for intuitive human-robot interaction and advanced autonomous behavior.

### 2.5. Mandatory Tech Stack
The project MUST strictly adhere to the following technology stack with no deviations:
*   **Frontend:** Docusaurus 3.9 (Classic Template), React for Chat Widget.
*   **Backend:** Python 3.10+, FastAPI, Uvicorn.
*   **AI/Logic:** OpenAI Agents SDK (or ChatKit), Gemini 1.5 Flash (via Router) for generation.
*   **Database:** Qdrant Cloud (Free Tier) for Vector Storage.
Rationale: Ensures project consistency, maintainability, and leverages proven technologies.

### 2.6. Spec-Driven Development (SDD) Mandate
The development workflow MUST always follow the sequence: "Have we specified this?" -> Run /sp.specify -> Run /sp.plan -> Run /sp.implement.
Rationale: Enforces a structured, predictable, and traceable development process.

### 2.7. The "Matrix" Protocol
Development MUST prioritize "Reusable Intelligence" over hardcoded logic. Whenever a repetitive task is identified (e.g., Ingesting books to DB, Deploying to GitHub), a reusable Python script MUST be created in the `skills/` folder (e.g., `skills/librarian.py`, `skills/publisher.py`). These skills SHOULD be treated as "Agent Skills" that can be invoked via CLI.
Rationale: Promotes modularity, reusability, and establishes an extensible agent-driven architecture.

### 2.8. Deployment Standards
The interactive book MUST be deployable to GitHub Pages. All code MUST be modular and clean.
Rationale: Ensures public accessibility, maintainability, and adherence to professional coding practices.

## 3. Governance

### 3.1. Amendment Policy
This Constitution can only be amended through a formal proposal process, requiring review and approval by a designated steering committee or lead authors. Proposed amendments MUST include a clear rationale and an impact assessment.

### 3.2. Versioning Policy
The Constitution's versioning MUST follow semantic versioning (MAJOR.MINOR.PATCH).
*   **MAJOR:** Backward incompatible governance changes, principle redefinitions, or significant structural overhauls.
*   **MINOR:** Addition of new principles, sections, or materially expanded guidance.
*   **PATCH:** Clarifications, wording refinements, typo corrections, or non-semantic updates.

### 3.3. Compliance Review
Regular reviews of content development processes against this Constitution MUST be conducted to ensure ongoing adherence to all defined principles and standards. Deviations MUST be documented and remediated.

**Version**: 2.1.0 | **Ratified**: TODO(RATIFICATION_DATE): Original adoption date unknown | **Last Amended**: 2025-12-03
