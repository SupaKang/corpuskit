"""Agent adapter protocol. Each adapter maps logical events to a target agent's
hook system and registers the MCP server + hooks idempotently."""


class BaseAdapter:
    name = "base"
    EVENT_MAP = {}  # logical -> native event name (str) or (event, matcher)

    def __init__(self, cfg):
        self.cfg = cfg

    def install(self, mcp=True, writeback=True, promptcontext=True):
        raise NotImplementedError

    def uninstall(self, mcp=True, writeback=True, promptcontext=True):
        raise NotImplementedError

    def status(self):
        raise NotImplementedError
