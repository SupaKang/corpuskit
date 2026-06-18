"""Adapter tests — idempotent install/uninstall against scratch settings files."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpuskit.core.config import Config              # noqa: E402
from corpuskit.adapters import get_adapter            # noqa: E402


def _cfg(tmp, agent_type, settings_name="settings.json"):
    (tmp / "corpus.yaml").write_text(
        f"knowledge: {{ corpus_root: '.' }}\n"
        f"agent: {{ type: {agent_type}, settings_path: '{tmp.as_posix()}/{settings_name}' }}\n",
        encoding="utf-8")
    return Config.load(tmp / "corpus.yaml")


def test_claude_install_idempotent(tmp_path):
    a = get_adapter(_cfg(tmp_path, "claude-code"))
    first = a.install()
    assert "mcpServers.knowledge-runtime" in first
    assert sorted(x for x in first if x in ("SessionEnd", "UserPromptSubmit")) == ["SessionEnd", "UserPromptSubmit"]
    assert a.install() == []                       # idempotent
    st = a.status()
    assert st["mcpServers"] == ["knowledge-runtime"]
    removed = a.uninstall()
    assert "knowledge-runtime" in removed
    assert a.status()["mcpServers"] == []
    # empty hook events dropped on uninstall
    data = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert "SessionEnd" not in data.get("hooks", {})


def test_cursor_mcp_only(tmp_path):
    a = get_adapter(_cfg(tmp_path, "cursor", "mcp.json"))
    done = a.install()
    assert any("mcpServers" in d for d in done)
    assert any("MCP-only" in d for d in done)      # hooks skipped
    assert a.status()["mcpServers"] == ["knowledge-runtime"]
    assert a.uninstall() == ["knowledge-runtime"]
