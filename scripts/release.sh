#!/usr/bin/env bash
# Create a semver tag, update CHANGELOG and push Docker images.
# Usage: ./scripts/release.sh <docker_registry>
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
LAST_VERSION=${LAST_TAG#v}
COMMITS=$(git log "$LAST_TAG"..HEAD --pretty=format:%s)
BUMP="patch"
for msg in $COMMITS; do
    if [[ "$msg" == *"BREAKING CHANGE"* || "$msg" == *"!:"* ]]; then
        BUMP="major"
        break
    elif [[ "$msg" == feat* && "$BUMP" != major ]]; then
        BUMP="minor"
    elif [[ "$msg" == fix* && "$BUMP" == patch ]]; then
        BUMP="patch"
    fi
done
IFS=. read -r major minor patch <<<"$LAST_VERSION"
case "$BUMP" in
    major)
        major=$((major+1)); minor=0; patch=0;;
    minor)
        minor=$((minor+1)); patch=0;;
    patch)
        patch=$((patch+1));;
esac
NEW_VERSION="$major.$minor.$patch"
DATE=$(date +"%Y-%m-%d")
CHANGELOG_ENTRY="## v$NEW_VERSION - $DATE"$'\n'
CHANGELOG_ENTRY+="$(git log "$LAST_TAG"..HEAD --pretty=format:"- %s (%h)")"$'\n\n'
{ printf "%s" "$CHANGELOG_ENTRY"; cat CHANGELOG.md 2>/dev/null; } > CHANGELOG.tmp
mv CHANGELOG.tmp CHANGELOG.md
git add CHANGELOG.md
git commit -m "chore(release): v$NEW_VERSION" || true
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"
./scripts/build-images.sh
if [[ $# -gt 0 ]]; then
    ./scripts/push-images.sh "$1" "v$NEW_VERSION"
fi
