import subprocess
import os
import asyncio
from typing import Dict, Tuple
from .base import Sandbox

class ProcessSandbox(Sandbox):
    def __init__(self):
        self.active_processes = []

    async def run_command(self, command: str, cwd: str = None, env: Dict[str, str] = None) -> Tuple[int, str, str]:
        # Security: Default to empty env to prevent inheriting sensitive host vars
        safe_env = env if env else {}
        
        # Ensure we don't allow crazy paths
        # On Windows, we can't easily chroot without containers, 
        # but we can restrict the environment and use specific users if configured.
        # For Phase 1 PoC, we rely on specific safe_env.

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=safe_env
            )
            self.active_processes.append(process)
            
            stdout, stderr = await process.communicate()
            
            return (
                process.returncode,
                stdout.decode() if stdout else "",
                stderr.decode() if stderr else ""
            )
        except Exception as e:
            return (-1, "", str(e))
        finally:
            if process in self.active_processes:
                self.active_processes.remove(process)

    def cleanup(self):
        for proc in self.active_processes:
            try:
                proc.terminate()
            except:
                pass
        self.active_processes = []
