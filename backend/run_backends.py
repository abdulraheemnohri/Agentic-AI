"""
Development launcher for the three backend processes:
- System 1 Authority (port 8101)
- System 2 Intelligence (port 8102)
- Main Backend (port 8000)
"""
from __future__ import annotations
import subprocess
import sys
import time


def main() -> None:
    print("Starting Agentic-AI backends...")
    print("=" * 50)

    # Start System 1 Authority Backend (port 8101)
    print("Starting System 1 Authority Backend (127.0.0.1:8101)...")
    system1_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.system1.server:app", "--host", "127.0.0.1", "--port", "8101"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)  # Wait for System 1 to start

    # Start System 2 Intelligence Backend (port 8102)
    print("Starting System 2 Intelligence Backend (127.0.0.1:8102)...")
    system2_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.system2.server:app", "--host", "127.0.0.1", "--port", "8102"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)  # Wait for System 2 to start

    # Start Main Backend (port 8000)
    print("Starting Main Backend (127.0.0.1:8000)...")
    main_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    print("=" * 50)
    print("All backends are running:")
    print("- System 1: http://127.0.0.1:8101")
    print("- System 2: http://127.0.0.1:8102")
    print("- Main Backend: http://127.0.0.1:8000")
    print("Press Ctrl+C to stop all backends.")
    print("=" * 50)

    try:
        # Wait for all processes to complete
        for process in [system1_process, system2_process, main_process]:
            process.wait()
    except KeyboardInterrupt:
        print("\nStopping all backends...")
        for process in [system1_process, system2_process, main_process]:
            process.terminate()
        for process in [system1_process, system2_process, main_process]:
            process.wait()
        print("All backends stopped.")


if __name__ == "__main__":
    main()
