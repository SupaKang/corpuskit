"""Cross-platform helpers: interpreter discovery, OS/WSL detect, which, free port."""
import os
import shutil
import socket
import sys
from pathlib import Path


def discover_python(configured=""):
    return configured or sys.executable


def is_windows():
    return os.name == "nt"


def is_wsl():
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except Exception:
        return False


def which(name):
    return shutil.which(name)


def free_port():
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
    finally:
        s.close()


def claude_settings_path():
    return Path.home() / ".claude" / "settings.json"
