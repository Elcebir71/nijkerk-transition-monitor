# Stikstofmonitor Nijkerk: method in short

As of 9 October 2026. This note says in two pages what `nitrogen.html`
shows, where each figure comes from, what is calculated here and what is
not. The evidence for every statement, with quotes and page numbers, is in
[`nitrogen-sources.md`](nitrogen-sources.md); the section names are given
in brackets.

## What the page is

A page that brings published government figures about livestock, nitrogen
emissions, nitrogen deposition and nature in and around Nijkerk together,
with source, reference date and limits. It is not a publication of the
municipality or of the source holders.

It does not model deposition, does not convert emission into deposition,
does not link animal numbers to deposition, does not show single farms,
does not compare deposition with the KDW itself and gives no costs.

## Sources

| On the page | Source | Period | How obtained |
|---|---|---|---|
| Livestock and farms | CBS, Landbouwtelling, StatLine `80781ned`; Nijkerk and Gelderland | 2000-2025, reference date 1 April | `fetch_cbs_livestock.py` |
| NH3 and NOx emissions per sector | Emissieregistratie, "ER Reeks 1990-2024 Definitief", per municipality | 1990-2024 | Export made by hand, then `load_emissions.py` |
| Deposition map | RIVM, GDN maps, 1 x 1 km: total N, NHx, NOy | 2025 | `fetch_rivm_deposition.py` |
| Natura 2000 boundaries | RVO, through PDOK (CC0) | Current | `fetch_natura2000.py` |
| Municipal boundary | Kadaster, through PDOK | Current | `fetch_natura2000.py` |
| Relevant nitrogen-sensitive habitat types and their KDW | RIVM, AERIUS open data, layer `relevant_habitats` | As served on the fetch date | `fetch_aerius_habitats.py` |
| Share of the Veluwe not above the KDW | RIVM, AERIUS Monitor, edition M26 | 2024 | Read from the screen by hand; a constant in the page |

The fetches behind the page are of 5 October 2026, except the habitat
layer, which is of 6 October 2026; the Monitor figure was read on 6 October
2026. The page shows these dates in its sources table.

## What is calculated here

Only simple values derived from published ones:

- **Municipal mean deposition.** The area-weighted mean of the GDN cells
  that overlap the municipality; the weight of a cell is the part of it
  inside the boundary (104 cells). RIVM does not publish this mean. Lowest
  and highest cell: only cells that lie at least half inside.
- **Share of NHx and NOy** in that mean.
- **Kilograms.** 1 mol N = 14.007 g, so mol N/ha times 0.014007 gives
  kg N/ha.
- **Areas and distances.** Natura 2000 area and mapped habitat inside the
  municipality and inside the map area, and the distance from the municipal
  boundary to the nearest of each. The map area is the bounding box of the
  municipality plus 15 km.
- **Livestock.** An index (first year = 100) and the share of Nijkerk in
  Gelderland.
- **Emissions.** Shares per sector and changes between years.

Everything else is shown as published.

## Terms

- **Emission and deposition.** Emission is what is released here, in
  tonnes of the substance. Deposition is what lands here, in mol nitrogen
  per hectare per year. Part of what lands in Nijkerk comes from elsewhere,
  and part of what is released in Nijkerk lands elsewhere.
- **NHx and NOy.** Reduced nitrogen, from ammonia (NH3), and oxidised
  nitrogen, from nitrogen oxides (NOx).
- **KDW** (kritische depositiewaarde). The level above which there is a
  risk that the quality of a habitat is significantly affected by nitrogen
  deposition. Values are taken from AERIUS. They were revised in 2023, so
  shares "below the KDW" from before that revision cannot be set next to
  current ones [Showing exceedance].
- **Nitrogen-sensitive.** A KDW below 2,400 mol N/ha/year [AERIUS
  definitions, point 2].
- **Relevant habitat types.** The nitrogen-sensitive types that count at a
  location under the policy criteria of AERIUS. The selection is AERIUS's
  [AERIUS definitions, point 1].
