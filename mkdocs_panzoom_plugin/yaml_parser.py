"""YAML metadata parser for Mermaid diagrams."""

import logging
import re
from typing import Any


logger = logging.getLogger(__name__)


def parse_mermaid_yaml_metadata(content: str) -> dict[str, Any]:
    """Parse YAML metadata from Mermaid diagram content.

    Args:
    ----
    content : str
        The content of the Mermaid diagram code block

    Returns
    -------
    dict[str, Any]
        Parsed YAML metadata as a dictionary. Returns empty dict if no metadata found.

    Example
    -------
    Input content:
    ```
    ---
    title: My Diagram
    panzoom: { enabled: false }
    ---
    graph TD
        A --> B
    ```

    Returns: {"title": "My Diagram", "panzoom": {"enabled": False}}

    """
    metadata: dict[str, Any] = {}

    try:
        # Check if content starts with YAML frontmatter
        if not content.strip().startswith("---"):
            return metadata

        # Find the YAML frontmatter block
        yaml_pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(yaml_pattern, content.strip(), re.DOTALL | re.MULTILINE)

        if not match:
            return metadata

        yaml_content = match.group(1)

        # Parse the YAML content manually to avoid adding dependencies
        # This is a simple parser that handles the basic cases we need
        for line in yaml_content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Handle simple key: value pairs
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Handle different value types
                if key == "panzoom":
                    # Parse panzoom object syntax: { enabled: false }
                    if value.startswith("{") and value.endswith("}"):
                        # Extract content between braces
                        obj_content = value[1:-1].strip()
                        panzoom_config = {}

                        # Parse key: value pairs within the object
                        for pair in obj_content.split(","):
                            if ":" in pair:
                                obj_key, obj_value = pair.split(":", 1)
                                obj_key = obj_key.strip()
                                obj_value = obj_value.strip()

                                # Convert boolean strings
                                if obj_value.lower() == "true":
                                    obj_value = True
                                elif obj_value.lower() == "false":
                                    obj_value = False

                                panzoom_config[obj_key] = obj_value

                        metadata[key] = panzoom_config
                    else:
                        # Handle as string value
                        metadata[key] = str(value)
                else:
                    # Handle other metadata fields as strings
                    metadata[key] = str(value)

        logger.debug(f"Parsed YAML metadata: {metadata}")
        return metadata

    except Exception as e:
        logger.warning(f"Error parsing YAML metadata: {e}")
        return {}


def analyze_diagram_complexity(diagram_content: str) -> dict[str, int]:
    """Analyze the complexity of a Mermaid diagram based on its source code.

    Args:
    ----
    diagram_content : str
        The Mermaid diagram source code (without YAML frontmatter)

    Returns
    -------
    dict[str, int]
        Dictionary containing complexity metrics:
        - lines: Number of non-empty lines
        - nodes: Estimated number of nodes/elements
        - edges: Estimated number of connections/arrows
        - total_chars: Total character count

    """
    if not diagram_content:
        return {"lines": 0, "nodes": 0, "edges": 0, "total_chars": 0}

    lines = [line.strip() for line in diagram_content.split("\n") if line.strip()]
    non_empty_lines = len(lines)
    total_chars = len(diagram_content)

    # Count potential nodes more conservatively
    # Look for node definitions (not just references in connections)
    node_patterns = [
        r"(\b[A-Z][A-Z0-9]*)\s*\[",  # A[Text] - node with bracket description
        r"(\b[A-Z][A-Z0-9]*)\s*\(",  # A(Text) - node with parentheses description
        r"(\b[A-Z][A-Z0-9]*)\s*\{",  # A{Text} - node with brace description (decision)
        r"(\b[A-Z][A-Z0-9]*)\s*-->",  # A --> B - simple node references in connections
        r"-->\s*(\b[A-Z][A-Z0-9]*)",  # A --> B - target nodes in connections
    ]

    nodes = set()
    for line in lines:
        for pattern in node_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            nodes.update(matches)

    # Count edges/connections (arrows and connections)
    edge_patterns = [
        r"-->",  # Standard arrow
        r"---",  # Line connection
        r"-\.",  # Dotted line
        r"==",  # Thick line
        r"==>",  # Thick arrow
        r"->>",  # Message arrow
        r"->",  # Simple arrow
    ]

    edges = 0
    for line in lines:
        for pattern in edge_patterns:
            edges += len(re.findall(pattern, line))

    return {
        "lines": non_empty_lines,
        "nodes": len(nodes),
        "edges": edges,
        "total_chars": total_chars,
    }


