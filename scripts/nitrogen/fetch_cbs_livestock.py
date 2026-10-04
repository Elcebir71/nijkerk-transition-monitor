"""Fetch farm and livestock counts for Nijkerk (and Gelderland) from CBS StatLine.

Usage (from the repo root):
    python scripts/nitrogen/fetch_cbs_livestock.py

Writes data/nitrogen/processed/livestock_trend.json
"""
from __future__ import annotations

import json
import sys
from datetime import date

import requests

import config

TIMEOUT_S = 30


def get_all(url: str, params: dict | None = None) -> list[dict]:
    """GET an OData v3 collection and follow paging links."""
    rows: list[dict] = []
    while url:
        response = requests.get(url, params=params, timeout=TIMEOUT_S)
        response.raise_for_status()
        payload = response.json()
        rows.extend(payload.get("value", []))
        url = payload.get("odata.nextLink")
        params = None  # the next link already contains the query
    return rows


def check_columns() -> None:
    """Stop early if CBS renamed or removed a column we rely on."""
    published = {p.get("Key") for p in get_all(f"{config.CBS_BASE_URL}/DataProperties")}
    missing = [key for key in config.CBS_INDICATORS if key not in published]
    if missing:
        sys.exit(f"CBS table {config.CBS_TABLE_ID} no longer has column(s): {', '.join(missing)}")


def fetch_rows() -> list[dict]:
    regions = [config.MUNICIPALITY_KEY, config.PROVINCE_KEY]
    region_filter = " or ".join(f"(RegioS eq '{key}')" for key in regions)
    columns = ["RegioS", "Perioden", *config.CBS_INDICATORS]
    return get_all(
        f"{config.CBS_BASE_URL}/TypedDataSet",
        {"$filter": region_filter, "$select": ",".join(columns)},
    )


def build_output(rows: list[dict], table_info: dict) -> dict:
    """Reshape CBS rows into one year-aligned series per region and indicator."""
    names = {
        config.MUNICIPALITY_KEY.strip(): config.MUNICIPALITY_NAME,
        config.PROVINCE_KEY.strip(): config.PROVINCE_NAME,
    }
    years = sorted({int(row["Perioden"][:4]) for row in rows})
    by_region: dict[str, dict[int, dict]] = {key: {} for key in names}
    for row in rows:
        region = row["RegioS"].strip()
        if region in by_region:
            by_region[region][int(row["Perioden"][:4])] = row

    regions = {}
    for region, per_year in by_region.items():
        values = {
            meta["id"]: [per_year.get(year, {}).get(column) for year in years]
            for column, meta in config.CBS_INDICATORS.items()
        }
        regions[region] = {"name": names[region], "values": values}

    # Share of the municipality in the provincial total, in percent.
    municipality = regions[config.MUNICIPALITY_KEY.strip()]["values"]
    province = regions[config.PROVINCE_KEY.strip()]["values"]
    share = {
        indicator: [
            round(100 * m / p, 2) if m is not None and p else None
            for m, p in zip(series, province[indicator])
        ]
        for indicator, series in municipality.items()
    }

    return {
        "source": {
            "publisher": "CBS (Centraal Bureau voor de Statistiek)",
            "table_id": config.CBS_TABLE_ID,
            "table_title": table_info.get("Title"),
            "url": config.CBS_STATLINE_URL,
            "method": config.CBS_METHOD,
            "reference_date": config.CBS_REFERENCE_DATE,
            "table_modified": table_info.get("Modified"),
            "fetched_on": date.today().isoformat(),
            "licence": "Reuse allowed with attribution to CBS",
        },
        "caveats": config.CBS_CAVEATS,
        "trend_breaks": config.CBS_TREND_BREAKS,
        "events": config.CBS_EVENTS,
        "indicators": {
            meta["id"]: {"label_nl": meta["label_nl"], "unit": meta["unit"], "cbs_column": column}
            for column, meta in config.CBS_INDICATORS.items()
        },
        "years": years,
        "regions": regions,
        "municipality_share_of_province_pct": share,
    }


def main() -> None:
    check_columns()
    table_info = get_all(f"{config.CBS_BASE_URL}/TableInfos")[0]
    rows = fetch_rows()
    if not rows:
        sys.exit("CBS returned no rows. Check the region keys in config.py.")

    output = build_output(rows, table_info)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    target = config.PROCESSED_DIR / "livestock_trend.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    # Short summary so the numbers can be compared with StatLine by eye.
    nijkerk = output["regions"][config.MUNICIPALITY_KEY.strip()]["values"]
    first, last = output["years"][0], output["years"][-1]
    print(f"Wrote {target.relative_to(config.REPO_ROOT)} ({first}-{last})")
    for indicator, series in nijkerk.items():
        print(f"  {indicator:16} {first}: {series[0]}   {last}: {series[-1]}")


if __name__ == "__main__":
    main()
