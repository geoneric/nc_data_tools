import os.path
import shutil
import shlex
import subprocess
import sys
import rasterio
from geoserver.catalog import Catalog


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
        raster_pathname,
        crs="EPSG:3857"):
    """
    The default coordinate reference system is the same as the one used
    by OpenStreetmap and Google. This will make it possible to overlay
    the raster on a web map.
    """

    # The graphics file contains three bands: RGB.
    with rasterio.open(graphics_pathname) as graphics_file:
        r, g, b = graphics_file.read()

        # The GeoTIFF file will contain the same three bands.
        profile = graphics_file.profile


    # How to map raster cell indices to 'world' coordinates.
    nr_rows = profile["height"]
    nr_cols = profile["width"]
    cell_size = 1.0
    west = 0.0
    north = 0.0 + nr_rows * cell_size
    gdal_transformation = (west, cell_size, 0.0, north, 0.0, -cell_size)
    transformation = rasterio.Affine.from_gdal(*gdal_transformation)


    profile.update(driver="GTiff")
    profile.update(transform=transformation)
    profile.update(crs=crs)

    with rasterio.open(raster_pathname, "w", **profile) as raster_file:
        raster_file.write(r, 1)
        raster_file.write(g, 2)
        raster_file.write(b, 3)


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

    assert os.path.exists(pathname)

    vrt_pathname = "{}.vrt".format(os.path.splitext(pathname)[0])

    assert not os.path.exists(vrt_pathname)

    gcps = " ".join(["-gcp {} {} {} {}".format(
        gcp[0][0], gcp[0][1], gcp[1][0], gcp[1][1]) for gcp in gcps])
    command1 = \
        "gdal_translate -of VRT -a_srs EPSG:3857 {gcps} {input} {output}".format(
            gcps=gcps, input=pathname, output=vrt_pathname)

    execute_command(command1)

    result_pathname = "{}_georeferenced{}".format(
        *os.path.splitext(pathname))

    assert not os.path.exists(result_pathname)

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
