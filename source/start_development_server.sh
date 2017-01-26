#!/usr/bin/env bash
set -e


docker build -t test/nc_data_tools .
docker run --env ENV=DEVELOPMENT -p5000:5000 -v$(pwd)/nc_data_tools:/nc_data_tools test/nc_data_tools
