import requests
import json
from typing import Dict, Any, List
from .base import Agent

class PlannerAgent(Agent):
    def __init__(self, ollama_url="http://localhost:11434"):
        super().__init__(name="Planner")
        self.ollama_url = ollama_url

    async def re_plan(self, task: Dict[str, Any]) -> Dict[str, Any]:
        goal = task.get("goal")
        failed_step = task.get("failed_step")
        error = task.get("error")
        vision = task.get("vision_context", "Unknown UI state")

        prompt = f"""
RE-PLANNING REQUIRED.
Original Goal: {goal}
The step {failed_step} FAILED with error: {error}.
Current Screen State: {vision}

Generate a NEW plan to achieve the original goal starting from this state. 
Be creative. If one method failed, try a different approach (e.g., instead of a click, use a hotkey).

Output a JSON LIST ONLY.
"""
        return await self._call_ollama(prompt, task.get("model", "llama3.2"))

    async def _call_ollama(self, prompt, model):
        try:
            import asyncio
            response = await asyncio.to_thread(
                requests.post,
                f"{self.ollama_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False, "format": "json"},
                timeout=30
            )
            if response.status_code == 200:
                content = response.json().get("response", "")
                try:
                    data = json.loads(content)
                    if isinstance(data, dict) and "plan" in data:
                        data = data["plan"]
                    if not isinstance(data, list):
                        data = [data]
                    return {"status": "success", "plan": data}
                except json.JSONDecodeError:
                    return {"status": "error", "error": f"Invalid JSON: {content}"}
            return {"status": "error", "error": f"Ollama Error: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        goal = task.get("goal")
        model = task.get("model", "llama3.2")
        
        # 1. SEMANTIC RETRIEVAL
        history_context = ""
        try:
            from memory_store import memory_store
            relevant_history = await memory_store.retrieve_relevant(goal)
            if relevant_history:
                history_context = "\nSimilar successful plans from history:\n"
                for item in relevant_history:
                    history_context += f"- Goal: {item['goal']}\n  Plan: {json.dumps(item['plan'])}\n"
        except Exception as e:
            print(f"[Planner] Memory retrieval skipped: {e}")

        prompt = f"""
You are an expert system automation planner. 
Your job is to convert the User's Goal into a strict JSON LIST of atomic actions.
{history_context}
Available Actions:
- COMMAND: Run a shell command
- TYPE: Type text
- HOTKEY: Press key combo
- CLICK: Click at coordinates
- WAIT: Wait for seconds
- BROWSE: Open a website URL
- CLICK_BROWSER: Click a CSS selector

User Goal: {goal}

Output a JSON LIST ONLY.
"""
        return await self._call_ollama(prompt, model)