- **Drawn and mapped surface.** AERIUS calls the polygons in which a
  habitat type occurs the "ingetekende oppervlakte" (drawn surface), and
  that surface times the coverage the "gekarteerde oppervlakte" (the area
  the type really occupies). The hectares of habitat on the page are drawn
  surface [AERIUS definitions, point 6].
- **Codes.** H: habitat type. ZGH: search area for a habitat type. Lg:
  nitrogen-sensitive habitat (leefgebied) of protected species. `L4030`: a
  leefgebied too, described by the province as "Lgt 4030, weinig vergraste
  heide en stuifzandheide" [AERIUS definitions, point 3].
- **Not above the KDW.** In AERIUS Monitor: the classes "geen
  overbelasting" and "bijna overbelast" together. The Monitor does not
  label the percentage it prints; this was read from its chart and from
  the values of the segments [A published figure for the Veluwe].

## Three deposition products that must not be mixed

| Product | Resolution | Year | Use here |
|---|---|---|---|
| RIVM GDN map | 1 x 1 km | 2025 | The map and the municipal mean on the page |
| AERIUS Monitor maps | 16 ha hexagons | 2024 in edition M26 | Source of the one Veluwe figure on the page |
| AERIUS open data, "actuele depositie" | 1 ha hexagons | 2024 | Not on the page; used once to test what the hexagon fields mean |

The page does not lay the KDW next to the GDN map. The comparison is made
by AERIUS Monitor, on its own maps. The municipal mean is deposition on the
territory of Nijkerk, not on the habitats of the Veluwe.

## Limits to keep in mind

- **Deposition is calculated, not measured per cell.** RIVM gives an
  uncertainty of 30-35% per cell; differences between neighbouring cells
  are often not meaningful [source 3].
- **"2025" is a mix of years.** Meteorology and measurements of 2025,
  national emission totals of 2024, spatial distribution of sources of 2023
  [source 3].
- **Emissions per municipality are an allocation, not a measurement.** The
  Emissieregistratie spreads emissions over the country with allocation
  keys [source 2].
- **Livestock is counted at the farm's main address.** CBS assigns a farm
  to the municipality of its main address; the animals can stand
  elsewhere. The series has method breaks in 2016, 2017 and 2018
  [source 1].
- **Every edition recalculates earlier years.** This holds for the
  Emissieregistratie, the RIVM monitor and AERIUS Monitor. A figure is
  quoted with its edition.
- **The Veluwe figure is about the whole Natura 2000 area**, not about
  Nijkerk: inside the municipality AERIUS maps no relevant
  nitrogen-sensitive habitat. The figure is copied by hand and has to be
  updated by hand.
- **The habitat layer carries no version of its own.** The service does
  not state one; the layer is shown as served on 6 October 2026, the day
  its catalogue record started to describe AERIUS 2026. It differs a
  little from the layer of the day before [Still needed].

## Checked, but not on the page

Kept in the register only: the meaning of the hexagon fields `exceeding`
("naderend overbelast", from 70 mol below the KDW), `above_cl`
("overbelast"), `critical_deposition` (the lowest KDW in the hexagon),
`surface` and `coverage` [AERIUS definitions, points 4 to 6]; an
aggregation for the Veluwe made here from an RIVM file, as a cross-check
[Showing exceedance]; and the position of Nijkerk relative to the
provincial nitrogen strips [Provincial policy context].

## Updating

1. Run the fetch scripts in the order given in the register [The page],
   then `build_page_data.py`.
2. The Emissieregistratie export is made by hand first.
3. Read the Veluwe figure again when a new AERIUS Monitor edition appears
   and change the constant in the page.
4. Compare with the previous figures before publishing, and name the
   edition and fetch date of every source.

Whether a source has changed is checked once a month by a scheduled job
that opens a GitHub issue; it changes nothing by itself. See
[`source-check.md`](source-check.md).
