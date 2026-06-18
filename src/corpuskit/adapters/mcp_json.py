"""Generic MCP-only adapter for agents that read an `mcp.json`-shaped config
(e.g. Cursor's ~/.cursor/mcp.json). These agents support MCP servers but not
Claude-Code-style SessionEnd/UserPromptSubmit hooks, so write-back / prompt-context
are skipped — the agent gets kr_search / kr_constraints via MCP."""
from pathlib import Path

from . import settings_registry as sr
from .base import BaseAdapter
from ..core import platform as plat


class McpJsonAdapter(BaseAdapter):
    name = "mcp-json"

    def __init__(self, cfg):
        super().__init__(cfg)
        sp = cfg.get("agent.settings_path") or ""
        self.settings = Path(sp) if sp else self._default_path()
        self.py = plat.discover_python(cfg.get("agent.python") or "")
        self.config_arg = str(cfg.config_path) if cfg.config_path else None
        self.server_name = cfg.get("knowledge.mcp.server_name", "knowledge-runtime")

    def _default_path(self):
        raise ValueError(
            f"agent.type={self.name} requires agent.settings_path (path to the agent's mcp.json)")

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
        if writeback or promptcontext:
            done.append(f"note: {self.name} has no write-back/prompt-context hooks (MCP-only); skipped")
        return done

    def uninstall(self, mcp=True, writeback=True, promptcontext=True):
        sr.backup(self.settings)
        if mcp and sr.remove_mcp_server(self.settings, self.server_name):
            return [self.server_name]
        return []

    def status(self):
        return sr.status(self.settings)


class CursorAdapter(McpJsonAdapter):
    name = "cursor"

    def _default_path(self):
        return Path.home() / ".cursor" / "mcp.json"
