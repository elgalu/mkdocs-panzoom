#!/bin/bash
# Run prek hooks on all files (no CI ref-range logic).
#
# Usage:
#   ./scripts/prek.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
# shellcheck source=/dev/null
source .venv/bin/activate

uvx --from 'prek' prek run --all-files
