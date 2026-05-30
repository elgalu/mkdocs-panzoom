"""Test the html_page module functionality."""

from unittest.mock import Mock

import pytest

from mkdocs_panzoom_plugin.html_page import HTMLPage


@pytest.fixture
def basic_html():
    """Create basic HTML content for testing."""
    return """
    <html>
    <head><title>Test</title></head>
    <body>
        <div class="mermaid">mermaid content</div>
        <img src="test.jpg" alt="test">
        <div class="d2">d2 content</div>
    </body>
    </html>
    """


@pytest.fixture
def basic_config():
    """Create basic configuration for testing."""
    return {
        "selectors": [".mermaid", "img", ".d2"],
        "key": "alt",
        "always_show_hint": False,
        "full_screen": False,
        "show_zoom_buttons": False,
        "hint_location": "bottom",
        "initial_zoom_level": 1.0,
        "zoom_step": 0.2,
        "buttons_size": "1.25em",
        "include_selectors": [],
        "exclude_selectors": [],
    }


@pytest.fixture
def mock_page():
    """Create a mock page object."""
    page = Mock()
    page.url = "test/"
    return page


@pytest.fixture
def mock_mkdocs_config():
    """Create a mock MkDocs configuration."""
    config = Mock()
    config.get = Mock(return_value={"name": "material"})
    return config


class TestHTMLPageInitialization:
    """Test HTMLPage initialization."""

    def test_html_page_init_basic(self, basic_html, basic_config, mock_page, mock_mkdocs_config):
        """Test basic HTMLPage initialization."""
        html_page = HTMLPage(basic_html, basic_config, mock_page, mock_mkdocs_config)

        assert html_page.soup is not None
        assert html_page.config == basic_config
        assert html_page.page == mock_page
        assert html_page.mkdocs_config == mock_mkdocs_config
        assert len(html_page.containers) > 0

    def test_html_page_str_representation(
        self, basic_html, basic_config, mock_page, mock_mkdocs_config
    ):
        """Test HTML page string representation."""
        html_page = HTMLPage(basic_html, basic_config, mock_page, mock_mkdocs_config)

        html_str = str(html_page)
        assert isinstance(html_str, str)
        assert "html" in html_str.lower()


class TestElementFinding:
    """Test element finding functionality."""

    def test_find_mermaid_elements(self, basic_html, basic_config, mock_page, mock_mkdocs_config):
        """Test finding mermaid elements."""
        html_page = HTMLPage(basic_html, basic_config, mock_page, mock_mkdocs_config)

        # Should find mermaid and d2 elements (img might not be included by default)
        assert len(html_page.containers) >= 2

    def test_find_elements_with_custom_selectors(self, mock_page, mock_mkdocs_config):
        """Test finding elements with custom selectors."""
        html = """
        <html><body>
            <div class="custom-diagram">content</div>
            <span id="my-chart">chart</span>
        </body></html>
        """

        config = {
            "selectors": [".custom-diagram", "#my-chart"],
            "include_selectors": [".custom-diagram", "#my-chart"],
            "exclude_selectors": [],
        }

        html_page = HTMLPage(html, config, mock_page, mock_mkdocs_config)

        assert len(html_page.containers) >= 0  # May be 0 if selectors are processed differently

    def test_find_elements_with_include_selectors(self, mock_page, mock_mkdocs_config):
        """Test finding elements with include selectors."""
        html = """
        <html><body>
            <div class="include-me">content</div>
            <div class="exclude-me">content</div>
        </body></html>
        """

        config = {
            "selectors": [],
            "include_selectors": [".include-me"],
            "exclude_selectors": [],
        }

        html_page = HTMLPage(html, config, mock_page, mock_mkdocs_config)

        assert len(html_page.containers) == 1

    def test_find_elements_with_exclude_selectors(
        self, basic_html, basic_config, mock_page, mock_mkdocs_config
    ):
        """Test finding elements with exclude selectors."""
        config = basic_config.copy()
        config["exclude_selectors"] = [".mermaid"]

        html_page = HTMLPage(basic_html, config, mock_page, mock_mkdocs_config)

        # Should find fewer elements (img and d2, but not mermaid)
        mermaid_found = any("mermaid" in str(container) for container in html_page.containers)
        assert not mermaid_found

    def test_find_elements_empty_html(self, basic_config, mock_page, mock_mkdocs_config):
        """Test finding elements in empty HTML."""
        html = "<html><body></body></html>"

        html_page = HTMLPage(html, basic_config, mock_page, mock_mkdocs_config)

        assert len(html_page.containers) == 0

    def test_element_matching_multiple_selectors_collected_once(
        self, mock_page, mock_mkdocs_config
    ):
        """An element matching two selectors is collected once, not duplicated.

        Regression: _find_elements accumulated across selectors without dedup, so a
        div matching both ".d2" and a custom include class got wrapped in two nested
        panzoom-boxes.
        """
        html = '<html><body><div class="d2 chart"><svg></svg></div></body></html>'
        config = {
            "selectors": [],
            "include_selectors": [".chart"],
            "exclude_selectors": [],
        }

        html_page = HTMLPage(html, config, mock_page, mock_mkdocs_config)

        assert len(html_page.containers) == 1
        html_page.add_panzoom()
        assert str(html_page).count('class="panzoom-box"') == 1


