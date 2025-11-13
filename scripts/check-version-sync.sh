#!/usr/bin/env bash
# Helper script to check if VERSION and frontend/package.json are in sync
# Usage: scripts/check-version-sync.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

VERSION_FILE="VERSION"
PACKAGE_JSON="frontend/package.json"

if [[ ! -f "$VERSION_FILE" ]]; then
  echo "Error: $VERSION_FILE not found"
  exit 1
fi

if [[ ! -f "$PACKAGE_JSON" ]]; then
  echo "Error: $PACKAGE_JSON not found"
  exit 1
fi

# Read versions
REPO_VERSION=$(cat "$VERSION_FILE")
PACKAGE_VERSION=$(node -p "require('./frontend/package.json').version")

echo "Repository VERSION: $REPO_VERSION"
echo "Frontend package.json: $PACKAGE_VERSION"

if [[ "$REPO_VERSION" == "$PACKAGE_VERSION" ]]; then
  echo "✓ Versions are in sync"
  exit 0
else
  echo "✗ Versions are OUT OF SYNC"
  echo ""
  echo "To fix, run:"
  echo "  npm run sync-version --prefix frontend"
  exit 1
fi
