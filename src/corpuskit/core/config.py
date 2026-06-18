"""Config loading: deep-merge user corpus.yaml over baked-in DEFAULTS.
Path resolution is relative to the config file's dir (or cwd for zero-config)."""
import copy
from pathlib import Path

from .defaults import DEFAULTS

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def _deep_merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def find_config(start=None):
    """Walk up from start (or cwd) looking for corpus.yaml."""
    cur = Path(start or Path.cwd()).resolve()
    for d in [cur, *cur.parents]:
        c = d / "corpus.yaml"
        if c.exists():
            return c
    return None


class Config:
    def __init__(self, data, config_path=None):
        self.data = data
        self.config_path = Path(config_path).resolve() if config_path else None
        base = self.config_path.parent if self.config_path else Path.cwd()
        root = self.get("knowledge.corpus_root", ".")
        rp = Path(root)
        self.corpus_root = rp if rp.is_absolute() else (base / rp).resolve()

    @classmethod
    def load(cls, path=None):
        if path is None:
            path = find_config()
        over = {}
        if path:
            path = Path(path)
            if yaml is None:
                raise RuntimeError("PyYAML required to read config — pip install pyyaml")
            over = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        merged = _deep_merge(DEFAULTS, over)
        return cls(merged, config_path=path)

    def get(self, dotted, default=None):
        cur = self.data
        for part in dotted.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return default
        return cur

    def resolve(self, relpath):
        """Resolve a config-relative path against corpus_root."""
        p = Path(relpath)
        return p if p.is_absolute() else (self.corpus_root / p)

    @property
    def index_db(self):
        return self.resolve(self.get("knowledge.search.index_db"))

    @property
    def manifest_path(self):
        return self.resolve(self.get("knowledge.search.manifest"))
