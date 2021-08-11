#!/usr/bin/env bash

set -e # Exit when any command fails.

export REPO_PATH="$(pwd)/.."
export BLUEPRINT_PATH="$(pwd)"
export PYTHONPATH="$BLUEPRINT_PATH/py"
export MYPYPATH="$PYTHONPATH"

echo "Checking mypy"
./mypy.sh
echo "Ok mypy"

echo "Checking unit tests"
python3 -m unittest unit_tests/*.py
echo "Ok unit tests"

echo "Checking integration tests"
python3 -m unittest integration_tests/*.py
echo "Ok integration tests"

echo "ALL TESTS PASSED"
