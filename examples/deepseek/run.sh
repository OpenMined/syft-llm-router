#!/bin/sh
set -e

uv venv -p 3.9 .venv
uv sync
. .venv/bin/activate

# Check if DEEPSEEK_API_KEY is set
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "Error: DEEPSEEK_API_KEY environment variable is not set"
    echo "Please set it with: export DEEPSEEK_API_KEY=your_api_key_here"
    exit 1
fi

while true; do
    echo "Running 'deepseek' with $(python3 --version) at '$(which python3)'"
    python3 server.py --project-name deepseek --api-key "$DEEPSEEK_API_KEY"

    echo "Sleeping for 10 seconds..."
    sleep 10
done

deactivate 