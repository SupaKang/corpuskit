"""RTK (rtk-ai/rtk) — discovery + version. External Apache-2.0 binary, used AS-IS
(no vendoring). Hook registration is handled by the agent adapter (PreToolUse/Bash)."""
import subprocess
from pathlib import Path

from ..core import platform as plat


def discover(cfg):
    b = cfg.get("compression.rtk.bin") or ""
    if b and Path(b).exists():
        return b
    w = plat.which("rtk")
    if w:
        return w
    cand = Path.home() / ".cargo" / "bin" / ("rtk.exe" if plat.is_windows() else "rtk")
    return str(cand) if cand.exists() else None


def version(bin_path):
    if not bin_path:
        return None
    try:
        r = subprocess.run([bin_path, "--version"], capture_output=True, text=True, timeout=10)
        return (r.stdout or r.stderr).strip() or None
    except Exception:
        return None


def install_hint(cfg):
    if plat.is_windows() and not plat.is_wsl():
        return ("Download rtk-x86_64-pc-windows-msvc.zip from github.com/rtk-ai/rtk/releases "
                "and put rtk.exe on PATH, or `cargo install --git https://github.com/rtk-ai/rtk --tag v0.42.4`.")
    return ("curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/master/install.sh | sh "
            "(or `cargo install --git https://github.com/rtk-ai/rtk --tag v0.42.4`).")
