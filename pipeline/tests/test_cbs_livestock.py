"""Tests for the checks of pipeline/cbs_livestock.py. Made-up rows; no network, no database.

Run from the repo root:
    python -m unittest discover -s pipeline/tests
"""
from __future__ import annotations

import sys
import unittest
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cbs_livestock as pipeline  # noqa: E402

config = pipeline.config
COLUMNS = list(config.CBS_INDICATORS)
TODAY = date(2026, 10, 7)


def make_rows(years=range(2022, 2026)) -> list[dict]:
    """Rows shaped like the CBS TypedDataSet: region keys padded to 6 characters, one row per year."""
    rows = []
    for year in years:
        for region, factor in ((config.MUNICIPALITY_KEY, 1), (config.PROVINCE_KEY, 50)):
            row = {"RegioS": region, "Perioden": f"{year}JJ00"}
            row.update({column: (100 + index + year - 2000) * factor for index, column in enumerate(COLUMNS)})
            rows.append(row)
    return rows


def problems_of(rows, published=None, today=TODAY) -> list[str]:
    try:
        pipeline.validate(rows, set(COLUMNS) if published is None else published, today)
    except pipeline.ValidationError as error:
        return error.problems
    return []


class ValidRows(unittest.TestCase):
    def test_good_rows_pass_and_come_back_in_long_form(self):
        clean = pipeline.validate(make_rows(), set(COLUMNS), TODAY)
        self.assertEqual(list(clean.columns), ["region_code", "year", "indicator", "value"])
        self.assertEqual(len(clean), 4 * 2 * len(COLUMNS))
        self.assertEqual(set(clean["region_code"]), {"GM0267", "PV25"})   # padding removed
        self.assertEqual(set(clean["indicator"]), set(pipeline.INDICATOR_IDS.values()))

    def test_a_missing_figure_stays_missing(self):
        rows = make_rows()
        rows[0][COLUMNS[0]] = None
        clean = pipeline.validate(rows, set(COLUMNS), TODAY)
        self.assertEqual(int(clean["value"].isna().sum()), 1)
        self.assertEqual(str(clean["value"].dtype), "Int64")

    def test_whole_numbers_given_as_decimals_are_accepted(self):
        rows = make_rows()
        rows[0][COLUMNS[0]] = 120.0
        self.assertEqual(problems_of(rows), [])


class FailedChecks(unittest.TestCase):
    def assert_problem(self, problems: list[str], text: str):
        self.assertTrue(any(text in problem for problem in problems), f"{text!r} not in {problems}")

    def test_no_rows(self):
        self.assert_problem(problems_of([]), "no rows")

    def test_column_removed_from_the_table(self):
        self.assert_problem(problems_of(make_rows(), published=set(COLUMNS[1:])), "no longer has column")

    def test_column_missing_in_the_rows(self):
        rows = [{key: value for key, value in row.items() if key != COLUMNS[0]} for row in make_rows()]
        self.assert_problem(problems_of(rows), "rows lack column")

    def test_period_that_is_not_a_year(self):
        rows = make_rows()
        rows[0]["Perioden"] = "2025KW01"
        self.assert_problem(problems_of(rows), "not a whole year")

    def test_region_missing(self):
        rows = [row for row in make_rows() if row["RegioS"] != config.PROVINCE_KEY]
        self.assert_problem(problems_of(rows), "no rows for region PV25")

    def test_region_not_asked_for(self):
        rows = make_rows() + [{**make_rows()[0], "RegioS": "GM0999"}]
        self.assert_problem(problems_of(rows), "not asked for")

    def test_duplicate_row(self):
        rows = make_rows() + [make_rows()[0]]
        self.assert_problem(problems_of(rows), "more than one row")

    def test_gap_in_the_years(self):
        rows = [row for row in make_rows() if not row["Perioden"].startswith("2023")]
        self.assert_problem(problems_of(rows), "missing in the series: 2023")

    def test_regions_cover_different_years(self):
        rows = [row for row in make_rows()
                if not (row["Perioden"].startswith("2025") and row["RegioS"] == config.PROVINCE_KEY)]
        self.assert_problem(problems_of(rows), "do not cover the same years")

    def test_latest_year_too_old(self):
        self.assert_problem(problems_of(make_rows(range(2018, 2022))), "latest year is 2021")

    def test_text_instead_of_a_number(self):
        rows = make_rows()
        rows[0][COLUMNS[0]] = "x"
        self.assert_problem(problems_of(rows), "not a number")

    def test_count_that_is_not_whole(self):
        rows = make_rows()
        rows[0][COLUMNS[0]] = 12.5
        self.assert_problem(problems_of(rows), "not a whole number")

    def test_negative_count(self):
        rows = make_rows()
        rows[0][COLUMNS[0]] = -1
        self.assert_problem(problems_of(rows), "negative")

    def test_indicator_without_any_value(self):
        rows = make_rows()
        for row in rows:
            if row["RegioS"] == config.MUNICIPALITY_KEY:
                row[COLUMNS[2]] = None
        self.assert_problem(problems_of(rows), "no value in any year")

    def test_municipality_above_province(self):
        rows = make_rows()
        rows[0][COLUMNS[0]] = 10**9
        self.assert_problem(problems_of(rows), "above PV25")

    def test_all_problems_are_listed_together(self):
        rows = make_rows()
        rows[0][COLUMNS[0]] = -1
        rows[1][COLUMNS[1]] = 12.5
        self.assertGreaterEqual(len(problems_of(rows)), 2)


class ComparedWithLastRun(unittest.TestCase):
    PREVIOUS = {"run_id": 3, "source_modified": datetime(2026, 3, 30, 2), "rows_fetched": 52}

    def test_first_run_has_nothing_to_compare(self):
        self.assertEqual(pipeline.compare_with_previous(52, None), [])

    def test_same_or_more_rows_is_fine(self):
        self.assertEqual(pipeline.compare_with_previous(52, self.PREVIOUS), [])
        self.assertEqual(pipeline.compare_with_previous(54, self.PREVIOUS), [])

    def test_fewer_rows_is_a_problem(self):
        problems = pipeline.compare_with_previous(50, self.PREVIOUS)
        self.assertEqual(len(problems), 1)
        self.assertIn("50 now, 52 then", problems[0])


if __name__ == "__main__":
    unittest.main()
