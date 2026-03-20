# AgentRx – Autonomous Drug Repurposing Intelligence Platform

AgentRx is a multi-agent, orchestrated intelligence system designed to transform fragmented biomedical data into structured, decision-ready insights for drug repurposing.

The platform accepts a molecule as input, coordinates multiple domain-specific research agents, performs cross-domain reasoning, applies deterministic confidence scoring, detects contradictions, validates regulatory feasibility, and generates a structured innovation report.

---

## Overview

Drug research data is distributed across multiple independent sources such as:

* PubMed for scientific literature
* ClinicalTrials.gov for clinical trials
* U.S. Food and Drug Administration for regulatory approvals

AgentRx orchestrates these sources through a modular multi-agent system and synthesizes them into a unified analytical perspective.

---

## Key Features

### Multi-Agent Architecture

* Clinical Agent: Clinical trial retrieval and analysis
* Literature Agent: Scientific paper extraction and reasoning
* Patent Agent: Patent landscape and risk analysis
* Regulatory Agent: Approvals, warnings, contraindications
* Market Agent: Disease prevalence and market opportunity

---

### Orchestration Layer

* Built using LangGraph
* Parallel and sequential task execution
* Centralized state management
* Context-aware inter-agent communication

---

### Intelligence Layer

* Signal normalization across domains
* Cross-domain reasoning (disease-centric insights)
* Deterministic confidence scoring
* Opportunity ranking

---

### Pre-Agentic Mechanism Layer

* Extracts mechanism of action (e.g., AMPK activation, VEGF inhibition)
* Enables mechanism-aware reasoning across agents

---

### Contradiction Layer

* Detects conflicts across domains
* Flags missing or weak evidence
* Improves scientific reliability

---

### Regulatory Post-Check

* Validates top opportunities against regulatory data
* Identifies risks, overlaps, and feasibility constraints

---

### Structured Output

* Summary
* Evidence
* Intelligence
* Contradictions
* Regulatory validation
* Final report

---

## Tech Stack

### Backend

* FastAPI
* Pydantic
* LangGraph
* httpx

### AI & Models

* Gemini (report synthesis, regulatory reasoning)
* Groq Llama (literature and patent analysis)

### Data & Storage

* ChromaDB (vector database)
* Neo4j (graph relationships)

### Frontend

* React
* Tailwind CSS
* Axios

---

## System Architecture (Simplified Flow)

Input → Pre-Agentic Layer → Parallel Agents → Aggregator → Intelligence → Contradiction Layer → Regulatory Post-Check → LLM Report → Final Output

---

## Setup Instructions

Follow the steps below to run the complete system locally.

---

### 1. Backend Setup

Create a virtual environment and install all dependencies:

```bash
python -m pip install -r requirements.txt
python -m pip install -r orchestrator\requirements.txt
python -m pip install -r clinical-agent\requirements.txt
python -m pip install -r patent-agent\requirements.txt
```

---

### 2. Frontend Setup (Initial)

Navigate to the frontend directory and install dependencies:

```bash
cd frontend
npm start
```

---

### 3. Start Backend Services

Return to the root directory.

Stop any running services:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop_all_servers.ps1 -IncludeLauncherWindows
```

Wait until:
“Stopped all” or “No server found”

Start all agents and orchestrator:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_all_servers.ps1
```

Note:
Startup may take 1–2 minutes as multiple agent services initialize.

---

### 4. Check System Health

Verify that all agents are running:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_health.ps1
```

Ensure all services return active status.

---

### 5. Run Frontend

Navigate back to the frontend directory:

```bash
cd frontend
npm run dev
```

---

### 6. Access Application

Open the frontend in your browser.

You can now:

* Check system health
* Enter a molecule
* Run full orchestrated analysis
* View structured results and reports

---

## Usage

1. Enter a molecule (e.g., Metformin)
2. The system orchestrates all agents
3. Observe real-time execution flow
4. Explore results through:

   * Summary
   * Agent outputs
   * Intelligence layer
   * Contradictions
   * Final report
5. Use chatbot interface for further queries

---

## Notes

* Some runs may show missing data (e.g., literature or patents) depending on API responses
* The system explicitly flags such gaps through contradiction and confidence layers
* This behavior is intentional to maintain transparency and avoid hallucinated outputs

---

## Project Vision

AgentRx moves beyond traditional data retrieval systems by introducing:

* Mechanism-aware reasoning
* Cross-domain intelligence
* Deterministic scoring
* Contradiction-aware validation

The goal is to build a **traceable, reliable decision intelligence system for drug repurposing**.

---

## Team

SixDucktors
Sri Sivasubramaniya Nadar College of Engineering
