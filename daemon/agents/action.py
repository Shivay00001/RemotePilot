import pyautogui
import platform
import asyncio
from typing import Dict, Any
from .base import Agent

class ActionAgent(Agent):
    def __init__(self):
        super().__init__(name="Action")
        # Safety: Fail-safe corner active
        pyautogui.FAILSAFE = True
        self.screen_width, self.screen_height = pyautogui.size()
        self.browser = None
        self.context = None
        self.page = None

    async def _ensure_browser(self):
        if not self.browser:
            pw = await async_playwright().start()
            self.browser = await pw.chromium.launch(headless=False)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input: {"action": "TYPE", "value": "hello"} or {"action": "BROWSE", "url": "..."}
        """
        action_type = task.get("action", "").upper()
        value = task.get("value", "")
        
        try:
            # --- Browser Actions ---
            if action_type == "BROWSE":
                await self._ensure_browser()
                url = task.get("url", value)
                await self.page.goto(url)
                # Extract text content for ResearchAgent
                content = await self.page.inner_text("body")
                return {
                    "status": "success", 
                    "detail": f"Navigated to {url}",
                    "content": content[:5000] # Limit content for LLM safety
                }

            elif action_type == "CLICK_BROWSER":
                await self._ensure_browser()
                selector = task.get("selector", value)
                await self.page.click(selector)
                return {"status": "success", "detail": f"Clicked browser element: {selector}"}

            # --- Native OS Actions ---
            elif action_type == "CLICK":
                # Expects "x y" or task has x,y
                x = task.get("x")
                y = task.get("y")
                if not x or not y:
                    coords = value.split()
                    if len(coords) == 2:
                        x, y = int(coords[0]), int(coords[1])
                
                if x is not None and y is not None:
                    pyautogui.click(x, y)
                    return {"status": "success", "detail": f"Clicked at {x}, {y}"}
                return {"status": "error", "error": "Missing coordinates"}

            elif action_type == "TYPE":
                pyautogui.write(value, interval=0.05)
                return {"status": "success", "detail": f"Typed: {value}"}

            elif action_type == "HOTKEY":
                keys = value.split('+')
                pyautogui.hotkey(*keys)
                return {"status": "success", "detail": f"Pressed: {value}"}

            elif action_type == "WAIT":
                time.sleep(float(value))
                return {"status": "success", "detail": f"Waited {value}s"}

            elif action_type == "COMMAND":
                # Legacy shell execution (un-sandboxed in this poC, should use SandboxAgent)
                process = subprocess.Popen(value, shell=True)
                return {"status": "success", "detail": f"Command started: {value}"}

            return {"status": "error", "error": f"Unknown action: {action_type}"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def cleanup(self):
        if self.browser:
            await self.browser.close()
