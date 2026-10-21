# BM-11450069-CODE
This project analyzes UK household electricity use (2020–2023) with SERL smart-meter data. Methods include SARIMA/SARIMAX forecasting, UMAP–HDBSCAN clustering, and tariff simulation. Results show falling demand but stable evening peaks, highlighting inequities and supporting equity-focused demand-response design.
---

## Table of contents

* [Overview](#overview)
* [Repository layout](#repository-layout)
* [Data access (SERL Study 8963)](#data-access-serl-study-8963)
* [Environment & setup](#environment--setup)
* [Reproducibility & run order](#reproducibility--run-order)
* [Key outputs](#key-outputs)
* [Tariff simulation notes](#tariff-simulation-notes)
* [Results at a glance](#results-at-a-glance)
* [Citations](#citations)
* [Licensing](#licensing)
* [Contributing](#contributing)

---

## Overview

This repository accompanies the MSc dissertation **“Towards Equitable Energy: Temporal Load Modelling for Inclusive Demand-Response.”** It studies how temporal structure (e.g., the evening peak) persists despite falling average consumption, and how subgroup differences (heating type, PV, efficiency, region, deprivation) shape forecasting accuracy and tariff exposure. Methods emphasise interpretability and policy relevance.

**Core modules**

* **EDA:** seasonal/diurnal structure, subgroup contrasts, distributional diagnostics.
* **Forecasting:** SARIMA/SARIMAX baselines with weather covariates; expanding-window backtests.
* **Clustering:** feature engineering of load-shape vectors; UMAP embedding; HDBSCAN density clustering.
* **Tariff simulation:** half-hourly cost exposure under dynamic vs flat tariffs; equity-oriented comparisons.

---

## Repository layout

Notebooks sit at the repository root and use paths relative to it, so run them from here.

```
.
├─ EDA - UnivariateYearly.ipynb
├─ EDA - BiandMultivariate.ipynb
├─ EDA - NumericAnalysis.ipynb
├─ TemporalForecasting.ipynb
├─ DemandModelling 1.ipynb
├─ DemandModelling 2.ipynb
├─ TariffSimulation.ipynb
├─ Bibliometric_Analyis.ipynb      # original filename preserved
├─ data/                           # inputs, not committed (see data/README.md)
├─ outputs/                        # everything the notebooks write, not committed
│  ├─ figures/
│  └─ artifacts/                   # API caches (geocoding, Google Trends)
└─ README.md
```

> **Note:** Raw SERL data are **not** included (see licensing). Place them in `data/` using the file names listed in [`data/README.md`](data/README.md).

---

## Data access (SERL Study 8963)

Analyses use the **Smart Energy Research Lab (SERL) Study 8963, 2020–2023** aggregated statistics (daily and half-hourly). Access is via the UK Data Service under safeguarded/End User Licence terms.

* Obtain credentials, accept the licence, and download the daily and half-hourly aggregated files for 2020–2023.
* Save them in `data/` with the file names listed in [`data/README.md`](data/README.md); no path edits are needed in the notebooks.
* Respect disclosure controls; publish only allowed aggregates.

---

## Environment & setup

Tested with **Python ≥ 3.10** (3.11 recommended).

```bash
# 1) Create environment
python -m venv .venv
# or: conda create -n equitable-energy python=3.11

# 2) Activate
source .venv/bin/activate            # macOS/Linux
#    or: .venv\Scripts\activate      # Windows

# 3) Install core libraries
pip install -U pip wheel
pip install pandas numpy scipy statsmodels scikit-learn umap-learn hdbscan \
            matplotlib plotly jupyter ipywidgets pydantic requests

# Optional (for tidy plots and exporting)
pip install kaleido openpyxl
```

*Jupyter extensions:* The notebooks use `ipywidgets`; if widgets don’t render, run:

```bash
jupyter nbextension enable --py widgetsnbextension
```

---

## Reproducibility & run order

For a clean end-to-end replication, execute notebooks **in the following sequence**:

1. **EDA - UnivariateYearly.ipynb** – yearly/seasonal/diurnal structure; basic metrics.
2. **EDA - BiandMultivariate.ipynb** – subgroup contrasts (EPC, IMD, heating, PV, region).
3. **EDA - NumericAnalysis.ipynb** – distributional diagnostics; load factor, skew/kurtosis.
4. **TemporalForecasting.ipynb** – SARIMA/SARIMAX (with meteorology); expanding-window backtests; export `sarima_forecasts.csv` and `forecast_12mo_per_subgroup.csv`.
5. **DemandModelling.ipynb** – feature engineering; UMAP→HDBSCAN; export `clustering_results.csv` and `subgroup_ratios_and_clusters.csv`.
6. **TariffSimulation.ipynb** – merge half-hourly demand with tariff schedules; compute exposure vs flat tariffs; export scenario tables.
7. **Bibliometric\_Analyis.ipynb** – literature scan and figures supporting the methodological framing.

**Selecting data with `serl_utils.py`.** Each SERL file stacks overlapping household groups (whole sample, heating fuel, PV, region, EPC, tenure, …), each in three units. Averaging across rows without picking one group and one unit mixes them. Use the helper, which raises an error if a filter is missing:

```python
from serl_utils import load_monthly, monthly_series, monthly_panel, load_half_hourly, daily_profile

df = load_monthly()
gas = monthly_series(df, "Gas", "kWh/day")                                   # whole sample, 48 months
regions = monthly_panel(df, "Electricity net", "kWh/day", "region")          # 48 months x 11 regions
pv = monthly_series(df, "Electricity imports", "kWh/day", pv="Yes")          # PV households only
profile = daily_profile(load_half_hourly(), 2023, "Electricity imports", "Wh", to_kwh=True)  # 48 half-hours
```

Run `python -m pytest` to check the helper; the tests that need SERL data are skipped if `data/` is empty.

**Seeds & determinism.** Where applicable, notebooks set random seeds for embeddings/clusterers; GPU is **not required**. Some algorithms (UMAP/HDBSCAN) can exhibit minor non-determinism; fix `random_state` to stabilise runs.

---

## Key outputs

* `sarima_forecasts.csv` — regional/monthly forecasts with prediction intervals.
* `subgroup_forecasts.csv` & `forecast_12mo_per_subgroup.csv` — subgroup-level forecast panels.
* `clustering_results.csv` & `subgroup_ratios_and_clusters.csv` — UMAP/HDBSCAN cluster labels and prevalence by subgroup.
* `data/Clean_Aggregated_data_2020_2023.csv` — cleaned daily aggregated statistics used as the modelling input (previously named `forcasting.csv`).

These CSVs are written to `outputs/` by the forecasting, clustering, and tariff notebooks and feed the figures/tables in the dissertation.

---

## Tariff simulation notes

* The tariff notebook aligns half-hourly demand with time-varying unit rates (e.g., Agile-type products).
* Public endpoints often suffice, but if an API key/region code is required, set environment variables (e.g., `OCTOPUS_REGION`, `OCTOPUS_API_KEY`) and follow the notebook’s prompts.
* Outputs compare **dynamic vs flat** exposure by persona/cluster and flag potential regressive effects.

---

## Results at a glance

* Mean annual consumption declines over 2020–2023, but the **evening peak persists** across years, seasons, and subgroups.
* SARIMAX with meteorology improves error relative to seasonal-naïve baselines in most regions (policy-grade, interpretable gains).
* UMAP→HDBSCAN reveals **behavioural regimes** (e.g., gas-heavy winters, PV-driven midday troughs).
* Dynamic tariffs can advantage flexible/PV personas but risk **regressive exposure** for inflexible, high-load winter regimes—supporting **segmented, equity-by-design** policies.

---

## Citations

If you use this repository, please cite:

* **Dissertation:** *Towards Equitable Energy: Temporal Load Modelling for Inclusive Demand-Response* (University of Manchester, 2025).
* **Data:** Smart Energy Research Lab (SERL), Study 8963 — Aggregated daily and half-hourly statistics, Great Britain, 2020–2023 (UK Data Service).
* Method references and an extended bibliography are summarised in `Bibliometric_Analyis.ipynb` and the dissertation’s reference list.

---

## Licensing

This repository mixes **code**, **text/figures**, and **third-party data**. To keep boundaries clear:

* **Code** (notebooks and scripts): recommend **MIT License**.
* **Text & figures** (dissertation excerpts, plots exported from notebooks): recommend **CC BY 4.0**.
* **Data:** SERL Study 8963 **is not redistributed** here and remains under the UK Data Service End User Licence (and any study-specific conditions). Users must obtain data directly and comply with those terms.

> Include `LICENSE` (MIT) and `LICENSE-docs` (CC BY 4.0). Add a `DATA_LICENSE.md` explaining that SERL data are excluded and how to request access.

---

## Contributing

Issues and pull requests that improve clarity, tests, or reproducibility are welcome. For substantial changes, open an issue first to discuss scope. Please avoid sharing any restricted data or disclosive statistics.

---
