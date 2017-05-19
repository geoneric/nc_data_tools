import os
import unittest
import numpy
from numpy.testing import assert_array_equal
import png
import rasterio
import tempfile
from nc_data_tools.data_tools import *
import test_case


class DataToolsTest(test_case.TestCase):

    def cells(self,
            dtype):

        return numpy.array([
                [-2,  -1],
                [ 0, 999],
                [ 1,   2]
            ], dtype=dtype)


    def create_test_raster(self,
            pathname,
            format="GTiff",
            dtype=numpy.int32,
            crs="EPSG:3857"):

        nr_rows = 3
        nr_cols = 2
        cell_size = 10.0
        west = 0.0
        north = 0.0 + nr_rows * cell_size
        transformation = rasterio.transform.from_origin(
            west, north, cell_size, cell_size)

        profile = {
            "driver": format,
            "width": nr_cols,
            "height": nr_rows,
            "dtype": dtype,
            "count": 1,
            "crs": crs,
            "transform": transformation,
            "nodata": 999
        }

        with rasterio.open(pathname, "w", **profile) as raster:
            raster.write(self.cells(dtype), 1)


    def test_is_name_of_graphics_file(self):
        self.assertTrue(is_name_of_graphics_file("blah.png"))
        self.assertTrue(is_name_of_graphics_file("/blah.png"))
        self.assertTrue(is_name_of_graphics_file("/tmp/blah.png"))

        self.assertFalse(is_name_of_graphics_file(".png"))
        self.assertFalse(is_name_of_graphics_file(""))
        self.assertFalse(is_name_of_graphics_file("png"))
        self.assertFalse(is_name_of_graphics_file("blah"))
        self.assertFalse(is_name_of_graphics_file("blah.dat"))
        self.assertFalse(is_name_of_graphics_file("/blah.dat"))
        self.assertFalse(is_name_of_graphics_file("/tmp/blah.dat"))


    def test_is_name_of_geotiff_file(self):
        self.assertTrue(is_name_of_geotiff_file("blah.tif"))
        self.assertTrue(is_name_of_geotiff_file("/blah.tif"))
        self.assertTrue(is_name_of_geotiff_file("/tmp/blah.tif"))

        self.assertTrue(is_name_of_geotiff_file("blah.tiff"))
        self.assertTrue(is_name_of_geotiff_file("/blah.tiff"))
        self.assertTrue(is_name_of_geotiff_file("/tmp/blah.tiff"))

        self.assertFalse(is_name_of_geotiff_file(".tif"))
        self.assertFalse(is_name_of_geotiff_file("blah.png"))
        self.assertFalse(is_name_of_geotiff_file("/blah.png"))
        self.assertFalse(is_name_of_geotiff_file("/tmp/blah.png"))
        self.assertFalse(is_name_of_geotiff_file("blah"))
        self.assertFalse(is_name_of_geotiff_file("/blah"))
        self.assertFalse(is_name_of_geotiff_file("/tmp/blah"))


    def test_geotiff_pathname(self):
        self.assertEqual(geotiff_pathname("blah.png"), "blah.tif")
        self.assertEqual(geotiff_pathname("/blah.png"), "/blah.tif")
        self.assertEqual(geotiff_pathname("/tmp/blah.png"), "/tmp/blah.tif")


    def test_convert_graphics_file_to_geotiff(self):

        with tempfile.NamedTemporaryFile(suffix=".png") as png_file:
            rgb_cells = [
                # Red, green, blue
                (255,0,0, 0,255,0, 0,0,255),
                # Dark red, dark green, dark blue
                (128,0,0, 0,128,0, 0,0,128)
            ]

            writer = png.Writer(int(len(rgb_cells[0]) / 3), len(rgb_cells))
            writer.write(png_file, rgb_cells)
            png_file.seek(0)

            graphics_pathname = png_file.name
            raster_pathname = geotiff_pathname(graphics_pathname)

            convert_graphics_file_to_geotiff(
                graphics_pathname, raster_pathname)


        with rasterio.open(raster_pathname) as raster_file:

            self.assertEqual(raster_file.bounds.left, 0.0)
            self.assertEqual(raster_file.bounds.bottom, 0.0)
            self.assertEqual(raster_file.bounds.right, 3.0)
            self.assertEqual(raster_file.bounds.top, 2.0)

            profile = raster_file.profile

            self.assertEqual(profile["dtype"], "uint8")
            self.assertEqual(profile["nodata"], None)
            self.assertEqual(profile["count"], 4)

            r, g, b, a = raster_file.read()

            assert_array_equal(r, [[255,0,0], [128,0,0]])
            assert_array_equal(g, [[0,255,0], [0,128,0]])
            assert_array_equal(b, [[0,0,255], [0,0,128]])
            assert_array_equal(a, [[255,255,255], [255,255,255]])

        os.remove(raster_pathname)


    def test_reproject_raster(self):
        # Given a geotiff in EPSG:3857, reproject it in EPSG:28992

        # Create geotiff in EPSG:3857
        source_pathname = "raster-3857.tif"
        dtype = numpy.int32
        source_crs = "EPSG:3857"
        self.create_test_raster(source_pathname, dtype=dtype, crs=source_crs)

        nr_rows = 3
        nr_cols = 2


        # Verify projection
        with rasterio.open(source_pathname) as source_raster:
            self.assertEqual(source_raster.crs,
                rasterio.crs.CRS.from_string(source_crs))


        # Reproject
        target_pathname = "raster-28992.tif"
        target_crs = "EPSG:28992"

        reproject_raster(source_pathname, target_pathname, target_crs)


        # Verify new projection
        with rasterio.open(target_pathname) as target_raster:
            self.assertEqual(
                target_raster.crs,
                rasterio.crs.CRS.from_string(target_crs))
            self.assertEqual(target_raster.width, nr_cols)
            self.assertEqual(target_raster.height, nr_rows)

        os.remove(source_pathname)
        os.remove(target_pathname)


    def test_reformat_geotiff_to_ascii(self):
        # Given a geotiff, reformat it to ascii
        source_pathname = "reformat_raster.tif"
        dtype = numpy.int32
        self.create_test_raster(source_pathname, dtype=dtype)

        # Reformat
        target_pathname = "reformat_raster.asc"

        reformat_raster(source_pathname, target_pathname)


        # Verify format of new raster.
        self.assertTrue(os.path.exists(target_pathname))

        with rasterio.open(target_pathname) as target_raster:

            profile = target_raster.profile
            self.assertEqual(profile["driver"], "AAIGrid")

            data = target_raster.read(1)
            self.assertArraysEqual(self.cells(dtype), data)

        os.remove(source_pathname)
        os.remove(target_pathname)


    def test_reformat_ascii_to_geotiff(self):
        # Given an ascii grid, reformat it to geotiff
        source_pathname = "reformat_raster.asc"
        dtype = numpy.int32
        self.create_test_raster(source_pathname, dtype=dtype)

        # Reformat
        target_pathname = "reformat_raster.tif"
        crs="EPSG:3857"

        reformat_raster(source_pathname, target_pathname,
            override_crs="EPSG:3857")


        # Verify format of new raster.
        self.assertTrue(os.path.exists(target_pathname))

        with rasterio.open(target_pathname) as target_raster:

            profile = target_raster.profile
            self.assertEqual(profile["driver"], "GTiff")

            data = target_raster.read(1)
            self.assertArraysEqual(self.cells(dtype), data)

            self.assertEqual(target_raster.crs,
                rasterio.crs.CRS.from_string(crs))

        os.remove(source_pathname)
        os.remove(target_pathname)


    def test_defined(self):
        pass


if __name__ == "__main__":
    unittest.main()
