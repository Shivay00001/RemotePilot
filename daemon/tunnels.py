import subprocess
import os
import signal
import threading
import time
from typing import Optional

class TunnelManager:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.public_url: Optional[str] = None

    def start_tunnel(self, token: str):
        """
        Starts cloudflared with the provided tunnel token.
        Expects cloudflared.exe to be in the PATH or same directory.
        """
        if self.process:
            self.stop_tunnel()

        print(f"[Tunnel] Starting Cloudflare Tunnel...")
        
        # Command to run cloudflared
        cmd = ["cloudflared", "tunnel", "--no-autoupdate", "run", "--token", token]
        
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Start a thread to monitor output for the URL or errors
            threading.Thread(target=self._monitor_tunnel, daemon=True).start()
            
        except FileNotFoundError:
            print("[Tunnel] Error: 'cloudflared' not found. Please install it.")
        except Exception as e:
            print(f"[Tunnel] Error starting tunnel: {e}")

    def _monitor_tunnel(self):
        if not self.process: return
        
        for line in self.process.stderr:
            # Cloudflared typically logs to stderr
            # print(f"[Cloudflared] {line.strip()}")
            if "Registered tunnel connection" in line:
                print("[Tunnel] Connection registered successfully.")
            if "Failed to create" in line:
                print(f"[Tunnel] Error: {line.strip()}")

    def stop_tunnel(self):
        if self.process:
            print("[Tunnel] Stopping tunnel...")
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)], capture_output=True)
            else:
                self.process.terminate()
            self.process = None
            self.public_url = None

tunnel_manager = TunnelManager()
