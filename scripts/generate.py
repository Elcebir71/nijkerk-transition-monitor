"""
Nijkerk Agricultural Transition Monitor - synthetic demo dataset generator.

IMPORTANT: all farm names, IDs and locations in the output are FICTIONAL.
They are NOT tied to any real address, BAG-parcel or existing business.
Only the AGGREGATE totals per animal category are calibrated (at a safety
margin below) real CBS Landbouwtelling 2023 figures for gemeente Nijkerk,
so the demo "looks" realistic in scale without describing any real farm.

Sources:
- CBS StatLine 80781ned, "Landbouw; gewassen, dieren en grondgebruik naar
  gemeente", regio GM0267 (Nijkerk), periode 2023JJ00. Fetched via OData API,
  29-09-2026.
- RVO.nl, Tabel 4 "Diergebonden normen 2024" (https://www.rvo.nl/sites/default/files/2023-12/Tabel-4-Diergebonden-normen-2024.pdf)
  for jongvee, vleesvarkens, fokzeugen, leghennen, vleeskuikens, melkgeiten,
  schapen, paarden/pony's: forfaitaire N-excretie (kg N/dier/jr) en
  mestproductie (m3/dier/jr).
- RVO.nl, Tabel 6 "Stikstof en fosfaat per melkkoe 2024" for melkkoeien:
  N-excretie varies 65-172 kg N/koe/jr depending on melkproductie/ureumgehalte;
  ~110-115 kg N is representative for average (~7.500 kg melk/jr) production -
  this script uses 120 kg N as a round representative value WITHIN that
  official range, not an exact per-farm calculation.
- Values marked "APPROX (niet RVO-tabel)" below are literature-typical
  estimates, NOT taken directly from an RVO table fetched in this project,
  because a separate table for that category was not retrieved. They are
  clearly flagged as such in the output notes.
"""
import csv
import json
import random
import math

from constants import NORMS, BIOGAS_YIELD, MEST_DENSITY_TON_PER_M3, AMMONIA_INHIBITION_NOTE

random.seed(42)

# ---------------------------------------------------------------------------
# 1. Real CBS Landbouwtelling 2023 totals for gemeente Nijkerk (GM0267)
# ---------------------------------------------------------------------------
REAL_2023 = {
    "melkkoe": 3074,
    "vleeskalf": 8421,
    "jongvee_vlees": 394,
    "jongvee_melk": 1912,
    "stier": 26,
    "fokzeug": 3416,
    "vleesvarken": 19438,
    "big": 18063,
    "leghen": 441132,
    "vleeskuiken": 393380,
    "eend": 10151,
    "melkgeit": 6874,
    "overige_geit": 7498 - 6874,
    "schaap": 3346,
    "paard_pony": 651,
}

# Safety margin: synthetic dataset totals target this fraction of the real
# 2023 total per category, so the demo never overstates real livestock counts.
TARGET_FRACTION = 0.85

# ---------------------------------------------------------------------------
# 2. Per-animal norms, biogas yield, manure density: imported from
#    constants.py (the single source of truth - see that file's docstring
#    for the full regeneration order across CSV / dashboard / docs).
# ---------------------------------------------------------------------------
# 3. Farm archetypes: 75 fictional farms, type distribution roughly reflecting
#    the real municipal herd composition (dairy-heavy, sizeable veal/pig/
#    poultry segments), NOT tied to any real address or BAG-parcel.
# ---------------------------------------------------------------------------
ARCHETYPES = (
    ["melkvee"] * 30
    + ["vleeskalveren"] * 8
    + ["varkens"] * 10
    + ["pluimvee"] * 9
    + ["geiten_schapen"] * 6
    + ["paarden"] * 5
    + ["gemengd"] * 7
)
assert len(ARCHETYPES) == 75
random.shuffle(ARCHETYPES)

TYPE_CATEGORIES = {
    "melkvee": ["melkkoe", "jongvee_melk", "stier"],
    "vleeskalveren": ["vleeskalf"],
    "varkens": ["fokzeug", "vleesvarken", "big"],
    "pluimvee": ["leghen", "vleeskuiken", "eend"],
    "geiten_schapen": ["melkgeit", "overige_geit", "schaap"],
    "paarden": ["paard_pony"],
    "gemengd": ["melkkoe", "jongvee_vlees", "schaap", "paard_pony"],
}

# Count how many farms draw on each category, to split the target total
farms_per_category = {cat: 0 for cat in REAL_2023}
for arche in ARCHETYPES:
    for cat in TYPE_CATEGORIES[arche]:
        farms_per_category[cat] += 1

