from typing import Dict, Any, List
import requests
import json
from .base import Agent

class ResearchAgent(Agent):
    def __init__(self, ollama_url="http://localhost:11434"):
        super().__init__(name="Research")
        self.ollama_url = ollama_url

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input: {"topic": "latest AI news", "pages": [...text content from tabs...]}
        Output: {"summary": "...", "sources": [...]}
        """
        topic = task.get("topic", "")
        pages_content = task.get("pages", [])
        
        prompt = f"""
You are a Research Analyst. 
Topic: {topic}

Below is content from multiple web pages. 
Synthesize a comprehensive summary of the findings. 
Be concise but thorough.

Content:
{" ".join(pages_content)[:8000]} 

Output JSON ONLY:
{{
  "summary": "...",
  "key_findings": ["...", "..."],
  "sources_analyzed": {len(pages_content)}
}}
"""
        try:
            import asyncio
            response = await asyncio.to_thread(
                requests.post,
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {"status": "success", "data": json.loads(result.get("response", "{}"))}
            else:
                return {"status": "error", "error": f"Ollama Error: {response.text}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

class DomainAgent(Agent):
    def __init__(self, ollama_url="http://localhost:11434"):
        super().__init__(name="Domain")
        self.ollama_url = ollama_url

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specialized prompts for Gmail, Outlook, etc.
        Input: {"domain": "gmail", "goal": "send email to bob", "context": "..."}
        """
        # This agent primarily generates BROWSER selectors or instructions for ActionAgent
        # by understanding specific web UI patterns.
        domain = task.get("domain", "")
        goal = task.get("goal", "")
        
        # In a real implementation, this would have a library of 'recipes'
        # or use LLM to map goal -> specific browser actions for known domains.
        return {"status": "success", "instructions": f"Specialized path for {domain} engaged for {goal}"}
