"""FastAPI Web Server for Carbon Coach Custom Frontend.

Serves the modern emerald glassmorphism dashboard on port 3000 and bridges
requests seamlessly to the Google ADK server on port 8000 without CORS issues.
"""

import json
import urllib.request
import os
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Carbon Coach Frontend Server")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
ADK_BACKEND_URL = "http://127.0.0.1:8000"

# Mount static assets
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.post("/api/session")
async def create_session(user_id: str = "demo_user"):
    """Creates a new session in the ADK backend."""
    url = f"{ADK_BACKEND_URL}/apps/carbon_coach/users/{user_id}/sessions"
    req = urllib.request.Request(
        url,
        data=json.dumps({}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except Exception as e:
        return {"error": str(e), "id": "fallback_session"}


@app.get("/api/session-state")
async def get_session_state(session_id: str, user_id: str = "demo_user"):
    """Fetches real-time session state including activities from ADK."""
    url = f"{ADK_BACKEND_URL}/apps/carbon_coach/users/{user_id}/sessions/{session_id}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except Exception as e:
        return {"error": str(e), "state": {"activities": []}}


@app.post("/api/run")
async def run_agent(request: Request):
    """Proxies user conversation turns to ADK /run."""
    body = await request.body()
    url = f"{ADK_BACKEND_URL}/run"
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            events = json.loads(resp.read().decode("utf-8"))
            return events
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    host = os.environ.get("HOST", "0.0.0.0")
    print("\n" + "=" * 60)
    print(f"Carbon Coach Premium Dashboard starting on http://{host}:{port}")
    print("Connecting to Google ADK Backend on http://127.0.0.1:8000")
    print("=" * 60 + "\n")
    uvicorn.run(app, host=host, port=port, log_level="info")
