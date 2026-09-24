# RemotePilot

Autonomous remote agent daemon: a FastAPI service (`daemon/`) that accepts a goal,
plans multi-step execution with an agent pipeline (planner → security screen → action
→ verifier → re-plan loop → synthesis), and streams logs over websocket. A Flutter
client lives in `ui/` (unverified in this pass).

## What actually works

- **Task lifecycle** — `POST /task/submit`, `GET /task/state/{id}`, `POST /task/schedule`
  (cron via APScheduler), `GET /metrics`, `WS /ws/logs`, Cloudflare tunnel start/stop.
- **Agent pipeline** — `daemon/agents/`: planner, router, action, verifier, monitor,
  memory, scheduler, safety, security, specialist, vision. The planner/vision call
  **Ollama at `http://localhost:11434`** — without a local Ollama the task lifecycle
  runs and then marks the task `FAILED` with a logged error (graceful, not a crash).
- **Token auth** — `daemon/auth.py`: every route except `GET /health` requires
  `Authorization: Bearer <token>` where the token is `REMOTEPILOT_TOKEN` (constant-time
  compare, never logged). The `/ws/logs` websocket takes `?token=`. Unset
  `REMOTEPILOT_TOKEN` = open dev mode (reported by `/health`).

## Hard limits (read before trusting this)

- ❌ **No real sandboxing.** `daemon/sandbox/local.py` is a plain subprocess shell;
  `COMMAND` actions in `action.py` run **un-sandboxed shell commands on the host**
  (the code itself admits this: "un-sandboxed in this poC, should use SandboxAgent").
  Do not expose this daemon to untrusted goals. Full sandboxing is out of scope for
  this pass and is documented as not done.
- Planner/vision need Ollama (`llama3.2` / `moondream` models) — not bundled.
- Native OS actions (click/type/hotkey) need `pyautogui` **and a display**; the daemon
  now boots headless (lazy import) and those actions return a clear error without one.
- Tunnel endpoints shell out to the `cloudflared` binary — must be installed separately;
  the tunnel token is passed from the request body.

## Quick start

```bash
cd daemon
pip install -r requirements.txt
export REMOTEPILOT_TOKEN="a-long-random-secret"   # never commit this
uvicorn main:app --host 127.0.0.1 --port 8000
```

```bash
curl localhost:8000/health
# {"status":"ok","auth":"token"}

curl -X POST localhost:8000/task/submit \
  -H "Authorization: Bearer $REMOTEPILOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"goal": "summarize the repo"}'
# -> {"task_id": "...", "status": "IDLE"}

curl localhost:8000/task/state/<task_id> \
  -H "Authorization: Bearer $REMOTEPILOT_TOKEN"
```

Without a token: `401 {"detail": "unauthorized: bad or missing token"}`.

## Layout

- `daemon/` — FastAPI daemon + agent pipeline
  - `main.py` — routes, task lifecycle
  - `auth.py` — token auth middleware (HTTP + websocket)
  - `task_manager.py`, `coordinator.py`, `memory_store.py`, `tunnels.py`
  - `agents/` — planner, action, verifier, monitor, memory, scheduler, safety,
    security, specialist, vision, router
  - `sandbox/` — placeholder; **not a real sandbox** (see limits)
- `ui/` — Flutter client (not exercised here)

## License

MIT — see `LICENSE`.
