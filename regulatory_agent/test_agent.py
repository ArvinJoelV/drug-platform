import requests
import json

BASE_URL = "http://localhost:8000"

def test_regulatory(molecule):
    """Test regulatory endpoint"""
    payload = {"molecule": molecule}
    response = requests.post(f"{BASE_URL}/regulatory", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n{'='*50}")
        print(f"Regulatory Intelligence for: {molecule}")
        print('='*50)
        
        if result['success'] and result['data']:
            data = result['data']
            print(f"Drug: {data['drug']}")
            print(f"Confidence: {data['confidence']:.2f}")
            
            print("\n✅ Approved Indications:")
            for ind in data['approved_indications']:
                print(f"  • {ind}")
            
            print("\n⚠️  Warnings:")
            for warn in data['warnings']:
                print(f"  • {warn}")
            
            print("\n🚫 Contraindications:")
            for contra in data['contradictions']:
                print(f"  • {contra}")
            
            print("\n📋 Adverse Events:")
            for ae in data['adverse_events']:
                print(f"  • {ae}")
            
            print(f"\n📝 Summary: {data['regulatory_summary']}")
            print(f"\n📚 Sources: {', '.join(data['sources'])}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    else:
        print(f"HTTP Error: {response.status_code}")

if __name__ == "__main__":
    print("Testing Regulatory Intelligence Agent...")
    
    # Test with various molecules
    test_molecules = ["Aspirin", "Metformin", "Ibuprofen"]
    
    for molecule in test_molecules:
        test_regulatory(molecule)
        print("\n" + "-"*50)