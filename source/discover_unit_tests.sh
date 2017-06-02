#!/usr/bin/env bash
set -e


# -W "ignore::FutureWarning:rasterio"
python \
    -m unittest discover test *_test.py
