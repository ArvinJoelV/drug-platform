# test_patent_agent.py
import requests
import json
import sys
import time

def test_health(base_url):
    """Test health endpoint"""
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✓ Health check passed")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False

def test_analyze_get(base_url, molecule):
    """Test GET analysis endpoint"""
    try:
        response = requests.get(f"{base_url}/analyze/{molecule}")
        if response.status_code == 200:
            print(f"✓ GET analysis for '{molecule}' passed")
            return response.json()
        else:
            print(f"✗ GET analysis failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ GET analysis error: {e}")
        return None

def test_analyze_post(base_url, molecule):
    """Test POST analysis endpoint"""
    try:
        response = requests.post(
            f"{base_url}/analyze",
            json={"molecule": molecule}
        )
        if response.status_code == 200:
            print(f"✓ POST analysis for '{molecule}' passed")
            return response.json()
        else:
            print(f"✗ POST analysis failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ POST analysis error: {e}")
        return None

def print_report(report, title):
    """Pretty print the analysis report"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    
    if report:
        print(f"Molecule: {report.get('molecule', 'Unknown')}")
        print(f"Patent Status: {report.get('patent_status', 'Unknown')}")
        print(f"Expiry Year: {report.get('expiry_year', 'Unknown')}")
        print(f"Commercial Freedom: {report.get('commercial_freedom', 'Unknown')}")
        
        if 'detailed_analysis' in report:
            da = report['detailed_analysis']
            print("\n--- Detailed Analysis ---")
            print(f"Total Patents: {da.get('patent_summary', {}).get('total_patents_found', '0')}")
            
            if 'repurposing_feasibility' in da:
                rf = da['repurposing_feasibility']
                print(f"Feasibility: {rf.get('freedom_to_operate', 'Unknown')}")
                print(f"Reasoning: {rf.get('reasoning', 'N/A')}")
            
            if da.get('opportunity_signals'):
                print("\nOpportunity Signals:")
                for signal in da['opportunity_signals']:
                    print(f"  • {signal}")
            
            if da.get('risk_factors'):
                print("\nRisk Factors:")
                for risk in da['risk_factors']:
                    print(f"  • {risk}")
    print()

def main():
    # Server configuration
    port = 8003
    base_url = f"http://localhost:{port}"
    
    # Test molecules
    test_molecules = ["Aspirin", "Ibuprofen", "Paracetamol", "UnknownMolecule"]
    
    print("🔬 Testing Patent Analysis Agent Server")
    print("="*60)
    
    # Check if server is running
    if not test_health(base_url):
        print("\n❌ Server not responding. Make sure the server is running:")
        print(f"   python patent_agent_server.py --port {port} --create-sample")
        sys.exit(1)
    
    # Test GET analysis for each molecule
    print("\n📊 Testing GET Analysis Endpoint")
    print("-"*40)
    for molecule in test_molecules:
        report = test_analyze_get(base_url, molecule)
        if report and molecule == "Aspirin":
            print_report(report, f"Analysis Report for {molecule}")
    
    # Test POST analysis
    print("\n📝 Testing POST Analysis Endpoint")
    print("-"*40)
    for molecule in test_molecules[:2]:  # Test first two molecules
        report = test_analyze_post(base_url, molecule)
        if report:
            print_report(report, f"POST Analysis for {molecule}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()