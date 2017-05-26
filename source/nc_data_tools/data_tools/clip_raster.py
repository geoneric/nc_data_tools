import rasterio
import rasterio.warp as warp


def clip_raster(
        large_raster_pathname,
        small_raster_pathname,
        clipped_raster_pathname):

    # Cookie-cut large raster with small raster
    with rasterio.open(large_raster_pathname) as large_raster, \
            rasterio.open(small_raster_pathname) as small_raster:

        # It is assumed here that the rasters align which each other
        assert large_raster.crs == small_raster.crs

        # Determine extent in cell indices of small raster in large raster
        extent = small_raster.bounds
        window = large_raster.window(*extent)

        # Adjust the profile of the large raster wrt extent of the small
        # raster
        profile = large_raster.meta.copy()
        profile.update({
            "height": window[0][1] - window[0][0],
            "width": window[1][1] - window[1][0],
            "transform": small_raster.transform,
        })

        with rasterio.open(clipped_raster_pathname, "w", **profile) as \
                clipped_raster:
            clipped_raster.write(large_raster.read(window=window))
