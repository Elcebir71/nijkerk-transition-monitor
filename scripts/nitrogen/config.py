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
    "MelkEnKalfkoeien2Jaar_88": {"id": "dairy_cows", "label_nl": "Melk- en kalfkoeien (>= 2 jaar)", "unit": "dieren"},
    "GeitenTotaal_96": {"id": "goats_total", "label_nl": "Geiten, totaal", "unit": "dieren"},
    "VarkensTotaal_121": {"id": "pigs_total", "label_nl": "Varkens, totaal", "unit": "dieren"},
    "KippenTotaal_125": {"id": "chickens_total", "label_nl": "Kippen, totaal", "unit": "dieren"},
}

# Method changes documented by CBS for this table. Show them on every trend chart.
CBS_TREND_BREAKS = [
    {"year": 2016, "affects": ["farms_total"],
     "note": "Farm population defined via the Handelsregister from 2016; clear break in number of farms."},
    {"year": 2017, "affects": ["cattle_total", "dairy_cows"],
     "note": "Cattle counts derived from the I&R register instead of the survey."},
    {"year": 2018, "affects": ["goats_total", "pigs_total", "chickens_total"],
     "note": "Goats and poultry derived from I&R registers; pigs and chickens adjusted for temporary vacancy."},
]

# Real-world events that explain a visible jump. Not method changes: keep them separate.
CBS_EVENTS = [
    {"year": 2003, "affects": ["chickens_total"],
     "note": "Avian influenza (H7N7) outbreak in the Gelderse Vallei, spring 2003; poultry culled around the 1 April count."},
]

CBS_METHOD = "Landbouwtelling (yearly agricultural census)"
CBS_REFERENCE_DATE = "1 April of each year (animal counts)"

CBS_CAVEATS = [
    "Animals are assigned to the municipality of the farm's main address, not to where they are kept.",
    "A missing value means CBS marks the figure as unknown, unreliable or confidential.",
]

# Other sources (used by later scripts)
RIVM_GDN_BASE_URL = "https://data.rivm.nl/data/gcn"
RIVM_GDN_FILES = ["depo_NTOT_2025.zip", "depo_NHx_2025.zip", "depo_NOy_2025.zip"]
PDOK_NATURA2000_WFS = "https://service.pdok.nl/rvo/natura2000/wfs/v1_0"
PDOK_NATURA2000_LAYER = "natura2000:natura2000"
NATURA2000_SEARCH_RADIUS_M = 15000
