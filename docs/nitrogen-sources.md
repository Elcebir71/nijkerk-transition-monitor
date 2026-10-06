# Nitrogen module: data source register

Last checked: 2026-10-04 (AERIUS definitions: 2026-10-06)

## Purpose

An independent data project that makes public information about nitrogen,
emissions and nature in Nijkerk easy to find, check and understand.

For the method in two pages, see [`methodology.md`](methodology.md). This
register is the evidence behind it.

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

## Kinds of sources

Not every source in this register carries the same weight. When a figure is
quoted, say which kind it comes from.

| Kind | Examples in this register | What it may be used for |
|---|---|---|
| Official data | CBS, Emissieregistratie, RIVM GDN, PDOK, AERIUS open data, AERIUS Monitor, RIVM Monitor Natura 2000 | The page. Always with source, edition and reference date |
| Official evaluation | PBL, WUR and RIVM on the nitrogen programme; Ecologische Autoriteit | Context in these notes. Not a data source for the page |
| Policy, adopted | Omgevingsverordening Gelderland, Beleidsregels salderen | Reference only. "Official" only once read in the regulation itself |
| Policy, in preparation | Consultation notes, Kamerbrieven with intentions, a municipality's zienswijze | Reasoning and history. Never as the rule in force |
| Derived here | Field test on the AERIUS layers, the Veluwe aggregation, distance and overlap checks | Cross-check. If ever quoted, as "calculated here from ..." |
| Reported | News coverage, a firm's summary of a letter | A pointer, until the primary source has been read. Marked "reported" |

Position papers and opinion pieces on the nitrogen debate are not recorded
here. The Stikstofmonitor shows published figures and takes no side on
whether the KDW is the right yardstick.

## Register

| Onderwerp | Bron | Dataset | Gebied | Periode | Formaat | Gebruik | Status |
|---|---|---|---|---|---|---|---|
| Landbouw (dieren, bedrijven) | CBS | StatLine `80781ned` | Nijkerk (`GM0267`), Gelderland (`PV25`) | 2000–2025 | OData / JSON | Bronanalyse, trend | Verified |
| NH₃ emissie | Emissieregistratie (RIVM e.a.) | ER Reeks 1990-2024 Definitief | Nijkerk (`0267`), per sector | 2000–2024 (agriculture missing before 2000) | XLSX (manual export) | Emissie | Verified |
| NOx emissie | Emissieregistratie (RIVM e.a.) | ER Reeks 1990-2024 Definitief | Nijkerk (`0267`), per sector | 1990–2024 | XLSX (manual export) | Emissie | Verified |
| Depositie | RIVM | GDN `depo_NTOT`, `depo_NHx`, `depo_NOy` | National 1x1 km grid, clipped to Nijkerk + 15 km | 2025; prognosis 2030–2040 | Zip with ESRI ASCII grid, EPSG:28992 | Weergave | Verified |
| Natura 2000 | PDOK / RVO | WFS `natura2000:natura2000` | Veluwe and surroundings | Current | GeoJSON, EPSG:28992, CC0 | Kaart | Verified |
| Stikstofgevoelige habitats en KDW | RIVM, AERIUS open data | WFS `base_geometries:relevant_habitats` | Map area (Nijkerk + 15 km) | As served on the fetch date, 6 October 2026; the catalogue record then described AERIUS 2026 | GeoJSON via WFS, EPSG:28992 | Weergave, tabel | Verified |
| Overschrijding per hexagoon | RIVM, AERIUS open data | WFS `base_geometries:hexagons`, `depositions:depositions` | Map area | 2024 (the only year in the layer for the map area) | WFS | Not used yet | Fields officially described (Handboek Data AERIUS 2026, p. 47) and confirmed in a test on the data (2026-10-06) |
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
- **Result for the map area (2026-10-06, on the page):** 31 habitat types
  and species habitats, all in the Veluwe, 39,442 ha mapped; KDW from 500
  to 2,399. The fetch of 2026-10-05, on the page until then, gave 33 types
  and 39,436 ha; see "Still needed" for the comparison. Figures elsewhere
  in this register that describe the layer (such as 2,097 ha for `L4030`)
  are of the earlier fetch unless a date says otherwise.
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
  verified; `L4030` is defined in a provincial source; the hexagon fields
  `exceeding` and `above_cl` have an official description (Handboek Data
  AERIUS 2026, p. 47) and a rule that fits every hexagon in the map area.
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
| 3 | What is code `L4030`? | Defined in a provincial source: a leefgebiedtype, with its species | See 3 below |
| 4 | What does hexagon field `exceeding` mean? | Verified: official field description, and it fits the data | "naderend overbelast": deposition above KDW minus 70 mol. See 4 and 5 below |
| 5 | What does hexagon field `above_cl` mean? | Verified: official field description, and it fits the data | "overbelast": deposition above the KDW. See 4 and 5 below |
| 6 | How do hexagon area and habitat coverage relate? | Verified: `surface` and `coverage` have an official field description | Drawn surface, and percentage of it covered by the habitat. See 6 below |

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

Settled later on 2026-10-06 from the full text of that same PAS-gebiedsanalyse
(252 pages, PDF supplied by the author). Section 5.18, p. 110, lists the
seven leefgebiedtypen of the Veluwe that have a KDW of their own, among them
"Lgt 4030 Weinig vergraste heide en stuifzandheide (kdw 1071)". It explains
that the habitat (leefgebied) of a species can consist of nitrogen-sensitive
habitat types, nitrogen-sensitive leefgebiedtypen and parts that are not
nitrogen-sensitive. Table 2 (p. 110-111) gives Lgt 4030 as nitrogen-sensitive
leefgebied of seven designated bird species: tapuit, nachtzwaluw,
boomleeuwerik, draaihals, roodborsttapuit, wespendief and grauwe klauwier.
Table 5a (p. 114) gives 2,143 ha of LGt4030 in the Veluwe.

So `L4030` is the leefgebiedtype "weinig vergraste heide en stuifzandheide":
heath that is habitat of these bird species without being mapped as habitat
type H4030. Two differences with the present data: AERIUS labels it "Droge
heiden", and its KDW is now 714 where the 2017 document says 1,071. The KDW
values were revised in 2023; whether that revision is what changed this
value was not checked. The earlier text of this
point said the document gives no definition; that was based on a partial
reading and is superseded by this paragraph.

The Handboek Data AERIUS 2026 (p. 36) confirms the category, without a
list: besides the habitat types of the Habitats Directive, "zijn een
veertiental stikstofgevoelige aanvullende leefgebieden opgenomen". The KDW
values come from Wageningen Environmental Research, "Overzicht van kritische
depositiewaarden voor stikstof, toegepast op habitattypen en leefgebieden
van Natura 2000: Herziening 2023" (31 August 2023).

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
with the deposition year, `coverage` and `L4030`. Answer pending; for the
field definitions it is no longer needed, see below.

