# Nitrogen module: data source register

Last checked: 2026-10-04

## Purpose

An independent data project that makes public information about nitrogen,
emissions and nature in Nijkerk easy to find, check and understand.

> Ik reken niet zelf aan depositie. Ik maak bestaande, betrouwbare
> overheidsdata toegankelijk en transparant.

## Data principles

- Real, traceable data only. No synthetic values anywhere in this module.
- Every indicator shows its source, reference date and method.
- Emission and deposition are always shown as separate things.
- No own deposition calculations. Deposition is shown as published by RIVM.
- No cost figures unless they come from a cited external source, and then
  labelled as not specific to Nijkerk.
- No individual farms on any map. Aggregate to grid cell or neighbourhood.

Nijkerk is in the province of **Gelderland**. Provincial policy sources must
be Gelderland sources. The main nitrogen-sensitive Natura 2000 context is the
**Veluwe**.

## Register

| Onderwerp | Bron | Dataset | Gebied | Periode | Formaat | Gebruik | Status |
|---|---|---|---|---|---|---|---|
| Landbouw (dieren, bedrijven) | CBS | StatLine `80781ned` | Nijkerk (`GM0267`), Gelderland (`PV25`) | 2000–2025 | OData / JSON | Bronanalyse, trend | Verified |
| NH₃ emissie | Emissieregistratie (RIVM e.a.) | ER Reeks 1990-2024 Definitief | Nijkerk (`0267`), per sector | 2000–2024 (agriculture missing before 2000) | XLSX (manual export) | Emissie | Verified |
| NOx emissie | Emissieregistratie (RIVM e.a.) | ER Reeks 1990-2024 Definitief | Nijkerk (`0267`), per sector | 1990–2024 | XLSX (manual export) | Emissie | Verified |
| Depositie | RIVM | GDN `depo_NTOT`, `depo_NHx`, `depo_NOy` | National 1x1 km grid, clipped to Nijkerk + 15 km | 2025; prognosis 2030–2040 | Zip with ESRI ASCII grid, EPSG:28992 | Weergave | Verified |
| Natura 2000 | PDOK / RVO | WFS `natura2000:natura2000` | Veluwe and surroundings | Current | GeoJSON, EPSG:28992, CC0 | Kaart | Verified |
| Stikstofgevoelige habitats en KDW | RIVM, AERIUS open data | WFS `base_geometries:relevant_habitats` | Map area (Nijkerk + 15 km) | As served on fetch date (AERIUS 2025) | GeoJSON via WFS, EPSG:28992 | Weergave, tabel | Verified |
| Overschrijding per hexagoon | RIVM, AERIUS open data | WFS `base_geometries:hexagons`, `depositions:depositions` | Map area | Deposition year 2023 | WFS | Not used yet | Fields seen, definitions not verified |
| Landgebruik | PDOK / CBS | To determine | Nijkerk | – | GIS | Context | Not checked |

The land-use row is not needed for v1.

## Per source

### 1. CBS: Landbouw; gewassen, dieren en grondgebruik naar gemeente

- **Where:** <https://opendata.cbs.nl/statline/#/CBS/nl/dataset/80781ned>
  API: `https://opendata.cbs.nl/ODataApi/odata/80781ned`
- **What it means:** yearly agricultural census (Landbouwtelling). Number of
  animals and number of farms per municipality. Reference date for animals is
  1 April. Definitive 2025 figures were added on 30 March 2026.
- **May calculate:** trend per animal type, share per animal type, comparison
  with the Gelderland total.
- **May not calculate:** where animals physically are. Farms are assigned to
  the municipality of their main address.
- **Known breaks:** 2016 (farm population defined via Handelsregister),
  2017 (cattle from I&R register), 2018 (goats and poultry from I&R; pigs and
  chickens adjusted for temporary vacancy). Mark these on every chart.
- **Script:** `scripts/nitrogen/fetch_cbs_livestock.py`

### 2. Emissieregistratie: NH₃ and NOx

- **Where:** <https://www.emissieregistratie.nl/data/data-export>
- **What it means:** official Dutch emission inventory by sector. The
  1990–2024 series is definitive and includes a regional distribution.
- **May calculate:** sector shares, change over time.
- **May not calculate:** emissions of individual farms; comparisons that mix
  different publication series (each yearly release recalculates history).
- **Export (by hand, 2026-10-05):** Compartiment Lucht; Stof Ammoniak and
  Stikstofoxiden (als NO2); Gebiedsindeling Gemeente; Bronniveau Sector; all
  years. The file contains all municipalities; the script keeps Nijkerk.
- **Years in the export:** 1990, 1995, 2000, 2005, 2010, 2015, 2019–2024.
  No 2025 rows at municipal level.
- **Known gap:** for 1990 and 1995 there is no agricultural NH₃ at municipal
  level (for any municipality). NH₃ totals for those years are left empty.
- **Result for Nijkerk, 2024:** NH₃ 352 t, 93% agriculture. NOx 317 t (as
  NO₂), 65% traffic and transport, 25% agriculture.
- **Unexplained:** NH₃ in Nijkerk drops 37% between 2000 and 2005, against
  12% for all municipalities together. Could be real or an effect of the
  spatial allocation. Shown on the page as a note, not explained.
