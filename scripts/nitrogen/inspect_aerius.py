"""One-off helper: show what the AERIUS open data service offers around Nijkerk.

Usage (from the repo root):
    python scripts/nitrogen/inspect_aerius.py

Prints, for each layer of interest: the attribute names and types, how many
features lie in the map area, and two sample features. Nothing is written.
The output is used to write fetch_aerius_habitats.py against the real field
names instead of guessed ones.
"""
from __future__ import annotations

import re

import requests

WFS_URL = "https://connect.aerius.nl/opendata/wfs"
# Map area in EPSG:28992: bounding box of Nijkerk plus 15 km.
MAP_BBOX = "140411,449181,186929,490103,urn:ogc:def:crs:EPSG::28992"
LAYERS = [
    "base_geometries:relevant_habitats",
    "base_geometries:hexagons_to_relevant_habitats",
    "base_geometries:extra_assessment_hexagons_to_habitats",
    "base_geometries:hexagons",
    "depositions:depositions",
]
TIMEOUT_S = 180


def get(params: dict) -> requests.Response:
    return requests.get(WFS_URL, params={"service": "WFS", "version": "2.0.0", **params}, timeout=TIMEOUT_S)


def short(value, limit: int = 90):
    text = str(value)
    return text if len(text) <= limit else text[:limit] + "..."


def describe(layer: str) -> None:
    print(f"\n=== {layer} ===")
    try:
        xsd = get({"request": "DescribeFeatureType", "typeNames": layer}).text
        fields = re.findall(r'<xsd?:element[^>]*\bname="([^"]+)"[^>]*\btype="([^"]+)"', xsd)
        print("fields:")
        for name, kind in fields:
            print(f"  {name:38} {kind}")
        if not fields:
            print("  (none found) first 300 characters of the reply:", short(xsd, 300))
    except requests.RequestException as error:
        print("  DescribeFeatureType failed:", error)

    try:
        hits = get({"request": "GetFeature", "typeNames": layer, "bbox": MAP_BBOX, "resultType": "hits"}).text
        matched = re.search(r'numberMatched="([^"]+)"', hits)
        print("features in map area:", matched.group(1) if matched else short(hits, 200))
    except requests.RequestException as error:
        print("  count failed:", error)

    try:
        reply = get({"request": "GetFeature", "typeNames": layer, "bbox": MAP_BBOX,
                     "count": "2", "outputFormat": "application/json"})
        if "json" not in reply.headers.get("Content-Type", ""):
            print("sample: reply is not JSON:", short(reply.text, 300))
            return
        for feature in reply.json().get("features", []):
            geometry = feature.get("geometry") or {}
            print("sample:", geometry.get("type"))
            for key, value in (feature.get("properties") or {}).items():
                print(f"  {key:38} {short(value)}")
    except (requests.RequestException, ValueError) as error:
        print("  sample failed:", error)


def main() -> None:
    for layer in LAYERS:
        describe(layer)


if __name__ == "__main__":
    main()
