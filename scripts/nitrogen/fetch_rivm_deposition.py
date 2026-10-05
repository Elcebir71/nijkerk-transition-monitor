"""Clip the RIVM large-scale nitrogen deposition maps (GDN) to Nijkerk and surroundings.

Usage (from the repo root, after fetch_natura2000.py):
    python scripts/nitrogen/fetch_rivm_deposition.py

Reads   data/nitrogen/raw/depo_*_<year>.asc   (downloads the RIVM zip if missing)
        data/nitrogen/processed/municipality_boundary.geojson
Writes  data/nitrogen/processed/deposition_grid.geojson

The values are shown exactly as RIVM publishes them. This script does not model
deposition and does not estimate the effect of any measure.
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from datetime import date
from pathlib import Path

import requests
from pyproj import Transformer
from shapely.geometry import box, shape
from shapely.ops import transform

import config

TIMEOUT_S = 120
WGS84_TO_RD = Transformer.from_crs("EPSG:4326", "EPSG:28992", always_xy=True)
RD_TO_WGS84 = Transformer.from_crs("EPSG:28992", "EPSG:4326", always_xy=True)


def find_or_download_grid(file_stem: str) -> Path | None:
    """Return the path of <file_stem>.asc under data/nitrogen/raw, downloading it if needed."""
    found = sorted(config.RAW_DIR.rglob(f"{file_stem}.asc"))
    if found:
        return found[0]
    url = f"{config.RIVM_GDN_BASE_URL}/{file_stem}.zip"
    print(f"Downloading {url}")
    try:
        response = requests.get(url, timeout=TIMEOUT_S)
        response.raise_for_status()
        config.RAW_DIR.mkdir(parents=True, exist_ok=True)
        zipfile.ZipFile(io.BytesIO(response.content)).extractall(config.RAW_DIR)
    except (requests.RequestException, zipfile.BadZipFile) as error:
        print(f"  could not download {file_stem}: {error}")
        return None
    found = sorted(config.RAW_DIR.rglob(f"{file_stem}.asc"))
    return found[0] if found else None


def read_ascii_grid(path: Path) -> dict:
    """Read an ESRI ASCII grid. The first data row is the northernmost row."""
    lines = path.read_text().splitlines()
    header = {parts[0].upper(): float(parts[1]) for parts in (line.split() for line in lines[:6])}
    rows = [[float(v) for v in line.split()] for line in lines[6:] if line.strip()]
    grid = {
        "ncols": int(header["NCOLS"]), "nrows": int(header["NROWS"]),
        "xll": header["XLLCORNER"], "yll": header["YLLCORNER"],
        "cellsize": header["CELLSIZE"], "nodata": header["NODATA_VALUE"], "rows": rows,
    }
    if len(rows) != grid["nrows"] or any(len(row) != grid["ncols"] for row in rows):
        sys.exit(f"{path.name}: grid size does not match its header.")
    return grid


def cell_value(grid: dict, col: int, row_from_south: int) -> float | None:
    """Value of the cell whose lower-left corner is (xll + col*size, yll + row_from_south*size)."""
    value = grid["rows"][grid["nrows"] - 1 - row_from_south][col]
    return None if abs(value - grid["nodata"]) < 1e-6 else value


def load_municipality():
    path = config.PROCESSED_DIR / "municipality_boundary.geojson"
    if not path.exists():
        sys.exit("municipality_boundary.geojson not found. Run fetch_natura2000.py first.")
    feature = json.loads(path.read_text(encoding="utf-8"))["features"][0]
    return transform(WGS84_TO_RD.transform, shape(feature["geometry"]))


def cell_polygon_wgs84(x0: float, y0: float, size: float) -> dict:
    corners = [(x0, y0), (x0 + size, y0), (x0 + size, y0 + size), (x0, y0 + size), (x0, y0)]
    ring = [[round(v, 5) for v in RD_TO_WGS84.transform(x, y)] for x, y in corners]
    return {"type": "Polygon", "coordinates": [ring]}


def summarise(values_and_shares: list[tuple[float, float]]) -> dict | None:
    """Area-weighted mean over the cells that overlap the municipality."""
    if not values_and_shares:
        return None
    total_share = sum(share for _, share in values_and_shares)
    mean = sum(value * share for value, share in values_and_shares) / total_share
    # Lowest and highest cell: only cells that lie at least half inside, to ignore slivers.
    values = [value for value, share in values_and_shares if share >= 0.5] or [v for v, _ in values_and_shares]
    return {
        "mean_mol_per_ha": round(mean),
        "mean_kg_n_per_ha": round(mean * config.MOL_N_TO_KG, 1),
        "lowest_cell_mol_per_ha": round(min(values)),
        "highest_cell_mol_per_ha": round(max(values)),
        "cells": len(values_and_shares),
    }


def main() -> None:
    grids = {}
    for key, component in config.RIVM_GDN_COMPONENTS.items():
        path = find_or_download_grid(component["file"])
        if path is None:
            if component["required"]:
                sys.exit(f"{component['file']}.asc is required. Download it from {config.RIVM_GDN_DOWNLOAD_PAGE}")
            continue
        grids[key] = read_ascii_grid(path)

    reference = grids["ntot"]
    size, xll, yll = reference["cellsize"], reference["xll"], reference["yll"]
    for key, grid in grids.items():
        if any(grid[k] != reference[k] for k in ("ncols", "nrows", "xll", "yll", "cellsize")):
            sys.exit(f"Grid '{key}' does not have the same layout as the total-nitrogen grid.")

    municipality = load_municipality()
    min_x, min_y, max_x, max_y = municipality.buffer(config.SURROUNDINGS_RADIUS_M).bounds
    cols = range(max(0, int((min_x - xll) // size)), min(reference["ncols"], int((max_x - xll) // size) + 1))
    rows = range(max(0, int((min_y - yll) // size)), min(reference["nrows"], int((max_y - yll) // size) + 1))
    m_min_x, m_min_y, m_max_x, m_max_y = municipality.bounds

    features = []
    inside = {key: [] for key in grids}
    for row in rows:
        y0 = yll + row * size
        for col in cols:
            x0 = xll + col * size
            values = {key: cell_value(grid, col, row) for key, grid in grids.items()}
            if all(value is None for value in values.values()):
                continue
            share = 0.0
            if x0 < m_max_x and x0 + size > m_min_x and y0 < m_max_y and y0 + size > m_min_y:
                share = municipality.intersection(box(x0, y0, x0 + size, y0 + size)).area / (size * size)
            for key, value in values.items():
                if value is not None and share > 0:
                    inside[key].append((value, share))
            features.append({
                "type": "Feature",
                "properties": {
                    **{key: (None if value is None else round(value)) for key, value in values.items()},
                    "share_in_municipality": round(share, 3),
                },
                "geometry": cell_polygon_wgs84(x0, y0, size),
            })

    summary = {
        key: {"label_nl": config.RIVM_GDN_COMPONENTS[key]["label_nl"], **stats}
        for key in grids if (stats := summarise(inside[key]))
    }
    collection = {
        "type": "FeatureCollection",
        "source": {
            "publisher": "RIVM (Rijksinstituut voor Volksgezondheid en Milieu)",
            "dataset": "GDN, Grootschalige Depositiekaarten Nederland",
            "year": config.RIVM_GDN_YEAR,
            "url": config.RIVM_GDN_DOWNLOAD_PAGE,
            "files": [config.RIVM_GDN_COMPONENTS[key]["file"] + ".asc" for key in grids],
            **config.RIVM_GDN_METADATA,
            "licence": "See RIVM disclaimer and copyright page (not checked yet)",
            "fetched_on": date.today().isoformat(),
        },
        "notes": [
            "Values are shown as published by RIVM. No own deposition modelling.",
            "The uncertainty per grid cell is large; differences between neighbouring cells are often not meaningful.",
            "The metadata in this file is the metadata RIVM gives for the total-nitrogen map.",
            "For deposition on nature areas RIVM refers to its report 'Monitor stikstofdepositie in Natura 2000-gebieden'.",
            f"Grid cells cover {config.MUNICIPALITY_NAME} plus about {config.SURROUNDINGS_RADIUS_M / 1000:.0f} km around it.",
            "share_in_municipality is the fraction of the cell that lies inside the municipal boundary.",
        ],
        "municipality_summary": summary,
        "features": features,
    }
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    target = config.PROCESSED_DIR / "deposition_grid.geojson"
    target.write_text(json.dumps(collection, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote {target.relative_to(config.REPO_ROOT)} ({target.stat().st_size / 1024:.0f} kB, {len(features)} cells)")
    print(f"\n{config.MUNICIPALITY_NAME}, {config.RIVM_GDN_YEAR}, {config.RIVM_GDN_METADATA['unit']}")
    for key, stats in summary.items():
        print(f"  {key:5} mean {stats['mean_mol_per_ha']:5} ({stats['mean_kg_n_per_ha']} kg N/ha)   "
              f"cells {stats['lowest_cell_mol_per_ha']}-{stats['highest_cell_mol_per_ha']}   n={stats['cells']}")


if __name__ == "__main__":
    main()
