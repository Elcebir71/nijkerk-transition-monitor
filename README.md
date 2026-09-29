# Nijkerk Agricultural Transition Monitor

Interactive prototype for gemeente Nijkerk: a manure/nitrogen/biogas-potential
dashboard with a scenario engine, built on a **fully synthetic** demo dataset
of 75 fictional farms.

**Live dashboard:** open [`index.html`](index.html) in a browser, or enable
GitHub Pages for this repo (Settings → Pages → Source: `main` / root) to get
a shareable link.

<p>
  <img src="docs/screenshot-kaart.png" alt="Map view: farm locations, scenario slider and KPI tiles" width="49%">
  <img src="docs/screenshot-tabel.png" alt="Table view: searchable/filterable farm list with detail panel" width="49%">
</p>

## What this is

Grew out of an earlier feasibility analysis for a Nijkerk "Biogas Hub"
(manure-to-biogas co-digestion facility). That analysis showed the hub's
business case is fragile once SDE++ subsidy support is factored in and
feedstock volumes decline — so instead of pushing a shaky infrastructure
proposal, this repo builds something in the author's own skillset (data /
GIS / cloud engineering): a reusable **monitoring and scenario-planning
tool** for the municipality's agricultural transition, of which the biogas
question is just one input.

## What it does

- Map + searchable table of 75 synthetic farms (7 archetypes: melkvee,
  vleeskalveren, varkens, pluimvee, geiten/schapen, paarden, gemengd)
- A **species-level scenario engine**: drag a reduction slider per animal
  sector (melkvee / varkens / pluimvee / overig) and watch N-excretion,
  manure volume and estimated biogas potential recompute live, per animal
  category — not a flat per-farm percentage
- Data-quality labeling per animal category (official RVO norm vs.
  literature approximation), not a single blanket label per farm
- Ammonia-inhibition flag for poultry-heavy manure mixes

## Data & methodology — read before using this for anything real

**Every farm, location and animal count in this dataset is entirely
fictional.** Nothing here describes a real business, address or parcel.

- **Totals are calibrated, not the individual rows.** Per animal category,
  the *sum* across all 75 synthetic farms is set to ~85% of the real 2023
  CBS Landbouwtelling total for gemeente Nijkerk (`data/generation_summary.json`
  has the exact real-vs-synthetic comparison per category). No individual
  farm's numbers are real.
- **Locations are fully random**, generated inside a schematic (non-cadastral)
  Nijkerk outline, excluding the built-up town centre and enforcing a minimum
  150m spacing between farms. An earlier version anchored points to real BRP
  agricultural-parcel centroids + jitter; that was deliberately replaced
  after review because it was judged not privacy-safe enough for a municipal
  presentation. See `scripts/generate.py` for the current method.
- **N-excretion / manure coefficients** are per-animal-category norms, mostly
  from RVO.nl "Tabel 4 Diergebonden normen 2024" and "Tabel 6 Stikstof en
  fosfaat per melkkoe 2024"; a few categories (marked `LITERATURE_APPROX` in
  the data) are literature-typical estimates, not taken from an RVO table
  fetched for this project. See `scripts/constants.py`.
- **Biogas yield and manure density** per manure type are illustrative
  literature ranges, not independently verified for this project.
- **"Afstand ref.punt"** is the distance to a self-chosen, indicative point
  near Arkemheen — **not** the official Natura 2000 boundary polygon.

This is a demonstration prototype, not a policy instrument, and not a
replacement for the underlying emission-reduction report.

## Repo layout

```
index.html            the dashboard (self-contained HTML/CSS/JS)
data/
  nijkerk_synthetic_farms_2023.csv   full 75-row dataset
  farms_data.json                    compact JSON embedded in index.html
  generation_summary.json            real vs. synthetic totals per category
scripts/
  constants.py           SINGLE SOURCE OF TRUTH for all coefficients
                          (N-excretion, manure, biogas yield, density,
                          scenario sectors, data-quality tiers)
  generate.py             builds data/*.csv + generation_summary.json
  build_compact_json.py   builds data/farms_data.json from the CSV
  sync_js_constants.py    regenerates index.html's embedded JS constants
                          from constants.py (keeps dashboard in sync with
                          the Python generator — never hand-edit those
                          JS blocks in index.html)
  build_doc_xlsx.py       builds docs/*.xlsx methodology documentation
docs/
  Nijkerk_Synthetische_Demodata_Documentatie.xlsx   full methodology + data-quality tables
```

### Regenerating the data

If a coefficient in `scripts/constants.py` changes, run in order from
`scripts/`:

```bash
python3 generate.py            # rebuilds data/*.csv + generation_summary.json
python3 build_compact_json.py  # rebuilds data/farms_data.json
python3 sync_js_constants.py   # re-syncs index.html's embedded JS
python3 build_doc_xlsx.py      # rebuilds the documentation workbook
```

## Roadmap / possible next phases

1. Replace synthetic data with real (anonymized, validated) farm-level data,
   with the municipality's or RVO's cooperation.
2. Real Natura 2000 boundary polygons (PDOK WFS/OGC) instead of the
   indicative reference point, for actual distance-to-boundary analysis.
3. An NH₃ emission-factor module (RVO stal-type emission factors) for a real
   air-quality layer, beyond the current qualitative ammonia-inhibition flag.

With those three, this stops being a demo and becomes a genuine
municipal policy-support tool.
