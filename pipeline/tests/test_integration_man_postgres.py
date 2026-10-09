"""Integration test: the MAN load against a real PostgreSQL database.

What only a real database can show: that a second download is stored next to the first, that
the same file is not stored twice, that the view returns the newest download, that the query
in pipeline/sql/man_queries.sql finds exactly the values that changed, and that a file that
fails a check stores nothing.

The files are made up, in the shape of the real downloads, so the test needs no network.

It runs only when TEST_DATABASE_URL is set, and only on a database whose name ends in
"_test": it drops and recreates the schema "etl" in it (as test_integration_postgres.py does).

    $env:TEST_DATABASE_URL = "postgresql://pipeline:local-dev-only@127.0.0.1:5432/stikstof_test"
    python -m unittest discover -s pipeline/tests -p "test_integration_man_postgres.py" -v
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import man_ammonia as man  # noqa: E402

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
URL = os.environ.get("TEST_DATABASE_URL", "")
TODAY = date(2026, 10, 9)
HEADER = "﻿Gebied;Locatienummer;Locatienaam;2023;2024;2025;\r\n"
FIRST = HEADER + ("Veluwe Algemeen;1;Het Leesten;2,0;1,7;2,6;\r\n"
                  "Veluwe Algemeen;5;Grote Ark;3,0;3,2;3,7;\r\n"
                  "Veluwe Algemeen;6;Kootwijk, De Houtbeek;;;;\r\n")
# The next yearly update: the provisional 2025 value of Grote Ark is revised from 3,7 to 3,9.
SECOND = FIRST.replace("3,2;3,7;", "3,2;3,9;")


def revision_query() -> str:
    """Query 2 of man_queries.sql, so the test checks the query that is documented."""
    text = (SQL_DIR / "man_queries.sql").read_text(encoding="utf-8")
    return text.split("-- 2.", 1)[1].split("-- 3.", 1)[0].split("\n", 1)[1]


@unittest.skipUnless(URL, "set TEST_DATABASE_URL to run the PostgreSQL integration test")
class TwoDownloadsInPostgres(unittest.TestCase):
    """One scenario, in order: the test methods are numbered and share the database."""

    @classmethod
    def setUpClass(cls):
        name = urlparse(URL).path.lstrip("/")
        if not name.endswith("_test"):
            raise unittest.SkipTest(f"refusing to use database {name!r}: its name must end in '_test'")
        cls.conn = man.connect(URL)
        cls.conn.execute("drop schema if exists etl cascade")
        for script in ("001_schema.sql", "002_man.sql"):
            cls.conn.execute((SQL_DIR / script).read_text(encoding="utf-8"))
        cls.folder = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls.folder.cleanup()

    def load(self, text: str, force: bool = False) -> int:
        path = Path(self.folder.name) / "man_65_jaar.csv"
        path.write_bytes(text.encode("utf-8"))
        return man.run(self.conn, path, area=65, kind="annual", url=man.URLS["annual"].format(area=65),
                       retrieved_at=datetime(2026, 10, 9, 20, 0, tzinfo=timezone.utc), force=force, today=TODAY)

    def scalar(self, sql: str):
        return self.conn.execute(sql).fetchone()[0]

    def last_run(self) -> tuple:
        return self.conn.execute("select status, rows_loaded, message from etl.load_run "
                                 "order by run_id desc limit 1").fetchone()

    def test_1_first_download_is_stored(self):
        self.assertEqual(self.load(FIRST), 0)
        self.assertEqual(self.last_run()[:2], ("succeeded", 6))
        self.assertEqual(self.scalar("select count(*) from etl.man_download"), 1)
        self.assertEqual(self.scalar("select count(*) from etl.man_measurement"), 6)
        self.assertEqual(self.scalar("select length(content) from etl.man_download"), len(FIRST.encode("utf-8")))

    def test_2_same_file_is_skipped(self):
        self.assertEqual(self.load(FIRST), 0)
        self.assertEqual(self.last_run()[0], "skipped")
        self.assertEqual(self.scalar("select count(*) from etl.man_download"), 1)

    def test_3_revised_file_is_stored_next_to_the_first(self):
        self.assertEqual(self.load(SECOND), 0)
        self.assertEqual(self.last_run()[0], "succeeded")
        self.assertEqual(self.scalar("select count(*) from etl.man_download"), 2)
        self.assertEqual(self.scalar("select count(*) from etl.man_measurement"), 12)

    def test_4_view_shows_the_newest_download(self):
        value = self.scalar("select value from etl.man_latest where location = 5 and year = 2025")
        self.assertEqual(Decimal(str(value)), Decimal("3.9"))
        self.assertEqual(self.scalar("select count(*) from etl.man_latest"), 6)

    def test_5_revision_query_finds_exactly_the_changed_value(self):
        rows = self.conn.execute(revision_query()).fetchall()
        self.assertEqual(len(rows), 1)
        area, kind, location, name, year, quarter, older, newer, change = rows[0]
        self.assertEqual((area, kind, location, year, quarter, change), (65, "annual", 5, 2025, None, "changed"))
        self.assertEqual((Decimal(str(older)), Decimal(str(newer))), (Decimal("3.7"), Decimal("3.9")))

    def test_6_failed_check_stores_nothing(self):
        self.assertEqual(self.load(SECOND.replace("3,9", "3.9")), 1)
        status, loaded, message = self.last_run()
        self.assertEqual((status, loaded), ("failed", None))
        self.assertIn("not a value", message)
        self.assertEqual(self.scalar("select count(*) from etl.man_download"), 2)

    def test_7_fewer_values_than_the_last_download_is_refused(self):
        fewer = SECOND.replace("Veluwe Algemeen;1;Het Leesten;2,0;1,7;2,6;\r\n", "")
        self.assertEqual(self.load(fewer), 1)
        self.assertIn("fewer than", self.last_run()[2])
        self.assertEqual(self.scalar("select count(*) from etl.man_download"), 2)


if __name__ == "__main__":
    unittest.main()
