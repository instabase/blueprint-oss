#!/usr/bin/env bash

set -e # Exit when any command fails.

export REPO_PATH="$(pwd)/.."
export BLUEPRINT_PATH="$(pwd)"
export PYTHONPATH="$BLUEPRINT_PATH/py"
export MYPYPATH="$PYTHONPATH"

python3 -m mypy -m bp
python3 -m mypy py/bp/rules/*.py
python3 -m mypy reference_extractions/paystubs/*.py
python3 -m mypy reference_extractions/checks/*.py
python3 -m mypy reference_extractions/bill_of_lading/*.py
python3 -m mypy unit_tests/*.py
python3 -m mypy integration_tests/*.py
python3 -m mypy py/bp/cli/*.py
