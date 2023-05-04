#!/usr/bin/env bash

set -e
set -x

# Sort imports one per line, so autoflake can remove unused imports
isort --force-single-line-imports .
# Formate app
autoflake --remove-all-unused-imports --remove-unused-variables --exclude=__init__.py --in-place --recursive .
black .
isort .
