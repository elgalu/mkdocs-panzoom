"""Test the main plugin functionality."""

from collections import OrderedDict
from unittest.mock import Mock

import pytest

from mkdocs_panzoom_plugin.plugin import PanZoomPlugin


@pytest.fixture
def plugin():
    """Create a plugin instance for testing."""
    return PanZoomPlugin()


@pytest.fixture
def mock_page():
    """Create a mock page object."""
    page = Mock()
    page.file = Mock()
    page.file.src_path = "test.md"
    page.file.dest_path = "test/index.html"
    page.title = "Test Page"
    page.content = "Test content"
    page.meta = {}
    page.url = "test/"
    return page


@pytest.fixture
def mock_mkdocs_config():
    """Create a mock MkDocs configuration."""
    config = Mock()
    config.__getitem__ = Mock(
        side_effect=lambda key: {
            "site_url": "https://example.com",
            "plugins": OrderedDict(),
            "theme": {"name": "material"},
        }.get(key)
    )
    config.__contains__ = Mock(side_effect=lambda key: key in {"site_url", "plugins", "theme"})
    config.get = Mock(
        side_effect=lambda key, default=None: {
            "site_url": "https://example.com",
            "plugins": OrderedDict(),
            "theme": {"name": "material"},
        }.get(key, default)
    )
    return config


class TestPluginInitialization:
    """Test plugin initialization."""

    def test_plugin_creation(self):
        """Test that plugin can be created successfully."""
        plugin = PanZoomPlugin()
        assert plugin is not None
        assert hasattr(plugin, "config_scheme")

    def test_plugin_config_scheme(self):
        """Test plugin configuration scheme."""
        plugin = PanZoomPlugin()
        config_dict = dict(plugin.config_scheme)

        expected_keys = {
            "mermaid",
            "images",
            "full_screen",
            "always_show_hint",
            "show_zoom_buttons",
            "key",
            "include",
            "exclude",
            "include_selectors",
            "exclude_selectors",
            "hint_location",
            "initial_zoom_level",
            "zoom_step",
            "buttons_size",
            "auto_enable",
            "auto_enable_threshold_lines",
            "auto_enable_threshold_nodes",
            "auto_enable_threshold_edges",
            "auto_enable_threshold_chars",
        }

        assert set(config_dict.keys()) == expected_keys


class TestPluginConfiguration:
    """Test plugin configuration handling."""

    def test_on_config_basic(self, plugin, mock_mkdocs_config):
        """Test basic configuration handling."""
        # Should not raise exception
        result = plugin.on_config(mock_mkdocs_config)
        assert result is not None

    def test_on_config_with_plugins(self, plugin, mock_mkdocs_config):
        """Test on_config method with various plugin configurations."""
        # Test with empty plugins
        result = plugin.on_config(mock_mkdocs_config)
        assert result is not None

        # Test with search plugin
        mock_mkdocs_config.__getitem__ = Mock(
            side_effect=lambda key: {
                "site_url": "https://example.com",
                "plugins": OrderedDict([("search", {})]),
                "theme": {"name": "material"},
            }.get(key)
        )

        result = plugin.on_config(mock_mkdocs_config)
        assert result is not None

    def test_on_config_plugins_list_with_options_dict(self, plugin):
        """A plugins list using the `- name: {options}` mapping form must not crash.

        Regression: the list branch previously built (entry, {}) tuples and a dict
        entry is unhashable, raising TypeError before any ordering check ran.
        """
        plugin.config = {
            "key": "alt",
            "hint_location": "bottom",
            "zoom_step": 0.2,
            "initial_zoom_level": 1.0,
        }
        config = {"plugins": ["search", {"mermaid2": {}}, {"panzoom": {"full_screen": True}}]}
        assert plugin.on_config(config) is config

    def test_on_config_panzoom_before_mermaid2_raises(self, plugin):
        """Panzoom listed before mermaid2 must raise ConfigurationError."""
        from mkdocs.exceptions import ConfigurationError

        plugin.config = {
            "key": "alt",
            "hint_location": "bottom",
            "zoom_step": 0.2,
            "initial_zoom_level": 1.0,
        }
        config = {"plugins": [{"panzoom": {}}, {"mermaid2": {}}]}
        with pytest.raises(ConfigurationError):
            plugin.on_config(config)


