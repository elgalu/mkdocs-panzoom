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

d2_ok() {
    # `d2 --version` is not enough: a wrong-arch binary exits non-zero with
    # "Exec format error". Treat only a clean version print as a working install.
    command_exists d2 && d2 --version >/dev/null 2>&1
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
    if d2_ok; then
        log_info "d2 is already installed: $(d2 --version 2>&1 | head -n1)"
        return 0
    fi

    log_info "Installing d2 (needed by mkdocs-d2-plugin for the demo docs)..."
    if [ "$(uname)" == 'Darwin' ] && command_exists brew; then
        brew install d2
        return 0
    fi

    # The upstream install.sh has misdetected arch on some hosts (pulling an
    # x86-64 build onto arm64), so install the matching release tarball directly.
    local os arch ver
    os=$(uname | tr '[:upper:]' '[:lower:]')
    case "$(uname -m)" in
        aarch64 | arm64) arch="arm64" ;;
        x86_64 | amd64) arch="amd64" ;;
        *) arch="" ;;
    esac
    ver="v0.7.1"
    if [ -n "$arch" ] && command_exists curl; then
        local tmp
        tmp=$(mktemp -d)
        if curl -fsSL -o "$tmp/d2.tar.gz" \
            "https://github.com/terrastruct/d2/releases/download/${ver}/d2-${ver}-${os}-${arch}.tar.gz" \
            && tar xzf "$tmp/d2.tar.gz" -C "$tmp"; then
            mkdir -p "$HOME/.local/bin"
            cp "$tmp/d2-${ver}/bin/d2" "$HOME/.local/bin/d2"
            chmod +x "$HOME/.local/bin/d2"
            rm -rf "$tmp"
            log_info "d2 installed to ~/.local/bin/d2 ($(d2 --version 2>&1 | head -n1))"
            return 0
        fi
        rm -rf "$tmp"
        log_warn "Direct d2 download failed; falling back to upstream installer."
    fi
    curl -fsSL https://d2lang.com/install.sh | sh
}

install_browser() {
    # Playwright drives the headless-browser E2E tests. Install the Chromium
    # headless shell (smaller than full Chromium). Non-fatal if it fails so the
    # rest of setup still succeeds; the E2E suite skips when no browser is present.
    log_info "Installing Chromium for Playwright E2E tests..."
    if ! playwright install chromium-headless-shell; then
        log_warn "Playwright browser install failed; E2E tests will be skipped."
    fi
}

main() {
    log_info "Starting development environment setup..."
    install_uv
    sync_deps
    install_hooks
    install_d2
    install_browser
    log_success "Setup complete. Run 'make check' to verify, or 'make help' to see all targets."
}

main "$@"
