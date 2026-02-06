import requests
from typing import Dict, Any, List
from .base import Agent

class ModelRouterAgent(Agent):
    def __init__(self):
        super().__init__(name="ModelRouter")
        self.ollama_url = "http://localhost:11434"
        self.available_models: List[str] = []

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        command = task.get("command")
        if command == "list_models":
            return self.list_models()
        elif command == "select_model":
            return self.select_model(task.get("intent", "general"))
        return {"error": "Unknown command"}

    def list_models(self) -> Dict[str, Any]:
        print(f"[ModelRouter] Fetching models from {self.ollama_url}...")
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            print(f"[ModelRouter] Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.available_models = [model['name'] for model in data.get('models', [])]
                self.log(f"Found models: {self.available_models}")
                return {"models": self.available_models}
            else:
                print(f"[ModelRouter] Error body: {response.text}")
                return {"error": f"Failed to fetch models: {response.text}"}
        except Exception as e:
            print(f"[ModelRouter] Exception: {e}")
            return {"error": f"Ollama connection error: {str(e)}"}

    def select_model(self, intent: str) -> Dict[str, Any]:
        # Simple heuristic for now
        self.list_models() # Refresh
        
        # Priority mapping
        priorities = {
            "coding": ["qwen", "deepseek-coder", "codellama"],
            "vision": ["llava", "moondream"],
            "reasoning": ["llama3.2", "llama3", "mistral", "gemma", "qwen"]
        }
        
        candidates = priorities.get(intent, priorities["general"])
        
        # Check if we have any candidate
        for candidate in candidates:
            # simple substring match
            for model in self.available_models:
                if candidate in model:
                    return {"selected_model": model}
        
        # Fallback to first available or error
        if self.available_models:
            return {"selected_model": self.available_models[0], "warning": "Fallback model selected"}
            
        return {"error": "No models available"}