# ---------------------------------------------------------------------------
# 4. Generate random shares per category (Dirichlet-like via random weights),
#    then scale so the category sum = TARGET_FRACTION * real 2023 total.
# ---------------------------------------------------------------------------
farm_category_counts = [dict() for _ in range(75)]
for cat, target_n_farms in farms_per_category.items():
    if target_n_farms == 0:
        continue
    weights = [random.uniform(0.4, 1.6) for _ in range(target_n_farms)]
    wsum = sum(weights)
    target_total = REAL_2023[cat] * TARGET_FRACTION
    shares = [w / wsum * target_total for w in weights]
    rounded = [round(s) for s in shares]
    farm_idx_for_share = []
    idx = 0
    for i, arche in enumerate(ARCHETYPES):
        if cat in TYPE_CATEGORIES[arche]:
            farm_category_counts[i][cat] = rounded[idx]
            farm_idx_for_share.append(i)
            idx += 1
    # Correction pass: rounding (and the ceiling below) must never push the
    # category total above TARGET_FRACTION * real 2023 total.
    cap = math.floor(target_total)
    current_sum = sum(farm_category_counts[i][cat] for i in farm_idx_for_share)
    while current_sum > cap:
        # trim 1 from the farm currently holding the most of this category
        holder = max(farm_idx_for_share, key=lambda i: farm_category_counts[i][cat])
        if farm_category_counts[holder][cat] == 0:
            break
        farm_category_counts[holder][cat] -= 1
        current_sum -= 1

# ---------------------------------------------------------------------------
# 5. Locations: V1.1 CHANGE (per external review, 29-09-2026) - locations are
#    now FULLY synthetic random points, with NO relationship whatsoever to any
#    real BRP parcel, BAG building or address. The previous version anchored
#    each point to a real agricultural-parcel centroid + 80-250m jitter; that
#    was reconsidered as still too close to a "real parcel -> shifted point"
#    mapping for a municipal-facing demo. Points are now drawn uniformly at
#    random inside a schematic Nijkerk outline (the same hand-drawn, non-
#    cadastral polygon used for the map visualisation), excluding the town
#    centre (a built-up area, not farmland) and kept a minimum distance apart
#    so dots don't visually overlap. No real geodata is read at all in this
#    step any more.
# ---------------------------------------------------------------------------
M_PER_DEG_LAT = 111_320.0

# Same schematic (non-cadastral) municipal outline used in the map artifact,
# as (lon, lat) pairs.
NIJKERK_OUTLINE = [
    (5.378, 52.183), (5.390, 52.174), (5.420, 52.171), (5.460, 52.174), (5.490, 52.178),
    (5.510, 52.188), (5.520, 52.205), (5.515, 52.225), (5.505, 52.242), (5.495, 52.258),
    (5.475, 52.272), (5.450, 52.278), (5.420, 52.276), (5.395, 52.265), (5.383, 52.245),
    (5.376, 52.220), (5.375, 52.200),
]
TOWN_CENTRE = (52.2192, 5.4775)  # Nijkerk centrum: built-up area, excluded from farm placement
TOWN_CENTRE_RADIUS_M = 900
MIN_FARM_SPACING_M = 150

def point_in_polygon(lon, lat, poly):
    inside = False
    n = len(poly)
    x, y = lon, lat
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
            inside = not inside
    return inside

def random_synthetic_location(placed, rng, max_tries=2000):
    lat_min, lat_max = 52.172, 52.278
    lon_min, lon_max = 5.373, 5.522
    for _ in range(max_tries):
        lat = rng.uniform(lat_min, lat_max)
        lon = rng.uniform(lon_min, lon_max)
        if not point_in_polygon(lon, lat, NIJKERK_OUTLINE):
            continue
        if haversine_m(lat, lon, *TOWN_CENTRE) < TOWN_CENTRE_RADIUS_M:
            continue
        too_close = False
        for (plat, plon) in placed:
            if haversine_m(lat, lon, plat, plon) < MIN_FARM_SPACING_M:
                too_close = True
                break
        if too_close:
            continue
        return round(lat, 5), round(lon, 5)
    # fallback: relax spacing constraint only, keep polygon/town-centre rules
    for _ in range(max_tries):
        lat = rng.uniform(lat_min, lat_max)
        lon = rng.uniform(lon_min, lon_max)
        if point_in_polygon(lon, lat, NIJKERK_OUTLINE) and haversine_m(lat, lon, *TOWN_CENTRE) >= TOWN_CENTRE_RADIUS_M:
            return round(lat, 5), round(lon, 5)
    raise RuntimeError("Could not place a synthetic farm location after relaxed retries")

