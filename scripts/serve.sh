#!/bin/bash
# Run the MkDocs live-preview server (non-strict, so warnings don't block dev).
#
# Usage:
#   ./scripts/serve.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
# shellcheck source=/dev/null
source .venv/bin/activate

echo "Starting documentation server at http://127.0.0.1:8000 ..."
uv run mkdocs serve --no-strict
