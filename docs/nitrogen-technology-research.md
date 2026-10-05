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
digestate. They do not by themselves reduce ammonia emission or deposition.

- Emissieregistratie (see `nitrogen-sources.md`): Nijkerk 2024 NH3 = 352 t,
  93% agriculture, i.e. ~327 t NH3, roughly 270 t N (NH3 is 14/17 N).
- The ~1,295 t N/yr used below is total excreted N. Only about one fifth of
  that figure leaves as agricultural NH3 (rough own calculation).
- Stripping and similar treatment acts after housing and storage, so the
  emission that already occurred in the stable and storage is not undone.
- Still missing: a per-technology breakdown of which emission pathway it
  touches (housing, storage, field application), with WUR/RIVM sources.
  Until then, the euro-per-tonne-N figures below are a nutrient-valorisation
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
   so ~1,295 t N/yr is an upper bound, not the treatable amount.
4. The membrane figure (EUR 2.07 / kg N = ~EUR 2,070 / t N) is a pilot-scale
   net cost and is not directly comparable to the US reference numbers.

## Suggested next steps

- Request capex/opex and a reference case from Colsen (contact listed on its
  N-recovery page).
- Estimate the truly treatable N fraction from housing/storage data.
- Decide whether a "treatment scenario" belongs in the dashboard roadmap.

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
