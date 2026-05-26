# AGENTS.md

This file provides project overview, context, and coding guidelines for AI coding agents
(Claude Code, Codex, Cursor, etc.) working in this repository.

## Project Overview

`mkdocs-panzoom-plugin` is an MkDocs plugin that adds pan/zoom UI controls around Mermaid
diagrams, D2 diagrams, and images at site-build time. Diagrams are wrapped in a `panzoom-box`
`<div>` and the runtime behavior is provided by the bundled
[anvaka/panzoom](https://github.com/anvaka/panzoom) JavaScript library
(`mkdocs_panzoom_plugin/panzoom/panzoom.min.js`).

The plugin entry point is registered in `pyproject.toml`:

```toml
[project.entry-points."mkdocs.plugins"]
panzoom = "mkdocs_panzoom_plugin.plugin:PanZoomPlugin"
```

## Architecture

Build-time flow (Python, MkDocs hooks):

1. `on_config` (plugin.py): validates config, ensures `panzoom` is registered after plugins
   that rewrite diagram HTML (e.g. `mermaid2`). If `panzoom` comes before `mermaid2` in
   `mkdocs.yml`, a `ConfigurationError` is raised.
2. `on_post_page` (plugin.py → html_page.py): for each rendered page that is not in the
   `exclude` list, parse with BeautifulSoup, find target elements, wrap each in a
   `panzoom-box` div with controls, and inject `<link>` + `<script>` tags pointing to
   the runtime assets.
3. `on_post_build` (plugin.py): copies the runtime assets (`panzoom.css`, `zoompan.js`,
   `panzoom.min.js`) into `<site_dir>/assets/{stylesheets,javascripts}/`.

Selector resolution (`html_page.py::HTMLPage._find_elements`):

- Defaults: `{".mermaid", ".d2"}`.
- `exclude_selectors` removes from defaults; `include_selectors` adds. `images: true` adds `img`.
- Legacy `mermaid: false` removes `.mermaid`.
- Final list is stored back into `self.config["selectors"]` and emitted to the runtime via a
  `<meta name="panzoom-data">` JSON tag (also carries `initial_zoom_level`, `zoom_step`,
  `buttons_size`).

Per-diagram opt-out and auto-detection (`yaml_parser.py`, called from
`html_page.py::_should_apply_panzoom`):

- For `<pre class="mermaid">` elements, the inner `<code>` text is parsed for a YAML
  frontmatter block (`---` ... `---`).
- If the frontmatter has `panzoom: { enabled: false }`, panzoom is skipped for that diagram.
- Otherwise, when `auto_enable: true` (default), `should_enable_panzoom()` enables panzoom
  only for diagrams that exceed any of the size thresholds (`auto_enable_threshold_lines`,
  `_nodes`, `_edges`, `_chars`). When `auto_enable: false`, all matched diagrams get panzoom
  (legacy behavior).
- Auto-detection currently runs only for Mermaid `<pre class="mermaid">`. D2 and `<img>`
  always get panzoom.

Runtime assets:

- `mkdocs_panzoom_plugin/custom/panzoom.css`: styling for the box, nav, hints, fullscreen modal.
- `mkdocs_panzoom_plugin/custom/zoompan.js`: reads the `<meta name="panzoom-data">` and
  `<meta name="panzoom-theme">` tags, wires up panzoom on each `.panzoom-box`, persists
  zoom/pan state per diagram in `localStorage` (auto-cleared after 30 days), implements
  reset/fullscreen/hint behavior.
- `mkdocs_panzoom_plugin/panzoom/panzoom.min.js`: third-party library, do not edit.

Box structure (`panzoom_box.py::create_panzoom_box`): the `nav` always contains a reset
button; info button is added unless `always_show_hint`; zoom-in/out buttons added when
`show_zoom_buttons`; fullscreen min/max buttons added when `full_screen`. The hint info box
is appended at the top or bottom of the panzoom-box depending on `hint_location`.

## Development Commands

`make` with no target prints a self-documenting help menu (no side effects). Run
`make setup` explicitly the first time you clone the repo. Each Make target is a
one-line wrapper that delegates to a small focused script under `scripts/`, so the
real logic lives there and is easy to read or run directly.

```bash
make                  # print the help menu (default target)
make setup            # → scripts/contributor-setup.sh (uv, .venv, deps, prek hooks, d2)
make test [ARGS=...]  # → scripts/test.sh (pytest + coverage; ARGS forwarded to pytest)
make check            # → scripts/check.sh (prek; CI: changed-files only, local: --all-files)
make prek             # → scripts/prek.sh (prek --all-files unconditionally)
make build            # → scripts/build.sh (mkdocs build --strict)
make serve            # → scripts/serve.sh (mkdocs serve --no-strict)
make env              # → scripts/env.sh (print Python / uv / venv diagnostics)
make clean            # → scripts/clean.sh (remove .venv, caches, site/)
```

Aliases: `tests` → `test`, `docs` → `build`, `all` / `hooks` → `check`.

Hooks run via [`prek`](https://github.com/j178/prek), a pre-commit-compatible runner
installed by `make setup` via `uv tool install prek`. The hook config is the standard
`.pre-commit-config.yaml`, so classic `pre-commit` also works if preferred.

CI behavior: `scripts/contributor-setup.sh` and `scripts/check.sh` detect CI via
`CDP_BUILD_VERSION` / `CI` and switch to `uv sync --frozen` and prek with
`--from-ref origin/HEAD --to-ref HEAD` respectively. The setup script also skips
the local-only d2 install in CI.

Run a single test:

```bash
uv run pytest tests/test_yaml_parser.py::test_should_enable_panzoom_with_explicit_yaml -v
```

Run tests without coverage (faster):

```bash
uv run pytest tests/test_html_page.py -v --no-cov
```

Coverage reports are written to `htmlcov/index.html` and `coverage.xml` after `make test`.

## Configuration Reference

Plugin options (defined in `plugin.py::PanZoomPlugin.config_scheme`, defaults in parens):

- Selectors: `include_selectors` (`[]`), `exclude_selectors` (`[]`), `mermaid` (`true`),
  `images` (`false`).
- UI: `always_show_hint` (`false`), `hint_location` (`"bottom"` or `"top"`),
  `show_zoom_buttons` (`false`), `buttons_size` (`"1.25em"`), `full_screen` (`false`).
- Zoom: `initial_zoom_level` (`1.0`), `zoom_step` (`0.2`), `key` (`"alt"`, also accepts
  `ctrl` / `shift` / `none`).
- Pages: `exclude` (`[]`), `include` (`["*"]`).
- Auto-detect: `auto_enable` (`true`), `auto_enable_threshold_lines` (`8`), `_nodes` (`6`),
  `_edges` (`5`), `_chars` (`200`).

Note: `site_url` must be set in `mkdocs.yml` for the plugin to function (otherwise relative
asset URLs break).

## Testing

Tests live in `tests/`, named `test_<module>.py` (one file per source module plus
regression tests for specific bugs like `test_hint_button_*`). The test suite mocks the
MkDocs `MkDocsConfig`, `Page`, and `File` objects rather than running a full build.

When adding behavior, prefer extending the matching `tests/test_<module>.py` over creating a
new file. The repo's pytest config (`pyproject.toml`) sets `--strict-markers`,
`--strict-config`, and runs coverage by default.

## Code Style

- Python 3.10+; line length 99 (per `pyproject.toml`, narrower than the global 130).
- `ruff` for linting + formatting; `mypy` is configured but with relaxed settings (most
  strict checks off; `tests/.*` is excluded).
- Pre-commit hook config is in `.pre-commit-config.yaml`.
- File naming: Python uses `underscores`; shell scripts and directories use `hyphens`.

## Plugin Ordering Constraint

In `mkdocs.yml`, list `panzoom` AFTER any plugin that emits the diagram HTML it should wrap.
The check is currently enforced for `mermaid2`, but the same rule applies to any plugin that
generates the targeted selectors (`.mermaid`, `.d2`, `img`). Putting `panzoom` first will
cause it to find no elements (or, for `mermaid2`, raise `ConfigurationError` in `on_config`).

## Repository Layout

| Path                                        | Purpose                                               |
| ------------------------------------------- | ----------------------------------------------------- |
| `mkdocs_panzoom_plugin/`                    | Plugin source                                         |
| `mkdocs_panzoom_plugin/custom/`             | Bundled CSS + project JS (`zoompan.js`)               |
| `mkdocs_panzoom_plugin/panzoom/`            | Third-party `panzoom.min.js` (do not edit)            |
| `tests/`                                    | Pytest tests, one file per source module              |
| `docs/`                                     | MkDocs documentation source (Mermaid/, D2/, etc.)     |
| `scripts/`                                  | Per-target shell scripts (setup, check, prek, test, build, serve, env, clean) |
| `mkdocs.yml`                                | Demo site config used by `make serve` / `make build`  |

The top-level `debug_*.py` and `test_*.py` files are ad-hoc scratch scripts, not part of the
test suite (pytest only collects from `tests/`).
