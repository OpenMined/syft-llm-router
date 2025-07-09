#!/bin/bash

# Syft LLM Router Frontend Development Server
# This script starts the frontend development server

echo "🚀 Starting Syft LLM Router Frontend..."

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: frontend/package.json not found. Please run this script from the project root."
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    bun install
fi

# Start the development server
echo "🌐 Starting development server on http://localhost:3000"
echo "📡 API proxy configured to http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

bun run dev 