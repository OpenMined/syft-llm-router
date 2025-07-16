#!/bin/bash

# Syft LLM Router Frontend Development Server
# This script starts the frontend development server

# Show help if requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "🚀 Syft LLM Router Frontend Development Server"
    echo ""
    echo "Usage: ./run_frontend.sh [backend_port]"
    echo ""
    echo "Arguments:"
    echo "  backend_port    Port number for the backend API (default: 8000)"
    echo ""
    echo "Examples:"
    echo "  ./run_frontend.sh          # Use default port 8000"
    echo "  ./run_frontend.sh 8080     # Use custom port 8080"
    echo ""
    exit 0
fi

# Default backend port
BACKEND_PORT=${1:-8000}

# Validate port number
if ! [[ "$BACKEND_PORT" =~ ^[0-9]+$ ]] || [ "$BACKEND_PORT" -lt 1 ] || [ "$BACKEND_PORT" -gt 65535 ]; then
    echo "❌ Error: Invalid port number '$BACKEND_PORT'. Port must be between 1 and 65535."
    echo "Usage: ./run_frontend.sh [backend_port]"
    exit 1
fi

echo "🚀 Starting Syft LLM Router Frontend..."
echo "📡 Backend API proxy configured to http://localhost:${BACKEND_PORT}"

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

# Export backend port for Vite to use
export VITE_BACKEND_PORT=$BACKEND_PORT

# Start the development server
echo "🌐 Starting development server on http://localhost:3000"
echo "📡 API proxy configured to http://localhost:${BACKEND_PORT}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

bun run dev 