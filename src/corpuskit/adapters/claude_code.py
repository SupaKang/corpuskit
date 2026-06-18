"""Claude Code adapter — registers the MCP server + SessionEnd/UserPromptSubmit
hooks into ~/.claude/settings.json via the idempotent settings_registry."""
from pathlib import Path

from . import settings_registry as sr
from .base import BaseAdapter
from ..core import platform as plat


def _q(s):
    s = str(s)
    return f'"{s}"' if (" " in s) else s


class ClaudeCodeAdapter(BaseAdapter):
    name = "claude-code"
    EVENT_MAP = {
        "session_end": "SessionEnd",
        "user_prompt_submit": "UserPromptSubmit",
        "pre_tool_use_bash": ("PreToolUse", "Bash"),
    }

    def __init__(self, cfg):
        super().__init__(cfg)
        sp = cfg.get("agent.settings_path") or ""
        self.settings = Path(sp) if sp else plat.claude_settings_path()
        self.py = plat.discover_python(cfg.get("agent.python") or "")
        self.config_arg = str(cfg.config_path) if cfg.config_path else None
        self.server_name = cfg.get("knowledge.mcp.server_name", "knowledge-runtime")

    def _hook_cmd(self, subcmd):
        parts = [self.py, "-m", "corpuskit.cli"]
        if self.config_arg:
            parts += ["--config", self.config_arg]
        parts.append(subcmd)
        return " ".join(_q(p) for p in parts)

    def _mcp_args(self):
        args = ["-m", "corpuskit.cli"]
        if self.config_arg:
            args += ["--config", self.config_arg]
        args.append("serve-mcp")
        return args

    def install(self, mcp=True, writeback=True, promptcontext=True):
        sr.backup(self.settings)
        done = []
        if mcp and sr.ensure_mcp_server(self.settings, self.server_name, self.py, self._mcp_args()):
            done.append(f"mcpServers.{self.server_name}")
        if writeback:
            ev = self.EVENT_MAP[self.cfg.get("agent.hooks.writeback_on", "session_end")]
            if sr.ensure_hook(self.settings, ev, self._hook_cmd("writeback")):
                done.append(ev)
        if promptcontext:
            ev = self.EVENT_MAP[self.cfg.get("agent.hooks.promptcontext_on", "user_prompt_submit")]
            if sr.ensure_hook(self.settings, ev, self._hook_cmd("promptcontext")):
                done.append(ev)
        return done

    def uninstall(self, mcp=True, writeback=True, promptcontext=True):
        sr.backup(self.settings)
        removed = []
        if mcp and sr.remove_mcp_server(self.settings, self.server_name):
            removed.append(self.server_name)
        if writeback:
            ev = self.EVENT_MAP[self.cfg.get("agent.hooks.writeback_on", "session_end")]
            if sr.remove_hook(self.settings, ev, self._hook_cmd("writeback")):
                removed.append(ev)
        if promptcontext:
            ev = self.EVENT_MAP[self.cfg.get("agent.hooks.promptcontext_on", "user_prompt_submit")]
            if sr.remove_hook(self.settings, ev, self._hook_cmd("promptcontext")):
                removed.append(ev)
        return removed

    def status(self):
        return sr.status(self.settings)