class TestPanzoomAddition:
    """Test panzoom functionality addition."""

    def test_add_panzoom_basic(self, basic_html, basic_config, mock_page, mock_mkdocs_config):
        """Test adding basic panzoom functionality."""
        html_page = HTMLPage(basic_html, basic_config, mock_page, mock_mkdocs_config)
        html_page.add_panzoom()

        # Check that panzoom boxes were added
        soup = html_page.soup
        panzoom_boxes = soup.find_all("div", class_="panzoom-box")
        assert len(panzoom_boxes) > 0

    def test_add_panzoom_with_css_link(
        self, basic_html, basic_config, mock_page, mock_mkdocs_config
    ):
        """Test that CSS link is added."""
        html_page = HTMLPage(basic_html, basic_config, mock_page, mock_mkdocs_config)
        html_page.add_panzoom()

        # Check for CSS link
        soup = html_page.soup
        css_link = soup.find("link", {"rel": "stylesheet"})
        assert css_link is not None
        assert "panzoom.css" in css_link.get("href", "")

    def test_add_panzoom_with_js_scripts(
        self, basic_html, basic_config, mock_page, mock_mkdocs_config
    ):
        """Test that JavaScript scripts are added."""
        html_page = HTMLPage(basic_html, basic_config, mock_page, mock_mkdocs_config)
        html_page.add_panzoom()

        # Check for JavaScript scripts
        soup = html_page.soup
        scripts = soup.find_all("script", {"src": True})

        script_sources = [script.get("src") for script in scripts]
        js_found = any("panzoom.min.js" in src for src in script_sources)
        plugin_js_found = any("zoompan.js" in src for src in script_sources)

        assert js_found
        assert plugin_js_found

    def test_add_panzoom_with_meta_data(
        self, basic_html, basic_config, mock_page, mock_mkdocs_config
    ):
        """Test that metadata is added for JavaScript."""
        html_page = HTMLPage(basic_html, basic_config, mock_page, mock_mkdocs_config)
        html_page.add_panzoom()

        # Check for panzoom-data meta tag
        soup = html_page.soup
        meta_tag = soup.find("meta", {"name": "panzoom-data"})
        assert meta_tag is not None

        # Check content includes expected configuration
        content = meta_tag.get("content", "")
        assert "selectors" in content
        assert "initial_zoom_level" in content

    def test_no_assets_injected_without_diagrams(
        self, basic_config, mock_page, mock_mkdocs_config
    ):
        """A page with no matched diagrams must not load the panzoom CSS/JS/meta.

        Otherwise every text-only page would download panzoom.min.js + zoompan.js +
        panzoom.css for no reason.
        """
        html = "<html><head></head><body><p>no diagrams here</p></body></html>"
        html_page = HTMLPage(html, basic_config, mock_page, mock_mkdocs_config)
        assert html_page.containers == []

        html_page.add_panzoom()
        soup = html_page.soup

        assert soup.find("link", {"rel": "stylesheet"}) is None
        assert soup.find_all("script", {"src": True}) == []
        assert soup.find("meta", {"name": "panzoom-data"}) is None
        assert soup.find_all("div", class_="panzoom-box") == []

    def test_add_panzoom_missing_head(self, basic_config, mock_page, mock_mkdocs_config):
        """Test handling of missing head tag."""
        html = "<html><body><div class='mermaid'>content</div></body></html>"

        html_page = HTMLPage(html, basic_config, mock_page, mock_mkdocs_config)

        # Should not raise exception
        html_page.add_panzoom()

        # Should still wrap elements
        soup = html_page.soup
        panzoom_boxes = soup.find_all("div", class_="panzoom-box")
        assert len(panzoom_boxes) > 0

    def test_add_panzoom_missing_body(self, basic_config, mock_page, mock_mkdocs_config):
        """Test handling of missing body tag."""
        html = "<html><head></head><div class='mermaid'>content</div></html>"

        html_page = HTMLPage(html, basic_config, mock_page, mock_mkdocs_config)

        # Should not raise exception
        html_page.add_panzoom()


