"""Baked-in default config. A user corpus.yaml is deep-merged over this.
Zero-config (no corpus.yaml) → auto_layout + project_key=dirname + English status map."""

DEFAULTS = {
    "version": 1,
    "locale": "en",
    "knowledge": {
        "corpus_root": ".",
        "keyed_roots": {},
        "flat_roots": {},
        "auto_layout": True,
        "file_glob": "**/*.md",
        "project_keys": {
            "canon": [], "alias": {}, "exclude": [], "absorb": [],
            "skip_subdirs": [], "key_from_dirname": True,
        },
        "frontmatter": {
            "style": "auto",                       # auto | bulleted | yaml | none
            "scan_lines": 40,
            "fields": {
                "project": ["project"],
                "date": ["date"],
                "status": ["status"],
                "title_from_h1": True,
            },
            "date_from_filename": r"(\d{8})",
            "wikilinks": True,
        },
        "status_map": {
            "CONFIRMED": ["confirmed"],
            "REVIEW": ["review"],
            "DONE": ["done"],
            "IN_PROGRESS": ["in_progress", "in progress"],
            "PLANNED": ["planned"],
            "DRAFT": ["draft"],
            "HELD": ["held"],
            "SUPERSEDED": ["superseded", "supersede"],
        },
        "search": {
            "tokenizer": "unicode61",
            "body_cap": 6000,
            "fts_columns": ["content", "project", "type", "status", "path"],
            "token_regex": r"[0-9A-Za-z가-힣]+",
            "top_k": 8,
            "index_db": ".corpuskit/index.db",
            "manifest": ".corpuskit/manifest.json",
        },
        "constraints": {
            "decisions_root": "decisions",
            "types": ["DONT_BREAK", "FIXED_ORDER", "BINDING", "ADOPT_ASIS",
                      "REQUIRES", "EXCLUDE", "INVARIANT"],
            "severity_order": ["block", "warn", "info"],
            "adr_template": "",
        },
        "mcp": {
            "server_name": "knowledge-runtime",
            "tools": {
                "search": {"name": "kr_search",
                           "description": "Search the indexed knowledge corpus (FTS5/BM25). Use instead of grep to find relevant specs/decisions/docs."},
                "constraints": {"name": "kr_constraints",
                                "description": "Query machine-readable @constraint rules for a component/file before risky edits."},
            },
        },
    },
    "agent": {
        "type": "claude-code",          # claude-code | cursor | cline | standalone
        "settings_path": "",
        "python": "",                   # "" → discover (venv → sys.executable)
        "hooks": {
            "writeback_on": "session_end",
            "promptcontext_on": "user_prompt_submit",
        },
    },
    "compression": {
        "enabled": False,
        "order": ["rtk", "headroom"],   # FIXED_ORDER; reversal rejected
        "rtk": {"bin": "", "install": "auto", "version": "~=0.42"},
        "headroom": {"python": "", "port": 0, "base_url_env": "ANTHROPIC_BASE_URL",
                     "install": "pip", "version": "~=0.26"},
        "native_windows": "degrade",    # degrade | error
    },
}
