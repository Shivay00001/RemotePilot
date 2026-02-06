import requests
import json

def check_all():
    # Since tasks are in memory of main.py, I can't access them directly.
    # But I can try to guess or use the log streaming to see IDs.
    pass

if __name__ == "__main__":
    # Let's just monitor logs
    import asyncio
    import websockets

    async def monitor():
        async with websockets.connect("ws://localhost:8000/ws/logs") as websocket:
            print("Connected to logs.")
            while True:
                msg = await websocket.recv()
                print(msg)

    asyncio.run(monitor())
