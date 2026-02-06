import requests
import asyncio
import websockets
import json

async def test_flow():
    # 1. Submit a simple task
    res = requests.post("http://localhost:8000/task/submit", json={"goal": "echo hello world"})
    task_id = res.json()["task_id"]
    print(f"Task submitted: {task_id}")

    # 2. Monitor logs via WebSocket
    async with websockets.connect("ws://localhost:8000/ws/logs") as websocket:
        try:
            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                if data.get("type") == "log":
                    log = data["data"]
                    print(f"  [LOG] [{log.get('agent')}] {log.get('message')}")
                elif data.get("type") == "state":
                    print(f"  [STATE] -> {data['data'].get('status')}")
                    if data["data"].get("status") in ["DONE", "FAILED"]:
                        break
        except Exception as e:
            print(f"WS Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_flow())
