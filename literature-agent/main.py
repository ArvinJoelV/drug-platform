import uuid
import json
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from Bio import Entrez
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from groq import Groq
import os
import chromadb
import time

load_dotenv()

# ---------------- CONFIG ----------------
Entrez.email = "test@example.com"
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

model = SentenceTransformer('all-MiniLM-L6-v2')

chroma_client = chromadb.PersistentClient(path="./chroma_db")

def get_collections():
    """Get or create collections, ensuring fresh references."""
    return (
        chroma_client.get_or_create_collection(name="papers"),
        chroma_client.get_or_create_collection(name="findings")
    )

# Initialize collections
papers_collection, findings_collection = get_collections()

app = FastAPI(title="Literature Research Agent")

# ---------------- MODELS ----------------
class AnalysisRequest(BaseModel):
    pmids: Optional[List[str]] = None
    query: Optional[str] = None
    max_results: int = 10

class Finding(BaseModel):
    pmid: str
    disease_associations: List[str]
    mechanisms: List[str]
    drug_mentions: List[str]
    sentiment: str
    evidence_snippet: str
    confidence: float
    paper_title: Optional[str] = None

class SearchRequest(BaseModel):
    disease: Optional[str] = None
    drug: Optional[str] = None
    mechanism: Optional[str] = None
    sentiment: Optional[str] = None
    top_k: int = 10

# ---------------- PUBMED FETCH (FIXED) ----------------
def fetch_pubmed_papers(query: str, max_results: int = 10):
    try:
        time.sleep(0.3)

        search_handle = Entrez.esearch(
            db="pubmed",
            term=query,
            retmax=max_results
        )
        search_results = Entrez.read(search_handle)
        pmids = search_results.get("IdList", [])

        if not pmids:
            print("No PMIDs found")
            return []

        fetch_handle = Entrez.efetch(
            db="pubmed",
            id=",".join(pmids),
            rettype="medline",
            retmode="xml"
        )

        records = Entrez.read(fetch_handle)

        papers = []

        for article in records.get("PubmedArticle", []):
            try:
                medline = article.get("MedlineCitation", {})
                article_data = medline.get("Article", {})

                pmid = str(medline.get("PMID", ""))
                title = str(article_data.get("ArticleTitle", ""))

                abstract = ""
                if "Abstract" in article_data:
                    abstract_parts = article_data["Abstract"].get("AbstractText", [])
                    abstract = " ".join([str(p) for p in abstract_parts])

                if not abstract.strip():
                    continue

                papers.append({
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract
                })

            except Exception as e:
                print("Parse error:", e)

        print(f"Fetched {len(papers)} valid papers")
        return papers

    except Exception as e:
        print("Fetch error:", e)
        return []

# ---------------- TEXT CHUNKING ----------------
def chunk_text(text: str, chunk_size: int = 200, overlap: int = 50):
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap

    return chunks

