import os.path
import shutil
import tempfile
import numpy
import rasterio
import rasterio.warp as warp
from .driver import driver_by_pathname

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


def reproject_raster_given_template(
        source_raster_pathname,
        template_raster_pathname,
        target_raster_pathname,
        resampling_method=warp.RESAMPLING.nearest,
        source_options={},
        template_options={},
        target_options={}):

    with rasterio.open(source_raster_pathname) as source_raster, \
            rasterio.open(template_raster_pathname) as template_raster:

        source_profile = source_raster.profile

        if "crs" in source_options:
            source_profile["crs"] = source_options["crs"]

        # Base target profile on template profile and selectively adjust
        # properties based on the source profile and the options passed in.
        target_profile = template_raster.meta.copy()
        target_profile["driver"] = driver_by_pathname(target_raster_pathname)
        target_profile["count"] = source_profile["count"]
        target_profile["dtype"] = source_profile["dtype"]
        target_profile["nodata"] = source_profile["nodata"]

        if "crs" in template_options:
            target_profile["crs"] = template_options["crs"]

        with rasterio.open(target_raster_pathname, "w",
                **target_profile) as target_raster:

            for b in range(1, source_raster.count + 1):
                warp.reproject(
                    source=rasterio.band(source_raster, b),
                    destination=rasterio.band(target_raster, b),
                    src_transform=source_profile["transform"],
                    src_crs=source_profile["crs"],
                    dst_transform=target_profile["transform"],
                    dst_crs=target_profile["crs"],
                    resampling=resampling_method)
                    # num_threads=2)


        if target_options.get("clip", False):
            # Create a new raster with the same extent as the source
            # raster.

            # Extent of the source raster in target crs.
            extent = warp.transform_bounds(
                source_raster.crs, target_raster.crs,
                *source_raster.bounds)
            window = target_raster.window(*extent)

            # Move target raster to a temp location and write a clipped version
            # using the name of the target raster.

            with tempfile.TemporaryDirectory() as directory_pathname:
                temp_target_raster_pathname = os.path.join(directory_pathname,
                        os.path.basename(target_raster_pathname))
                shutil.move(target_raster_pathname, temp_target_raster_pathname)

                with rasterio.open(temp_target_raster_pathname) as \
                        target_raster:

                    profile = target_raster.meta.copy()
                    profile.update({
                        "height": window[0][1] - window[0][0],
                        "width": window[1][1] - window[1][0],
                        "transform": target_raster.window_transform(window)
                    })

                    with rasterio.open(
                            target_raster_pathname, "w", **profile) as \
                                clipped_target_raster:
                        clipped_target_raster.write(
                            target_raster.read(window=window))
