# Third-party tools

corpuskit's compression orchestration **shells out to / pip-installs** external tools.
They are **not vendored** and **not forked** — corpuskit only discovers, installs (on
request), and manages their lifecycle. Each is independently licensed.

| Tool | License | Used how |
|---|---|---|
| [RTK (`rtk-ai/rtk`)](https://github.com/rtk-ai/rtk) | Apache-2.0 | external binary on PATH / `~/.cargo/bin`; invoked via subprocess and an agent PreToolUse(Bash) hook |
| [Headroom (`chopratejas/headroom`, `headroom-ai`)](https://github.com/chopratejas/headroom) | Apache-2.0 | pip-installed into a configured venv; run as a local transport proxy |

Notes:
- The `[memory]` extra installs `headroom-ai`, which may download HuggingFace / sentence-transformer **model weights** at runtime — those weights carry their **own licenses**, independent of corpuskit's Apache-2.0 code.
- Version compatibility is pinned major.minor and surfaced by `corpus compression health` / `doctor`.
- corpuskit's own code (everything under `src/corpuskit/`) is Apache-2.0; see `LICENSE`.