def is_diagram_large_enough_for_panzoom(
    diagram_content: str, thresholds: dict[str, int] | None = None
) -> bool:
    """Determine if a diagram is large/complex enough to benefit from panzoom.

    Args:
    ----
    diagram_content : str
        The Mermaid diagram source code (without YAML frontmatter)
    thresholds : dict[str, int], optional
        Custom thresholds for determining if panzoom should be enabled.
        Default thresholds: {"lines": 8, "nodes": 6, "edges": 5, "total_chars": 200}

    Returns
    -------
    bool
        True if diagram is complex enough for panzoom, False otherwise

    """
    if thresholds is None:
        thresholds = {
            "lines": 8,  # 8+ lines of diagram code
            "nodes": 6,  # 6+ nodes/elements
            "edges": 5,  # 5+ connections
            "total_chars": 200,  # 200+ characters total
        }

    complexity = analyze_diagram_complexity(diagram_content)

    # Use OR logic - if any metric exceeds threshold, enable panzoom
    return (
        complexity["lines"] >= thresholds["lines"]
        or complexity["nodes"] >= thresholds["nodes"]
        or complexity["edges"] >= thresholds["edges"]
        or complexity["total_chars"] >= thresholds["total_chars"]
    )


def extract_diagram_content(full_content: str) -> str:
    """Extract just the diagram content, removing YAML frontmatter if present.

    Args:
    ----
    full_content : str
        The full Mermaid content including potential YAML frontmatter

    Returns
    -------
    str
        Just the diagram content without YAML frontmatter

    """
    # Check if content has YAML frontmatter
    if not full_content.strip().startswith("---"):
        return full_content

    # Find the YAML frontmatter block and remove it
    yaml_pattern = r"^---\s*\n.*?\n---\s*\n"
    match = re.match(yaml_pattern, full_content.strip(), re.DOTALL | re.MULTILINE)

    if match:
        # Return content after the YAML block
        return full_content[match.end() :].strip()

    return full_content


def should_enable_panzoom(content: str, thresholds: dict[str, int] | None = None) -> bool:
    """Check if panzoom should be enabled for a diagram based on YAML metadata and size.

    This function implements smart auto-detection:
    1. If YAML explicitly sets panzoom.enabled, respect that setting
    2. Otherwise, auto-detect based on diagram complexity/size
    3. Small/simple diagrams get panzoom disabled by default
    4. Large/complex diagrams get panzoom enabled by default

    Args:
    ----
    content : str
        The content of the diagram code block
    thresholds : dict[str, int], optional
        Custom thresholds for size-based auto-detection

    Returns
    -------
    bool
        True if panzoom should be enabled, False otherwise

    """
    metadata = parse_mermaid_yaml_metadata(content)
    panzoom_config = metadata.get("panzoom", {})

    # If user explicitly set panzoom.enabled in YAML, respect that choice
    if isinstance(panzoom_config, dict) and "enabled" in panzoom_config:
        enabled = panzoom_config.get("enabled", True)
        logger.debug(f"Using explicit panzoom setting: {enabled}")
        return bool(enabled)

    # No explicit setting found - use size-based auto-detection
    diagram_content = extract_diagram_content(content)
    complexity = analyze_diagram_complexity(diagram_content)
    is_large = is_diagram_large_enough_for_panzoom(diagram_content, thresholds)

    logger.debug(
        f"Auto-detecting panzoom for diagram: complexity={complexity}, is_large={is_large}"
    )
    return is_large
