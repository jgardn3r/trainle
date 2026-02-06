#!/bin/python3

import urllib
import zipfile
import tempfile
import geojson
import json
import os.path
from pathlib import Path
import geopandas as gdp
import gtfs_kit as gk

# Transport VIC GTFS schedule
url = "https://opendata.transport.vic.gov.au/dataset/3f4e292e-7f8a-4ffe-831f-1953be0fe448/resource/fb152201-859f-4882-9206-b768060b50ad/download/gtfs.zip"

print("Retrieving gtfs data")
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
        temp_dir = Path(temp_dir)
        with zipfile.ZipFile(gtfs_zip_path) as zip_file:
            zip_file.extractall(temp_dir)

        with zipfile.ZipFile(temp_dir / "2/google_transit.zip") as zip_file:
            zip_file.extractall(gtfs_extract_dir)


print("Reading gtfs feed")
feed = gk.read_feed(gtfs_extract_dir, dist_units="m")
# print(feed.get_routes(as_gdf=True).geometry[-1:].simplify(tolerance=0.00005, preserve_topology=True))
# Filter out the replacement bus routes
# route_ids = [route for route in feed.routes["route_id"] if route[-3:] != "-R:"]


ASSETS_DIR = Path(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../src/assets")
)

# json_str = feed.get_routes(as_gdf=True).geometry[-2:-1].simplify(tolerance=0.0005, preserve_topology=True).to_json()
json_str = feed.get_routes(as_gdf=True).geometry[-2:-1].to_json()

print("Writing JSON")
with open(ASSETS_DIR / "metro_routes.json", "w") as file:
    json.dump(json.loads(json_str), file, indent=4)
    # json.dump(gk.routes.routes_to_geojson(feed, route_short_names=["aus:vic:vic-02-WIL:"]), file, indent=4)


#     print("Files extracted to:", temp_dir)

# Unzip 2 then unzip again to temp folder
# Unzip 2 then unzip again to temp folder

# extract shapes
