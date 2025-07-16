#!/usr/bin/env bash
# Release script that updates the changelog using git-cliff and tags a version.

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"

echo "Generating changelog for v$VERSION"
# Prepend the latest release notes to CHANGELOG.md
# The Unreleased section is kept for future changes.
if [ -f CHANGELOG.md ]; then
  git cliff --unreleased --tag "v$VERSION" --prepend CHANGELOG.md
else
  git cliff --unreleased --tag "v$VERSION" > CHANGELOG.md
fi

git add CHANGELOG.md

echo "Committing changelog" 
 git commit -m "chore: update changelog for v$VERSION" && git tag -a "v$VERSION" -m "Release v$VERSION"

echo "Release v$VERSION is ready"
