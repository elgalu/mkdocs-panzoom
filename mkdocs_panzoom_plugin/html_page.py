"""HTML page processing module for the mkdocs-panzoom plugin."""

import json
import logging
from typing import Any

from bs4 import BeautifulSoup, Tag

from mkdocs_panzoom_plugin.panzoom_box import (
    create_css_link,
    create_js_script,
    create_js_script_plugin,
    create_panzoom_box,
)
from mkdocs_panzoom_plugin.yaml_parser import should_enable_panzoom


logger = logging.getLogger(__name__)


class HTMLPage:
    """HTML page processor that adds pan-zoom functionality to images and diagrams."""

    def __init__(
        self, content: str, config: dict[str, Any], page: Any, mkdocs_config: Any
    ) -> None:
        """Initialize HTMLPage with content and configuration.

        Args:
        ----
        content : str
            HTML content to process
        config : dict[str, Any]
            Plugin configuration dictionary
        page : Any
            MkDocs page object
        mkdocs_config : Any
            MkDocs configuration object

        """
        try:
            self.soup = BeautifulSoup(content, "html.parser")
            self.config = config
            self.page = page
            self.mkdocs_config = mkdocs_config
            self.default_selectors: set[str] = {".mermaid", ".d2"}
            self.containers: list[Tag] = self._find_elements()
            logger.debug(f"HTMLPage initialized with {len(self.containers)} containers")
        except Exception as e:
            logger.error(f"Failed to initialize HTMLPage: {e}")
            raise

    def __str__(self) -> str:
        """Return the HTML content as a string."""
        return str(self.soup)

    def add_panzoom(self) -> None:
        """Add pan-zoom functionality to identified containers."""
        try:
            for idx, element in enumerate(self.containers):
                panzoom_box = create_panzoom_box(self.soup, self.config, idx)
                element.wrap(panzoom_box)

            # Include the css and js in the file - with error handling
            if self.soup.head is not None:
                self.soup.head.append(create_css_link(self.soup, self.page))
                self._add_data_for_js()
            else:
                logger.warning("HTML head tag not found, cannot add CSS and metadata")

            if self.soup.body is not None:
                self.soup.body.append(create_js_script(self.soup, self.page))
                self.soup.body.append(create_js_script_plugin(self.soup, self.page))
            else:
                logger.warning("HTML body tag not found, cannot add JavaScript")

            logger.debug(f"Pan-zoom functionality added to {len(self.containers)} containers")
        except Exception as e:
            logger.error(f"Failed to add pan-zoom functionality: {e}")
            raise

    def _add_data_for_js(self) -> None:
        """Add metadata for JavaScript configuration."""
        try:
            meta_tag = self.soup.new_tag("meta")
            meta_tag["name"] = "panzoom-data"
            meta_tag["content"] = json.dumps(
                {
                    "selectors": self.config.get("selectors"),
                    "initial_zoom_level": self.config.get("initial_zoom_level", 1.0),
                    "zoom_step": self.config.get("zoom_step", 0.2),
                    "buttons_size": self.config.get("buttons_size", "1.25em"),
                }
            )
            theme_tag = self.soup.new_tag("meta")
            theme_tag["name"] = "panzoom-theme"

            # Safely access theme name with fallback
            theme_name = "material"  # Default fallback
            if hasattr(self.mkdocs_config, "get"):
                theme = self.mkdocs_config.get("theme")
                if theme and hasattr(theme, "name"):
                    theme_name = theme.name

            theme_tag["content"] = theme_name

            if self.soup.head is not None:
                self.soup.head.append(meta_tag)
                self.soup.head.append(theme_tag)
            else:
                logger.warning("HTML head tag not found, cannot add metadata")

        except Exception as e:
            logger.error(f"Failed to add metadata for JavaScript: {e}")
            # Don't re-raise, this is not critical

    def _find_elements(self) -> list[Tag]:
        """Find elements that should have pan-zoom functionality applied.

        Returns
        -------
            List of BeautifulSoup Tag elements to be wrapped with pan-zoom

        """
        output: list[Tag] = []

        try:
            # Get final set of selectors with proper type handling
            included_selectors_raw = self.config.get("include_selectors", [])
            excluded_selectors_raw = self.config.get("exclude_selectors", [])

            # Ensure we have lists of strings
            if not isinstance(included_selectors_raw, list):
                included_selectors_raw = []
            if not isinstance(excluded_selectors_raw, list):
                excluded_selectors_raw = []

            included_selectors = {str(s) for s in included_selectors_raw}
            excluded_selectors = {str(s) for s in excluded_selectors_raw}

            final_selectors = self.default_selectors.difference(excluded_selectors)
            final_selectors.update(included_selectors)

            if self.config.get("images", False):
                final_selectors.add("img")

            # Fix critical bug: check if mermaid is in final_selectors before removing
            if not self.config.get("mermaid", True) and ".mermaid" in final_selectors:
                final_selectors.remove(".mermaid")

            self.config.update({"selectors": list(final_selectors)})

            for selector in self.config.get("selectors", []):
                try:
                    found_elements = []
                    if selector.startswith("."):
                        # Find by class
                        elements = self.soup.find_all(class_=selector.lstrip("."))
                        found_elements = [elem for elem in elements if isinstance(elem, Tag)]
                    elif selector.startswith("#"):
                        # Find by ID
                        id_element = self.soup.find(id=selector.lstrip("#"))
                        if id_element is not None and isinstance(id_element, Tag):
                            found_elements = [id_element]
                    else:
                        # Find by tag name
                        elements = self.soup.find_all(selector)
                        found_elements = [elem for elem in elements if isinstance(elem, Tag)]

                    # Filter elements based on per-diagram panzoom settings
                    for elem in found_elements:
                        if self._should_apply_panzoom(elem):
                            output.append(elem)
                        else:
                            logger.debug(
                                "Skipping element due to panzoom.enabled=false in YAML metadata"
                            )

                except Exception as e:
                    logger.warning(f"Error processing selector '{selector}': {e}")
                    continue

            logger.debug(f"Found {len(output)} elements for selectors: {final_selectors}")
            return output

        except Exception as e:
            logger.error(f"Failed to find elements: {e}")
            return []

    def _should_apply_panzoom(self, element: Tag) -> bool:
        """Check if panzoom should be applied to an element based on its content.

        Args:
        ----
        element : Tag
            BeautifulSoup Tag element to check

        Returns
        -------
        bool
            True if panzoom should be applied, False if disabled via YAML metadata

        """
        try:
            # Check if this is a Mermaid diagram with potential YAML metadata
            if element.name == "pre" and "mermaid" in element.get("class", []):
                # Look for the code content within the pre element
                code_element = element.find("code")
                if code_element:
                    # Use get_text() to extract all text content, including nested elements
                    content = code_element.get_text()
                    if content:
                        return should_enable_panzoom(content)

            # For other elements (like D2, images), default to enabled
            # Could be extended in the future for other diagram types
            return True

        except Exception as e:
            logger.warning(f"Error checking panzoom settings for element: {e}")
            # Default to enabled on error
            return True
