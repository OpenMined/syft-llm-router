#!/bin/sh
set -e

uv venv -p 3.12 .venv
uv pip install .
. .venv/bin/activate

while true; do
    echo "Running 'inbox' with $(python3 --version) at '$(which python3)'"
    python3 server.py --project-name rag-app

    echo "Sleeping for 10 seconds..."
    sleep 10
done

deactivate
