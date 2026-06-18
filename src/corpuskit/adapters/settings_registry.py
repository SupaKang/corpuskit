"""Idempotent settings.json editor — backup + check-before-update, parameterized
target file/key. Extracted from OVERMIND's register_*.py; shared by agent adapters."""
import json
import shutil
from pathlib import Path


def _load(path):
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def backup(path):
    p = Path(path)
    if p.exists():
        shutil.copy(str(p), str(p) + ".bak")


def ensure_mcp_server(path, name, command, args, env=None):
    d = _load(path)
    ms = d.setdefault("mcpServers", {})
    if name in ms:
        return False
    entry = {"command": command, "args": list(args)}
    if env:
        entry["env"] = dict(env)
    ms[name] = entry
    _save(path, d)
    return True


def ensure_hook(path, event, command, matcher=""):
    d = _load(path)
    arr = d.setdefault("hooks", {}).setdefault(event, [])
    exists = any(
        h.get("command") == command
        for blk in arr if isinstance(blk, dict)
        for h in blk.get("hooks", [])
    )
    if exists:
        return False
    arr.append({"matcher": matcher, "hooks": [{"type": "command", "command": command}]})
    _save(path, d)
    return True


def remove_mcp_server(path, name):
    d = _load(path)
    if d.get("mcpServers", {}).pop(name, None) is not None:
        _save(path, d)
        return True
    return False


def remove_hook(path, event, command):
    d = _load(path)
    arr = d.get("hooks", {}).get(event, [])
    changed = False
    new_arr = []
    for blk in arr:
        if isinstance(blk, dict):
            hooks = blk.get("hooks", [])
            kept = [h for h in hooks if h.get("command") != command]
            if len(kept) != len(hooks):
                changed = True
            blk["hooks"] = kept
            if kept:
                new_arr.append(blk)      # drop now-empty blocks
        else:
            new_arr.append(blk)
    if changed:
        if new_arr:
            d["hooks"][event] = new_arr
        else:
            d["hooks"].pop(event, None)  # drop now-empty event
        _save(path, d)
    return changed


def status(path):
    d = _load(path)
    return {"mcpServers": list(d.get("mcpServers", {}).keys()),
            "hooks": {k: len(v) for k, v in d.get("hooks", {}).items()}}
