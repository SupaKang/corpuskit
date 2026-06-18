"""corpus CLI entry point."""
import argparse
import json
import sys
from pathlib import Path

from ..core.config import Config
from ..knowledge import manifest as manifest_mod
from ..knowledge import index as index_mod
from ..knowledge import constraints as constraints_mod

_SAMPLE_YAML = """version: 1
locale: en
knowledge:
  corpus_root: "."
  auto_layout: true        # walk **/*.md, project_key = top-level dirname
  # keyed_roots: { specs: spec, decisions: decision }
  # flat_roots: { daily: daily }
  search: { tokenizer: unicode61 }
  constraints: { decisions_root: decisions }
agent:
  type: claude-code
compression:
  enabled: false
"""


def _reconfig():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ── knowledge ────────────────────────────────────────────────────────────────
def cmd_init(args):
    target = Path(args.path or ".") / "corpus.yaml"
    if target.exists() and not args.force:
        print(f"exists: {target} (use --force)")
        return
    target.write_text(_SAMPLE_YAML, encoding="utf-8")
    print(f"wrote {target}")


def cmd_index(args):
    cfg = Config.load(args.config)
    if args.index_cmd == "build":
        m = manifest_mod.build(cfg)
        if not args.report:
            manifest_mod.write(cfg, m)
            n, db = index_mod.build(cfg, m)
            print(f"manifest: {m['counts']['total']} docs -> {cfg.manifest_path}")
            print(f"index:    {n} docs -> {db}")
        c = m["counts"]
        print(json.dumps({"total": c["total"], "by_type": c["by_type"],
                          "by_status": c["by_status"]}, ensure_ascii=False, indent=2))
        cov = m["coverage"]
        print("UNKNOWN dirs:", cov["unknown_dirs"] or "none")
        if cov["warnings"]:
            print(f"warnings: {len(cov['warnings'])}")
    elif args.index_cmd == "query":
        res = index_mod.query(cfg, args.query, args.top_k)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return
        print(f"query: {args.query!r} -- {len(res)} hits")
        for i, r in enumerate(res, 1):
            print(f"  {i}. ({r['score']:.1f}) [{r['project'] or '-'}/{r['type']}] {r['title'][:120]}")


def cmd_constraints(args):
    cfg = Config.load(args.config)
    found = constraints_mod.collect(cfg, args.component or "")
    if args.json:
        print(json.dumps(found, ensure_ascii=False, indent=2))
        return
    print(constraints_mod.render(found, args.component or ""))


# ── runtime (mcp + hooks) ────────────────────────────────────────────────────
def cmd_serve_mcp(args):
    from ..knowledge import mcp_server
    if args.selftest:
        mcp_server.selftest(args.config)
    else:
        mcp_server.run(args.config)


def cmd_writeback(args):
    from ..knowledge import writeback
    writeback.run(args.config)


def cmd_promptcontext(args):
    from ..knowledge import promptcontext
    promptcontext.run(args.config)


# ── agent install ────────────────────────────────────────────────────────────
def _adapter(args):
    from ..adapters import get_adapter
    cfg = Config.load(args.config)
    return get_adapter(cfg)


def _flags(args):
    any_flag = args.mcp or args.writeback or args.promptcontext
    if not any_flag:
        return dict(mcp=True, writeback=True, promptcontext=True)
    return dict(mcp=args.mcp, writeback=args.writeback, promptcontext=args.promptcontext)


def cmd_install(args):
    a = _adapter(args)
    done = a.install(**_flags(args))
    print(f"[{a.name}] installed:", done or "(nothing new)")
    print("status:", json.dumps(a.status(), ensure_ascii=False))


def cmd_uninstall(args):
    a = _adapter(args)
    removed = a.uninstall(**_flags(args))
    print(f"[{a.name}] removed:", removed or "(nothing)")


def cmd_status(args):
    a = _adapter(args)
    print(json.dumps(a.status(), ensure_ascii=False, indent=2))


