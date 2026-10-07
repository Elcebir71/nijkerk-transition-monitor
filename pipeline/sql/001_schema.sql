-- Schema of the ETL pipeline. Apply with psql; safe to run more than once.
--
-- The pipeline is separate from nitrogen.html: it stores what a source said at every
-- load, so two editions can be compared with a query. It never changes the page.

create schema if not exists etl;

-- One row per run of the pipeline for one source.
create table if not exists etl.load_run (
    run_id          bigint generated always as identity primary key,
    source          text        not null,                 -- e.g. 'cbs_80781ned'
    started_at      timestamptz not null default now(),
    finished_at     timestamptz,
    status          text        not null default 'running'
                    check (status in ('running', 'succeeded', 'failed', 'skipped')),
    source_modified timestamp,                            -- edition of the source, as the source states it
    rows_fetched    integer,
    rows_loaded     integer,
    message         text                                  -- why a run failed or was skipped
);

-- Raw: every row as CBS returned it, unchanged, kept per run.
create table if not exists etl.cbs_livestock_raw (
    run_id     bigint not null references etl.load_run (run_id),
    region_key text   not null,                           -- 'GM0267', 'PV25'
    period_key text   not null,                           -- '2025JJ00'
    payload    jsonb  not null,
    primary key (run_id, region_key, period_key)
);

-- Clean: one value per region, year, indicator and edition of the CBS table.
-- A new edition adds rows and replaces nothing, so revisions stay visible.
create table if not exists etl.livestock (
    region_code     text      not null,
    year            smallint  not null check (year between 1980 and 2100),
    indicator       text      not null,                   -- 'farms_total', 'cattle_total', ...
    value           integer   check (value >= 0),         -- null: CBS gives no figure (unknown or confidential)
    source_modified timestamp not null,
    run_id          bigint    not null references etl.load_run (run_id),
    primary key (region_code, year, indicator, source_modified)
);

-- The newest edition of every value.
create or replace view etl.livestock_latest as
select distinct on (region_code, year, indicator)
       region_code, year, indicator, value, source_modified, run_id
from etl.livestock
order by region_code, year, indicator, source_modified desc;
