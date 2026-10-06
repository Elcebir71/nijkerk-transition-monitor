# Nitrogen removal / recovery technologies for manure — research notes

Status: exploratory desk research (Oct 2026). Not a feasibility study.
Figures come from the cited sources, are mostly non-Dutch, and must not be
read as quotes for Nijkerk. Where a source gave no number, none is invented.

## Why this matters for the project

Nijkerk's core problem is livestock manure N -> ammonia emission -> nitrogen
deposition on Natura 2000 areas. The dashboard models the *source side*
(fewer animals). These notes cover the *treatment side*: technologies that
remove or recover N from manure/digestate. Candidate for a roadmap module.

## Out of scope (checked and set aside)

- **"GoGreen" algae exhaust filter** (two Pennsylvania students, 2023 invention
  convention): CO2 from vehicle exhaust, not manure N. The widely shared
  figures (74.25% CO2 reduction, "16% of global emissions") appear only on
  social media; no independent test data found. Not relevant to this project.
  Source: [ChaddsFordLive](https://chaddsfordlive.com/2023/07/uhs-pair-scrub-emissions/)
- **PGPB / rhizobia nitrogen fixation**: reduces synthetic fertilizer N on the
  crop side; does not address the livestock manure surplus. Complementary at
  best.

## Important limitation: recovered N is not avoided NH3 emission

The technologies below treat N that is already in collected manure or
digestate. They do not undo ammonia emission that has already occurred in
housing or storage. Depending on where they sit in the manure chain, they
can lower emission at a later step, in the sources checked mainly at field
application (see the matrix below).

- Emissieregistratie (see `nitrogen-sources.md`): Nijkerk 2024 NH3 = 352 t,
  93% agriculture, i.e. ~327 t NH3, roughly 270 t N (NH3 is 14/17 N).
- The ~1,295 t N/yr used below is total excreted N. Only about one fifth of
  that figure leaves as agricultural NH3 (rough own calculation).
- Stripping and similar treatment acts after housing and storage, so the
  emission that already occurred in the stable and storage is not undone.
- Which emission pathway each technology touches (housing, storage, field
  application) is worked out in "Which emission pathway does each technology
  touch?" below. The euro-per-tonne-N figures are a nutrient-valorisation
  view, not an emission-reduction cost.
- These notes use CBS-calibrated totals and US reference prices. They belong
  to the prototype side of the repo, not to the Stikstofmonitor, which uses
  no synthetic data and makes no cost estimates.

## Technology comparison

| Technology | Maturity | What it does | Key figures (as reported) |
|---|---|---|---|
| Nitrification-denitrification | Commercial | Converts N to harmless N2 gas (N destroyed) | ~$1,600 / t N (US reference) |
| Anammox-based deammonification | Commercial, growing | Ammonium + nitrite -> N2, anoxic, no organic carbon needed | See reviews below |
| Ammonia stripping + scrubbing (e.g. Colsen AMFER) | TRL 9 | Strips NH3 at ~60 C, recovers ammonium sulphate/nitrate fertilizer | Typical ~50% removal of mineral N, >85% possible; 1-500 t/h; capex/opex not published |
| Gas-permeable membrane (e-PTFE) | Pilot (TRL ~6-7) | NH3 diffuses through membrane into acid, gives ammonium sulphate | 14-49% TAN removal, 43-80% of removed N captured, product 3.2% N; ~EUR 2.07 / kg N recovered (Spanish pilot, 2,800 sows, 7 months) |
| Electrochemical recovery (ion-selective electrode, KNiHCF) | Lab (TRL ~3-4) | Selective NH4+/K+ capture, co-produces H2 or H2O2 | ~100% selectivity in lab; no pilot; electrode durability and cost unknown |
| Bioelectrochemical systems | Mostly reviews/lab | Microbial-electrochemical ammonia removal | Limited field data |

Dutch vendors with relevant services: Colsen (nitrogen removal, N-recovery,
AMFER), Nijhuis Saur Industries (Byosis), Sustec (nutrient recovery).

## Which emission pathway does each technology touch?

The table above counts N removed from manure. Deposition is driven by NH3
that escapes to air, and that happens at several points in the manure chain.
A technology only helps where it sits in that chain.

### Where agricultural NH3 is emitted (Netherlands, 2022)

From PBL (2024), Table 3.1, based on the Emissieregistratie. Shares are
calculated here from the published kilotons.

| Pathway | kt NH3 | Share |
|---|---|---|
| Housing and storage (stal en opslag) | 54.8 | 50% |
| Application of animal manure | 32.7 | 30% |
| Application of synthetic fertilizer | 8.9 | 8% |
| Private parties (hobby animals etc.) | 6.5 | 6% |
| Other | 5.0 | 5% |
| Grazing | 1.3 | 1% |
| Manure treatment and processing | 1.0 | 1% |
| **Total** | **110.2** | |

National figures. The Emissieregistratie export used in this repo is at
sector level, so no such split is available for Nijkerk.

The "one fifth" comparison in the limitation section above is indicative
only: the two numbers come from different sources and years, the emission
figure also contains fertilizer, and emissions are counted where they are
released, not where the animals are.

### Technology matrix: which N flow, which pathway

Two different flows, not to be mixed up:

- NH3 emission -> atmosphere -> deposition (what the Stikstofmonitor shows)
- N in manure/digestate -> stripping or recovery -> recovered N product

How to read the matrix:

- Housing / Storage / Application: does the technology lower NH3 emission on
  that pathway (yes, no, higher, or not reported).
- "NH3 reduction" is relative to that one pathway, not to total emission.
  A 45% cut on application is not a 45% cut overall.
- "As reported" means the figure is copied from the source named in the row.
  Official emission factors and field measurements are marked as such.
  WLR = Wageningen Livestock Research report number.
- The national inventory model NEMA works on the TAN-flow principle (RIVM
  2024-0015): N that is not lost in the barn stays in the manure and moves on
  to storage and application. A barn measure without a step behind it
  therefore shifts part of the emission downstream.

| Technology | Input | N flow it acts on | Housing | Storage | Application | NH3 reduction (as reported) | N recovery |
|---|---|---|---|---|---|---|---|
| Chemical air scrubber | Exhaust air of the barn | NH3 already in the barn air, bound with sulphuric acid | Yes | No | No | 70-95% of housing emission (official factors, IPLO) | Yes, ammonium sulphate in the discharge water |
| Biological / combi air scrubber | Exhaust air of the barn | NH3 in barn air, converted by bacteria to nitrite/nitrate | Yes | No | No | 70-85% official (biological). Combi scrubbers on pig farms measured 41-67% against 85% required (WLR 1337) | Partly, N leaves as nitrite/nitrate in discharge water |
| Faeces/urine separation with air extraction (Lely Sphere) | Dairy barn floor and pit air | NH3 formed under and just above the floor, captured in a filter | Yes | Not reported | Not reported | 77%: 3 against 13 kg NH3 per animal place per year, 4 farms (as reported by NCM) | Yes, liquid fertilizer substitute |
| Daily removal on a closed floor with scraper | Fresh manure | Less time for TAN to volatilise in the barn | Yes | Yes, when the manure goes straight to a digester | No: more TAN arrives at application | Housing -42% (calculated from WLR 1449 Table 3, dairy, model) | No |
| Slurry acidification in the barn | Slurry in the pit, sulphuric acid, pH below 5.5 | TAN kept as ammonium in the slurry | Partly: pit only, floor emission unchanged | Not quantified | Yes | Housing: pigs 64% (VERA 2016), dairy about 30%. Application: 49% (VERA 2012, Denmark); Dutch trials 7-24% (all via WLR 1375) | No, N stays in the manure |
| Low-emission application (injection) | Slurry at spreading | TAN applied to land | No | No | Yes | Emission 2% of TAN (arable injector) against 17% (shallow injection on grassland), as cited by NCM | No |
| Digestion alone (for reference) | Slurry | Organic N turned into TAN; no N removed | No direct effect | Higher: +47% from stored digestate (study cited by NCM) | Higher: +24% (WLR 1449, model) | Negative unless combined with other steps | No |
| Stripping + scrubbing (e.g. Colsen AMFER) | Digestate or its liquid fraction | TAN in digestate -> ammonium sulphate/nitrate | No | Not reported | Yes | Application -45% against raw slurry (WLR 1449, model). Vendor documents give N removal only (typically 50% of mineral N, >85% possible) and make no emission claim | Yes |
| Gas-permeable membrane | Stored raw slurry (pilot) | TAN in slurry -> ammonium sulphate | No | Not measured | Not measured | None reported as emission; 14-49% TAN removal | Yes |
| Nitrification-denitrification | Liquid fraction; in this region veal calf slurry | TAN -> N2 gas | No | No | Less mineral N to apply; not quantified | Not a reduction figure: process emission NH3-N 0.3% and N2O-N 5.0% of total N in the incoming manure (WLR 962 Table 2, veal calf slurry, estimate) | No, N is destroyed |
| Anammox-based deammonification | Ammonium-rich liquid | TAN -> N2 gas | No | No | Less mineral N to apply; not quantified | Not found for manure in the sources checked | No, N is destroyed |
| Electrochemical recovery | Manure wastewater (lab) | NH4+ captured on an electrode | No | Unknown | Unknown | None reported | Yes (lab) |

What the matrix shows:

1. Only the first five rows touch housing, the largest pathway. None of them
   is a treatment technology from the comparison table above.
2. The technologies that recover N (stripping, membrane, electrochemical) act
   on application at most. Their vendor documents report N removal, not
   emission reduction.
3. Technologies that destroy N (nitrification-denitrification, anammox)
   shrink the manure surplus, not the barn emission, and nitrification-
   denitrification has its own N2O emission.
4. Acidification conflicts with the biogas chain: according to WLR 1375,
   central digesters do not accept acidified manure. The same report lists
   sulphur load and damage to concrete as obstacles in the Netherlands.
5. Official scrubber percentages and measured ones differ. Use both, labelled.

### Already operating nearby

Stichting Mestverwerking Gelderland treats veal calf slurry biologically at
four plants on the Veluwe (Putten, Elspeet, Ede, Stroe): 660,000 t per year
from about 450 calf farms, as stated on its website. A 2007 article describes
the process as nitrification followed by denitrification to N2 gas. Whether
and how much Nijkerk veal slurry goes there is not known here. Nijkerk had
8,421 veal calves in 2023 (`data/generation_summary.json`).

### What a full chain looks like (WUR, modelled)

Wageningen Livestock Research report 1449 (2023) modelled one average dairy
farm (103.5 cows) from 26 farms in Wijnjewoude. NH3 in kg per year:

| Scenario | Housing | Grazing | External storage | Processing | Application | Total | Change |
|---|---|---|---|---|---|---|---|
| 0. Current | 1,758 | 37 | 19 | – | 1,395 | 3,209 | – |
| 1a. Daily removal + digestion | 1,016 | 37 | 3 | – | 1,730 | 2,786 | -13% |
| 2a. 1a + stripping | 1,016 | 37 | 3 | 75 | 765 | 1,895 | -41% |
| 2b. 2a + dilution | 1,016 | 37 | 3 | 75 | 615 | 1,746 | -46% |
| 2c. 2a + acidification | 1,016 | 37 | 3 | 75 | 606 | 1,737 | -46% |

What this shows:

1. The housing reduction (-42%) comes from a closed floor with a scraper and
   daily manure removal. It is a barn measure, not a treatment technology,
   and it is more than half of the total reduction in scenario 2a.
2. Digestion without stripping raises application emission by 24%.
3. Stripping brings application emission 45% below raw slurry.

Model results for dairy, not measurements, and not Nijkerk. A WUR desk study
(report WPR-840, 2020) notes that little field research exists on the effect
of digestion on emissions.

### Consequences for this project

- Treatment is not a stand-alone answer to deposition. It needs a barn-side
  step in front of it.
- Barn-side performance in practice is disputed. A CBS study (2019) and a
  Wageningen Livestock Research verification found no difference in N loss
  between dairy barns with and without a low-emission floor, and combi air
  scrubbers measured well below their official percentage (see the matrix).
- The useful link to the biogas work is the chain, not the digester:
  daily removal -> digestion -> stripping.
- The recovered ammonium sulphate is itself applied to land. NCM reports very
  high emission from ammonium sulphate solution on calcareous soil (project
  KNAP, report not yet published). Soil type in and around Nijkerk not
  checked.
- Open question: emissions are counted where manure is applied. How much of
  Nijkerk's manure is applied inside the municipality is not known here.
- National policy follows the same split by pathway. The cabinet package of
  26 June 2026 sets a farm norm for dairy of "0,164 kg NH3 ... uit stallen
  en mestopslag per fosfaatrecht" in 2035: a norm on housing and storage
  emission only. PBL (2026, publication 6203) puts housing and storage at 60
  kt NH3 and field emission at 42 kt in 2019 (p. 24) and notes that field
  emissions "vallen nu niet onder de voorgestelde bedrijfsspecifieke
  emissienormen" (p. 7). So a technology that recovers N from digestate does
  not help a farm meet that norm; the barn-side rows of the matrix do. Keep
  three quantities apart in any scenario: N recovered, NH3 emission avoided,
  and deposition avoided.

## Rough order-of-magnitude for Nijkerk (illustrative only)

Inputs from this repo (`data/generation_summary.json`): synthetic total
~1,100,659 kg N/yr = 85% of the real 2023 CBS-based total, so real total is
roughly 1,295 t N/yr and ~153,000 t manure/yr (~17.5 t/h averaged).

- Capacity fits inside a single AMFER-class installation (1-500 t/h).
- At 50% removal: ~647 t N/yr; at 85%: ~1,100 t N/yr.
- Value at US reference prices ($1,200-1,700 / t N): roughly $0.8-1.9 M/yr.

Caveats (important):
1. Capex/opex for AMFER is not public; vendor quote required.
2. Reference prices are US digestate economics, not Dutch energy/fertilizer
   markets or subsidy regimes.
3. Not all excreted N becomes processable slurry (grazing, storage losses),
   so ~1,295 t N/yr is an upper bound, not the treatable amount. If the
   figure is ever shown in the prototype, word it as: "De geschatte totale
   N-excretie bedraagt circa 1.295 ton N per jaar; dit is geen schatting van
   de behandelbare hoeveelheid."
4. The membrane figure (EUR 2.07 / kg N = ~EUR 2,070 / t N) is a pilot-scale
   net cost and is not directly comparable to the US reference numbers.

## Suggested next steps

- Request capex/opex and a reference case from Colsen (contact listed on its
  N-recovery page).
- Estimate the truly treatable N fraction from housing/storage data.
- Decide whether a "treatment scenario" belongs in the dashboard roadmap.
  If so, it should model the chain per pathway, not kg N removed.
- Find a pathway split (housing / application) for pigs, veal calves and
  poultry; report 1449 covers dairy only.
- Check soil type (calcareous or not) for land where recovered ammonium
  sulphate would be applied.
- Still to verify for the matrix:
  - application emission factors per technique from the primary source
    (RIVM 2024-0015, chapter on agricultural soils; only the first chapters
    could be read, the 2% and 17% come from NCM);
  - the official emission factor and legal status of the Lely Sphere from
    the regulation itself, not from a news item;
  - current capacity and N removal of the SMG plants, and whether Nijkerk
    farms deliver there;
  - how many Nijkerk barns already have an air scrubber (not in any dataset
    used in this repo).

## Sources

- [Colsen: Nitrogen removal](https://www.colsen.nl/en/services/nitrogen-removal)
- [Colsen: N-recovery](https://www.colsen.nl/en/services/n-recovery)
- [Colsen AMFER, Newtrient catalog](https://www.newtrient.com/catalog/colsen-amfer-ammonia-stripping/)
- [AMFER, Nutriman farmer platform](https://nutriman.net/farmer-platform/technology/id_455)
- [Nijhuis Saur Industries: Byosis](https://www.nijhuissaurindustries.com/byosis/)
- [Sustec nutrient recovery, Newtrient](https://www.newtrient.com/catalog/sustec-nutrient-recovery/)
- [Economical Recovery of Ammonia from Anaerobic Digestate, LPELC](https://lpelc.org/economical-recovery-of-ammonia-from-anaerobic-digestate/)
- [Treatment technologies for ammonia in liquid manure, LPELC](https://lpelc.org/treatment-technologies-for-ammonia-in-liquid-manure-nitrification-denitrification-and-anammox-based-deammonification/)
- [Stripping/scrubbing before nitrification-denitrification saves costs, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1385894723057157)
- [Pilot-scale membrane-based N recovery from swine manure, MDPI Membranes](https://www.mdpi.com/2077-0375/10/10/270)
- [Electrochemical ammonia recovery from manure wastewater, Nature Sustainability](https://www.nature.com/articles/s41893-023-01252-z)
- [Technologies to recover nitrogen from livestock manure, review](https://www.researchgate.net/publication/350881141_Technologies_to_Recover_Nitrogen_from_Livestock_Manure_-_A_Review)

Emission pathways (checked 2026-10-06):

- [PBL (2024), Toelichting op de geraamde ontwikkeling van de ammoniakemissie uit de landbouw tot 2030/2035, publication 5671, Table 3.1](https://www.pbl.nl/system/files/document/2024-12/pbl-2024-toelichting-geraamde-ontwikkeling-ammoniakemissie-landbouw-5671_0.pdf)
- [Wageningen Livestock Research (2023), report 1449: Berekeningen over emissies, massabalansen en economie bij gezamenlijke monomestvergisting, scenariostudie Wijnjewoude, Table 3](https://edepot.wur.nl/640987)
- [WUR (2020), report WPR-840: Mestvergisting als onderdeel van duurzame kringlopen](https://edepot.wur.nl/524221)
- [NCM (2026), Hoe zit het met monomestvergisting en stikstof?](https://www.mestverwaarding.nl/kenniscentrum/5627/hoe-zit-het-met-monomestvergisting-en-stikstof)
- [NCM (2023), Ammoniakemissie bij emissiearme stallen wordt onderschat (on the CBS 2019 study and the WLR verification)](https://www.mestverwaarding.nl/kenniscentrum/3588/ammoniakemissie-bij-emissiearme-stallen-wordt-onderschat)

National policy (checked 2026-10-06):

- [Kamerbrief "Weer ruimte voor boer, natuur en bouw", 26 June 2026 (Tweede Kamer, 2026D33108)](https://www.tweedekamer.nl/kamerstukken/brieven_regering/detail?id=2026Z14788&did=2026D33108)
- [PBL (2026), Reflectie op "Weer ruimte voor boer, natuur en bouw", publication 6203](https://www.pbl.nl/publicaties/reflectie-op-weer-ruimte-voor-boer-natuur-en-bouw-maatregelpakket-voor-landbouw-natuur-en-stikstof)

Technology matrix (checked 2026-10-06):

- [RIVM (2024), Methodology for the calculation of emissions from agriculture (NEMA), report 2024-0015](https://www.rivm.nl/bibliotheek/rapporten/2024-0015.pdf)
- [IPLO: Chemische wasser](https://iplo.nl/thema/toepassing-regels-praktijk/veehouderijen/stalsystemen-aanvullende-technieken/luchtwassers/typen-luchtwassers/chemische-wasser/)
- [IPLO: Biologische wasser](https://iplo.nl/thema/toepassing-regels-praktijk/veehouderijen/stalsystemen-aanvullende-technieken/luchtwassers/typen-luchtwassers/biologische-wasser/)
- [Wageningen Livestock Research (2021), report 1337: Onderzoek naar verbeterpunten voor combi-luchtwassers in de praktijk](https://edepot.wur.nl/554345)
- [Wageningen Livestock Research (2022), report 1375: Perspectief van het aanzuren van mest in Nederland om methaan- en ammoniakemissie te reduceren](https://edepot.wur.nl/572080)
- [Wageningen Livestock Research (2016), report 962: Emissiefactoren mestbewerking](https://edepot.wur.nl/386801)
- [NCM (2023), Lely Sphere heeft definitieve emissiefactor voor ammoniak](https://www.mestverwaarding.nl/kenniscentrum/3343/lely-sphere-heeft-definitieve-emissiefactor-voor-ammoniak)
- [Stichting Mestverwerking Gelderland](https://www.smg.nl/)
- [Mestverwerking Gelderland maakt van kalvergier bruikbare eindproducten, Nutswerk 2007](https://edepot.wur.nl/674370)
- Vendor documents for AMFER: the Colsen, Newtrient and Nutriman pages listed above.