# ── compression + doctor ─────────────────────────────────────────────────────
def cmd_compression(args):
    from ..compression.orchestrator import Orchestrator
    cfg = Config.load(args.config)
    orch = Orchestrator(cfg)
    fn = {"install": orch.install, "start": orch.start, "stop": orch.stop,
          "status": orch.status, "health": orch.health}[args.comp_cmd]
    print(json.dumps(fn(), ensure_ascii=False, indent=2, default=str))


def cmd_doctor(args):
    import platform as _pf
    from ..core import platform as plat
    cfg = Config.load(args.config)
    info = {
        "config": str(cfg.config_path) if cfg.config_path else "(zero-config defaults)",
        "corpus_root": str(cfg.corpus_root),
        "python": sys.executable,
        "os": _pf.platform(), "windows": plat.is_windows(), "wsl": plat.is_wsl(),
        "manifest_exists": cfg.manifest_path.exists(),
        "index_exists": cfg.index_db.exists(),
        "agent": cfg.get("agent.type"),
        "compression_enabled": cfg.get("compression.enabled"),
    }
    if cfg.get("compression.enabled"):
        try:
            from ..compression.orchestrator import Orchestrator
            info["compression"] = Orchestrator(cfg).health()
        except Exception as e:
            info["compression_error"] = str(e)
    print(json.dumps(info, ensure_ascii=False, indent=2, default=str))


def build_parser():
    p = argparse.ArgumentParser(prog="corpus",
                                description="corpuskit -- config-driven knowledge corpus runtime")
    p.add_argument("--config", default=None, help="path to corpus.yaml (else auto-discover)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init", help="scaffold a corpus.yaml")
    pi.add_argument("--path", default=".")
    pi.add_argument("--force", action="store_true")
    pi.set_defaults(func=cmd_init)

    px = sub.add_parser("index", help="build/query the corpus index")
    xs = px.add_subparsers(dest="index_cmd", required=True)
    pb = xs.add_parser("build")
    pb.add_argument("--report", action="store_true", help="dry-run: counts only, no files written")
    pq = xs.add_parser("query")
    pq.add_argument("query")
    pq.add_argument("--top-k", dest="top_k", type=int, default=None)
    pq.add_argument("--json", action="store_true")
    px.set_defaults(func=cmd_index)

    pc = sub.add_parser("constraints", help="query @constraint rules")
    pc.add_argument("--component", default="")
    pc.add_argument("--json", action="store_true")
    pc.set_defaults(func=cmd_constraints)

    pm = sub.add_parser("serve-mcp", help="run the MCP stdio server")
    pm.add_argument("--selftest", action="store_true")
    pm.set_defaults(func=cmd_serve_mcp)

    pw = sub.add_parser("writeback", help="(hook) rebuild manifest+index, silent")
    pw.set_defaults(func=cmd_writeback)
    pp = sub.add_parser("promptcontext", help="(hook) emit active constraints as context")
    pp.set_defaults(func=cmd_promptcontext)

    for name, fn, help_ in (("install", cmd_install, "register MCP+hooks for --agent"),
                            ("uninstall", cmd_uninstall, "remove registrations"),
                            ("status", cmd_status, "show registrations")):
        sp = sub.add_parser(name, help=help_)
        sp.add_argument("--agent", default=None, help="override agent.type")
        sp.add_argument("--mcp", action="store_true")
        sp.add_argument("--writeback", action="store_true")
        sp.add_argument("--promptcontext", action="store_true")
        sp.set_defaults(func=fn)

    pcomp = sub.add_parser("compression", help="orchestrate RTK+Headroom compression")
    pcomp.add_argument("comp_cmd", choices=["install", "start", "stop", "status", "health"])
    pcomp.set_defaults(func=cmd_compression)

    pdoc = sub.add_parser("doctor", help="environment + runtime diagnostics")
    pdoc.set_defaults(func=cmd_doctor)
    return p


def main(argv=None):
    _reconfig()
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
