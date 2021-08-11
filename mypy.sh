#!/usr/bin/env bash

pushd blueprint
bash ./mypy.sh
popd

pushd server
bash ./mypy.sh
popd
