#!/bin/bash

rm -rf backend/.venv

cd backend
uv venv -p 3.12 .venv
# install dependencies from pyproject.toml
uv sync
cd ..

# Build frontend static files
echo "Building frontend..."
cd frontend

# Install bun if not installed
if [[ "$OSTYPE" == "msys" ]]; then
    echo "Windows detected. Installing bun..."
    powershell -c "irm bun.sh/install.ps1 | iex"
    # Add Bun to PATH for this session
    export BUN_INSTALL="$USERPROFILE\\.bun"
    export PATH="$BUN_INSTALL\\bin:$PATH"
else
    # Else, for MacOS and Linux, install bun
    if ! command -v bun &> /dev/null; then
        echo "Bun is not installed. Installing..."
        curl -fsSL https://bun.sh/install | bash
        # Add Bun to PATH for this script session
        export BUN_INSTALL="$HOME/.bun"
        export PATH="$BUN_INSTALL/bin:$PATH"
    fi
fi

# Ensure Bun is in PATH even if already installed
if [[ "$OSTYPE" == "msys" ]]; then
    export BUN_INSTALL="$USERPROFILE\\.bun"
    export PATH="$BUN_INSTALL\\bin:$PATH"
else
    export BUN_INSTALL="$HOME/.bun"
    export PATH="$BUN_INSTALL/bin:$PATH"
fi
# Install bun dependencies
bun install
bun run build
cd ..

# Copy frontend build to backend static directory
echo "Copying frontend build to backend..."
mkdir -p backend/static
cp -r frontend/dist/* backend/static/

# Set default port if not provided
SYFTBOX_ASSIGNED_PORT=${SYFTBOX_ASSIGNED_PORT:-8080}
cd backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port $SYFTBOX_ASSIGNED_PORT --workers 1 