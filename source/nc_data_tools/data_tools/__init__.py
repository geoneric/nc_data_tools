import os.path
import shutil
import shlex
import subprocess
import sys
import numpy
import rasterio
from geoserver.catalog import Catalog
from . clip_raster import *
from . reformat_raster import *
from . reproject_raster import *
from . subtract_raster import *


def is_name_of_graphics_file(
        pathname):

    return os.path.splitext(pathname)[1] in [".png"]


def is_name_of_geotiff_file(
        pathname):

    return os.path.splitext(pathname)[1] in [".tif", ".tiff"]


def geotiff_pathname(
        pathname):

    return "{}.tif".format(os.path.splitext(pathname)[0])


def convert_graphics_file_to_geotiff(
        graphics_pathname,
        geotiff_pathname,
        crs="EPSG:3857"):
    """
    The default coordinate reference system is the same as the one used
    by OpenStreetmap and Google.

    An alpha band is added to the result to mark no-data values.
    """
    # The graphics file contains three or four bands: RGB or RGBA.
    # The geotiff file will contain four bands: RGBA.
    with rasterio.open(graphics_pathname) as graphics_file:
        if graphics_file.count == 3:
            r, g, b = graphics_file.read()
            a = numpy.copy(r)
            a[...] = 255
        else:
            r, g, b, a = graphics_file.read()

        # The GeoTIFF file will contain the same bands.
        profile = graphics_file.profile


    # How to map raster cell indices to 'world' coordinates.
    # This will position the raster on the equator.
    nr_rows = profile["height"]
    nr_cols = profile["width"]
    cell_size = 1.0
    west = 0.0
    north = 0.0 + nr_rows * cell_size
    # gdal_transformation = (west, cell_size, 0.0, north, 0.0, -cell_size)
    # transformation = rasterio.Affine.from_gdal(*gdal_transformation)
    transformation = rasterio.transform.from_origin(
        west, north, cell_size, cell_size)

    profile.update(driver="GTiff")
    profile.update(count=4)
    profile.update(transform=transformation)
    profile.update(crs=crs)

    with rasterio.open(geotiff_pathname, "w", **profile) as geotiff_file:
        geotiff_file.write(r, 1)
        geotiff_file.write(g, 2)
        geotiff_file.write(b, 3)
        geotiff_file.write(a, 4)


def workspace_exists(
        catalog,
        workspace_name):

    return any([workspace_name == workspace.name for workspace in
        catalog.get_workspaces()])


def create_workspace(
        catalog,
        workspace_name):
    # namespace_uri = "http://nc_assessment/{}".format(workspace_name)
    catalog.create_workspace(workspace_name)  # , namespace_uri)


def delete_store(
        catalog,
        workspace,
        store_name):

    catalog.delete(
        catalog.get_store(store_name, workspace), purge=True, recurse=True)
    catalog.reload()


def delete_workspace(
        catalog,
        workspace_name):

    assert workspace_exists(catalog, workspace_name)
    catalog.delete(
        catalog.get_workspace(workspace_name), purge=True, recurse=True)
    catalog.reload()
    assert not workspace_exists(catalog, workspace_name)



def register_raster(
        pathname,
        workspace_name,
        geoserver_uri,
        geoserver_user,
        geoserver_password):
    """
    Register raster with Geoserver

    The result of registering a raster is a WMS end-point for visualizing it.
    In case pathname points to a graphics file, it is converted to a raster
    first (GeoTIFF).
    """

    if not os.path.exists(pathname):
        raise RuntimeError("file {} does not exist".format(pathname))


    # Translate graphics file into a GeoTIFF if necessary.
    if is_name_of_geotiff_file(pathname):
        raster_pathname = pathname
    else:
        raster_pathname = geotiff_pathname(pathname)
        convert_graphics_file_to_geotiff(pathname, raster_pathname)

    assert os.path.exists(raster_pathname)


    # Register raster with Geoserver.
    catalog = Catalog(geoserver_uri, geoserver_user, geoserver_password)

    if not workspace_exists(catalog, workspace_name):
        create_workspace(catalog, workspace_name)

    workspace = catalog.get_workspace(workspace_name)
    coverage_name = os.path.splitext(os.path.basename(raster_pathname))[0]

    catalog.create_coveragestore_external_geotiff(coverage_name,
        "file://{}".format(raster_pathname), workspace)

    layer_name = "{}:{}".format(workspace_name, coverage_name)

    return layer_name


