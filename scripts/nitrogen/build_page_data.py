"""Bundle the processed files into one script file for nitrogen.html.

Usage (from the repo root, after the fetch scripts):
    python scripts/nitrogen/build_page_data.py

Writes data/nitrogen/processed/nitrogen_data.js

The page loads this file with a <script> tag, so it also works when
nitrogen.html is opened directly from disk (no web server needed).
The data is copied as it is; nothing is recalculated here.
"""
from __future__ import annotations

import json
import sys
from datetime import date

import config

# key in the page data -> (processed file, script that creates it)
INPUTS = {
    "livestock": ("livestock_trend.json", "fetch_cbs_livestock.py"),
    "boundary": ("municipality_boundary.geojson", "fetch_natura2000.py"),
    "natura2000": ("natura2000_nearby.geojson", "fetch_natura2000.py"),
    "deposition": ("deposition_grid.geojson", "fetch_rivm_deposition.py"),
    "habitats": ("nitrogen_sensitive_habitats.geojson", "fetch_aerius_habitats.py"),
}


def main() -> None:
    bundle = {"built_on": date.today().isoformat()}
    for key, (file_name, script) in INPUTS.items():
        path = config.PROCESSED_DIR / file_name
        if not path.exists():
            sys.exit(f"{file_name} not found. Run scripts/nitrogen/{script} first.")
        bundle[key] = json.loads(path.read_text(encoding="utf-8"))

    target = config.PROCESSED_DIR / "nitrogen_data.js"
    payload = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
    target.write_text(f"window.NITROGEN_DATA = {payload};\n", encoding="utf-8")
    print(f"Wrote {target.relative_to(config.REPO_ROOT)} ({target.stat().st_size / 1024:.0f} kB)")


if __name__ == "__main__":
    main()
