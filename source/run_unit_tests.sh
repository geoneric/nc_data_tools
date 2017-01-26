#!/usr/bin/env bash
set -e


docker build -t test/nc_data_tools .
docker run --env ENV=TEST -p5000:5000 test/nc_data_tools
