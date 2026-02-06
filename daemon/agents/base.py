from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class Agent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's specific task."""
        pass

    def log(self, message: str):
        print(f"[{self.name}] {message}")
