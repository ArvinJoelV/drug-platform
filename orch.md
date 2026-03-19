# Orchestrator Architecture Documentation

## Overview

The orchestrator now functions as a **layered pipeline**, where all existing domain agents remain unchanged. All new intelligence, reasoning, and synthesis capabilities are implemented within the orchestrator itself.

---

## High-Level Flow

### Execution Pipeline

```
Input -> Parallel Agent Layer -> Aggregator -> Intelligence Layer -> Regulatory Postcheck -> LLM Report -> Finalizer
```

### Concrete Flow

```
input -> clinical -> literature -> aggregator -> intelligence -> regulatory_postcheck -> llm_report -> finalizer
```

### Parallel Execution

The following agents run in parallel after input and converge at the aggregator:

* patent
* regulatory
* market

### Full Graph

```
START -> input

input -> clinical
input -> patent
input -> regulatory
input -> market

clinical -> literature

patent -> aggregator
regulatory -> aggregator
market -> aggregator
literature -> aggregator

aggregator -> intelligence
intelligence -> regulatory_postcheck
regulatory_postcheck -> llm_report
llm_report -> finalizer

finalizer -> END
```

This design preserves the **zero-disruption rule** — no agent contracts were modified.

---

## Implemented Features

### Orchestrator State

The orchestrator now maintains:

* analysis_id
* agent outputs
* aggregated_report
* intelligence_data
* regulatory_postcheck
* llm_report
* final_report
* node status
* node errors

---

### Intelligence Layer (Post-Aggregation)

* Signal normalization
* Cross-domain reasoning
* Deterministic confidence scoring
* Opportunity ranking

---

### LLM Report Layer

* Gemini-based structured synthesis
* Deterministic fallback if unavailable

---

### Regulatory Postcheck

* Evaluates top opportunities using existing regulatory data
* No additional regulatory agent calls

---

### In-Memory Analysis Store

* Generates analysis_id
* Stores completed results
* Supports modular retrieval endpoints

---

### Literature Enrichment

* Literature queries use:

  * molecule
  * top clinical conditions from clinical output

---

## Orchestrator Nodes

### input

Initializes state with molecule and base status.

### clinical

Calls clinical agent.

### patent

Calls patent agent.

### regulatory

Calls regulatory agent.

### market

Calls market agent.

### literature

Uses enriched clinical context for querying.

### aggregator

Creates unified cross-domain evidence payload.

### intelligence

Runs deterministic reasoning and scoring.

### regulatory_postcheck

Performs post-hoc regulatory validation.

### llm_report

Generates final narrative report.

### finalizer

Builds final API response.

---

## Intelligence Layer Details

### 1. Signal Normalization

All agent outputs are converted into a unified schema.

#### Clinical

* diseases
* trial strength
* phases
* statuses

#### Literature

* diseases
* mechanisms
* sentiment
* papers analyzed

#### Patent

* freedom to operate
* risk factors

#### Regulatory

* approved indications
* risks
* warnings
* confidence

#### Market

* disease
* market score
* market potential
* market statistics

---

### 2. Cross-Domain Reasoning

Builds disease-centric insights:

* disease
* evidence_summary
* supporting_domains
* missing_domains
* risk_flags

Key logic includes:

* Clinical vs literature presence
* Market alignment
* Regulatory overlap
* Evidence completeness
* Novelty detection
* Risk awareness

---

### 3. Confidence Scoring

Deterministic weighted scoring:

* Clinical → highest weight
* Literature → secondary
* Market → supporting
* Patent → minor influence
* Regulatory → penalty layer
* Missing domains → negative impact

Outputs:

* per_disease_scores
* global_score
* global_confidence
* scoring metadata

---

### 4. Opportunity Ranking

Each disease becomes a ranked opportunity:

* disease
* score
* confidence
* rationale
* signals_used
* novelty

Ranking factors:

* Evidence strength
* Novelty bonus/penalty
* Risk penalties
* Domain coverage

Top 5 opportunities are returned.

---

## Regulatory Postcheck

* Evaluates top opportunities against existing regulatory data
* Detects:

  * approved indication overlap
  * warnings and contraindications

Output:

* checked_candidates

Note:
No second regulatory agent call is performed. This is a deterministic post-hoc validation.

---

## LLM Report Layer

### Input

* molecule
* summary
* key evidence
* top opportunities
* cross-domain insights
* confidence breakdown
* regulatory postcheck

### Output

* executive_summary
* key_findings
* top_repurposing_opportunities
* risks_and_limitations
* final_recommendation
* generation metadata

Modes:

* Primary: Gemini
* Fallback: deterministic synthesis

---

## Technology Stack

* FastAPI → API layer
* LangGraph → orchestration workflow
* Pydantic → data models
* httpx → async agent calls
* PowerShell → environment automation
* In-memory Python store → persistence

---

## LLM Usage

### Gemini

* Used in orchestrator (llm_report)
* Used in regulatory agent reasoning
* Model: gemini-3-flash-preview

### Groq / Llama

* Used in literature agent
* Model: llama-3.1-8b-instant

### OpenAI (Market Agent)

* References like gpt-4o-mini exist in market agent

Note:
The orchestrator itself is deterministic except for the llm_report node.

---

## API Endpoints

### Main Analysis

```
POST /analyze
```

Input:

```
{
  "molecule": "Metformin"
}
```

Output includes:

* summary
* evidence
* intelligence
* llm_report
* meta
* agents
* analysis_id

---

### Backward Compatibility

```
POST /orchestrate
```

---

### Retrieval Endpoints

```
GET /analysis/{id}/status
GET /analysis/{id}/partial
GET /analysis/{id}/summary
GET /analysis/{id}/evidence
GET /analysis/{id}/intelligence
GET /analysis/{id}/report
GET /analysis/{id}/agents
```

---

## Final Response Structure

### 1. Summary

* clinical signal
* literature signal
* patent status
* regulatory status
* market signal

### 2. Evidence

* clinical trials
* papers
* patents
* approvals
* regulatory data
* market data

### 3. Intelligence

* normalized signals
* cross-domain insights
* confidence breakdown
* top opportunities

### 4. LLM Report

* executive summary
* key findings
* opportunities
* risks
* recommendation

### 5. Meta

* confidence
* sources
* regulatory postcheck
* analysis_id

### 6. Agents

* per-agent status
* per-agent error
* per-agent raw response

---

## Inter-Agent Communication

### Implemented

* Clinical → Literature enrichment

  * Literature queries include clinical-derived conditions

### Not Implemented

* Literature → Clinical feedback loop
* Second regulatory agent loop
* Threshold-based feedback cycles

---

## Architectural Evolution

### Before

* Workflow coordinator
* Response merger

### Now

* Workflow coordinator
* Cross-domain normalization engine
* Deterministic scoring engine
* Opportunity ranking system
* Report synthesis layer
* Modular analysis API

---

## Conclusion

The orchestrator has evolved from a simple aggregation layer into a **full decision-intelligence system**, while maintaining strict isolation and stability of all domain agents.
