# Variables
DOCKER_TAG ?= nanobot:latest
NANOBOT_REPO_PATH ?= ./nanobot

# Default target
.PHONY: help
help:
	@echo "Usage:"
	@echo "  make build-nanobot                    # Build nanobot image with default tag, assumes nanobot is checked out in ./nanobot"
	@echo "  make build-nanobot DOCKER_TAG=mytag  # Build with custom tag"
	@echo "  make build-nanobot NANOBOT_REPO_PATH=path # Build with custom path to nanobot repo"
	@echo "  make build-nanobot DOCKER_TAG=mytag NANOBOT_REPO_PATH=path # Both custom"

# Build nanobot image
.PHONY: build-nanobot
build-nanobot:
	docker build -f Dockerfile.nanobot -t $(DOCKER_TAG) --build-context nanobot=$(NANOBOT_REPO_PATH) $(OPTIONAL_ARGS) .
