"""Load the ammonia measurements of the RIVM MAN network (Meetnet Ammoniak in Natuurgebieden).

Usage (from the repo root, with a file downloaded by hand from man.rivm.nl):
    python pipeline/man_ammonia.py --file data/nitrogen/raw/man_65_jaar.csv --kind annual --dry-run
    python pipeline/man_ammonia.py --file data/nitrogen/raw/man_65_jaar.csv --kind annual
    python pipeline/man_ammonia.py --file data/nitrogen/raw/man_65_3_maanden.csv --kind quarterly

The database is given in DATABASE_URL, as for cbs_livestock.py. It is never written to the log.

What it does:
    read      reads the file and computes its SHA-256. A MAN file has no edition date, so the
              SHA-256 is how a new version is recognised: a file with the same SHA-256 as the
              last stored download is skipped.
    validate  checks the format and the values before anything is stored. Every problem is
              listed, and one problem is enough to stop.
    load      stores the file as downloaded and its values, in one transaction, and reports
              which values changed since the last download. Every run is recorded in
              etl.load_run, also when it fails or is skipped.

The file is not fetched yet: whether the download links may be retrieved automatically has
been asked to RIVM (docs/nitrogen-sources.md, section 6). The time of retrieval is taken from
the file's modification time unless --retrieved-at is given.

It is separate from nitrogen.html and never changes the page.

Exit code: 0 loaded, skipped or dry run passed; 1 the file failed a check; 2 the file or the
database could not be read.

The files (man.rivm.nl, "Downloaden meetgegevens") are semicolon separated, use a decimal
comma, start with a byte order mark and have one row per location and one column per period:
"2025" in the annual file, "2025-3" in the three-monthly file. An empty cell means no value.
See docs/nitrogen-sources.md, section 6, for what the values mean and what they may be used for.

This module only checks the format. Whether the values are plausible is checked later.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

ID_COLUMNS = ("Gebied", "Locatienummer", "Locatienaam")
ANNUAL = re.compile(r"^(\d{4})$")
QUARTER = re.compile(r"^(\d{4})-([1-4])$")   # seasonal quarters: 1 = Feb-Apr ... 4 = Nov-Jan
VALUE = re.compile(r"^\d+(,\d+)?$")            # decimal comma, e.g. 3,7

URLS = {"annual": "https://man.rivm.nl/Man/Data/{area}",
        "quarterly": "https://man.rivm.nl/Man/Data_3_maanden/{area}"}
# A gross-error check, not a judgement on the level: the annual values of area 65 are below 10.
MAX_VALUE = Decimal("100")
# The annual file is updated every June; its latest year should not be older than this.
MAX_AGE_OF_LATEST_YEAR = 2
MAX_LISTED = 25   # more changes than this are counted, not all printed

log = logging.getLogger("man_ammonia")


class FormatError(Exception):
    """The file is not shaped like a MAN download. `problems` holds one line per problem."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class Measurement:
    area: str
    location: int
    location_name: str
    year: int
    quarter: int | None      # None in the annual file
    value: Decimal           # µg/m³; Decimal, so a revision is a change in the figure, not in rounding


def parse(text: str) -> list[Measurement]:
    """Every value in a MAN file, as one record per location and period."""
    rows = list(csv.reader(io.StringIO(text.lstrip("﻿")), delimiter=";"))
    if not rows:
        raise FormatError(["the file is empty"])
    header = drop_trailing_empty(rows[0])
    problems: list[str] = []

    if tuple(header[:3]) != ID_COLUMNS:
        raise FormatError([f"the first columns are {header[:3]}, expected {list(ID_COLUMNS)}"])
    periods = []
    for column in header[3:]:
        if match := ANNUAL.match(column):
            periods.append((int(match[1]), None))
        elif match := QUARTER.match(column):
            periods.append((int(match[1]), int(match[2])))
        else:
            problems.append(f"column {column!r} is not a period")
    if not periods and not problems:
        problems.append("the file has no period columns")
    if len({quarter is None for _, quarter in periods}) > 1:
        problems.append("the file mixes annual and three-monthly columns")
    if problems:
        raise FormatError(problems)

    measurements = []
    for line, row in enumerate(rows[1:], start=2):
        row = drop_trailing_empty(row)
        if not row:
            continue
        if len(row) > len(header):
            problems.append(f"line {line}: {len(row)} cells for {len(header)} columns")
            continue
        area, number, name = (row + ["", "", ""])[:3]
        if not number.isdigit():
            problems.append(f"line {line}: location number {number!r} is not a number")
            continue
        for (year, quarter), cell in zip(periods, row[3:]):
            cell = cell.strip()
            if not cell:
                continue
            if not VALUE.match(cell):
                period = year if quarter is None else f"{year}-{quarter}"
                problems.append(f"line {line}, {period}: {cell!r} is not a value")
                continue
            measurements.append(Measurement(area, int(number), name, year, quarter,
                                            Decimal(cell.replace(",", "."))))
    if problems:
        raise FormatError(problems)
    return measurements


