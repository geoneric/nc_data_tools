import numpy
import rasterio


def subtract_raster(
        lhs_raster_pathname,
        rhs_raster_pathname,
        target_raster_pathname):

    with rasterio.open(lhs_raster_pathname) as lhs_raster, \
            rasterio.open(rhs_raster_pathname) as rhs_raster:

        lhs_profile = lhs_raster.profile
        rhs_profile = rhs_raster.profile

        lhs_nodata_value = lhs_profile["nodata"]
        rhs_nodata_value = rhs_profile["nodata"]

        profile = lhs_raster.meta.copy()
        nodata_value = profile["nodata"]

        with rasterio.open(target_raster_pathname, "w", **profile) as \
                target_raster:

            lhs = lhs_raster.read()
            rhs = rhs_raster.read()

            assert lhs.shape == rhs.shape

            result = lhs - rhs
            result[
                numpy.logical_or(
                    lhs == lhs_nodata_value, rhs == rhs_nodata_value)] = \
                nodata_value

            target_raster.write(result)
