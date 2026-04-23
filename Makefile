SHELL := /bin/bash
export ANTHROPIC_API_KEY E2E_FILTER E2E_MODEL HERMES_AGENT_CMD OPENCLAW_AGENT_CMD

COMPOSE := docker compose -f tests/e2e/docker/docker-compose.yml

.PHONY: test test-hermes test-openclaw \
        test-docker test-docker-hermes test-docker-openclaw \
        docker-build docker-shell-hermes docker-shell-openclaw help

test: test-hermes test-openclaw

test-hermes:
	./tests/e2e/hermes/run.sh

test-openclaw:
	./tests/e2e/openclaw/run.sh

test-docker: test-docker-hermes test-docker-openclaw

test-docker-hermes:
	$(COMPOSE) run --rm hermes

test-docker-openclaw:
	$(COMPOSE) run --rm openclaw

docker-build:
	$(COMPOSE) build

docker-shell-hermes:
	$(COMPOSE) run --rm --entrypoint bash hermes

docker-shell-openclaw:
	$(COMPOSE) run --rm --entrypoint bash openclaw

help:
	@printf '%s\n' \
		'Targets:' \
		'  make test                  Run both e2e suites on the host' \
		'  make test-hermes           Run the Hermes e2e suite on the host' \
		'  make test-openclaw         Run the OpenClaw e2e suite on the host' \
		'  make test-docker           Run both e2e suites in Docker' \
		'  make test-docker-hermes    Run the Hermes suite in Docker' \
		'  make test-docker-openclaw  Run the OpenClaw suite in Docker' \
		'  make docker-build          Build both Docker images' \
		'  make docker-shell-hermes   Interactive shell in the Hermes image' \
		'  make docker-shell-openclaw Interactive shell in the OpenClaw image' \
		'' \
		'Useful env vars:' \
		'  ANTHROPIC_API_KEY=...      Provider credential' \
		'  E2E_FILTER=...             Filter fixtures by filename substring' \
		'  E2E_MODEL=...              Model ID (default: claude-sonnet-4-6)' \
		'  HERMES_AGENT_CMD=...       Override the Hermes one-shot command' \
		'  OPENCLAW_AGENT_CMD=...     Override the OpenClaw one-shot command'
