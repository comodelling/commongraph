#!/bin/bash

current_dir=$(basename "$PWD")
if [ "$current_dir" != "objectivenet" ] || [ ! -d "backend" ]; then
    echo "Error: This script must be run from the 'objectivenet' directory and require a 'backend' subdirectory."
    exit 1
fi

# Check if backend/.env exists and if not, copy from backend/.envbase
if [ ! -f backend/.env ]; then
    if [ -f backend/.envbase ]; then
        echo "backend/.env not found. Copying from backend/.envbase..."
        cp backend/.envbase backend/.env
        echo "backend/.env has been created. You may edit it to customise your settings."
    else
        echo "Error: Neither backend/.env nor backend/.envbase exist. Aborting."
        exit 1
    fi
fi

# Load environment variables from .env file
set -o allexport
source backend/.env
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
