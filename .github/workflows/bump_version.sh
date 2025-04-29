#!/bin/bash

# Function to get the latest version from PyPI (pure bash)
get_latest_version() {
    curl -s "https://pypi.org/pypi/pyfooda/json" | sed -n 's/.*"version": *"\([^"]*\)".*/\1/p' | head -1
}

# Bumps patch version (e.g., 0.1.1 -> 0.1.2)
bump_version() {
    local version=$1                    # Input version string
    local major=$(echo $version | cut -d. -f1)    # Get major version
    local minor=$(echo $version | cut -d. -f2)    # Get minor version
    local patch=$(echo $version | cut -d. -f3)    # Get patch version
    local new_patch=$((patch + 1))               # Increment patch
    echo "$major.$minor.$new_patch"              # Return new version
}

# Read current version and trim whitespace
current_version=$(cat pandas_nhanes/VERSION | tr -d ' \t\n\r')
echo "[BUMP] Current version: $current_version" >&2

# Get latest version from PyPI
latest_version=$(get_latest_version)
echo "[BUMP] Latest version on PyPI: $latest_version" >&2
new_version=$(bump_version "$latest_version")

if [ "$current_version" != "$new_version" ]; then
    echo "[BUMP] Current version of "$current_version" is outdated, using $new_version" >&2
    printf "%s" "$new_version" > pyfooda/VERSION
    echo "[BUMP] Updated pyfooda/VERSION to $new_version" >&2

    if [ -n "$GITHUB_ACTIONS" ]; then
        echo "[BUMP] Committing and pushing version bump..." >&2
        git config --global user.name 'GitHub Actions'
        git config --global user.email 'actions@github.com'
        git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
        git add pyfooda/VERSION
        git commit -m "Bump version to $new_version [skip ci]" >&2
        git push >&2
        echo "[BUMP] Commit and push complete." >&2
    fi
    printf "%s" "$new_version"
    exit 0
else
    echo "[BUMP] Current version of $current_version is up-to-date." >&2
    # Output the un-bumped version string to stdout
    printf "%s" "$current_version"
    exit 0
fi
fi 