Settled later on 2026-10-06 from the Handboek Data AERIUS 2026, v1.0 (RIVM,
6 October 2026, 54 pages; PDF supplied by the author; chapter 5 and section
4.3-4.4 read). Section 5.1, "Velden webservice hexagons" (p. 47):

| Veld | Type | Omschrijving |
|---|---|---|
| `relevant` | boolean | "Geeft aan of het hexagoon relevant is." |
| `exceeding` | boolean | "Waarde of het hexagoon naderend overbelast is." |
| `above_cl` | boolean | "Waarde of het hexagoon overbelast is." |
| `extra_assessment` | boolean | "Betreft hexagoon met een hersteldoel" |
| `critical_deposition` | integer | "Minimale kritische depositie in mol N/ha/jaar" |

- This is the official field description that was missing. Together with
  the definition of the terms it closes points 4 and 5: `above_cl` is
  "overbelast" (deposition above the KDW), `exceeding` is "naderend
  overbelast" (from 70 mol below the KDW). The field test found exactly
  this split.
- The 70 mol is in the term, not in the field table. Besides RIVM 2025-0020
  above, the online documentation of AERIUS Calculator 2025 (Resultaten,
  Weergave) says: "Er is sprake van bijna overbelasting wanneer de
  achtergronddepositie minder dan 70 mol onder de KDW ligt", and speaks of
  "de meest kritische depositiewaarde".
- `critical_deposition` of a hexagon is the lowest KDW in it ("Minimale"),
  as the field test showed.
- Which map decides: the "actuele depositiekaart", calculated on 1 ha
  hexagons, "is gebruikt voor het bepalen van de hexagonen met een
  naderende overbelasting" (p. 39).
- Correction of the earlier text of this point: "no public document was
  found that defines these field names" was wrong for the Handboek Data.
  The reading tool gets the text of the 2025 editions (v2, and v3 of 14
  April 2026) only up to p. 48, just before the field tables, and that
  limit was not noticed. The 2025 editions were not read beyond that page;
  the table above is from the 2026 edition.
- The Handboek Data AERIUS 2026 is dated 6 October 2026, the day of the
  field test. A fresh download that evening gave the same numbers as the
  first one, so the data did not change during that day. Whether it is
  AERIUS 2025 or AERIUS 2026 data, the service does not say. See "Still
  needed".

**6. Hexagon area and coverage.**

- A hexagon at the finest level is 1 ha (zoom level 1). Source: RIVM
  metadata of the link table; Handboek Werken met Calculator 2025, p. 27
  ("één hectare rondom dat rekenpunt").
- A hexagon is relevant when it *partly* overlaps relevant habitat. No
  minimum share is stated in the definition.
- The link table (`hexagons_to_relevant_habitats`) records per hexagon which
  relevant habitat types are present. For its fields see "Field test".
- RIVM's dashboard data defines the relevant surface as "ingetekend
  oppervlakte maal dekkingspercentage" (see "Showing exceedance" below).
  That supports reading `coverage` as this coverage percentage.
- Official field descriptions, Handboek Data AERIUS 2026: in the link
  table `surface` is "Ingetekende oppervlakte" and `coverage` is
  "Percentage dekking van het habitat" (p. 48-49); in `relevant_habitats`
  `coverage` is again "Percentage dekking van het habitat" (p. 50). So the
  relevant surface is drawn surface times coverage, as in RIVM's dashboard
  data. The handbook gives no more than these few words.
