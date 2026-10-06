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
| Overschrijding per hexagoon | RIVM, AERIUS open data | WFS `base_geometries:hexagons`, `depositions:depositions` | Map area | 2024 (the only year in the layer for the map area) | WFS | Not used yet | Field meanings fit the data in a test (2026-10-06); no official field definition found |
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
  critical deposition value (KDW, mol N per ha per year) and one coverage
  value per record. A record is one habitat type in one Natura 2000 area
  (all its polygons together), so the coverage is not per polygon. Covers
  Natura 2000 areas only.
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
  verified; `L4030` only from secondary sources; for the hexagon fields
  `exceeding` and `above_cl` a rule was found that fits every hexagon in the
  map area, but no official field definition.
- **Note on years:** the open data deposition layer holds one year for the
  map area, 2024 (read on 2026-10-06), not 2023 as noted here earlier. The
  AERIUS Handboek Data 2025 lists 2020 and 2023 as the reference years of
  Monitor 2025; why the open data layer carries 2024 is not explained in
  the documents checked. The RIVM GDN map on the page is for 2025. Do not
  combine the two in one figure.
- **Script:** `scripts/nitrogen/fetch_aerius_habitats.py`. The download is
  kept in `data/nitrogen/raw/` (not committed) and reused on later runs.

## AERIUS definitions: verification

Checked on 2026-10-06 in three steps: against RIVM and BIJ12 documents,
then against what the service returns, then with a test on all hexagons in
the map area. The statuses in the table are the outcome after all three.

| # | Question | Status | Finding |
|---|---|---|---|
| 1 | What does "relevant" mean in `relevant_habitats`? | Verified for hexagons; applied to the habitat layer by its metadata | See 1 below |
| 2 | Is nitrogen-sensitive a KDW below 2,400 mol? | Verified | See 2 below |
| 3 | What is code `L4030`? | A habitat-of-species type, per a provincial source; species list from secondary sources only | See 3 below |
| 4 | What does hexagon field `exceeding` mean? | Fits the data; no official field definition | Deposition above KDW minus 70 mol. See "Field test" below |
| 5 | What does hexagon field `above_cl` mean? | Fits the data; no official field definition | Deposition above the KDW. See "Field test" below |
| 6 | How do hexagon area and habitat coverage relate? | Hexagon and `surface` confirmed on the data; `coverage` narrowed down, not defined | See "Field test" below |

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
map area, so it matters for the table.

Added on 2026-10-06 from a primary provincial source: the PAS-gebiedsanalyse
057 Veluwe (Provincie Gelderland, 15 December 2017) uses "LGt4030" and "ZG
LGt4030" next to LGt01, LGt09, LGt13 and LGt14 in its nitrogen load figures
(Figure 3.4a; text on p. 15). So the province itself treats it as a
leefgebiedtype, separate from habitat type H4030. That document gives no
definition and no species list in the part read (first 41 pages), and the
Natuurdoelanalyse Veluwe (2023) does not mention it in its first 16 pages.
The species list therefore still rests on the two consultancy reports.
Asked of the AERIUS helpdesk on 2026-10-06.

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
deposition above KDW minus 70 mol. The test on the data (see "Field test"
below) shows which field carries which. Still open: confirmation of the
field definitions by AERIUS itself. Asked on 2026-10-06 through the AERIUS
contact form (Landelijk Informatiepunt Stikstof en Natura 2000), together
with the deposition year, `coverage` and `L4030`. Answer pending.

**6. Hexagon area and coverage.**

- A hexagon at the finest level is 1 ha (zoom level 1). Source: RIVM
  metadata of the link table; Handboek Werken met Calculator 2025, p. 27
  ("één hectare rondom dat rekenpunt").
- A hexagon is relevant when it *partly* overlaps relevant habitat. No
  minimum share is stated in the definition.
- The link table (`hexagons_to_relevant_habitats`) records per hexagon which
  relevant habitat types are present. For its fields see "Field test".