# Arkemheen Natura 2000-gebied: APPROXIMATE reference point (polder/
# natuurgebied ten noordwesten van Nijkerk, langs het Veluwemeer/Nuldernauw),
# NIET de exacte officiele gebiedsgrens (die vereist een polygon-bestand dat
# in deze sessie niet is opgehaald). Uitsluitend voor een INDICATIEVE
# afstand-tot-Arkemheen-kolom in de demo, niet voor een juridische toets.
ARKEMHEEN_REF = (52.265, 5.405)

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

# ---------------------------------------------------------------------------
# 6. Assemble rows
# ---------------------------------------------------------------------------
rng = random.Random(42)
placed_points = []
rows = []
for i, arche in enumerate(ARCHETYPES):
    farm_id = f"SYN-{i+1:03d}"
    lat, lon = random_synthetic_location(placed_points, rng)
    placed_points.append((lat, lon))
    dist_arkemheen_m = round(haversine_m(lat, lon, *ARKEMHEEN_REF))
    counts = farm_category_counts[i]

    total_n = 0.0
    manure_by_type = {"rundvee": 0.0, "varkens": 0.0, "pluimvee": 0.0, "overig": 0.0}
    for cat, n_animals in counts.items():
        n_kg, m3_per_dier, mtype, _src = NORMS[cat]
        total_n += n_animals * n_kg
        manure_by_type[mtype] += n_animals * m3_per_dier

    total_manure_m3 = sum(manure_by_type.values())
    total_manure_ton = sum(
        manure_by_type[mtype] * MEST_DENSITY_TON_PER_M3[mtype] for mtype in manure_by_type
    )
    biogas_m3 = sum(
        manure_by_type[mtype] * MEST_DENSITY_TON_PER_M3[mtype] * BIOGAS_YIELD[mtype][0]
        for mtype in manure_by_type
    )
    pluimvee_share = manure_by_type["pluimvee"] / total_manure_m3 if total_manure_m3 > 0 else 0.0
    data_quality = "LITERATURE_APPROX" if any(
        NORMS[cat][3].startswith("APPROX") for cat in counts if counts.get(cat, 0) > 0
    ) else "OFFICIAL_RVO"

    rows.append({
        "farm_id": farm_id,
        "synthetic": "JA - NIET EEN ECHT BEDRIJF",
        "farm_type": arche,
        "latitude": lat,
        "longitude": lon,
        "afstand_arkemheen_m": dist_arkemheen_m,
        **{f"aantal_{cat}": counts.get(cat, 0) for cat in NORMS},
        "totaal_N_excretie_kg_jr": round(total_n),
        "totaal_mest_m3_jr": round(total_manure_m3, 1),
        "totaal_mest_ton_jr": round(total_manure_ton, 1),
        "geschat_biogaspotentieel_m3_jr": round(biogas_m3),
        "data_quality": data_quality,
        "amoniakinhibitie_waarschuwing": "JA" if pluimvee_share > 0.5 else "",
    })

# ---------------------------------------------------------------------------
# 7. Write CSV
# ---------------------------------------------------------------------------
fieldnames = list(rows[0].keys())
with open("../data/nijkerk_synthetic_farms_2023.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

# ---------------------------------------------------------------------------
# 8. Sanity check: synthetic totals vs. real 2023 totals (should be <= target)
# ---------------------------------------------------------------------------
check = {cat: 0 for cat in REAL_2023}
for r in rows:
    for cat in REAL_2023:
        check[cat] += r.get(f"aantal_{cat}", 0)

print(f"{'categorie':<16} {'synthetisch':>12} {'doel(85%)':>12} {'echt 2023':>12}")
for cat in REAL_2023:
    print(f"{cat:<16} {check[cat]:>12} {round(REAL_2023[cat]*TARGET_FRACTION):>12} {REAL_2023[cat]:>12}")

total_n_all = sum(r["totaal_N_excretie_kg_jr"] for r in rows)
total_manure_all = sum(r["totaal_mest_ton_jr"] for r in rows)
total_biogas_all = sum(r["geschat_biogaspotentieel_m3_jr"] for r in rows)
print(f"\nTotaal N-excretie (synthetisch, 75 bedrijven): {total_n_all:,.0f} kg N/jr")
print(f"Totaal mest (synthetisch): {total_manure_all:,.0f} ton/jr")
print(f"Totaal geschat biogaspotentieel (synthetisch): {total_biogas_all:,.0f} m3/jr")

with open("../data/generation_summary.json", "w") as f:
    json.dump({
        "check": check,
        "real_2023": REAL_2023,
        "target_fraction": TARGET_FRACTION,
        "total_n_kg": total_n_all,
        "total_manure_ton": total_manure_all,
        "total_biogas_m3": total_biogas_all,
    }, f, indent=2)

print("\nSaved: ../data/nijkerk_synthetic_farms_2023.csv, ../data/generation_summary.json")
