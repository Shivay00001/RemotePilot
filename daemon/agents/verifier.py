from typing import Dict, Any
from .base import Agent
# We need VisionAgent, but importing might cause circular dep if not careful.
# Ideally, we pass VisionAgent instance or use dependency injection.
# For this phase, we'll assume Coordinator passes it or we import inside method.

class VerifierAgent(Agent):
    def __init__(self, vision_agent=None):
        super().__init__(name="Verifier")
        self.vision_agent = vision_agent

    def set_vision_agent(self, agent):
        self.vision_agent = agent

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input: {"expectation": "A success message is visible", "capture": True}
        """
        expectation = task.get("expectation", "")
        
        if not self.vision_agent:
            return {"status": "error", "error": "Vision Agent not connected"}
            
        print(f"[Verifier] Verifying visually: {expectation}")
        
        # 1. Capture screen via VisionAgent setup
        # VisionAgent.execute with 'describe' or custom prompt
        res = await self.vision_agent.execute({
            "command": f"Verify: {expectation}. Return JSON with 'match' (bool) and 'reason' (string).",
            "model": "llava"
        })
        
        if res.get("status") == "success":
            desc = res.get("description", "")
            # Expecting model to follow JSON if prompted, but we add a heuristic 
            # for standard LLM text output as fallback
            match = "YES" in desc.upper() or "TRUE" in desc.upper()
            
            return {
                "status": "success", 
                "verified": match, 
                "details": desc
            }
        else:
            return {"status": "error", "error": "Vision verification failed", "detail": res.get("error")}
