"""Test script for Market Intelligence Agent Server."""

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

def test_analyze_get(base_url, disease):
    """Test GET analysis endpoint"""
    try:
        response = requests.get(f"{base_url}/analyze/{disease.replace(' ', '%20')}")
        if response.status_code == 200:
            print(f"✓ GET analysis for '{disease}' passed")
            return response.json()
        else:
            print(f"✗ GET analysis failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ GET analysis error: {e}")
        return None

def test_analyze_post(base_url, disease):
    """Test POST analysis endpoint"""
    try:
        response = requests.post(
            f"{base_url}/analyze",
            json={"disease": disease}
        )
        if response.status_code == 200:
            print(f"✓ POST analysis for '{disease}' passed")
            return response.json()
        else:
            print(f"✗ POST analysis failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ POST analysis error: {e}")
        return None

def print_analysis(report, title):
    """Pretty print the analysis report"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    
    if report:
        print(f"Disease: {report.get('disease', 'Unknown')}")
        print(f"Market Potential: {report.get('market_potential', 'Unknown')}")
        print(f"Global Prevalence: {report.get('global_prevalence', 'Unknown')}")
        print(f"Market Growth: {report.get('market_growth', 'Unknown')}")
        
        if 'detailed_analysis' in report:
            da = report['detailed_analysis']
            if 'market_summary' in da:
                print(f"\nSummary: {da['market_summary']}")
            
            if 'opportunity_signals' in da:
                print("\nOpportunity Signals:")
                for signal in da['opportunity_signals'][:3]:
                    print(f"  • {signal}")
            
            if 'risk_factors' in da:
                print("\nRisk Factors:")
                for risk in da['risk_factors'][:3]:
                    print(f"  • {risk}")
    print()

def main():
    # Server configuration
    port = 8006
    base_url = f"http://localhost:{port}"
    
    # Test diseases
    test_diseases = [
        "colorectal cancer",
        "breast cancer", 
        "diabetes",
        "alzheimer's disease",
        "rare disease"  # Should return unknown/low potential
    ]
    
    print("🔬 Testing Market Intelligence Agent Server")
    print("="*60)
    
    # Check if server is running
    if not test_health(base_url):
        print("\n❌ Server not responding. Make sure the server is running:")
        print(f"   python market_agent_server.py --port {port} --create-sample")
        sys.exit(1)
    
    # Test GET analysis for each disease
    print("\n📊 Testing GET Analysis Endpoint")
    print("-"*40)
    for disease in test_diseases:
        report = test_analyze_get(base_url, disease)
        if report and disease == "colorectal cancer":
            print_analysis(report, f"Market Analysis: {disease}")
    
    # Test POST analysis
    print("\n📝 Testing POST Analysis Endpoint")
    print("-"*40)
    for disease in test_diseases[:2]:
        report = test_analyze_post(base_url, disease)
        if report:
            print_analysis(report, f"POST Analysis: {disease}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()