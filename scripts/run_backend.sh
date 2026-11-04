#!/usr/bin/env bash
set -e

# Resolve directory paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$BACKEND_DIR/.venv"

echo "=== Starting Moodwave Backend Service ==="
echo "Project Root: $PROJECT_ROOT"
echo "Backend Dir:  $BACKEND_DIR"

# Create virtual environment if it does not exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install or update requirements
echo "Installing/verifying requirements from $BACKEND_DIR/requirements.txt..."
pip install -r "$BACKEND_DIR/requirements.txt"

# Run uvicorn from backend directory
echo "Starting uvicorn on http://0.0.0.0:8000..."
cd "$BACKEND_DIR"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
