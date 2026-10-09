"""Integration test: the whole pipeline against a real PostgreSQL database.

The unit tests check the rules with made-up rows. This test checks what only a real
database can show: that a second CBS edition is stored next to the first, that the
view returns the newest value, that a revision can be found with a query, and that a
run that fails a check stores nothing.

CBS is replaced by made-up editions, so the test needs no network and does not depend
on when CBS publishes. The database is real.

It runs only when TEST_DATABASE_URL is set, and only on a database whose name ends in
"_test": the test drops and recreates the schema "etl" in it. Example (PowerShell):

    docker exec stikstof-db psql -U pipeline -d stikstof -c "create database stikstof_test"
    $env:TEST_DATABASE_URL = "postgresql://pipeline:local-dev-only@127.0.0.1:5432/stikstof_test"
    python -m unittest discover -s pipeline/tests -p "test_integration_postgres.py" -v

Without TEST_DATABASE_URL it is skipped, so `unittest discover` still needs no database.
"""
from __future__ import annotations

import os
import sys
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest import mock
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cbs_livestock as pipeline  # noqa: E402

config = pipeline.config
COLUMNS = list(config.CBS_INDICATORS)
SCHEMA_FILE = Path(__file__).resolve().parents[1] / "sql" / "001_schema.sql"
TODAY = date(2026, 10, 9)
YEARS = range(2000, 2026)                      # 26 years x 2 regions = 52 rows, as in the real table
EDITION_A = datetime(2026, 3, 30, 2, 0)        # the edition CBS published on 30 March 2026
EDITION_B = datetime(2027, 3, 30, 2, 0)        # a made-up later edition
REVISED = (config.MUNICIPALITY_KEY, 2024, COLUMNS[1])   # the one value edition B changes
URL = os.environ.get("TEST_DATABASE_URL", "")


def make_rows(revise: bool = False) -> list[dict]:
    """Rows shaped like the CBS TypedDataSet, with one missing figure as in the real table."""
    rows = []
    for year in YEARS:
        for region, factor in ((config.MUNICIPALITY_KEY, 1), (config.PROVINCE_KEY, 50)):
            row = {"RegioS": region, "Perioden": f"{year}JJ00"}
            row.update({column: (100 + index + year - 2000) * factor for index, column in enumerate(COLUMNS)})
            if year == 2000:
                row[COLUMNS[-1]] = None                        # CBS gives no figure here
            if revise and (region, year, COLUMNS[1]) == REVISED:
                row[COLUMNS[1]] += 7                           # CBS revised this count
            rows.append(row)
    return rows


