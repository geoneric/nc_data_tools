#!/usr/bin/env bash
set -e


if [ "$ENV" = "DEVELOPMENT" ]; then
    exec python server_development.py
elif [ "$ENV" = "TEST" ]; then
    exec python -m unittest discover test *_test.py
else
    exec python server_production.py
fi
