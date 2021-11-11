#!/usr/bin/env bash

set -e # Exit when any command fails.

export PYTHONPATH="$(pwd)/py"

python3 -m venv .venv
. .venv/bin/activate
pip3 install -r requirements.txt

# This turns on hot reload for the server.
export FLASK_ENV=development

python3 -m bp_server
