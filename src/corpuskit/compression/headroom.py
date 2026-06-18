"""Headroom (chopratejas/headroom) — discovery, version, proxy exe, port probe.
External Apache-2.0 package, used AS-IS via pip (no vendoring)."""
import socket
import subprocess
from pathlib import Path

from ..core import platform as plat


def python_bin(cfg):
    return plat.discover_python(
        cfg.get("compression.headroom.python") or cfg.get("agent.python") or "")


def installed(py):
    if not py:
        return None
    try:
        r = subprocess.run(
            [py, "-c", "import importlib.metadata as m; print(m.version('headroom-ai'))"],
            capture_output=True, text=True, timeout=25)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def proxy_exe(py):
    if not py:
        return None
    p = Path(py).parent
    cand = p / ("headroom.exe" if plat.is_windows() else "headroom")
    return str(cand) if cand.exists() else None


def port_open(port):
    if not port:
        return False
    s = socket.socket()
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", int(port)))
        return True
    except Exception:
        return False
    finally:
        s.close()
