#!/usr/bin/env bash

pushd blueprint
bash ./mypy.sh
bash ./tests.sh
popd

pushd server
bash ./mypy.sh
popd
