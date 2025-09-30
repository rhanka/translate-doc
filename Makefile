SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
FRONTEND_DIR := $(ROOT_DIR)/frontend
BACKEND_DIR := $(ROOT_DIR)/backend

.PHONY: help build test dev up down fmt lint deploy deploy-frontend deploy-backend clean

help:
	@echo "Available targets:"
	@echo "  build            Build frontend and backend containers"
	@echo "  dev              Run the full stack with live rebuilds"
	@echo "  up               Start the local development stack"
	@echo "  down             Stop the local development stack"
	@echo "  clean            Remove containers and volumes"
	@echo "  fmt              Format the frontend sources"
	@echo "  lint             Lint the frontend sources"
	@echo "  test             Run backend tests"
	@echo "  deploy           Deploy frontend and backend"
	@echo "  deploy-frontend  Deploy only the frontend"
	@echo "  deploy-backend   Deploy only the backend"

build:
	docker compose build

dev:
	docker compose up --build

up:
	docker compose up -d

down:
	docker compose down

clean:
	docker compose down -v

fmt:
	docker compose run --rm frontend npm run format
	docker compose run --rm frontend npm run lint

lint:
	docker compose run --rm frontend npm run lint

test:
	docker compose run --rm backend pytest

deploy:
ifeq ($(SKIP_FRONTEND_DEPLOY),1)
	@echo "Skipping frontend deployment (SKIP_FRONTEND_DEPLOY=1)"
else
	$(MAKE) deploy-frontend
endif
ifeq ($(SKIP_BACKEND_DEPLOY),1)
	@echo "Skipping backend deployment (SKIP_BACKEND_DEPLOY=1)"
else
	$(MAKE) deploy-backend
endif

deploy-frontend:
	@if [ -z "$$GITHUB_REPOSITORY" ]; then \
		echo "GITHUB_REPOSITORY must be set (e.g. owner/repo)" >&2; \
		exit 1; \
	fi
	@if [ -z "$$GITHUB_TOKEN" ]; then \
		echo "GITHUB_TOKEN is required to deploy to GitHub Pages" >&2; \
		exit 1; \
	fi
	docker run --rm \
	  -e GITHUB_TOKEN \
	  -e GIT_COMMITTER_NAME="github-actions[bot]" \
	  -e GIT_COMMITTER_EMAIL="github-actions[bot]@users.noreply.github.com" \
	  -e GIT_AUTHOR_NAME="github-actions[bot]" \
	  -e GIT_AUTHOR_EMAIL="github-actions[bot]@users.noreply.github.com" \
	  -e GITHUB_REPOSITORY \
	  -v "$(FRONTEND_DIR):/app" \
	  -w /app \
	  node:20-alpine \
	  sh -c "npm install --legacy-peer-deps && npm run build && npx gh-pages -d dist -r https://x-access-token:$$GITHUB_TOKEN@github.com/$$GITHUB_REPOSITORY.git -u 'github-actions[bot] <github-actions[bot]@users.noreply.github.com>'"

deploy-backend:
	@missing=0; \
	for var in SCW_NAMESPACE_ID SCW_ACCESS_KEY SCW_SECRET_KEY SCW_DEFAULT_ORGANIZATION_ID SCW_DEFAULT_PROJECT_ID SCW_BACKEND_CONTAINER_ID; do \
	  if [ -z "$$$${var}" ]; then \
	    echo "$$var is required" >&2; \
	    missing=1; \
	  fi; \
	done; \
	if [ "$$missing" -ne 0 ]; then exit 1; fi
	TAG=$${GITHUB_SHA:-$$(git rev-parse --short HEAD)}; \
	IMAGE="rg.fr-par.scw.cloud/$${SCW_NAMESPACE_ID}/translate-doc-backend:$${TAG}"; \
	echo "Building backend image $$IMAGE" >&2; \
	docker build --target production -t "$$IMAGE" "$(BACKEND_DIR)"; \
	echo "Authenticating to Scaleway registry" >&2; \
	echo "$$SCW_SECRET_KEY" | docker login rg.fr-par.scw.cloud -u "$$SCW_ACCESS_KEY" --password-stdin; \
	echo "Pushing image" >&2; \
	docker push "$$IMAGE"; \
	echo "Deploying container $$SCW_BACKEND_CONTAINER_ID" >&2; \
	docker run --rm \
	  -e SCW_ACCESS_KEY \
	  -e SCW_SECRET_KEY \
	  -e SCW_DEFAULT_ORGANIZATION_ID \
	  -e SCW_DEFAULT_PROJECT_ID \
	  scaleway/scw-cli:latest \
	  scw container container deploy "$$SCW_BACKEND_CONTAINER_ID" image="$$IMAGE"
