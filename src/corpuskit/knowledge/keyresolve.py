"""Project-key resolution (canon/alias/exclude/absorb + dirname default) and
status normalization — both config-driven, locale-agnostic."""


class KeyResolver:
    def __init__(self, pk_cfg):
        pk = pk_cfg or {}
        self.canon_lc = {str(k).lower(): str(k) for k in pk.get("canon", []) or []}
        self.alias = {str(k).lower(): v for k, v in (pk.get("alias") or {}).items()}
        self.absorb = {str(s).lower() for s in pk.get("absorb", []) or []}
        self.exclude = {str(s).lower() for s in pk.get("exclude", []) or []}
        self.key_from_dirname = pk.get("key_from_dirname", True)

    def resolve(self, name):
        """→ (canonical_key|None, kind) where kind ∈ canon/alias/dirname/exclude/absorb/meta/unknown."""
        if not name:
            return None, "unknown"
        low = name.strip().lower()
        if low.startswith("_"):
            return None, "meta"
        if low in self.exclude:
            return None, "exclude"
        if low in self.absorb:
            return None, "absorb"
        if low in self.alias:
            return self.alias[low], "alias"
        if low in self.canon_lc:
            return self.canon_lc[low], "canon"
        if self.key_from_dirname:
            return name, "dirname"
        return None, "unknown"


def normalize_status(raw, status_map):
    if not raw:
        return "UNKNOWN"
    low = str(raw).strip().lower()
    for canon, needles in (status_map or {}).items():
        for n in needles or []:
            if str(n).lower() in low:
                return canon
    return "OTHER"
