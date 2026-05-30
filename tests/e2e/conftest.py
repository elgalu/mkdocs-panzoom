"""Fixtures for headless-browser end-to-end tests.

The suite is hermetic: it drives the real ``PanZoomPlugin`` hooks
(``on_post_page`` + ``on_post_build``) to emit an HTML page and copy the real
runtime assets (``zoompan.js``, ``panzoom.min.js``, ``panzoom.css``) into a temp
site directory, then loads that page in headless Chromium. No external binaries
(d2, git) and no network (the Mermaid CDN) are needed: the diagram targets are
inline SVGs, which is exactly the shape D2 and image targets have after a build.

If Playwright or its browser binary is unavailable, the whole package is skipped
rather than failing, so ``make test`` stays green on machines without a browser.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest


# Skip the entire package gracefully if the browser stack is not present.
playwright_module = pytest.importorskip(
    "playwright.sync_api",
    reason="playwright not installed; run 'uv sync' and 'playwright install chromium-headless-shell'",
)
sync_playwright = playwright_module.sync_playwright


# A tiny inline SVG used both as the <img> source and as the .d2 diagram body.
# Using inline SVG keeps the test offline and deterministic.
_IMG_SVG_B64 = (
    "data:image/svg+xml;base64,"
    "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSItMDAi"
    "IGhlaWdodD0iMTAwIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0i"
    "IzM5ZiIvPjwvc3ZnPg=="
)
_D2_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="150">'
    '<rect width="300" height="150" fill="#9c3"/></svg>'
)

_PAGE_HTML = f"""<!doctype html>
<html>
  <head><title>panzoom e2e</title></head>
  <body>
    <img src="{_IMG_SVG_B64}" width="200" height="100" alt="sample">
    <div class="d2">{_D2_SVG}</div>
  </body>
</html>"""


def _browser_available() -> bool:
    """Return True if a headless Chromium can actually be launched."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception:
        return False


if not _browser_available():
    pytest.skip(
        "Chromium for Playwright is unavailable; run 'playwright install chromium-headless-shell'",
        allow_module_level=True,
    )


def _build_site(site_dir: Path, config_overrides: dict | None = None) -> Path:
    """Run the real plugin hooks to emit a hermetic site, return the page path.

    Args:
    ----
    site_dir : Path
        Directory to act as MkDocs ``site_dir``.
    config_overrides : dict | None
        Plugin-config keys to override on top of the scheme defaults.

    Returns
    -------
    Path
        Path to the generated ``index.html``.

    """
    from mkdocs_panzoom_plugin.plugin import PanZoomPlugin

    plugin = PanZoomPlugin()
    plugin.config = {key: opt.default for key, opt in plugin.config_scheme}
    plugin.config.update(
        {
            "images": True,
            "show_zoom_buttons": True,
            "full_screen": True,
            "key": "none",
        }
    )
    if config_overrides:
        plugin.config.update(config_overrides)

    page = Mock()
    page.url = ""  # root page: relative asset URLs resolve to ./assets/...
    page.file = Mock()
    page.file.src_path = "index.md"

    mkdocs_config = Mock()
    theme = Mock()
    theme.name = "mkdocs"  # non-material: zoompan.js runs init immediately
    mkdocs_config.get = Mock(return_value=theme)
    mkdocs_config.__getitem__ = Mock(side_effect=lambda k: {"site_dir": str(site_dir)}[k])

    output = plugin.on_post_page(_PAGE_HTML, page=page, config=mkdocs_config)
    plugin.on_post_build(config=mkdocs_config)

    index = site_dir / "index.html"
    index.write_text(output, encoding="utf-8")
    return index


@pytest.fixture(scope="session")
def site_url(tmp_path_factory) -> str:
    """Build the hermetic demo site once and return a file:// URL to its page."""
    site_dir = tmp_path_factory.mktemp("panzoom-e2e-site")
    index = _build_site(site_dir)
    return index.as_uri()


@pytest.fixture(scope="session")
def _browser():
    """Session-scoped headless Chromium."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(_browser, site_url):
    """Load the demo site in a fresh browser context (isolated localStorage).

    Panzoom initialization is awaited so each test starts from a wired-up state.
    """
    context = _browser.new_context()
    pg = context.new_page()
    page_errors: list[str] = []
    pg.on("pageerror", lambda exc: page_errors.append(str(exc)))
    pg.goto(site_url)
    pg.wait_for_load_state("networkidle")
    # zoompan.js polls on an interval; wait until both targets are wired.
    pg.wait_for_function("document.querySelectorAll('[data-zoom]').length >= 2", timeout=10000)
    pg.page_errors = page_errors  # type: ignore[attr-defined]
    yield pg
    context.close()


def make_site(tmp_path: Path, **config_overrides) -> str:
    """Build a one-off site with custom plugin config; return a file:// URL.

    Used by tests that need a configuration different from the shared session site
    (e.g. a specific modifier key). Not a fixture so callers can parametrize freely.
    """
    site_dir = tmp_path / "site"
    site_dir.mkdir()
    index = _build_site(site_dir, config_overrides=config_overrides)
    return index.as_uri()


def make_site_without_theme_meta(tmp_path: Path) -> str:
    """Build a site, then strip the ``panzoom-theme`` meta tag from the page.

    Exercises the runtime path where ``zoompan.js`` loads on a page that lacks the
    theme meta tag (e.g. a head-less or stripped template): the script must not
    crash on a null ``querySelector`` result.
    """
    import re

    site_dir = tmp_path / "site"
    site_dir.mkdir()
    index = _build_site(site_dir)
    html = index.read_text(encoding="utf-8")
    html = re.sub(r'<meta[^>]*name="panzoom-theme"[^>]*/?>', "", html)
    index.write_text(html, encoding="utf-8")
    return index.as_uri()
