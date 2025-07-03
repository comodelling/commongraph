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

# Load environment-specific overrides
if [ "$APP_ENV" = "production" ] && [ -f .env.production ]; then
    source ./.env.production
    echo "Loaded production environment overrides"
elif [ "$APP_ENV" = "development" ] && [ -f .env.development ]; then
    source ./.env.development  
    echo "Loaded development environment overrides"
fi
set -o allexport

# Determine which environment-specific compose file to use
ENV_COMPOSE_FILE=""
if [ "$APP_ENV" = "production" ]; then
    ENV_COMPOSE_FILE="-f docker-compose.prod.yaml"
    echo "Using production environment"
elif [ "$APP_ENV" = "development" ]; then
    ENV_COMPOSE_FILE="-f docker-compose.dev.yaml"
    echo "Using development environment"
fi

DOCKER_COMPOSE_CMD="docker compose -f docker-compose.yaml"

# Add environment-specific compose file
if [ -n "$ENV_COMPOSE_FILE" ]; then
    DOCKER_COMPOSE_CMD="$DOCKER_COMPOSE_CMD $ENV_COMPOSE_FILE"
fi

if [ "$ENABLE_GRAPH_DB" = true ]; then
    DOCKER_COMPOSE_CMD="$DOCKER_COMPOSE_CMD -f docker-compose.janusgraph.yaml"
    echo "Enabling JanusGraph"
fi

# Append any passed arguments to the docker compose command
DOCKER_COMPOSE_CMD="$DOCKER_COMPOSE_CMD $@"

echo "Running command: $DOCKER_COMPOSE_CMD"
$DOCKER_COMPOSE_CMD