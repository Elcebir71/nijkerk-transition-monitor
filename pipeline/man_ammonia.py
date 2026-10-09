"""Read the ammonia measurements of the RIVM MAN network (Meetnet Ammoniak in Natuurgebieden).

Step 1 of the MAN pipeline: turn one downloaded MAN file into one record per location and
period. Nothing is fetched and nothing is stored yet.

The files (man.rivm.nl, "Downloaden meetgegevens") are semicolon separated, use a decimal
comma, start with a byte order mark and have one row per location and one column per period:
"2025" in the annual file, "2025-3" in the three-monthly file. An empty cell means no value.
See docs/nitrogen-sources.md, section 6, for what the values mean and what they may be used for.

This module only checks the format. Whether the values are plausible is checked later.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

ID_COLUMNS = ("Gebied", "Locatienummer", "Locatienaam")
ANNUAL = re.compile(r"^(\d{4})$")
QUARTER = re.compile(r"^(\d{4})-([1-4])$")   # seasonal quarters: 1 = Feb-Apr ... 4 = Nov-Jan
VALUE = re.compile(r"^\d+(,\d+)?$")            # decimal comma, e.g. 3,7


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
