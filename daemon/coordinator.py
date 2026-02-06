from typing import Dict, Any
from agents.base import Agent
from agents.router import ModelRouterAgent
from agents.planner import PlannerAgent
from agents.vision import VisionAgent
from agents.action import ActionAgent
from agents.security import SecurityAgent
from agents.verifier import VerifierAgent
from agents.specialist import ResearchAgent, DomainAgent
from agents.monitor import MonitorAgent
from agents.memory import MemoryAgent
from agents.scheduler import SchedulerAgent
from sandbox.local import ProcessSandbox
from logger import audit_logger

class Coordinator:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.router = ModelRouterAgent()
        self.planner = PlannerAgent()
        self.action = ActionAgent()
        self.vision = VisionAgent()
        self.security = SecurityAgent()
        self.verifier = VerifierAgent()
        self.monitor = MonitorAgent()
        self.memory = MemoryAgent()
        self.research = ResearchAgent()
        self.domain = DomainAgent()
        self.scheduler = None # Will be set by main.py
        self.sandbox = ProcessSandbox()
        
        # Wire dependencies
        self.verifier.set_vision_agent(self.vision)
        
        self.register_agent(self.router)
        self.register_agent(self.planner)
        self.register_agent(self.action)
        self.register_agent(self.vision)
        self.register_agent(self.security)
        self.register_agent(self.verifier)
        self.register_agent(self.monitor)
        self.register_agent(self.memory)
        self.register_agent(self.research)
        self.register_agent(self.domain)
        
    def register_agent(self, agent: Agent):
        self.agents[agent.name] = agent
        print(f"[Coordinator] Registered agent: {agent.name}")

    async def user_request(self, command: str):
        print(f"[Coordinator] Received request: {command}")
        audit_logger.log_event("USER_REQUEST", {"command": command})
        
        try:
            if command.startswith("list models"):
                return await self.router.execute({"command": "list_models"})
            
            if command.startswith("verify "):
                expectation = command[7:]
                res = await self.verifier.execute({"expectation": expectation})
                audit_logger.log_event("VERIFICATION", res)
                return res

            # Vision Command
            if command.startswith("see") or command.startswith("vision"):
                res = await self.vision.execute({"command": command, "model": "llava"})
                audit_logger.log_event("VISION_RESULT", res)
                return res

            if command.startswith("run "):
                # Legacy direct run - UNCHECKED for Phase 1/2 compatibility, 
                # but ideally should go through Safety too.
                # For Phase 3, let's Audit it.
                cmd_to_run = command[4:]
                audit_logger.log_event("LEGACY_RUN_START", {"cmd": cmd_to_run})
                res = await self.sandbox.run_command(cmd_to_run)
                audit_logger.log_event("LEGACY_RUN_END", {"result": res})
                return res
                
            if command.startswith("plan "):
                goal = command[5:]
                router_res = self.router.select_model("reasoning")
                selected_model = router_res.get("selected_model", "llama3")
                
                print(f"[Coordinator] Routing to Planner with model {selected_model}")
                plan_res = await self.planner.execute({
                    "goal": goal,
                    "model": selected_model
                })
                audit_logger.log_event("PLAN_GENERATED", plan_res)
                return plan_res

            if command.startswith("execute_plan "):
                # Expects JSON string of plan steps
                import json
                try:
                    plan_json = command[13:]
                    steps = json.loads(plan_json)
                    
                    # Resilience: Wrap in list if only one step was provided as a dict
                    if isinstance(steps, dict):
                        steps = [steps]
                    
                    if not isinstance(steps, list):
                        return {"status": "error", "error": "Plan must be a list of steps"}

                    # 1. SAFETY CHECK
                    safety_res = await self.safety.execute({"plan": steps})
                    audit_logger.log_event("SAFETY_CHECK", safety_res)
                    
                    if safety_res["status"] != "SAFE":
                        print(f"[Coordinator] BLOCKED by Safety: {safety_res['reason']}")
                        return {"status": "blocked", "reason": safety_res["reason"]}

                    # 2. EXECUTION
                    results = []
                    for step in steps:
                        action_type = step.get("action", "").upper()
                        print(f"[Coordinator] Step: {action_type} {step.get('value')}")
                        
                        if action_type == "COMMAND":
                            code, out, err = await self.sandbox.run_command(step.get("value"))
                            res = {"step": step, "status": "executed", "stdout": out, "stderr": err}
                        else:
                            res = await self.action.execute(step)
                            res = {"step": step, "result": res}
                        
                        results.append(res)
                        audit_logger.log_event("STEP_EXECUTED", res)
                            
                    return {"status": "success", "results": results}
                except json.JSONDecodeError:
                    return {"status": "error", "error": "Invalid plan JSON"}

        except Exception as e:
            print(f"[Coordinator] Error: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

        return {"status": "acknowledged", "summary": f"Coordinator received: {command}"}

# Singleton instance
coordinator = Coordinator()
