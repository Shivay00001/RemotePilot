import time
import asyncio
import psutil
from typing import Dict, Any, Optional
from .base import Agent

class MonitorAgent(Agent):
    def __init__(self):
        super().__init__(name="Monitor")
        self.active_processes = []
        self.start_time = None
        self._abort_requested = False

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input: {"action": "check_health", "task_id": "..."}
        """
        action = task.get("action", "check_health")
        
        if action == "check_health":
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            print(f"[Monitor] Heartbeat: CPU {cpu}% | RAM {ram}%")
            return {
                "status": "success",
                "cpu": cpu,
                "ram": ram,
                "abort_status": self._abort_requested
            }
        
        elif action == "abort":
            self._abort_requested = True
            return {"status": "abort_triggered"}

        return {"status": "idle"}

    def is_hung(self, last_update_time: float, threshold: float = 60.0) -> bool:
        return (time.time() - last_update_time) > threshold

    def request_abort(self):
        self._abort_requested = True

    def reset(self):
        self._abort_requested = False
        self.start_time = time.time()
