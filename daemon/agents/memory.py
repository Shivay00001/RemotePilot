import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List
from .base import Agent

class MemoryAgent(Agent):
    def __init__(self, db_path="memory.db"):
        super().__init__(name="Memory")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id TEXT PRIMARY KEY,
                goal TEXT,
                plan TEXT,
                status TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input: {"action": "store", "data": {...}} or {"action": "retrieve", "query": "..."}
        """
        action = task.get("action", "store")
        
        if action == "store":
            data = task.get("data", {})
            conn = sqlite3.connect(self.db_path)
            conn.execute("INSERT OR REPLACE INTO history VALUES (?, ?, ?, ?, ?)", (
                data.get("id"),
                data.get("goal"),
                json.dumps(data.get("plan")),
                data.get("status"),
                datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
            return {"status": "success"}

        elif action == "retrieve":
            # Simple retrieval for now
            return {"status": "success", "history": []}

        return {"status": "idle"}
