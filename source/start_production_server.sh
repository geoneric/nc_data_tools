#!/usr/bin/env bash
set -e


docker build -t test/nc_data_tools .
docker run -p3031:3031 test/nc_data_tools