- The `coverage` field of `relevant_habitats` is not defined in the AERIUS
  documents checked. Probable meaning, from the BIJ12 Methodiekdocument
  (2015, p. 21): one mapped polygon can hold several habitat types, "waarbij
  per type het percentage in het vlak wordt vermeld". For search areas no
  percentage is recorded: "het percentage is 100% zoekgebied" (p. 8).
- Two search-area types in the data have an area-wide coverage below 1
  (ZGH3130, ZGH6230dka), which does not match that rule. See "Field test",
  point 7.
- Related: for the unknown type H9999 the KDW is "de laagste KDW van een
  aangewezen habitattype of leefgebied van een aangewezen soort binnen het
  Natura 2000-gebied" (RIVM 2025-0020, p. 29). H9999 does not occur in the
  map area.

### Observed in the service (2026-10-06)

From the output of `inspect_aerius.py`, run on 2026-10-06. Field names and
types are as served; the meanings in the last column are readings, not
definitions.

| Layer | Features in map area | Fields (besides ids and geometry) | Reading |
|---|---|---|---|
| `base_geometries:hexagons` | 71,442 | `zoom_level`, `relevant`, `exceeding`, `above_cl`, `extra_assessment` (all boolean), `critical_deposition` | Both samples were zoom level 4 and 5 with every field empty. The field test confirmed that the flags are filled at zoom level 1 only |
| `depositions:depositions` | 46,826 | `year`, `zoom_level`, `total_deposition` | Samples: year 2024, zoom level 1, values 1,895 and 2,058. Unit not stated by the service |
| `base_geometries:hexagons_to_relevant_habitats` | 81,522 | `zoom_level`, habitat type, `critical_deposition`, `surface`, `coverage` | `surface` samples 9,334.45 and 10,000.00: fits m2 of habitat inside a 1 ha hexagon |
| `base_geometries:relevant_habitats` | 41 | habitat type, `critical_deposition`, `coverage` | Sample coverage 0.47026383437375235 for a whole area and type: looks like a calculated average, not a recorded percentage |
| `base_geometries:extra_assessment_hexagons_to_habitats` | 0 | habitat type, `critical_deposition` | Nothing in the map area |

What this changes:

- `exceeding` and `above_cl` are yes/no flags, so the two-candidate reading
  under 4 and 5 can be tested: join hexagons and depositions on
  `receptor_id` and `zoom_level`, and compare `total_deposition` with
  `critical_deposition`. Done in the field test below.
- `coverage` in `relevant_habitats` is one value per Natura 2000 area and
  habitat type. The field test supports reading it as an average over the
  whole area.
- `coverage_weighted_ha_in_map_area` in the processed habitat file multiplies
  the area inside the map area by that area-wide value. It is therefore an
  approximation for the map area. The page does not show this figure.

### Field test on the data (2026-10-06)

All features of three layers in the map area (bounding box of Nijkerk plus
15 km) were downloaded and compared: 71,442 hexagons, 46,826 deposition
values, 81,522 hexagon-habitat rows. Run by the author on 2026-10-06 with
`scripts/nitrogen/inspect_aerius_fields.py`, which only reads from the
service and writes a report to `data/nitrogen/raw/` (not committed).

A rule that fits the data is not an official definition. It shows which
reading is consistent with what the service publishes.

**1. Where the flags are filled.** Only at zoom level 1 (52,932 hexagons).
At zoom levels 2 to 5 every field is empty. `receptor_id` is not unique on
its own; `receptor_id` plus `zoom_level` is (no repeated keys).

**2. `relevant`.** 43,770 hexagons are relevant, 9,162 are not. Exactly the
relevant ones have a KDW, a deposition value and at least one row in the
link table. The smallest `surface` in the link table is 0.0 m2, which fits
"(deels) overlapt" without a minimum share.

