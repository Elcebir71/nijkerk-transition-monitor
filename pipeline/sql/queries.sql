-- Example questions the loaded data can answer. Read-only; run with psql:
--   psql ... -f pipeline/sql/queries.sql
-- All queries read etl.livestock_latest (the newest edition of every value),
-- except the one about revisions, which compares editions.

\echo
\echo '1. Nijkerk: first and last year per indicator, and the change in percent'
with nijkerk as (
    select indicator, year, value
    from etl.livestock_latest
    where region_code = 'GM0267' and value is not null
), span as (
    select indicator, min(year) as first_year, max(year) as last_year
    from nijkerk
    group by indicator
)
select s.indicator,
       s.first_year, f.value as first_value,
       s.last_year,  l.value as last_value,
       round(100.0 * (l.value - f.value) / nullif(f.value, 0), 1) as change_pct
from span s
join nijkerk f on f.indicator = s.indicator and f.year = s.first_year
join nijkerk l on l.indicator = s.indicator and l.year = s.last_year
order by s.indicator;

\echo
\echo '2. Share of Nijkerk in Gelderland, last five years, in percent'
select m.year,
       m.indicator,
       m.value as nijkerk,
       p.value as gelderland,
       round(100.0 * m.value / nullif(p.value, 0), 2) as share_pct
from etl.livestock_latest m
join etl.livestock_latest p
  on p.year = m.year and p.indicator = m.indicator and p.region_code = 'PV25'
where m.region_code = 'GM0267'
  and m.indicator in ('cattle_total', 'goats_total')
  and m.year > (select max(year) - 5 from etl.livestock_latest)
order by m.indicator, m.year;

\echo
\echo '3. Nijkerk: the five largest changes from one year to the next, per indicator'
with steps as (
    select indicator, year, value,
           lag(value) over (partition by indicator order by year) as previous_value
    from etl.livestock_latest
    where region_code = 'GM0267'
), ranked as (
    select indicator, year, previous_value, value,
           round(100.0 * (value - previous_value) / nullif(previous_value, 0), 1) as change_pct,
           row_number() over (partition by indicator
                              order by abs(1.0 * (value - previous_value) / nullif(previous_value, 0)) desc nulls last) as position
    from steps
    where previous_value is not null and value is not null
)
select indicator, year, previous_value, value, change_pct
from ranked
where position <= 5 and indicator in ('farms_total', 'chickens_total')
order by indicator, position;

\echo
\echo '4. Values that CBS revised between two editions (empty while only one edition is loaded)'
select older.region_code, older.year, older.indicator,
       older.source_modified as old_edition, older.value as old_value,
       newer.source_modified as new_edition, newer.value as new_value
from etl.livestock older
join etl.livestock newer using (region_code, year, indicator)
where older.source_modified < newer.source_modified
  and older.value is distinct from newer.value
order by older.region_code, older.indicator, older.year;

\echo
\echo '5. The runs of the pipeline'
select run_id, status, started_at::timestamp(0) as started, source_modified as edition,
       rows_fetched, rows_loaded, message
from etl.load_run
order by run_id;
