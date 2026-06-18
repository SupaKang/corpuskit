"""Write-back: rebuild manifest + index. For SessionEnd-style hooks —
silent (stdout suppressed), exit 0, fail-soft. stdlib only."""
import contextlib
import io
import os

from ..core.config import Config
from . import index as index_mod
from . import manifest as manifest_mod


def run(config_path=None):
    cfg = Config.load(config_path or os.environ.get("CORPUSKIT_CONFIG"))
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            m = manifest_mod.build(cfg)
            manifest_mod.write(cfg, m)
            index_mod.build(cfg, m)
            return m["counts"]["total"]
        except Exception:
            return None
