-- Schema for the RIVM MAN ammonia measurements. Apply after 001_schema.sql; safe to run more than once.
--
-- A MAN file has no edition date. Every download is therefore kept with its SHA-256 and the
-- time it was retrieved; a download with the same SHA-256 as the last one is not stored again.
-- Every download is a complete snapshot of the file, so "the current values" are the values of
-- the newest download, and a revision is a difference between two downloads.
-- Runs are recorded in etl.load_run (source 'man_<area>_annual' or 'man_<area>_quarterly').

-- One row per stored download.
create table if not exists etl.man_download (
    run_id       bigint      primary key references etl.load_run (run_id),
    area_number  smallint    not null,                     -- 65 = Veluwe Algemeen
    file_kind    text        not null check (file_kind in ('annual', 'quarterly')),
    url          text        not null,
    retrieved_at timestamptz not null,
    sha256       char(64)    not null,
    content      bytea       not null                      -- the file exactly as downloaded
);

-- Every value of a stored download.
create table if not exists etl.man_measurement (
    run_id        bigint   not null references etl.man_download (run_id),
    location      smallint not null,                       -- Locatienummer, e.g. 5 = Grote Ark
    location_name text     not null,
    year          smallint not null check (year between 2000 and 2100),
    quarter       smallint check (quarter between 1 and 4),  -- null in the annual file; 1 = Feb-Apr ... 4 = Nov-Jan
    value         numeric  not null check (value >= 0)       -- µg/m³, exactly as in the file
);
-- One value per location and period in a download. quarter is null in the annual file, and
-- a primary key cannot hold null, so the key is a unique index that treats null as a value.
create unique index if not exists man_measurement_key
    on etl.man_measurement (run_id, location, year, quarter) nulls not distinct;

-- The values of the newest download of every area and file kind.
create or replace view etl.man_latest as
select d.area_number, d.file_kind, d.retrieved_at, m.*
from etl.man_measurement m
join etl.man_download d using (run_id)
where d.run_id = (select max(newer.run_id) from etl.man_download newer
                  where newer.area_number = d.area_number and newer.file_kind = d.file_kind);
