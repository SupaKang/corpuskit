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


def test_claude_install_reads_bom_settings_and_preserves_env(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(
        '\ufeff{"env":{"ANTHROPIC_BASE_URL":"http://127.0.0.1:8787"}}',
        encoding="utf-8",
    )
    a = get_adapter(_cfg(tmp_path, "claude-code"))

    assert "mcpServers.knowledge-runtime" in a.install()

    data = json.loads(settings.read_text(encoding="utf-8"))
    assert data["env"]["ANTHROPIC_BASE_URL"] == "http://127.0.0.1:8787"
    assert data["mcpServers"]["knowledge-runtime"]


def test_claude_install_dedupes_windows_path_separator_variants(tmp_path):
    settings = tmp_path / "settings.json"
    cfg = _cfg(tmp_path, "claude-code")
    a = get_adapter(cfg)
    command = a._hook_cmd("writeback").replace("\\", "/")
    settings.write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionEnd": [
                        {
                            "matcher": "",
                            "hooks": [{"type": "command", "command": command}],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    a.install()

    data = json.loads(settings.read_text(encoding="utf-8"))
    assert len(data["hooks"]["SessionEnd"]) == 1


def test_claude_install_dedupes_quoted_config_path_variants(tmp_path):
    settings = tmp_path / "settings.json"
    cfg = _cfg(tmp_path, "claude-code")
    a = get_adapter(cfg)
    command = a._hook_cmd("writeback").replace(
        f"--config {tmp_path / 'corpus.yaml'}",
        f'--config "{tmp_path / "corpus.yaml"}"',
    )
    settings.write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionEnd": [
                        {
                            "matcher": "",
                            "hooks": [{"type": "command", "command": command}],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    a.install()

    data = json.loads(settings.read_text(encoding="utf-8"))
    assert len(data["hooks"]["SessionEnd"]) == 1


def test_claude_hook_command_uses_forward_slash_config_path(tmp_path):
    a = get_adapter(_cfg(tmp_path, "claude-code"))

    command = a._hook_cmd("writeback")

    assert f"--config {tmp_path.as_posix()}/corpus.yaml" in command
    assert f"--config {tmp_path}\\corpus.yaml" not in command


def test_claude_install_rewrites_existing_hook_to_canonical_command(tmp_path):
    settings = tmp_path / "settings.json"
    cfg = _cfg(tmp_path, "claude-code")
    a = get_adapter(cfg)
    canonical = a._hook_cmd("writeback")
    old_command = canonical.replace(
        f"{tmp_path.as_posix()}/corpus.yaml",
        str(tmp_path / "corpus.yaml"),
    )
    settings.write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionEnd": [
                        {
                            "matcher": "",
                            "hooks": [{"type": "command", "command": old_command}],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    a.install()

    data = json.loads(settings.read_text(encoding="utf-8"))
    hooks = data["hooks"]["SessionEnd"][0]["hooks"]
    assert len(hooks) == 1
    assert hooks[0]["command"] == canonical


def test_cursor_mcp_only(tmp_path):
    a = get_adapter(_cfg(tmp_path, "cursor", "mcp.json"))
    done = a.install()
    assert any("mcpServers" in d for d in done)
    assert any("MCP-only" in d for d in done)      # hooks skipped
    assert a.status()["mcpServers"] == ["knowledge-runtime"]
    assert a.uninstall() == ["knowledge-runtime"]
