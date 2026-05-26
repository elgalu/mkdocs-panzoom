SHELL := /bin/bash
.DEFAULT_GOAL := help
.PHONY: help setup all hooks check prek clean env build serve test tests docs

help: ## Show this help message
	@echo "mkdocs-panzoom-plugin Makefile"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Note: 'make' alone prints this help. Run 'make setup' the first time you clone."

setup: ## First-time contributor setup (.venv, deps, prek hooks, d2 if needed)
	@./scripts/contributor-setup.sh

check: ## Run prek hooks (CI: changed files only; local: --all-files)
	@./scripts/check.sh

prek: ## Run prek on all files unconditionally
	@./scripts/prek.sh

test: ## Run pytest with coverage (extra args via ARGS=...)
	@./scripts/test.sh $(ARGS)

tests: test ## Alias for 'test'

build: ## Build demo docs (mkdocs build --strict, output: site/)
	@./scripts/build.sh

serve: ## Live-preview docs at http://127.0.0.1:8000
	@./scripts/serve.sh

docs: build ## Alias for 'build'

env: ## Print Python / uv / venv diagnostic info
	@./scripts/env.sh

clean: ## Remove .venv, build artifacts, caches, rendered site/
	@./scripts/clean.sh

all: check ## Alias for 'check'
hooks: check ## Alias for 'check'
