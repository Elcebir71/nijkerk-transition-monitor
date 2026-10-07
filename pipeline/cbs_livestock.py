"""Load the CBS livestock counts into PostgreSQL: extract, validate, load.

Usage (from the repo root):
    python pipeline/cbs_livestock.py --dry-run   fetch and validate only; no database needed
    python pipeline/cbs_livestock.py             fetch, validate and load
    python pipeline/cbs_livestock.py --force     load even when this edition was loaded before

The database is given in the environment variable DATABASE_URL, for example
postgresql://user:password@host:5432/dbname. It is never written to the log.

What it does:
    extract   asks CBS StatLine for the edition of the table (its "Modified" date) and for the
              rows of Nijkerk and Gelderland. An edition that was loaded before is skipped.
    validate  checks the rows before anything is stored. Every problem is listed, and one
              problem is enough to stop: nothing is loaded from a run that fails a check.
    load      stores the rows as CBS gave them (etl.cbs_livestock_raw) and the clean values
              (etl.livestock), in one transaction. Every run is recorded in etl.load_run,
              also when it fails or is skipped.

It is separate from nitrogen.html and never changes the page or its data files.

What it cannot see: a change in the values that CBS makes without a new "Modified" date.

Exit code: 0 loaded, skipped or dry run passed; 1 the data failed a check; 2 CBS or the
database could not be reached. A scheduled job that ends with anything but 0 needs a look.

Needs requests and pandas, and psycopg for the database (see pipeline/requirements.txt).
The tables are made by pipeline/sql/001_schema.sql.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "nitrogen"))
import config  # noqa: E402  (the settings of the nitrogen module)
import fetch_cbs_livestock as cbs  # noqa: E402  (the fetch the page uses; the same request here)

SOURCE = f"cbs_{config.CBS_TABLE_ID}"
PERIOD_PATTERN = r"^\d{4}JJ00$"   # a whole year in CBS notation, e.g. 2025JJ00
EXPECTED_REGIONS = (config.MUNICIPALITY_KEY.strip(), config.PROVINCE_KEY.strip())
INDICATOR_IDS = {column: meta["id"] for column, meta in config.CBS_INDICATORS.items()}
# The census is published the year after the count at the latest.
MAX_AGE_OF_LATEST_YEAR = 2

log = logging.getLogger("cbs_livestock")


class SourceError(Exception):
    """CBS could not be read."""


class ValidationError(Exception):
    """The rows failed one or more checks. `problems` holds one line per failed check."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------

def fetch_edition() -> tuple[datetime, set[str]]:
    """The "Modified" date of the table and the column keys it has now."""
    try:
        table_info = cbs.get_all(f"{config.CBS_BASE_URL}/TableInfos")[0]
        modified = datetime.fromisoformat(table_info["Modified"])
        published = {p.get("Key") for p in cbs.get_all(f"{config.CBS_BASE_URL}/DataProperties")}
    except (requests.RequestException, ValueError, LookupError, TypeError) as error:
        raise SourceError(f"could not read the table description: {type(error).__name__}: {error}") from error
    return modified, published


def fetch_rows() -> list[dict]:
    try:
        return cbs.fetch_rows()
    except (requests.RequestException, ValueError) as error:
        raise SourceError(f"could not read the rows: {type(error).__name__}: {error}") from error


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

