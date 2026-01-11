#!/usr/bin/python3

from hashlib import sha1
import hmac
import requests
import geojson
import json
import os
import pathlib
from dotenv import load_dotenv
from datetime import date

API_BASE_URL = "https://timetableapi.ptv.vic.gov.au"
load_dotenv()

ASSETS_DIR = pathlib.Path(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../src/assets")
)


def get_ptv_api_data(request: str) -> dict:
    response = requests.get(
        "https://www.ptv.vic.gov.au/lithe" + request,
        headers={"Sec-Fetch-Site": "cross-site"},
    )
    return json.loads(response.content)


def get_timetable_api_url(request: str) -> str:
    dev_id = os.environ.get("PTV_DEV_ID")
    key_bytes = bytearray(os.environ.get("PTV_API_KEY"), "ascii")
    request = request + ("&" if ("?" in request) else "?") + "devid={0}".format(dev_id)
    raw = bytearray(request, "ascii")
    hashed = hmac.new(key_bytes, raw, sha1)
    signature = hashed.hexdigest()

    return API_BASE_URL + request + "&signature={0}".format(signature.upper())


def get_timetable_api_data(request: str) -> dict:
    response = requests.get(get_timetable_api_url(request))
    return json.loads(response.content)


def find_route_type_with_name(name: str) -> str:
    for route_type in get_timetable_api_data("/v3/route_types")["route_types"]:
        if route_type["route_type_name"] == name:
            return str(route_type["route_type"])


def get_route_ids(route_type: str) -> list[str]:
    result = []
    for route in get_timetable_api_data(
        "/v3/routes?route_types={0}".format(route_type)
    )["routes"]:
        result.append(route["route_id"])
    return result


def get_route(route_id: str) -> dict:
    return get_timetable_api_data(
        "/v3/routes/{0}?include_geopath=true".format(route_id)
    )


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

            # There are some extraneous paths in the data
            if len(coordinates) > 2:
                line_strings.append(coordinates)
    return geojson.Feature(
        geometry=geojson.MultiLineString(line_strings),
        properties={"line": route["route"]["route_name"]},
    )


def get_existing_stop_ids(stop_file: str) -> list:
    output = []
    if os.path.exists(stop_file):
        with open(stop_file, "r") as file:
            contents = file.read()
            if contents.strip() == "":
                return output

            existing_data = json.loads(contents)
            for stop in existing_data["features"]:
                if (
                    stop.get("properties", None) is not None
                    and stop["properties"].get("id", None) is not None
                ):
                    output.append(stop)
    return output


def write_routes_geojson(asset_name: str, route_type: int) -> None:
    route_data = get_route_data(get_route_ids(route_type))

    track_features = []

    for route in route_data:
        route_geojson = get_route_geojson(route)
        track_features.append(route_geojson)

    with open(asset_name, "w") as file:
        json.dump(geojson.FeatureCollection(track_features), file, indent=4)


# ==================================================================================================

route_type = find_route_type_with_name("Train")
route_type_prefix = "metro"

write_routes_geojson(
    os.path.join(ASSETS_DIR, f"{route_type_prefix}_routes.json"), route_type
)
