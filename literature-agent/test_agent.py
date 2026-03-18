import requests
import json
from pprint import pprint
import time

# Base URL for the agent server
BASE_URL = "http://localhost:8000"

def test_root():
    """Test if server is running"""
    response = requests.get(f"{BASE_URL}/")
    print("Root endpoint:", response.json())
    print()

def test_analyze_by_query():
    """Test analyzing papers by search query"""
    # Use a more specific query to get real results
    payload = {
        "query": "aspirin[Title] AND cancer[Title] AND 2020[Date]",  # More specific query
        "max_results": 3
    }
    
    print("Analyzing papers by query...")
    print(f"Query: {payload['query']}")
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Papers analyzed: {result['papers_analyzed']}")
        print(f"Findings extracted: {result['findings_extracted']}")
        
        if result['findings']:
            print("\nSample findings:")
            for finding in result['findings'][:3]:
                print(f"  PMID: {finding.get('pmid')}")
                print(f"  Diseases: {finding.get('disease_associations')}")
                print(f"  Drugs: {finding.get('drug_mentions')}")
                print(f"  Mechanisms: {finding.get('mechanisms')}")
                print(f"  Sentiment: {finding.get('sentiment')}")
                print(f"  Evidence: {finding.get('evidence_snippet')[:100]}...")
                print()
        else:
            print("No findings extracted - papers might not have abstracts or relevant content")
    else:
        print(f"Error: {response.status_code} - {response.text}")
    print("-" * 50)

def test_search_by_disease():
    """Test searching for findings by disease"""
    payload = {
        "disease": "cancer",
        "top_k": 3
    }
    
    print("Searching for cancer-related findings...")
    response = requests.post(f"{BASE_URL}/search", json=payload)
    
    if response.status_code == 200:
        findings = response.json()
        print(f"Found {len(findings)} findings")
        for i, finding in enumerate(findings):
            print(f"\nFinding {i+1}:")
            pprint(finding)
    else:
        print(f"Error: {response.status_code} - {response.text}")
    print("-" * 50)

def test_search_by_drug():
    """Test searching for findings by drug"""
    payload = {
        "drug": "aspirin",
        "top_k": 3
    }
    
    print("Searching for aspirin-related findings...")
    response = requests.post(f"{BASE_URL}/search", json=payload)
    
    if response.status_code == 200:
        findings = response.json()
        print(f"Found {len(findings)} findings")
        for i, finding in enumerate(findings):
            print(f"\nFinding {i+1}:")
            pprint(finding)
    else:
        print(f"Error: {response.status_code} - {response.text}")
    print("-" * 50)

def test_search_by_mechanism():
    """Test searching for findings by biological mechanism"""
    payload = {
        "mechanism": "inflammation",
        "top_k": 3
    }
    
    print("Searching for inflammation mechanism findings...")
    response = requests.post(f"{BASE_URL}/search", json=payload)
    
    if response.status_code == 200:
        findings = response.json()
        print(f"Found {len(findings)} findings")
        for i, finding in enumerate(findings):
            print(f"\nFinding {i+1}:")
            pprint(finding)
    else:
        print(f"Error: {response.status_code} - {response.text}")
    print("-" * 50)

def test_search_by_sentiment():
    """Test searching for findings by sentiment"""
    payload = {
        "sentiment": "positive",
        "top_k": 3
    }
    
    print("Searching for positive findings...")
    response = requests.post(f"{BASE_URL}/search", json=payload)
    
    if response.status_code == 200:
        findings = response.json()
        print(f"Found {len(findings)} findings")
        for i, finding in enumerate(findings):
            print(f"\nFinding {i+1}:")
            pprint(finding)
    else:
        print(f"Error: {response.status_code} - {response.text}")
    print("-" * 50)

def test_combined_search():
    """Test combined search with multiple criteria"""
    payload = {
        "disease": "lung cancer",
        "drug": "immunotherapy",
        "sentiment": "positive",
        "top_k": 3
    }
    
    print("Combined search (lung cancer + immunotherapy + positive)...")
    response = requests.post(f"{BASE_URL}/search", json=payload)
    
    if response.status_code == 200:
        findings = response.json()
        print(f"Found {len(findings)} findings")
        for i, finding in enumerate(findings):
            print(f"\nFinding {i+1}:")
            pprint(finding)
    else:
        print(f"Error: {response.status_code} - {response.text}")
    print("-" * 50)

def test_get_paper():
    """Test getting paper details by PMID"""
    # First analyze a paper to get a PMID
    analyze_payload = {
        "query": "aspirin cancer",
        "max_results": 1
    }
    
    response = requests.post(f"{BASE_URL}/analyze", json=analyze_payload)
    if response.status_code == 200:
        result = response.json()
        if result['findings']:
            pmid = result['findings'][0]['pmid']
            
            print(f"Getting paper details for PMID: {pmid}")
            response = requests.get(f"{BASE_URL}/paper/{pmid}")
            
            if response.status_code == 200:
                paper_data = response.json()
                print(f"Paper PMID: {paper_data['pmid']}")
                print(f"Has abstract: {paper_data['has_abstract']}")
                print(f"Findings count: {len(paper_data['findings'])}")
                if paper_data['findings']:
                    print("Sample finding:")
                    pprint(paper_data['findings'][0])
            else:
                print(f"Error: {response.status_code} - {response.text}")
    print("-" * 50)

def test_clear_database():
    """Test clearing the database"""
    print("Clearing database...")
    response = requests.delete(f"{BASE_URL}/clear")
    if response.status_code == 200:
        print("Database cleared:", response.json())
    else:
        print(f"Error: {response.status_code} - {response.text}")
    print("-" * 50)

def run_all_tests():
    """Run all test scenarios"""
    print("=" * 60)
    print("LITERATURE RESEARCH AGENT - TEST SUITE")
    print("=" * 60)
    
    # Test 1: Check server
    test_root()
    
    # Test 2: Clear database (start fresh)
    test_clear_database()
    time.sleep(1)  # Wait a bit
    
    # Test 3: Analyze papers
    test_analyze_by_query()
    time.sleep(1)
    
    # Test 4: Search by disease
    test_search_by_disease()
    time.sleep(1)
    
    # Test 5: Search by drug
    test_search_by_drug()
    time.sleep(1)
    
    # Test 6: Search by mechanism
    test_search_by_mechanism()
    time.sleep(1)
    
    # Test 7: Search by sentiment
    test_search_by_sentiment()
    time.sleep(1)
    
    # Test 8: Combined search
    test_combined_search()
    time.sleep(1)
    
    # Test 9: Get paper details
    test_get_paper()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    # Ask user which test to run
    print("Literature Research Agent Test Client")
    print("1. Run all tests")
    print("2. Analyze papers by query")
    print("3. Search by disease")
    print("4. Search by drug")
    print("5. Search by mechanism")
    print("6. Search by sentiment")
    print("7. Combined search")
    print("8. Get paper details")
    print("9. Clear database")
    
    choice = input("\nEnter your choice (1-9): ")
    
    if choice == "1":
        run_all_tests()
    elif choice == "2":
        test_analyze_by_query()
    elif choice == "3":
        test_search_by_disease()
    elif choice == "4":
        test_search_by_drug()
    elif choice == "5":
        test_search_by_mechanism()
    elif choice == "6":
        test_search_by_sentiment()
    elif choice == "7":
        test_combined_search()
    elif choice == "8":
        test_get_paper()
    elif choice == "9":
        test_clear_database()
    else:
        print("Invalid choice")