- Background to that description, from the BIJ12 Methodiekdocument
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
reading is consistent with what the service publishes. The official field
descriptions were found afterwards, in the Handboek Data AERIUS 2026 (see
points 4 to 6 above), and agree with the outcome below.

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
  habitat type really occupies, as in the BIJ12 percentages. The Handboek
  Data AERIUS 2026 describes the field as "Percentage dekking van het
  habitat", which agrees. The BIJ12 rule of 2015 that search areas are
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
- [AERIUS Handboek Data 2025, v3 (14 April 2026)](https://www.aeriusproducten.nl/documenten/2026/04/14/handboek-data-aerius-2025-v3)
- RIVM, Handboek Data AERIUS 2026, v1.0, 6 October 2026 (read from a PDF supplied by the author; link not recorded)
- [AERIUS Calculator 2025, online documentation](https://docs.aerius.nl/downloads/nl/calculator-2025.html)
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

One figure on the page does not come from that file: the share of the
nitrogen-sensitive surface of the Veluwe where deposition is not above the
KDW (0,7% in 2024, AERIUS Monitor M26). It was read from the screen, so it
is a constant in the page script (`PUBLISHED_EXCEEDANCE`) with its edition,
year and reading date, and it is shown as context for the whole Veluwe, not
as a figure for Nijkerk. Update it by hand when a new Monitor edition
appears. Source and reading: "A published figure for the Veluwe: AERIUS
Monitor" below.

## Showing exceedance: official figures and classes

Checked on 2026-10-06, to decide whether and how the page could show KDW
exceedance. Nothing is decided here and nothing was added to the page.

The RIVM report below was read in full text on 2026-10-06 (PDF supplied by
the author); page numbers are the printed ones.

**Official figure, national.** RIVM, Monitor stikstofdepositie in Natura
2000-gebieden 2026 (report 2026-0018):

- "In 2024 was de neerslag op 31 procent van de oppervlakte lager dan de
  KDW. Een jaar eerder was dat 30 procent." (p. 3)
- "Op basis van een berekening met gemiddelde weersomstandigheden bedroeg
  het oppervlak onder de KDW in 2024 31 procent." Mean exceedance in 2024:
  about 385 mol/ha/year (p. 63).
- The figure counts mapped nitrogen-sensitive habitat area. The current
  deposition is calculated at 16 ha resolution (p. 30). KDW values are from
  Wamelink et al. (2023) and run from 429 to 2,400 mol/ha/year (p. 19).

**No official figure for the Veluwe in this report.** The Veluwe is named
twice, without a number:

- "Op de Veluwe leidt bijvoorbeeld de ammoniakuitstoot van de landbouw in
  de Gelderse Vallei tot een hoge depositie." (p. 51)
- The expected fall in deposition "is het sterkst nabij landbouwgebieden
  zoals de Veluwe of het noorden van Limburg" (p. 56).

The first sentence matters for this project: it is RIVM, not this repo,
linking agricultural ammonia from the Gelderse Vallei to deposition on the
Veluwe. It can be quoted with its source. It is not a figure and says
nothing about Nijkerk specifically.

**Where a regional figure could come from.** The RIVM dashboard gives the
results nationally and "per provincie" (p. 33), not per Natura 2000 area.
The open data behind the report includes a "Dataset onderliggend aan
Dashboard" and a breakdown of KDW exceedance by categories of nature
(p. 33). Neither was read in this check. The XLSX with the figure data
holds national series only (read for the 2025 edition; no row per area).

**Official figures for Gelderland.** RIVM publishes the data behind its
dashboard as six workbooks (`RIVM-MIL_*_20260401.xlsx`; Monitor 2025 data,
database `monitor_2025_20250719`; supplied by the author, read on
2026-10-06). They are per province, not per Natura 2000 area. For Gelderland,
reference year 2023, at 16 ha:

| Gelderland, 2023 | Value | Netherlands |
|---|---|---|
| Relevant mapped nitrogen-sensitive surface | 83,623 ha | 171,842 ha |
| Share with deposition not above the KDW | 2.1% (1,754 ha) | 29.7% (51,040 ha) |
| Mean deposition | 1,649 mol/ha/year | 1,368 |
| Mean exceedance of the KDW | 456 mol/ha/year | 263 |
| Natura 2000 areas with nitrogen-sensitive nature | 13 of 16 | 130 of 162 |

Source: `Provinciekengetallen`. The national row in that file is at 1 ha.

Share of the surface per exceedance class (mol above the KDW), from
`exceedance_kdw_class`:

| Gelderland | None | 0-250 | 250-500 | 500-750 | 750-1000 | >1000 |
|---|---|---|---|---|---|---|
| 2023 (reference) | 2.1% | 5.3% | 15.9% | 43.3% | 28.4% | 5.0% |
| 2024 (historical series) | 1.9% | 5.0% | 20.6% | 55.6% | 15.1% | 1.8% |
| 2030 (prognosis) | 4.0% | 17.8% | 55.1% | 20.8% | 2.1% | 0.1% |
| 2035 (prognosis) | 7.4% | 23.3% | 60.6% | 8.2% | 0.5% | 0.0% |

Where the deposition on Gelderland's nitrogen-sensitive nature comes from,
2023, in mol/ha/year (`GemiddeldeDepositieOntwikkelingPrognoses`, scenario
Diagnose): Dutch agriculture 960 of 1,649 (58%), mobility 218, Germany 204,
Belgium 114. For the Netherlands as a whole agriculture is 686 of 1,358
(50%).

Inside or outside the province (`Depositieherkomst_binnenbuitenprovincie`,
an older data version, DASH 2024; rows added up here): agriculture inside
Gelderland 31% of the deposition load, agriculture elsewhere in the
Netherlands 23%, agriculture abroad 14%. All sources inside Gelderland
together: 38%.

These are RIVM's own figures, so they can be shown with a plain source
reference. They are about the province, not about the Veluwe or Nijkerk.
The licence of these workbooks is not stated in them; still to record from
the catalogue.

The same workbooks define terms used elsewhere in this register:

- Relevant surface: "Het gekarteerde oppervlak (ingetekend oppervlakte maal
  dekkingspercentage) van alle stikstofrelevante kartering waaraan een
  doelstelling van een habitattype of soort is gekoppeld". This is the
  official wording behind `coverage`: a coverage percentage applied to the
  drawn area.
- "Zoomlevel 1 is 1 ha, zoomlevel 3 is 16 ha."

**A published figure for the Veluwe: AERIUS Monitor.** AERIUS Monitor has a
chart "Ontwikkeling stikstofbelasting" (under "Stikstofdepositie en natuur")
that gives, per Natura 2000 area, "De oppervlakte in het gebied met een
bepaalde onder- of overbelasting stikstof, in relatie tot de kritische
depositiewaarde, met prognoses over de ontwikkeling." Read from the screen
by the author on 2026-10-06, for the Veluwe and "Alle habitattypen en l..."
(the last entry is cut off on screen), in two editions; the percentage
printed next to each bar:

| Veluwe | Edition | Printed next to the bar |
|---|---|---|
| 2024 (historisch) | M26 | 0,7% |
| 2020 (historisch) | M25 | 0,3% |
| 2023 (historisch) | M25 | 0,5% |
| 2025 (prognose) | M25 | 0,5% |
| 2030 (prognose) | M25 | 2,3% |
| 2035 (prognose) | M25 | 5,7% |
| 2040 (doorkijkjaar) | M25 | 11,6% |

M26 shows one bar only, 2024, and no prognoses. That fits the 2026 report,
which did not renew them.

- What the percentage is: the bar is drawn on both sides of a line marked
  "KDW", on an axis "Oppervlakte (%) met onder-/overbelasting". The printed
  percentage matches the length of the part to the right of that line, so
  it is the share of the surface not above the KDW. The Monitor does not
  label the number; the reading rests on the drawing and on the segment
  tooltips below, which add up to it.
- The segments carry the class names of the legend recorded under "Classes"
  below. Tooltips read for 2024 in M26: "Sterke overbelasting (3,6%)",
  "Matige overbelasting (95,4%)" and "Geen overbelasting (0,5%)". Tooltips
  read in the bars with prognoses (the printed values are those of M25; the
  edition is not visible in these two screenshots): "Sterke overbelasting
  (13,5%)" for 2020, "Lichte overbelasting (3,4%)" for 2030 and "Bijna
  overbelast (3,3%)" for 2035. The other segment values were not read.
- The printed percentage includes "bijna overbelast". In 2035 that segment
  (3,3%) lies right of the KDW line and inside the bar that carries 5,7%;
  the rest of that part, about 2,4%, is then "geen overbelasting". For 2024
  the printed 0,7% is likewise more than "geen overbelasting" alone (0,5%).
  "Lichte overbelasting" is the palest segment left of the line.
- The Veluwe in 2024 (M26), share of the surface per class:

  | Class | Share | How obtained |
  |---|---|---|
  | Sterke overbelasting (≥2x KDW) | 3,6% | tooltip |
  | Matige overbelasting (>70 mol boven KDW, <2x KDW) | 95,4% | tooltip |
  | Lichte overbelasting (≤70 mol boven KDW) | about 0,3% | 100 minus the rest |
  | Bijna overbelast (≤70 mol onder KDW) | about 0,2% | 0,7 minus 0,5 |
  | Geen overbelasting (>70 mol onder KDW) | 0,5% | tooltip |
  | Not above the KDW (the last two together) | 0,7% | printed next to the bar |

  The two "about" values are subtractions made here from rounded
  percentages, so each can be off by 0,1 point. Their tooltips were not
  read.
- Name the edition next to any figure. Do not read the step from M25 to M26
  as a trend: each edition recalculates, as RIVM's own series show (see
  "Editions and series differ" below).
- The prognoses are model results of the 2025 edition. The 2026 report says
  they may be too favourable (see the notes on the aggregation below).
- The figure that goes with the 31% of RIVM report 2026-0018 (Netherlands,
  2024) is the M26 one: 0,7% for the Veluwe in 2024.

So for the Veluwe a published share exists and no calculation of our own is
needed to state it. The aggregation below stays as a cross-check.

