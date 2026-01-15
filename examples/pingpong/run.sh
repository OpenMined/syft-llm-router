#!/bin/sh
set -e

# Create virtual environment using Python 3.12
uv venv -p 3.12 .venv

# Install the current project dependencies (if any)
uv pip install .

# Activate the virtual environment
. .venv/bin/activate

# Install dependencies from requirements.txt
# pip install -r requirements.txt

# Start running the server in a loop
while true; do
    echo "Running 'inbox' with $(python3 --version) at '$(which python3)'"
    python3 pong_server.py

    echo "Sleeping for 10 seconds..."
    sleep 10
done

# Deactivate the virtual environment
deactivate