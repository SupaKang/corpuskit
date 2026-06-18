"""Config tests — defaults, deep-merge, dotted get, path resolution."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpuskit.core.config import Config, _deep_merge, find_config   # noqa: E402


def test_zero_config_defaults():
    from corpuskit.core.defaults import DEFAULTS
    cfg = Config(_deep_merge(DEFAULTS, {}), None)
    assert cfg.get("locale") == "en"
    assert cfg.get("knowledge.search.tokenizer") == "unicode61"
    assert cfg.get("knowledge.project_keys.key_from_dirname") is True


def test_deep_merge_overrides_lists_and_scalars():
    base = {"a": {"b": [1, 2], "c": 1}, "d": 9}
    over = {"a": {"b": [3], "e": 5}}
    out = _deep_merge(base, over)
    assert out["a"]["b"] == [3]      # list replaced, not extended
    assert out["a"]["c"] == 1        # untouched key kept
    assert out["a"]["e"] == 5        # new key added
    assert out["d"] == 9


def test_user_override(tmp_path):
    (tmp_path / "corpus.yaml").write_text(
        "locale: ko\nknowledge: { search: { tokenizer: trigram, top_k: 3 } }\n", encoding="utf-8")
    cfg = Config.load(tmp_path / "corpus.yaml")
    assert cfg.get("locale") == "ko"
    assert cfg.get("knowledge.search.tokenizer") == "trigram"
    assert cfg.get("knowledge.search.top_k") == 3
    # untouched default still present
    assert cfg.get("knowledge.search.body_cap") == 6000
    assert cfg.corpus_root == tmp_path.resolve()
