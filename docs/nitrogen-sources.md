# Nitrogen module: data source register

Last checked: 2026-10-04 (AERIUS definitions: 2026-10-06)

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
| Overschrijding per hexagoon | RIVM, AERIUS open data | WFS `base_geometries:hexagons`, `depositions:depositions` | Map area | Deposition year 2023 | WFS | Not used yet | Fields seen; `exceeding` and `above_cl` still not verified (2026-10-06) |
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
- **Spatial allocation (Emissieregistratie, "Ruimtelijke verdeling van
  emissies over Nederland"):** emissions are distributed with
  "verdeelsleutels, waarbij de verdeling wordt benaderd via gegevens die een
  sterk verband hebben met de emissiebronnen". For large point sources
  "zijn emissie en locatie beide bekend". For road traffic "wordt
  bijvoorbeeld de verkeersintensiteit gebruikt". Municipal figures are
  therefore allocations, not measurements, and include through traffic.
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
- **Official description (Nationaal Georegister):** "Deze webservice bevat
  de stikstofgevoelige habitattypen binnen een Natura2000-[ge]bied die ook
  daadwerkelijk relevant zijn bevonden voor AERIUS 2025". Published
  2025-10-07. Licence: public domain (CC Public Domain Mark 1.0), no
  restrictions. The page wording "relevante stikstofgevoelige habitattypen"
  follows this description.
- **Codes:** H = habitat type. ZGH = search area: indications, but no
  certainty, that the type is present (source: BIJ12 Methodiekdocument
  kartering habitattypen). Lg = "stikstofgevoelige leefgebieden van soorten
  van de Vogel- en Habitatrichtlijn" (source: natura2000.nl,
  herstelstrategieën; Lg13 and Lg14 match the names in the data). `L4030`:
  see point 3 of the verification section below.
- **Definitions checked on 2026-10-06:** see "AERIUS definitions:
  verification" below. In short: "relevant" and the 2,400 mol threshold are
  verified; `L4030` only from secondary sources; the hexagon fields
  `exceeding` and `above_cl` are still not verified.
- **Note on years:** AERIUS deposition per hexagon is for 2023, the RIVM GDN
  map on the page is for 2025. Do not combine them in one figure. The AERIUS
  Handboek Data 2025 lists 2020 and 2023 as the reference years of Monitor
  2025.
- **Script:** `scripts/nitrogen/fetch_aerius_habitats.py`. The download is
  kept in `data/nitrogen/raw/` (not committed) and reused on later runs.

## AERIUS definitions: verification

Checked on 2026-10-06 against RIVM and BIJ12 documents. The AERIUS service
itself could not be queried in this check, so nothing below was tested
against live field values.

| # | Question | Status | Finding |
|---|---|---|---|
| 1 | What does "relevant" mean in `relevant_habitats`? | Verified for hexagons; applied to the habitat layer by its metadata | See 1 below |
| 2 | Is nitrogen-sensitive a KDW below 2,400 mol? | Verified | See 2 below |
| 3 | What is code `L4030`? | Secondary sources only | See 3 below |
| 4 | What does hexagon field `exceeding` mean? | Not verified | See 4 and 5 below |
| 5 | What does hexagon field `above_cl` mean? | Not verified | See 4 and 5 below |
| 6 | How do hexagon area and habitat coverage relate? | Hexagon verified; `coverage` probable | See 6 below |

**1. "Relevant".** The RIVM metadata for the AERIUS link table between
hexagons and relevant habitats says: "De voorwaarden onder welke een
stikstofgevoelig habitattype ook daadwerkelijk relevant wordt bevonden zijn
beleidsmatig vastgesteld." The conditions are written out for hexagons in
RIVM-briefrapport 2025-0020 (p. 29-30) and 2024-0078 (p. 25):

- Habitats Directive areas: a hexagon is relevant when it (partly) overlaps
  "een stikstofgevoelig habitattype met een relevante doelstelling", "een
  onbekend stikstofgevoelig habitattype", or "het stikstofgevoelige
  leefgebied van een habitatsoort met een relevante doelstelling".
- Birds Directive areas: when it (partly) overlaps "het leefgebied van een
  soort met een doelstelling".
- In both cases the area must be designated (in draft or definitively) and
  a matching (draft or definitive) objective must apply at that location
  (2024-0078, p. 25).

Not found: a text that states these same conditions for the polygon layer
`relevant_habitats` itself. The page wording stays as it is ("volgens de
beleidscriteria"), which matches the metadata.

**2. Threshold.** "Habitattypen en leefgebieden van habitatsoorten zijn
stikstofgevoelig wanneer de KDW kleiner is dan 2.400 mol/ha/jr" (RIVM
2025-0020, p. 30; same in 2024-0078, p. 25; equivalent sentence in RIVM
report 2020-0174, p. 22). Consistent with the data: the highest KDW in the map area
is 2,399 (Lg01).

**3. `L4030`.** Not found in the AERIUS Handboek Data 2025, in the BIJ12
Methodiekdocument (2015), or in the first 41 pages of the Beheerplan Natura
2000 Veluwe. Two consultancy reports on the Veluwe use it:

