#!/usr/bin/env bash
# Convenience script: check VERSION sync status, then sync if needed
# Usage: scripts/sync-version.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

VERSION_FILE="VERSION"
PACKAGE_JSON="frontend/package.json"

echo "Checking VERSION sync status..."
echo ""

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
PACKAGE_VERSION=$(node -p "require('./frontend/package.json').version" 2>/dev/null || echo "unknown")

echo "Repository VERSION: $REPO_VERSION"
echo "Frontend package.json: $PACKAGE_VERSION"
echo ""

if [[ "$REPO_VERSION" == "$PACKAGE_VERSION" ]]; then
  echo "✓ Versions are already in sync"
  exit 0
else
  echo "✗ Versions are OUT OF SYNC"
  echo ""
  echo "Running: npm run sync-version --prefix frontend"
  npm run sync-version --prefix frontend

  echo ""
  echo "✓ Version sync complete!"
  echo ""
  echo "Changes staged:"
  git diff --name-only --cached || echo "  (no cached changes)"
  echo ""
  echo "Next steps:"
  echo "  1. Review changes: git diff --cached"
  echo "  2. Commit: git commit -m 'Sync version to $REPO_VERSION'"
  exit 0
fi
