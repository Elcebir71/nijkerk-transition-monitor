-- Queries on the MAN tables (pipeline/sql/002_man.sql).

-- 1. Every download: when, which file, and its SHA-256.
select run_id, area_number, file_kind, retrieved_at, left(sha256, 12) as sha256, length(content) as bytes
from etl.man_download
order by run_id;

-- 2. What changed between the last two downloads of the same file:
--    a changed value, a value that is new, or a value that is gone.
with ranked as (
    select run_id, area_number, file_kind,
           row_number() over (partition by area_number, file_kind order by run_id desc) as n
    from etl.man_download
),
pairs as (
    select newer.area_number, newer.file_kind, older.run_id as older_run, newer.run_id as newer_run
    from ranked newer join ranked older using (area_number, file_kind)
    where newer.n = 1 and older.n = 2
),
older as (select p.*, m.location, m.location_name, m.year, m.quarter, m.value
          from pairs p join etl.man_measurement m on m.run_id = p.older_run),
newer as (select p.*, m.location, m.location_name, m.year, m.quarter, m.value
          from pairs p join etl.man_measurement m on m.run_id = p.newer_run)
select coalesce(n.area_number, o.area_number) as area_number,
       coalesce(n.file_kind, o.file_kind)     as file_kind,
       coalesce(n.location, o.location)       as location,
       coalesce(n.location_name, o.location_name) as location_name,
       coalesce(n.year, o.year)               as year,
       coalesce(n.quarter, o.quarter)         as quarter,
       o.value as older_value, n.value as newer_value,
       case when o.value is null then 'new'
            when n.value is null then 'gone'
            else 'changed' end                as change
from older o
full join newer n
  on  n.area_number = o.area_number and n.file_kind = o.file_kind
  and n.location = o.location and n.year = o.year
  and n.quarter is not distinct from o.quarter
where o.value is distinct from n.value
order by area_number, file_kind, location, year, quarter;

-- 3. The current annual values of one location (5 = Grote Ark, area 65).
select year, value
from etl.man_latest
where area_number = 65 and file_kind = 'annual' and location = 5
order by year;
