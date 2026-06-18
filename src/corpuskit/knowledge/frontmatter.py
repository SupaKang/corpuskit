"""Frontmatter parsing — supports YAML block, bulleted (`- field: value`), or none,
with configurable field-name aliases (English + any locale). Always fail-soft."""
import re

_H1 = re.compile(r"^#\s+(.+?)\s*$")
_WIKI = re.compile(r"\[\[([^\]]+)\]\]")


def _reverse_fields(fields):
    rev = {}
    for logical in ("project", "date", "status"):
        for lab in fields.get(logical, []) or []:
            rev[str(lab)] = logical
    return rev


def parse(text, fm_cfg):
    fields = fm_cfg.get("fields", {})
    rev = _reverse_fields(fields)
    style = fm_cfg.get("style", "auto")
    scan = int(fm_cfg.get("scan_lines", 40))
    title_from_h1 = fields.get("title_from_h1", True)
    out = {"title": None, "date": None, "status_raw": None, "fm_project": None, "wikilinks": []}

    labels_alt = "|".join(re.escape(l) for l in sorted(rev, key=len, reverse=True)) if rev else None
    bulleted_re = re.compile(rf"^[-*]\s*({labels_alt})\s*[:：]\s*(.+?)\s*$") if labels_alt else None
    yaml_kv_re = re.compile(rf"^\s*({labels_alt})\s*:\s*(.+?)\s*$") if labels_alt else None

    def assign(logical, val):
        val = val.strip().strip('"').strip("'")
        if logical == "project":
            out["fm_project"] = val
        elif logical == "date":
            out["date"] = val.replace("-", "").strip()[:8]
        elif logical == "status":
            out["status_raw"] = val

    lines = text.splitlines()

    if style in ("auto", "yaml") and lines and lines[0].strip() == "---" and yaml_kv_re:
        for i in range(1, min(len(lines), scan + 1)):
            if lines[i].strip() == "---":
                break
            m = yaml_kv_re.match(lines[i])
            if m and m.group(1) in rev:
                assign(rev[m.group(1)], m.group(2))

    for ln in lines[:scan]:
        if out["title"] is None and title_from_h1:
            mh = _H1.match(ln)
            if mh:
                out["title"] = mh.group(1)
                continue
        if style in ("auto", "bulleted") and bulleted_re:
            mb = bulleted_re.match(ln)
            if mb and mb.group(1) in rev:
                assign(rev[mb.group(1)], mb.group(2))

    if fm_cfg.get("wikilinks", True):
        out["wikilinks"] = sorted(set(m.strip() for m in _WIKI.findall(text)))
    return out
