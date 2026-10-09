"""Tests for pipeline/compare_with_page.py. No network, no database.

Run from the repo root:
    python -m unittest discover -s pipeline/tests
"""
from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compare_with_page as check  # noqa: E402

EDITION = datetime(2026, 3, 30, 2, 0)


def values() -> dict:
    return {("GM0267", 2024, "cattle_total"): 12216, ("GM0267", 2025, "cattle_total"): 10990,
            ("GM0267", 2025, "goats_total"): None, ("PV25", 2025, "cattle_total"): 840000}


class Compare(unittest.TestCase):
    def test_same_page_and_database_agree(self):
        self.assertEqual(check.compare((EDITION, values()), (EDITION, values())), [])

    def test_a_newer_edition_in_the_database_is_reported(self):
        differences = check.compare((EDITION, values()), (datetime(2027, 3, 30, 2, 0), values()))
        self.assertEqual(len(differences), 1)
        self.assertIn("edition", differences[0])

    def test_a_revised_value_is_reported_with_both_figures(self):
        database = values()
        database[("GM0267", 2024, "cattle_total")] = 12300
        self.assertEqual(check.compare((EDITION, values()), (EDITION, database)),
                         ["GM0267 2024 cattle_total: page 12216, database 12300"])

    def test_a_figure_on_one_side_only_is_a_difference(self):
        database = values()
        database[("GM0267", 2025, "goats_total")] = 7000
        self.assertEqual(check.compare((EDITION, values()), (EDITION, database)),
                         ["GM0267 2025 goats_total: page no figure, database 7000"])

    def test_a_year_in_the_database_but_not_on_the_page_is_reported(self):
        database = values()
        database[("GM0267", 2026, "cattle_total")] = 10500
        self.assertEqual(check.compare((EDITION, values()), (EDITION, database)),
                         ["GM0267 2026 cattle_total: in the database (10500), not on the page"])

    def test_an_empty_database_says_what_to_do(self):
        differences = check.compare((EDITION, values()), (None, {}))
        self.assertEqual(len(differences), 1)
        self.assertIn("cbs_livestock.py", differences[0])


class PageFile(unittest.TestCase):
    def test_the_real_page_file_can_be_read(self):
        edition, page = check.page_values()
        regions = {key[0] for key in page}
        indicators = {key[2] for key in page}
        years = {key[1] for key in page}
        self.assertEqual(regions, {"GM0267", "PV25"})
        self.assertEqual(len(page), len(regions) * len(indicators) * len(years))
        self.assertIsInstance(edition, datetime)


if __name__ == "__main__":
    unittest.main()
