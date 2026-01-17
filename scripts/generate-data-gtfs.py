#!/bin/python3

import urllib
import zipfile
import tempfile
import geojson
import json
import os.path
from pathlib import Path
import shutil
import gtfs_kit as gk

# Transport VIC GTFS schedule
url = "https://opendata.transport.vic.gov.au/dataset/3f4e292e-7f8a-4ffe-831f-1953be0fe448/resource/fb152201-859f-4882-9206-b768060b50ad/download/gtfs.zip"

gtfs_zip_path = Path("/tmp/gtfs.zip")
if not gtfs_zip_path.exists():
    # TODO: Ensure repeatable script execution by deleting stuff
    print(f"Downloading GTFS data to {gtfs_zip_path}")
    urllib.request.urlretrieve(url, gtfs_zip_path)


gtfs_extract_dir = Path("/tmp/gtfs-metro-extract")
if not gtfs_extract_dir.exists():
    # TODO: Ensure repeatable script execution by deleting stuff
    # shutil.rmtree(gtfs_extract_dir)
    # gtfs_extract_dir.mkdir(parents=True)


    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(gtfs_zip_path, "r") as zip_file:
            zip_file.extractall(temp_dir)

        with zipfile.ZipFile(temp_dir / "2/google_transit.zip", "r") as zip_file:
            zip_file.extractall(gtfs_extract_dir)

print(gk.list_feed(gtfs_extract_dir))
feed = gk.read_feed(gtfs_extract_dir, dist_units="m")
print(gk.shapes.get_shapes(feed))

ASSETS_DIR = Path(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../src/assets")
)


# with open(ASSETS_DIR / "tracks.json", "w") as file:
#     json.dump(gk.shapes.shapes_to_geojson(feed), file, indent=4)


#     print("Files extracted to:", temp_dir)

# Unzip 2 then unzip again to temp folder

# extract shapes
