# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MkDocs plugin that adds pan and zoom functionality to images and Mermaid/D2 diagrams.
The plugin uses the [panzoom](https://github.com/anvaka/panzoom) JavaScript library
and integrates with MkDocs through Python hooks to inject necessary HTML, CSS, and JavaScript.

## Architecture

The plugin follows MkDocs plugin architecture with these key components:

- **`mkdocs_panzoom_plugin/plugin.py`**: Main plugin class (`PanZoomPlugin`) that extends `BasePlugin`
- **`mkdocs_panzoom_plugin/html_page.py`**: HTML processing logic for injecting panzoom functionality
- **`mkdocs_panzoom_plugin/exclude.py`**: Page exclusion logic
- **`mkdocs_panzoom_plugin/panzoom_box.py`**: HTML element processing for panzoom containers
- **`mkdocs_panzoom_plugin/custom/`**: CSS and JavaScript assets
- **`mkdocs_panzoom_plugin/panzoom/`**: Third-party panzoom.min.js library

The plugin works by:

1. Processing pages during `on_post_page` hook to inject panzoom HTML/CSS/JS
1. Copying static assets during `on_post_build` hook
1. Using BeautifulSoup to parse and modify HTML content
1. Adding JavaScript initialization code for each diagram/image

## Development Commands

```bash
# Set up development environment
make setup

# Run tests with coverage
make test
# Or directly: uv run pytest tests/ -v --cov=mkdocs_panzoom_plugin --cov-report=term-missing --cov-report=html --cov-report=xml

# Run tests and pre-commit checks
make check

# Build documentation
make build
# Or directly: uv run mkdocs build

# Serve documentation locally
make serve
# Or directly: uv run mkdocs serve

# Clean up build artifacts
make clean

# Display environment information
make env
```

## Key Configuration Options

The plugin supports extensive configuration via `mkdocs.yml`:

- **Selectors**: `include_selectors`/`exclude_selectors` for targeting specific HTML elements
- **Keys**: `key` option (alt/ctrl/shift/none) for disabling pan/zoom
- **UI**: `always_show_hint`, `hint_location`, `show_zoom_buttons`, `buttons_size`
- **Zoom**: `initial_zoom_level`, `zoom_step`
- **Pages**: `exclude` for excluding specific pages
- **Legacy**: `mermaid`, `images` boolean flags

## Testing

The project uses pytest with comprehensive test coverage. Tests are located in `tests/` directory and cover:

- Plugin configuration validation
- HTML processing functionality
- Page exclusion logic
- Asset copying
- Edge cases and error handling

## Code Quality Tools

- **Ruff**: Linting and formatting (configured in pyproject.toml)
- **MyPy**: Type checking (currently with relaxed settings)
- **Pre-commit**: Automated checks on commit
- **Pytest**: Testing with coverage reporting

## Important Notes

- The plugin must be positioned after certain other plugins (like mermaid2) in the plugins list
- Requires `site_url` to be defined in mkdocs.yml
- Uses BeautifulSoup4 for HTML parsing
- Stores zoom state in browser localStorage with automatic cleanup
- Supports Python 3.10+