**3. Deposition.** One year, 2024. 43,770 values at zoom level 1 (one per
relevant hexagon) and 3,056 at zoom level 4, which covers the whole map
area (the Handboek Data 2025 describes a nationwide map on 64 ha hexagons).
Range 643 to 8,301. The service does not state the unit; mol N/ha/year is
assumed.

**4. `above_cl` and `exceeding`.** With margin = `total_deposition` minus
`critical_deposition`, for the 43,770 relevant hexagons:

| `exceeding` | `above_cl` | Hexagons | Margin, lowest | Margin, highest |
|---|---|---|---|---|
| true | true | 43,664 | +0.5 | +5,668.6 |
| true | false | 59 | -67.7 | -0.2 |
| false | false | 47 | -1,381.6 | -75.3 |

- `above_cl` is true exactly when deposition is above the KDW: fits all
  43,770 hexagons.
- `exceeding` is true exactly when deposition is above KDW minus 70 mol:
  fits all 43,770 hexagons. This is the "(naderend) overbelast" of RIVM
  2025-0020, so `exceeding` includes hexagons that are still below the KDW.
- The rule "deposition above the KDW" does not reproduce `exceeding`: it
  fails for the 59 hexagons in the middle row.
- Limits of the test: no hexagon has a margin between -75.3 and -67.7, so
  the data fits any threshold in that range; 70 is the documented one.
  Whether the boundary itself counts (> or >=) cannot be seen. One map area,
  one year.

**5. Hexagon KDW.** In all 43,770 relevant hexagons the hexagon
`critical_deposition` equals the lowest KDW of its habitat types in the link
table.

**6. `surface`.** Every row geometry in the link table is a full 1 ha
hexagon (10,000 m2 within 1 m2). `surface` runs from 0 to 10,000, so it
fits m2 of that habitat type inside the hexagon. It is not multiplied by
`coverage`: in 3,183 rows `surface` is larger than 1 ha times `coverage`.
In 1,887 hexagons the surfaces of all types add up to more than 1 ha, so
types overlap each other inside a hexagon.

**7. `coverage`.**

- It is not the share of the hexagon that the habitat covers: rows with a
  `surface` well below 10,000 m2 have coverage 1.
- Lg types and `L4030` always have coverage 1 (54,674 rows). H types are
  below 1 in 7,178 of 25,014 rows, lowest 0.05. Search-area types are below
  1 in 363 of 1,834 rows, in ZGH6230dka and ZGH2330 only.
- The single value per type in `relevant_habitats` is close to, but not the
  same as, the surface-weighted mean of the hexagon values in the map area
  (for example H4030 0.898 against 0.887, H5130 0.543 against 0.890). It
  matches where the type lies almost wholly in the map area (ZGH2330 0.9997
  in both). This fits an average over the whole Natura 2000 area.
- Reading that fits all of this: the share of the mapped area that the
  habitat type really occupies, as in the BIJ12 percentages. Not confirmed
  by an AERIUS document. The BIJ12 rule of 2015 that search areas are
  always 100% does not hold in this data.
- `L4030` behaves like the Lg types (always 1) and unlike H4030, which
  supports reading it as habitat of species (leefgebied), see point 3 above.

**What the flags show for the map area.** Of the 43,770 relevant hexagons,
43,664 (99.8%) are above their KDW and 43,723 (99.9%) are flagged
`exceeding`; 47 are not. For comparison, RIVM 2025-0020 counts 173,622 of
252,258 relevant hexagons nationally as (naderend) overbelast (69%). The
hexagons in the map area belong to the Veluwe; the nearest relevant habitat
is about 0.7 km outside the municipal boundary.

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

## Provincial policy context (Gelderland)

Checked on 2026-10-06. This is a reference list, not content for the page:
the Stikstofmonitor shows data, not policy. The original project sketch
with Utrecht references is not in this repo, so nothing was replaced here.
Policy in this field changes fast; recheck before quoting any of it.

"Check" says how far each row was verified: *official* = read on a
government site or in the published regulation; *reported* = from news
coverage only.

