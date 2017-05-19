import os.path
import rasterio


def reformat_raster(
        source_raster_pathname,
        target_raster_pathname,
        override_crs=None):

    driver_by_extension = {
        ".tif": "GTiff",
        ".asc": "AAIGrid"
    }

    target_driver = driver_by_extension[
        os.path.splitext(target_raster_pathname)[1]]

    with rasterio.open(source_raster_pathname) as source_raster:

        profile = source_raster.profile
        profile["driver"] = target_driver

        if override_crs is not None:
            profile["crs"] = override_crs

        with rasterio.open(target_raster_pathname, "w", **profile) as \
                target_raster:

            target_raster.write(source_raster.read())
