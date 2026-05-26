#!/bin/bash
# Remove build artifacts, caches, virtual environments, and the rendered docs site.
#
# Usage:
#   ./scripts/clean.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR" || exit 1

echo "Cleaning up..."
find . -name '.venv' -type d -exec rm -rf {} + 2>/dev/null || true
find . -name 'build' -type d -exec rm -rf {} + 2>/dev/null || true
find . -name 'dist' -type d -exec rm -rf {} + 2>/dev/null || true
find . -name '*.egg-info' -type d -exec rm -rf {} + 2>/dev/null || true
find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find . -name '.pytest_cache' -type d -exec rm -rf {} + 2>/dev/null || true
find . -name '.mypy_cache' -type d -exec rm -rf {} + 2>/dev/null || true
find . -name '.ruff_cache' -type d -exec rm -rf {} + 2>/dev/null || true
find . -name 'site' -type d -exec rm -rf {} + 2>/dev/null || true
find . -name 'htmlcov' -type d -exec rm -rf {} + 2>/dev/null || true
find . -name '*.pyc' -delete 2>/dev/null || true
echo "✓ Cleanup complete!"
