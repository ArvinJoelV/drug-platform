# patent_agent_server.py
import json
import argparse
import datetime
from collections import Counter
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from dotenv import load_dotenv
import chromadb
from groq import Groq

load_dotenv()

# Global variable to store the patent database
PATENT_DATABASE = None

class PatentAnalysisAgent:
    def __init__(self, data_filepath=None):
        self.today = datetime.date.today()
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.Client()
        try:
            self.chroma_client.delete_collection("patents")
        except Exception:
            pass
        self.collection = self.chroma_client.create_collection(name="patents")
        
        # Load patent database if provided
        self.patent_data = {}
        if data_filepath and os.path.exists(data_filepath):
            self.load_patent_database(data_filepath)

    def load_patent_database(self, data_filepath):
        """Load all patent data from a master database file"""
        with open(data_filepath, 'r') as f:
            all_data = json.load(f)
        
        # Index patents by molecule name
        for entry in all_data:
            molecule = entry.get("molecule", "").lower()
            if molecule:
                self.patent_data[molecule] = entry
                
        print(f"Loaded patent data for {len(self.patent_data)} molecules")

    def get_patents_for_molecule(self, molecule_name):
        """Retrieve patents for a specific molecule"""
        molecule_lower = molecule_name.lower()
        
        # Check if we have data for this molecule
        if molecule_lower in self.patent_data:
            data = self.patent_data[molecule_lower]
        else:
            # Return empty data for unknown molecules
            data = {"molecule": molecule_name, "patents": []}
        
        # Load patents into ChromaDB for this query
        patents = data.get("patents", [])
        if patents:
            documents = []
            metadatas = []
            ids = []
            
            for i, p in enumerate(patents):
                doc = f"Title: {p.get('title', '')}\nAbstract: {p.get('abstract', '')}\nAssignee: {p.get('assignee', '')}"
                documents.append(doc)
                metadatas.append({
                    "patent_id": p.get("patent_id", f"Unknown_{i}"),
                    "assignee": p.get("assignee", "Unknown")
                })
                ids.append(p.get("patent_id", f"Unknown_{i}"))
                
            # Clear previous collection and add new data
            try:
                self.chroma_client.delete_collection("patents")
            except:
                pass
            self.collection = self.chroma_client.create_collection(name="patents")
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
        
        return data

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

    def generate_rag_insights(self, molecule, context_docs, facts):
        """Calls Groq API to generate nuanced insights."""
        if not self.groq_client:
            return {
                "repurposing_feasibility": {
                    "freedom_to_operate": "Unknown", 
                    "reasoning": "Groq API key not configured. Set GROQ_API_KEY environment variable."
                },
                "opportunity_signals": [],
                "risk_factors": ["LLM insights unavailable - API key missing"]
            }
        
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
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant", 
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "repurposing_feasibility": {"freedom_to_operate": "Unknown", "reasoning": "Failed to generate LLM insights."},
                "opportunity_signals": [],
                "risk_factors": []
            }

    def analyze_molecule(self, molecule_name):
        """Main analysis function called by the server"""
        # Get patents for this molecule
        data = self.get_patents_for_molecule(molecule_name)
        molecule = data.get("molecule", molecule_name)
        patents = data.get("patents", [])
        
        total_patents = len(patents)
        if total_patents == 0:
            return self._empty_report(molecule)

        # Deterministic analysis
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
                try:
                    exp_date = datetime.datetime.strptime(expiry_str, "%Y-%m-%d").date()
                    if not earliest_expiry or exp_date < earliest_expiry:
                        earliest_expiry = exp_date
                    if not latest_expiry or exp_date > latest_expiry:
                        latest_expiry = exp_date
                        
                    is_expired = exp_date < self.today
                    
                    if p_type == "Composition" and core_status == "Unknown":
                        core_status = "Expired" if is_expired else "Active"
                except:
                    pass
                    
            citations.append(f"{p.get('patent_id', 'Unknown ID')} ({assignee})")

        # Calculate concentration risk
        if assignee_counter:
            top_assignee, top_count = assignee_counter.most_common(1)[0]
            concentration_risk = f"High monopoly risk ({top_count}/{total_patents} by {top_assignee})" if top_count / total_patents >= 0.5 else "Low concentration, distributed field."
        else:
            concentration_risk = "No assignee data"

        hard_facts = {
            "core_status": core_status,
            "earliest_expiry": earliest_expiry.strftime("%Y-%m-%d") if earliest_expiry else "Unknown",
            "latest_expiry": latest_expiry.strftime("%Y-%m-%d") if latest_expiry else "Unknown",
            "type_distribution": dict(type_counter),
            "concentration_risk": concentration_risk
        }

        # RAG Layer
        if patents:
            results = self.collection.query(
                query_texts=[f"{molecule} indications, formulations, and methods of treatment"],
                n_results=min(3, total_patents)
            )
            
            context_docs = ""
            if results and results.get('documents'):
                for idx, doc in enumerate(results['documents'][0]):
                    context_docs += f"--- Patent {idx+1} ---\n{doc}\n\n"
        else:
            context_docs = "No patents found in database."

        # LLM Augmentation
        llm_insights = self.generate_rag_insights(molecule, context_docs, hard_facts)

        # Format response according to the orchestrator's expected output
        report = {
            "molecule": molecule,
            "patent_status": core_status,  # Simplified for orchestrator
            "expiry_year": hard_facts["latest_expiry"].split("-")[0] if hard_facts["latest_expiry"] != "Unknown" else "Unknown",
            "commercial_freedom": llm_insights.get("repurposing_feasibility", {}).get("freedom_to_operate", "Unknown"),
            "detailed_analysis": {
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
                "citations": citations[:5]  # Limit citations
            }
        }
        
        return report

    def _empty_report(self, molecule):
        return {
            "molecule": molecule,
            "patent_status": "Unknown",
            "expiry_year": "Unknown",
            "commercial_freedom": "High",
            "detailed_analysis": {
                "patent_summary": {
                    "total_patents_found": "0",
                    "major_assignees": [],
                    "patent_types_distribution": {}
                },
                "expiry_analysis": {
                    "core_patent_status": "Unknown",
                    "earliest_expiry": "Unknown",
                    "latest_expiry": "Unknown"
                },
                "repurposing_feasibility": {
                    "freedom_to_operate": "High",
                    "reasoning": "No patents found for this molecule in the database. This suggests freedom to operate, but verify with a comprehensive search."
                },
                "opportunity_signals": ["No patent barriers identified"],
                "risk_factors": ["Limited patent data available - manual verification recommended"],
                "citations": []
            }
        }