def execute_command(
        command):
    try:

        command = shlex.split(command)

        subprocess.run(command, shell=False, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    except subprocess.CalledProcessError as exception:

        sys.stderr.write("{}\n".format(exception))
        sys.stderr.write("{}\n".format(exception.stderr))
        sys.stderr.flush()

        raise


def georeference_raster(
        pathname,
        gcps,
        geoserver_uri,
        geoserver_user,
        geoserver_password,
        workspace_name,
        layer_name):
    """
    Georeference a raster
    """

    assert os.path.exists(pathname), pathname

    with rasterio.open(pathname) as raster_dataset:
        top = raster_dataset.bounds.top

        for point_pair in gcps:
            point_pair[0][1] = top - point_pair[0][1]

    vrt_pathname = "{}.vrt".format(os.path.splitext(pathname)[0])

    assert not os.path.exists(vrt_pathname), vrt_pathname

    gcps = " ".join(["-gcp {} {} {} {}".format(
        gcp[0][0], gcp[0][1], gcp[1][0], gcp[1][1]) for gcp in gcps])
    command1 = \
        "gdal_translate -of VRT -a_srs EPSG:3857 {gcps} {input} {output}".format(
            gcps=gcps, input=pathname, output=vrt_pathname)

    execute_command(command1)

    result_pathname = "{}_georeferenced{}".format(
        *os.path.splitext(pathname))

    assert not os.path.exists(result_pathname), result_pathname

    command2 = \
        "gdalwarp -s_srs EPSG:3857 -t_srs EPSG:3857 {input} {output}".format(
            input=vrt_pathname, output=result_pathname)

    execute_command(command2)

    shutil.move(result_pathname, pathname)
    os.remove(vrt_pathname)

    assert os.path.exists(pathname)
    assert not os.path.exists(vrt_pathname)
    assert not os.path.exists(result_pathname)


    # Recreate the coverage store to simulate refresh of the WMS layer.
    catalog = Catalog(geoserver_uri, geoserver_user, geoserver_password)
    workspace = catalog.get_workspace(workspace_name)
    coverage_name = os.path.splitext(os.path.basename(pathname))[0]

    delete_store(catalog, workspace, coverage_name)
    catalog.create_coveragestore_external_geotiff(coverage_name,
        "file://{}".format(pathname), workspace)


def retrieve_colors(
        pathname):
    """
    Return list of unique colors present in RGB raster pointed to by
    *pathname*
    """

    assert os.path.exists(pathname)

    with rasterio.open(pathname) as raster:
        nr_rows = raster.height
        nr_cols = raster.width
        red_band, green_band, blue_band, _ = raster.read()

    assert red_band.dtype == numpy.uint8
    assert green_band.dtype == numpy.uint8
    assert blue_band.dtype == numpy.uint8

    colors = set()

    for row in range(nr_rows):
        for r, g, b in zip(red_band[row], green_band[row], blue_band[row]):
            colors.add((int(r), int(g), int(b)))

    return list(colors)




def _classify_raster(
        raster_pathname,
        lut,
        classified_raster_pathname):

    # The raster contains four bands: RGBA.
    with rasterio.open(raster_pathname) as raster_dataset:

        profile = raster_dataset.profile
        assert profile["count"] == 4

        r, g, b, _ = raster_dataset.read()
        mask = raster_dataset.dataset_mask()

        dtype = numpy.int32
        profile.update(count=1)
        profile.update(dtype=dtype)

        classes = numpy.asarray(r, dtype=dtype)
        assert classes is not r  # Must be a copy

        nr_rows = len(classes)
        nr_cols = len(classes[0])
        nodata = -999


        for row in range(nr_rows):
            for col in range(nr_cols):
                if mask[row][col] == 0:
                    classes[row][col] = nodata
                else:
                    color = (r[row][col], g[row][col], b[row][col])

                    if color in lut:
                        classes[row][col] = lut[color]
                    else:
                        # No class associated with this color. Mask it out.
                        classes[row][col] = nodata


        with rasterio.open(classified_raster_pathname, "w", **profile) as \
                classified_raster_dataset:
            classified_raster_dataset.nodata = nodata
            classified_raster_dataset.write(classes, 1)


def classify_raster(
        pathname,
        lut,
        geoserver_uri,
        geoserver_user,
        geoserver_password,
        workspace_name):
        # layer_name):
    """
    Classify a raster
    """

    assert os.path.exists(pathname), pathname

    result_pathname = "{}_classified{}".format(
        *os.path.splitext(pathname))

    _classify_raster(pathname, lut, result_pathname)

    assert os.path.exists(pathname)
    assert os.path.exists(result_pathname)


    # Recreate the coverage store to simulate refresh of the WMS layer.
    catalog = Catalog(geoserver_uri, geoserver_user, geoserver_password)
    workspace = catalog.get_workspace(workspace_name)
    coverage_name = os.path.splitext(os.path.basename(pathname))[0]

    delete_store(catalog, workspace, coverage_name)
    catalog.create_coveragestore_external_geotiff(coverage_name,
        "file://{}".format(result_pathname), workspace)

    return result_pathname




# def reclassify_raster(
#         raster_pathname,
#         lut,
#         classified_raster_pathname):
# 
#     # The raster contains four bands: RGBA.
#     with rasterio.open(raster_pathname) as raster_dataset:
# 
#         profile = raster_dataset.profile
#         assert profile["count"] == 4
# 
#         r, g, b, _ = raster_dataset.read()
#         mask = raster_dataset.dataset_mask()
# 
#         dtype = numpy.int32
#         profile.update(count=1)
#         profile.update(dtype=dtype)
# 
#         classes = numpy.asarray(r, dtype=dtype)
#         assert classes is not r  # Must be a copy
# 
#         nr_rows = len(classes)
#         nr_cols = len(classes[0])
# 
#         for row in range(nr_rows):
#             for col in range(nr_cols):
#                 if mask[row][col] != 0:
#                     color = (r[row][col], g[row][col], b[row][col])
# 
#                     if color in lut:
#                         classes[row][col] = lut[color]
#                     else:
#                         # No class associated with this color. Mask it out.
#                         mask[row][col] = 0
# 
#         with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # , INTERNAL_MASK_FLAGS_1=2):
#             with rasterio.open(classified_raster_pathname, "w", **profile) as \
#                     classified_raster_dataset:
#                 classified_raster_dataset.write(classes, 1)
#                 classified_raster_dataset.write_mask(mask)
