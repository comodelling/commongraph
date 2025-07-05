#!/bin/bash
set -e

# This script is now deprecated in favor of init-databases.sh
# Keeping it for backward compatibility

echo "Note: This script is deprecated. Please use init-databases.sh instead."
echo "Creating test database for backward compatibility..."

# Create the test database using createdb (simpler and more reliable)
if ! psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "testdb"; then
    echo "Creating test database..."
    createdb -U "$POSTGRES_USER" testdb
    echo "Test database created successfully"
else
    echo "Test database already exists"
fi
