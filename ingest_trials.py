import sys
import chromadb
from sentence_transformers import SentenceTransformer
from clinical_api import fetch_trials

def ingest(drug: str) -> bool:
    print(f"Fetching trials for '{drug}'...")
    trials = fetch_trials(drug)
    if not trials:
        print("No trials found.")
        return False

    print(f"Found {len(trials)} trials. Initializing Chromadb...")
    
    # Initialize Persistent ChromaDB
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_or_create_collection(name="clinical_trials")
    
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    documents = []
    metadatas = []
    ids = []
    
    for trial in trials:
        pmids_str = ", ".join(trial.get("pmids", [])) if trial.get("pmids") else "N/A"
        doc_text = (
            f"Trial ID: {trial['trial_id']}\n"
            f"Title: {trial['title']}\n"
            f"Condition: {trial['condition']}\n"
            f"Phase: {trial['phase']}\n"
            f"Status: {trial['status']}\n"
            f"PMIDs: {pmids_str}\n"
            f"Summary: {trial.get('summary', 'N/A')}"
        )
        documents.append(doc_text)
        metadatas.append(
            {"trial_id": trial["trial_id"], "drug_queried": drug.lower()}
        )
        ids.append(trial["trial_id"])
        
    print("Creating embeddings and storing in database...")
    embeddings = model.encode(documents).tolist()
    
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    
    print("Ingestion complete. Database is ready for queries.")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_trials.py <drug_name>")
        sys.exit(1)
        
    drug_name = " ".join(sys.argv[1:])
    ingest(drug_name)
