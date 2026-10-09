# ETL pipeline: CBS livestock counts into PostgreSQL

As of 9 October 2026. A small pipeline next to the Stikstofmonitor: it
fetches the CBS livestock table for Nijkerk and Gelderland, checks the rows
and stores them in PostgreSQL, with the edition of the table they came
from.

It is separate from `nitrogen.html`. It never changes the page or its data
files; the page is still refreshed by hand, after comparing.

## Why

The page shows one state of a source. CBS recalculates earlier years, and
the page cannot say what a figure was before. The database keeps every
edition that was loaded, so "what changed between two editions" is a query.

## What it does

| Step | What happens |
|---|---|
| Extract | Asks CBS StatLine (`80781ned`) for the "Modified" date of the table and for the rows of Nijkerk and Gelderland. An edition that was loaded before is skipped. |
| Validate | Checks the rows before anything is stored. All failed checks are listed; one is enough to stop the run. |
| Load | Stores the rows as CBS gave them and the clean values, in one transaction. |

Every run is recorded in `etl.load_run`, also a failed or skipped one.

### Checks

- the columns the pipeline relies on are still in the table and in the rows
- there are rows, for both regions, and for no other region
- every period is a whole year; no year occurs twice for a region
- no gaps in the years; both regions cover the same years
- the latest year is not older than two years ago
- every value is a whole number of zero or more, or missing
- no indicator is empty for a whole region
- Nijkerk never exceeds Gelderland
- not fewer rows than in the last loaded run

A missing value stays missing: CBS gives no figure when it is unknown,
unreliable or confidential.

### Tables (schema `etl`)

| Table | Holds |
|---|---|
| `load_run` | One row per run: status, edition, rows fetched and loaded, the reason of a failure or skip |
| `cbs_livestock_raw` | The rows as CBS returned them (JSON), per run |
| `livestock` | One value per region, year, indicator and edition. A new edition adds rows and replaces nothing |
| `livestock_latest` (view) | The newest edition of every value |

## Running it

A local database with Docker (the password is for this local database
only, which listens on 127.0.0.1):

```powershell
docker run --name stikstof-db -e POSTGRES_USER=pipeline -e POSTGRES_PASSWORD=local-dev-only -e POSTGRES_DB=stikstof -p 127.0.0.1:5432:5432 -v stikstof-db-data:/var/lib/postgresql/data -d postgres:16
docker cp pipeline/sql/001_schema.sql stikstof-db:/tmp/001_schema.sql
docker exec stikstof-db psql -U pipeline -d stikstof -v ON_ERROR_STOP=1 -f /tmp/001_schema.sql
```

The pipeline, from the repo root:

```powershell
python -m pip install -r pipeline/requirements.txt
python pipeline/cbs_livestock.py --dry-run
$env:DATABASE_URL = "postgresql://pipeline:local-dev-only@127.0.0.1:5432/stikstof"
python pipeline/cbs_livestock.py
```

| Option | Meaning |
|---|---|
| `--dry-run` | Fetch and validate only; no database needed |
| `--force` | Load even when this edition was loaded before; its values are replaced, not doubled |

Exit code: 0 loaded, skipped or dry run passed; 1 the data failed a check;
2 CBS or the database could not be reached.

Example queries are in [`sql/queries.sql`](sql/queries.sql). The tests of
the checks need no network and no database:

```powershell
python -m unittest discover -s pipeline/tests
```
`tests/test_integration_postgres.py` runs the whole pipeline against a real
PostgreSQL database, with made-up CBS editions. It is skipped unless
`TEST_DATABASE_URL` is set, and it only runs on a database whose name ends
in `_test`, because it recreates the schema `etl`. How to run it is at the
top of the file.

## Does the page still match the database?

`compare_with_page.py` compares `data/nitrogen/processed/livestock_trend.json`,
from which the page is built, with the newest edition in the database. It
reads both and changes neither.

    python pipeline/compare_with_page.py

It lists every difference: another edition, a value that differs, a figure
on one side only, a year on one side only. Exit code: 0 they agree, 1 they
differ, 2 the database or the file could not be read. When CBS revises its
figures, the database gets the new edition and this check says that the
page has not followed yet.

## Reading the figures

The largest jumps in the series are not changes on the farms alone. The
number of farms drops in 2016 because CBS changed which farms count, and
the chickens of 2003 were counted during the avian influenza outbreak.
These breaks and events are listed in `scripts/nitrogen/config.py`
(`CBS_TREND_BREAKS`, `CBS_EVENTS`); a change across such a year needs that
note.

## Limits

- **A change without a new date is not seen.** The pipeline decides by the
  "Modified" date of the table. Values that CBS would change without a new
  date are loaded only with `--force`.
- **Two regions, six indicators.** Only what the page uses.
- **Animals are counted at the farm's main address**, not where they are
  kept; the same caveat as on the page.
- **A failed run tells nobody by itself.** It ends with exit code 1 or 2
  and a row in `etl.load_run`; someone has to look.

## What was shown to work, and what was not

Shown on 7 October 2026, on the author's computer with PostgreSQL 16 in
Docker: the 22 tests; a dry run against CBS (52 rows, 312 values, the same
figures as on the page); a first load (312 values in run 1); a second run
that skipped the same edition; the example queries; the container image
built and run against that database, where `--force` loaded the same
edition again and the table still held 312 values.

Shown on 9 October 2026 against PostgreSQL 16 with the real driver, with
made-up CBS editions (`tests/test_integration_postgres.py`, 8 tests): a
second edition stored next to the first, 624 values with none replaced;
the view `livestock_latest` returning the newer value; the revision query
finding exactly the one changed value; `--force` replacing instead of
doubling; a run with a negative count and a run with fewer rows both
failing and storing nothing. A database error was shown only with a
stand-in for the driver.

On 9 October 2026 `compare_with_page.py` found the page and the database in
agreement: 312 values, edition of 30 March 2026. The page's figures and the
pipeline's come from two separate requests to CBS, so the two routes give
the same result.

Not shown: a real second edition from CBS (the table is updated about once
a year), and a scheduled run. The container image is in
`docker/etl-pipeline/`; it has run on the author's computer only.
