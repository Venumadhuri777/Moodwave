#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ANDROID_DIR="$PROJECT_ROOT/android"

echo "=== Building Moodwave Android Application (Debug) ==="
echo "Android Directory: $ANDROID_DIR"

cd "$ANDROID_DIR"

if [ -f "./gradlew" ]; then
    chmod +x ./gradlew
    ./gradlew assembleDebug "$@"
else
    echo "Error: gradlew not found in $ANDROID_DIR" >&2
    exit 1
fi
