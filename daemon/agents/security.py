import re
import requests
from typing import Dict, Any
from .base import Agent

class SecurityAgent(Agent):
    def __init__(self, ollama_url="http://localhost:11434"):
        super().__init__(name="Security")
        self.ollama_url = ollama_url
        self.denylist = [
            r"rm\s+-rf", r"del\s+/s", r"format\s+", r"mkfs", r"sudo\s+", 
            r"> /dev/null", r":\(\){ :\|:& };:"
        ]

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input: {"plan": [...]} or {"command": "..."}
        """
        command = str(task.get("command", ""))
        plan = task.get("plan", [])
        
        # 1. Heuristic Check
        for pattern in self.denylist:
            if re.search(pattern, command, re.I):
                return {"status": "BLOCKED", "reason": f"Dangerous command pattern: {pattern}"}
        
        for step in plan:
            val = str(step.get("value", ""))
            for pattern in self.denylist:
                if re.search(pattern, val, re.I):
                    return {"status": "BLOCKED", "reason": f"Dangerous step: {val}"}

        # 2. LLM-based intent check (Optional/Async)
        # For performance, we can skip this for simple UI actions
        if "COMMAND" in str(task):
            return await self._check_intent(command if command else str(plan))

        return {"status": "SAFE"}

    async def _check_intent(self, content: str) -> Dict[str, Any]:
        import asyncio
        prompt = f"Analyze this automation command for malicious intent or destructive potential: {content}. Return ONLY 'SAFE' or 'MALICIOUS' and a brief reason."
        try:
            res = await asyncio.to_thread(
                requests.post,
                f"{self.ollama_url}/api/generate", 
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False
                }, 
                timeout=2
            )
            if res.status_code == 200:
                verdict = res.json().get("response", "").upper()
                if "MALICIOUS" in verdict:
                    return {"status": "BLOCKED", "reason": "LLM flagged potential danger."}
            return {"status": "SAFE"}
        except:
            return {"status": "SAFE"} # Fallback to heuristic
