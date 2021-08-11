#!/usr/bin/env bash

set -e # Exit when any command fails.

export REPO_PATH="$(pwd)/.."
export BLUEPRINT_PATH="$REPO_PATH/blueprint"
export SERVER_PATH="$REPO_PATH/server"
export PYTHONPATH="$BLUEPRINT_PATH/py:$SERVER_PATH/py"
export MYPYPATH="$PYTHONPATH"

python3 -m mypy py/bp_server/*.py
