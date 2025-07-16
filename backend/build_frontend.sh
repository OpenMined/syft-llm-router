#!/bin/bash

# Build frontend static files
echo "Building frontend..."
cd ../frontend
bun install
bun run build
cd ../backend

# Copy frontend build to backend static directory
echo "Copying frontend build to backend..."
mkdir -p static
cp -r ../frontend/dist/* static/

echo "Frontend build complete!" 