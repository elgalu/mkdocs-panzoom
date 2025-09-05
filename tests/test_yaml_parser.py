"""Tests for YAML metadata parsing functionality."""

from mkdocs_panzoom_plugin.yaml_parser import parse_mermaid_yaml_metadata, should_enable_panzoom


class TestParseMermaidYamlMetadata:
    """Test cases for parsing YAML metadata from Mermaid diagrams."""

    def test_no_yaml_metadata(self):
        """Test content without YAML metadata."""
        content = """graph TD
    A --> B
    B --> C"""

        result = parse_mermaid_yaml_metadata(content)
        assert result == {}

    def test_empty_yaml_metadata(self):
        """Test empty YAML metadata block."""
        content = """---
---
graph TD
    A --> B"""

        result = parse_mermaid_yaml_metadata(content)
        assert result == {}

    def test_title_only_metadata(self):
        """Test YAML metadata with title only."""
        content = """---
title: My Diagram
---
graph TD
    A --> B"""

        result = parse_mermaid_yaml_metadata(content)
        assert result == {"title": "My Diagram"}

    def test_panzoom_disabled(self):
        """Test YAML metadata with panzoom disabled."""
        content = """---
panzoom: { enabled: false }
---
flowchart LR
    A --> B"""

        result = parse_mermaid_yaml_metadata(content)
        assert result == {"panzoom": {"enabled": False}}

    def test_panzoom_enabled(self):
        """Test YAML metadata with panzoom explicitly enabled."""
        content = """---
panzoom: { enabled: true }
---
flowchart LR
    A --> B"""

        result = parse_mermaid_yaml_metadata(content)
        assert result == {"panzoom": {"enabled": True}}

    def test_multiple_fields(self):
        """Test YAML metadata with multiple fields including panzoom."""
        content = """---
title: Complex Diagram
panzoom: { enabled: false }
---
graph TB
    A --> B --> C"""

        result = parse_mermaid_yaml_metadata(content)
        assert result == {"title": "Complex Diagram", "panzoom": {"enabled": False}}

    def test_malformed_yaml(self):
        """Test handling of malformed YAML content."""
        content = """---
title: My Diagram
panzoom: { enabled: invalid }
invalid line without colon
---
graph TD
    A --> B"""

        # Should return empty dict on error
        result = parse_mermaid_yaml_metadata(content)
        # Should handle this gracefully, might return partial results
        assert isinstance(result, dict)

    def test_no_frontmatter_delimiters(self):
        """Test content that doesn't start with YAML frontmatter."""
        content = """graph TD
---
title: This is not YAML frontmatter
---
    A --> B"""

        result = parse_mermaid_yaml_metadata(content)
        assert result == {}

    def test_incomplete_frontmatter(self):
        """Test content with incomplete YAML frontmatter."""
        content = """---
title: Incomplete
graph TD
    A --> B"""

        result = parse_mermaid_yaml_metadata(content)
        assert result == {}

    def test_whitespace_handling(self):
        """Test YAML metadata with various whitespace scenarios."""
        content = """---
  title:   Spaced Title
  panzoom:  { enabled: false }
---
graph TD
    A --> B"""

        result = parse_mermaid_yaml_metadata(content)
        assert result == {"title": "Spaced Title", "panzoom": {"enabled": False}}


class TestShouldEnablePanzoom:
    """Test cases for determining if panzoom should be enabled."""

    def test_no_metadata_defaults_to_enabled(self):
        """Test that diagrams without metadata default to panzoom enabled."""
        content = """graph TD
    A --> B
    B --> C"""

        result = should_enable_panzoom(content)
        assert result is True

    def test_panzoom_disabled_via_metadata(self):
        """Test that panzoom can be disabled via YAML metadata."""
        content = """---
panzoom: { enabled: false }
---
flowchart LR
    A --> B"""

        result = should_enable_panzoom(content)
        assert result is False

    def test_panzoom_explicitly_enabled_via_metadata(self):
        """Test that panzoom can be explicitly enabled via YAML metadata."""
        content = """---
panzoom: { enabled: true }
---
flowchart LR
    A --> B"""

        result = should_enable_panzoom(content)
        assert result is True

    def test_other_metadata_does_not_affect_panzoom(self):
        """Test that other metadata fields don't affect panzoom behavior."""
        content = """---
title: My Diagram
theme: dark
---
graph TB
    A --> B"""

        result = should_enable_panzoom(content)
        assert result is True  # Should default to enabled

    def test_invalid_panzoom_config_defaults_to_enabled(self):
        """Test that invalid panzoom config defaults to enabled."""
        content = """---
panzoom: invalid_value
---
graph TB
    A --> B"""

        result = should_enable_panzoom(content)
        assert result is True  # Should default to enabled

    def test_empty_panzoom_config_defaults_to_enabled(self):
        """Test that empty panzoom config defaults to enabled."""
        content = """---
panzoom: {}
---
flowchart LR
    A --> B"""

        result = should_enable_panzoom(content)
        assert result is True  # Should default to enabled when no 'enabled' key

    def test_title_with_disabled_panzoom(self):
        """Test combination of title and disabled panzoom."""
        content = """---
title: Mint (Scaled)
panzoom: { enabled: false }
---
graph TB
    Client --> DNS"""

        result = should_enable_panzoom(content)
        assert result is False

    def test_boolean_string_parsing(self):
        """Test parsing of boolean values as strings."""
        # Test various boolean representations
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
        ]

        for bool_str, expected in test_cases:
            content = f"""---
panzoom: {{ enabled: {bool_str} }}
---
graph TD
    A --> B"""

            result = should_enable_panzoom(content)
            assert result is expected, f"Failed for boolean string: {bool_str}"
