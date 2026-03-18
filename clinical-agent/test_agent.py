#!/usr/bin/env python3
"""
Test client for the Clinical Trial Agent Server.
"""

import requests
import json
import sys
from typing import Dict, List

class ClinicalTrialClient:
    """Client for interacting with the Clinical Trial Agent Server."""
    
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
    
    def health_check(self) -> Dict:
        """Check if the server is healthy."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def analyze_molecule_get(self, molecule: str) -> Dict:
        """Analyze a molecule using GET request."""
        response = requests.get(
            f"{self.base_url}/analyze",
            params={"molecule": molecule}
        )
        response.raise_for_status()
        return response.json()
    
    def analyze_molecule_post(self, molecule: str) -> Dict:
        """Analyze a molecule using POST request."""
        response = requests.post(
            f"{self.base_url}/analyze",
            json={"molecule": molecule}
        )
        response.raise_for_status()
        return response.json()
    
    def print_trial_analysis(self, result: Dict):
        """Pretty print the trial analysis results."""
        print("\n" + "="*80)
        print(f"CLINICAL TRIAL ANALYSIS: {result['molecule']}")
        print("="*80)
        
        if "error" in result:
            print(f"ERROR: {result['error']}")
            return
        
        if "message" in result:
            print(f"MESSAGE: {result['message']}")
            return
        
        # Print summary
        summary = result.get("summary", {})
        print(f"\n📊 SUMMARY")
        print(f"  Total Trials Found: {result['total_trials_found']}")
        
        if summary:
            print(f"\n  Phases Distribution:")
            for phase, count in summary.get("phases", {}).items():
                print(f"    - {phase}: {count}")
            
            print(f"\n  Status Distribution:")
            for status, count in summary.get("statuses", {}).items():
                print(f"    - {status}: {count}")
            
            if summary.get("most_common_condition"):
                print(f"\n  Most Common Condition: {summary['most_common_condition']}")
        
        # Print individual trials
        if result["trials"]:
            print(f"\n📋 DETAILED TRIALS")
            for i, trial in enumerate(result["trials"], 1):
                print(f"\n  {i}. {trial['title']}")
                print(f"     Trial ID: {trial['trial_id']}")
                print(f"     Condition: {trial['condition']}")
                print(f"     Phase: {trial['phase']}")
                print(f"     Status: {trial['status']}")
                print(f"     Relevance Score: {trial.get('relevance_score', 'N/A')}")
                
                if trial.get('pmids'):
                    print(f"     PMIDs: {', '.join(trial['pmids'][:3])}")
                
                if trial.get('summary') and trial['summary'] != "N/A":
                    summary_preview = trial['summary'][:100] + "..."
                    print(f"     Summary: {summary_preview}")
        else:
            print("\n  No trials found.")


def interactive_mode(client: ClinicalTrialClient):
    """Run interactive mode for testing."""
    print("\n" + "="*80)
    print("CLINICAL TRIAL AGENT - INTERACTIVE TEST MODE")
    print("="*80)
    print("\nCommands:")
    print("  analyze <molecule> - Analyze clinical trials for a molecule")
    print("  health            - Check server health")
    print("  exit              - Exit interactive mode")
    print()
    
    while True:
        try:
            command = input(">>> ").strip()
            
            if command.lower() == "exit":
                break
            elif command.lower() == "health":
                result = client.health_check()
                print(json.dumps(result, indent=2))
            elif command.startswith("analyze "):
                molecule = command[8:].strip()
                if molecule:
                    print(f"\nAnalyzing clinical trials for: {molecule}")
                    result = client.analyze_molecule_post(molecule)
                    client.print_trial_analysis(result)
                else:
                    print("Please specify a molecule name")
            else:
                print("Unknown command. Try: analyze <molecule>, health, exit")
                
        except KeyboardInterrupt:
            break
        except requests.exceptions.ConnectionError:
            print("Error: Cannot connect to server. Is it running?")
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point for the test client."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test client for Clinical Trial Agent")
    parser.add_argument("--url", default="http://localhost:8001", help="Server URL")
    parser.add_argument("--molecule", help="Molecule to analyze (optional)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    client = ClinicalTrialClient(args.url)
    
    # Check server health first
    try:
        health = client.health_check()
        print(f"✅ Server health check passed: {health}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {args.url}")
        print("   Make sure the server is running: python clinical_agent_server.py")
        sys.exit(1)
    
    if args.interactive:
        interactive_mode(client)
    elif args.molecule:
        # Single molecule analysis
        result = client.analyze_molecule_post(args.molecule)
        client.print_trial_analysis(result)
    else:
        # Default: analyze a few example molecules
        examples = ["Aspirin", "Metformin", "Ibuprofen"]
        print("\nRunning example analyses...")
        
        for molecule in examples:
            print(f"\n{'='*60}")
            print(f"Analyzing: {molecule}")
            print('='*60)
            
            result = client.analyze_molecule_post(molecule)
            client.print_trial_analysis(result)


if __name__ == "__main__":
    main()