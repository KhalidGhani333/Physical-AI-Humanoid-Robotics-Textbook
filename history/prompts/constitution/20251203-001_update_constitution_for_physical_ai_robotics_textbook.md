---
id: 20251203-001
title: Update constitution for Physical AI Robotics Textbook
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
Textbook for Teaching Physical AI & Humanoid Robotics Course
 The Course Details
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
Capstone Project: The Autonomous Humanoid. A final project where a simulated robot receives a voice command, plans a path, navigates obstacles, identifian object using computer vision, and manipulates it.
es
```

## Response snapshot

Updated `.specify/memory/constitution.md` to version 2.0.0. Replaced project vision and core principles with content for 'Textbook for Teaching Physical AI & Humanoid Robotics Course'. Noted pending updates for plan, spec, and tasks templates.

## Outcome

- ✅ Impact: Updated project constitution with new course details.
- 🧪 Tests: N/A
- 📁 Files: Updated 1 file: `.specify/memory/constitution.md`. 4 templates marked for pending updates.
- 🔁 Next prompts:
- 🧠 Reflection: Successfully updated the constitution based on user input, including a major version bump and a sync impact report. Manual PHR creation was required due to script failure.

## Evaluation notes (flywheel)

- Failure modes observed: `create-phr.sh` script failed.
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Investigate `create-phr.sh` script execution path or permission issues.
