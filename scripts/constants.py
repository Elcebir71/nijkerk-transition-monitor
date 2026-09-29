"""
SINGLE SOURCE OF TRUTH for all per-animal-category coefficients used across
this project: the CSV generator (generate.py), the documentation workbook
(build_doc_xlsx.py) and the interactive dashboard (monitor.html, via
sync_js_constants.py, which regenerates monitor.html's embedded JS constants
directly from this file - never hand-edit those JS blocks).

If a coefficient needs to change, change it HERE ONLY, then re-run, in order:
    python3 generate.py              # regenerates the CSV + generation_summary.json
    python3 build_compact_json.py    # regenerates ../farms_data.json from the CSV
    python3 sync_js_constants.py     # regenerates monitor.html's embedded JS
    python3 build_doc_xlsx.py        # regenerates the documentation .xlsx

Sources: see the per-category "source" string below. RVO.nl Tabel 4
"Diergebonden normen 2024" and Tabel 6 "Stikstof en fosfaat per melkkoe 2024"
for the entries marked as such; entries marked "APPROX" are literature-typical
estimates, not taken from an RVO table fetched in this project.
"""

# category -> (kg N/dier/jr, m3 mest/dier/jr, manure_type, source)
NORMS = {
    "melkkoe": (120.0, 22.0, "rundvee", "RVO Tabel 6 2024 (range 65-172 kg N; 120 = representatief punt in dat officiele bereik); mestvolume APPROX (niet RVO-tabel, literatuur-typisch 20-25 m3/koe/jr)"),
    "vleeskalf": (11.0, 2.8, "rundvee", "APPROX (niet RVO-tabel) - literatuur-typische waarde voor vleeskalveren (korte levenscyclus, vloeibaar rantsoen)"),
    "jongvee_vlees": (45.0, 6.0, "rundvee", "RVO Tabel 4 2024, gemiddelde van categorie 101 (32,3 kg N/4,4 m3) en 102 (66,9 kg N/9,5 m3)"),
    "jongvee_melk": (45.0, 6.0, "rundvee", "RVO Tabel 4 2024, gemiddelde van categorie 101 en 102 (zie boven)"),
    "stier": (67.0, 9.5, "rundvee", "RVO Tabel 4 2024, categorie 102-niveau als proxy (geen aparte stierentabel geraadpleegd)"),
    "fokzeug": (20.7, 2.5, "varkens", "RVO Tabel 4 2024, categorie 401 (fokzeugen incl. biggen tot 25kg): 20,6-20,9 kg N, 2,0-2,5 m3"),
    "vleesvarken": (7.0, 0.73, "varkens", "RVO Tabel 4 2024, categorie 411: 6,4-7,6 kg N, 0,71-0,75 m3"),
    "big": (3.0, 0.3, "varkens", "APPROX (niet RVO-tabel) - gespeende biggen, lager dan fokzeug/vleesvarken-categorie; literatuur-typisch"),
    "leghen": (0.50, 0.016, "pluimvee", "RVO Tabel 4 2024, categorie 301: 0,46-0,55 kg N, 0,014-0,018 m3"),
    "vleeskuiken": (0.29, 0.011, "pluimvee", "RVO Tabel 4 2024, categorie 312: 0,29 kg N, 0,011 m3"),
    "eend": (0.30, 0.015, "pluimvee", "APPROX (niet RVO-tabel) - orde-grootte vleeskuiken als proxy"),
    "melkgeit": (9.4, 0.8, "overig", "RVO Tabel 4 2024, categorie 600: 9,4 kg N, 0,8 m3"),
    "overige_geit": (6.0, 0.5, "overig", "APPROX (niet RVO-tabel) - lager dan melkgeit-categorie verondersteld"),
    "schaap": (9.9, 0.6, "overig", "RVO Tabel 4 2024, categorie 550: 9,9 kg N, 0,6 m3"),
    "paard_pony": (43.0, 6.1, "overig", "RVO Tabel 4 2024, gemiddelde van categorie 943 paard (58,8 kg N/7,8 m3) en 941 pony (27,3 kg N/4,4 m3)"),
}

# manure_type -> (m3 biogas / ton mest, source)
BIOGAS_YIELD = {
    "rundvee": (30.0, "Zelfde waarde als hoofdrapport/hub-model (indicatief, mono-vergisting rundveemest)"),
    "varkens": (35.0, "APPROX - literatuur-typisch bereik ca. 25-40 m3/ton voor varkensdrijfmest, hoger drogestofgehalte dan rundvee"),
    "pluimvee": (100.0, "APPROX - literatuur-typisch bereik ca. 80-150 m3/ton voor (vaste) pluimveemest, veel hoger drogestofgehalte"),
    "overig": (28.0, "APPROX - in lijn met rundvee-orde-grootte voor geiten/schapen/paardenmest"),
}

# manure_type -> ton/m3
MEST_DENSITY_TON_PER_M3 = {
    "rundvee": 1.00,
    "varkens": 1.00,
    "pluimvee": 0.65,
    "overig": 1.00,
}

# category -> scenario-engine sector (melkvee/varkens/pluimvee/overig). Not
# the same grouping as manure_type above: jongvee_vlees is rundvee-mesttype
# but sits in the "overig" scenario sector, alongside schaap/geit/paard/
# vleeskalf, because those aren't what a municipal "melkvee-krimp" scenario
# means in practice.
CATEGORY_SECTOR = {
    "melkkoe": "melkvee", "jongvee_melk": "melkvee", "stier": "melkvee",
    "fokzeug": "varkens", "vleesvarken": "varkens", "big": "varkens",
    "leghen": "pluimvee", "vleeskuiken": "pluimvee", "eend": "pluimvee",
    "vleeskalf": "overig", "jongvee_vlees": "overig", "melkgeit": "overig",
    "overige_geit": "overig", "schaap": "overig", "paard_pony": "overig",
}

AMMONIA_INHIBITION_NOTE = (
    "Amoniakinhibitie-kanttekening: het 'geschat biogaspotentieel' voor pluimveemest is een theoretisch "
    "volume x opbrengstfactor-cijfer. Puur mono-vergisten van 100% pluimveemest kan in de praktijk leiden "
    "tot amoniakinhibitie van het vergistingsproces (hoog N-gehalte/laag C:N); in de praktijk wordt "
    "pluimveemest doorgaans verdund of meevergist met rundveemest. Dit cijfer is dus GEEN procesontwerp."
)


def data_quality_tier(category):
    """'A' (OFFICIAL_RVO) or 'L' (LITERATURE_APPROX), derived from NORMS' source string."""
    return "L" if NORMS[category][3].startswith("APPROX") else "A"


ANIMAL_QUALITY = {cat: data_quality_tier(cat) for cat in NORMS}
