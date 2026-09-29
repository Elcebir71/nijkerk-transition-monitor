"""
Regenerates index.html's embedded JS constant blocks (CATEGORY_INFO,
BIOGAS_YIELD_M3_PER_TON, MEST_DENSITY_TON_PER_M3, CATEGORY_SECTOR,
ANIMAL_QUALITY) directly from constants.py, so the dashboard's client-side
scenario engine can never silently drift from the Python CSV generator.

Run this after any change to constants.py, before publishing/deploying:
    python3 sync_js_constants.py
"""
import re
import json

from constants import NORMS, BIOGAS_YIELD, MEST_DENSITY_TON_PER_M3, CATEGORY_SECTOR, ANIMAL_QUALITY

MONITOR_HTML = "../index.html"


def js_category_info():
    lines = ["const CATEGORY_INFO = {"]
    for cat, (n_kg, m3, mtype, _src) in NORMS.items():
        lines.append(f'  {cat}: {{n:{n_kg}, m3:{m3}, type:"{mtype}"}},')
    lines.append("};")
    return "\n".join(lines)


def js_dict_simple(name, d):
    body = ", ".join(f'{k}:{v}' for k, v in d.items())
    return f"const {name} = {{{body}}};"


def js_category_sector():
    lines = ["const CATEGORY_SECTOR = {"]
    # group by sector for readability, same order as constants.py
    lines.append("  " + ", ".join(f'{cat}:"{sector}"' for cat, sector in CATEGORY_SECTOR.items()) + ",")
    lines.append("};")
    return "\n".join(lines)


def js_animal_quality():
    body = ", ".join(f'{cat}:"{tier}"' for cat, tier in ANIMAL_QUALITY.items())
    return f"const ANIMAL_QUALITY = {{{body}}};"


def replace_block(html, marker_start_pattern, marker_end, new_text):
    pattern = re.compile(marker_start_pattern + r".*?" + re.escape(marker_end), re.S)
    new_html, n = pattern.subn(new_text, html, count=1)
    if n != 1:
        raise RuntimeError(f"Expected 1 match for pattern {marker_start_pattern!r}, got {n}")
    return new_html


html = open(MONITOR_HTML, encoding="utf-8").read()

html = replace_block(html, r"const CATEGORY_INFO = \{", "\n};", js_category_info())
html = replace_block(html, r"const BIOGAS_YIELD_M3_PER_TON = \{", "};",
                      js_dict_simple("BIOGAS_YIELD_M3_PER_TON", {k: v[0] for k, v in BIOGAS_YIELD.items()}))
html = replace_block(html, r"const MEST_DENSITY_TON_PER_M3 = \{", "};",
                      js_dict_simple("MEST_DENSITY_TON_PER_M3", MEST_DENSITY_TON_PER_M3))
html = replace_block(html, r"const CATEGORY_SECTOR = \{", "\n};", js_category_sector())
html = replace_block(html, r"const ANIMAL_QUALITY = \{", "};", js_animal_quality())

open(MONITOR_HTML, "w", encoding="utf-8").write(html)
print("Synced index.html JS constants from constants.py (single source of truth).")
