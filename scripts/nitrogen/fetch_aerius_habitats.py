"""Fetch the nitrogen-sensitive habitat types around Nijkerk from AERIUS open data.

Usage (from the repo root, after fetch_natura2000.py):
    python scripts/nitrogen/fetch_aerius_habitats.py

Writes data/nitrogen/processed/nitrogen_sensitive_habitats.geojson

What this layer adds: which Natura 2000 areas in the map area contain habitat
types that AERIUS marks as relevant (nitrogen-sensitive), and their critical
deposition value (KDW). What it does NOT do: compare the KDW with the RIVM
deposition map, or say anything about individual locations or permits.
"""
from __future__ import annotations

import json
import sys
from datetime import date

import requests
from shapely.geometry import MultiPolygon, Polygon, box
from shapely.ops import unary_union

import config
from fetch_natura2000 import polygons_only, to_geometry, to_wgs84_geojson
from fetch_rivm_deposition import load_municipality

TIMEOUT_S = 600
CLIP_MARGIN_M = 2500        # cut shapes a little outside the map area, so the cut is never visible
# The drawn shape is made much lighter than the source (which has tens of thousands of
# small holes). This only affects the picture; all areas in the table use the full data.
DRAW_SIMPLIFY_M = 100
DRAW_MIN_PART_M2 = 10000    # parts smaller than 1 ha are not drawn
DRAW_MIN_HOLE_M2 = 20000    # holes smaller than 2 ha are filled in the drawing
RAW_FILE = "aerius_relevant_habitats.json"


def fetch_relevant_habitats(bounds: tuple[float, float, float, float]) -> tuple[list[dict], str]:
    """Return the features and the date they were downloaded. The download is kept in data/nitrogen/raw."""
    raw_path = config.RAW_DIR / RAW_FILE
    if raw_path.exists():
        print(f"Using the download saved earlier ({raw_path.name}). Delete that file to download again.")
        features = json.loads(raw_path.read_text(encoding="utf-8")).get("features", [])
        return features, date.fromtimestamp(raw_path.stat().st_mtime).isoformat()

    crs = "urn:ogc:def:crs:EPSG::28992"
    params = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": config.AERIUS_HABITAT_LAYER,
        "outputFormat": "application/json", "srsName": crs,
        "bbox": ",".join(str(round(v)) for v in bounds) + "," + crs,
    }
    print("Downloading relevant habitat types from AERIUS (this can take a few minutes)...")
    response = requests.get(config.AERIUS_WFS, params=params, timeout=TIMEOUT_S)
    response.raise_for_status()
    if "json" not in response.headers.get("Content-Type", ""):
        sys.exit("AERIUS did not return JSON: " + response.text[:300])
    data = response.json()
    features = data.get("features", [])
    print(f"  received {len(features)} features, {len(response.content) / 1e6:.1f} MB")
    matched = data.get("numberMatched")
    if isinstance(matched, int) and matched > len(features):
        sys.exit(f"AERIUS returned {len(features)} of {matched} features. Paging is needed; tell the script author.")
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(response.content)
    return features, date.today().isoformat()


def drawing_shape(merged):
    """A lighter version of the merged habitat shape, for the map only."""
    parts = []
    for part in merged.geoms:
        if part.area < DRAW_MIN_PART_M2:
            continue
        holes = [ring for ring in part.interiors if Polygon(ring).area >= DRAW_MIN_HOLE_M2]
        parts.append(Polygon(part.exterior, holes))
    return polygons_only(MultiPolygon(parts).simplify(DRAW_SIMPLIFY_M))


def area_ha(geometry) -> float:
    return polygons_only(geometry).area / 10000


