from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
import json
from typing import Optional, Dict, Any, List

from task_manager import task_manager, TaskStatus
from coordinator import coordinator

app = FastAPI(title="RemotePilot Daemon", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class TaskSubmitRequest(BaseModel):
    goal: str

@app.get("/")
async def root():
    return {"status": "RemotePilot Online", "version": "1.0.0"}

@app.post("/task/submit")
async def submit_task(req: TaskSubmitRequest):
    task = task_manager.create_task(req.goal)
    # Start task processing in background
    asyncio.create_task(process_task(task.id))
    return {"task_id": task.id, "status": task.status}

@app.get("/task/state/{task_id}")
async def get_task_state(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": task.id,
        "status": task.status,
        "goal": task.goal,
        "plan": task.plan,
        "logs": task.logs
    }

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    queue = asyncio.Queue()
    task_manager.log_queues.append(queue)
    try:
        while True:
            data = await queue.get()
            await websocket.send_json(data)
    except WebSocketDisconnect:
        task_manager.log_queues.remove(queue)

async def process_task(task_id: str):
    print(f"\n[Lifecycle] STARTING TASK: {task_id}")
    task = task_manager.get_task(task_id)
    if not task: return

    coordinator.monitor.reset()
    try:
        # 1. SECURITY & PLANNING
        print(f"[Lifecycle] {task_id} -> PHASE: PLANNING")
        await task_manager.update_state(task_id, TaskStatus.PLANNING)
        plan_res = await coordinator.planner.execute({"goal": task.goal})
        
        if plan_res["status"] != "success":
            raise Exception(f"Planning failed: {plan_res.get('error')}")
            
        task.plan = plan_res.get("plan", [])
        
        # Security Screening
        sec_res = await coordinator.security.execute({"plan": task.plan})
        if sec_res["status"] == "BLOCKED":
            raise Exception(f"Security Alert: {sec_res['reason']}")

        log = task.add_log("Planner", f"Generated & Secured {len(task.plan)} steps.")
        print(f"[Lifecycle] {task_id} -> PLAN SECURED ({len(task.plan)} steps)")
        await task_manager.broadcast_log(task_id, log)

        # 2. MODEL_CHECK
        await task_manager.update_state(task_id, TaskStatus.MODEL_CHECK)
        
        # 3. SANDBOX_SETUP
        await task_manager.update_state(task_id, TaskStatus.SANDBOX_SETUP)
        
        # 4. EXECUTION LOOP with SELF-CORRECTION
        research_fragments = []
        step_index = 0
        retry_count = 0
        max_retries = 10 # Allow the agent to pivot many times

        while step_index < len(task.plan) and retry_count < max_retries:
            step = task.plan[step_index]
            
            # ACT
            await task_manager.update_state(task_id, TaskStatus.ACT)
            action_res = await coordinator.action.execute(step)
            
            if action_res.get("content"):
                research_fragments.append(action_res["content"])
            
            log = task.add_log("Action", f"Step {step_index+1}: {action_res.get('detail', 'Executed')}")
            await task_manager.broadcast_log(task_id, log)

            # VERIFY
            await task_manager.update_state(task_id, TaskStatus.VERIFY)
            verify_res = await coordinator.verifier.execute({
                "expectation": f"Goal state after action: {step.get('action')}"
            })
            
            if verify_res.get("verified"):
                step_index += 1
                retry_count = 0 # Reset retries on success
            else:
                # SELF-CORRECTION TRIGGER
                retry_count += 1
                await task_manager.update_state(task_id, TaskStatus.PLANNING)
                log = task.add_log("Monitor", f"Verification FAILED. Triggering Re-Plan (Attempt {retry_count}).", "WARNING")
                await task_manager.broadcast_log(task_id, log)
                
                # Get current UI state for context
                vision_context = await coordinator.vision.execute({"command": "Describe detailed UI state", "model": "llava"})
                
                replan_res = await coordinator.planner.re_plan({
                    "goal": task.goal,
                    "failed_step": step,
                    "error": verify_res.get("details", "Visual mismatch"),
                    "vision_context": vision_context.get("description", "VLM context missing")
                })
                
                if replan_res["status"] == "success":
                    task.plan = replan_res["plan"]
                    step_index = 0 # Restart from new plan
                    log = task.add_log("Planner", "Pivot successful. New plan generated.")
                    await task_manager.broadcast_log(task_id, log)
                else:
                    raise Exception(f"Self-correction failed: {replan_res.get('error')}")

        # 5. SPECIALIST SYNTHESIS
        if research_fragments:
            summary_res = await coordinator.research.execute({"topic": task.goal, "pages": research_fragments})
            log = task.add_log("Research", summary_res.get("data", {}).get("summary", "Synthesis done."))
            await task_manager.broadcast_log(task_id, log)

        await task_manager.update_state(task_id, TaskStatus.DONE)
        
        # 6. STORE MEMORY (RAG & HISTORY)
        from memory_store import memory_store
        await memory_store.add_interaction(task.goal, task.plan)
        
        await coordinator.memory.execute({
            "action": "store", 
            "data": {"id": task_id, "goal": task.goal, "plan": task.plan, "status": "DONE"}
        })

    except Exception as e:
        log = task.add_log("Monitor", f"CRITICAL: {str(e)}", "ERROR")
        await task_manager.broadcast_log(task_id, log)
        await task_manager.update_state(task_id, TaskStatus.FAILED)
        await coordinator.memory.execute({
            "action": "store", 
            "data": {"id": task_id, "goal": task.goal, "plan": task.plan, "status": "FAILED"}
        })

from tunnels import tunnel_manager

# ... existing app and routes ...

class TunnelRequest(BaseModel):
    token: str

@app.post("/tunnel/start")
async def start_tunnel(req: TunnelRequest):
    tunnel_manager.start_tunnel(req.token)
    return {"status": "Tunnel starting..."}

@app.post("/tunnel/stop")
async def stop_tunnel():
    tunnel_manager.stop_tunnel()
    return {"status": "Tunnel stopping..."}

async def submit_task_callback(goal: str):
    task = task_manager.create_task(goal)
    asyncio.create_task(process_task(task.id))

@app.on_event("startup")
async def startup_event():
    try:
        from agents.scheduler import SchedulerAgent
        coordinator.scheduler = SchedulerAgent(submit_task_callback)
        coordinator.register_agent(coordinator.scheduler)
        print("[System] Startup complete.")
    except Exception as e:
        print(f"[System] Startup error: {e}")
        import traceback
        traceback.print_exc()

@app.get("/metrics")
async def get_metrics():
    return await coordinator.monitor.execute({"action": "check_health"})

@app.post("/task/schedule")
async def schedule_task(req: TaskSubmitRequest, cron: str):
    res = await coordinator.scheduler.execute({"action": "schedule", "goal": req.goal, "cron": cron})
    return res

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