@unittest.skipUnless(URL, "set TEST_DATABASE_URL to run the PostgreSQL integration test")
class SecondEditionInPostgres(unittest.TestCase):
    """One scenario, in order: the test methods are numbered and share the database."""

    @classmethod
    def setUpClass(cls):
        name = urlparse(URL).path.lstrip("/")
        if not name.endswith("_test"):
            raise unittest.SkipTest(f"refusing to use database {name!r}: its name must end in '_test'")
        cls.conn = pipeline.connect(URL)
        cls.conn.execute("drop schema if exists etl cascade")
        cls.conn.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
        cls.values_per_edition = len(YEARS) * 2 * len(COLUMNS)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    # -- helpers -------------------------------------------------------------------

    def run_edition(self, modified: datetime, rows: list[dict], force: bool = False) -> int:
        """One pipeline run with CBS replaced by the given edition."""
        with mock.patch.object(pipeline, "fetch_edition", return_value=(modified, set(COLUMNS))), \
             mock.patch.object(pipeline, "fetch_rows", return_value=rows):
            return pipeline.run(self.conn, force=force, today=TODAY)

    def scalar(self, sql: str, params: tuple = ()):
        return self.conn.execute(sql, params).fetchone()[0]

    def last_run(self) -> tuple:
        return self.conn.execute(
            "select status, source_modified, rows_loaded, message from etl.load_run "
            "order by run_id desc limit 1").fetchone()

    def counts(self) -> tuple[int, int]:
        return (self.scalar("select count(*) from etl.livestock"),
                self.scalar("select count(*) from etl.cbs_livestock_raw"))

    # -- the scenario --------------------------------------------------------------

    def test_1_first_edition_is_loaded(self):
        self.assertEqual(self.run_edition(EDITION_A, make_rows()), 0)
        status, edition, loaded, _ = self.last_run()
        self.assertEqual((status, edition, loaded), ("succeeded", EDITION_A, self.values_per_edition))
        self.assertEqual(self.counts(), (self.values_per_edition, len(YEARS) * 2))
        self.assertEqual(self.scalar("select count(*) from etl.livestock where value is null"), 2)

    def test_2_same_edition_is_skipped(self):
        self.assertEqual(self.run_edition(EDITION_A, make_rows()), 0)
        self.assertEqual(self.last_run()[0], "skipped")
        self.assertEqual(self.counts()[0], self.values_per_edition)

    def test_3_second_edition_is_stored_next_to_the_first(self):
        self.assertEqual(self.run_edition(EDITION_B, make_rows(revise=True)), 0)
        self.assertEqual(self.last_run()[:2], ("succeeded", EDITION_B))
        self.assertEqual(self.counts()[0], 2 * self.values_per_edition)
        self.assertEqual(self.scalar("select count(distinct source_modified) from etl.livestock"), 2)

    def test_4_view_shows_the_newest_value_and_keeps_missing_figures_missing(self):
        region, year, column = REVISED
        indicator = pipeline.INDICATOR_IDS[column]
        latest = self.conn.execute(
            "select value, source_modified from etl.livestock_latest "
            "where region_code = %s and year = %s and indicator = %s", (region, year, indicator)).fetchone()
        self.assertEqual(latest, ((100 + 1 + year - 2000) + 7, EDITION_B))
        self.assertEqual(self.scalar("select count(*) from etl.livestock_latest"), self.values_per_edition)
        self.assertEqual(self.scalar("select count(*) from etl.livestock_latest where value is null"), 2)

    def test_5_revision_query_finds_exactly_the_changed_value(self):
        # The same query as number 4 in pipeline/sql/queries.sql.
        revisions = self.conn.execute(
            "select older.region_code, older.year, older.indicator, older.value, newer.value "
            "from etl.livestock older join etl.livestock newer using (region_code, year, indicator) "
            "where older.source_modified < newer.source_modified "
            "and older.value is distinct from newer.value").fetchall()
        region, year, column = REVISED
        old = 100 + 1 + year - 2000
        self.assertEqual(revisions, [(region, year, pipeline.INDICATOR_IDS[column], old, old + 7)])

    def test_6_force_replaces_and_does_not_double(self):
        self.assertEqual(self.run_edition(EDITION_B, make_rows(revise=True), force=True), 0)
        self.assertEqual(self.last_run()[0], "succeeded")
        self.assertEqual(self.counts()[0], 2 * self.values_per_edition)

    def test_7_failed_check_stores_nothing(self):
        before = self.counts()
        rows = make_rows(revise=True)
        rows[0][COLUMNS[0]] = -1                                  # a negative count
        self.assertEqual(self.run_edition(datetime(2028, 3, 30, 2, 0), rows), 1)
        status, _, loaded, message = self.last_run()
        self.assertEqual((status, loaded), ("failed", None))
        self.assertIn("negative", message)
        self.assertEqual(self.counts(), before)

    def test_8_fewer_rows_than_the_last_load_is_refused(self):
        before = self.counts()
        rows = [row for row in make_rows(revise=True) if row["Perioden"] != "2000JJ00"]
        self.assertEqual(self.run_edition(datetime(2028, 3, 30, 2, 0), rows), 1)
        status, _, _, message = self.last_run()
        self.assertEqual(status, "failed")
        self.assertIn("fewer rows", message)
        self.assertEqual(self.counts(), before)


if __name__ == "__main__":
    unittest.main()
