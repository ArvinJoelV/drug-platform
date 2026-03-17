import json
import argparse
import datetime
from collections import Counter
import os
from dotenv import load_dotenv
import chromadb
from groq import Groq
load_dotenv()

class PatentAnalysisAgent:
    def __init__(self):
        self.today = datetime.date.today()
        # Initialize Groq Client
        self.groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        # Initialize ChromaDB (in-memory for this script, but can be persistent)
        self.chroma_client = chromadb.Client()
        # Delete collection if it exists from a previous run in the same session
        try:
            self.chroma_client.delete_collection("patents")
        except Exception:
            pass
        self.collection = self.chroma_client.create_collection(name="patents")

    def categorize_patent(self, title, abstract):
        """Rule-based categorization of patents from title/abstract keywords."""
        text = (title + " " + abstract).lower()
        if any(kw in text for kw in ["method of treat", "use of", "treating", "therapeutic use", "indication"]):
            return "Method-of-use"
        elif any(kw in text for kw in ["formulation", "composition comprising", "capsule", "tablet", "delivery", "carrier"]):
            return "Formulation"
        elif any(kw in text for kw in ["process for preparing", "method of synthesizing", "manufacturing", "synthesis"]):
            return "Process"
        elif any(kw in text for kw in ["crystalline", "polymorph", "compound of formula", "novel compound"]):
            return "Composition"
        else:
            return "Other"

    def estimate_expiry(self, filing_date_str):
        """Estimate expiry as filing date + 20 years."""
        try:
            fd = datetime.datetime.strptime(filing_date_str, "%Y-%m-%d").date()
            return fd.replace(year=fd.year + 20)
        except Exception:
            return None

    def load_data(self, json_filepath):
        """Loads data and embeds it into ChromaDB."""
        with open(json_filepath, 'r') as f:
            data = json.load(f)
            
        patents = data.get("patents", [])
        if not patents:
            return data
            
        documents = []
        metadatas = []
        ids = []
        
        for p in patents:
            # Embed the title and abstract as the main document
            doc = f"Title: {p.get('title', '')}\nAbstract: {p.get('abstract', '')}\nAssignee: {p.get('assignee', '')}"
            documents.append(doc)
            
            # Store structured info in metadata
            metadatas.append({
                "patent_id": p.get("patent_id", "Unknown"),
                "assignee": p.get("assignee", "Unknown")
            })
            ids.append(p.get("patent_id", "Unknown"))
            
        # Add to ChromaDB
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Loaded {len(patents)} patents into ChromaDB vector store.")
        return data

    def generate_rag_insights(self, molecule, context_docs, facts):
        """Calls Groq API to generate nuanced insights based on facts + vector context."""
        
        prompt = f"""
        You are an expert pharmaceutical patent analyst. Your task is to analyze the patent landscape for the molecule '{molecule}' and output EXACTLY a JSON object with no markdown formatting, no code blocks, and no extra text.

        Here are the hard facts calculated deterministically:
        - Core Patent Status: {facts['core_status']}
        - Earliest Expiry: {facts['earliest_expiry']}
        - Latest Expiry: {facts['latest_expiry']}
        - Patent Types Found: {facts['type_distribution']}
        - Concentration: {facts['concentration_risk']}

        Here are the most relevant patent summaries retrieved from the vector database:
        {context_docs}

        Based on these facts and the patent abstracts, generate the remaining fields for the report.
        Strictly limit your analysis to what is provided.
        
        Your output MUST be a raw JSON object matching this exact schema:
        {{
            "repurposing_feasibility": {{
                "freedom_to_operate": "High / Medium / Low",
                "reasoning": "1-2 sentence explanation based on the facts and context."
            }},
            "opportunity_signals": [
                "Opportunity 1 based on context",
                "Opportunity 2 based on context"
            ],
            "risk_factors": [
                "Risk 1",
                "Risk 2"
            ]
        }}
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama-3.1-8b-instant", 
                temperature=0.2, # Low temp for analytical consistency
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON from the LLM
            llm_output = json.loads(response.choices[0].message.content)
            return llm_output
        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "repurposing_feasibility": {"freedom_to_operate": "Unknown", "reasoning": "Failed to generate LLM insights."},
                "opportunity_signals": [],
                "risk_factors": []
            }

    def analyze(self, data):
        """Hybrid logic: Deterministic Facts + Vector DB Retrieval + Groq LLM."""
        molecule = data.get("molecule", "Unknown Molecule")
        patents = data.get("patents", [])
        
        total_patents = len(patents)
        if total_patents == 0:
            return self._empty_report(molecule)

        # --- DETERMINISTIC BASE LAYER ---
        assignee_counter = Counter()
        type_counter = Counter()
        
        core_status = "Unknown"
        earliest_expiry = None
        latest_expiry = None
        citations = []

        for p in patents:
            assignee = p.get("assignee", "Unknown")
            assignee_counter[assignee] += 1
            
            p_type = self.categorize_patent(p.get("title", ""), p.get("abstract", ""))
            type_counter[p_type] += 1
            
            expiry_str = p.get("expiry_date")
            if not expiry_str and p.get("filing_date"):
                estimated = self.estimate_expiry(p.get("filing_date"))
                if estimated:
                    expiry_str = estimated.strftime("%Y-%m-%d")
                    
            if expiry_str:
                exp_date = datetime.datetime.strptime(expiry_str, "%Y-%m-%d").date()
                if not earliest_expiry or exp_date < earliest_expiry:
                    earliest_expiry = exp_date
                if not latest_expiry or exp_date > latest_expiry:
                    latest_expiry = exp_date
                    
                is_expired = exp_date < self.today
                
                if p_type == "Composition":
                    core_status = "Expired" if is_expired else "Active"
                    
            citations.append(f"{p.get('patent_id', 'Unknown ID')} ({assignee})")

        # Calculate concentration risk for facts
        top_assignee, top_count = assignee_counter.most_common(1)[0]
        concentration_risk = f"High monopoly risk ({top_count}/{total_patents} by {top_assignee})" if top_count / total_patents >= 0.5 else "Low concentration, distributed field."

        hard_facts = {
            "core_status": core_status,
            "earliest_expiry": earliest_expiry.strftime("%Y-%m-%d") if earliest_expiry else "Unknown",
            "latest_expiry": latest_expiry.strftime("%Y-%m-%d") if latest_expiry else "Unknown",
            "type_distribution": dict(type_counter),
            "concentration_risk": concentration_risk
        }

        # --- RAG LAYER: Query Vector DB ---
        # Query the DB to find general context about the molecule and indications
        results = self.collection.query(
            query_texts=[f"{molecule} indications, formulations, and methods of treatment"],
            n_results=min(3, total_patents) # Get top 3 most relevant patents
        )
        
        context_docs = ""
        if results and results['documents']:
            for idx, doc in enumerate(results['documents'][0]):
                context_docs += f"--- Patent {idx+1} ---\n{doc}\n\n"

        # --- LLM AUGMENTATION ---
        llm_insights = self.generate_rag_insights(molecule, context_docs, hard_facts)

        # --- MERGE & FORMAT OUTPUT ---
        report = {
            "molecule": molecule,
            "patent_summary": {
                "total_patents_found": str(total_patents),
                "major_assignees": [a for a, c in assignee_counter.most_common(3)],
                "patent_types_distribution": hard_facts["type_distribution"]
            },
            "expiry_analysis": {
                "core_patent_status": hard_facts["core_status"],
                "earliest_expiry": hard_facts["earliest_expiry"],
                "latest_expiry": hard_facts["latest_expiry"]
            },
            "repurposing_feasibility": llm_insights.get("repurposing_feasibility", {}),
            "opportunity_signals": llm_insights.get("opportunity_signals", []),
            "risk_factors": llm_insights.get("risk_factors", []),
            "citations": citations
        }
        
        return report

    def _empty_report(self, molecule):
        return {
            "molecule": molecule,
            "patent_summary": {"total_patents_found": "0", "major_assignees": [], "patent_types_distribution": {}},
            "expiry_analysis": {"core_patent_status": "Unknown", "earliest_expiry": "Unknown", "latest_expiry": "Unknown"},
            "repurposing_feasibility": {"freedom_to_operate": "High", "reasoning": "No patents found matching criteria. Verify search scope."},
            "opportunity_signals": [],
            "risk_factors": ["Insufficient data to assess risks."],
            "citations": []
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Patent Analysis Agent (Hybrid RAG)")
    parser.add_argument("--data", type=str, required=True, help="Path to the JSON file containing patent data")
    args = parser.parse_args()

    # ensure groq api key exists
    if not os.environ.get("GROQ_API_KEY"):
        print(json.dumps({"error": "GROQ_API_KEY environment variable is not set. Please set it to run the hybrid agent."}))
        exit(1)

    agent = PatentAnalysisAgent()
    try:
        data_input = agent.load_data(args.data)
        report = agent.analyze(data_input)
        print("\n\n=== FINAL PATENT INTELLIGENCE REPORT ===\n")
        print(json.dumps(report, indent=2))
    except FileNotFoundError:
        print(json.dumps({"error": f"Data file {args.data} not found. Please provide a valid JSON file."}))
    except json.JSONDecodeError:
        print(json.dumps({"error": f"Failed to parse {args.data}. Ensure it is valid JSON."}))
