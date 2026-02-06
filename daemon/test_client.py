import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("Checking Daemon health...")
    try:
        r = requests.get(f"{BASE_URL}/")
        print(f"Root: {r.status_code}")
        print(f"Body: {r.text}")
        if r.status_code == 200:
            print(r.json())
    except Exception as e:
        print(f"Daemon error: {e}")
        return False

    print("\nTesting Model Listing...")
    try:
        r = requests.post(f"{BASE_URL}/execute", json={"command": "list models"})
        print(f"List Models Status: {r.status_code}")
        print(f"List Models Body: {r.text}")
        if r.status_code == 200:
            print(f"Models JSON: {r.json()}")
    except Exception as e:
        print(f"List Models Failed: {e}")

    print("\nTesting Sandbox Execution...")
    r = requests.post(f"{BASE_URL}/execute", json={"command": "run echo 'RemotePilot is working!'"})
    print(f"Exec Status: {r.status_code}")
    print(f"Exec Body: {r.text}")
    if r.status_code == 200:
        print(f"Exec JSON: {r.json()}") # Only decode if 200 OK
    
    print("\nTesting Planner...")
    try:
        # Simple plan request
        r = requests.post(f"{BASE_URL}/execute", json={"command": "plan open notepad and type hello"})
        print(f"Plan Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Plan Response: {r.json()}")
    except Exception as e:
        print(f"Plan Failed: {e}")

    print("\nTesting Execute Plan...")
    try:
        # Dummy plan
        dummy_plan = '[{"action": "COMMAND", "value": "echo Execution Works"}, {"action": "WAIT", "value": "0.1"}]'
        r = requests.post(f"{BASE_URL}/execute", json={"command": f"execute_plan {dummy_plan}"})
        print(f"ExecPlan Status: {r.status_code}")
    except Exception as e:
        print(f"ExecPlan Failed: {e}")

    print("\nTesting Vision...")
    try:
        r = requests.post(f"{BASE_URL}/execute", json={"command": "vision describe screen"})
        print(f"Vision Status: {r.status_code}")
    except Exception as e:
        print(f"Vision Failed: {e}")

    print("\nTesting Safety Block...")
    try:
        # Dangerous plan
        unsafe_plan = '[{"action": "COMMAND", "value": "rm -rf /"}]'
        r = requests.post(f"{BASE_URL}/execute", json={"command": f"execute_plan {unsafe_plan}"})
        print(f"Safety Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Safety Response: {r.json()}") # Should say BLOCKED
    except Exception as e:
        print(f"Safety Test Failed: {e}")

    print("\nTesting Verifier...")
    try:
        r = requests.post(f"{BASE_URL}/execute", json={"command": "verify execution is correct"})
        print(f"Verify Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Verify Response: {r.json()}")
    except Exception as e:
        print(f"Verify Failed: {e}")

    return True

if __name__ == "__main__":
    if not test_api():
        sys.exit(1)
