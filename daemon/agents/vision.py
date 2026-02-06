import io
import base64
import pyautogui
from PIL import Image
import requests
from typing import Dict, Any
from .base import Agent

class VisionAgent(Agent):
    def __init__(self, ollama_url="http://localhost:11434"):
        super().__init__(name="Vision")
        self.ollama_url = ollama_url

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input: {"command": "describe screen", "model": "moondream"}
        """
        command = task.get("command", "")
        model = task.get("model", "moondream") 
        
        # 1. Capture Screenshot
        try:
            screenshot = pyautogui.screenshot()
            
            # Convert to Base64
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            # 2. Query Ollama
            print(f"[Vision] Analyzing screen with {model}...")
            
            prompt = "Describe this image briefly."
            if "describe" in command:
                prompt = "Describe the UI elements visible on the screen."
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "images": [img_str],
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {"status": "success", "description": result.get("response", "")}
            else:
                return {"status": "error", "error": f"Ollama Vision Error: {response.text}"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
