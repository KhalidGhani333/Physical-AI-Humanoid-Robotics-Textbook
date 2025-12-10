---
id: PHR-20251129-001
title: Generate Physical AI Robotics Constitution
stage: constitution
date: 2025-11-29
surface: CLI
model: claude-sonnet-4-5-20250929
feature: N/A
branch: master
user: User
command: /sp.constitution
labels: [docs, governance, initialization]
links:
  spec: N/A
  ticket: N/A
  adr: N/A
  pr: N/A
files:
- path: .specify/memory/constitution.md
  status: modified
tests: N/A
---

## Prompt

Generate a complete Project Constitution for the textbook project “Physical AI & Humanoid Robotics,”
strictly following the Spec-Kit Plus Constitution Phase standards from the referenced methodology.
Create a project-wide rulebook that remains stable unless formally amended. Include the project purpose,
project vision, in-scope and out-of-scope boundaries, core definitions related to Physical AI, humanoid robotics,
embodied intelligence, intelligent agents, and robot–AI interaction; core principles guiding all decisions;
key standards for writing, accuracy, pedagogy, and scientific rigor; global constraints across content,
formatting, terminology, and robotics/AI correctness; success criteria for the completed textbook;
universal writing and content development guidelines; technical and robotics standards for diagrams,
mathematical notation, control systems representation, and hardware/software architecture accuracy;
naming conventions for chapters, diagrams, examples, and terminology; rules for visuals and illustrations;
research-grade referencing and citation requirements; validation, peer-review, and scientific accuracy rules;
safety, ethics, and integrity expectations; contribution and collaboration guidelines for all authors;
and a formal amendment policy. Ensure the entire Constitution aligns with SDD’s principles, is unambiguous,
actionable, and applies uniformly across the full textbook project. /n The Course Details
Physical AI & Humanoid Robotics
Focus and Theme: AI Systems in the Physical World. Embodied Intelligence.
Goal: Bridging the gap between the digital brain and the physical body. Students apply their AI knowledge to control Humanoid Robots in simulated and real-world environments.
Quarter Overview
The future of AI extends beyond digital spaces into the physical world. This capstone quarter introduces Physical AI—AI systems that function in reality and comprehend physical laws. Students learn to design, simulate, and deploy humanoid robots capable of natural human interactions using ROS 2, Gazebo, and NVIDIA Isaac.
Module 1: The Robotic Nervous System (ROS 2)
Focus: Middleware for robot control.
ROS 2 Nodes, Topics, and Services.
Bridging Python Agents to ROS controllers using rclpy.
Understanding URDF (Unified Robot Description Format) for humanoids.


Module 2: The Digital Twin (Gazebo & Unity)
Focus: Physics simulation and environment building.
Simulating physics, gravity, and collisions in Gazebo.
High-fidelity rendering and human-robot interaction in Unity.
Simulating sensors: LiDAR, Depth Cameras, and IMUs.


Module 3: The AI-Robot Brain (NVIDIA Isaac™)
Focus: Advanced perception and training.
NVIDIA Isaac Sim: Photorealistic simulation and synthetic data generation.
Isaac ROS: Hardware-accelerated VSLAM (Visual SLAM) and navigation.
Nav2: Path planning for bipedal humanoid movement.


Module 4: Vision-Language-Action (VLA)
Focus: The convergence of LLMs and Robotics.
Voice-to-Action: Using OpenAI Whisper for voice commands.
Cognitive Planning: Using LLMs to translate natural language ("Clean the room") into a sequence of ROS 2 actions.
Capstone Project: The Autonomous Humanoid. A final project where a simulated robot receives a voice command, plans a path, navigates obstacles, identifies an object using computer vision, and manipulates it.

## Response snapshot

Read the existing constitution template. Generated a comprehensive project constitution for "Physical AI & Humanoid Robotics" by extracting details from the user's prompt. This included defining project overview, scope, core definitions, principles, content standards, technical standards, naming conventions, quality/review, collaboration, and governance. The constitution was then written to `.specify/memory/constitution.md`. Attempted to check consistency with `.specify/scripts/bash/` and `.specify/templates/commands/` but these directories were not found. Identified `website/` but no `README.md` or `docs/` in the root. Read `plan-template.md`, `spec-template.md`, and `tasks-template.md`. Updated the Sync Impact Report within `constitution.md` to reflect the status of template checks and missing directories/files. Created the PHR directory and wrote the PHR.

## Outcome

- ✅ Impact: Generated a comprehensive project constitution.
- 🧪 Tests: N/A
- 📁 Files: 1 file created/modified (.specify/memory/constitution.md). 1 PHR created (history/prompts/constitution/PHR-20251129-001_generate_physical_ai_robotics_constitution.md).
- 🔁 Next prompts: Manual follow-up for template updates.
- 🧠 Reflection: Successfully generated constitution by extracting details from user prompt and adapting template. Noted missing project directories and files during consistency checks, which impacted the thoroughness of the consistency propagation checklist.

## Evaluation notes (flywheel)

- Failure modes observed: N/A
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
