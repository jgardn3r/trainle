#!/usr/bin/python

from hashlib import sha1
import hmac
import requests
import geojson
import json
import os
import pathlib
from dotenv import load_dotenv

API_BASE_URL = "https://timetableapi.ptv.vic.gov.au"
load_dotenv()


def get_url(request: str) -> str:
    dev_id = os.environ.get("PTV_DEV_ID")
    key_bytes = bytearray(os.environ.get("PTV_API_KEY"), "ascii")
    request = request + ("&" if ("?" in request) else "?") + "devid={0}".format(dev_id)
    raw = bytearray(request, "ascii")
    hashed = hmac.new(key_bytes, raw, sha1)
    signature = hashed.hexdigest()

    return API_BASE_URL + request + "&signature={0}".format(signature.upper())


def get_data(request: str) -> dict:
    response = requests.get(get_url(request))
    return json.loads(response.content)


def find_train_route_type() -> str:
    for route_type in get_data("/v3/route_types")["route_types"]:
        if route_type["route_type_name"] == "Train":
            return str(route_type["route_type"])


def get_route_ids(route_type: str) -> list[str]:
    result = []
    for route in get_data("/v3/routes?route_types={0}".format(route_type))["routes"]:
        result.append(route["route_id"])
    return result


def get_route(route_id: str) -> dict:
    return get_data("/v3/routes/{0}?include_geopath=true".format(route_id))


def get_route_data(route_ids: list[str]) -> list[dict]:
    result = []
    for route_id in route_ids:
        result.append(get_route(route_id))
    return result


def get_route_geojson(route: dict) -> geojson:
    geopaths = route["route"]["geopath"]
    line_strings = []

    for geopath in geopaths:
        for path in geopath["paths"]:
            coordinates = []
            last = None
            for coord in str(path).split(" "):
                coord = float(coord.strip(",").strip())
                if last is None:
                    last = coord
                else:
                    coordinates.append((coord, last))
                    last = None
            line_strings.append(coordinates)
    return geojson.Feature(geometry=geojson.MultiLineString(line_strings), properties={
        "line": route["route"]["route_name"]
    })


# Find route type for trains
train_route_type = find_train_route_type()

route_data = get_route_data(get_route_ids(train_route_type))

track_files = []
track_features = []

for route in route_data:
    src_dir = pathlib.Path(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "../src/")
    )
    route_relative_path = "assets/{0}".format(route["route"]["route_gtfs_id"])
    route_dir = pathlib.Path(os.path.join(src_dir, route_relative_path))
    route_dir.mkdir(exist_ok=True)

    route_geojson = get_route_geojson(route)
    track_features.append(route_geojson)

    # track_file = os.path.join(route_dir, "track.json")
    # with open(track_file, "w") as file:
    #     json.dump(get_route_geojson(route), file, indent=4)
    # track_files.append("./" + route_relative_path + "/track.json")

assets_dir = pathlib.Path(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../src/assets")
)
track_file = os.path.join(assets_dir, "tracks.json")

with open(track_file, "w") as file:
    json.dump(geojson.FeatureCollection(track_features), file, indent=4)
# track_files.append("./" + route_relative_path + "/track.json")

# with open(os.path.join(src_dir, "lines.ts"), "w") as file:
#     for track_file in track_files:
#         file.write(f'import track from "{track_file}"\n')

# for route in route_data:
#     print(route["route_name"])
# print(get_data("/v3/route_types")["route_types"])
