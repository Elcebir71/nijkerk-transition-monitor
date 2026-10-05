"""Shared settings for the nitrogen module. Real open data only, no synthetic values."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "nitrogen" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "nitrogen" / "processed"

# CBS region keys are padded to 6 characters, so provinces carry two trailing spaces.
MUNICIPALITY_KEY = "GM0267"
MUNICIPALITY_NAME = "Nijkerk"
PROVINCE_KEY = "PV25  "
PROVINCE_NAME = "Gelderland"

# CBS StatLine: "Landbouw; gewassen, dieren en grondgebruik naar gemeente"
CBS_TABLE_ID = "80781ned"
CBS_BASE_URL = f"https://opendata.cbs.nl/ODataApi/odata/{CBS_TABLE_ID}"
CBS_STATLINE_URL = f"https://opendata.cbs.nl/statline/#/CBS/nl/dataset/{CBS_TABLE_ID}"

# Column keys as published by CBS. The script checks them against the live
# table definition before fetching, so a renamed column fails loudly.
CBS_INDICATORS = {
    "AantalLandbouwbedrijvenTotaal_1": {"id": "farms_total", "label_nl": "Landbouwbedrijven, totaal", "unit": "bedrijven"},
    "RundveeTotaal_84": {"id": "cattle_total", "label_nl": "Rundvee, totaal", "unit": "dieren"},
    "MelkEnKalfkoeien2Jaar_88": {"id": "dairy_cows", "label_nl": "Melk- en kalfkoeien (2 jaar en ouder)", "unit": "dieren"},
    "GeitenTotaal_96": {"id": "goats_total", "label_nl": "Geiten, totaal", "unit": "dieren"},
    "VarkensTotaal_121": {"id": "pigs_total", "label_nl": "Varkens, totaal", "unit": "dieren"},
    "KippenTotaal_125": {"id": "chickens_total", "label_nl": "Kippen, totaal", "unit": "dieren"},
}

# Method changes documented by CBS for this table. Show them on every trend chart.
CBS_TREND_BREAKS = [
    {"year": 2016, "affects": ["farms_total"],
     "note": "Farm population defined via the Handelsregister from 2016; clear break in number of farms.",
     "note_nl": "Vanaf 2016 bepaalt het Handelsregister welke bedrijven meetellen; duidelijke trendbreuk in het aantal bedrijven."},
    {"year": 2017, "affects": ["cattle_total", "dairy_cows"],
     "note": "Cattle counts derived from the I&R register instead of the survey.",
     "note_nl": "Vanaf 2017 komen de aantallen rundvee uit het I&R-register in plaats van uit de opgave."},
    {"year": 2018, "affects": ["goats_total", "pigs_total", "chickens_total"],
     "note": "Goats and poultry derived from I&R registers; pigs and chickens adjusted for temporary vacancy.",
     "note_nl": "Vanaf 2018 komen geiten en pluimvee uit I&R-registers; varkens en kippen worden gecorrigeerd voor tijdelijke leegstand."},
]

# Real-world events that explain a visible jump. Not method changes: keep them separate.
CBS_EVENTS = [
    {"year": 2003, "affects": ["chickens_total"],
     "note": "Avian influenza (H7N7) outbreak in the Gelderse Vallei, spring 2003; poultry culled around the 1 April count.",
     "note_nl": "Uitbraak van vogelgriep (H7N7) in de Gelderse Vallei, voorjaar 2003; pluimvee geruimd rond de telling van 1 april."},
]

CBS_METHOD = "Landbouwtelling (yearly agricultural census)"
CBS_REFERENCE_DATE = "1 April of each year (animal counts)"

CBS_CAVEATS = [
    "Animals are assigned to the municipality of the farm's main address, not to where they are kept.",
    "A missing value means CBS marks the figure as unknown, unreliable or confidential.",
]

# Other sources (used by later scripts)
# Radius around the municipality that the map layers cover.
SURROUNDINGS_RADIUS_M = 15000

# RIVM GDN: large-scale deposition maps. ESRI ASCII grid, 1x1 km, EPSG:28992.
RIVM_GDN_BASE_URL = "https://data.rivm.nl/data/gcn"
RIVM_GDN_DOWNLOAD_PAGE = "https://www.rivm.nl/gcn-gdn-kaarten/depositiekaarten/downloaden"
RIVM_GDN_YEAR = 2025
# The total is required; the two components are added when their files are available.
RIVM_GDN_COMPONENTS = {
    "ntot": {"file": f"depo_NTOT_{RIVM_GDN_YEAR}", "label_nl": "Totaal stikstof (N)", "required": True},
    "nhx": {"file": f"depo_NHx_{RIVM_GDN_YEAR}", "label_nl": "Gereduceerd stikstof (NHx)", "required": False},
    "noy": {"file": f"depo_NOy_{RIVM_GDN_YEAR}", "label_nl": "Geoxideerd stikstof (NOy)", "required": False},
}
# Taken from Metadata_depo_NTOT_2025.pdf inside the RIVM zip.
RIVM_GDN_METADATA = {
    "description_nl": "Jaargemiddelde depositie totaal stikstof in Nederland (droog + nat)",
    "scenario_nl": "Feitelijke omstandigheden",
    "unit": "mol N per ha per year",
    "resolution": "1x1 km",
    "model": "OPS-pro 5.3.1.0, calibrated on measurements",
    "accuracy": "sigma = 30-35% per grid cell",
    "release": "1.0, 10-08-2026 (productie 2602)",
    "report": "Mijnen-Visser et al., Grootschalige concentratie- en depositiekaarten Nederland, Rapportage juni 2026",
}
MOL_N_TO_KG = 14.007 / 1000

# AERIUS open data (RIVM): nitrogen-sensitive ("relevant") habitat types in Natura 2000 areas.
# Layer and field names were read from the live service with inspect_aerius.py on 2026-10-05.
AERIUS_WFS = "https://connect.aerius.nl/opendata/wfs"
AERIUS_HABITAT_LAYER = "base_geometries:relevant_habitats"
AERIUS_PRODUCT_PAGE = "https://www.aeriusproducten.nl/producten/aerius-monitor"
# PDOK: municipal boundary (Kadaster, Bestuurlijke Gebieden). Coordinates are EPSG:28992 (metres).
PDOK_MUNICIPALITY_WFS = "https://service.pdok.nl/kadaster/bestuurlijkegebieden/wfs/v1_0"
PDOK_MUNICIPALITY_LAYER = "bestuurlijkegebieden:Gemeentegebied"
PDOK_MUNICIPALITY_CODE = "0267"
# Small box around Nijkerk town, only used to find the boundary feature.
MUNICIPALITY_SEED_BBOX = (157000, 465000, 163000, 472000)

# PDOK: Natura 2000 boundaries (RVO). Licence CC0.
PDOK_NATURA2000_WFS = "https://service.pdok.nl/rvo/natura2000/wfs/v1_0"
PDOK_NATURA2000_LAYER = "natura2000:natura2000"
# Codes used in the "beschermin" attribute. Unknown codes are passed through unchanged.
NATURA2000_PROTECTION_LABELS = {"VR": "Vogelrichtlijn", "HR": "Habitatrichtlijn", "VR+HR": "Vogel- en Habitatrichtlijn"}
