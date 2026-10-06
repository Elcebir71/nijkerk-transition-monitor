"""One-off helper: KDW exceedance per Natura 2000 area from an RIVM monitor GeoPackage.

Usage (from the repo root):
    python scripts/nitrogen/inspect_rivm_monitor_classes.py [area name] [path to .gpkg]

Defaults: area "Veluwe", file
data/nitrogen/raw/RIVM-MIL_M25-Deposities_Overbelastingsklasse_20260401.gpkg
(RIVM, data behind the Monitor stikstofdepositie in Natura 2000-gebieden 2025;
download it from the RIVMdata catalogue and put it in data/nitrogen/raw/, which
is not committed). Only reads the file and prints a report. Needs no packages.

What it does: for each year in the file it adds up `cartographic_surface` per
exceedance class, for the whole country and for one Natura 2000 area. The class
of a row is taken from its own `distance_to_kdw` (deposition minus KDW), with
RIVM's class limits. For the whole country this comes within about 1.5
percentage points of the shares printed in the RIVM report, and the mean
deposition within 1 mol. The figures for a single area are an aggregation made here from RIVM
values. They are not figures published by RIVM.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

DEFAULT_FILE = (Path(__file__).resolve().parents[2] / "data" / "nitrogen" / "raw"
                / "RIVM-MIL_M25-Deposities_Overbelastingsklasse_20260401.gpkg")
TABLE = "nitro"
# RIVM's classes in this monitor: mol N/ha/year above the KDW.
CLASS_LABELS = ["none", "0-250", "250-500", "500-750", "750-1000", ">1000"]
CLASS_SQL = ("case when distance_to_kdw <= 0 then 0 when distance_to_kdw <= 250 then 1 "
             "when distance_to_kdw <= 500 then 2 when distance_to_kdw <= 750 then 3 "
             "when distance_to_kdw <= 1000 then 4 else 5 end")


def report(cursor: sqlite3.Cursor, title: str, where: str, params: tuple) -> None:
    years = [row[0] for row in cursor.execute(f"select distinct year from {TABLE} where {where} order by 1", params)]
    if not years:
        print(f"\n{title}: no rows. Check the area name.")
        return
    print(f"\n{title}")
    print("share of mapped surface per class (%), hexagons per class, surface-weighted means in mol N/ha/year")
    print(f"{'year':>5} " + " ".join(f"{label:>9}" for label in CLASS_LABELS)
          + f" {'hexagons':>9} {'none':>6} {'deposition':>11} {'exceedance':>11}")
    for year in years:
        rows = cursor.execute(
            f"select {CLASS_SQL}, sum(cartographic_surface), count(*) from {TABLE} "
            f"where {where} and year = ? group by 1", params + (year,)).fetchall()
        surface = {k: s for k, s, _ in rows}
        count = {k: n for k, _, n in rows}
        total = sum(surface.values())
        deposition, exceedance = cursor.execute(
            f"select sum(deposition * cartographic_surface) / sum(cartographic_surface), "
            f"sum(max(distance_to_kdw, 0) * cartographic_surface) / sum(cartographic_surface) "
            f"from {TABLE} where {where} and year = ?", params + (year,)).fetchone()
        print(f"{year:>5} " + " ".join(f"{100 * surface.get(k, 0) / total:9.1f}" for k in range(6))
              + f" {sum(count.values()):>9} {count.get(0, 0):>6} {deposition:11.0f} {exceedance:11.0f}")


def main() -> None:
    area = sys.argv[1] if len(sys.argv) > 1 else "Veluwe"
    path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_FILE
    if not path.exists():
        sys.exit(f"File not found: {path}")
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    cursor = connection.cursor()

    print(f"File: {path.name}")
    zooms = [row[0] for row in cursor.execute(f"select distinct zoom_level from {TABLE}")]
    print(f"Rows: {cursor.execute(f'select count(*) from {TABLE}').fetchone()[0]}; zoom levels: {zooms} "
          "(3 = hexagons of 16 ha)")
    print("An aggregation made here from RIVM values; not figures published by RIVM.")

    report(cursor, "Netherlands (check against the RIVM report)", "1 = 1", ())
    report(cursor, f"Natura 2000 area: {area}", "natura2000_area_name = ?", (area,))

    stored = cursor.execute(
        f"select count(*) from {TABLE} where kdw_class_id - 1 <> {CLASS_SQL}").fetchone()[0]
    print(f"\nRows where the stored `kdw_class` differs from the class of the row's own `distance_to_kdw`: {stored}")
    print("(the stored class is not used above; what it is based on is not documented in the file)")


if __name__ == "__main__":
    main()
