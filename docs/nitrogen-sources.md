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
| NH₃ emissie | Emissieregistratie (RIVM e.a.) | Reeks 1990–2024 | Municipal level to verify | 1990–2024 | CSV (manual export) | Emissie | Partly verified |
| NOx emissie | Emissieregistratie (RIVM e.a.) | Reeks 1990–2024 | Municipal level to verify | 1990–2024 | CSV (manual export) | Emissie | Partly verified |
| Depositie | RIVM | GDN `depo_NTOT`, `depo_NHx`, `depo_NOy` | National 1x1 km grid, clipped to Nijkerk + 15 km | 2025; prognosis 2030–2040 | Zip with ESRI ASCII grid, EPSG:28992 | Weergave | Verified |
| Natura 2000 | PDOK / RVO | WFS `natura2000:natura2000` | Veluwe and surroundings | Current | GeoJSON, EPSG:28992, CC0 | Kaart | Verified |
| Depositie per habitat | AERIUS Monitor | To determine | Veluwe | – | – | Weergave | Not checked |
| Landgebruik | PDOK / CBS | To determine | Nijkerk | – | GIS | Context | Not checked |

The last two rows are not needed for v1.

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
- **To verify:** whether the export module offers municipality level for
  NH₃ and NOx. Older documentation lists municipality, 5x5 km and 1x1 km.
  If only grid cells are available, clip 5x5 km cells to the Nijkerk boundary.
- **Script:** `scripts/nitrogen/load_emissions.py` (to write)

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

## Still needed

- A cited source for which nearby Natura 2000 areas are nitrogen-sensitive.
- Province of Gelderland policy documents, to replace the Utrecht references
  in the original project sketch.
