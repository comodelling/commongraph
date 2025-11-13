#!/bin/bash
set -e

# Function to create database if it doesn't exist
create_database_if_not_exists() {
    local db_name=$1
    echo "Checking if database '$db_name' exists..."

    # Check if database exists, create if it doesn't
    if psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$db_name"; then
        echo "Database '$db_name' already exists"
    else
        echo "Creating database '$db_name'"
        createdb -U "$POSTGRES_USER" "$db_name"
        echo "Database '$db_name' created successfully"
    fi
}

# Create the main application database
create_database_if_not_exists "$POSTGRES_DB"

# Create the test database
create_database_if_not_exists "testdb"

echo "Database initialization completed!"
