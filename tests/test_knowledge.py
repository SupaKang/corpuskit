"""Core knowledge-runtime tests: manifest build, key resolution, frontmatter
styles, status normalization, FTS search, constraint parsing."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpuskit.core.config import Config            # noqa: E402
from corpuskit.knowledge import manifest, index, constraints, frontmatter  # noqa: E402


def _make_corpus(tmp):
    (tmp / "alpha").mkdir()
    (tmp / "beta").mkdir()
    (tmp / "decisions").mkdir()
    (tmp / "alpha" / "intro.md").write_text(
        "# Alpha intro\n\n- status: confirmed\n\nWidget search engine over documents.\n",
        encoding="utf-8")
    (tmp / "beta" / "design.md").write_text(
        "---\nproject: B\nstatus: draft\n---\n\n# Beta design\n\nGadget design notes.\n",
        encoding="utf-8")
    (tmp / "decisions" / "adr1.md").write_text(
        "# ADR — beta backend\n\n@constraint DONT_BREAK | target=beta-api | "
        "rule=keep v1 contract | adr=[[adr1]] | severity=warn\n", encoding="utf-8")
    (tmp / "corpus.yaml").write_text(
        "knowledge:\n  corpus_root: \".\"\n  auto_layout: true\n"
        "  search: { index_db: .corpuskit/index.db, manifest: .corpuskit/manifest.json }\n"
        "  constraints: { decisions_root: decisions }\n", encoding="utf-8")
    return Config.load(tmp / "corpus.yaml")


def test_manifest_and_keys(tmp_path):
    cfg = _make_corpus(tmp_path)
    m = manifest.build(cfg)
    assert m["counts"]["total"] == 3
    keys = {e["raw_dir"]: e["project_key"] for e in m["entries"]}
    assert keys["alpha"] == "alpha" and keys["beta"] == "beta"   # dirname keys
    assert m["coverage"]["unknown_dirs"] == {}


def test_frontmatter_styles(tmp_path):
    cfg = _make_corpus(tmp_path)
    m = manifest.build(cfg)
    by_dir = {e["raw_dir"]: e for e in m["entries"]}
    assert by_dir["alpha"]["status"] == "CONFIRMED"   # bulleted
    assert by_dir["beta"]["status"] == "DRAFT"        # yaml block


def test_search(tmp_path):
    cfg = _make_corpus(tmp_path)
    m = manifest.build(cfg)
    manifest.write(cfg, m)
    n, _ = index.build(cfg, m)
    assert n == 3
    hits = index.query(cfg, "gadget design")
    assert hits and hits[0]["project"] == "beta"


def test_constraints(tmp_path):
    cfg = _make_corpus(tmp_path)
    found = constraints.collect(cfg, "")
    assert len(found) == 1 and found[0]["type"] == "DONT_BREAK"
    assert constraints.collect(cfg, "beta-api")
    assert constraints.collect(cfg, "nonexistent") == []


def test_zero_config(tmp_path, monkeypatch):
    # no corpus.yaml — defaults
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "x.md").write_text("# x\n\nhello world", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    cfg = Config.load(None)
    m = manifest.build(cfg)
    assert m["counts"]["total"] == 1
    assert m["entries"][0]["project_key"] == "p"
