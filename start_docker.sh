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

# Parse command-line arguments
BUILD=false
HELP=false
DETACH=false
INVALID_OPTION=false
for arg in "$@"; do
    if [ "$arg" = "--build" ]; then
        BUILD=true
    elif [ "$arg" = "--help" ]; then
        HELP=true
    elif [ "$arg" = "--detach" ]; then
        DETACH=true
    else
        INVALID_OPTION=true
    fi
done

if [ "$HELP" = true ] || [ "$INVALID_OPTION" = true ]; then
    echo "Usage: $0 [--build] [--help] [--detach]"
    echo "Description: Start ObjectiveNet's Docker containers"
    echo "--build    Build the Docker containers before starting"
    echo "--detach   Run Docker containers in the background"
    echo "--help     Display this help message"
    exit 0
fi

DOCKER_COMPOSE_CMD="docker compose -f docker-compose.yaml"

if [ "$ENABLE_GRAPH_DB" = true ]; then
    DOCKER_COMPOSE_CMD="$DOCKER_COMPOSE_CMD -f docker-compose.janusgraph.yaml"
    echo "Enabling JanusGraph"
fi

if [ "$BUILD" = true ]; then
    DOCKER_COMPOSE_CMD="$DOCKER_COMPOSE_CMD up --build"
else
    DOCKER_COMPOSE_CMD="$DOCKER_COMPOSE_CMD up"
fi

if [ "$DETACH" = true ]; then
    DOCKER_COMPOSE_CMD="$DOCKER_COMPOSE_CMD -d"
fi

echo "Running command: $DOCKER_COMPOSE_CMD"
$DOCKER_COMPOSE_CMD