**A figure for the Veluwe, aggregated here from RIVM's hexagon data.** RIVM
publishes the data behind its exceedance map as a GeoPackage. The file
`RIVM-MIL_M25-Deposities_Overbelastingsklasse_20260401.gpkg` (Monitor 2025
data; supplied by the author, read on 2026-10-06) has one row per 16 ha
hexagon and year, with the Natura 2000 area name, `cartographic_surface`,
`deposition` and `distance_to_kdw`. Adding up the surface per class, with
`scripts/nitrogen/inspect_rivm_monitor_classes.py`:

| Veluwe | Below the KDW | 0-250 | 250-500 | 500-750 | 750-1000 | >1000 | Mean deposition | Mean exceedance |
|---|---|---|---|---|---|---|---|---|
| 2023 (reference) | 0.1% | 4.2% | 18.1% | 44.7% | 29.6% | 3.3% | 1,657 | 660 |
| 2030 (prognosis) | 0.6% | 19.4% | 58.8% | 20.4% | 0.8% | 0.0% | 1,390 | 393 |
| 2035 (prognosis) | 3.5% | 25.9% | 64.6% | 5.9% | 0.1% | 0.0% | 1,296 | 300 |

Shares are of the mapped nitrogen-sensitive surface; classes and means are
in mol N/ha/year above the KDW. In 2023, 77 of the 6,496 hexagons of the
Veluwe have a deposition at or below the KDW.

How far this can be trusted:

- It is an aggregation made here from RIVM values, not a figure published by
  RIVM. Say so wherever it is used.
- Check on the national total, same method against the 2025 report's own
  figure data:

  | Netherlands | Below the KDW, here | In the report | Mean deposition, here | In the report |
  |---|---|---|---|---|
  | 2023 | 30.3% | 29.6% | 1,364 | 1,365 |
  | 2030 | 33.2% | 32.7% | 1,153 | 1,154 |
  | 2035 | 35.9% | 35.4% | 1,076 | 1,077 |

  Class shares differ by at most 1.5 percentage points. The reason for
  this small gap has not been established.
- It is the 2025 edition: reference year 2023, prognoses from that edition.
  The 2026 edition reports on 2024 and did not renew the prognoses; it notes
  that fewer farms take part in the buy-out schemes than assumed (p. 56), so
  the prognoses may be too favourable.
- The file also stores a class per row (`kdw_class`). In 13,782 of 137,700
  rows it differs from the class that follows from the row's own
  `distance_to_kdw`. What the stored class is based on is not documented in
  the file, so it is not used here. For the Veluwe the difference is small
  (55 of 6,496 rows in 2023).
- The surface in the GeoPackage adds up to about twice RIVM's stated
  relevant surface (345,164 ha against 171,842 ha nationally; 163,623 ha
  for the Veluwe against 83,623 ha for all of Gelderland). The reason is
  not known. Shares and weighted means are not affected if the factor is
  the same everywhere, and the national check above passes, but do not
  quote hectares from this file.
- The result fits the official provincial figures: Gelderland has 2.1%
  below the KDW in 2023 and class shares close to those of the Veluwe,
  which is most of the province's nitrogen-sensitive surface.
- Against AERIUS Monitor M25 for the Veluwe (above), the share not above
  the KDW comes out lower here: 0.1% against 0,5% for 2023, 0.6% against
  2,3% for 2030, 3.5% against 5,7% for 2035. Both say that almost all of
  the Veluwe is above the KDW. The reason for the difference has not been
  established. What is known: both are on 16 ha hexagons. For AERIUS
  Monitor 2025 the release notes say "De stikstofdepositie is in
  tegenstelling tot voorheen beschikbaar op een resolutie van 16ha en niet
  meer op 1ha"; the Handboek Data AERIUS 2026 says the same of the Monitor
  maps (p. 40). How the Monitor adds up surface per class, and over which
  surface, was not checked. An earlier version of this note gave a
  difference in resolution as the likely cause; that was wrong. Where a
  share for the Veluwe is quoted, quote the Monitor's.
- Arkemheen and Veluwerandmeren do not occur in the file, in line with the
  AERIUS habitat layer.
- Still to record: the title and licence of the catalogue record this file
  comes from.

**Resolution matters little at national level.** Annex figure B.1 (p. 88),
for 2024 with average weather:

| Map resolution | Mean deposition (mol/ha/year) | Area below the KDW |
|---|---|---|
| 1 ha | 1,303 | 30.7% |
| 16 ha | 1,294 | 30.7% |
| 1 km2 | 1,261 | 31.1% |

The same page warns: "De depositiewaarde op een individueel punt op de kaart
heeft een grote onzekerheid." An average over a habitat is less uncertain
than a single calculation point. That is an argument against reading much
into single hexagons.

**Editions and series differ.** The dataset of the 2025 edition (report
2025-0021) gives 29.3% below the KDW for 2024 in its historical series,
which was provisional then. The 2026 edition gives 31%. Always name the
edition next to the figure.

**The KDW values themselves were revised in 2023.** RIVM report 2026-0018
uses the values of Wamelink et al. (2023), see above. A share "below the
KDW" that was calculated before that revision rests on other thresholds and
cannot be set next to a current one. So older forecasts for 2025 or 2030
are not a yardstick for today's figures. Which values changed, and by how
much, was not looked up here.

**Independent evaluation: PBL, WUR and RIVM (2026).** "Monitoring en
evaluatie van het programma Stikstofreductie en Natuurverbetering.
Syntheserapport 2026", PBL publication 5782, 12 March 2026, made "op
verzoek van het Ministerie van LVVN". Only the publication page was read on
2026-10-06, not the report. From that page:

- "De wettelijke doelen voor de verlaging van de stikstofdepositie op
  Natura 2000-gebieden worden niet gehaald".
- The share of nitrogen-sensitive nature below the KDW "is gestegen van
  ongeveer 21 procent in 2005 naar 30 procent in 2023". The 30% agrees with
  the 2025 monitor (29.6% for 2023, see the national check above).
- "Voor 2030 wordt 33 procent ingeschat met de meegenomen maatregelen,
  terwijl het doel voor dat jaar 50 procent is."
- "Het herstel van de natuur blijft achter bij wat er binnen de Europese
  Unie is afgesproken."

These are national figures. The page gives nothing for the Veluwe or for
Gelderland. Still to do if this is ever quoted: read the report itself.

**RIVM's own classes.** In this monitor RIVM classes exceedance in absolute
mol above the KDW: geen overschrijding, 0-250, 250-500, 500-750, 750-1000,
more than 1000 mol N/ha/year. These are not the AERIUS Monitor classes
below.

**The count in this repo is something else.** "43,664 of 43,770 relevant
hexagons above their KDW" (see "Field test") counts 1 ha hexagons in a box
of our own choosing, from the AERIUS open data. It is not a figure for the
Veluwe and cannot be set next to the 31%: a different area (a box around
Nijkerk against the whole country) and a different unit (number of
hexagons against hectares of mapped habitat). Resolution is not the
obstacle, as the table above shows. Keep the count as a technical check,
not as a headline figure.

