"""Generalized MCP server. Tool names/descriptions come from config; tool logic
delegates to the SAME index.query / constraints.collect the CLI uses.
stdout is reserved for the MCP protocol — tool functions only RETURN strings."""
import os
import sys

from ..core.config import Config
from . import index as index_mod
from . import constraints as constraints_mod


def _search_text(cfg, query, top_k=8):
    res = index_mod.query(cfg, query, top_k)
    if not res:
        return f"{query!r}: no matching documents."
    lines = [f"# {query!r} — {len(res)} hits"]
    for i, r in enumerate(res, 1):
        lines.append(f"{i}. [{r['project'] or '-'}/{r['type']}] {r['title'][:120]}")
        lines.append(f"    {r['path']}  (status={r['status'] or '-'}, score={r['score']:.1f})")
    return "\n".join(lines)


def build_server(cfg):
    from mcp.server.fastmcp import FastMCP

    mcp_cfg = cfg.get("knowledge.mcp", {}) or {}
    tools = mcp_cfg.get("tools", {}) or {}
    s = tools.get("search", {})
    c = tools.get("constraints", {})
    server = FastMCP(mcp_cfg.get("server_name", "knowledge-runtime"))

    def search(query: str, top_k: int = 8) -> str:
        return _search_text(cfg, query, top_k)

    def constraints(component: str = "") -> str:
        return constraints_mod.render(constraints_mod.collect(cfg, component), component)

    server.tool(name=s.get("name", "kr_search"),
                description=s.get("description", "Search the indexed corpus."))(search)
    server.tool(name=c.get("name", "kr_constraints"),
                description=c.get("description", "Query @constraint rules for a component."))(constraints)
    return server


def run(config_path=None):
    cfg = Config.load(config_path or os.environ.get("CORPUSKIT_CONFIG"))
    build_server(cfg).run()


def selftest(config_path=None):
    cfg = Config.load(config_path or os.environ.get("CORPUSKIT_CONFIG"))
    print("== search ==", file=sys.stderr)
    print(_search_text(cfg, "test", 3), file=sys.stderr)
    print("\n== constraints ==", file=sys.stderr)
    print(constraints_mod.render(constraints_mod.collect(cfg, ""), ""), file=sys.stderr)
