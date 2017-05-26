import rasterio
from .driver import driver_by_pathname


def reformat_raster(
        source_raster_pathname,
        target_raster_pathname,
        override_crs=None):

    target_driver = driver_by_pathname(target_raster_pathname)

    with rasterio.open(source_raster_pathname) as source_raster:

        profile = source_raster.profile
        profile["driver"] = target_driver

        if override_crs is not None:
            profile["crs"] = override_crs

        with rasterio.open(target_raster_pathname, "w", **profile) as \
                target_raster:

            target_raster.write(source_raster.read())