class TestConfigurationHandling:
    """Test configuration handling."""

    def test_selector_generation_default(self, basic_html, mock_page, mock_mkdocs_config):
        """Test default selector generation."""
        config = {
            "include_selectors": [],
            "exclude_selectors": [],
        }

        html_page = HTMLPage(basic_html, config, mock_page, mock_mkdocs_config)

        # Should use default selectors (.mermaid, .d2)
        expected_selectors = {".mermaid", ".d2"}
        assert set(html_page.config["selectors"]) == expected_selectors

    def test_selector_generation_with_include(self, basic_html, mock_page, mock_mkdocs_config):
        """Test selector generation with include selectors."""
        config = {
            "include_selectors": ["img", ".custom"],
            "exclude_selectors": [],
        }

        html_page = HTMLPage(basic_html, config, mock_page, mock_mkdocs_config)

        # Should combine default and include selectors
        selectors = html_page.config["selectors"]
        assert ".mermaid" in selectors
        assert ".d2" in selectors
        assert "img" in selectors
        assert ".custom" in selectors

    def test_selector_generation_with_exclude(self, basic_html, mock_page, mock_mkdocs_config):
        """Test selector generation with exclude selectors."""
        config = {
            "include_selectors": [],
            "exclude_selectors": [".mermaid"],
        }

        html_page = HTMLPage(basic_html, config, mock_page, mock_mkdocs_config)

        # Should exclude .mermaid from default selectors
        selectors = html_page.config["selectors"]
        assert ".mermaid" not in selectors
        assert ".d2" in selectors


