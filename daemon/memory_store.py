import numpy as np
import requests
import json
import os
from typing import List, Dict, Any

class MemoryStore:
    def __init__(self, ollama_url="http://localhost:11434", storage_file="vector_memory.json"):
        self.ollama_url = ollama_url
        self.storage_file = storage_file
        self.memory: List[Dict[str, Any]] = []
        self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    self.memory = json.load(f)
            except:
                self.memory = []

    def _save_memory(self):
        with open(self.storage_file, 'w') as f:
            json.dump(self.memory, f)

    async def get_embedding(self, text: str) -> List[float]:
        import asyncio
        try:
            res = await asyncio.to_thread(
                requests.post,
                f"{self.ollama_url}/api/embeddings", 
                json={
                    "model": "nomic-embed-text",
                    "prompt": text
                }, 
                timeout=5
            )
            if res.status_code == 200:
                return res.json().get("embedding", [])
        except:
            pass
        return []

    async def add_interaction(self, goal: str, plan: List[Dict[str, Any]]):
        embedding = await self.get_embedding(goal)
        if embedding:
            self.memory.append({
                "goal": goal,
                "plan": plan,
                "vector": embedding
            })
            self._save_memory()

    async def retrieve_relevant(self, goal: str, top_k: int = 2) -> List[Dict[str, Any]]:
        query_vec = await self.get_embedding(goal)
        if not query_vec or not self.memory:
            return []

        # Cosine Similarity
        scores = []
        q_v = np.array(query_vec)
        for item in self.memory:
            i_v = np.array(item["vector"])
            score = np.dot(q_v, i_v) / (np.linalg.norm(q_v) * np.linalg.norm(i_v))
            scores.append((score, item))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scores[:top_k] if s[0] > 0.7] # Only highly relevant

memory_store = MemoryStore()
