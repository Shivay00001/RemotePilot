from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from typing import Dict, Any
from .base import Agent

class SchedulerAgent(Agent):
    def __init__(self, task_submit_callback):
        super().__init__(name="Scheduler")
        self.scheduler = AsyncIOScheduler()
        self.submit_callback = task_submit_callback
        self.scheduler.start()

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input: {"action": "schedule", "goal": "...", "cron": "0 10 * * *"}
        """
        action = task.get("action", "schedule")
        goal = task.get("goal")
        cron = task.get("cron") # e.g. "*/5 * * * *" for every 5 mins
        
        if action == "schedule" and goal and cron:
            job_id = f"job_{int(datetime.now().timestamp())}"
            self.scheduler.add_job(
                self.submit_callback, 
                'cron', 
                args=[goal],
                minute=cron.split()[0],
                hour=cron.split()[1],
                day=cron.split()[2],
                month=cron.split()[3],
                day_of_week=cron.split()[4],
                id=job_id
            )
            return {"status": "success", "job_id": job_id}

        return {"status": "error", "error": "Invalid schedule params"}

    def list_jobs(self):
        return [{"id": j.id, "next_run": str(j.next_run_time)} for j in self.scheduler.get_jobs()]
