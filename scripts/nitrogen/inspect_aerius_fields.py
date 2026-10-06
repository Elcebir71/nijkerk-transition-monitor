"""One-off helper: test what the AERIUS hexagon fields mean, using the data itself.

Usage (from the repo root):
    python scripts/nitrogen/inspect_aerius_fields.py [--refresh]

Without --refresh the script reads the downloads it saved earlier, if any.
With --refresh it downloads the three layers again and replaces the saved
files. The report states for each layer which of the two happened, and when.

Questions this helps with (see docs/nitrogen-sources.md, "AERIUS definitions"):
  1. Which rule reproduces the hexagon field `exceeding`?
  2. Which rule reproduces the hexagon field `above_cl`?
  3. What are `surface` and `coverage` in the hexagon-to-habitat link table?

It downloads three layers for the map area (Nijkerk + 15 km), keeps them in
data/nitrogen/raw/ (not committed) and prints a report. The report is also
saved as data/nitrogen/raw/aerius_field_test_report.txt. Nothing else is written.

A rule that fits the data is NOT an official definition. It only shows which
reading is consistent with what the service publishes.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import requests

WFS_URL = "https://connect.aerius.nl/opendata/wfs"
CRS = "urn:ogc:def:crs:EPSG::28992"
# Map area in EPSG:28992: bounding box of Nijkerk plus 15 km (same as inspect_aerius.py).
MAP_BBOX = "140411,449181,186929,490103," + CRS
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "nitrogen" / "raw"
REPORT_FILE = "aerius_field_test_report.txt"
TIMEOUT_S = 900
PAGE_SIZE = 20000
NEAR_MARGIN_MOL = 70          # "(naderend) overbelast": from 70 mol below the KDW (RIVM 2025-0020, p. 30)
HEXAGON_M2 = 10000            # 1 ha
AREA_TOLERANCE_M2 = 1.0

# layer -> (file name in data/nitrogen/raw, sort key used only if the service needs paging)
LAYERS = {
    "base_geometries:hexagons": ("aerius_hexagons.json", "receptor_id,zoom_level"),
    "depositions:depositions": ("aerius_depositions.json", "receptor_id,zoom_level,year"),
    "base_geometries:hexagons_to_relevant_habitats": ("aerius_hexagons_to_habitats.json", "receptor_id,zoom_level,habitat_type_id"),
}
HABITAT_RAW_FILE = "aerius_relevant_habitats.json"   # written earlier by fetch_aerius_habitats.py

RULES = {
    "deposition >  KDW": lambda dep, kdw: dep > kdw,
    "deposition >= KDW": lambda dep, kdw: dep >= kdw,
    f"deposition >  KDW - {NEAR_MARGIN_MOL}": lambda dep, kdw: dep > kdw - NEAR_MARGIN_MOL,
    f"deposition >= KDW - {NEAR_MARGIN_MOL}": lambda dep, kdw: dep >= kdw - NEAR_MARGIN_MOL,
}

REFRESH = "--refresh" in sys.argv[1:]
TIME_FORMAT = "%Y-%m-%d %H:%M %Z"

report_lines: list[str] = []
provenance_lines: list[str] = []   # per layer: downloaded now, or read from a saved file


def out(text: str = "") -> None:
    print(text)
    report_lines.append(text)


def request_features(layer: str, extra: dict) -> dict:
    params = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": layer,
        "outputFormat": "application/json", "srsName": CRS, "bbox": MAP_BBOX, **extra,
    }
    response = requests.get(WFS_URL, params=params, timeout=TIMEOUT_S)
    response.raise_for_status()
    if "json" not in response.headers.get("Content-Type", ""):
        sys.exit(f"AERIUS did not return JSON for {layer}: {response.text[:300]}")
    return response.json()


def fetch(layer: str) -> list[dict]:
    """Return all features of a layer in the map area.

    Uses the saved download if there is one, unless --refresh was given.
    """
    file_name, sort_key = LAYERS[layer]
    path = RAW_DIR / file_name
    if path.exists() and not REFRESH:
        saved_at = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
        print(f"Using the download saved earlier ({file_name}). Run with --refresh to download again.")
        provenance_lines.append(f"  {layer}: NOT downloaded in this run; read from the file saved on {saved_at.strftime(TIME_FORMAT)}")
        return json.loads(path.read_text(encoding="utf-8"))["features"]

    print(f"Downloading {layer} (this can take several minutes)...")
    data = request_features(layer, {})
    features = data.get("features", [])
    matched = data.get("numberMatched")
    if isinstance(matched, int) and matched > len(features):
        print(f"  the service returned {len(features)} of {matched}; downloading in pages of {PAGE_SIZE}")
        features = []
        while len(features) < matched:
            page = request_features(layer, {"count": PAGE_SIZE, "startIndex": len(features), "sortBy": sort_key})
            if not page.get("features"):
                break
            features.extend(page["features"])
            print(f"  {len(features)} of {matched}")
        if len(features) != matched:
            sys.exit(f"Got {len(features)} of {matched} features for {layer}. Stop; the test would be incomplete.")
    print(f"  {len(features)} features")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"layer": layer, "features": features}), encoding="utf-8")
    provenance_lines.append(f"  {layer}: downloaded in this run, {datetime.now().astimezone().strftime(TIME_FORMAT)}")
    return features


def ring_area(ring: list) -> float:
    total = 0.0
    for (x1, y1, *_), (x2, y2, *_) in zip(ring, ring[1:]):
        total += x1 * y2 - x2 * y1
    return abs(total) / 2


def geometry_area(geometry: dict | None) -> float | None:
    """Area in m2 of a GeoJSON Polygon or MultiPolygon in EPSG:28992 (holes subtracted)."""
    if not geometry:
        return None
    if geometry["type"] == "Polygon":
        polygons = [geometry["coordinates"]]
    elif geometry["type"] == "MultiPolygon":
        polygons = geometry["coordinates"]
    else:
        return None
    return sum(ring_area(p[0]) - sum(ring_area(hole) for hole in p[1:]) for p in polygons)


def spread(values: list[float]) -> str:
    return f"min {min(values):9.1f}  max {max(values):9.1f}" if values else "-"


def code_group(code: str | None) -> str:
    """H3130 -> H, ZGH3130 -> ZGH, Lg13 -> Lg, L4030 -> L."""
    code = code or "?"
    for prefix in ("ZGH", "Lg", "H", "L"):
        if code.startswith(prefix):
            return prefix
    return "other"


def report_hexagons(hexagons: list[dict]) -> dict:
    out("=" * 78)
    out("A. base_geometries:hexagons")
    out("=" * 78)
    by_zoom = Counter(f["properties"].get("zoom_level") for f in hexagons)
    out("features per zoom_level: " + ", ".join(f"{z}: {n}" for z, n in sorted(by_zoom.items(), key=lambda i: str(i[0]))))

    out("\nvalue combinations per zoom_level (relevant, exceeding, above_cl, extra_assessment, KDW present):")
    combos: dict = defaultdict(Counter)
    for feature in hexagons:
        p = feature["properties"]
        combos[p.get("zoom_level")][(p.get("relevant"), p.get("exceeding"), p.get("above_cl"),
                                     p.get("extra_assessment"), p.get("critical_deposition") is not None)] += 1
    for zoom in sorted(combos, key=str):
        out(f"  zoom_level {zoom}:")
        for combo, count in combos[zoom].most_common():
            relevant, exceeding, above_cl, extra, has_kdw = combo
            out(f"    relevant={str(relevant):5} exceeding={str(exceeding):5} above_cl={str(above_cl):5} "
                f"extra_assessment={str(extra):5} KDW={'yes' if has_kdw else 'no ':3} : {count}")

    keyed = {}
    duplicates = 0
    for feature in hexagons:
        p = feature["properties"]
        key = (p.get("receptor_id"), p.get("zoom_level"))
        duplicates += key in keyed
        keyed[key] = p
    out(f"\nunique (receptor_id, zoom_level): {len(keyed)}; repeated keys: {duplicates}")
    return keyed


def report_depositions(depositions: list[dict]) -> dict:
    out("\n" + "=" * 78)
    out("B. depositions:depositions")
    out("=" * 78)
    per_year_zoom = Counter((f["properties"].get("year"), f["properties"].get("zoom_level")) for f in depositions)
    for (year, zoom), count in sorted(per_year_zoom.items(), key=lambda i: (str(i[0][0]), str(i[0][1]))):
        out(f"  year {year}, zoom_level {zoom}: {count} features")
    by_year: dict = defaultdict(dict)
    for feature in depositions:
        p = feature["properties"]
        if p.get("total_deposition") is not None:
            by_year[p.get("year")][(p.get("receptor_id"), p.get("zoom_level"))] = float(p["total_deposition"])
    for year, values in sorted(by_year.items(), key=lambda i: str(i[0])):
        out(f"  year {year}: total_deposition {spread(list(values.values()))} (unit not stated by the service; expected mol N/ha/year)")
    return by_year


def report_rules(hexagons: dict, depositions_by_year: dict) -> None:
    out("\n" + "=" * 78)
    out("C. Which rule reproduces `exceeding` and `above_cl`?")
    out("=" * 78)
    out("margin = total_deposition - critical_deposition, per hexagon (same receptor_id and zoom_level).")
    for year, depositions in sorted(depositions_by_year.items(), key=lambda i: str(i[0])):
        out(f"\n--- deposition year {year} ---")
        joined = []
        for key, props in hexagons.items():
            kdw, dep = props.get("critical_deposition"), depositions.get(key)
            if kdw is not None and dep is not None:
                joined.append((dep, float(kdw), props))
        with_kdw = sum(1 for p in hexagons.values() if p.get("critical_deposition") is not None)
        out(f"hexagons with a KDW: {with_kdw}; of these with a deposition value: {len(joined)}; "
            f"deposition values without a hexagon KDW: {sum(1 for k in depositions if (hexagons.get(k) or {}).get('critical_deposition') is None)}")
        if not joined:
            out("no hexagon has both a KDW and a deposition value; nothing to test for this year.")
            continue

        for field in ("exceeding", "above_cl"):
            out(f"\nfield `{field}`:")
            for value in (True, False, None):
                margins = [dep - kdw for dep, kdw, p in joined if p.get(field) is value]
                out(f"  {str(value):5}: {len(margins):6} hexagons   margin {spread(margins)}")
            out("  agreement with each candidate rule (hexagons where the field is true or false):")
            for name, rule in RULES.items():
                tested = [(dep, kdw, p[field]) for dep, kdw, p in joined if p.get(field) is not None]
                wrong = [(dep - kdw) for dep, kdw, flag in tested if rule(dep, kdw) != flag]
                verdict = "FITS ALL" if tested and not wrong else f"{len(wrong)} do not fit"
                detail = f" (their margins: {spread(wrong)})" if wrong else ""
                out(f"    {name:24}: {len(tested) - len(wrong):6} of {len(tested):6} fit  -> {verdict}{detail}")

        out("\nthe two fields against each other:")
        pairs = Counter((p.get("exceeding"), p.get("above_cl")) for _, _, p in joined)
        for (exceeding, above_cl), count in pairs.most_common():
            margins = [dep - kdw for dep, kdw, p in joined if p.get("exceeding") is exceeding and p.get("above_cl") is above_cl]
            out(f"  exceeding={str(exceeding):5} above_cl={str(above_cl):5}: {count:6} hexagons   margin {spread(margins)}")


def report_links(links: list[dict], hexagons: dict) -> None:
    out("\n" + "=" * 78)
    out("D. base_geometries:hexagons_to_relevant_habitats: `surface` and `coverage`")
    out("=" * 78)
    out(f"rows: {len(links)}; per zoom_level: " +
        ", ".join(f"{z}: {n}" for z, n in sorted(Counter(f['properties'].get('zoom_level') for f in links).items(), key=lambda i: str(i[0]))))

    # D1. What is the geometry of a row: the whole hexagon, or the piece inside the habitat?
    whole = piece = other = 0
    weighted_piece = 0
    for feature in links:
        p = feature["properties"]
        area, surface, coverage = geometry_area(feature.get("geometry")), p.get("surface"), p.get("coverage")
        if area is None or surface is None:
            continue
        surface = float(surface)
        if abs(area - HEXAGON_M2) <= AREA_TOLERANCE_M2:
            whole += 1
        elif abs(area - surface) <= AREA_TOLERANCE_M2:
            piece += 1
        elif coverage is not None and abs(area * float(coverage) - surface) <= AREA_TOLERANCE_M2:
            weighted_piece += 1
        else:
            other += 1
    out("\nD1. area of the row geometry compared with `surface` (tolerance 1 m2):")
    out(f"  geometry is a full 1 ha hexagon:            {whole}")
    out(f"  geometry area equals `surface`:             {piece}")
    out(f"  geometry area x coverage equals `surface`:  {weighted_piece}")
    out(f"  none of these:                              {other}")

    # D2. Is `surface` already multiplied by `coverage`? If it were, surface could never exceed 1 ha x coverage.
    surfaces = [float(f["properties"]["surface"]) for f in links if f["properties"].get("surface") is not None]
    out(f"\nD2. `surface`: {spread(surfaces)} (1 ha = {HEXAGON_M2} m2)")
    partial = [f["properties"] for f in links
               if f["properties"].get("coverage") is not None and f["properties"].get("surface") is not None
               and float(f["properties"]["coverage"]) < 1]
    above = [p for p in partial if float(p["surface"]) > HEXAGON_M2 * float(p["coverage"]) + AREA_TOLERANCE_M2]
    out(f"  rows with coverage < 1: {len(partial)}")
    out(f"  of these, rows where surface > 1 ha x coverage: {len(above)}")
    out("  (if this is above 0, `surface` cannot be the hexagon area already multiplied by `coverage`)")
    for p in above[:5]:
        out(f"    e.g. receptor {p.get('receptor_id')} {p.get('habitat_type_name')}: surface {float(p['surface']):.1f}, coverage {float(p['coverage']):.4f}")

    per_receptor: dict = defaultdict(float)
    for feature in links:
        p = feature["properties"]
        if p.get("surface") is not None:
            per_receptor[(p.get("receptor_id"), p.get("zoom_level"))] += float(p["surface"])
    over = sum(1 for total in per_receptor.values() if total > HEXAGON_M2 + AREA_TOLERANCE_M2)
    out(f"  hexagons where the surfaces of all habitat types add up to more than 1 ha: {over} of {len(per_receptor)}")
    out("  (above 0 means habitat types overlap each other inside a hexagon)")

    # D3. coverage per code group and per habitat type.
    out("\nD3. `coverage` per code group (H, ZGH, Lg, L):")
    groups: dict = defaultdict(list)
    types: dict = defaultdict(list)
    for feature in links:
        p = feature["properties"]
        if p.get("coverage") is not None:
            groups[code_group(p.get("habitat_type_name"))].append(float(p["coverage"]))
            types[p.get("habitat_type_name")].append((float(p["coverage"]), float(p.get("surface") or 0)))
    for group, values in sorted(groups.items()):
        below = sum(1 for v in values if v < 1)
        out(f"  {group:5}: {len(values):6} rows, coverage < 1 in {below:6}, min {min(values):.4f}, distinct values {len(set(values))}")

    habitat_level = {}
    habitat_path = RAW_DIR / HABITAT_RAW_FILE
    if habitat_path.exists():
        for feature in json.loads(habitat_path.read_text(encoding="utf-8")).get("features", []):
            p = feature["properties"]
            habitat_level[(p.get("natura2000_area_name"), p.get("habitat_type_name"))] = p.get("coverage")
    out("\nD3b. per habitat type: coverage in the link table, and the single value in relevant_habitats")
    out("      (surface-weighted mean = sum(surface x coverage) / sum(surface), map area only):")
    out(f"  {'code':12} {'rows':>6} {'min':>7} {'max':>7} {'distinct':>8} {'weighted mean':>14}   relevant_habitats (whole Natura 2000 area)")
    area_of = {f["properties"].get("habitat_type_name"): f["properties"].get("natura2000_area_name") for f in links}
    for code in sorted(types, key=str):
        values = types[code]
        covs = [c for c, _ in values]
        total_surface = sum(s for _, s in values)
        mean = sum(c * s for c, s in values) / total_surface if total_surface else float("nan")
        whole_area = habitat_level.get((area_of.get(code), code))
        whole_text = f"{float(whole_area):.4f}" if whole_area is not None else ("file not found" if not habitat_level else "not in file")
        out(f"  {str(code):12} {len(values):6} {min(covs):7.4f} {max(covs):7.4f} {len(set(covs)):8} {mean:14.4f}   {whole_text}")

    # D4. Is the hexagon KDW the lowest KDW of the habitat types in it?
    lowest: dict = {}
    for feature in links:
        p = feature["properties"]
        if p.get("critical_deposition") is not None:
            key = (p.get("receptor_id"), p.get("zoom_level"))
            lowest[key] = min(lowest.get(key, float("inf")), float(p["critical_deposition"]))
    same = different = missing = 0
    examples = []
    for key, value in lowest.items():
        hexagon_kdw = (hexagons.get(key) or {}).get("critical_deposition")
        if hexagon_kdw is None:
            missing += 1
        elif float(hexagon_kdw) == value:
            same += 1
        else:
            different += 1
            if len(examples) < 5:
                examples.append(f"receptor {key[0]}: hexagon {float(hexagon_kdw):.0f}, lowest in link table {value:.0f}")
    out("\nD4. hexagon `critical_deposition` compared with the lowest KDW of its habitat types in the link table:")
    out(f"  equal: {same}; different: {different}; hexagon not found or without KDW: {missing}")
    for example in examples:
        out("    e.g. " + example)


def main() -> None:
    hexagon_features = fetch("base_geometries:hexagons")
    deposition_features = fetch("depositions:depositions")
    link_features = fetch("base_geometries:hexagons_to_relevant_habitats")

    out("AERIUS field test, map area " + MAP_BBOX.split(",urn")[0])
    out("A rule that fits the data is not an official definition.")
    out("\nWhere the data of this run came from:")
    for line in provenance_lines:
        out(line)
    habitat_path = RAW_DIR / HABITAT_RAW_FILE
    if habitat_path.exists():
        saved_at = datetime.fromtimestamp(habitat_path.stat().st_mtime).astimezone()
        out(f"  base_geometries:relevant_habitats (used in D3b only): file saved on {saved_at.strftime(TIME_FORMAT)} "
            "by fetch_aerius_habitats.py; never downloaded by this script")
    out()
    hexagons = report_hexagons(hexagon_features)
    depositions_by_year = report_depositions(deposition_features)
    report_rules(hexagons, depositions_by_year)
    report_links(link_features, hexagons)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / REPORT_FILE).write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"\nReport saved as data/nitrogen/raw/{REPORT_FILE}")


if __name__ == "__main__":
    main()
