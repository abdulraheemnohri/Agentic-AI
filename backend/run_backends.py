"""Development launcher for the two dedicated backend processes."""
from __future__ import annotations
import subprocess
import sys


def main() -> None:
    commands = [
        [sys.executable, "-m", "uvicorn", "backend.system1_server:app", "--host", "127.0.0.1", "--port", "8101"],
        [sys.executable, "-m", "uvicorn", "backend.system2_server:app", "--host", "127.0.0.1", "--port", "8102"],
    ]
    processes = [subprocess.Popen(command) for command in commands]
    try:
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        for process in processes:
            process.terminate()
        for process in processes:
            process.wait()


if __name__ == "__main__":
    main()
