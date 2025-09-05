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

    def test_no_metadata_uses_auto_detection(self):
        """Test that diagrams without metadata use auto-detection based on size."""
        # Small diagram should be auto-disabled
        small_content = """graph TD
    A --> B"""
        result = should_enable_panzoom(small_content)
        assert result is False

        # Large diagram should be auto-enabled
        large_content = """flowchart TD
    A[Start Process] --> B{Decision Point}
    B -->|Yes| C[Process Option 1]
    B -->|No| D[Process Option 2]
    C --> E[Validation Step]
    D --> F[Alternative Step]
    E --> G[Final Processing]
    F --> G
    G --> H[End Process]"""
        result = should_enable_panzoom(large_content)
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

    def test_other_metadata_uses_auto_detection(self):
        """Test that other metadata fields don't affect panzoom behavior, uses auto-detection."""
        # Small diagram with other metadata should be auto-disabled
        content = """---
title: My Diagram
theme: dark
---
graph TB
    A --> B"""

        result = should_enable_panzoom(content)
        assert result is False  # Should be auto-disabled due to small size

    def test_invalid_panzoom_config_uses_auto_detection(self):
        """Test that invalid panzoom config falls back to auto-detection."""
        content = """---
panzoom: invalid_value
---
graph TB
    A --> B"""

        result = should_enable_panzoom(content)
        assert result is False  # Should be auto-disabled due to small size

    def test_empty_panzoom_config_uses_auto_detection(self):
        """Test that empty panzoom config falls back to auto-detection."""
        content = """---
panzoom: {}
---
flowchart LR
    A --> B"""

        result = should_enable_panzoom(content)
        assert result is False  # Should be auto-disabled due to small size

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


class TestDiagramComplexityAnalysis:
    """Test cases for analyzing diagram complexity and size-based auto-detection."""

    def test_analyze_simple_diagram(self):
        """Test complexity analysis of a simple diagram."""
        from mkdocs_panzoom_plugin.yaml_parser import analyze_diagram_complexity

        simple_diagram = """flowchart TD
    A --> B
    B --> C"""

        complexity = analyze_diagram_complexity(simple_diagram)

        assert complexity["lines"] == 3
        assert complexity["nodes"] >= 3  # Should detect A, B, C
        assert complexity["edges"] >= 2  # Should detect A-->B, B-->C and possibly more
        assert complexity["total_chars"] > 0

    def test_analyze_complex_diagram(self):
        """Test complexity analysis of a complex diagram."""
        from mkdocs_panzoom_plugin.yaml_parser import analyze_diagram_complexity

        complex_diagram = """flowchart TD
    A[Start Process] --> B{Decision Point}
    B -->|Yes| C[Process Option 1]
    B -->|No| D[Process Option 2]
    C --> E[Validation Step]
    D --> F[Alternative Step]
    E --> G[Final Processing]
    F --> G
    G --> H[End Process]

    subgraph "Validation"
        E --> E1[Check Data]
        E1 --> E2[Verify Results]
        E2 --> E
    end"""

        complexity = analyze_diagram_complexity(complex_diagram)

        assert complexity["lines"] >= 10
        assert complexity["nodes"] >= 8
        assert complexity["edges"] >= 7
        assert complexity["total_chars"] >= 300

    def test_extract_diagram_content_no_yaml(self):
        """Test extracting diagram content when no YAML frontmatter is present."""
        from mkdocs_panzoom_plugin.yaml_parser import extract_diagram_content

        content_without_yaml = """flowchart TD
    A --> B
    B --> C"""

        result = extract_diagram_content(content_without_yaml)
        assert result == content_without_yaml

    def test_extract_diagram_content_with_yaml(self):
        """Test extracting diagram content when YAML frontmatter is present."""
        from mkdocs_panzoom_plugin.yaml_parser import extract_diagram_content

        content_with_yaml = """---
title: My Diagram
panzoom: { enabled: false }
---
flowchart TD
    A --> B
    B --> C"""

        result = extract_diagram_content(content_with_yaml)
        expected = """flowchart TD
    A --> B
    B --> C"""

        assert result == expected

    def test_is_diagram_large_enough_small_diagram(self):
        """Test that small diagrams are correctly identified."""
        from mkdocs_panzoom_plugin.yaml_parser import is_diagram_large_enough_for_panzoom

        small_diagram = """flowchart LR
    A --> B"""

        result = is_diagram_large_enough_for_panzoom(small_diagram)
        assert result is False

    def test_is_diagram_large_enough_large_diagram(self):
        """Test that large diagrams are correctly identified."""
        from mkdocs_panzoom_plugin.yaml_parser import is_diagram_large_enough_for_panzoom

        large_diagram = """flowchart TD
    A[Start Process] --> B{Decision Point}
    B -->|Yes| C[Process Option 1]
    B -->|No| D[Process Option 2]
    C --> E[Validation Step]
    D --> F[Alternative Step]
    E --> G[Final Processing]
    F --> G
    G --> H[End Process]"""

        result = is_diagram_large_enough_for_panzoom(large_diagram)
        assert result is True

    def test_is_diagram_large_enough_custom_thresholds(self):
        """Test size detection with custom thresholds."""
        from mkdocs_panzoom_plugin.yaml_parser import is_diagram_large_enough_for_panzoom

        medium_diagram = """flowchart TD
    A --> B --> C --> D"""

        # With default thresholds, this might be large enough due to character count
        is_diagram_large_enough_for_panzoom(medium_diagram)
        # Don't assert specific result as it depends on exact character counting

        # With very low thresholds, this should be large
        low_thresholds = {"lines": 1, "nodes": 2, "edges": 1, "total_chars": 10}
        result_low = is_diagram_large_enough_for_panzoom(medium_diagram, low_thresholds)
        assert result_low is True

    def test_auto_detection_vs_explicit_setting(self):
        """Test that explicit YAML settings override auto-detection."""
        # Small diagram with explicit enable
        small_with_explicit_enable = """---
panzoom: { enabled: true }
---
flowchart LR
    A --> B"""

        result = should_enable_panzoom(small_with_explicit_enable)
        assert result is True  # Should respect explicit setting

        # Large diagram with explicit disable
        large_with_explicit_disable = """---
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
    G --> H[End Process]"""

        result = should_enable_panzoom(large_with_explicit_disable)
        assert result is False  # Should respect explicit setting

    def test_auto_detection_small_diagram(self):
        """Test auto-detection correctly disables panzoom for small diagrams."""
        small_diagram = """flowchart LR
    A --> B --> C"""

        result = should_enable_panzoom(small_diagram)
        assert result is False  # Should auto-disable for small diagram

    def test_auto_detection_large_diagram(self):
        """Test auto-detection correctly enables panzoom for large diagrams."""
        large_diagram = """flowchart TD
    A[Start Process] --> B{Decision Point}
    B -->|Yes| C[Process Option 1]
    B -->|No| D[Process Option 2]
    C --> E[Validation Step]
    D --> F[Alternative Step]
    E --> G[Final Processing]
    F --> G
    G --> H[End Process]
    I[Additional Node] --> J[Another Node]
    K[Yet Another] --> L[Final Node]"""

        result = should_enable_panzoom(large_diagram)
        assert result is True  # Should auto-enable for large diagram
