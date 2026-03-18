import httpx
import asyncio
import json

async def test_orchestrator():
    url = "http://localhost:8000/orchestrate"
    payload = {"molecule": "metformin"}
    
    print(f"Calling orchestrator with: {payload}")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            print(f"Status Code: {response.status_code}")
            print("Response:")
            print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_orchestrator())
