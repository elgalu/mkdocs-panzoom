#!/bin/bash
# Run pre-commit hooks via prek.
# In CI (CDP_BUILD_VERSION or CI set), runs only on changed files.
# Otherwise, runs on all files.
#
# Usage:
#   ./scripts/check.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
# shellcheck source=/dev/null
source .venv/bin/activate

if [ -n "${CDP_BUILD_VERSION:-}" ] || [ -n "${CI:-}" ]; then
    uvx --from 'prek' prek run --show-diff-on-failure --from-ref origin/HEAD --to-ref HEAD
else
    uvx --from 'prek' prek run --all-files
fi
