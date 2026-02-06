from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

class Sandbox(ABC):
    @abstractmethod
    async def run_command(self, command: str, cwd: str = None, env: Dict[str, str] = None) -> Tuple[int, str, str]:
        """
        Run a command in the sandbox.
        Returns: (exit_code, stdout, stderr)
        """
        pass

    @abstractmethod
    def cleanup(self):
        """Destroy the sandbox resources."""
        pass
