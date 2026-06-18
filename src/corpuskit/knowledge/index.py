"""L3 search — self-contained SQLite FTS5 index over full document bodies.
Config-driven tokenizer / columns / body cap. stdlib only (no torch/Headroom)."""
import json
import re
import sqlite3
from pathlib import Path

from . import manifest as manifest_mod


def _entry_text(e):
    parts = [f"[{e.get('type')}]", e.get("title") or Path(e["path"]).stem]
    if e.get("project_key"):
        parts.append(f"project={e['project_key']}")
    if e.get("status") and e["status"] != "UNKNOWN":
        parts.append(f"status={e['status']}")
    parts.append(e["path"])
    if e.get("wikilinks"):
        parts.append("links=" + ",".join(e["wikilinks"][:5]))
    return " | ".join(p for p in parts if p)


def _colval(cfg, col, e):
    if col == "content":
        cap = int(cfg.get("knowledge.search.body_cap", 6000))
        body = ""
        try:
            body = (cfg.corpus_root / e["path"]).read_text(encoding="utf-8", errors="replace")[:cap]
        except Exception:
            pass
        return _entry_text(e) + "\n" + body
    if col == "project":
        return e.get("project_key") or ""
    return e.get(col) or ""


def build(cfg, manifest=None):
    if manifest is None:
        mp = cfg.manifest_path
        manifest = (json.loads(mp.read_text(encoding="utf-8"))
                    if mp.exists() else manifest_mod.build(cfg))
    entries = manifest["entries"]
    tok = cfg.get("knowledge.search.tokenizer", "unicode61")
    cols = cfg.get("knowledge.search.fts_columns",
                   ["content", "project", "type", "status", "path"])
    db = cfg.index_db
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db))
    con.execute("DROP TABLE IF EXISTS docs")
    con.execute(f"CREATE VIRTUAL TABLE docs USING fts5({', '.join(cols)}, tokenize='{tok}')")
    rows = [tuple(_colval(cfg, c, e) for c in cols) for e in entries]
    con.executemany(
        f"INSERT INTO docs({','.join(cols)}) VALUES({','.join('?' * len(cols))})", rows)
    con.commit()
    con.close()
    return len(rows), db


def query(cfg, q, top_k=None):
    db = cfg.index_db
    if not db.exists():
        return []
    top_k = top_k or int(cfg.get("knowledge.search.top_k", 8))
    token_re = cfg.get("knowledge.search.token_regex", r"[0-9A-Za-z가-힣]+")
    toks = re.findall(token_re, q or "")
    if not toks:
        return []
    match = " OR ".join(f'"{t}"' for t in toks)
    con = sqlite3.connect(str(db))
    try:
        rows = con.execute(
            "SELECT path, project, type, status, content, bm25(docs) AS s "
            "FROM docs WHERE docs MATCH ? ORDER BY s LIMIT ?", (match, top_k)).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()
    out = []
    for path, project, typ, status, content, s in rows:
        title = (content or "").splitlines()[0] if content else ""
        out.append({"path": path, "project": project, "type": typ,
                    "status": status, "title": title, "score": s})
    return out