- HaskoningDHV (2020), Compensatieplan stikstofgevoelig habitat Veluwe:
  "L4030 leefgebied droge heide", for the Birds Directive species
  boomleeuwerik, tapuit, grauwe klauwier, draaihals and wespendief, citing
  the Beheerplan Natura 2000 Veluwe.
- Pinkenberg assessment (gemeente Rozendaal, 2024): "L4030 Droge
  heiden-weinig vergrast", citing the PAS gebiedsanalyse (Provincie
  Gelderland, 2017).

Reading: dry heath that counts as habitat (leefgebied) of bird species, not
as habitat type H4030. This fits the Birds Directive rule under 1, and in
the data `L4030` has coverage 1.0 like the Lg types. It is 2,097 ha in the
map area, so it matters for the table. Still needed: the definition from a
provincial or AERIUS source.

**4 and 5. `exceeding` and `above_cl`.** No public document was found that
defines these field names (Handboek Data 2025, Handboek Calculator 2025,
Leeswijzer AERIUS Check, RIVM briefrapporten, RIVM metadata). What is
defined is the policy term behind them:

- "Vanaf een berekende achtergronddepositie (de meest recente
  depositiekaart) van 70 mol/ha/jaar onder de KDW geldt een hexagoon als een
  (naderend) overbelaste hexagoon" (RIVM 2025-0020, p. 30).
- National counts in that report (p. 27): 252,258 relevant hexagons, of which
  173,622 (naderend) overbelast.

So there are two candidate meanings: deposition above the KDW, and
deposition above KDW minus 70 mol. Which field carries which, and whether
either does, is not known. Do not publish a hexagon exceedance layer until
this is settled. Two ways to settle it:

1. Test on the data: for the hexagons in the map area, compare total
   deposition with `critical_deposition` and see which rule reproduces each
   field (run `inspect_aerius.py` for the field names first).
2. Ask the AERIUS helpdesk for the field definitions of the open data
   service.

**6. Hexagon area and coverage.**

- A hexagon at the finest level is 1 ha (zoom level 1). Source: RIVM
  metadata of the link table; Handboek Werken met Calculator 2025, p. 27
  ("één hectare rondom dat rekenpunt").
- A hexagon is relevant when it *partly* overlaps relevant habitat. No
  minimum share is stated in the definition.
- The link table (`hexagons_to_relevant_habitats`) records per hexagon which
  relevant habitat types are present. Its fields were not checked.
- The `coverage` field of `relevant_habitats` is not defined in the AERIUS
  documents checked. Probable meaning, from the BIJ12 Methodiekdocument
  (2015, p. 21): one mapped polygon can hold several habitat types, "waarbij
  per type het percentage in het vlak wordt vermeld". For search areas no
  percentage is recorded: "het percentage is 100% zoekgebied" (p. 8).
- Unexplained: two search-area types in the data have a coverage below 1
  (ZGH3130, ZGH6230dka), which does not match that rule.
- Related: for the unknown type H9999 the KDW is "de laagste KDW van een
  aangewezen habitattype of leefgebied van een aangewezen soort binnen het
  Natura 2000-gebied" (RIVM 2025-0020, p. 29). H9999 does not occur in the
  map area.

Sources for this section:

- [RIVM-briefrapport 2025-0020, Actualisatie AERIUS Calculator 2025](https://www.rivm.nl/bibliotheek/rapporten/2025-0020.pdf)
- [RIVM-briefrapport 2024-0078, Actualisatie AERIUS Calculator 2024](https://www.rivm.nl/bibliotheek/rapporten/2024-0078.pdf)
- [RIVM-rapport 2020-0174, Impactanalyse Actualisatie AERIUS Calculator 2020](https://www.rivm.nl/bibliotheek/rapporten/2020-0174.pdf)
- [RIVM metadata: AERIUS koppeltabel hexagonengrid en relevante-habitats](https://data.rivm.nl/meta/srv/metadata/bf6fb96b-16ea-4f30-9ac9-d66a18f674ad)
- [AERIUS Handboek Data 2025, v2](https://www.aeriusproducten.nl/site/binaries/site-content/collections/documents/2025/12/8/handboek-data-aerius-2025-v2/handboek-data-aerius-2025-v2.pdf)
- [AERIUS Handboek Werken met Calculator 2025](https://www.aeriusproducten.nl/site/binaries/site-content/collections/documents/2025/12/9/handboek-werken-met-aerius-calculator-2025/handboek-werken-met-calculator-2025.pdf)
- [BIJ12, Methodiekdocument kartering habitattypen Natura 2000 (2015)](https://www.bij12.nl/wp-content/uploads/2023/11/WW-BIJLAGE-09-%E2%80%93-Methodiekdocument-kartering-habitattypen.pdf)
- [HaskoningDHV (2020), Compensatieplan stikstofgevoelig habitat Natura 2000-gebied Veluwe](https://zoek.officielebekendmakingen.nl/blg-959322.pdf)
- [Pinkenberg, beoordeling stikstofdepositie (gemeente Rozendaal, 2024)](https://www.rozendaal.nl/wp-content/uploads/2024/07/Pinkenberg_Toelichting_Bijlage-7-Ecologische-effectbeoordeling.pdf)

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
