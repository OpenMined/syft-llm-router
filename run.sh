#!/bin/bash

# Function to detect if running on Windows
is_windows() {
    [[ "$OSTYPE" == "msys" ]]
}

# Function to add tool to PATH based on platform
add_to_path() {
    local tool_name=$1
    local windows_path=$2
    local unix_path=$3
    
    if is_windows; then
        export PATH="$windows_path:$PATH"
    else
        export PATH="$unix_path:$PATH"
    fi
}

# Function to install uv if not present
install_uv() {
    if ! command -v uv &> /dev/null; then
        echo "uv is not installed. Installing..."
        if is_windows; then
            echo "Windows detected. Installing uv..."
            powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
        else
            curl -fsSL https://astral.sh/uv/install.sh | bash
        fi
    fi
}

# Function to setup uv PATH
setup_uv_path() {
    add_to_path "uv" "$USERPROFILE\\.local\\bin" "$HOME/.local/bin"
}

# Function to install bun based on platform
install_bun() {
    if is_windows; then
        echo "Windows detected. Installing bun..."
        powershell -c "irm bun.sh/install.ps1 | iex"
    else
        if ! command -v bun &> /dev/null; then
            echo "Bun is not installed. Installing..."
            curl -fsSL https://bun.sh/install | bash
        fi
    fi
}

# Function to setup bun PATH and environment
setup_bun_path() {
    if is_windows; then
        export BUN_INSTALL="$USERPROFILE\\.bun"
        export PATH="$BUN_INSTALL\\bin:$PATH"
    else
        export BUN_INSTALL="$HOME/.bun"
        export PATH="$BUN_INSTALL/bin:$PATH"
    fi
}

# Main script starts here
echo "Starting application setup..."

# Clean and setup backend
rm -rf backend/.venv
cd backend

# Install and setup uv
install_uv
setup_uv_path

# Create virtual environment and install dependencies
uv venv -p 3.12 .venv
uv sync
cd ..

# Build frontend
echo "Building frontend..."
cd frontend

# Install and setup bun
install_bun
setup_bun_path

# Build frontend assets
bun install
bun run build
cd ..

# Copy frontend build to backend
echo "Copying frontend build to backend..."
mkdir -p backend/static
cp -r frontend/dist/* backend/static/

# Setup environment file from example.env
echo "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f "example.env" ]; then
        cp example.env .env
        echo "📝 Created .env file from example.env template."
    else
        echo "⚠️  Warning: example.env not found."
    fi
else
    echo "✅ .env file already exists."
fi

# Start the application
SYFTBOX_ASSIGNED_PORT=${SYFTBOX_ASSIGNED_PORT:-8080}
cd backend
echo "Starting server on port $SYFTBOX_ASSIGNED_PORT..."
uv run uvicorn main:app --reload --host 0.0.0.0 --port $SYFTBOX_ASSIGNED_PORT --workers 1