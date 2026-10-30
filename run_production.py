"""Production Container Entrypoint for Google Cloud Run.

Launches Google ADK CLI on port 8000 and the FastAPI Gateway on $PORT (default 8080).
"""

import os
import sys
import time
import subprocess
import uvicorn
from frontend_server import app

def main():
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"[Production] Launching Google ADK Runtime on port 8000...")
    adk_process = subprocess.Popen(
        [sys.executable, "-m", "google.adk.cli", "web", "."],
        env=os.environ.copy()
    )

    # Allow ADK server to initialize
    time.sleep(3)

    print(f"[Production] Starting Frontend Server on {host}:{port}...")
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    finally:
        print("[Production] Shutting down ADK server...")
        adk_process.terminate()
        adk_process.wait()

if __name__ == "__main__":
    main()
