"""Compression orchestration tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpuskit.compression.orchestrator import Orchestrator  # noqa: E402
from corpuskit.core.config import Config  # noqa: E402


def test_start_reuses_existing_headroom_port(tmp_path, monkeypatch):
    (tmp_path / "corpus.yaml").write_text(
        "knowledge: { corpus_root: '.' }\n"
        "compression: { enabled: true, headroom: { port: 8787 } }\n",
        encoding="utf-8",
    )
    cfg = Config.load(tmp_path / "corpus.yaml")
    orch = Orchestrator(cfg)

    monkeypatch.setattr(
        orch,
        "discover",
        lambda: {
            "rtk_bin": "rtk",
            "headroom_python": sys.executable,
            "headroom_version": "0.26.0",
            "headroom_proxy_ready": True,
            "headroom_exe": "headroom",
        },
    )
    monkeypatch.setattr(
        "corpuskit.compression.orchestrator.headroom.port_open",
        lambda port: port == 8787,
    )

    def fail_popen(*args, **kwargs):
        raise AssertionError("start should reuse an already-open proxy port")

    monkeypatch.setattr("corpuskit.compression.orchestrator.subprocess.Popen", fail_popen)

    result = orch.start()

    assert result["ok"] is True
    assert result["reused"] is True
    assert result["base_url"] == "http://127.0.0.1:8787"
