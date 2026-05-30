"""Headless-browser end-to-end tests driving the real runtime (zoompan.js).

Each test loads the hermetically generated site (see conftest) in headless
Chromium and asserts on observable behavior: panzoom initialization, the
zoom/reset/fullscreen controls, the hint toggle, modifier-key gating, and
localStorage persistence.
"""

import re

import pytest

from .conftest import make_site, make_site_without_theme_meta


pytestmark = pytest.mark.e2e


def _scale_of(page, selector: str) -> float:
    """Return the current X-scale of the transform matrix on the first match."""
    transform = page.locator(selector).first.evaluate("e => e.style.transform")
    match = re.search(r"matrix\(([-0-9.]+)", transform or "matrix(1,")
    return float(match.group(1)) if match else 1.0


class TestInitialization:
    """Panzoom wires up the expected targets and assets without errors."""

    def test_no_page_errors(self, page):
        assert page.page_errors == []

    def test_assets_loaded(self, page):
        # The runtime function from zoompan.js must be present on the page.
        assert page.evaluate("typeof activate_zoom_pan") == "function"
        # The panzoom library must have loaded too.
        assert page.evaluate("typeof panzoom") == "function"

    def test_both_targets_wrapped(self, page):
        assert page.locator(".panzoom-box").count() == 2

    def test_targets_initialized(self, page):
        # img and the inline-SVG .d2 div both get data-zoom set by zoompan.js.
        assert page.evaluate("document.querySelectorAll('[data-zoom]').length") == 2

    def test_controls_present(self, page):
        # show_zoom_buttons + full_screen are enabled in the session site.
        assert page.locator(".panzoom-reset").count() == 2
        assert page.locator(".panzoom-zoom-in").count() == 2
        assert page.locator(".panzoom-zoom-out").count() == 2
        assert page.locator(".panzoom-max").count() == 2


class TestZoomControls:
    """The zoom-in / zoom-out / reset buttons change the element transform."""

    def test_zoom_in_increases_scale(self, page):
        before = _scale_of(page, ".panzoom-box img")
        page.locator(".panzoom-box .panzoom-zoom-in").first.click()
        page.wait_for_timeout(250)
        after = _scale_of(page, ".panzoom-box img")
        assert after > before

    def test_zoom_out_decreases_scale(self, page):
        page.locator(".panzoom-box .panzoom-zoom-in").first.click()
        page.wait_for_timeout(200)
        mid = _scale_of(page, ".panzoom-box img")
        page.locator(".panzoom-box .panzoom-zoom-out").first.click()
        page.wait_for_timeout(200)
        after = _scale_of(page, ".panzoom-box img")
        assert after < mid

    def test_reset_restores_identity(self, page):
        page.locator(".panzoom-box .panzoom-zoom-in").first.click()
        page.wait_for_timeout(200)
        assert _scale_of(page, ".panzoom-box img") != 1.0
        page.locator(".panzoom-box .panzoom-reset").first.click()
        page.wait_for_timeout(200)
        assert _scale_of(page, ".panzoom-box img") == 1.0


class TestFullscreen:
    """The maximize/minimize buttons toggle the fullscreen class."""

    def test_maximize_then_minimize(self, page):
        box = page.locator(".panzoom-box").first
        assert box.evaluate("e => e.classList.contains('panzoom-fullscreen')") is False

        page.locator(".panzoom-box .panzoom-max").first.click()
        page.wait_for_timeout(150)
        assert box.evaluate("e => e.classList.contains('panzoom-fullscreen')") is True

        page.locator(".panzoom-box .panzoom-min").first.click()
        page.wait_for_timeout(150)
        assert box.evaluate("e => e.classList.contains('panzoom-fullscreen')") is False


class TestHint:
    """The info button toggles the hint box visibility."""

    def test_info_toggles_hint(self, page):
        hint = page.locator(
            ".panzoom-box .panzoom-info-box, .panzoom-box .panzoom-info-box-top"
        ).first
        assert hint.evaluate("e => e.classList.contains('panzoom-hidden')") is True

        page.locator(".panzoom-box .panzoom-info").first.click()
        page.wait_for_timeout(120)
        assert hint.evaluate("e => e.classList.contains('panzoom-hidden')") is False

        page.locator(".panzoom-box .panzoom-info").first.click()
        page.wait_for_timeout(120)
        assert hint.evaluate("e => e.classList.contains('panzoom-hidden')") is True


