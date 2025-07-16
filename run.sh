#!/bin/bash

rm -rf backend/.venv

cd backend
uv venv -p 3.12 .venv
uv pip install -r requirements.txt -U
cd ..

# Build frontend static files
echo "Building frontend..."
cd frontend
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
uv run uvicorn app:app --reload --host 0.0.0.0 --port $SYFTBOX_ASSIGNED_PORT --workers 1 