| Document or programme | Body and date | What it is | Check |
|---|---|---|---|
| Stikstofreductiegebieden (strokenbeleid), in the Omgevingsverordening Gelderland | Provinciale Staten, adopted 23 or 24 September 2026 (sources differ); in force from October 2026 | "Stikstofgevoelige natuur die overbelast is en stroken van maximaal 500 meter eromheen", in four areas: Veluwe, Landgoederen Brummen, Bekendelle, Willinks Weust | Definition and areas: official. Dates and rules: reported |
| Versnellingsaanpak Stikstof | Province; follows the Gelderse Maatregelen Stikstof (from 2019) after the 2024 progress report | Four tracks: source measures (including the strips), extra nature measures, permits and enforcement, information and monitoring | Official |
| Aanpak Veluwe | Rijk, province, 2 water boards, 21 municipalities; at least 10 years, to 2035; implementation started June 2026 | "Herstel van de natuur én ruimte voor wonen, werken en ondernemen" on and around the Veluwe | Programme: official. Start, budget and target: reported |
| Beleidsregels salderen Gelderland 2026 | Gedeputeerde Staten, adopted 27 January 2026; in force 10 February 2026; amended version in force 18 July 2026 | Rules for internal and external netting (salderen) when a nature permit is granted. Province-wide | Official (CVDR756662). Percentages not recorded here: two readings gave different numbers |
| Vitaal landelijk gebied Gelderland (VLGG) | Gedeputeerde Staten decided at the end of September 2024 not to adopt it for now | Concept programme for the rural area. Shelved after the cabinet withdrew the Transitiefonds and the NPLG. Named Veluwe and Gelderse Vallei among its priority areas | Official for 2024; later status not checked |
| Natuurdoelanalyse Veluwe | Provincie Gelderland, final concept 5 June 2023 | State of the nature goals of the Veluwe, with KDW exceedance per habitat type | Official |
| Advice on the Natuurdoelanalyse Veluwe | Ecologische Autoriteit, 25 April 2024 | "Vermindering van de stikstofbelasting voor de Veluwe een harde voorwaarde is voor natuurherstel" | Official |
| Beheerplan Natura 2000 Veluwe; PAS-gebiedsanalyse 057 Veluwe | Provincie Gelderland, December 2017 | Older management plan and nitrogen analysis. Useful for definitions (see `L4030`), not for current policy | Official |
| Gelderse gebiedsagenda Foodvalley | Province with eight municipalities, Nijkerk among them | Regional agenda; names "de transitie van het landelijk gebied (gericht op onder andere stikstof, bodem, water, landbouw, natuur, klimaat)" | Official; no date on the page |
| Gelderse Stikstofbank | Province | "Wij nemen op dit moment geen nieuwe aanvragen in behandeling" | Official |

Rules in the stikstofreductiegebieden, as reported (Nieuwe Oogst, 24
September 2026; not read in the regulation itself): no new livestock farms
and no new combustion installations from the entry into force; no nitrogen
fertilizer from 2030; emission requirements for barns and combustion
installations and emission-free mobile machinery from 2035, for governments
from 2028.

### What this means for Nijkerk

- **Is Nijkerk inside a strip?** Not checked on the provincial map. By this
  repo's own figure the nearest relevant nitrogen-sensitive habitat is about
  0.7 km outside the municipal boundary, which is more than 500 m. On that
  figure the strip would not reach the municipality. The figure is rounded
  to 0.1 km and uses the AERIUS habitat layer, and the province draws its
  own boundary, so this needs to be looked up on the provincial map before
  it is stated anywhere.
- **Province-wide rules apply.** The Beleidsregels salderen hold for every
  nature permit in Gelderland, Nijkerk included.
- **Aanpak Veluwe.** Whether Nijkerk is one of the 21 municipalities was not
  confirmed from an official list. Two council groups in Nijkerk (CDA,
  CU-SGP) put questions to the college about it (StadNijkerk, 3 October
  2026). Reported, without a named source document: a target of at least
  65% less nitrogen emission in and around the Veluwe against 2019, and 300
  million euro from the Rijk for the first phase.
