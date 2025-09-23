SHELL := /bin/bash

.DEFAULT_GOAL := help

export COMPOSE_DOCKER_CLI_BUILD ?= 1
export DOCKER_BUILDKIT ?= 1

.PHONY: help build backend-build frontend-build test backend-test frontend-test up down deploy deploy-backend deploy-frontend clean

help:
@echo "Available targets:"
@echo "  build            Build frontend and backend Docker images"
@echo "  test             Run frontend and backend test suites inside Docker"
@echo "  up               Start development environment with Docker Compose"
@echo "  down             Stop development environment"
@echo "  deploy           Deploy backend to Scaleway and build frontend bundle"

build: frontend-build backend-build

backend-build:
docker build --target prod -t translate-doc-backend:latest backend

frontend-build:
docker build --target build -t translate-doc-frontend:latest frontend

test: backend-test frontend-test

backend-test:
docker compose run --rm backend pytest

frontend-test:
docker compose run --rm frontend npm run test

up:
docker compose up --build

down:
docker compose down

deploy: deploy-backend deploy-frontend

deploy-backend:
bash scripts/deploy_backend.sh

deploy-frontend:
bash scripts/build_frontend.sh

clean:
docker compose down --volumes --remove-orphans || true
docker image prune -f || true