class TestPersistence:
    """Zoom state is saved to localStorage and cleared on reset."""

    def test_zoom_writes_localstorage(self, page):
        assert (
            page.evaluate("Object.keys(localStorage).filter(k => k.startsWith('panzoom-')).length")
            == 0
        )
        page.locator(".panzoom-box .panzoom-zoom-in").first.click()
        page.wait_for_timeout(400)  # debounce is 200ms
        keys = page.evaluate("Object.keys(localStorage).filter(k => k.startsWith('panzoom-'))")
        assert len(keys) >= 1

    def test_state_restored_after_reload(self, page):
        page.locator(".panzoom-box .panzoom-zoom-in").first.click()
        page.wait_for_timeout(400)
        saved = _scale_of(page, ".panzoom-box img")
        assert saved != 1.0

        page.reload()
        page.wait_for_load_state("networkidle")
        page.wait_for_function("document.querySelectorAll('[data-zoom]').length >= 2")
        page.wait_for_timeout(200)
        restored = _scale_of(page, ".panzoom-box img")
        assert restored == saved

    def test_reset_clears_localstorage(self, page):
        page.locator(".panzoom-box .panzoom-zoom-in").first.click()
        page.wait_for_timeout(400)
        assert (
            page.evaluate("Object.keys(localStorage).filter(k => k.startsWith('panzoom-')).length")
            >= 1
        )
        page.locator(".panzoom-box .panzoom-reset").first.click()
        # Reset clears storage after the reset-triggered pan/zoom events settle
        # (debounce + margin); wait past that window before asserting.
        page.wait_for_function(
            "Object.keys(localStorage).filter(k => k.startsWith('panzoom-')).length === 0",
            timeout=3000,
        )

    def test_reset_state_stays_cleared(self, page):
        """Regression: the debounced save handlers must not re-persist state after reset.

        Previously panzoom_reset() cleared localStorage synchronously, but the
        moveTo/zoomAbs calls emitted pan/zoom events whose debounced handlers
        re-saved an identity state ~200ms later, so the key reappeared.
        """
        page.locator(".panzoom-box .panzoom-zoom-in").first.click()
        page.wait_for_timeout(400)
        page.locator(".panzoom-box .panzoom-reset").first.click()
        # Wait well past the debounce window, then confirm nothing was re-saved.
        page.wait_for_timeout(600)
        assert (
            page.evaluate("Object.keys(localStorage).filter(k => k.startsWith('panzoom-')).length")
            == 0
        )


class TestModifierKeyGating:
    """The configured modifier key is wired into the box's data-key attribute."""

    def test_data_key_attribute_reflects_config(self, _browser, tmp_path):
        # Build a one-off site with key='ctrl' and confirm the data-key wiring.
        url = make_site(tmp_path, key="ctrl")
        context = _browser.new_context()
        pg = context.new_page()
        pg.goto(url)
        pg.wait_for_load_state("networkidle")
        pg.wait_for_function("document.querySelectorAll('[data-zoom]').length >= 2")
        data_key = pg.locator(".panzoom-box").first.get_attribute("data-key")
        context.close()
        assert data_key == "ctrl"


class TestRobustness:
    """zoompan.js degrades gracefully on unexpected page shapes."""

    def test_missing_theme_meta_does_not_throw(self, _browser, tmp_path):
        """Regression: a missing panzoom-theme meta tag must not crash the script.

        zoompan.js previously did `querySelector(...).content` unguarded, throwing a
        TypeError on any page where the meta tag was absent, which aborted all
        initialization.
        """
        url = make_site_without_theme_meta(tmp_path)
        context = _browser.new_context()
        pg = context.new_page()
        errors: list[str] = []
        pg.on("pageerror", lambda exc: errors.append(str(exc)))
        pg.goto(url)
        pg.wait_for_load_state("networkidle")
        # Initialization still proceeds via the polling fallback.
        pg.wait_for_function("document.querySelectorAll('[data-zoom]').length >= 2", timeout=10000)
        context.close()
        assert errors == []
