import os
import unittest
from numpy.testing import assert_array_equal
import png
import rasterio
import tempfile
from nc_data_tools.data_tools import \
    convert_graphics_file_to_geotiff, \
    is_name_of_geotiff_file, \
    is_name_of_graphics_file, \
    geotiff_pathname


class DataToolsTest(unittest.TestCase):

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

            convert_graphics_file_to_geotiff(graphics_pathname, raster_pathname)


        with rasterio.open(raster_pathname) as raster_file:

            self.assertEqual(raster_file.bounds.left, 0.0)
            self.assertEqual(raster_file.bounds.bottom, 0.0)
            self.assertEqual(raster_file.bounds.right, 3.0)
            self.assertEqual(raster_file.bounds.top, 2.0)

            profile = raster_file.profile

            self.assertEqual(profile["dtype"], "uint8")
            self.assertEqual(profile["nodata"], None)
            self.assertEqual(profile["count"], 3)

            r, g, b = raster_file.read()

            assert_array_equal(r, [[255,0,0], [128,0,0]])
            assert_array_equal(g, [[0,255,0], [0,128,0]])
            assert_array_equal(b, [[0,0,255], [0,0,128]])

        os.remove(raster_pathname)


if __name__ == "__main__":
    unittest.main()
