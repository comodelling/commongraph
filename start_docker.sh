#!/bin/bash

current_dir=$(basename "$PWD")
if [ "$current_dir" != "commongraph" ] || [ ! -d "backend" ]; then
    echo "Error: This script must be run from the 'commongraph' directory and require a 'backend' subdirectory."
    exit 1
fi

if [ ! -f config.yaml ]; then
    echo "Error: config.yaml not found in project root. Aborting."
    exit 1
fi

# Ensure root .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found in project root. Aborting."
    exit 1
fi

# Load environment variables from root .env
set -o allexport
source ./.env
set -o allexport

DOCKER_COMPOSE_CMD="docker compose -f docker-compose.yaml"

if [ "$ENABLE_GRAPH_DB" = true ]; then
    DOCKER_COMPOSE_CMD="$DOCKER_COMPOSE_CMD -f docker-compose.janusgraph.yaml"
    echo "Enabling JanusGraph"
fi

# Append any passed arguments to the docker compose command
DOCKER_COMPOSE_CMD="$DOCKER_COMPOSE_CMD $@"

echo "Running command: $DOCKER_COMPOSE_CMD"
$DOCKER_COMPOSE_CMD