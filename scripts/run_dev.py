"""Concurrent dev runner for backend and frontend."""

import os
import signal
import subprocess
import sys
import time

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

# Pick python binary
venv_python = (
    os.path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe")
    if os.name == "nt"
    else os.path.join(BACKEND_DIR, ".venv", "bin", "python")
)
python_bin = venv_python if os.path.exists(venv_python) else sys.executable
npm_cmd = "npm.cmd" if os.name == "nt" else "npm"


def main() -> None:
    print("[dev] Starting Live Medical Transcription Dev Environment...")
    backend_proc = subprocess.Popen(
        [python_bin, "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BACKEND_DIR,
    )

    frontend_proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=FRONTEND_DIR,
    )

    def shutdown(signum: int, frame: object) -> None:
        print("\n[dev] Shutting down backend and frontend...")
        frontend_proc.terminate()
        backend_proc.terminate()
        frontend_proc.wait()
        backend_proc.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print("[dev] Backend process exited.")
                break
            if frontend_proc.poll() is not None:
                print("[dev] Frontend process exited.")
                break
    except KeyboardInterrupt:
        shutdown(0, None)


if __name__ == "__main__":
    main()