- **Units:** kg of the substance per year; NOx expressed as NO₂. Not
  comparable with deposition in mol N.
- **Terms of use (from the export):** reuse allowed with source attribution;
  no rights can be derived from the data.
- **Script:** `scripts/nitrogen/load_emissions.py` (needs `openpyxl`)

### 3. RIVM GDN: grootschalige depositiekaarten

- **Where:** <https://www.rivm.nl/gcn-gdn-kaarten/depositiekaarten/downloaden>
  Files: `https://data.rivm.nl/data/gcn/depo_NTOT_2025.zip` (also `NHx`, `NOy`)
- **What it means:** modelled large-scale nitrogen deposition for the past
  year plus prognoses for 2030, 2035 and 2040 (2040 is indicative).
- **May calculate:** nothing beyond clipping and displaying. Show the values
  as published, with the year.
- **May not calculate:** the effect of a local measure on deposition. That
  requires the atmospheric dispersion model behind AERIUS. Not suitable for
  permit-level statements either.
- **Format (from the metadata in the zip):** 1x1 km grid, RD New (EPSG:28992),
  unit mol N per ha per year, total deposition (dry + wet), model OPS-pro
  5.3.1.0 calibrated on measurements. Release 1.0 of 10-08-2026.
- **Uncertainty:** RIVM gives sigma = 30–35% per grid cell. Differences between
  neighbouring cells are often not meaningful; say so next to the map.
- **Inputs behind the 2025 map:** 2025 meteorology and measurements, 2024
  national emission totals, 2023 spatial distribution of Dutch sources.
- **Nature areas:** RIVM refers to its report "Monitor stikstofdepositie in
  Natura 2000-gebieden" for deposition on nature areas. Do not publish own
  per-area averages as if they were that monitor.
- **Script:** `scripts/nitrogen/fetch_rivm_deposition.py`

### 4. PDOK: Natura 2000 boundaries

- **Where:** `https://service.pdok.nl/rvo/natura2000/wfs/v1_0`
  layer `natura2000:natura2000`
- **What it means:** boundaries of the 162 Dutch Natura 2000 areas. Licence CC0.
- **May calculate:** distance to Nijkerk, overlap with the municipality.
- **May not calculate:** whether an area is nitrogen-sensitive. The boundary
  data does not say this. Not every Natura 2000 area is designated for
  nitrogen-sensitive habitats, so that label needs its own source.
- **Result for Nijkerk (2026-10-04):** Arkemheen (VR) overlaps the municipality
  for about 1,004 ha; Veluwerandmeren (VR+HR) for about 23 ha; the Veluwe
  (VR+HR) lies about 0.7 km outside the boundary.
- **Script:** `scripts/nitrogen/fetch_natura2000.py`

### 5. AERIUS: nitrogen-sensitive habitat types

- **Where:** `https://connect.aerius.nl/opendata/wfs`, layer
  `base_geometries:relevant_habitats`. Product information:
  <https://www.aeriusproducten.nl/producten/aerius-monitor>
- **What it means:** per Natura 2000 area and habitat type, the mapped
  polygons that AERIUS treats as relevant (nitrogen-sensitive), with the
  critical deposition value (KDW, mol N per ha per year) and a coverage
  fraction per polygon. Covers Natura 2000 areas only.
- **Result for the map area (2026-10-05):** 33 habitat types and species
  habitats, all in the Veluwe, 39,436 ha mapped; KDW from 500 to 2,399.
  Inside the municipality of Nijkerk: 0 ha. Arkemheen, Veluwerandmeren and
  Eemmeer & Gooimeer Zuidoever have no relevant types in the map area.
- **May calculate:** area of mapped habitat in the map area and inside the
  municipality; distance to the nearest mapped habitat.
- **May not calculate:** an own comparison of KDW with the RIVM 1x1 km map.
  If exceedance is shown later, use the flags AERIUS publishes per hexagon.
- **Codes:** H = habitat type. ZGH = search area: indications, but no
  certainty, that the type is present (source: BIJ12 Methodiekdocument
  kartering habitattypen). Lg and L = species habitats (leefgebieden); this
  reading is not yet backed by a quoted source.
- **To verify:** the exact criteria for "relevant"; whether the threshold is
  a KDW below 2,400 mol; the licence of this specific layer; the meaning of
  the hexagon fields `exceeding` and `above_cl`.
- **Note on years:** AERIUS deposition per hexagon is for 2023, the RIVM GDN
  map on the page is for 2025. Do not combine them in one figure.
- **Script:** `scripts/nitrogen/fetch_aerius_habitats.py`. The download is
  kept in `data/nitrogen/raw/` (not committed) and reused on later runs.

## The page

`nitrogen.html` shows the five working layers. It reads one file,
`data/nitrogen/processed/nitrogen_data.js`, which `scripts/nitrogen/build_page_data.py`
makes by copying the processed files as they are. Run order:

1. `fetch_cbs_livestock.py`
2. `fetch_natura2000.py`
3. `fetch_rivm_deposition.py`
4. `fetch_aerius_habitats.py`
5. `load_emissions.py` (after a manual export, see the script)
6. `build_page_data.py`

The map area is the bounding box of the municipality plus 15 km. Natura 2000
areas are listed when they intersect that area.

## Still needed

- Province of Gelderland policy documents, to replace the Utrecht references
  in the original project sketch.
