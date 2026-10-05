"""Fetch the Nijkerk boundary and the Natura 2000 areas around it from PDOK.

Usage (from the repo root):
    pip install requests shapely pyproj
    python scripts/nitrogen/fetch_natura2000.py

Writes to data/nitrogen/processed/:
    municipality_boundary.geojson
    natura2000_nearby.geojson

This script only reports boundaries, distance and overlap. It does NOT say
whether an area is nitrogen-sensitive: that is not in this dataset.
"""
from __future__ import annotations

import json
import sys
from datetime import date

import requests
from pyproj import Transformer
from shapely import make_valid
from shapely.geometry import MultiPolygon, box, mapping, shape
from shapely.ops import transform

import config

TIMEOUT_S = 60
SIMPLIFY_TOLERANCE_M = 20
# Areas are cut off a little outside the map area, so the cut never shows as a line on the map.
CLIP_MARGIN_M = 2500
RD_TO_WGS84 = Transformer.from_crs("EPSG:28992", "EPSG:4326", always_xy=True)


def wfs_features(base_url: str, layer: str, bbox: tuple[float, float, float, float]) -> list[dict]:
    """Return all features of a layer that intersect a bounding box (EPSG:28992)."""
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": layer,
        "outputFormat": "application/json",
        "bbox": ",".join(str(round(v)) for v in bbox),
    }
    response = requests.get(base_url, params=params, timeout=TIMEOUT_S)
    response.raise_for_status()
    return response.json().get("features", [])


def to_geometry(feature: dict):
    geometry = shape(feature["geometry"])
    return geometry if geometry.is_valid else make_valid(geometry)


def round_coordinates(value, digits: int = 5):
    if isinstance(value, (list, tuple)):
        return [round_coordinates(v, digits) for v in value]
    return round(value, digits)


def polygons_only(geometry) -> MultiPolygon:
    """Drop stray points and lines that repairing or clipping can leave behind."""
    parts = []
    for part in getattr(geometry, "geoms", [geometry]):
        if part.geom_type == "Polygon":
            parts.append(part)
        elif part.geom_type in ("MultiPolygon", "GeometryCollection"):
            parts.extend(polygons_only(part).geoms)
    return MultiPolygon(parts)


def to_wgs84_geojson(geometry) -> dict:
    """Simplify in metres, reproject to WGS84 and round to about 1 m."""
    simplified = polygons_only(geometry.simplify(SIMPLIFY_TOLERANCE_M, preserve_topology=True))
    geojson = mapping(transform(RD_TO_WGS84.transform, simplified))
    return {"type": geojson["type"], "coordinates": round_coordinates(geojson["coordinates"])}


def find_municipality(features: list[dict]):
    for feature in features:
        if feature["properties"].get("code") == config.PDOK_MUNICIPALITY_CODE:
            return to_geometry(feature)
    found = sorted(f["properties"].get("naam", "?") for f in features)
    sys.exit(f"Municipality code {config.PDOK_MUNICIPALITY_CODE} not found. PDOK returned: {found}")


def describe_areas(features: list[dict], municipality, map_area) -> list[dict]:
    """Keep areas that intersect the map area and add distance and overlap."""
    clip_area = map_area.buffer(CLIP_MARGIN_M)
    areas = []
    for feature in features:
        geometry = to_geometry(feature)
        if not geometry.intersects(map_area):
            continue
        distance_m = municipality.distance(geometry)
        props = feature["properties"]
        code = props.get("beschermin")
        areas.append({
            "type": "Feature",
            "properties": {
                "name": props.get("naamN2K"),
                "site_nr": props.get("nr"),
                "protection_code": code,
                "protection_label_nl": config.NATURA2000_PROTECTION_LABELS.get(code, code),
                "status": props.get("status"),
                "distance_to_municipality_km": round(distance_m / 1000, 1),
                "overlap_with_municipality_ha": round(municipality.intersection(geometry).area / 10000, 1),
                "area_total_ha": round(geometry.area / 10000),
                "geometry_clipped_to_map_area": True,
                "nitrogen_sensitive": None,
            },
            # Only the part in and just around the map area is kept, to limit file size.
            "geometry": to_wgs84_geojson(geometry.intersection(clip_area)),
        })
    return sorted(areas, key=lambda a: (a["properties"]["distance_to_municipality_km"], a["properties"]["name"] or ""))


def source_block(dataset: str, publisher: str, url: str, layer: str, licence: str) -> dict:
    return {"dataset": dataset, "publisher": publisher, "url": url, "layer": layer,
            "licence": licence, "fetched_on": date.today().isoformat()}


def write_geojson(name: str, source: dict, notes: list[str], features: list[dict]) -> None:
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    target = config.PROCESSED_DIR / name
    collection = {"type": "FeatureCollection", "source": source, "notes": notes, "features": features}
    target.write_text(json.dumps(collection, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {target.relative_to(config.REPO_ROOT)} ({target.stat().st_size / 1024:.0f} kB)")


def main() -> None:
    municipality = find_municipality(
        wfs_features(config.PDOK_MUNICIPALITY_WFS, config.PDOK_MUNICIPALITY_LAYER, config.MUNICIPALITY_SEED_BBOX)
    )
    radius_m = config.SURROUNDINGS_RADIUS_M
    # Same rectangle as the deposition map: the municipality plus the radius, as a bounding box.
    map_area = box(*municipality.buffer(radius_m).bounds)
    areas = describe_areas(
        wfs_features(config.PDOK_NATURA2000_WFS, config.PDOK_NATURA2000_LAYER, map_area.bounds),
        municipality, map_area,
    )
    if not areas:
        sys.exit("No Natura 2000 areas found. Check the radius and the PDOK service.")

    write_geojson(
        "municipality_boundary.geojson",
        source_block("Bestuurlijke Gebieden", "Kadaster via PDOK", config.PDOK_MUNICIPALITY_WFS,
                     config.PDOK_MUNICIPALITY_LAYER, "See PDOK metadata (not checked yet)"),
        [f"Boundary simplified to {SIMPLIFY_TOLERANCE_M} m for display."],
        [{"type": "Feature",
          "properties": {"name": config.MUNICIPALITY_NAME, "code": config.MUNICIPALITY_KEY,
                         "area_ha": round(municipality.area / 10000)},
          "geometry": to_wgs84_geojson(municipality)}],
    )
    write_geojson(
        "natura2000_nearby.geojson",
        source_block("Natura 2000", "RVO via PDOK", config.PDOK_NATURA2000_WFS,
                     config.PDOK_NATURA2000_LAYER, "CC0"),
        [f"Areas that intersect the map area: the bounding box of {config.MUNICIPALITY_NAME} plus {radius_m / 1000:.0f} km.",
         "Geometries are cut off just outside that map area; area_total_ha refers to the whole area.",
         "nitrogen_sensitive is empty on purpose: this dataset does not contain that information.",
         "One Natura 2000 area can appear as more than one feature."],
        areas,
    )

    print(f"\n{config.MUNICIPALITY_NAME}: {municipality.area / 10000:.0f} ha")
    print(f"{'Area':38} {'Type':6} {'Dist km':>8} {'Overlap ha':>11} {'Total ha':>9}")
    for area in areas:
        p = area["properties"]
        print(f"{(p['name'] or '?')[:38]:38} {str(p['protection_code'])[:6]:6} "
              f"{p['distance_to_municipality_km']:8.1f} {p['overlap_with_municipality_ha']:11.1f} {p['area_total_ha']:9}")


if __name__ == "__main__":
    main()
