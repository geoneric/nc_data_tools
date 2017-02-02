import os.path
import sys
import rasterio
import requests
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


    # payload = {
    #     "timestamp": timestamp,
    #     "priority": priority,
    #     "severity": severity,
    #     "message": message
    # }

    # response = requests.post(uri, json={"log": payload})

    # if response.status_code != 201:
    #     raise RuntimeError(response.json()["message"])
