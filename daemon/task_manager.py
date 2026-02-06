import asyncio
import uuid
import json
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

class TaskStatus(str, Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    MODEL_CHECK = "MODEL_CHECK"
    SANDBOX_SETUP = "SANDBOX_SETUP"
    OBSERVE = "OBSERVE"
    ACT = "ACT"
    VERIFY = "VERIFY"
    DONE = "DONE"
    FAILED = "FAILED"

class Task:
    def __init__(self, goal: str):
        self.id = str(uuid.uuid4())
        self.goal = goal
        self.status = TaskStatus.IDLE
        self.logs = []
        self.created_at = datetime.now().isoformat()
        self.plan = []
        self.error = None

    def add_log(self, agent: str, message: str, level: str = "INFO"):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "message": message,
            "level": level
        }
        self.logs.append(log_entry)
        return log_entry

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.active_task_id: Optional[str] = None
        self.log_queues: List[asyncio.Queue] = []

    def create_task(self, goal: str) -> Task:
        task = Task(goal)
        self.tasks[task.id] = task
        self.active_task_id = task.id
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    async def broadcast_log(self, task_id: str, log_entry: Dict[str, Any]):
        for queue in self.log_queues:
            await queue.put({"task_id": task_id, "type": "log", "data": log_entry})

    async def update_state(self, task_id: str, status: TaskStatus):
        task = self.get_task(task_id)
        if task:
            task.status = status
            for queue in self.log_queues:
                await queue.put({
                    "task_id": task_id, 
                    "type": "state", 
                    "data": {"status": status.value}
                })

task_manager = TaskManager()
