#!/usr/bin/env bash
# ==============================================================================
# Development Environment Setup and Contributor Bootstrap Script
# ==============================================================================
#
# PURPOSE:
#   Idempotently set up a contributor's local environment for the
#   mkdocs-panzoom-plugin project: uv, .venv with Python from .python-version,
#   project deps via `uv sync`, prek hooks from .pre-commit-config.yaml, and
#   d2 (only because mkdocs-d2-plugin is in pyproject.toml for the demo docs).
#
# USAGE:
#   ./scripts/contributor-setup.sh
#
# CI BEHAVIOR:
#   When CDP_BUILD_VERSION or CI is set, runs `uv sync --frozen` for
#   reproducibility and skips d2 install.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

is_ci() {
    [ -n "${CDP_BUILD_VERSION:-}" ] || [ -n "${CI:-}" ] || [ -n "${GITHUB_ACTIONS:-}" ]
}

install_uv() {
    if command_exists uv; then
        log_info "uv is already installed: $(uv --version)"
        return 0
    fi

    log_info "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # uv installs to ~/.local/bin
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        export PATH="$HOME/.local/bin:$PATH"
    fi
}

sync_deps() {
    log_info "Setting up Python environment with uv..."
    if is_ci; then
        # In CI, install exactly what is in the committed lockfile. --frozen skips
        # dependency re-resolution so the build is reproducible and fails fast if
        # the lockfile is out of sync with pyproject.toml.
        UV_HTTP_TIMEOUT=300 uv sync --frozen
    else
        UV_HTTP_TIMEOUT=300 uv sync
    fi
}

install_hooks() {
    log_info "Installing prek (pre-commit) hooks..."
    # shellcheck source=/dev/null
    source .venv/bin/activate
    # prek is pre-commit-compatible and faster. Install via uv tool if missing.
    if ! command_exists prek; then
        uv tool install prek
    fi
    prek install --install-hooks
}

install_d2() {
    # d2 is only needed locally for `make serve` / `make build` to render D2 diagrams
    # in the demo docs. Skip in CI to keep the build fast.
    if is_ci; then
        log_info "CI detected, skipping d2 install."
        return 0
    fi
    if ! grep -q "mkdocs-d2-plugin" pyproject.toml 2>/dev/null; then
        return 0
    fi
    if command_exists d2; then
        log_info "d2 is already installed: $(d2 --version 2>&1 | head -n1)"
        return 0
    fi

    log_info "Installing d2 (needed by mkdocs-d2-plugin for the demo docs)..."
    if [ "$(uname)" == 'Darwin' ] && command_exists brew; then
        brew install d2
    else
        curl -fsSL https://d2lang.com/install.sh | sh
    fi
}

main() {
    log_info "Starting development environment setup..."
    install_uv
    sync_deps
    install_hooks
    install_d2
    log_success "Setup complete. Run 'make check' to verify, or 'make help' to see all targets."
}

main "$@"
