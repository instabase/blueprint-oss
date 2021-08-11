#!/usr/bin/env bash

set -e # Exit when any command fails.

export PYTHONPATH="$(pwd)/py"

if [ -n "$1" ]
then
  export STUDIO_PROJECTS_PATH="$1"
else
  echo "Please pass in a path to your projects folder"
  exit -1
fi

python3 -m venv .venv
. .venv/bin/activate
pip3 install -r requirements.txt

# This turns on hot reload for the server.
export FLASK_ENV=development

python3 -m bp_server
