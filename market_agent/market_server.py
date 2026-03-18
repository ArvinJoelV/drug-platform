"""MCP-like server for the Market Intelligence Agent."""

from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from typing import Any

from market_agent.market_agent import MarketIntelligenceAgent


# Global agent instance
MARKET_AGENT = None


class MarketAgentHandler(BaseHTTPRequestHandler):
    """HTTP handler for market agent requests"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "healthy", 
                "service": "market_intelligence_agent",
                "version": "1.0.0"
            }).encode())
            return
            
        elif parsed_path.path.startswith("/analyze/"):
            # Extract disease name from path
            disease = parsed_path.path[9:]  # Remove "/analyze/"
            disease = urllib.parse.unquote(disease)
            
            if not disease:
                self.send_error(400, "Disease name required")
                return
                
            # Parse query parameters for optional CSV path
            query_params = urllib.parse.parse_qs(parsed_path.query)
            prevalence_csv = query_params.get('prevalence_csv', [None])[0]
            
            self.process_disease_request(disease, prevalence_csv)
        else:
            self.send_error(404, f"Endpoint not found: {parsed_path.path}")
    
    def do_POST(self):
        """Handle POST requests for disease analysis"""
        if self.path == "/analyze":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                disease = data.get('disease')
                prevalence_csv = data.get('prevalence_csv')
                model = data.get('model', 'gpt-4o-mini')
                
                if not disease:
                    self.send_error(400, "Disease name required in request body")
                    return
                    
                self.process_disease_request(disease, prevalence_csv, model)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
        else:
            self.send_error(404, "Endpoint not found")
    
    def process_disease_request(self, disease: str, prevalence_csv: str | None = None, model: str = "gpt-4o-mini"):
        """Process disease analysis and send response"""
        try:
            # Get the global agent instance
            agent = self.server.market_agent
            
            # Perform analysis
            print(f"Analyzing disease: {disease}")
            result = agent.analyze_disease(
                disease_name=disease,
                prevalence_csv_path=prevalence_csv,
                model=model
            )
            
            # Format response for orchestrator (simplified)
            response = self._format_for_orchestrator(result, disease)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            print(f"Error processing request: {str(e)}")
            self.send_error(500, f"Analysis failed: {str(e)}")
    
    def _format_for_orchestrator(self, result: dict[str, Any], disease: str) -> dict[str, Any]:
        """Format the detailed analysis into a simplified response for the orchestrator"""
        
        # Extract key insights for orchestrator
        market_summary = result.get("market_summary", {})
        
        # Determine market potential based on the analysis
        market_potential = self._determine_market_potential(result)
        
        # Extract prevalence if available
        prevalence = "Unknown"
        if "prevalence_analysis" in result:
            pa = result["prevalence_analysis"]
            if "global_prevalence" in pa:
                prevalence = pa["global_prevalence"]
            elif "estimated_prevalence" in pa:
                prevalence = pa["estimated_prevalence"]
        
        # Extract growth trend
        growth = "Unknown"
        if "market_trends" in result:
            trends = result["market_trends"]
            growth = trends.get("growth_trend", "Unknown")
        
        return {
            "disease": disease,
            "market_potential": market_potential,
            "global_prevalence": prevalence,
            "market_growth": growth,
            "detailed_analysis": result  # Keep full analysis for debugging
        }
    
    def _determine_market_potential(self, result: dict[str, Any]) -> str:
        """Determine market potential based on analysis results"""
        market_summary = result.get("market_summary", {})
        summary_text = str(market_summary).lower()
        
        if "high" in summary_text or "significant" in summary_text or "large" in summary_text:
            return "High"
        elif "moderate" in summary_text or "medium" in summary_text:
            return "Medium"
        elif "low" in summary_text or "small" in summary_text or "limited" in summary_text:
            return "Low"
        else:
            return "Unknown"


class MarketAgentServer(HTTPServer):
    """Custom HTTP server with market agent instance"""
    def __init__(self, server_address, handler_class, market_agent):
        super().__init__(server_address, handler_class)
        self.market_agent = market_agent


def create_sample_prevalence_data():
    """Create sample prevalence data for testing"""
    sample_data = [
        {
            "disease": "colorectal cancer",
            "prevalence": "High",
            "global_cases": "1.9 million annually",
            "incidence_rate": "19.5 per 100,000",
            "region": "Global"
        },
        {
            "disease": "breast cancer",
            "prevalence": "High", 
            "global_cases": "2.3 million annually",
            "incidence_rate": "47.8 per 100,000",
            "region": "Global"
        },
        {
            "disease": "lung cancer",
            "prevalence": "High",
            "global_cases": "2.2 million annually",
            "incidence_rate": "22.5 per 100,000", 
            "region": "Global"
        },
        {
            "disease": "diabetes",
            "prevalence": "Very High",
            "global_cases": "537 million",
            "incidence_rate": "6.7% of adults",
            "region": "Global"
        },
        {
            "disease": "alzheimer's disease",
            "prevalence": "Moderate",
            "global_cases": "55 million",
            "incidence_rate": "5-8% of elderly",
            "region": "Global"
        }
    ]
    
    os.makedirs("data", exist_ok=True)
    with open("data/prevalence_sample.csv", "w") as f:
        f.write("disease,prevalence,global_cases,incidence_rate,region\n")
        for row in sample_data:
            f.write(f"{row['disease']},{row['prevalence']},{row['global_cases']},{row['incidence_rate']},{row['region']}\n")
    
    print("Sample prevalence data created: data/prevalence_sample.csv")
    return "data/prevalence_sample.csv"


def main():
    parser = argparse.ArgumentParser(description="Market Intelligence Agent Server")
    parser.add_argument("--port", type=int, default=8004, help="Server port")
    parser.add_argument("--create-sample", action="store_true", help="Create sample prevalence data")
    parser.add_argument("--persist-dir", type=str, default="./chroma_store", help="ChromaDB persist directory")
    parser.add_argument("--top-k", type=int, default=5, help="Number of documents to retrieve")
    args = parser.parse_args()

    # Create sample data if requested
    if args.create_sample:
        create_sample_prevalence_data()

    # Initialize market agent
    print("Initializing Market Intelligence Agent...")
    market_agent = MarketIntelligenceAgent(
        persist_directory=args.persist_dir,
        top_k=args.top_k
    )
    
    # Start server
    server_address = ('', args.port)
    httpd = MarketAgentServer(server_address, MarketAgentHandler, market_agent)
    
    print(f"\n🚀 Market Intelligence Agent Server running on port {args.port}")
    print("\n📊 Endpoints:")
    print(f"  GET  /health                    - Health check")
    print(f"  GET  /analyze/<disease>          - Analyze specific disease")
    print(f"  POST /analyze                    - Analyze with JSON body")
    print("\n📝 Examples:")
    print(f"  curl http://localhost:{args.port}/analyze/colorectal%20cancer")
    print(f"  curl -X POST http://localhost:{args.port}/analyze \\")
    print(f"    -H 'Content-Type: application/json' \\")
    print(f"    -d '{{\"disease\": \"breast cancer\"}}'")
    print(f"\n📁 Sample prevalence data: data/prevalence_sample.csv (if --create-sample used)")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
        httpd.shutdown()


if __name__ == "__main__":
    main()