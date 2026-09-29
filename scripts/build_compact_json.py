"""Build the compact FARMS array (embedded in index.html) from the CSV."""
import csv
import json

ANIMAL_KEYS = [
    "melkkoe", "vleeskalf", "jongvee_vlees", "jongvee_melk", "stier",
    "fokzeug", "vleesvarken", "big", "leghen", "vleeskuiken", "eend",
    "melkgeit", "overige_geit", "schaap", "paard_pony",
]

rows = list(csv.DictReader(open("../data/nijkerk_synthetic_farms_2023.csv", encoding="utf-8")))

farms = []
for r in rows:
    an = {k: int(r[f"aantal_{k}"]) for k in ANIMAL_KEYS if int(r[f"aantal_{k}"]) > 0}
    farms.append({
        "id": r["farm_id"],
        "t": r["farm_type"],
        "la": float(r["latitude"]),
        "lo": float(r["longitude"]),
        "ark": int(r["afstand_arkemheen_m"]),
        "n": int(r["totaal_N_excretie_kg_jr"]),
        "m": float(r["totaal_mest_ton_jr"]),
        "b": int(r["geschat_biogaspotentieel_m3_jr"]),
        "q": "A" if r["data_quality"] == "OFFICIAL_RVO" else "L",
        "am": 1 if r["amoniakinhibitie_waarschuwing"] == "JA" else 0,
        "an": an,
    })

with open("../data/farms_data.json", "w", encoding="utf-8") as f:
    json.dump(farms, f, ensure_ascii=False, separators=(",", ":"))

print(f"Wrote {len(farms)} farms to ../data/farms_data.json")