def main() -> None:
    municipality = load_municipality()
    map_area = box(*municipality.buffer(config.SURROUNDINGS_RADIUS_M).bounds)
    clip_area = map_area.buffer(CLIP_MARGIN_M)

    habitat_types: dict[tuple[str, str], dict] = {}
    parts_per_area: dict[str, list] = {}
    # Audit trail: every Natura 2000 area the service returned, and how many of its
    # records really lie in the map area. Shows that no area was skipped by name.
    reply: dict[str, dict] = {}
    source_features, fetched_on = fetch_relevant_habitats(map_area.bounds)
    for feature in source_features:
        counts = reply.setdefault(feature["properties"].get("natura2000_area_name"),
                                  {"records_returned": 0, "records_in_map_area": 0, "mapped_ha_in_municipality": 0.0})
        counts["records_returned"] += 1
        geometry = to_geometry(feature)
        if max(geometry.bounds) < 1000:
            sys.exit("Unexpected coordinates from AERIUS (not in metres). Stop.")
        in_map_ha = area_ha(geometry.intersection(map_area)) if geometry.intersects(map_area) else 0.0
        if in_map_ha < 0.0001:
            continue  # the service selects on the bounding box; this one lies outside the map area
        props = feature["properties"]
        area_name, code = props.get("natura2000_area_name"), props.get("habitat_type_name")
        coverage = props.get("coverage")
        entry = habitat_types.setdefault((area_name, code), {
            "natura2000_area": area_name,
            "habitat_code": code,
            "habitat_description": props.get("habitat_type_description"),
            "kdw_mol_per_ha": props.get("critical_deposition"),
            "mapped_ha_in_map_area": 0.0,
            "coverage_weighted_ha_in_map_area": 0.0,
            "mapped_ha_in_municipality": 0.0,
        })
        entry["mapped_ha_in_map_area"] += in_map_ha
        entry["coverage_weighted_ha_in_map_area"] += in_map_ha * (1.0 if coverage is None else coverage)
        in_municipality_ha = area_ha(geometry.intersection(municipality))
        entry["mapped_ha_in_municipality"] += in_municipality_ha
        counts["records_in_map_area"] += 1
        counts["mapped_ha_in_municipality"] += in_municipality_ha
        parts_per_area.setdefault(area_name, []).append(polygons_only(geometry.intersection(clip_area)))

    if not habitat_types:
        sys.exit("No relevant habitat types found in the map area. Check the AERIUS service.")

    rows = sorted(habitat_types.values(),
                  key=lambda r: (r["natura2000_area"] or "", r["kdw_mol_per_ha"] or 0, r["habitat_code"] or ""))
    for row in rows:
        for key in ("mapped_ha_in_map_area", "coverage_weighted_ha_in_map_area", "mapped_ha_in_municipality"):
            row[key] = round(row[key], 1)

    features = []
    for area_name, parts in sorted(parts_per_area.items(), key=lambda item: item[0] or ""):
        merged = polygons_only(unary_union(parts))
        own_rows = [r for r in rows if r["natura2000_area"] == area_name]
        kdws = [r["kdw_mol_per_ha"] for r in own_rows if r["kdw_mol_per_ha"] is not None]
        features.append({
            "type": "Feature",
            "properties": {
                "natura2000_area": area_name,
                "habitat_types": len(own_rows),
                "lowest_kdw_mol_per_ha": min(kdws) if kdws else None,
                "mapped_ha_in_map_area": round(area_ha(merged.intersection(map_area)), 1),
                "mapped_ha_in_municipality": round(area_ha(merged.intersection(municipality)), 1),
                "distance_to_municipality_km": round(municipality.distance(merged) / 1000, 1),
            },
            "geometry": to_wgs84_geojson(drawing_shape(merged)),
        })

    collection = {
        "type": "FeatureCollection",
        "source": {
            "publisher": "RIVM, AERIUS open data",
            "dataset": "AERIUS relevante habitatkartering",
            "description_nl": "De stikstofgevoelige habitattypen binnen een Natura 2000-gebied die ook daadwerkelijk relevant zijn bevonden voor AERIUS",
            "record": config.AERIUS_HABITAT_RECORD,
            "layer": config.AERIUS_HABITAT_LAYER,
            "url": config.AERIUS_WFS,
            "info": config.AERIUS_PRODUCT_PAGE,
            "version": "As served on the fetch date. The register record describes the AERIUS 2025 release (published 2025-10-07).",
            "licence": "Public domain (Creative Commons Public Domain Mark 1.0), no restrictions, per the Nationaal Georegister record",
            "fetched_on": fetched_on,
        },
        "notes": [
            "Habitat types are the ones AERIUS marks as relevant (nitrogen-sensitive) for a location.",
            "kdw_mol_per_ha is the critical deposition value (kritische depositiewaarde) as given by AERIUS, in mol N per ha per year.",
            "No comparison is made here between the KDW and the RIVM deposition map.",
            "mapped_ha is the area of the mapped polygons; coverage_weighted_ha multiplies the mapped area of a habitat type by the one coverage AERIUS gives for that type in the whole Natura 2000 area, so for a part of the area it is an approximation.",
            f"Map area: the bounding box of {config.MUNICIPALITY_NAME} plus {config.SURROUNDINGS_RADIUS_M / 1000:.0f} km. Areas are computed on the unsimplified data.",
            f"Drawn shapes: all relevant habitat types of an area merged, parts under {DRAW_MIN_PART_M2 / 10000:g} ha left out, "
            f"holes under {DRAW_MIN_HOLE_M2 / 10000:g} ha filled, simplified to {DRAW_SIMPLIFY_M} m. For display only.",
            "Codes: H = habitat type; ZGH = search area (indications, but no certainty, that the habitat type is present); "
            "Lg = nitrogen-sensitive habitat of Birds and Habitats Directive species (leefgebied).",
            "service_reply lists every Natura 2000 area the service returned for the bounding box; the query is by location, not by area name.",
            "What 'relevant' means, the KDW threshold and the code L4030: see docs/nitrogen-sources.md, 'AERIUS definitions: verification'.",
        ],
        "service_reply": [
            {"natura2000_area": name, **{k: (round(v, 1) if isinstance(v, float) else v) for k, v in counts.items()}}
            for name, counts in sorted(reply.items(), key=lambda item: item[0] or "")
        ],
        "habitat_types": rows,
        "features": features,
    }
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    target = config.PROCESSED_DIR / "nitrogen_sensitive_habitats.geojson"
    target.write_text(json.dumps(collection, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {target.relative_to(config.REPO_ROOT)} ({target.stat().st_size / 1024:.0f} kB)")

    print("\nAll Natura 2000 areas in the AERIUS reply for this bounding box:")
    print(f"{'Natura 2000 area':30} {'Records':>8} {'In map area':>12} {'In Nijkerk ha':>14}")
    for name, counts in sorted(reply.items(), key=lambda item: item[0] or ""):
        print(f"{(name or '?')[:30]:30} {counts['records_returned']:8} {counts['records_in_map_area']:12} {counts['mapped_ha_in_municipality']:14.1f}")
    print(f"Total mapped relevant habitat inside {config.MUNICIPALITY_NAME}: "
          f"{sum(c['mapped_ha_in_municipality'] for c in reply.values()):.1f} ha (all areas together)")

    print(f"\n{'Natura 2000 area':30} {'Types':>5} {'Lowest KDW':>11} {'In map ha':>10} {'In Nijkerk ha':>14} {'Nearest km':>11}")
    for feature in features:
        p = feature["properties"]
        print(f"{(p['natura2000_area'] or '?')[:30]:30} {p['habitat_types']:5} {str(p['lowest_kdw_mol_per_ha']):>11} "
              f"{p['mapped_ha_in_map_area']:10.1f} {p['mapped_ha_in_municipality']:14.1f} {p['distance_to_municipality_km']:11.1f}")
    print(f"\n{'Area':22} {'Code':12} {'KDW':>6} {'In map ha':>10} {'In Nijkerk ha':>14}  Description")
    for r in rows:
        print(f"{(r['natura2000_area'] or '?')[:22]:22} {(r['habitat_code'] or '?')[:12]:12} {str(r['kdw_mol_per_ha']):>6} "
              f"{r['mapped_ha_in_map_area']:10.1f} {r['mapped_ha_in_municipality']:14.1f}  {(r['habitat_description'] or '')[:60]}")


if __name__ == "__main__":
    main()
