"""Prompt-context injector: emit active @constraint rules as additionalContext JSON
for a UserPromptSubmit-style hook. stdlib only; fail-soft."""
import json
import os

from ..core.config import Config
from . import constraints as constraints_mod

_HEADERS = {
    "en": "[knowledge runtime] active constraints — DO NOT VIOLATE (use kr_constraints/kr_search to verify):",
    "ko": "[기관 기억] 활성 제약 — 위반 금지(의심 시 kr_constraints/kr_search 조회):",
}


def context_text(cfg):
    cons = constraints_mod.collect(cfg, "")
    if not cons:
        return ""
    header = _HEADERS.get(cfg.get("locale", "en"), _HEADERS["en"])
    lines = [header]
    for c in cons:
        lines.append(f"- [{c['severity'].upper()}] {c['type']} · {c['target']}: {c['rule']}")
    return "\n".join(lines)


def run(config_path=None, event="UserPromptSubmit"):
    cfg = Config.load(config_path or os.environ.get("CORPUSKIT_CONFIG"))
    try:
        ctx = context_text(cfg)
    except Exception:
        return
    if not ctx:
        return
    print(json.dumps(
        {"hookSpecificOutput": {"hookEventName": event, "additionalContext": ctx}},
        ensure_ascii=False))