**Why the open data carries 2024.** The Monitor 2026 reports on 2024, and
states that the current deposition "wordt daarnaast ook berekend op 1
hectare. Deze wordt gebruikt in AERIUS Calculator" (p. 88; also p. 30,
footnote 4). That fits the year 2024 in the open data layer. A reading, not
a statement by AERIUS.

**An older download of the same hexagon deposition.** RIVM also offers the
background deposition as a GeoPackage. The file
`RIVM-MIL_AchtergrondStikstofdepositie_20241001.gpkg` (supplied by the
author, read on 2026-10-06) has one layer, `ndep_2022`: total nitrogen
deposition for 2022 on 252,203 hexagons of 1 ha, one row per `receptor_id`.

- 252,203 is the national number of relevant hexagons given for AERIUS 2024
  in RIVM 2024-0078 (p. 26). In the Nijkerk map area the file has 43,770
  hexagons, the same number as the relevant hexagons in the open data
  service.
- It holds deposition only: no KDW, no area name, no class. It cannot give
  exceedance or a Veluwe figure on its own.
- It is an older product (2022, published 1 October 2024). Do not read the
  difference with the 2024 values of the service as a trend: each release
  recalculates.

**Classes.** AERIUS Monitor 2026 itself shows five classes, as the legend of
its map "Afstand tot de KDW" (tab "Stikstofdepositie en natuur", selection
M26, Veluwe, 2024; read from the screen by the author on 2026-10-06):

| Class | Legend text in AERIUS Monitor |
|---|---|
| Geen overbelasting | >70 mol onder KDW |
| Bijna overbelast KDW | ≤70 mol onder KDW |
| Lichte overbelasting KDW | ≤70 mol boven KDW |
| Matige overbelasting KDW | >70 mol boven KDW maar <2x KDW |
| Sterke overbelasting | ≥2x KDW |

- This settles the class thresholds from the primary source. An older
  legend (AERIUS Monitor of January 2022, in a Provincie Zuid-Holland
  document) had four classes, without "licht"; RIVM reports say "(naderend)
  overbelast" where the Monitor legend says "bijna overbelast".
- The first two boundaries match the field test: `exceeding` turns true at
  70 mol below the KDW, `above_cl` at the KDW.
- AERIUS Monitor has a second map, "Afstand tot de KDW per habitat type",
  which shows the class for one chosen habitat type.
- On the Veluwe map for 2024 most hexagons are "matige overbelasting", with
  scattered "sterke overbelasting" and a few green ones. So at class level
  the map does show spatial differences. The Monitor draws coarse hexagons
  at this zoom; how it aggregates the 1 ha values into them is not known.
  Shares of the surface are in the Monitor's chart "Ontwikkeling
  stikstofbelasting" (see "A published figure for the Veluwe" above).
- The two hexagon flags in the open data give three steps without any
  calculation of our own: neither flag (geen), `exceeding` only (bijna),
  `above_cl` (above the KDW: licht, matig and sterk together). In the map
  area that is 47, 59 and 43,664 hexagons.
- Splitting "above the KDW" into licht, matig and sterk needs a comparison
  of deposition with the KDW per hexagon. With the official thresholds this
  is applying a published rule to two published values, but it is still a
  calculation made here. The alternatives are to link to AERIUS Monitor, or
  to use a layer that already carries the class (the Gelderland geoportaal
  is said to have one; not opened in this check).

**Other things read from AERIUS Monitor 2026 on the same day.**

- Its habitat type list for the Veluwe has "H4030 - Droge heiden", "L4030 -
  Droge heiden" and "ZGH4030 - Droge heiden" as three separate entries. So
  `L4030` is a type of its own in the official product. No definition is
  shown.
- Its habitat map legend: "Zeer stikstofgevoelig (KDW < 1400 mol N/ha/j)",
  "Stikstofgevoelig (KDW 1400 - 2400 mol N/ha/j)", "Beperkt stikstofgevoelig
  (KDW >= 2400 mol N/ha/j)". This agrees with the 2,400 mol threshold.
- Its deposition map ("Totale depositie") is in kg N/ha/j, with classes from
  ≤10 to >32. This repo uses mol N/ha/year; 1 kg N is about 71.4 mol.
- The year offered for M26 is 2024, the same year as in the open data.

**Three different deposition products.** Do not mix them in one figure:

| Product | Resolution | Year | Where it is used here |
|---|---|---|---|
| RIVM GDN map | 1 x 1 km | 2025 | The map on the page |
| AERIUS open data | 1 ha hexagons | 2024 | Field test only |
| RIVM Monitor Natura 2000 | 16 ha | 2024 | Not used; source of the 31% |

The Handboek Data AERIUS 2026 says the same of two of them (p. 40): the
maps in AERIUS Monitor "zijn niet direct te vergelijken met de
achtergronddepositie voor AERIUS Calculator vanwege verschillen in
methodiek", and their resolution "grover (16 ha) dan de
achtergronddepositie in AERIUS Calculator (1 hectare)". Its Table 4 gives
the years per Monitor edition: M2025 has reference years 2020 and 2023,
prognoses for 2025, 2030 and 2035, and an indicative prognosis for 2040.
That is what was read from the M25 chart.

Sources for this section:

