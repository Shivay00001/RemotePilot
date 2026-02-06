from typing import Dict, Any, List
from .base import Agent

class SafetyAgent(Agent):
    def __init__(self):
        super().__init__(name="Safety")
        self.forbidden_keywords = [
            "rm -rf", "format", "mkfs", "dd if=", ":(){ :|:& };:", # Fork bomb
            "shutdown", "reboot", "del /s /q", "rd /s /q"
        ]

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input: {"plan": [...]}
        Output: {"status": "SAFE" | "UNSAFE", "reason": "..."}
        """
        plan = task.get("plan", [])
        
        for step in plan:
            action_type = step.get("action", "").upper()
            value = step.get("value", "").lower()
            
            # Check for generic forbidden keywords in any command/value
            for keyword in self.forbidden_keywords:
                if keyword in value:
                    return {
                        "status": "UNSAFE", 
                        "reason": f"Forbidden keyword detected: {keyword} in step {step}"
                    }
                    
            # Specific heuristic: Command length limits?
            # if len(value) > 1000: return {"status": "UNSAFE", "reason": "Command too long"}

        return {"status": "SAFE", "reason": "No threats detected"}
