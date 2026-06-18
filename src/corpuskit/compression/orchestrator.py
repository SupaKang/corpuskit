"""Compression orchestrator — lifecycle over external RTK (tool layer) + Headroom
(transport proxy). Fixed order rtk->headroom. Shells out; never vendors."""
import json
import os
import subprocess
import time

from ..core import platform as plat
from . import compat, headroom, rtk

STATE = ".corpuskit/compression.json"


class Orchestrator:
    def __init__(self, cfg):
        self.cfg = cfg
        order = cfg.get("compression.order", ["rtk", "headroom"])
        if list(order) != ["rtk", "headroom"]:
            raise ValueError("compression.order must be [rtk, headroom] (fixed; reversal rejected)")
        self.state_path = cfg.resolve(STATE)

    def discover(self):
        py = headroom.python_bin(self.cfg)
        return {
            "rtk_bin": rtk.discover(self.cfg),
            "headroom_python": py,
            "headroom_version": headroom.installed(py),
            "headroom_proxy_ready": headroom.proxy_ready(py),
            "headroom_exe": headroom.proxy_exe(py),
        }

    def _state(self):
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def status(self):
        d = self.discover()
        st = self._state()
        port = st.get("port") or self.cfg.get("compression.headroom.port") or 0
        d["proxy_running"] = headroom.port_open(port)
        d["state"] = st
        return d

    def health(self):
        d = self.discover()
        issues = []
        if not d["rtk_bin"]:
            issues.append(["warn", "RTK not found. Shell-output (Layer 1) compression disabled. " + rtk.install_hint(self.cfg)])
        else:
            lvl, msg = compat.check("rtk", rtk.version(d["rtk_bin"]))
            if lvl != "ok":
                issues.append([lvl, msg])
        if not d["headroom_version"]:
            issues.append(["warn", "Headroom not installed in configured python. Run `corpus compression install`."])
        else:
            lvl, msg = compat.check("headroom", d["headroom_version"])
            if lvl != "ok":
                issues.append([lvl, msg])
        if plat.is_windows() and not plat.is_wsl():
            mode = self.cfg.get("compression.native_windows", "degrade")
            issues.append([("error" if mode == "error" else "info"),
                           "native Windows: RTK PreToolUse(Bash) hook degrades to CLAUDE.md-injection; "
                           "rely on Headroom-solo transport proxy for automatic savings, or use WSL for the RTK hook."])
        return {"discover": d, "issues": issues}

    def install(self):
        d = self.discover()
        steps = []
        if not d["headroom_version"] or not d["headroom_proxy_ready"]:
            py = headroom.python_bin(self.cfg)
            ver = self.cfg.get("compression.headroom.version", "~=0.26")
            try:
                subprocess.run([py, "-m", "pip", "install", f"headroom-ai[proxy]{ver}"], check=True, timeout=900)
                steps.append("installed headroom-ai[proxy]")
            except Exception as e:
                steps.append(f"headroom install failed: {e}; pip install headroom-ai[proxy]{ver} manually")
        else:
            steps.append(f"headroom {d['headroom_version']} present with proxy dependencies")
        if not d["rtk_bin"]:
            steps.append("RTK missing — " + rtk.install_hint(self.cfg))
        else:
            steps.append(f"RTK present ({d['rtk_bin']})")
        return steps

    def start(self):
        d = self.discover()
        exe = d["headroom_exe"]
        if not (exe or d["headroom_version"]):
            return {"ok": False, "error": "Headroom not installed; run `corpus compression install`."}
        if not d["headroom_proxy_ready"]:
            return {"ok": False, "error": "Headroom proxy dependencies missing; run `corpus compression install`."}
        port = self.cfg.get("compression.headroom.port") or 0
        if not port:
            port = plat.free_port()
        env_name = self.cfg.get("compression.headroom.base_url_env", "ANTHROPIC_BASE_URL")
        base = f"http://127.0.0.1:{port}"
        if headroom.port_open(port):
            st = {"pid": None, "port": port, "base_url": base, "env": env_name}
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps(st, indent=2), encoding="utf-8")
            return {"ok": True, **st, "reused": True}
        cmd = [exe, "proxy", "--port", str(port)] if exe else \
              [headroom.python_bin(self.cfg), "-m", "headroom", "proxy", "--port", str(port)]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            return {"ok": False, "error": f"failed to launch proxy: {e}"}
        st = {"pid": proc.pid, "port": port, "base_url": base, "env": env_name}
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(st, indent=2), encoding="utf-8")
        deadline = time.time() + 30
        while time.time() < deadline:
            if headroom.port_open(port):
                break
            if proc.poll() is not None:
                return {"ok": False, **st, "error": f"Headroom proxy exited with code {proc.returncode}"}
            time.sleep(0.5)
        else:
            return {"ok": False, **st, "error": f"Headroom proxy did not listen on port {port} within 30s"}
        return {"ok": True, **st, "hint": f"set {env_name}={base} for your agent (the adapter can export it)"}

    def stop(self):
        st = self._state()
        if not st:
            return {"ok": True, "note": "not running"}
        pid = st.get("pid")
        try:
            if plat.is_windows():
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            else:
                os.kill(int(pid), 15)
        except Exception:
            pass
        try:
            self.state_path.unlink()
        except Exception:
            pass
        return {"ok": True, "stopped_pid": pid}
