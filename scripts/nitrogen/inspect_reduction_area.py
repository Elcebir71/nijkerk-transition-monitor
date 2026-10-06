"""One-off helper: does the municipality overlap a provincial nitrogen zone layer?

Usage (from the repo root, after fetch_natura2000.py):
    python scripts/nitrogen/inspect_reduction_area.py [layer id]

Default layer id: 141 of the Gelderland map service "Omgevingsverordening", said to
be "Voorbereidingsbesluit - Beperkingengebied stikstofemissie". The script prints
the layer's own name and description, so check there what was really tested. It
also lists every layer of the service with "stikstof" in its name; the zone of the
adopted regulation may be another layer than the one of the preparatory decision.

It reads the layer from the provincial ArcGIS service, only around the
municipality, and compares it with the municipal boundary in this repo:
overlap in hectares and as a share of the municipality, or else the shortest
distance. The download is kept in data/nitrogen/raw/ (not committed). Nothing
else is written.

This is a geometric check on published boundaries. It is not a legal statement
about any address or parcel; for that the province points to its own map.
"""
from __future__ import annotations

import json
import re
import sys

import requests
from shapely.ops import transform, unary_union

import config
from fetch_natura2000 import to_geometry
from fetch_rivm_deposition import WGS84_TO_RD, load_municipality

SERVICE_URL = "https://geoportaal.gelderland.nl/gisserver/rest/services/Omgevingsverordening/Omgevingsverordening/MapServer"
DEFAULT_LAYER_ID = 141
SEARCH_MARGIN_M = 5000      # the layer is only read within this distance of the municipality
PAGE_SIZE = 500
TIMEOUT_S = 300
RD_SRID = 28992


def get_json(url: str, params: dict) -> dict:
    response = requests.get(url, params={"f": "json", **params}, timeout=TIMEOUT_S)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        sys.exit(f"The service returned an error for {url}: {data['error']}")
    return data


def plain(text: str | None) -> str:
    """Layer descriptions can contain HTML."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def list_nitrogen_layers() -> None:
    layers = get_json(SERVICE_URL, {}).get("layers", [])
    found = [layer for layer in layers if "stikstof" in (layer.get("name") or "").lower()]
    print(f"Layers of the service with 'stikstof' in the name ({len(found)} of {len(layers)}):")
    for layer in found:
        print(f"  {layer.get('id'):>4}  {layer.get('name')}")


def fetch_zone(layer_url: str, bounds: tuple[float, float, float, float]) -> list[dict]:
    """All features of the layer that touch the search box, as GeoJSON features in RD coordinates."""
    xmin, ymin, xmax, ymax = bounds
    base = {
        "where": "1=1", "outFields": "*", "f": "geojson", "outSR": RD_SRID,
        "geometry": f"{xmin},{ymin},{xmax},{ymax}", "geometryType": "esriGeometryEnvelope",
        "inSR": RD_SRID, "spatialRel": "esriSpatialRelIntersects", "resultRecordCount": PAGE_SIZE,
    }
    features: list[dict] = []
    while True:
        response = requests.get(layer_url + "/query", params={**base, "resultOffset": len(features)}, timeout=TIMEOUT_S)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            sys.exit(f"The service returned an error: {data['error']}")
        page = data.get("features", [])
        features.extend(page)
        more = data.get("exceededTransferLimit") or (data.get("properties") or {}).get("exceededTransferLimit")
        if not page or not more:
            return features


def to_rd(geometry):
    """The service is asked for RD coordinates; if it answers in degrees anyway, convert."""
    if max(abs(value) for value in geometry.bounds) < 1000:
        return transform(WGS84_TO_RD.transform, geometry)
    return geometry


def main() -> None:
    layer_id = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_LAYER_ID
    layer_url = f"{SERVICE_URL}/{layer_id}"

    list_nitrogen_layers()

    info = get_json(layer_url, {})
    print(f"\nTested layer {layer_id}: {info.get('name')}")
    print(f"  type: {info.get('type')}, geometry: {info.get('geometryType')}")
    print(f"  description: {plain(info.get('description'))[:900] or '(none)'}")
    print(f"  copyright: {plain(info.get('copyrightText')) or '(none)'}")
    total = get_json(layer_url + "/query", {"where": "1=1", "returnCountOnly": "true"}).get("count")
    print(f"  features in the whole layer: {total}")

    municipality = load_municipality()
    search_box = municipality.buffer(SEARCH_MARGIN_M).bounds
    features = fetch_zone(layer_url, search_box)
    print(f"\nFeatures within {SEARCH_MARGIN_M / 1000:g} km of {config.MUNICIPALITY_NAME}: {len(features)}")

    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = config.RAW_DIR / f"gelderland_layer_{layer_id}_near_municipality.geojson"
    raw_path.write_text(json.dumps({"type": "FeatureCollection", "layer": info.get("name"), "features": features}),
                        encoding="utf-8")
    print(f"Saved as data/nitrogen/raw/{raw_path.name}")

    municipality_ha = municipality.area / 10000
    print(f"\n{config.MUNICIPALITY_NAME}: {municipality_ha:,.0f} ha (boundary from this repo)")
    if not features:
        print(f"RESULT: no part of this layer lies within {SEARCH_MARGIN_M / 1000:g} km of the municipality.")
        return

    zone = unary_union([to_rd(to_geometry(feature)) for feature in features if feature.get("geometry")])
    overlap_ha = municipality.intersection(zone).area / 10000
    if overlap_ha > 0.0001:
        print(f"RESULT: OVERLAP. {overlap_ha:,.2f} ha of the municipality lies inside this layer "
              f"({100 * overlap_ha / municipality_ha:.2f}% of the municipality).")
    else:
        distance_m = municipality.distance(zone)
        print(f"RESULT: NO OVERLAP. Shortest distance from the municipal boundary to this layer: {distance_m:,.0f} m.")
    print("Sample attributes of the first feature:")
    for key, value in list((features[0].get("properties") or {}).items())[:12]:
        print(f"  {key}: {str(value)[:120]}")


if __name__ == "__main__":
    main()