# HTTP Server Handler
class PatentAgentHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests - health check or molecule query"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "service": "patent_agent"}).encode())
            return
            
        elif parsed_path.path.startswith("/analyze/"):
            # Extract molecule name from path
            molecule = parsed_path.path[9:]  # Remove "/analyze/"
            molecule = urllib.parse.unquote(molecule)
            
            if not molecule:
                self.send_error(400, "Molecule name required")
                return
                
            self.process_molecule_request(molecule)
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_POST(self):
        """Handle POST requests for molecule analysis"""
        if self.path == "/analyze":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                molecule = data.get('molecule')
                
                if not molecule:
                    self.send_error(400, "Molecule name required in request body")
                    return
                    
                self.process_molecule_request(molecule)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
        else:
            self.send_error(404, "Endpoint not found")
    
    def process_molecule_request(self, molecule):
        """Process molecule analysis and send response"""
        try:
            # Get the global agent instance
            agent = self.server.agent
            
            # Perform analysis
            report = agent.analyze_molecule(molecule)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(report, indent=2).encode())
            
        except Exception as e:
            self.send_error(500, f"Analysis failed: {str(e)}")


class PatentAgentServer(HTTPServer):
    def __init__(self, server_address, handler_class, agent):
        super().__init__(server_address, handler_class)
        self.agent = agent


def create_sample_patent_database():
    """Create a sample patent database for testing"""
    sample_data = [
        {
            "molecule": "Aspirin",
            "patents": [
                {
                    "patent_id": "US1234567",
                    "title": "Acetylsalicylic acid composition for pain relief",
                    "abstract": "A composition comprising acetylsalicylic acid for treating pain and inflammation.",
                    "assignee": "Bayer AG",
                    "filing_date": "1980-05-15",
                    "expiry_date": "2000-05-15"
                },
                {
                    "patent_id": "US2345678",
                    "title": "Method of using aspirin for cardiovascular protection",
                    "abstract": "Method of treating cardiovascular conditions using low-dose aspirin.",
                    "assignee": "Bayer AG",
                    "filing_date": "1985-03-20",
                    "expiry_date": "2005-03-20"
                }
            ]
        },
        {
            "molecule": "Ibuprofen",
            "patents": [
                {
                    "patent_id": "US3456789",
                    "title": "Ibuprofen formulations for oral administration",
                    "abstract": "Novel formulations of ibuprofen with enhanced bioavailability.",
                    "assignee": "Boots Group",
                    "filing_date": "1990-07-10",
                    "expiry_date": "2010-07-10"
                }
            ]
        },
        {
            "molecule": "Paracetamol",
            "patents": [
                {
                    "patent_id": "US4567890",
                    "title": "Stable paracetamol compositions",
                    "abstract": "Pharmaceutical compositions containing paracetamol with improved stability.",
                    "assignee": "GSK",
                    "filing_date": "1995-11-25",
                    "expiry_date": "2015-11-25"
                }
            ]
        }
    ]
    
    with open("patent_database.json", "w") as f:
        json.dump(sample_data, f, indent=2)
    
    print("Sample patent database created: patent_database.json")
    return "patent_database.json"


def main():
    parser = argparse.ArgumentParser(description="Patent Analysis Agent Server")
    parser.add_argument("--port", type=int, default=8003, help="Server port")
    parser.add_argument("--database", type=str, help="Path to patent database JSON file")
    parser.add_argument("--create-sample", action="store_true", help="Create sample patent database")
    args = parser.parse_args()

    # Create sample database if requested
    if args.create_sample:
        db_path = create_sample_patent_database()
        args.database = db_path

    # Initialize agent with patent database
    agent = PatentAnalysisAgent(data_filepath=args.database)
    
    # Start server
    server_address = ('', args.port)
    httpd = PatentAgentServer(server_address, PatentAgentHandler, agent)
    
    print(f"Patent Analysis Agent Server running on port {args.port}")
    print(f"Loaded patent data for {len(agent.patent_data)} molecules")
    print("\nEndpoints:")
    print(f"  GET  /health                    - Health check")
    print(f"  GET  /analyze/<molecule>         - Analyze specific molecule")
    print(f"  POST /analyze                    - Analyze with JSON body {{'molecule': 'name'}}")
    print("\nExample: curl http://localhost:8003/analyze/Aspirin")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()


if __name__ == "__main__":
    main()