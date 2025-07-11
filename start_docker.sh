#!/bin/bash

current_dir=$(basename "$PWD")
if [ "$current_dir" != "commongraph" ] || [ ! -d "backend" ]; then
    echo "Error: This script must be run from the 'commongraph' directory and require a 'backend' subdirectory."
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

# Use CONFIG_FILE from .env
if [ -z "$CONFIG_FILE" ]; then
    echo "Error: CONFIG_FILE not set in .env. Aborting."
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file '$CONFIG_FILE' not found. Aborting."
    exit 1
fi

# Function to ensure database exists
ensure_database_exists() {
    echo "Checking if database '$POSTGRES_DB' exists..."
    
    # Wait for PostgreSQL to be ready
    echo "Waiting for PostgreSQL to be ready..."
    docker compose -f docker-compose.yaml exec postgres pg_isready -U "$POSTGRES_USER" -d postgres -h localhost
    
    # Check if our target database exists
    if docker compose -f docker-compose.yaml exec postgres psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$POSTGRES_DB"; then
        echo "Database '$POSTGRES_DB' already exists"
    else
        echo "Creating database '$POSTGRES_DB'"
        docker compose -f docker-compose.yaml exec postgres createdb -U "$POSTGRES_USER" "$POSTGRES_DB"
        echo "Database '$POSTGRES_DB' created successfully"
    fi
    
    # Also ensure test database exists
    if docker compose -f docker-compose.yaml exec postgres psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "testdb"; then
        echo "Test database already exists"
    else
        echo "Creating test database"
        docker compose -f docker-compose.yaml exec postgres createdb -U "$POSTGRES_USER" testdb
        echo "Test database created successfully"
    fi
}

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

# Handle special commands
if [ "$1" = "up" ] || [ "$1" = "start" ]; then
    echo "Starting services..."
    $DOCKER_COMPOSE_CMD up -d postgres
    echo "PostgreSQL started, ensuring database exists..."
    ensure_database_exists
    echo "Starting remaining services..."
    $DOCKER_COMPOSE_CMD up "${@:2}"
# elif [ "$1" = "reset-db" ]; then
#     echo "Resetting database volume..."
#     $DOCKER_COMPOSE_CMD down -v
#     echo "Database volume removed. Starting fresh..."
#     $DOCKER_COMPOSE_CMD up -d postgres
#     sleep 5
#     ensure_database_exists
#     $DOCKER_COMPOSE_CMD up "${@:2}"
else
    # For all other commands, just pass through
    DOCKER_COMPOSE_CMD="$DOCKER_COMPOSE_CMD $@"
    echo "Running command: $DOCKER_COMPOSE_CMD"
    $DOCKER_COMPOSE_CMD
fi