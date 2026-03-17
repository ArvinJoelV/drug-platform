# Clinical Trials RAG System

A Retrieval-Augmented Generation (RAG) system for searching and analyzing clinical trials data from ClinicalTrials.gov.

## Features
- **Dynamic Ingestion**: Automatically fetches and embeds clinical trial data for new drugs.
- **Vector Database**: Uses ChromaDB for efficient semantic search.
- **Strict Relevance**: Filters search results based on similarity thresholds.
- **Detailed Insights**: Provides trial summaries, conditions, phases, and direct links to ClinicalTrials.gov and PubMed.

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ArvinJoelV/drug-platform.git
   cd drug-platform
   # Switch to the clinical-agent branch if applicable
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Required Python Version:**
   - Python 3.9+ recommended.

## Usage

### Interactive Search
Run the interactive RAG system:
```bash
python rag_query.py
```
Type a drug and a condition (e.g., `metformin cancer`) to see relevant clinical trials.

### Manual Ingestion
To pre-ingest data for a specific drug:
```bash
python ingest_trials.py <drug_name>
```

## Essential Files
- `clinical_api.py`: Handles fetching data from ClinicalTrials.gov API.
- `ingest_trials.py`: Handles embedding and storing data in the vector database.
- `rag_query.py`: Main entry point for the interactive RAG interface.
- `requirements.txt`: Project dependencies.
