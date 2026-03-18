#!/usr/bin/env python3
"""
Clinical Trial Agent Server
Provides clinical trial analysis for molecules via a simple HTTP endpoint.
"""

import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import sys
import chromadb
from sentence_transformers import SentenceTransformer
from ingest_trials import ingest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClinicalTrialAgent:
    """Clinical Trial Agent for retrieving and analyzing trials related to a molecule."""
    
    def __init__(self, db_path="./chroma_db", model_name="all-MiniLM-L6-v2"):
        """Initialize the clinical trial agent with vector database and embedding model."""
        self.db_path = db_path
        self.model_name = model_name
        self.chroma_client = None
        self.collection = None
        self.model = None
        self.SIMILARITY_THRESHOLD = 1.05  # L2 distance threshold for relevance
        
        self._initialize()
    
    def _initialize(self):
        """Initialize database connection and embedding model."""
        try:
            logger.info(f"Connecting to ChromaDB at {self.db_path}")
            self.chroma_client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.chroma_client.get_or_create_collection(
                name="clinical_trials", 
                metadata={"hnsw:space": "l2"}
            )
            
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Clinical Trial Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Clinical Trial Agent: {e}")
            raise
    
    def analyze_molecule(self, molecule_name: str) -> dict:
        """
        Analyze clinical trials for a given molecule.
        
        Args:
            molecule_name: Name of the molecule/drug to analyze
            
        Returns:
            Dictionary with clinical trial analysis results
        """
        logger.info(f"Analyzing clinical trials for molecule: {molecule_name}")
        
        # Validate input
        if not molecule_name or not molecule_name.strip():
            return {
                "molecule": molecule_name,
                "error": "Invalid molecule name provided",
                "trials": []
            }
        
        drug_query = molecule_name.strip().lower()
        
        # Check if drug exists in database, ingest if not
        existing_trials = self.collection.get(
            where={"drug_queried": drug_query},
            limit=1
        )
        
        if not existing_trials.get("ids"):
            logger.info(f"New drug detected: {drug_query}. Fetching trials...")
            success = ingest(drug_query)
            if not success:
                logger.warning(f"No clinical trials found for {drug_query}")
                return {
                    "molecule": molecule_name,
                    "message": f"No clinical trials found for {molecule_name}",
                    "trials": []
                }
        
        # Create query embedding
        query = f"{molecule_name} clinical trials"
        query_embedding = self.model.encode([query]).tolist()
        
        # Search for relevant trials
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=10,  # Get more results to filter
            where={"drug_queried": drug_query}
        )
        
        # Process and structure results
        trials = self._process_results(results, drug_query)
        
        # Create summary statistics
        summary = self._create_summary(trials)
        
        return {
            "molecule": molecule_name,
            "summary": summary,
            "trials": trials,
            "total_trials_found": len(trials)
        }
    
    def _process_results(self, results, drug_query):
        """Process and filter search results into structured trial data."""
        trials = []
        
        if not results["documents"] or not results["documents"][0]:
            return trials
        
        valid_results = 0
        for i, (doc, dist) in enumerate(zip(results["documents"][0], results["distances"][0])):
            # Filter by similarity threshold
            if dist > self.SIMILARITY_THRESHOLD:
                continue
            
            valid_results += 1
            trial = self._parse_trial_document(doc, drug_query, dist)
            if trial:
                trials.append(trial)
        
        logger.info(f"Found {valid_results} relevant trials for {drug_query}")
        return trials
    
    def _parse_trial_document(self, doc, drug_query, distance):
        """Parse a trial document into structured format."""
        lines = doc.split('\n')
        trial = {
            "trial_id": "N/A",
            "title": "N/A",
            "condition": "N/A",
            "phase": "N/A",
            "status": "N/A",
            "summary": "N/A",
            "pmids": [],
            "relevance_score": round(1.0 / (distance + 0.1), 2),  # Convert distance to relevance
            "drug_queried": drug_query
        }
        
        for line in lines:
            if line.startswith("Title: "):
                trial["title"] = line.replace("Title: ", "").strip()
            elif line.startswith("Condition: "):
                trial["condition"] = line.replace("Condition: ", "").strip()
            elif line.startswith("Phase: "):
                trial["phase"] = line.replace("Phase: ", "").strip()
            elif line.startswith("Status: "):
                trial["status"] = line.replace("Status: ", "").strip()
            elif line.startswith("Trial ID: "):
                trial["trial_id"] = line.replace("Trial ID: ", "").strip()
            elif line.startswith("PMIDs: "):
                pmids_str = line.replace("PMIDs: ", "").strip()
                if pmids_str and pmids_str != "N/A":
                    trial["pmids"] = [pmid.strip() for pmid in pmids_str.split(", ")]
            elif line.startswith("Summary: "):
                trial["summary"] = line.replace("Summary: ", "").strip()
        
        return trial
    
    def _create_summary(self, trials):
        """Create summary statistics from trials."""
        if not trials:
            return {
                "total_trials": 0,
                "phases": {},
                "statuses": {},
                "conditions": [],
                "most_common_condition": None
            }
        
        phases = {}
        statuses = {}
        conditions = []
        
        for trial in trials:
            # Count phases
            phase = trial["phase"]
            phases[phase] = phases.get(phase, 0) + 1
            
            # Count statuses
            status = trial["status"]
            statuses[status] = statuses.get(status, 0) + 1
            
            # Collect conditions
            if trial["condition"] != "N/A":
                conditions.append(trial["condition"])
        
        # Find most common condition
        most_common_condition = None
        if conditions:
            from collections import Counter
            condition_counts = Counter(conditions)
            most_common_condition = condition_counts.most_common(1)[0][0]
        
        return {
            "total_trials": len(trials),
            "phases": phases,
            "statuses": statuses,
            "conditions": list(set(conditions))[:5],  # Top 5 unique conditions
            "most_common_condition": most_common_condition
        }


