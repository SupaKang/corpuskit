# Publishing corpuskit to PyPI (Trusted Publishing)

corpuskit publishes via **PyPI Trusted Publishing (OIDC)** — GitHub Actions authenticates
to PyPI with a short-lived token; **no API token is ever stored** in the repo or secrets.

## One-time setup (you do this once on pypi.org)
1. Create the project (or reserve the name) — if `corpuskit` is taken, change `name` in
   `pyproject.toml` (e.g. `corpus-kit`) and keep the `corpus` console script.
2. PyPI → your project → **Settings → Publishing → Add a trusted publisher** (GitHub):
   - **Owner:** `SupaKang`
   - **Repository:** `corpuskit`
   - **Workflow name:** `release.yml`
   - **Environment:** `pypi`
3. (GitHub) the `pypi` environment is created automatically by the workflow; optionally add
   reviewers/protection in repo Settings → Environments.

## Cut a release
1. Bump `version` in `pyproject.toml` (e.g. `0.1.0` → `0.1.1`); commit.
2. On GitHub: **Releases → Draft a new release → tag `v0.1.1` → Publish**.
3. The `release.yml` workflow builds the sdist+wheel and publishes to PyPI automatically.

## Before first publish (recommended)
- Test on **TestPyPI** first: add a second trusted publisher there and a `workflow_dispatch`
  run pointed at `repository-url: https://test.pypi.org/legacy/`.
- Verify `python -m build` produces a clean wheel locally: `pip install build && python -m build`.

## Install (until first release)
```bash
pip install "git+https://github.com/SupaKang/corpuskit"
```
