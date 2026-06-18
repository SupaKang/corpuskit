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
    if t in ("cursor", "cline"):
        raise NotImplementedError(
            f"adapter '{t}' is a stub. Use agent.type: standalone for now, or contribute "
            f"a {t} adapter (map logical events session_end/user_prompt_submit to {t}'s hook API).")
    raise ValueError(f"unknown agent.type: {t}")
