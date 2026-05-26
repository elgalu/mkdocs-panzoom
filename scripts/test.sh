#!/bin/bash
# Run pytest with coverage. Extra args are forwarded to pytest.
#
# Usage:
#   ./scripts/test.sh [pytest args...]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
# shellcheck source=/dev/null
source .venv/bin/activate

uv run pytest tests/ -v \
    --cov=mkdocs_panzoom_plugin \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=xml \
    "$@"