def validate(rows: list[dict], published_columns: set[str], today: date) -> pd.DataFrame:
    """Check the rows and return them in long form: region_code, year, indicator, value.

    Raises ValidationError with every failed check, so one run shows all that is wrong.
    """
    problems: list[str] = []

    missing = [column for column in config.CBS_INDICATORS if column not in published_columns]
    if missing:
        problems.append(f"the table no longer has column(s): {', '.join(missing)}")
    if not rows:
        raise ValidationError(problems + ["CBS returned no rows"])

    frame = pd.DataFrame(rows)
    needed = ["RegioS", "Perioden", *config.CBS_INDICATORS]
    absent = [column for column in needed if column not in frame.columns]
    if absent:
        raise ValidationError(problems + [f"the rows lack column(s): {', '.join(absent)}"])

    frame["region_code"] = frame["RegioS"].astype("string").str.strip()
    period = frame["Perioden"].astype("string")
    bad_period = ~period.str.match(PERIOD_PATTERN).fillna(False).astype(bool)
    if bad_period.any():
        examples = sorted(set(period[bad_period].fillna("<empty>")))[:5]
        raise ValidationError(problems + [f"period(s) that are not a whole year: {', '.join(examples)}"])
    frame["year"] = period.str[:4].astype(int)

    regions = set(frame["region_code"].dropna())
    for region in EXPECTED_REGIONS:
        if region not in regions:
            problems.append(f"no rows for region {region}")
    unexpected = sorted(regions - set(EXPECTED_REGIONS))
    if unexpected:
        problems.append(f"rows for region(s) that were not asked for: {', '.join(unexpected)}")

    duplicated = frame[frame.duplicated(["region_code", "year"], keep=False)]
    if not duplicated.empty:
        pairs = sorted({f"{r} {y}" for r, y in zip(duplicated["region_code"], duplicated["year"])})[:5]
        problems.append(f"more than one row for: {', '.join(pairs)}")

    years_per_region = {region: set(group["year"]) for region, group in frame.groupby("region_code")}
    for region, years in sorted(years_per_region.items()):
        gaps = sorted(set(range(min(years), max(years) + 1)) - years)
        if gaps:
            problems.append(f"{region}: year(s) missing in the series: {', '.join(map(str, gaps))}")
    if len({frozenset(years) for years in years_per_region.values()}) > 1:
        problems.append("the regions do not cover the same years")
    latest = int(frame["year"].max())
    if latest < today.year - MAX_AGE_OF_LATEST_YEAR:
        problems.append(f"the latest year is {latest}; expected {today.year - MAX_AGE_OF_LATEST_YEAR} or later")

    long = frame.melt(id_vars=["region_code", "year"], value_vars=list(config.CBS_INDICATORS),
                      var_name="cbs_column", value_name="value")
    long["indicator"] = long["cbs_column"].map(INDICATOR_IDS)
    number = pd.to_numeric(long["value"], errors="coerce")

    not_a_number = long["value"].notna() & number.isna()
    if not_a_number.any():
        problems.append(f"{int(not_a_number.sum())} value(s) that are not a number, "
                        f"e.g. {long.loc[not_a_number, 'value'].iloc[0]!r} for {describe(long[not_a_number].iloc[0])}")
    not_whole = number.notna() & (number % 1 != 0)
    if not_whole.any():
        problems.append(f"{int(not_whole.sum())} count(s) that are not a whole number, "
                        f"e.g. {number[not_whole].iloc[0]} for {describe(long[not_whole].iloc[0])}")
    negative = number < 0
    if negative.any():
        problems.append(f"{int(negative.sum())} negative count(s), "
                        f"e.g. {number[negative].iloc[0]} for {describe(long[negative].iloc[0])}")

    long["number"] = number
    for (region, indicator), group in long.groupby(["region_code", "indicator"]):
        if group["number"].isna().all():
            problems.append(f"{region} {indicator}: no value in any year")

    # A municipality cannot have more animals or farms than its province.
    wide = long.pivot_table(index=["year", "indicator"], columns="region_code", values="number", aggfunc="first")
    if set(EXPECTED_REGIONS) <= set(wide.columns):
        municipality, province = EXPECTED_REGIONS
        above = wide[wide[municipality] > wide[province]]
        if not above.empty:
            year, indicator = above.index[0]
            problems.append(f"{len(above)} value(s) of {municipality} above {province}, e.g. {indicator} in {year}")

    if problems:
        raise ValidationError(problems)

    clean = long[["region_code", "year", "indicator"]].copy()
    clean["value"] = number.astype("Int64")   # a nullable whole number: missing stays missing
    return clean.sort_values(["region_code", "year", "indicator"]).reset_index(drop=True)


def describe(row: pd.Series) -> str:
    return f"{row['region_code']} {row['indicator']} {row['year']}"


def compare_with_previous(rows_fetched: int, previous: dict | None) -> list[str]:
    """CBS adds a year to this table and removes none, so fewer rows than last time is wrong."""
    if previous and previous.get("rows_fetched") is not None and rows_fetched < previous["rows_fetched"]:
        return [f"fewer rows than in the last loaded run {previous['run_id']}: "
                f"{rows_fetched} now, {previous['rows_fetched']} then"]
    return []


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def connect(url: str):
    import psycopg  # imported here, so a dry run and the tests need no database driver

    return psycopg.connect(url, autocommit=True)


def last_loaded_run(conn) -> dict | None:
    row = conn.execute(
        "select run_id, source_modified, rows_fetched from etl.load_run "
        "where source = %s and status = 'succeeded' order by run_id desc limit 1", (SOURCE,)).fetchone()
    return {"run_id": row[0], "source_modified": row[1], "rows_fetched": row[2]} if row else None


def start_run(conn) -> int:
    return conn.execute("insert into etl.load_run (source) values (%s) returning run_id", (SOURCE,)).fetchone()[0]


def finish_run(conn, run_id: int, status: str, *, source_modified: datetime | None = None,
               rows_fetched: int | None = None, rows_loaded: int | None = None, message: str | None = None) -> None:
    conn.execute(
        "update etl.load_run set status = %s, finished_at = now(), source_modified = %s, "
        "rows_fetched = %s, rows_loaded = %s, message = %s where run_id = %s",
        (status, source_modified, rows_fetched, rows_loaded, message, run_id))


