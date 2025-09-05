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


def should_enable_panzoom(content: str) -> bool:
    """Check if panzoom should be enabled for a diagram based on its YAML metadata.

    Args:
    ----
    content : str
        The content of the diagram code block

    Returns
    -------
    bool
        True if panzoom should be enabled (default), False if disabled via metadata

    """
    metadata = parse_mermaid_yaml_metadata(content)

    # Check for panzoom.enabled setting
    panzoom_config = metadata.get("panzoom", {})

    if isinstance(panzoom_config, dict):
        enabled = panzoom_config.get("enabled", True)  # Default to True
        return bool(enabled)

    # Default to enabled if no panzoom config found
    return True
