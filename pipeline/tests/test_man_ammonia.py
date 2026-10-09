"""Tests for pipeline/man_ammonia.py. No network, no database.

Run from the repo root:
    python -m unittest discover -s pipeline/tests

The made-up files below copy the shape of the real downloads. The real files are not in the
repository; if they are in data/nitrogen/raw/ (see the file names below), they are checked too.
"""
from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import man_ammonia as man  # noqa: E402

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "nitrogen" / "raw"
ANNUAL_FILE = RAW_DIR / "man_65_jaar.csv"
QUARTER_FILE = RAW_DIR / "man_65_3_maanden.csv"

ANNUAL = ("﻿Gebied;Locatienummer;Locatienaam;2023;2024;2025;\r\n"
          "Veluwe Algemeen;5;Grote Ark;3,0;3,2;3,7;\r\n"
          "Veluwe Algemeen;10;Kootwijk, de Houtbeek 4;;2,9;3,1;\r\n"
          "Veluwe Algemeen;6;Kootwijk, De Houtbeek;;;;\r\n")
QUARTERS = ("﻿Gebied;Locatienummer;Locatienaam;2025-1;2025-2;2025-3;2025-4;\r\n"
            "Veluwe Algemeen;5;Grote Ark;3,8;4,0;3,9;;\r\n")


class Parse(unittest.TestCase):
    def test_annual_file_gives_one_record_per_value(self):
        records = man.parse(ANNUAL)
        self.assertEqual(len(records), 5)
        self.assertEqual(records[0], man.Measurement("Veluwe Algemeen", 5, "Grote Ark", 2023, None, Decimal("3.0")))

    def test_decimal_comma_becomes_an_exact_decimal(self):
        values = {(r.location, r.year): r.value for r in man.parse(ANNUAL)}
        self.assertEqual(values[(5, 2025)], Decimal("3.7"))

    def test_empty_cells_give_no_record(self):
        locations = {r.location for r in man.parse(ANNUAL)}
        self.assertNotIn(6, locations)
        self.assertNotIn((10, 2023), {(r.location, r.year) for r in man.parse(ANNUAL)})

    def test_comma_in_a_location_name_is_kept(self):
        names = {r.location: r.location_name for r in man.parse(ANNUAL)}
        self.assertEqual(names[10], "Kootwijk, de Houtbeek 4")

    def test_quarterly_file_keeps_the_quarter(self):
        records = man.parse(QUARTERS)
        self.assertEqual([(r.year, r.quarter, r.value) for r in records],
                         [(2025, 1, Decimal("3.8")), (2025, 2, Decimal("4.0")), (2025, 3, Decimal("3.9"))])


class FormatProblems(unittest.TestCase):
    def assert_problem(self, text: str, expected: str):
        with self.assertRaises(man.FormatError) as caught:
            man.parse(text)
        self.assertTrue(any(expected in problem for problem in caught.exception.problems),
                        caught.exception.problems)

    def test_empty_file(self):
        self.assert_problem("", "empty")

    def test_unexpected_first_columns(self):
        self.assert_problem("Area;Number;Name;2025;\r\n", "first columns")

    def test_a_column_that_is_not_a_period(self):
        self.assert_problem("Gebied;Locatienummer;Locatienaam;2025;Opmerking;\r\n", "'Opmerking'")

    def test_mixed_annual_and_quarterly_columns(self):
        self.assert_problem("Gebied;Locatienummer;Locatienaam;2025;2025-1;\r\n", "mixes")

    def test_a_decimal_point_is_refused(self):
        # A point could be a thousands separator; the files use a comma.
        self.assert_problem(ANNUAL.replace("3,7", "3.7"), "'3.7' is not a value")

    def test_a_negative_value_is_refused(self):
        self.assert_problem(ANNUAL.replace("3,7", "-3,7"), "'-3,7' is not a value")

    def test_more_cells_than_columns(self):
        self.assert_problem(ANNUAL.replace("3,7;", "3,7;4,1;"), "cells for")

    def test_every_problem_is_listed(self):
        text = ANNUAL.replace("3,7", "x").replace("3,2", "y")
        with self.assertRaises(man.FormatError) as caught:
            man.parse(text)
        self.assertEqual(len(caught.exception.problems), 2)


@unittest.skipUnless(ANNUAL_FILE.exists() and QUARTER_FILE.exists(),
                     f"put the MAN downloads of area 65 in {RAW_DIR} to check the real files")
class RealFiles(unittest.TestCase):
    def test_annual_file_of_area_65(self):
        records = man.read_file(ANNUAL_FILE)
        grote_ark = {r.year: r.value for r in records if r.location == 5}
        self.assertEqual(grote_ark[2017], Decimal("4.5"))
        self.assertEqual(grote_ark[2025], Decimal("3.7"))
        self.assertEqual({r.location for r in records}, {1, 2, 3, 4, 5, 10, 11})   # 6 has no values
        self.assertTrue(all(r.quarter is None for r in records))

    def test_quarterly_file_of_area_65(self):
        records = man.read_file(QUARTER_FILE)
        self.assertEqual(max((r.year, r.quarter) for r in records), (2025, 3))
        self.assertTrue(all(r.quarter in (1, 2, 3, 4) for r in records))


if __name__ == "__main__":
    unittest.main()
