"""
Token auth for the RemotePilot daemon.

The bearer token comes from the REMOTEPILOT_TOKEN env var:
    - every HTTP route except /health requires
      `Authorization: Bearer <token>` (401 otherwise, constant-time compare);
    - the /ws/logs websocket accepts the token as a `?token=` query param
      (browsers can't set custom WS headers);
    - if REMOTEPILOT_TOKEN is unset, the daemon runs OPEN (dev only) and
      /health reports auth: "open".

The token value is never logged or printed.
"""

import hmac
import os
from urllib.parse import parse_qs

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

TOKEN = os.environ.get("REMOTEPILOT_TOKEN", "")

PUBLIC_PATHS = {"/health"}


def _valid(provided: str) -> bool:
    if not TOKEN or not provided:
        return False
    return hmac.compare_digest(provided, TOKEN)


class TokenAuthMiddleware:
    """Pure-ASGI auth covering both HTTP and websocket scopes."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in PUBLIC_PATHS or not TOKEN:
            await self.app(scope, receive, send)
            return

        if scope["type"] == "websocket":
            qs = parse_qs(scope.get("query_string", b"").decode())
            ok = _valid(qs.get("token", [""])[0])
        else:
            headers = dict(scope.get("headers", []))
            auth = headers.get(b"authorization", b"").decode()
            ok = auth.startswith("Bearer ") and _valid(auth[len("Bearer "):].strip())

        if not ok:
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 4401})
            else:
                resp = JSONResponse({"detail": "unauthorized: bad or missing token"}, status_code=401)
                await resp(scope, receive, send)
            return

        await self.app(scope, receive, send)


def auth_mode() -> str:
    return "token" if TOKEN else "open (REMOTEPILOT_TOKEN not set)"
