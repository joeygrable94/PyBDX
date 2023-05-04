#!/usr/bin/env bash

set -e
set -x

mypy .
black --check .
isort --check-only .
flake8 .