- **Regional setting.** Nijkerk is part of Regio Foodvalley, which spans
  Gelderland and Utrecht. This may be where the Utrecht references in the
  first sketch came from. Provincial rules for Nijkerk are Gelderland rules.

Sources for this section:

- [Provincie Gelderland: Stikstof (overview)](https://www.gelderland.nl/themas/stikstof)
- [Provincie Gelderland: Stikstofreductiegebieden](https://www.gelderland.nl/themas/stikstof/stikstofreductiegebieden)
- [Provincial map of the stikstofreductiegebieden (geoportaal)](https://geoportaal.gelderland.nl/portaal/apps/experiencebuilder/experience/?id=08388c65b5174fd696babce99b50d253)
- [Provincie Gelderland: Versnellingsaanpak Stikstof](https://www.gelderland.nl/themas/stikstof/versnellingsaanpak-stikstof)
- [Provincie Gelderland: Aanpak Veluwe](https://www.gelderland.nl/themas/organisatie/samenwerkingen/aanpak-veluwe)
- [Beleidsregels salderen Gelderland 2026 (CVDR756662)](https://lokaleregelgeving.overheid.nl/CVDR756662)
- [Provincie Gelderland: Voortgang programma Vitaal landelijk gebied Gelderland](https://www.gelderland.nl/voortgang-programma-vitaal-landelijk-gebied-gelderland-1)
- [Ecologische Autoriteit: Veluwe, provincie Gelderland (analysis and advice)](https://www.ecologischeautoriteit.nl/advies/veluwe-provincie-gelderland/)
- [PAS-gebiedsanalyse 057 Veluwe (Provincie Gelderland, 2017)](https://www.natura2000.nl/sites/default/files/PAS/Gebiedsanalyses_vigerend/057_Veluwe_gebiedsanalyse_15-12-2017_GL.pdf)
- [Gelderse gebiedsagenda Foodvalley](https://provincie.gelderland.nl/geldersegebiedsagenda/foodvalley)
- [Nieuwe Oogst, 24 September 2026: Groen licht Gelderse stikstofaanpak](https://www.nieuweoogst.nl/nieuws/2026/09/24/groen-licht-gelderse-stikstofaanpak-verbod-op-nieuwvestiging-in-zones-gaat-in)
- [Binnenlands Bestuur: Gelderland legt als eerste provincie stikstofstroken vast](https://www.binnenlandsbestuur.nl/ruimte-en-milieu/gelderland-legt-als-eerste-provincie-stikstofstroken-vast)
- [Veluwe FM: Gelderland stelt stikstofmaatregelen voor Veluwe vast](https://veluwefm.nl/gelderland-stelt-stikstofmaatregelen-voor-veluwe-vast/)
- [Gemeente Putten: Zonering (stikstof)](https://www.putten.nl/Milieu_Natuur/Milieu/Zonering)
- [StadNijkerk, 17 June 2026: Grote gebiedsaanpak Veluwe van start](https://www.stadnijkerk.nl/lokaal/duurzaamheid/1286784/grote-gebiedsaanpak-veluwe-van-start-overheden-werken-aan-sti)
- [StadNijkerk, 3 October 2026: CDA en CU/SGP over Aanpak Veluwe](https://www.stadnijkerk.nl/lokaal/politiek/1315615/cda-en-cu-sgp-willen-naadje-van-de-kous-weten-rond-plan-aanpa)

## Still needed

- Look up on the provincial map whether any part of Nijkerk lies in a
  stikstofreductiegebied.
- Read the adopted text of the Omgevingsverordening for the rules and dates
  now taken from news coverage.
- Confirm whether Nijkerk is a party to the Aanpak Veluwe.
- The answer of the AERIUS helpdesk (asked 2026-10-06).