def read_file(path: Path) -> list[Measurement]:
    return parse(path.read_text(encoding="utf-8-sig"))


def drop_trailing_empty(cells: list[str]) -> list[str]:
    """The files end every line with a semicolon, which makes one empty last cell."""
    cells = list(cells)
    while cells and not cells[-1].strip():
        cells.pop()
    return cells


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """The values failed one or more checks. `problems` holds one line per failed check."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


Key = tuple[int, int, "int | None"]   # location, year, quarter


def key(m: Measurement) -> Key:
    return (m.location, m.year, m.quarter)


def validate(measurements: list[Measurement], kind: str, today: date) -> list[str]:
    """Every way in which the values of one file are not what a MAN file of this kind holds."""
    if not measurements:
        return ["the file holds no values"]
    problems = []
    annual = [m for m in measurements if m.quarter is None]
    if kind == "annual" and len(annual) != len(measurements):
        problems.append("--kind annual, but the file has three-monthly columns")
    if kind == "quarterly" and annual:
        problems.append("--kind quarterly, but the file has annual columns")
    areas = {m.area for m in measurements}
    if len(areas) > 1:
        problems.append(f"the file holds more than one area: {sorted(areas)}")
    names: dict[int, set[str]] = {}
    for m in measurements:
        names.setdefault(m.location, set()).add(m.location_name)
    for location, found in sorted(names.items()):
        if len(found) > 1:
            problems.append(f"location {location} has more than one name: {sorted(found)}")
    keys = [key(m) for m in measurements]
    if len(keys) != len(set(keys)):
        problems.append("a location occurs twice in the file")
    for m in measurements:
        if m.value > MAX_VALUE:
            problems.append(f"location {m.location}, {period(m)}: {m.value} is above {MAX_VALUE} µg/m³")
    latest = max(m.year for m in measurements)
    if latest < today.year - MAX_AGE_OF_LATEST_YEAR:
        problems.append(f"the latest year is {latest}; expected {today.year - MAX_AGE_OF_LATEST_YEAR} or later")
    return problems


def compare_with_previous(count: int, previous: "Download | None") -> list[str]:
    """A file that holds fewer values than the last download needs a look before it is stored."""
    if previous and count < previous.value_count:
        return [f"{count} values, fewer than the {previous.value_count} of run {previous.run_id}; "
                "use --force if that is expected"]
    return []


def changes(older: dict[Key, Decimal], newer: dict[Key, Decimal]) -> list[str]:
    """Every value that changed, appeared or disappeared between two downloads, one line each."""
    lines = []
    for k in sorted(older.keys() | newer.keys(), key=lambda k: (k[0], k[1], k[2] or 0)):
        before, after = older.get(k), newer.get(k)
        if before == after:
            continue
        where = f"location {k[0]}, {k[1] if k[2] is None else f'{k[1]}-{k[2]}'}"
        if before is None:
            lines.append(f"{where}: new, {after}")
        elif after is None:
            lines.append(f"{where}: gone, was {before}")
        else:
            lines.append(f"{where}: {before} -> {after}")
    return lines


def period(m: Measurement) -> str:
    return str(m.year) if m.quarter is None else f"{m.year}-{m.quarter}"


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Download:
    run_id: int
    sha256: str
    value_count: int


def connect(url: str):
    import psycopg  # imported here, so a dry run and the tests need no database driver

    return psycopg.connect(url, autocommit=True)


def is_database_error(error: Exception) -> bool:
    return type(error).__module__.split(".")[0] == "psycopg"


def last_download(conn, area: int, kind: str) -> Download | None:
    row = conn.execute(
        "select d.run_id, d.sha256, (select count(*) from etl.man_measurement m where m.run_id = d.run_id) "
        "from etl.man_download d where d.area_number = %s and d.file_kind = %s "
        "order by d.run_id desc limit 1", (area, kind)).fetchone()
    return Download(row[0], row[1].strip(), row[2]) if row else None


def stored_values(conn, run_id: int) -> dict[Key, Decimal]:
    rows = conn.execute("select location, year, quarter, value from etl.man_measurement where run_id = %s",
                        (run_id,)).fetchall()
    return {(location, year, quarter): Decimal(str(value)) for location, year, quarter, value in rows}


def load(conn, run_id: int, area: int, kind: str, url: str, retrieved_at: datetime,
         sha256: str, content: bytes, measurements: list[Measurement]) -> None:
    """Store the file and its values in one transaction."""
    with conn.transaction():
        conn.execute(
            "insert into etl.man_download (run_id, area_number, file_kind, url, retrieved_at, sha256, content) "
            "values (%s, %s, %s, %s, %s, %s, %s)", (run_id, area, kind, url, retrieved_at, sha256, content))
        with conn.cursor() as cursor:
            cursor.executemany(
                "insert into etl.man_measurement (run_id, location, location_name, year, quarter, value) "
                "values (%s, %s, %s, %s, %s, %s)",
                [(run_id, m.location, m.location_name, m.year, m.quarter, m.value) for m in measurements])


def run(conn, path: Path, *, area: int, kind: str, url: str, retrieved_at: datetime,
        force: bool, today: date) -> int:
    """One run for one file. `conn` is None in a dry run. Returns the exit code."""
    source = f"man_{area}_{kind}"
    run_id = conn.execute("insert into etl.load_run (source) values (%s) returning run_id",
                          (source,)).fetchone()[0] if conn else None

    def record(status: str, message: str | None = None, fetched: int | None = None,
               loaded: int | None = None) -> None:
        if conn:
            conn.execute("update etl.load_run set status = %s, finished_at = now(), rows_fetched = %s, "
                         "rows_loaded = %s, message = %s where run_id = %s",
                         (status, fetched, loaded, message, run_id))

    try:
        content = path.read_bytes()
        sha256 = hashlib.sha256(content).hexdigest()
        log.info("%s: %d bytes, SHA-256 %s, retrieved %s", path.name, len(content), sha256[:12],
                 retrieved_at.isoformat(timespec="minutes"))
        previous = last_download(conn, area, kind) if conn else None
        if previous and previous.sha256 == sha256 and not force:
            message = f"same file as run {previous.run_id} (SHA-256 {sha256[:12]})"
            log.info("Skipped: %s", message)
            record("skipped", message)
            return 0

        measurements = parse(content.decode("utf-8-sig"))
        problems = validate(measurements, kind, today) + compare_with_previous(len(measurements), previous)
        if problems:
            raise ValidationError(problems)
        locations = {m.location for m in measurements}
        log.info("Validated: %d values, %d locations, %d to %d", len(measurements), len(locations),
                 min(m.year for m in measurements), max(m.year for m in measurements))

        if not conn:
            log.info("Dry run: nothing was stored")
            return 0
        older = stored_values(conn, previous.run_id) if previous else {}
        load(conn, run_id, area, kind, url, retrieved_at, sha256, content, measurements)
        record("succeeded", fetched=len(measurements), loaded=len(measurements))
        log.info("Loaded %d values in run %d", len(measurements), run_id)
        if previous:
            changed = changes(older, {key(m): m.value for m in measurements})
            log.info("Compared with run %d: %d value(s) differ", previous.run_id, len(changed))
            for line in changed[:MAX_LISTED]:
                log.info("Changed: %s", line)
            if len(changed) > MAX_LISTED:
                log.info("... and %d more", len(changed) - MAX_LISTED)
        return 0
    except (FormatError, ValidationError) as error:
        for problem in error.problems:
            log.error("Check failed: %s", problem)
        record("failed", "validation: " + "; ".join(error.problems))
        return 1
    except (OSError, UnicodeDecodeError) as error:
        log.error("Could not read %s: %s: %s", path, type(error).__name__, error)
        record("failed", f"file: {type(error).__name__}")
        return 2
    except Exception as error:
        if not is_database_error(error):
            raise
        log.error("Database: %s: %s", type(error).__name__, str(error).strip())
        try:   # the transaction was rolled back; say so in the run record if the database still answers
            record("failed", f"database: {type(error).__name__}")
        except Exception:
            pass
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Load a downloaded RIVM MAN file into PostgreSQL.")
    parser.add_argument("--file", type=Path, required=True, help="the file downloaded from man.rivm.nl")
    parser.add_argument("--kind", choices=sorted(URLS), required=True, help="annual or three-monthly values")
    parser.add_argument("--area", type=int, default=65, help="MAN area number (default 65, Veluwe Algemeen)")
    parser.add_argument("--retrieved-at", type=datetime.fromisoformat,
                        help="when the file was downloaded, e.g. 2026-10-09T20:15 (default: its modification time)")
    parser.add_argument("--dry-run", action="store_true", help="read and validate only; no database")
    parser.add_argument("--force", action="store_true", help="store even a file stored before, or one with fewer values")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)

    try:
        retrieved_at = args.retrieved_at or datetime.fromtimestamp(args.file.stat().st_mtime)
    except OSError as error:
        log.error("Could not read %s: %s", args.file, error)
        return 2
    if retrieved_at.tzinfo is None:
        retrieved_at = retrieved_at.astimezone()   # local time of this computer, stored with its offset

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
        return run(conn, args.file, area=args.area, kind=args.kind, url=URLS[args.kind].format(area=args.area),
                   retrieved_at=retrieved_at, force=args.force, today=date.today())
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