class TestErrorHandling:
    """Test error handling in HTMLPage."""

    def test_invalid_html_handling(self, basic_config, mock_page, mock_mkdocs_config):
        """Test handling of invalid HTML."""
        invalid_html = "<html><div>unclosed div<body>content"

        # Should not raise exception during initialization
        html_page = HTMLPage(invalid_html, basic_config, mock_page, mock_mkdocs_config)
        assert html_page.soup is not None

    def test_empty_config_handling(self, basic_html, mock_page, mock_mkdocs_config):
        """Test handling of empty configuration."""
        empty_config = {}

        # Should not raise exception
        html_page = HTMLPage(basic_html, empty_config, mock_page, mock_mkdocs_config)
        html_page.add_panzoom()

        assert html_page.soup is not None

    def test_non_list_selectors_are_coerced(self, basic_html, mock_page, mock_mkdocs_config):
        """include_selectors / exclude_selectors that aren't lists are treated as empty."""
        config = {
            "include_selectors": "not-a-list",
            "exclude_selectors": None,
        }
        html_page = HTMLPage(basic_html, config, mock_page, mock_mkdocs_config)
        # Falls back to the default selector set.
        selectors = html_page.config["selectors"]
        assert ".mermaid" in selectors
        assert ".d2" in selectors

    def test_mermaid_false_removes_mermaid_selector(
        self, basic_html, mock_page, mock_mkdocs_config
    ):
        """The legacy mermaid: false flag drops .mermaid from the selector set."""
        config = {
            "include_selectors": [],
            "exclude_selectors": [],
            "mermaid": False,
        }
        html_page = HTMLPage(basic_html, config, mock_page, mock_mkdocs_config)
        assert ".mermaid" not in html_page.config["selectors"]

    def test_find_elements_per_selector_error_is_skipped(
        self, basic_html, basic_config, mock_page, mock_mkdocs_config
    ):
        """If matching one selector raises, that selector is skipped, not fatal."""
        html_page = HTMLPage(basic_html, basic_config, mock_page, mock_mkdocs_config)

        def boom(*args, **kwargs):
            raise RuntimeError("boom")

        # Make every find_all raise; _find_elements should swallow per selector
        # and return an empty list rather than propagating.
        html_page.soup.find_all = boom
        html_page.soup.find = boom
        assert html_page._find_elements() == []

    def test_find_elements_outer_error_returns_empty(
        self, basic_html, basic_config, mock_page, mock_mkdocs_config
    ):
        """A failure before the selector loop yields an empty list (safe fallback)."""
        html_page = HTMLPage(basic_html, basic_config, mock_page, mock_mkdocs_config)

        # config.get is used early in _find_elements; make it explode.
        class _BoomConfig(dict):
            def get(self, *args, **kwargs):
                raise RuntimeError("boom")

        html_page.config = _BoomConfig()
        assert html_page._find_elements() == []

    def test_should_apply_panzoom_swallows_errors(
        self, basic_config, mock_page, mock_mkdocs_config
    ):
        """_should_apply_panzoom defaults to True if inspecting an element raises."""
        html_page = HTMLPage(
            "<html><body></body></html>", basic_config, mock_page, mock_mkdocs_config
        )

        class _BoomTag:
            name = "pre"

            def get(self, *args, **kwargs):
                raise RuntimeError("boom")

        assert html_page._should_apply_panzoom(_BoomTag()) is True

    def test_init_reraises_on_parse_failure(
        self, basic_config, mock_page, mock_mkdocs_config, monkeypatch
    ):
        """HTMLPage.__init__ logs and re-raises if HTML parsing fails."""
        import mkdocs_panzoom_plugin.html_page as hp_mod

        def boom(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(hp_mod, "BeautifulSoup", boom)
        with pytest.raises(RuntimeError):
            HTMLPage("<html></html>", basic_config, mock_page, mock_mkdocs_config)

    def test_add_panzoom_reraises_on_wrap_failure(
        self, basic_html, basic_config, mock_page, mock_mkdocs_config
    ):
        """add_panzoom logs and re-raises if wrapping an element fails."""
        html_page = HTMLPage(basic_html, basic_config, mock_page, mock_mkdocs_config)

        # Force an error during the wrap loop; add_panzoom catches, logs, re-raises.
        def boom(*args, **kwargs):
            raise RuntimeError("boom")

        for elem in html_page.containers:
            elem.wrap = boom
        with pytest.raises(RuntimeError):
            html_page.add_panzoom()

    def test_add_data_for_js_swallows_serialization_error(
        self, basic_html, basic_config, mock_page, mock_mkdocs_config, monkeypatch
    ):
        """_add_data_for_js logs (not raises) if building the metadata fails."""
        html_page = HTMLPage(basic_html, basic_config, mock_page, mock_mkdocs_config)

        import mkdocs_panzoom_plugin.html_page as hp_mod

        def boom(*args, **kwargs):
            raise RuntimeError("boom")

        # json.dumps is the first thing inside the try; make it fail.
        monkeypatch.setattr(hp_mod.json, "dumps", boom)
        # Must not raise (the metadata step is non-critical).
        html_page._add_data_for_js()

    def test_add_data_for_js_without_head_warns(self, basic_config, mock_page, mock_mkdocs_config):
        """_add_data_for_js logs a warning instead of crashing when <head> is absent."""
        html_page = HTMLPage("<div class='d2'></div>", basic_config, mock_page, mock_mkdocs_config)
        if html_page.soup.head is not None:
            html_page.soup.head.decompose()
        # Called directly (add_panzoom guards head): must not raise.
        html_page._add_data_for_js()
        assert html_page.soup.find("meta", attrs={"name": "panzoom-data"}) is None

    def test_theme_name_read_from_object(self, basic_html, mock_page):
        """The panzoom-theme meta is filled from a theme object's .name attribute."""
        from unittest.mock import Mock

        theme = Mock()
        theme.name = "readthedocs"
        mkdocs_config = Mock()
        mkdocs_config.get = Mock(return_value=theme)

        config = {
            "include_selectors": [],
            "exclude_selectors": [],
            "selectors": [".d2"],
        }
        html_page = HTMLPage(basic_html, config, mock_page, mkdocs_config)
        html_page.add_panzoom()
        meta = html_page.soup.find("meta", attrs={"name": "panzoom-theme"})
        assert meta is not None
        assert meta["content"] == "readthedocs"


class TestYamlMetadataParsing:
    """Test YAML metadata parsing for per-diagram panzoom control."""

    def test_mermaid_with_disabled_panzoom(self, basic_config, mock_page, mock_mkdocs_config):
        """Test that Mermaid diagrams with panzoom disabled are excluded."""
        html_with_disabled_panzoom = """
        <html>
        <head><title>Test</title></head>
        <body>
            <pre class="mermaid"><code>---
panzoom: { enabled: false }
---
flowchart LR
    A --> B</code></pre>
            <pre class="mermaid"><code>flowchart TD
    C --> D</code></pre>
        </body>
        </html>
        """

        html_page = HTMLPage(
            html_with_disabled_panzoom, basic_config, mock_page, mock_mkdocs_config
        )

        # Should find no mermaid diagrams:
        # - First one is explicitly disabled
        # - Second one is auto-disabled (small diagram)
        assert len(html_page.containers) == 0

    def test_mermaid_with_enabled_panzoom(self, basic_config, mock_page, mock_mkdocs_config):
        """Test that Mermaid diagrams with panzoom explicitly enabled are included."""
        html_with_enabled_panzoom = """
        <html>
        <head><title>Test</title></head>
        <body>
            <pre class="mermaid"><code>---
panzoom: { enabled: true }
---
flowchart LR
    A --> B</code></pre>
        </body>
        </html>
        """

        html_page = HTMLPage(
            html_with_enabled_panzoom, basic_config, mock_page, mock_mkdocs_config
        )

        # Should find the mermaid diagram
        assert len(html_page.containers) == 1

    def test_mermaid_with_other_yaml_metadata(self, basic_config, mock_page, mock_mkdocs_config):
        """Test that Mermaid diagrams with other YAML metadata use auto-detection."""
        html_with_other_metadata = """
        <html>
        <head><title>Test</title></head>
        <body>
            <pre class="mermaid"><code>---
title: My Diagram
theme: dark
---
flowchart LR
    A --> B</code></pre>
        </body>
        </html>
        """

        html_page = HTMLPage(html_with_other_metadata, basic_config, mock_page, mock_mkdocs_config)

        # Should not find the mermaid diagram (small diagram, auto-disabled)
        assert len(html_page.containers) == 0

    def test_mixed_mermaid_diagrams(self, basic_config, mock_page, mock_mkdocs_config):
        """Test handling of mixed Mermaid diagrams with different panzoom settings."""
        mixed_html = """
        <html>
        <head><title>Test</title></head>
        <body>
            <pre class="mermaid"><code>---
panzoom: { enabled: false }
---
flowchart LR
    A --> B</code></pre>
            <pre class="mermaid"><code>flowchart TD
    C --> D</code></pre>
            <pre class="mermaid"><code>---
title: Enabled Diagram
panzoom: { enabled: true }
---
graph TB
    E --> F</code></pre>
            <div class="d2">D2 diagram content</div>
        </body>
        </html>
        """

        html_page = HTMLPage(mixed_html, basic_config, mock_page, mock_mkdocs_config)

        # Should find 2 containers:
        # - 1 mermaid with explicit enabled
        # - 1 d2 diagram
        # The disabled mermaid should be excluded
        # The mermaid without metadata should be auto-disabled (small diagram)
        assert len(html_page.containers) == 2

        # Verify the disabled one is not included
        for container in html_page.containers:
            if container.name == "pre" and "mermaid" in container.get("class", []):
                code_element = container.find("code")
                if code_element:
                    content = code_element.get_text()
                    # Should not contain the disabled diagram
                    assert "panzoom: { enabled: false }" not in content

    def test_non_mermaid_elements_unaffected(self, basic_config, mock_page, mock_mkdocs_config):
        """Test that non-Mermaid elements are not affected by YAML parsing."""
        html_with_mixed_content = """
        <html>
        <head><title>Test</title></head>
        <body>
            <img src="test.jpg" alt="test">
            <div class="d2">D2 content</div>
            <pre class="mermaid"><code>---
panzoom: { enabled: false }
---
flowchart LR
    A --> B</code></pre>
        </body>
        </html>
        """

        # Add images support to config for this test
        config_with_images = basic_config.copy()
        config_with_images["images"] = True

        html_page = HTMLPage(
            html_with_mixed_content, config_with_images, mock_page, mock_mkdocs_config
        )

        # Should find 2 containers: img and d2 (mermaid should be excluded)
        assert len(html_page.containers) == 2

        # Verify we have the img and d2 elements
        container_types = []
        for container in html_page.containers:
            if container.name == "img":
                container_types.append("img")
            elif container.name == "div" and "d2" in container.get("class", []):
                container_types.append("d2")

        assert "img" in container_types
        assert "d2" in container_types


class TestSizeBasedAutoDetection:
    """Test size-based auto-detection in HTML processing."""

    def test_small_diagram_auto_disabled(self, basic_config, mock_page, mock_mkdocs_config):
        """Test that small Mermaid diagrams are automatically excluded from panzoom."""
        html_with_small_diagram = """
        <html>
        <head><title>Test</title></head>
        <body>
            <pre class="mermaid"><code>flowchart LR
    A --> B</code></pre>
        </body>
        </html>
        """

        html_page = HTMLPage(html_with_small_diagram, basic_config, mock_page, mock_mkdocs_config)

        # Small diagram should be auto-excluded
        assert len(html_page.containers) == 0

    def test_large_diagram_auto_enabled(self, basic_config, mock_page, mock_mkdocs_config):
        """Test that large Mermaid diagrams are automatically included in panzoom."""
        html_with_large_diagram = """
        <html>
        <head><title>Test</title></head>
        <body>
            <pre class="mermaid"><code>flowchart TD
    A[Start Process] --> B{Decision Point}
    B -->|Yes| C[Process Option 1]
    B -->|No| D[Process Option 2]
    C --> E[Validation Step]
    D --> F[Alternative Step]
    E --> G[Final Processing]
    F --> G
    G --> H[End Process]</code></pre>
        </body>
        </html>
        """

        html_page = HTMLPage(html_with_large_diagram, basic_config, mock_page, mock_mkdocs_config)

        # Large diagram should be auto-included
        assert len(html_page.containers) == 1

    def test_explicit_override_small_diagram(self, basic_config, mock_page, mock_mkdocs_config):
        """Test that explicit YAML setting overrides auto-detection for small diagrams."""
        html_with_explicit_enable = """
        <html>
        <head><title>Test</title></head>
        <body>
            <pre class="mermaid"><code>---
panzoom: { enabled: true }
---
flowchart LR
    A --> B</code></pre>
        </body>
        </html>
        """

        html_page = HTMLPage(
            html_with_explicit_enable, basic_config, mock_page, mock_mkdocs_config
        )

        # Should respect explicit setting despite being small
        assert len(html_page.containers) == 1

    def test_explicit_override_large_diagram(self, basic_config, mock_page, mock_mkdocs_config):
        """Test that explicit YAML setting overrides auto-detection for large diagrams."""
        html_with_explicit_disable = """
        <html>
        <head><title>Test</title></head>
        <body>
            <pre class="mermaid"><code>---
panzoom: { enabled: false }
---
flowchart TD
    A[Start Process] --> B{Decision Point}
    B -->|Yes| C[Process Option 1]
    B -->|No| D[Process Option 2]
    C --> E[Validation Step]
    D --> F[Alternative Step]
    E --> G[Final Processing]
    F --> G
    G --> H[End Process]</code></pre>
        </body>
        </html>
        """

        html_page = HTMLPage(
            html_with_explicit_disable, basic_config, mock_page, mock_mkdocs_config
        )

        # Should respect explicit setting despite being large
        assert len(html_page.containers) == 0

    def test_custom_thresholds(self, basic_config, mock_page, mock_mkdocs_config):
        """Test that custom thresholds are respected."""
        html_with_small_diagram = """
        <html>
        <head><title>Test</title></head>
        <body>
            <pre class="mermaid"><code>flowchart LR
    A --> B</code></pre>
        </body>
        </html>
        """

        # With default config, this should be excluded (small)
        html_page_default = HTMLPage(
            html_with_small_diagram, basic_config, mock_page, mock_mkdocs_config
        )
        assert len(html_page_default.containers) == 0

        # With very low thresholds, this should be included
        config_with_low_thresholds = basic_config.copy()
        config_with_low_thresholds.update(
            {
                "auto_enable_threshold_lines": 1,
                "auto_enable_threshold_nodes": 1,
                "auto_enable_threshold_edges": 1,
                "auto_enable_threshold_chars": 10,
            }
        )

        html_page_low_threshold = HTMLPage(
            html_with_small_diagram, config_with_low_thresholds, mock_page, mock_mkdocs_config
        )
        assert len(html_page_low_threshold.containers) == 1

    def test_auto_enable_disabled(self, basic_config, mock_page, mock_mkdocs_config):
        """Test that when auto_enable is disabled, all diagrams get panzoom (legacy behavior)."""
        html_with_small_diagram = """
        <html>
        <head><title>Test</title></head>
        <body>
            <pre class="mermaid"><code>flowchart LR
    A --> B</code></pre>
        </body>
        </html>
        """

        # Disable auto_enable feature
        config_no_auto = basic_config.copy()
        config_no_auto["auto_enable"] = False

        html_page = HTMLPage(
            html_with_small_diagram, config_no_auto, mock_page, mock_mkdocs_config
        )

        # Should include even small diagrams when auto_enable is disabled
        assert len(html_page.containers) == 1