def load(conn, run_id: int, rows: list[dict], clean: pd.DataFrame, source_modified: datetime) -> int:
    """Store the raw rows and the clean values in one transaction. Returns the number of clean values."""
    raw_values = [(run_id, str(row["RegioS"]).strip(), str(row["Perioden"]), json.dumps(row, ensure_ascii=False))
                  for row in rows]
    clean_values = [(r.region_code, int(r.year), r.indicator, None if pd.isna(r.value) else int(r.value),
                     source_modified, run_id)
                    for r in clean.itertuples(index=False)]
    with conn.transaction():
        with conn.cursor() as cursor:
            cursor.executemany(
                "insert into etl.cbs_livestock_raw (run_id, region_key, period_key, payload) "
                "values (%s, %s, %s, %s::jsonb)", raw_values)
            # The same edition loaded again (--force) replaces its own values; another edition adds rows.
            cursor.executemany(
                "insert into etl.livestock (region_code, year, indicator, value, source_modified, run_id) "
                "values (%s, %s, %s, %s, %s, %s) "
                "on conflict (region_code, year, indicator, source_modified) "
                "do update set value = excluded.value, run_id = excluded.run_id", clean_values)
    return len(clean_values)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def summary_lines(clean: pd.DataFrame) -> list[str]:
    municipality = clean[clean["region_code"] == EXPECTED_REGIONS[0]]
    first, last = int(municipality["year"].min()), int(municipality["year"].max())
    lines = [f"{config.MUNICIPALITY_NAME}, {first} and {last}:"]
    for indicator in INDICATOR_IDS.values():
        series = municipality[municipality["indicator"] == indicator].set_index("year")["value"]
        lines.append(f"  {indicator:16} {series.get(first)}   {series.get(last)}")
    return lines


def run(conn, *, force: bool, today: date) -> int:
    """One run of the pipeline. `conn` is None in a dry run. Returns the exit code."""
    run_id = start_run(conn) if conn else None

    def record(status: str, **details) -> None:
        if conn:
            finish_run(conn, run_id, status, **details)

    modified = None
    try:
        modified, published = fetch_edition()
        log.info("CBS table %s, edition of %s", config.CBS_TABLE_ID, modified.isoformat())
        previous = last_loaded_run(conn) if conn else None
        if previous and previous["source_modified"] == modified and not force:
            message = f"edition of {modified.isoformat()} was loaded in run {previous['run_id']}"
            log.info("Skipped: %s", message)
            record("skipped", source_modified=modified, message=message)
            return 0

        rows = fetch_rows()
        log.info("Fetched %d rows", len(rows))
        clean = validate(rows, published, today)
        problems = compare_with_previous(len(rows), previous)
        if problems:
            raise ValidationError(problems)
        log.info("Validated: %d values, %d without a figure", len(clean), int(clean["value"].isna().sum()))
        for line in summary_lines(clean):
            log.info(line)

        if not conn:
            log.info("Dry run: nothing was stored")
            return 0
        loaded = load(conn, run_id, rows, clean, modified)
        record("succeeded", source_modified=modified, rows_fetched=len(rows), rows_loaded=loaded)
        log.info("Loaded %d values in run %d", loaded, run_id)
        return 0
    except ValidationError as error:
        for problem in error.problems:
            log.error("Check failed: %s", problem)
        record("failed", source_modified=modified, message="validation: " + "; ".join(error.problems))
        return 1
    except SourceError as error:
        log.error("CBS: %s", error)
        record("failed", source_modified=modified, message=f"source: {error}")
        return 2
    except Exception as error:
        if not is_database_error(error):
            raise
        log.error("Database: %s: %s", type(error).__name__, str(error).strip())
        try:   # the transaction was rolled back; say so in the run record if the database still answers
            record("failed", source_modified=modified, message=f"database: {type(error).__name__}")
        except Exception:
            pass
        return 2


def is_database_error(error: Exception) -> bool:
    return type(error).__module__.split(".")[0] == "psycopg"


def main() -> int:
    parser = argparse.ArgumentParser(description="Load CBS livestock counts into PostgreSQL.")
    parser.add_argument("--dry-run", action="store_true", help="fetch and validate only; no database")
    parser.add_argument("--force", action="store_true", help="load even when this edition was loaded before")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)

    conn = None
    if not args.dry_run:
        url = os.environ.get("DATABASE_URL")
        if not url:
            log.error("DATABASE_URL is not set. Use --dry-run to run without a database.")
            return 2
        try:
            conn = connect(url)
        except Exception as error:  # the driver's message names host and user, never the password
            log.error("Could not connect to the database: %s: %s", type(error).__name__, str(error).strip())
            return 2
    try:
        return run(conn, force=args.force, today=date.today())
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
