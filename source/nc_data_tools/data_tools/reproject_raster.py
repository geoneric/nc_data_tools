import rasterio
import rasterio.warp as warp


def reproject_raster(
        source_raster_pathname,
        target_raster_pathname,
        target_crs,
        resampling_method=warp.RESAMPLING.nearest):

    with rasterio.open(source_raster_pathname) as source_raster:

        affine, width, height = warp.calculate_default_transform(
            source_raster.crs, target_crs,
            source_raster.width, source_raster.height,
            *source_raster.bounds)

        profile = source_raster.meta.copy()
        profile.update({
            "crs": target_crs,
            "transform": affine,
            "width": width,
            "height": height
        })

        with rasterio.open(target_raster_pathname, "w", **profile) as \
                target_raster:

            for b in range(1, source_raster.count + 1):
                warp.reproject(
                    source=rasterio.band(source_raster, b),
                    destination=rasterio.band(target_raster, b),
                    src_transform=source_raster.affine,
                    src_crs=source_raster.crs,
                    dst_transform=affine,
                    dst_crs=target_crs,
                    resampling=resampling_method)
