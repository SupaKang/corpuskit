"""L1 manifest builder — walks the corpus (keyed_roots/flat_roots or auto_layout),
parses frontmatter, resolves project key, normalizes status. Fail-soft."""
import json
import re
from datetime import datetime, timezone

from . import frontmatter
from .keyresolve import KeyResolver, normalize_status


def build(cfg):
    K = cfg.data["knowledge"]
    root = cfg.corpus_root
    resolver = KeyResolver(K["project_keys"])
    fm_cfg = K["frontmatter"]
    status_map = K["status_map"]
    skip_subdirs = {str(s).lower() for s in K["project_keys"].get("skip_subdirs", []) or []}
    date_fn_re = re.compile(fm_cfg.get("date_from_filename") or r"(\d{8})")
    keyed = K.get("keyed_roots") or {}
    flat = K.get("flat_roots") or {}
    auto = K.get("auto_layout", True) and not keyed and not flat
    file_glob = K.get("file_glob", "**/*.md")

    entries = []
    cov = {"unknown_dirs": {}, "excluded_dirs": {}, "absorbed_dirs": {},
           "meta_dirs": {}, "warnings": []}

    def rel(p):
        try:
            return str(p.relative_to(root)).replace("\\", "/")
        except Exception:
            return str(p)

    def iter_md(base):
        for p in base.rglob("*.md"):
            if any(part.lower() in skip_subdirs for part in p.parts):
                continue
            yield p

    def make_entry(path, atype, raw_dir, forced_key=None, derive_from_fm=False):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            cov["warnings"].append(f"read-fail {path.name}: {e}")
            return
        f = frontmatter.parse(text, fm_cfg)
        date = f["date"]
        if not date:
            m = date_fn_re.search(path.name)
            if m:
                date = m.group(1)
        key = forced_key
        if derive_from_fm:
            key, _kind = resolver.resolve(f.get("fm_project") or "")
            if key is None:
                k = f"{raw_dir}/(loose)"
                cov["unknown_dirs"][k] = cov["unknown_dirs"].get(k, 0) + 1
        entries.append({
            "project_key": key, "raw_dir": raw_dir, "type": atype, "path": rel(path),
            "title": f["title"], "date": date, "status_raw": f["status_raw"],
            "status": normalize_status(f["status_raw"], status_map), "wikilinks": f["wikilinks"],
        })

    if auto:
        for p in sorted(root.glob(file_glob)):
            if not p.is_file() or p.suffix.lower() != ".md":
                continue
            if any(part.lower() in skip_subdirs for part in p.parts):
                continue
            try:
                parts = p.relative_to(root).parts
            except Exception:
                parts = (p.name,)
            dirname = parts[0] if len(parts) > 1 else ""
            pk = None
            if dirname:
                key, kind = resolver.resolve(dirname)
                if kind in ("exclude", "meta", "absorb"):
                    bucket = {"exclude": "excluded_dirs", "meta": "meta_dirs",
                              "absorb": "absorbed_dirs"}[kind]
                    cov[bucket][dirname] = cov[bucket].get(dirname, 0) + 1
                    continue
                pk = key
            make_entry(p, "doc", dirname or "(root)", forced_key=pk)
    else:
        for root_rel, atype in keyed.items():
            base = root / root_rel
            if not base.exists():
                continue
            for entry in sorted(base.iterdir()):
                if entry.is_dir():
                    key, kind = resolver.resolve(entry.name)
                    if kind in ("exclude", "absorb", "meta", "unknown"):
                        bucket = {"exclude": "excluded_dirs", "absorb": "absorbed_dirs",
                                  "meta": "meta_dirs", "unknown": "unknown_dirs"}[kind]
                        cov[bucket][f"{root_rel}/{entry.name}"] = sum(1 for _ in iter_md(entry))
                        continue
                    for md in iter_md(entry):
                        make_entry(md, atype, entry.name, forced_key=key)
                elif entry.is_file() and entry.suffix == ".md":
                    make_entry(entry, atype, root_rel, derive_from_fm=True)
        for root_rel, atype in flat.items():
            base = root / root_rel
            if not base.exists():
                continue
            for md in sorted(base.glob("*.md")):
                make_entry(md, atype, "(flat)", forced_key=None)

    by_project, by_type, by_status = {}, {}, {}
    for e in entries:
        pk = e["project_key"] or "(none)"
        by_project[pk] = by_project.get(pk, 0) + 1
        by_type[e["type"]] = by_type.get(e["type"], 0) + 1
        by_status[e["status"]] = by_status.get(e["status"], 0) + 1

    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "corpus_root": str(root),
        "counts": {
            "total": len(entries),
            "by_project": dict(sorted(by_project.items())),
            "by_type": dict(sorted(by_type.items())),
            "by_status": dict(sorted(by_status.items())),
        },
        "coverage": cov,
        "entries": entries,
    }


def write(cfg, manifest):
    out = cfg.manifest_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
