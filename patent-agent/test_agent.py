import os
import subprocess
def test_agent():
    print("running patent_agent.py with sample_data.json...")
    
    script_path = os.path.join(os.path.dirname(__file__), "patent_agent.py")
    data_path = os.path.join(os.path.dirname(__file__), "sample_data.json")
    
    if not os.path.exists(script_path):
        print(f"Error: Could not find {script_path}")
        return
        
    if not os.path.exists(data_path):
        print(f"Error: Could not find {data_path}")
        return
        
    result = subprocess.run(
        ["python", script_path, "--data", data_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("Success! Agent Output:\n")
        print(result.stdout)
    else:
        print("Error analyzing data:\n")
        print(result.stderr)

if __name__ == "__main__":
    test_agent()