- [RIVM, Monitor stikstofdepositie in Natura 2000-gebieden 2026 (publication page)](https://www.rivm.nl/publicaties/monitor-stikstofdepositie-in-natura-2000-gebieden-2026)
- [RIVM report 2026-0018 (PDF)](https://www.rivm.nl/bibliotheek/rapporten/2026-0018.pdf)
- [RIVM, dataset bij de Monitor 2026 (XLSX)](https://www.rivm.nl/documenten/dataset-bij-monitor-stikstofdepositie-in-natura-2000-gebieden-2026)
- [RIVM, Monitor stikstofdepositie in Natura 2000-gebieden 2025 (report 2025-0021 and its dataset)](https://www.rivm.nl/publicaties/monitor-stikstofdepositie-in-natura-2000-gebieden-2025)
- [RIVM dashboard Stikstofdepositie in Natura 2000-gebieden](https://stikstofdepositiedata.rivm.nl/)
- [PBL, WUR and RIVM (2026), Monitoring en evaluatie van het programma Stikstofreductie en Natuurverbetering, Syntheserapport 2026 (publication page)](https://www.pbl.nl/publicaties/monitoring-en-evaluatie-van-het-programma-stikstofreductie-en-natuurverbetering)
- [AERIUS Monitor (product page; the Monitor itself was read on screen)](https://www.aeriusproducten.nl/producten/aerius-monitor)
- [Release notes AERIUS Monitor 2025 (7 October 2025)](https://www.aeriusproducten.nl/documenten/2025/10/7/release-notes-aerius-monitor-2025)
- [Provincie Zuid-Holland, factsheets Gebiedsplan stikstof 0.5 (2022)](https://www.zuid-holland.nl/publish/pages/30032/pzhfactsheetsgebiedsplanstikstof0-5.pdf)
- [Natuurdoelanalyse Veluwe (Provincie Gelderland, 2023)](https://pas.ecologischeautoriteit.nl/files/ea/5123/013610-5123-natuurdoelanalyse-veluwe.pdf)

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
| Stikstofreductiegebieden (strokenbeleid), in the Omgevingsverordening Gelderland | Provinciale Staten, adopted 23 September 2026; in force 23 October 2026 | "Stikstofgevoelige natuur die overbelast is en stroken van maximaal 500 meter eromheen", in four areas: Veluwe, Landgoederen Brummen, Bekendelle, Willinks Weust | Definition, areas and dates: official. Rules: reported |
| Versnellingsaanpak Stikstof | Province; follows the Gelderse Maatregelen Stikstof (from 2019) after the 2024 progress report | Four tracks: source measures (including the strips), extra nature measures, permits and enforcement, information and monitoring | Official |
| "Weer ruimte voor boer, natuur en bouw" (national package) | Kabinet; Kamerbrief of the minister of LVVN, 26 June 2026 (2026D33108) | Emission targets for 2035 against 2019, farm emission norms, zones around nitrogen-sensitive Natura 2000 areas, and a separate target around the Veluwe. See "National package" below | Official (Kamerbrief). Mostly intentions still to be laid down in law |
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

### Nijkerk's position relative to the stikstofreductiegebieden

Nijkerk lies entirely outside the Gelderland stikstofreductiegebieden. The
municipality says so itself in its formal response (zienswijze) to the
draft 2026 amendment of the Omgevingsverordening Gelderland:

- Burgemeester en wethouders van Nijkerk to Gedeputeerde Staten van
  Gelderland, 31 March 2026, reference 2091532, on the draft laid open on
  12 February 2026: "Wij concluderen dat onze gemeente volledig buiten dit
  stikstofreductiegebied ligt", and so "deze regels geen of slechts een
  beperkte impact heeft op ons als gemeente". Read in the letter itself
  (4 pages). The letter does not mention the Aanpak Veluwe.
- The statement is about the draft. The amendment was adopted on 23
  September 2026 with strips of at most 500 m, and this repo's own figure
  (nearest relevant habitat about 0.7 km outside the municipal boundary)
  agrees with it. The adopted map itself was not opened.
- Geometric check, run by the author on 2026-10-06 with
  `scripts/nitrogen/inspect_reduction_area.py`: **no overlap**. The shortest
  distance from the municipal boundary to the zone is 172 m.
  - Layer tested: 141 of the provincial map service "Omgevingsverordening",
    "Voorbereidingsbesluit- Beperkingengebied stikstofemissie". Its own
    description: the nitrogen-sensitive habitats and leefgebieden of the
    Veluwe, Landgoederen Brummen, Willinks Weust and Bekendelle "met en
    strook of zone van 500 meter vanaf de grens van de stikstofgevoelige
    habitats en leefgebieden"; file created on 15 April 2025 for the
    preparatory decision that Provinciale Staten took on 16 April 2025.
  - The layer has four features; one (Veluwe) lies within 5 km of Nijkerk.
    It is the only layer of that service with "stikstof" in its name.
  - This agrees with the two other pieces of evidence: the municipality's
    statement, and this repo's distance to the nearest relevant habitat
    (about 0.7 km, so about 0.2 km to a 500 m strip).
  - Limits: it is the zone of the preparatory decision, not a layer of the
    regulation adopted on 23 September 2026, which was not found in the
    service. The adopted strips are at most 500 m, so they should not reach
    further. A geometric check on published boundaries is not a legal
    statement about any parcel.
- The margin is small. Nijkerk is outside the zone, but at its closest point
  by less than 200 m. "Entirely outside" is correct; "far from it" would not
  be.

Keep two things apart:

- Outside the stikstofreductiegebied: the zone rules (no new livestock
  farms, later requirements for barns and fertilizer) do not apply in
  Nijkerk.
- Not outside the nitrogen question: emissions in Nijkerk and deposition on
  the nearby Veluwe are what the Stikstofmonitor shows, and nearly all
  relevant hexagons in the map area are above their KDW (see "Field test").
  Being outside the zone says nothing about that.

### The province's consultation note on the strips (July 2025)

Provincie Gelderland, "Denkrichting invulling beleid stikstofstroken",
"Versie 8 juli 2025", 22 pages; annex 1 to a document for Provinciale
Staten. Supplied by the author as a PDF and read in full on 2026-10-06 (the
Staten site refuses automated reading). Page numbers are those printed in
the note.

Status: a text for consultation, "ter bespreking tijdens de participatie
tot en met oktober 2025". The note says of itself: "het gaat dus nog niet
om een besluit" (p. 3). It shows the province's reasoning and the rules it
was considering then. It is not the regulation adopted on 23 September
2026.

**How the strips are drawn.** This part was not open for discussion: "De
komst en de omvang van de strook (maximaal 500 meter) staan vast" (p. 6).

- Measured from the habitat itself, not from the Natura 2000 boundary: the
  strips rest on "de feitelijke ligging van de stikstofgevoelige
  habitattypen en leefgebiedtypen met een 'nee, tenzij'-oordeel in de
  natuurdoelanalyse" (p. 8).
- Not from hexagons. The national idea of April 2025 was a strip around
  overloaded hexagons; the province rejects that because hexagons "zijn een
  hulpmiddel in het AERIUS-model en volgen veel minder precies de contouren
  van de natuur" (p. 9).
- The same boundary as the preparatory decision of 16 April 2025: "Wat de
  provincie betreft verandert de strook van 500 meter niet en blijft deze
  hetzelfde als in het voorbereidingsbesluit" (p. 8), and no later changes
  are intended (p. 10). This supports the use of layer 141 for the
  geometric check above. Whether the adopted regulation kept exactly that
  boundary still has to be read in the regulation.
- On the boundary (p. 9-10) the province prefers "scenario 2": a project
  lies in the strip if 50% or more of its nitrogen emission comes from
  emission points inside the boundary, or if it emits more than 1,000 kg
  NH3-equivalent per year inside it. Farmland is judged per cadastral
  parcel: a parcel that lies for at least 50% inside the strip falls under
  the rules as a whole, other parcels of the same farm do not.
- A consequence, drawn here and not stated in the note: for land the rules
  follow the parcel, not the farm address. A farm based outside the strip
  can have parcels inside it.
- The strips at Winterswijk (Bekendelle, Willinks Weust) were conditional
  on the outcome of a local area process (p. 10).

**Figures the province gives.**

- The Veluwe: "de depositie op de Veluwe gemiddeld 1.650 mol per hectare
  per jaar" and "Bijna overal op de Veluwe (99%) wordt de KDW overschreden"
  (p. 4). This agrees with AERIUS Monitor (0,5% to 0,7% not above the KDW)
  and with the mean deposition of the aggregation made here (1,657).
- The aim and its size: a reduction of 70% of all nitrogen emissions in the
  500 m strip against 2018 would lower deposition by "circa 75 mol per
  hectare per jaar voor de Veluwe en circa 145 mol per hectare per jaar
  voor de Landgoederen Brummen" (p. 4). The province adds that "zeker méér
  nodig zal zijn dan strokenbeleid alleen" and that measures outside the
  strip "onontkoombaar" are.
- Why near the nature: of ammonia and nitrogen oxides about 5% and 2.5% of
  the emission lands within 500 m of the source; from a study of the
  Universiteit van Amsterdam, "9% van de ammoniakemissies van een boerderij
  komen binnen 500 meter terecht" (p. 3; the study is not named).
- Where the emission in the strips comes from: agriculture about 65%
  (p. 14), mobility about 25% (p. 18), businesses and public functions
  about 5% (p. 11), housing and building less than 5% (p. 20).
- Farms: about 8,500 in Gelderland, of which about 400 (5%) in the strips
  around the Veluwe and Landgoederen Brummen: nearly 80 arable, nearly 90
  with housed animals, about 50 dairy, about 150 other grazing livestock,
  about 15 other (p. 14). Totals for all strips; nothing per municipality.
- National policy at that time: the Kamerbrief of 25 April 2025
  (35334-362) spoke of "een strook van 250 meter rond overbelaste
  hexagonen"; the province kept 500 m because 250 m gives half the effect
  (p. 4, 8). The later national package is under "National package of June
  2026" below.

**Rules under consideration for agriculture** (p. 15; not the adopted
text): emission norms in kg ammonia per animal place for 2030 and 2035;
best available technique in half of a farm's barns by 2030 and in all by
2035; emission norms per hectare for arable and land-based livestock
farming; artificial fertilizer halved by 2030 and banned in 2035; a lower
norm and a maximum temperature for spreading slurry; external netting only
with a farm inside the strip, with 85% taken off; a minimum share of
permanent grassland. The province intended to let norms apply from 2030,
not only from 2035 (p. 15). The news report on the adopted rules, quoted
above, says no nitrogen fertilizer from 2030. Note and report differ; which
is right for the adopted text is not known until the regulation is read.

**For the technology note** (`docs/nitrogen-technology-research.md`):

- The province separates "innovatie" (techniques "die nog niet
  wetenschappelijk bewezen zijn en nog niet juridisch geborgd") from
  "modernisering" (proven and legally secured). Inside the strips only the
  second counts: "een bewezen technologie in de strook minstens 45%
  emissiereductie moet opleveren". Innovation policy "krijgt buiten de
  stroken vorm" (p. 16).
- For industrial manure processing in the strips it considers requiring
  that this is done indoors and with a chemical air scrubber (p. 13).

Not recorded from this note: its chapter on money (p. 22) and the subsidy
percentages. One date in the note is evidently a slip: a ruling of the Raad
van State "op 18 december 2025" that led to a proposal of 28 January 2025
(p. 6).

### National package of June 2026

"Weer ruimte voor boer, natuur en bouw", Kamerbrief of 26 June 2026. Read on
2026-10-06 in the text of the letter (twice) and checked against a summary
by an accountancy firm (Van de Graft Accountants, 15 July 2026; PDF supplied
by the author) and the PBL reflection of September 2026.

- **Emission targets for 2035 against 2019:** "42-46% (NH3) in de landbouw",
  "50% (NOx) in de mobiliteit", "50% (NH3) in de industrie". Interim target
  for agriculture, per the accountants' summary: 23-25% in 2030.
- **Around the Veluwe:** "Rond de Veluwe wordt met de provincie Gelderland
  naast de zonering 65-69% emissiereductie over een groter gebied
  afgesproken, dus ook buiten de zones." The letter does not say how that
  larger area is delimited.
- **Zones:** about 85 nitrogen-sensitive Natura 2000 areas get a zone of 500
  m, "vanaf de rand van het Natura 2000-gebied" (read once); 15 areas "met
  een hoge stikstofoverbelasting uit de zone" get 1,000 m. The areas are
  not named in the letter. Rules in the zones concern livestock density,
  manure application room and plant protection products.
- **Farm norm for dairy:** "0,164 kg NH3 en 92 kg CO2-eq uit stallen en
  mestopslag per fosfaatrecht voor de melkveehouderij in 2035". Norms for
  intensive livestock per animal place follow in early 2027.
- **Money:** "Voor de Veluwe en de Peel is reeds €600 miljoen gereserveerd".
- **PBL on the package** (publication 6203): "het emissiedoel komt binnen
  bereik, maar vooralsnog alleen met 'generieke korting'" (p. 6).

What this means for Nijkerk, and what it does not settle:

- **The 65-69% area probably matters more for Nijkerk than the 500 m zone.**
  It reaches beyond the zones by its own wording, and RIVM names the
  agriculture of the Gelderse Vallei as a source of high deposition on the
  Veluwe (see "Showing exceedance"). Whether Nijkerk lies in that area is
  not stated anywhere read so far.
- **The national zone is not the same as the provincial one.** The
  provincial zone is 500 m from nitrogen-sensitive habitats (layer 141:
  Nijkerk is 172 m outside). The national zone is measured from the edge of
  the Natura 2000 area and may be 1,000 m for areas with a high overload.
  The Veluwe boundary lies about 0.7 km from the municipal boundary, so a
  500 m national zone would not reach Nijkerk and a 1,000 m zone would.
  Which width the Veluwe gets is not known. Do not present "Nijkerk is
  outside the zone" as settled for the national approach.
- **Arkemheen and Veluwerandmeren** lie partly inside Nijkerk, but have no
  relevant nitrogen-sensitive habitat in the AERIUS layer. The national
  zones are for nitrogen-sensitive areas, so they are assumed not to get
  one. An assumption, not checked against a list.
- Most of the package is still intention: the letter announces legislation.

### What else this means for Nijkerk

- **Province-wide rules apply.** The Beleidsregels salderen hold for every
  nature permit in Gelderland, Nijkerk included.
- **Aanpak Veluwe.** Whether Nijkerk is one of the 21 municipalities was not
  confirmed from an official list. Two council groups in Nijkerk (CDA,
  CU-SGP) put questions to the college about it (StadNijkerk, 3 October
  2026). The target is 65-69% emission reduction "over een groter gebied"
  around the Veluwe (Kamerbrief of 26 June 2026, see "National package"
  below); earlier news coverage said "at least 65%". Reported in the news,
  not checked: 300 million euro from the Rijk for the first phase.
- **Regional setting.** Nijkerk is part of Regio Foodvalley, which spans
  Gelderland and Utrecht. This may be where the Utrecht references in the
  first sketch came from. The province made a similar slip: according to
  Nijkerk's zienswijze, the explanatory note to article 5.62a of the draft
  said that Nijkerk "aanhaakt bij de naastgelegen Utrechtse
  woningbouwregio", which the municipality calls incorrect: it belongs to
  the Foodvalley region. Provincial rules for Nijkerk are Gelderland rules.

Sources for this section:

- [Provincie Gelderland: Stikstof (overview)](https://www.gelderland.nl/themas/stikstof)
- [Provincie Gelderland: Stikstofreductiegebieden](https://www.gelderland.nl/themas/stikstof/stikstofreductiegebieden)
- [Provincie Gelderland: Denkrichting invulling beleid stikstofstroken, versie 8 juli 2025 (Staten document; read from a PDF supplied by the author)](https://gelderland.stateninformatie.nl/document/15783213/3/Bijlage+1+Notitie+%E2%80%98Denkrichting+invulling+beleid+stikstofstroken)
- [Kamerbrief "Weer ruimte voor boer, natuur en bouw", 26 June 2026 (Tweede Kamer, 2026D33108)](https://www.tweedekamer.nl/kamerstukken/brieven_regering/detail?id=2026Z14788&did=2026D33108)
- [The same Kamerbrief on open.overheid.nl](https://open.overheid.nl/details/bc6acef2-0bb5-4ea6-976d-c7630b45ac89)
- [Rijksoverheid: Kabinet haalt Nederland van het stikstofslot, 26 June 2026](https://www.onslevendlandschap.nl/actueel/nieuws/2026/06/26/kabinet-haalt-nederland-van-het-stikstofslot)
- [PBL (2026), Reflectie op "Weer ruimte voor boer, natuur en bouw", publication 6203](https://www.pbl.nl/publicaties/reflectie-op-weer-ruimte-voor-boer-natuur-en-bouw-maatregelpakket-voor-landbouw-natuur-en-stikstof)
- [Van de Graft Accountants, Nieuwe aanpak stikstofproblematiek, 15 July 2026 (secondary source)](https://www.vga.nl/nieuwe-aanpak-stikstofproblematiek/)
- [Gemeente Nijkerk, zienswijze op ontwerp Omgevingsverordening Provincie Gelderland 2025-2026, 31 March 2026](https://nijkerk.bestuurlijkeinformatie.nl/Document/View/92fbd1f1-7848-4ef8-a22b-767cf84a7c77)
- [Provincie Gelderland: Omgevingsverordening (adoption and entry into force)](https://www.gelderland.nl/themas/omgeving/omgevingsverordening)
- [Omgevingsverordening Gelderland on Regels op de kaart](https://omgevingswet.overheid.nl/regels-op-de-kaart/documenten/_akn_nl_act_pv25_2023_omgevingsverordening_akn_nl_bill_pv25_2026_2026_000561/overzicht)
- [Omgevingsverordening Gelderland, legal text (CVDR705323)](https://lokaleregelgeving.overheid.nl/CVDR705323/10)
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

- Read the adopted text of the Omgevingsverordening for the zone rules now
  taken from news coverage. On 2026-10-06 the published legal text was still
  the version of 14 November 2025; the new one takes effect on 23 October
  2026.
- Confirm whether Nijkerk is a party to the Aanpak Veluwe.
- From the annexes of the Kamerbrief of 26 June 2026 or later documents:
  which zone width the Veluwe gets (500 or 1,000 m), and how the "groter
  gebied" with the 65-69% target is delimited.
- When AERIUS Monitor M27 appears: read the Veluwe share again and update
  `PUBLISHED_EXCEEDANCE` in `nitrogen.html`.
- The answer of the AERIUS helpdesk (asked 2026-10-06). No longer needed
  for `exceeding`, `above_cl`, `surface` and `coverage`, which the Handboek
  Data AERIUS 2026 describes. Still of use for the year of the deposition
  in the open data, which the handbook does not name.
- AERIUS 2026 was published on 6 October 2026. The habitat layer on the
  page and the field test were made around that date and are labelled
  AERIUS 2025. Fetch again, compare, and state the AERIUS version: habitat
  types, KDW values, hexagon flags and the deposition year can all have
  changed.
  - First check, by the author on 6 October 2026 around 19:35 CEST: the
    three hexagon layers were downloaded again (the saved files moved
    aside; the screen showed the downloads: 71,442, 46,826 and 81,522
    features) and the field test gave the same report in every number:
    deposition year 2024, 43,770 relevant hexagons, 43,664 / 59 / 47,
    81,522 link rows. So that evening the open data service returned the
    same hexagon data as before. Either AERIUS 2026 was not yet in the
    service, or it changed nothing in this map area; which of the two is
    not known.
  - Not rechecked: the habitat layer shown on the page
    (`relevant_habitats`), which that script does not download. Its
    record in the Nationaal Georegister, as seen by the author on 6
    October 2026 at 22:16 CEST, describes the layer as the habitat types
    "die ook daadwerkelijk relevant zijn bevonden voor AERIUS 2026". The
    layer on the page was fetched on 5 October 2026, the day before
    AERIUS 2026 was published, and its metadata note still refers to the
    AERIUS 2025 release. So the page may show the previous version of
    this layer. Fetch it again and compare the habitat types, areas and
    KDW values before rebuilding the page data.
  - Done by the author on 6 October 2026 at about 22:18 CEST: a fresh
    download of `relevant_habitats` (41 features) differs from the layer
    of 5 October that the page shows. Compared from the printed output of
    `fetch_aerius_habitats.py`:

    | | On the page (fetched 5 October) | Fresh download (6 October) |
    |---|---|---|
    | Habitat types in the map area | 33 | 31 |
    | Mapped relevant habitat in the map area | 39,436 ha | 39,442 ha |
    | Inside Nijkerk | 0 ha | 0 ha |
    | Nearest to the municipal boundary | 0.7 km | 0.7 km |
    | Lowest and highest KDW | 500 and 2,399 | 500 and 2,399 |

    The two types that are gone are search areas with almost no surface
    (ZGH2320 0.0 ha, ZGH5130 0.3 ha). The KDW of all 31 remaining types is
    unchanged. The mapped area changed for 19 types; the largest changes
    are H2330 (2,045 to 1,842 ha), Lg09 (449 to 621 ha) and `L4030` (2,097
    to 2,130 ha). So the service now returns another version of this
    layer, in line with its catalogue record. Confirmed afterwards by
    comparing the two data files themselves. The page data was rebuilt
    with the fresh download on 6 October 2026; all other layers in the
    page data are unchanged.
  - Open: the hexagon layers were identical at 19:35 that evening. Whether
    they have changed since has not been checked.
  - Check again some days later. The script now writes into its report
    whether each layer was downloaded in that run, and when; `--refresh`
    downloads again.
- For the Veluwe figure: the title and licence of the RIVMdata catalogue
  record of the GeoPackage, and whether a Monitor 2026 version of the file
  exists (reference year 2024).
- From AERIUS Monitor's chart "Ontwikkeling stikstofbelasting" for the
  Veluwe in M26: the tooltips of "bijna overbelast" and "lichte
  overbelasting" for 2024 (now derived by subtraction). Also how the
  Monitor aggregates hexagons on its map.
