#!/usr/bin/env python
import os.path
import sys
import docopt
import rasterio
import rasterio.warp as warp
from data_tools import reproject_raster_given_template


doc_string = """\
Reproject a raster

usage:
    {command} [--s_crs=<epsg>] [--t_crs=<epsg>] [--clip] <source> <template>
        <target> (average|nearest)
    {command} (-h | --help)

arguments:
    source      Name of raster to reproject
    template    Name of raster to read target projection properties from
    target      Name of raster to create
    nearest     Use nearest neighboorhood resampling method

options:
    -h --help   Show this screen
    --s_crs=<epsg>  CRS of source raster
    --t_crs=<epsg>  CRS of template raster
    --clip          Clip the result to the window of the source raster

A new raster will be created with the same projection properties as the
template raster. The cell values will be read from the source raster.

Only pass coordinate reference systems in case these cannot be obtained
from the source and template rasters themselves.
"""


if __name__ == "__main__":
    arguments = docopt.docopt(doc_string)

    source_raster_pathname = arguments["<source>"]
    template_raster_pathname = arguments["<template>"]
    target_raster_pathname = arguments["<target>"]

    source_options = {}
    template_options = {}
    target_options = {}

    if arguments["--s_crs"] is not None:
        source_options["crs"] = rasterio.crs.CRS.from_epsg(
            arguments["--s_crs"])

    if arguments["--t_crs"] is not None:
        template_options["crs"] = rasterio.crs.CRS.from_epsg(
            arguments["--t_crs"])

    target_options["clip"] = arguments["--clip"]

    if arguments["nearest"]:
        method = warp.RESAMPLING.nearest
    elif arguments["average"]:
        method = warp.RESAMPLING.average

    reproject_raster_given_template(
        source_raster_pathname, template_raster_pathname,
        target_raster_pathname, resampling_method=method,
        source_options=source_options, template_options=template_options,
        target_options=target_options)
