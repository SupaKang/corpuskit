# corpuskit

Config-driven **knowledge corpus runtime** + **compression orchestration** for AI coding agents — multi-agent via MCP, zero-config on any docs folder.

It turns a folder of markdown into a searchable, constraint-aware institutional memory your agent can query (instead of re-deriving from scratch), and orchestrates external token-compression tools. Generalized from a working Claude-Code system; **a project is just one `corpus.yaml`**.

## What you get
- **Manifest + FTS5 search** over full document bodies (SQLite, stdlib — no embeddings/torch needed). Query with BM25.
- **Machine-readable constraints** — `@constraint TYPE | target= | rule= | adr= | severity=` lines in your decision/ADR docs, queryable by component.
- **MCP server** exposing `kr_search` / `kr_constraints` (names/descriptions configurable) — works with any MCP-capable agent (Claude Code, Cursor, …).
- **Agent install** — idempotent registration of the MCP server + write-back (SessionEnd) + constraint-injection (UserPromptSubmit) hooks.
- **Compression orchestration** — discover/install/lifecycle/health over external [RTK](https://github.com/rtk-ai/rtk) (shell-output) + [Headroom](https://github.com/chopratejas/headroom) (transport proxy), used AS-IS (never vendored).

## Install
```bash
pip install corpuskit            # core (CLI + manifest/index/constraints)
pip install "corpuskit[mcp]"     # + MCP server
pip install "corpuskit[all]"
# until published: pip install git+https://github.com/SupaKang/corpuskit
```

## Quickstart (zero-config)
```bash
cd my-docs/                 # any folder of *.md
corpus index build         # project_key = top-level dirname; full-body FTS5 index
corpus index query "rate limiter design"
corpus constraints --component payments-api
```
No `corpus.yaml` needed — defaults to `auto_layout` + dirname keys + standard YAML/bulleted frontmatter.

## Config (`corpus.yaml`) — opt in when you need it
```yaml
knowledge:
  keyed_roots: { specs: spec, decisions: decision }   # relpath -> doc_type (key = subdir)
  flat_roots:  { daily: daily }
  frontmatter: { style: auto, fields: { project: [project], status: [status] } }
  constraints: { decisions_root: decisions }
agent: { type: claude-code }       # claude-code | standalone | (cursor/cline stubs)
compression: { enabled: false }
```
`corpus init` scaffolds one. See `examples/overmind.yaml` for a full localized (Korean) instance.

## Agent integration
```bash
corpus install --agent claude-code     # idempotent: MCP + SessionEnd + UserPromptSubmit (backs up settings.json)
corpus status --agent claude-code
corpus uninstall --agent claude-code
```
Restart your agent; it gains `kr_search` / `kr_constraints` tools, auto-injected active constraints, and self-updating index on session end.

## Compression
```bash
corpus compression install   # ensure RTK + Headroom present
corpus compression start     # launch Headroom proxy, print ANTHROPIC_BASE_URL
corpus compression health    # versions, native-Windows degradation, port
```

## CLI
`corpus init | index build|query | constraints | serve-mcp | install|uninstall|status | compression … | doctor`

## License
Apache-2.0 (this code). External tools RTK and Headroom are separate Apache-2.0 projects, used as-is — see `THIRD_PARTY.md`.
