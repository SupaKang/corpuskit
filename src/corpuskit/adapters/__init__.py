"""Adapter factory — selects the agent integration adapter from config."""
from .base import BaseAdapter


class StandaloneAdapter(BaseAdapter):
    """No agent host — register nothing; caller prints copy-paste instructions."""
    name = "standalone"

    def install(self, mcp=True, writeback=True, promptcontext=True):
        return []

    def uninstall(self, mcp=True, writeback=True, promptcontext=True):
        return []

    def status(self):
        return {"mcpServers": [], "hooks": {}}


def get_adapter(cfg):
    t = cfg.get("agent.type", "claude-code")
    if t == "claude-code":
        from .claude_code import ClaudeCodeAdapter
        return ClaudeCodeAdapter(cfg)
    if t == "standalone":
        return StandaloneAdapter(cfg)
    if t == "cursor":
        from .mcp_json import CursorAdapter
        return CursorAdapter(cfg)
    if t in ("cline", "mcp-json"):
        from .mcp_json import McpJsonAdapter
        return McpJsonAdapter(cfg)
    raise ValueError(f"unknown agent.type: {t}")
