import chromadb
from sentence_transformers import SentenceTransformer
from ingest_trials import ingest

def interactive_loop():
    print("Loading database...")
    try:
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        collection = chroma_client.get_or_create_collection(name="clinical_trials", metadata={"hnsw:space": "l2"})
    except Exception as e:
        print("Error: Could not load the vector database. Have you run ingestion yet?")
        print(f"Details: {e}")
        return

    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("\nClinical Trials RAG System Ready")
    print("Enter drug and disease (e.g. 'metformin cancer')")
    print("Type exit to quit\n")

    while True:
        try:
            query = input("> ")
            if query.strip().lower() == 'exit':
                break
            if not query.strip():
                continue
            
            # Extract the drug name (assume it's the first word)
            parts = query.strip().split()
            if not parts:
                continue
            drug_query = parts[0].lower()
            
            # Check if this drug exists in the database
            existing_trials = collection.get(
                where={"drug_queried": drug_query},
                limit=1
            )
            
            # Dynamically ingest if missing!
            if not existing_trials.get("ids"):
                print(f"\n[!] New drug detected: {drug_query}. Downloading trials in the background...")
                success = ingest(drug_query)
                if not success:
                    print(f"Could not find any clinical trials for {drug_query}. Try another drug.\n")
                    continue
                    
            query_embedding = model.encode([query]).tolist()
            
            # Search ONLY for trials related to this specific drug
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=5,
                where={"drug_queried": drug_query}
            )
            
            print("\nTop Clinical Trials\n")
            if not results["documents"] or not results["documents"][0]:
                print("No relevant trials found in the database.\n")
                continue
                
            # Filter results by similarity distance to ensure strict relevance
            valid_results = 0
            
            # In ChromaDB (using default L2 distance), a lower distance means it's MORE similar.
            # A threshold of 1.05 is usually a good baseline for strict sentence-transformers relevance.
            SIMILARITY_THRESHOLD = 1.05
            
            for i, (doc, dist) in enumerate(zip(results["documents"][0], results["distances"][0])):
                
                # If the distance is too high, it's just a random guess
                if dist > SIMILARITY_THRESHOLD:
                    continue
                    
                valid_results += 1
                lines = doc.split('\n')
                title = ""
                condition = ""
                phase = ""
                status = ""
                trial_id = "N/A"
                pmids = ""
                summary = "N/A"
                for line in lines:
                    if line.startswith("Title: "):
                        title = line.replace("Title: ", "").strip()
                    elif line.startswith("Condition: "):
                        condition = line.replace("Condition: ", "").strip()
                    elif line.startswith("Phase: "):
                        phase = line.replace("Phase: ", "").strip()
                    elif line.startswith("Status: "):
                        status = line.replace("Status: ", "").strip()
                    elif line.startswith("Trial ID: "):
                        trial_id = line.replace("Trial ID: ", "").strip()
                    elif line.startswith("PMIDs: "):
                        pmids = line.replace("PMIDs: ", "").strip()
                    elif line.startswith("Summary: "):
                        summary = line.replace("Summary: ", "").strip()
                        
                # 1. Main Info (Title, Condition, Phase, Status)
                print(f"{valid_results}. {title}\n")
                print(f"Condition: {condition}")
                print(f"Phase: {phase}")
                print(f"Status: {status}\n")
                
                # 2. Insight Section
                print("Insight:")
                if summary and summary != "N/A":
                    snippet = summary[:400] + "..." if len(summary) > 400 else summary
                    print(f"{snippet}\n")
                else:
                    print("No summary available for this trial.\n")
                
                # 3. Why Section
                print("Why:")
                print(f"This trial was selected because it matches your search for '{drug_query}' in the context of '{condition}'.\n")
                
                # 4. Source Section
                print("Source:")
                if pmids and pmids != "N/A":
                    for pmid in pmids.split(", "):
                        print(f"PubMed Article PMID: {pmid}")
                        print(f"URL: https://pubmed.ncbi.nlm.nih.gov/{pmid}/\n")
                
                print(f"ClinicalTrials.gov NCT ID: {trial_id}")
                print(f"URL: https://clinicaltrials.gov/study/{trial_id}\n")
                
                print("=" * 60 + "\n")
                
            if valid_results == 0:
                 print(f"Could not find any clinical trials EXACTLY matching '{query}' in our database.")
                 print("The vector database only returned low-confidence, unrelated matches.\n")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    interactive_loop()
