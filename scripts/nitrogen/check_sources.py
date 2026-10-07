"""Check whether the sources behind the Stikstofmonitor have changed since the last look.

Usage (from the repo root):
    python scripts/nitrogen/check_sources.py                 compare with the saved state, print a report
    python scripts/nitrogen/check_sources.py --write-state   save what the sources say now as the new state
    python scripts/nitrogen/check_sources.py --issue         also open a GitHub issue when something changed

What it does: it asks each source a small question (a date, a count, a short list),
turns the answer into a "fingerprint" and compares that with the fingerprint saved in
data/nitrogen/source_state.json. It downloads no data for the page and changes nothing
on the page. Refreshing the page stays a decision made by hand, after comparing.

What it cannot see: a change in the shapes of a layer when the attributes stay the
same, and the sources that have no machine-readable signal. Those are listed as
"by hand", with the date they were last looked at.

Options:
    --state PATH_OR_URL   where to read the saved state (default: the file in this repo).
                          A URL lets a scheduled job read the state from GitHub.
    --issue               open a GitHub issue when a source changed, could not be read, or
                          a check by hand is due. Needs the environment variables
                          GITHUB_TOKEN and GITHUB_REPOSITORY (owner/name).
    --manual-days N       remind of a check by hand after N days (default 120).

Exit code: 0 nothing to report, 1 something to report, 2 the state could not be read.

Needs only the `requests` package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

import requests

import config

TIMEOUT_S = 120
STATE_PATH = config.REPO_ROOT / "data" / "nitrogen" / "source_state.json"
ISSUE_TITLE = "Stikstofmonitor: a source changed or needs a look"
ISSUE_LABEL = "source-check"
GITHUB_API = "https://api.github.com"

# The map area of the page in EPSG:28992: the bounding box of Nijkerk plus 15 km. The same box as in
# inspect_aerius.py; fetch_aerius_habitats.py computes it from the municipal boundary.
MAP_BBOX_RD = "140411,449181,186929,490103,urn:ogc:def:crs:EPSG::28992"
HABITAT_FIELDS = ("natura2000_area_name", "habitat_type_name", "critical_deposition", "coverage")

# Sources without a signal a script can read. `how` says what to look at.
MANUAL_SOURCES = {
    "emissieregistratie": {
        "label": "Emissieregistratie: NH3 and NOx per municipality",
        "how": "Open https://www.emissieregistratie.nl/data/data-export and see whether a newer series than "
               "the one named on the page is offered. The export is made by hand.",
    },
    "aerius_monitor": {
        "label": "AERIUS Monitor: share of the Veluwe not above the KDW",
        "how": "Open AERIUS Monitor, chart 'Ontwikkeling stikstofbelasting', area Veluwe, and see whether a newer "
               "edition than the one named on the page is offered. The figure is read from the screen.",
    },
}


class CheckError(Exception):
    """A source could not be read. The message goes into the report."""


def sha256_of(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def get(url: str, **kwargs) -> requests.Response:
    try:
        response = requests.get(url, timeout=TIMEOUT_S, **kwargs)
    except requests.RequestException as error:
        raise CheckError(f"no answer: {error}") from error
    if response.status_code != 200:
        raise CheckError(f"HTTP {response.status_code}")
    return response


# ---------------------------------------------------------------------------
# One function per source. Each returns a small dict: the fingerprint.
# ---------------------------------------------------------------------------

def check_cbs_livestock() -> dict:
    """CBS states when the table was last modified."""
    rows = get(f"{config.CBS_BASE_URL}/TableInfos", params={"$format": "json"}).json().get("value", [])
    if not rows:
        raise CheckError("TableInfos is empty")
    return {"modified": rows[0].get("Modified"), "period": rows[0].get("Period")}


def head_or_none(url: str) -> dict | None:
    """Size and date of a file, without downloading it. None when the file is not there."""
    try:
        response = requests.head(url, timeout=TIMEOUT_S, allow_redirects=True)
    except requests.RequestException as error:
        raise CheckError(f"no answer: {error}") from error
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        raise CheckError(f"HTTP {response.status_code} for {url}")
    return {"bytes": response.headers.get("Content-Length"), "last_modified": response.headers.get("Last-Modified")}


def check_rivm_gdn() -> dict:
    """The file of the year on the page, and whether a file for the next year has appeared."""
    year = config.RIVM_GDN_YEAR
    current = head_or_none(f"{config.RIVM_GDN_BASE_URL}/depo_NTOT_{year}.zip")
    if current is None:
        raise CheckError(f"the file for {year}, which the page uses, is not there any more")
    following = head_or_none(f"{config.RIVM_GDN_BASE_URL}/depo_NTOT_{year + 1}.zip")
    return {"year_on_page": year, "file": current, "next_year_available": following is not None}


def wfs_count(base_url: str, layer: str) -> int:
    """Number of features in a WFS layer, without downloading them."""
    params = {"service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": layer, "resultType": "hits"}
    text = get(base_url, params=params).text
    match = re.search(r'numberMatched="(\d+)"', text)
    if not match:
        raise CheckError("the service did not give a feature count")
    return int(match.group(1))


def check_natura2000() -> dict:
    return {"features": wfs_count(config.PDOK_NATURA2000_WFS, config.PDOK_NATURA2000_LAYER)}


def check_municipal_boundaries() -> dict:
    return {"features": wfs_count(config.PDOK_MUNICIPALITY_WFS, config.PDOK_MUNICIPALITY_LAYER)}


def habitat_rows(extra_params: dict) -> list[list[str]]:
    """Area, habitat type, KDW and coverage of the habitat records, without the shapes (those are over 100 MB)."""
    params = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": config.AERIUS_HABITAT_LAYER,
        "outputFormat": "application/json", "propertyName": ",".join(HABITAT_FIELDS), **extra_params,
    }
    response = get(config.AERIUS_WFS, params=params)
    if "json" not in response.headers.get("Content-Type", ""):
        raise CheckError("the service did not return JSON: " + response.text[:120].replace("\n", " "))
    features = response.json().get("features", [])
    if not features:
        raise CheckError("the layer came back empty")
    return sorted([str(feature["properties"].get(field)) for field in HABITAT_FIELDS] for feature in features)


def check_aerius_habitats() -> dict:
    """Two questions: did the layer change anywhere, and did it change in the map area of the page?

    The second asks for the same box as fetch_aerius_habitats.py, so its numbers can be laid next to
    the page: the count for the Veluwe is the number of habitat types the page reports.
    """
    everywhere = habitat_rows({})
    in_map_area = habitat_rows({"srsName": MAP_BBOX_RD.split(",", 4)[4], "bbox": MAP_BBOX_RD})
    return {
        "records_netherlands": len(everywhere),
        "hash_netherlands": sha256_of(everywhere),
        "records_in_map_area": len(in_map_area),
        "hash_in_map_area": sha256_of(in_map_area),
        "habitat_types_veluwe_in_map_area": sum(1 for row in in_map_area if row[0] == "Veluwe"),
    }


def check_aerius_catalogue_record() -> dict:
    """The catalogue record names the AERIUS release in its description."""
    text, last_error = "", None
    # The record can be asked for in more than one way; which one this catalogue answers is tried in order.
    for url, headers in ((config.AERIUS_HABITAT_RECORD + "/formatters/xml", {}),
                         (config.AERIUS_HABITAT_RECORD, {"Accept": "application/xml"}),
                         (config.AERIUS_HABITAT_RECORD, {"Accept": "application/json"})):
        try:
            text = get(url, headers=headers).text
        except CheckError as error:
            last_error = error
            continue
        if re.search(r"AERIUS\s+20\d\d", text):
            break
    releases = sorted(set(re.findall(r"AERIUS\s+(20\d\d)", text)))
    if not releases:
        raise CheckError(str(last_error) if last_error and not text else "no AERIUS release found in the record")
    stamp = re.search(r"<gmd:dateStamp>\s*<gco:Date(?:Time)?>([^<]+)<", text)
    return {"releases_named": releases, "record_date": stamp.group(1) if stamp else None}


CHECKS = {
    "cbs_livestock": ("CBS: livestock and farms (StatLine 80781ned)", check_cbs_livestock),
    "rivm_gdn": ("RIVM: GDN deposition map", check_rivm_gdn),
    "natura2000": ("PDOK: Natura 2000 boundaries", check_natura2000),
    "municipal_boundaries": ("PDOK: municipal boundaries", check_municipal_boundaries),
    "aerius_habitats": ("AERIUS: relevant habitat types and KDW", check_aerius_habitats),
    "aerius_catalogue_record": ("AERIUS: catalogue record of the habitat layer", check_aerius_catalogue_record),
}


# ---------------------------------------------------------------------------
# State, comparison, report
# ---------------------------------------------------------------------------

def read_state(location: str) -> dict:
    if location.startswith(("http://", "https://")):
        return get(location).json()
    path = Path(location)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_checks() -> dict:
    """Ask every source. Returns {source id: {"fingerprint": ...} or {"error": ...}}."""
    results = {}
    for source_id, (label, check) in CHECKS.items():
        print(f"Checking {label} ...")
        try:
            results[source_id] = {"fingerprint": check()}
        except CheckError as error:
            results[source_id] = {"error": str(error)}
    return results


def differences(old: dict, new: dict) -> list[str]:
    """One line per field that differs between two fingerprints."""
    lines = []
    for key in sorted(set(old) | set(new)):
        if old.get(key) != new.get(key):
            lines.append(f"{key}: {json.dumps(old.get(key), ensure_ascii=False)} -> {json.dumps(new.get(key), ensure_ascii=False)}")
    return lines


def build_report(state: dict, results: dict, today: date, manual_days: int) -> tuple[list[str], bool]:
    """Return the report lines and whether there is anything to act on."""
    saved = state.get("sources", {})
    lines, attention = [], False
    lines.append(f"Source check of {today.isoformat()}; saved state of {state.get('written_on') or 'not written yet'}")
    lines.append("")
    for source_id, (label, _) in CHECKS.items():
        result = results[source_id]
        if "error" in result:
            lines.append(f"COULD NOT READ  {label}: {result['error']}")
            attention = True
        elif source_id not in saved:
            lines.append(f"NEW             {label}: no saved state yet")
            attention = True
        else:
            changed = differences(saved[source_id], result["fingerprint"])
            if changed:
                lines.append(f"CHANGED         {label}")
                lines.extend(f"                  {line}" for line in changed)
                attention = True
            else:
                lines.append(f"same            {label}")
    lines.append("")
    for source_id, source in MANUAL_SOURCES.items():
        checked_on = (state.get("manual", {}).get(source_id) or {}).get("checked_on")
        age = (today - date.fromisoformat(checked_on)).days if checked_on else None
        if age is None or age > manual_days:
            when = f"last looked at on {checked_on}, {age} days ago" if checked_on else "never recorded"
            lines.append(f"BY HAND, DUE    {source['label']}: {when}")
            lines.append(f"                  {source['how']}")
            attention = True
        else:
            lines.append(f"by hand         {source['label']}: looked at on {checked_on}, {age} days ago")
    return lines, attention


def write_state(results: dict, old_state: dict, today: date) -> None:
    """Save the fingerprints that could be read. A source that failed keeps its old fingerprint."""
    sources = dict(old_state.get("sources", {}))
    for source_id, result in results.items():
        if "fingerprint" in result:
            sources[source_id] = result["fingerprint"]
    manual = dict(old_state.get("manual", {}))
    for source_id in MANUAL_SOURCES:
        manual.setdefault(source_id, {"checked_on": None})
    state = {
        "about": "Fingerprints of the sources behind nitrogen.html, written by scripts/nitrogen/check_sources.py. "
                 "Update 'manual' by hand after looking at those sources.",
        "written_on": today.isoformat(),
        "sources": sources,
        "manual": manual,
    }
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {STATE_PATH.relative_to(config.REPO_ROOT)}")


# ---------------------------------------------------------------------------
# GitHub issue
# ---------------------------------------------------------------------------

def open_issue(report_lines: list[str]) -> str:
    """Open an issue with the report, unless one from an earlier check is still open."""
    token, repository = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if not token or not repository:
        return "No issue opened: GITHUB_TOKEN and GITHUB_REPOSITORY are not both set."
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    base = f"{GITHUB_API}/repos/{repository}/issues"
    try:
        existing = requests.get(base, headers=headers, params={"state": "open", "labels": ISSUE_LABEL}, timeout=TIMEOUT_S)
        existing.raise_for_status()
        body = "```\n" + "\n".join(report_lines) + "\n```\n\nOpened by `scripts/nitrogen/check_sources.py`. " \
               "Nothing on the page was changed. After looking, refresh the data by hand if needed and save the " \
               "new state with `--write-state`."
        if existing.json():
            number = existing.json()[0]["number"]
            comment = requests.post(f"{base}/{number}/comments", headers=headers, json={"body": body}, timeout=TIMEOUT_S)
            comment.raise_for_status()
            return f"Added the report to open issue #{number}."
        created = requests.post(base, headers=headers, timeout=TIMEOUT_S,
                                json={"title": ISSUE_TITLE, "body": body, "labels": [ISSUE_LABEL]})
        created.raise_for_status()
        return f"Opened issue #{created.json()['number']}."
    except requests.RequestException as error:
        return f"Could not open an issue: {error}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether the sources of the Stikstofmonitor changed.")
    parser.add_argument("--state", default=str(STATE_PATH), help="path or URL of the saved state")
    parser.add_argument("--write-state", action="store_true", help="save the current answers as the new state")
    parser.add_argument("--issue", action="store_true", help="open a GitHub issue when there is something to report")
    parser.add_argument("--manual-days", type=int, default=120, help="remind of checks by hand after this many days")
    args = parser.parse_args()

    try:
        state = read_state(args.state)
    except (CheckError, ValueError) as error:
        print(f"Could not read the saved state from {args.state}: {error}")
        return 2

    today = date.today()
    results = run_checks()
    report_lines, attention = build_report(state, results, today, args.manual_days)
    print()
    print("\n".join(report_lines))
    print(f"\nFinished at {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}.")

    if args.write_state:
        write_state(results, state, today)
    if args.issue and attention:
        print(open_issue(report_lines))
    return 1 if attention else 0


if __name__ == "__main__":
    sys.exit(main())