class ClinicalAgentHandler(BaseHTTPRequestHandler):
    """HTTP Handler for the Clinical Trial Agent server."""
    
    def _set_headers(self, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == "/health":
            self._handle_health_check()
        elif parsed_url.path == "/analyze":
            self._handle_analyze_get(parsed_url)
        else:
            self._send_error(404, "Endpoint not found")
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == "/analyze":
            self._handle_analyze_post()
        else:
            self._send_error(404, "Endpoint not found")
    
    def _handle_health_check(self):
        """Handle health check requests."""
        self._set_headers()
        response = {
            "status": "healthy",
            "service": "Clinical Trial Agent",
            "version": "1.0.0"
        }
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def _handle_analyze_get(self, parsed_url):
        """Handle GET requests to /analyze endpoint."""
        query_params = parse_qs(parsed_url.query)
        molecule = query_params.get("molecule", [None])[0]
        
        if not molecule:
            self._send_error(400, "Missing required parameter: molecule")
            return
        
        self._process_and_respond(molecule)
    
    def _handle_analyze_post(self):
        """Handle POST requests to /analyze endpoint."""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            molecule = data.get("molecule")
            
            if not molecule:
                self._send_error(400, "Missing required field: molecule")
                return
            
            self._process_and_respond(molecule)
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON payload")
    
    def _process_and_respond(self, molecule):
        """Process molecule analysis and send response."""
        try:
            # Get the server instance from the global variable
            result = server.agent.analyze_molecule(molecule)
            
            self._set_headers()
            self.wfile.write(json.dumps(result, indent=2).encode())
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            self._send_error(500, f"Internal server error: {str(e)}")
    
    def _send_error(self, status_code, message):
        """Send error response."""
        self._set_headers(status_code)
        error_response = {"error": message}
        self.wfile.write(json.dumps(error_response).encode())
    
    def log_message(self, format, *args):
        """Override to use logger instead of stderr."""
        logger.info(f"{self.address_string()} - {format % args}")


class ClinicalAgentServer:
    """Clinical Trial Agent Server."""
    
    def __init__(self, host="localhost", port=8001, db_path="./chroma_db"):
        self.host = host
        self.port = port
        self.db_path = db_path
        self.agent = None
        self.httpd = None
    
    def start(self):
        """Start the server."""
        try:
            # Initialize the agent
            logger.info("Initializing Clinical Trial Agent...")
            self.agent = ClinicalTrialAgent(db_path=self.db_path)
            
            # Start HTTP server
            server_address = (self.host, self.port)
            self.httpd = HTTPServer(server_address, ClinicalAgentHandler)
            
            logger.info(f"Clinical Trial Agent Server started at http://{self.host}:{self.port}")
            logger.info("Available endpoints:")
            logger.info(f"  GET  /health - Health check")
            logger.info(f"  GET  /analyze?molecule=<name> - Analyze molecule (GET)")
            logger.info(f"  POST /analyze - Analyze molecule (POST with JSON)")
            logger.info("\nPress Ctrl+C to stop the server")
            
            # Store server instance for handler access
            global server
            server = self
            
            self.httpd.serve_forever()
            
        except KeyboardInterrupt:
            logger.info("\nShutting down server...")
            self.stop()
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            sys.exit(1)
    
    def stop(self):
        """Stop the server."""
        if self.httpd:
            self.httpd.shutdown()
            logger.info("Server stopped")


# Global variable for handler access
server = None


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clinical Trial Agent Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--db-path", default="./chroma_db", help="Path to ChromaDB")
    
    args = parser.parse_args()
    
    agent_server = ClinicalAgentServer(
        host=args.host,
        port=args.port,
        db_path=args.db_path
    )
    agent_server.start()


if __name__ == "__main__":
    main()