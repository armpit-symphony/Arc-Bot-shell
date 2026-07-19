from __future__ import annotations

import subprocess
import sys

from arc_bot_shell.service.pidfile import process_is_alive


def test_process_liveness_detects_spawned_python_process() -> None:
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        assert process_is_alive(process.pid) is True
    finally:
        process.terminate()
        process.wait(timeout=5)
    assert process_is_alive(process.pid) is False
