#!/bin/bash
# Simple shell script to build the executable
# Usage: ./build.sh [clean|include-ini]

echo "🚀 Zoom Poll Analyzer Build Script"
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

cd "$PROJECT_DIR"

if [ "$1" = "clean" ]; then
    echo "🧹 Cleaning build artifacts..."
    python scripts/build_executable.py --clean
    exit 0
fi

if [ "$1" = "include-ini" ]; then
    echo "📦 Building executable with INI file..."
    python scripts/build_executable.py --include-ini
    exit 0
fi

echo "📦 Building executable for current platform..."
python scripts/build_executable.py

echo
echo "✅ Build script completed!"
