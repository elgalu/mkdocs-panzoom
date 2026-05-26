#!/bin/bash
# Build the demo MkDocs site with strict mode.
#
# Usage:
#   ./scripts/build.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
# shellcheck source=/dev/null
source .venv/bin/activate

if [ ! -f "mkdocs.yml" ]; then
    echo "No mkdocs.yml found, skipping docs build."
    exit 0
fi

echo "Building documentation (output: site/)..."
uv run mkdocs build --strict
echo "✓ Documentation built!"
