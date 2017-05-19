import os.path


driver_by_extension = {
    ".asc": "AAIGrid",
    ".map": "PCRaster",
    ".tif": "GTiff",
}


def driver_by_pathname(
        pathname):
    return driver_by_extension[os.path.splitext(pathname)[1]]
