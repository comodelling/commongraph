#!/bin/bash

# Load environment variables from .env file
set -o allexport
source backend/.env
set -o allexport

if [ "$DB_TYPE" = "janusgraph" ]; then
    echo "Starting with JanusGraph"
    docker compose -f docker-compose.yaml -f docker-compose.janusgraph.yaml up
elif [ "$DB_TYPE" = "sqlite" ]; then
    echo "Starting with SQLite"
    docker compose -f docker-compose.yaml up
fi
