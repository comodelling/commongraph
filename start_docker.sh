#!/bin/bash

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
if [ "$GRAPH_DB_TYPE" = "janusgraph" ]; then
    DOCKER_COMPOSE_CMD="$DOCKER_COMPOSE_CMD -f docker-compose.janusgraph.yaml"
elif [ "$DB_TYPE" != "sqlite" ]; then
    echo "Error: Invalid GRAPH_DB_TYPE specified. Use 'janusgraph' or 'sqlite'."
    exit 1
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