class TestPluginBasics:
    """Test basic plugin functionality."""

    def test_plugin_can_be_imported(self) -> None:
        """Test that the plugin can be imported."""
        assert PanZoomPlugin is not None

    def test_plugin_instantiation(self) -> None:
        """Test plugin can be instantiated."""
        plugin = PanZoomPlugin()
        assert plugin is not None

    def test_plugin_config_scheme(self) -> None:
        """Test plugin configuration scheme."""
        plugin = PanZoomPlugin()

        # Check that config scheme exists and has expected keys
        config_scheme = dict(plugin.config_scheme)

        expected_keys = [
            "mermaid",
            "images",
            "full_screen",
            "always_show_hint",
            "show_zoom_buttons",
            "key",
            "include",
            "exclude",
            "include_selectors",
            "exclude_selectors",
            "hint_location",
            "initial_zoom_level",
            "zoom_step",
            "buttons_size",
        ]

        for key in expected_keys:
            assert key in config_scheme


class TestPluginPostPage:
    """Test plugin post-page processing."""

    def test_on_post_page_basic(self, plugin, mock_page, mock_mkdocs_config):
        """Test basic post-page processing."""
        # Set up basic plugin config
        plugin.config = {
            "exclude": [],
            "key": "alt",
            "always_show_hint": False,
            "full_screen": False,
            "show_zoom_buttons": False,
        }

        html_content = """
        <html>
        <head><title>Test</title></head>
        <body><div class="mermaid">test</div></body>
        </html>
        """

        result = plugin.on_post_page(html_content, page=mock_page, config=mock_mkdocs_config)

        assert isinstance(result, str)
        assert "panzoom-box" in result

    def test_on_post_page_excluded_file(self, plugin, mock_page, mock_mkdocs_config):
        """Test post-page processing with excluded file."""
        # Configure plugin to exclude this file
        plugin.config = {
            "exclude": ["test.md"],
        }

        html_content = "<html><body>content</body></html>"

        result = plugin.on_post_page(html_content, page=mock_page, config=mock_mkdocs_config)

        # Should return original content unchanged
        assert result == html_content

    def test_on_post_page_with_zoom_buttons(self, plugin, mock_page, mock_mkdocs_config):
        """Test post-page processing with zoom buttons enabled."""
        plugin.config = {
            "exclude": [],
            "show_zoom_buttons": True,
            "key": "alt",
        }

        html_content = """
        <html>
        <head><title>Test</title></head>
        <body><div class="mermaid">test</div></body>
        </html>
        """

        result = plugin.on_post_page(html_content, page=mock_page, config=mock_mkdocs_config)

        assert "panzoom-zoom-in" in result
        assert "panzoom-zoom-out" in result

    def test_on_post_page_with_fullscreen(self, plugin, mock_page, mock_mkdocs_config):
        """Test post-page processing with fullscreen enabled."""
        plugin.config = {
            "exclude": [],
            "full_screen": True,
            "key": "alt",
        }

        html_content = """
        <html>
        <head><title>Test</title></head>
        <body><div class="mermaid">test</div></body>
        </html>
        """

        result = plugin.on_post_page(html_content, page=mock_page, config=mock_mkdocs_config)

        assert "panzoom-max" in result
        assert "panzoom-min" in result

    def test_on_post_page_error_handling(self, plugin, mock_page, mock_mkdocs_config):
        """Test error handling in post-page processing."""
        plugin.config = {}

        # Invalid HTML that might cause issues
        html_content = "<html><div>unclosed"

        # Should not raise exception
        result = plugin.on_post_page(html_content, page=mock_page, config=mock_mkdocs_config)
        assert isinstance(result, str)


