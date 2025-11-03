"""
Pytest configuration for backend tests.

This file is automatically loaded by pytest and sets up the test environment.
"""
import os
import sys
from pathlib import Path

# Ensure we're running from project root
project_root = Path(__file__).parent.parent
os.chdir(project_root)

# Set test configuration if not already set
if "CONFIG_FILE" not in os.environ:
    os.environ["CONFIG_FILE"] = "config/config-example.yaml"

# Set test database URL if not already set
if "POSTGRES_TEST_DB_URL" not in os.environ:
    os.environ["POSTGRES_TEST_DB_URL"] = "postgresql://postgres:postgres@localhost/testdb"

# Set secret key for tests
if "SECRET_KEY" not in os.environ:
    os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
