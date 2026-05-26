#!/bin/bash
# Display environment information for debugging.
#
# Usage:
#   ./scripts/env.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR" || exit 1

echo "Environment information:"
echo "Project root: $PROJECT_DIR"
echo -n "Python version: " && python --version 2>/dev/null || echo "Python not found"
echo -n "UV version: " && uv --version 2>/dev/null || echo "UV not found"
echo "Virtual environment: ${VIRTUAL_ENV:-Not activated}"
echo "UV project info:"
uv info 2>/dev/null || echo "No UV project found"
echo "UV lock status:"
test -f uv.lock && echo "✓ uv.lock exists" || echo "✗ uv.lock missing"
echo "UV cache info:"
uv cache dir 2>/dev/null || echo "UV cache directory not available"
