"""Compare the livestock figures on the page with the newest edition in the database.

The page (nitrogen.html) is refreshed by hand from data/nitrogen/processed/livestock_trend.json.
The pipeline stores every CBS edition in PostgreSQL. The two are kept apart on purpose; this
check says whether they still agree, so that a CBS revision the page has not taken over yet
is noticed instead of shown as current.

It reads both and changes neither.

Usage (from the repo root, with DATABASE_URL set as for cbs_livestock.py):
    python pipeline/compare_with_page.py

Exit code: 0 the page and the database agree; 1 they differ, every difference is listed;
2 the database or the page file could not be read.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cbs_livestock as pipeline  # noqa: E402  (connect, and the settings of the nitrogen module)

config = pipeline.config
PAGE_FILE = config.PROCESSED_DIR / "livestock_trend.json"
MAX_LISTED = 25   # more differences than this are counted, not all printed

log = logging.getLogger("compare_with_page")

Key = tuple[str, int, str]   # region code, year, indicator


def page_values(path: Path = PAGE_FILE) -> tuple[datetime, dict[Key, int | None]]:
    """The CBS edition the page was built from, and every value it shows."""
    data = json.loads(path.read_text(encoding="utf-8"))
    edition = datetime.fromisoformat(data["source"]["table_modified"])
    years = data["years"]
    values: dict[Key, int | None] = {}
    for region, entry in data["regions"].items():
        for indicator, series in entry["values"].items():
            if len(series) != len(years):
                raise ValueError(f"{region} {indicator}: {len(series)} values for {len(years)} years")
            for year, value in zip(years, series):
                values[(region, int(year), indicator)] = None if value is None else int(value)
    return edition, values


def database_values(conn) -> tuple[datetime | None, dict[Key, int | None]]:
    """The newest edition in the database, and the newest value of every figure."""
    rows = conn.execute(
        "select region_code, year, indicator, value, source_modified from etl.livestock_latest").fetchall()
    values = {(region, int(year), indicator): value for region, year, indicator, value, _ in rows}
    edition = max((row[4] for row in rows), default=None)
    return edition, values


def compare(page: tuple[datetime, dict], database: tuple[datetime | None, dict]) -> list[str]:
    """Every way in which the page and the database disagree, one line each."""
    page_edition, page_vals = page
    db_edition, db_vals = database
    if db_edition is None:
        return ["the database holds no livestock values; run pipeline/cbs_livestock.py first"]

    differences = []
    if page_edition != db_edition:
        differences.append(f"edition: the page was built from {page_edition.isoformat()}, "
                           f"the newest in the database is {db_edition.isoformat()}")
    for key in sorted(page_vals.keys() - db_vals.keys()):
        differences.append(f"{describe(key)}: on the page, not in the database")
    for key in sorted(db_vals.keys() - page_vals.keys()):
        differences.append(f"{describe(key)}: in the database ({show(db_vals[key])}), not on the page")
    for key in sorted(page_vals.keys() & db_vals.keys()):
        if page_vals[key] != db_vals[key]:
            differences.append(f"{describe(key)}: page {show(page_vals[key])}, database {show(db_vals[key])}")
    return differences


def describe(key: Key) -> str:
    region, year, indicator = key
    return f"{region} {year} {indicator}"


def show(value: int | None) -> str:
    return "no figure" if value is None else str(value)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    try:
        page = page_values()
    except (OSError, ValueError, KeyError) as error:
        log.error("Could not read %s: %s: %s", PAGE_FILE.name, type(error).__name__, error)
        return 2

    url = os.environ.get("DATABASE_URL")
    if not url:
        log.error("DATABASE_URL is not set.")
        return 2
    try:
        conn = pipeline.connect(url)
    except Exception as error:  # the driver's message names host and user, never the password
        log.error("Could not connect to the database: %s: %s", type(error).__name__, str(error).strip())
        return 2
    try:
        database = database_values(conn)
    except Exception as error:
        if not pipeline.is_database_error(error):
            raise
        log.error("Database: %s: %s", type(error).__name__, str(error).strip())
        return 2
    finally:
        conn.close()

    differences = compare(page, database)
    if not differences:
        log.info("The page and the database agree: %d values, edition of %s",
                 len(page[1]), page[0].isoformat())
        return 0
    for line in differences[:MAX_LISTED]:
        log.warning("Differs: %s", line)
    if len(differences) > MAX_LISTED:
        log.warning("... and %d more", len(differences) - MAX_LISTED)
    log.warning("%d difference(s). If CBS revised the figures, refresh the page with "
                "scripts/nitrogen/fetch_cbs_livestock.py and build_page_data.py.", len(differences))
    return 1


if __name__ == "__main__":
    sys.exit(main())