# ---------------- LLM EXTRACTION (FIXED) ----------------
def extract_findings_with_llm(text: str, pmid: str, title: str):
    prompt = f"""Extract biomedical findings from this text as a JSON array. Return ONLY valid JSON, no markdown or extra text.

Each item must have these exact fields:
- disease_associations (list of strings)
- mechanisms (list of strings)
- drug_mentions (list of strings)
- sentiment (string: positive/negative/neutral)
- evidence_snippet (string, max 200 chars)
- confidence (float 0.0-1.0)

Text:
{text[:1000]}

Return ONLY the JSON array, example:
[{{"disease_associations": ["diabetes"], "mechanisms": ["insulin signaling"], "drug_mentions": ["metformin"], "sentiment": "positive", "evidence_snippet": "...", "confidence": 0.8}}]"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        content = response.choices[0].message.content.strip()
        
        if not content:
            raise ValueError("Empty response from LLM")

        # Clean markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Attempt to parse JSON
        findings = json.loads(content)

        # Ensure list format
        if isinstance(findings, dict):
            findings = [findings]

        # Validate structure and add metadata
        valid_findings = []
        for f in findings:
            if isinstance(f, dict):
                # Ensure required fields exist
                f.setdefault("disease_associations", [])
                f.setdefault("mechanisms", [])
                f.setdefault("drug_mentions", [])
                f.setdefault("sentiment", "neutral")
                f.setdefault("evidence_snippet", text[:200])
                f.setdefault("confidence", 0.5)
                f["pmid"] = pmid
                f["paper_title"] = title
                valid_findings.append(f)
        
        return valid_findings if valid_findings else _fallback_finding(pmid, title, text)

    except json.JSONDecodeError as e:
        print(f"LLM JSON parse error: {e}, content was: {content[:100]}")
        return _fallback_finding(pmid, title, text)
    except Exception as e:
        print(f"LLM error: {e}")
        return _fallback_finding(pmid, title, text)


def _fallback_finding(pmid: str, title: str, text: str):
    """Return a fallback finding when LLM fails."""
    return [{
        "pmid": pmid,
        "paper_title": title,
        "disease_associations": [],
        "mechanisms": [],
        "drug_mentions": [],
        "sentiment": "neutral",
        "evidence_snippet": text[:200],
        "confidence": 0.3
    }]

# ---------------- STORAGE ----------------
def store_paper_analysis(pmid: str, title: str, abstract: str, findings: List[Dict]):
    papers_coll, _ = get_collections()
    chunks = chunk_text(abstract)
    embeddings = model.encode(chunks)

    for i, chunk in enumerate(chunks):
        papers_coll.add(
            documents=[chunk],
            embeddings=[embeddings[i].tolist()],
            metadatas=[{
                "pmid": pmid,
                "title": title,
                "chunk_index": i
            }],
            ids=[f"paper_{pmid}_{i}_{uuid.uuid4()}"]
        )

    for i, finding in enumerate(findings):
        _, findings_coll = get_collections()
        text = json.dumps(finding)
        emb = model.encode([text])[0].tolist()

        findings_coll.add(
            documents=[text],
            embeddings=[emb],
            metadatas=[{
                "pmid": pmid,
                "sentiment": finding.get("sentiment", "neutral")
            }],
            ids=[f"finding_{pmid}_{i}_{uuid.uuid4()}"]
        )

# ---------------- SEARCH ----------------
def search_findings(disease=None, drug=None, mechanism=None, sentiment=None, top_k=10):
    _, findings_coll = get_collections()
    query = " ".join(filter(None, [disease, drug, mechanism, sentiment])) or "biomedical findings"

    embedding = model.encode([query]).tolist()

    where = {"sentiment": sentiment} if sentiment else None

    results = findings_coll.query(
        query_embeddings=embedding,
        n_results=top_k,
        where=where
    )

    output = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            try:
                f = json.loads(doc)
                if results["distances"]:
                    f["score"] = 1 - results["distances"][0][i]
                output.append(f)
            except:
                continue

    return output

# ---------------- API ----------------
@app.get("/")
async def root():
    return {"status": "ready"}

@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    if not request.query and not request.pmids:
        raise HTTPException(400, "Provide query or pmids")

    if request.query:
        papers = fetch_pubmed_papers(request.query, request.max_results)
    else:
        papers = fetch_pubmed_papers(" ".join(request.pmids), len(request.pmids))

    all_findings = []

    for p in papers:
        findings = extract_findings_with_llm(p["abstract"], p["pmid"], p["title"])
        store_paper_analysis(p["pmid"], p["title"], p["abstract"], findings)
        all_findings.extend(findings)

    return {
        "status": "success",
        "papers_analyzed": len(papers),
        "findings_extracted": len(all_findings),
        "findings": all_findings
    }

@app.post("/search")
async def search(request: SearchRequest):
    return search_findings(
        request.disease,
        request.drug,
        request.mechanism,
        request.sentiment,
        request.top_k
    )

@app.get("/paper/{pmid}")
async def get_paper(pmid: str):
    """Get paper details and associated findings by PMID"""
    papers_coll, _ = get_collections()
    
    try:
        # Query papers collection for this PMID
        results = papers_coll.get(
            where={"pmid": pmid}
        )
        
        has_abstract = len(results["documents"]) > 0 if results["documents"] else False
        title = results["metadatas"][0]["title"] if results["metadatas"] else "Unknown"
        
        # Get findings for this PMID
        _, findings_coll = get_collections()
        findings_results = findings_coll.get(
            where={"pmid": pmid}
        )
        
        findings = []
        if findings_results and findings_results["documents"]:
            for doc in findings_results["documents"]:
                try:
                    findings.append(json.loads(doc))
                except:
                    pass
        
        return {
            "pmid": pmid,
            "title": title,
            "has_abstract": has_abstract,
            "findings": findings
        }
    except Exception as e:
        raise HTTPException(404, f"Paper {pmid} not found: {str(e)}")

@app.delete("/clear")
async def clear():
    global papers_collection, findings_collection
    try:
        chroma_client.delete_collection("papers")
        chroma_client.delete_collection("findings")
    except:
        pass
    # Refresh collection references
    papers_collection, findings_collection = get_collections()
    return {"status": "cleared"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)