class TestPluginValidation:
    """Test plugin validation functionality."""

    def test_validate_config_missing_site_url(self, plugin, mock_mkdocs_config):
        """Test validation with missing site_url."""
        plugin.config = {}
        # Create a config without site_url
        mock_mkdocs_config.__getitem__ = Mock(
            side_effect=lambda key: {"plugins": OrderedDict()}.get(key)
        )
        mock_mkdocs_config.__contains__ = Mock(side_effect=lambda key: key in {"plugins"})

        # Should handle missing site_url gracefully
        result = plugin.on_config(mock_mkdocs_config)
        assert result is not None

    def test_validate_config_invalid_key_falls_back_to_alt(self, plugin):
        """An unrecognized 'key' value is reset to the 'alt' default."""
        plugin.config = {"key": "invalid"}
        plugin._validate_config()
        assert plugin.config["key"] == "alt"

    def test_validate_config_invalid_hint_location_falls_back(self, plugin):
        """An unrecognized 'hint_location' is reset to the 'bottom' default."""
        plugin.config = {"hint_location": "sideways"}
        plugin._validate_config()
        assert plugin.config["hint_location"] == "bottom"

    def test_validate_config_invalid_zoom_values_fall_back(self, plugin):
        """Non-positive / non-numeric zoom values are reset to their defaults."""
        plugin.config = {
            "key": "alt",
            "hint_location": "bottom",
            "initial_zoom_level": -1,  # invalid: not positive
            "zoom_step": 0,  # invalid: not positive
        }
        plugin._validate_config()
        assert plugin.config["zoom_step"] == 0.2
        assert plugin.config["initial_zoom_level"] == 1.0

    def test_validate_config_non_numeric_zoom_values_fall_back(self, plugin):
        """A non-numeric zoom value is also reset to its default."""
        plugin.config = {
            "key": "alt",
            "hint_location": "bottom",
            "zoom_step": "fast",
            "initial_zoom_level": "big",
        }
        plugin._validate_config()
        assert plugin.config["zoom_step"] == 0.2
        assert plugin.config["initial_zoom_level"] == 1.0

    def test_on_config_without_plugins_key_returns_config(self, plugin):
        """on_config returns early (unchanged) when there is no 'plugins' key."""
        config = {"site_url": "https://example.com"}
        assert plugin.on_config(config) is config


class TestPluginIntegration:
    """Test plugin integration scenarios."""

    def test_plugin_with_multiple_elements(self, plugin, mock_page, mock_mkdocs_config):
        """Test plugin with multiple diagrams/images."""
        plugin.config = {
            "exclude": [],
            "key": "alt",
            "show_zoom_buttons": True,
        }

        html_content = """
        <html>
        <head><title>Test</title></head>
        <body>
            <div class="mermaid">mermaid 1</div>
            <img src="test.jpg" alt="test">
            <div class="d2">d2 diagram</div>
            <div class="mermaid">mermaid 2</div>
        </body>
        </html>
        """

        result = plugin.on_post_page(html_content, page=mock_page, config=mock_mkdocs_config)

        # Should create multiple panzoom boxes
        panzoom_count = result.count("panzoom-box")
        assert panzoom_count > 1

    def test_plugin_with_custom_selectors(self, plugin, mock_page, mock_mkdocs_config):
        """Test plugin with custom selector configuration."""
        plugin.config = {
            "exclude": [],
            "include_selectors": [".custom-chart"],
            "exclude_selectors": [".mermaid"],
        }

        html_content = """
        <html>
        <body>
            <div class="mermaid">should be excluded</div>
            <div class="custom-chart">should be included</div>
        </body>
        </html>
        """

        result = plugin.on_post_page(html_content, page=mock_page, config=mock_mkdocs_config)

        # Should only process custom-chart, not mermaid
        assert "custom-chart" in result
        # The mermaid div should still be there but not wrapped in panzoom-box
        assert "should be excluded" in result
        assert "should be included" in result


class TestPluginErrorHandling:
    """Error paths in on_post_page / on_post_build degrade gracefully."""

    def test_on_post_page_returns_original_on_error(self, plugin, mock_mkdocs_config):
        """If processing raises, the original HTML is returned unchanged."""
        plugin.config = {"exclude": []}
        html = "<html><body><div class='mermaid'>x</div></body></html>"

        class _BoomFile:
            @property
            def src_path(self):
                raise RuntimeError("boom")

        class _BoomPage:
            file = _BoomFile()

        # The outer try in on_post_page must swallow the error and return input.
        result = plugin.on_post_page(html, page=_BoomPage(), config=mock_mkdocs_config)
        assert result == html

    def test_on_post_build_copies_assets(self, plugin, tmp_path):
        """on_post_build copies the css/js runtime assets into site_dir/assets."""
        config = {"site_dir": str(tmp_path)}
        plugin.on_post_build(config=config)

        css = tmp_path / "assets" / "stylesheets" / "panzoom.css"
        zoompan = tmp_path / "assets" / "javascripts" / "zoompan.js"
        lib = tmp_path / "assets" / "javascripts" / "panzoom.min.js"
        assert css.is_file()
        assert zoompan.is_file()
        assert lib.is_file()

    def test_on_post_build_raises_on_bad_site_dir(self, plugin):
        """A site_dir that can't be created surfaces the error (re-raised)."""
        # A NUL byte in the path makes os.makedirs raise ValueError.
        config = {"site_dir": "\x00invalid"}
        with pytest.raises(ValueError):
            plugin.on_post_build(config=config)
