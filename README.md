# BM-11450069-CODE
This project analyses GB household electricity and gas use (2020–2023) with SERL smart-meter data. Methods include ETS/SARIMA(X) forecasting with rolling-origin evaluation, clustering of household-group seasonal profiles, Bayesian weather regression, and tariff simulation with published Octopus Agile prices. Demand fell by about a fifth while the 18:30 evening peak persisted; dynamic pricing lowered 2023 bills for every household group, slightly less so for the most deprived.
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

* **EDA:** yearly, seasonal and daily structure; spread between households; differences by dwelling, household, PV, heating fuel and deprivation; temperature response.
* **Forecasting:** seasonal naive, ETS, SARIMA and SARIMAX with heating degree days for 11 regions; rolling-origin backtest (5 folds × 12 months); 2024 forecasts.
* **Household groups:** seasonal-shape clusters (k-means) for electricity and gas; personas from seven interpretable features.
* **Modelling:** Bayesian (PyMC) regression of gas use on heating degree days and solar; time-split ML models for monthly electricity.
* **Tariff simulation:** Agile vs flat bills from published 2023 prices, load shifting, and comparisons by household group and region.

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
├─ EnergyPovertyTariffs.ipynb
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
pip install pandas numpy scipy statsmodels scikit-learn matplotlib seaborn \
            pymc arviz requests jupyter pytest

# Optional: Bibliometric_Analyis.ipynb (zero-shot model, ~1.6 GB download on first run)
pip install transformers torch
# Optional: the Google Trends client in the TemporalForecasting appendix
pip install pytrends
```

---

## Reproducibility & run order

For a clean end-to-end replication, execute notebooks **in the following sequence**:

Each notebook reads the data itself, so they can be run in any order. A natural sequence:

1. **EDA - UnivariateYearly.ipynb** – yearly levels, daily profiles, spread between households, seasonality, differences by dwelling and household.
2. **EDA - BiandMultivariate.ipynb** – electricity vs gas, PV, heating fuel, weekday/weekend, temperature and solar.
3. **EDA - NumericAnalysis.ipynb** – derived statistics per half-hour (CV, skewness, confidence intervals).
4. **TemporalForecasting.ipynb** – regional forecasting and rolling-origin evaluation; 2024 forecasts.
5. **DemandModelling 1.ipynb** – seasonal patterns and clusters of household groups.
6. **DemandModelling 2.ipynb** – household-group personas.
7. **TariffSimulation.ipynb** – Bayesian gas–weather model, time-split ML, and the tariff comparison.
8. **EnergyPovertyTariffs.ipynb** – HDBSCAN groupings of household types, energy-poverty signals, SARIMA 2024 forecasts, and 2024 Agile vs flat bills with flexibility- and access-gap scenarios.
9. **Bibliometric\_Analyis.ipynb** – literature descriptives and validated zero-shot topic labels.

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

**Seeds & determinism.** k-means, random forests, gradient boosting, ETS simulations and PyMC sampling use fixed seeds (`random_state=42` / `random_seed=42`). GPU is **not required**.

---

## Key outputs

All written to `outputs/` (not committed; re-created by running the notebooks):

* `forecast_evaluation.csv`, `forecasts_2024_by_region.csv` — backtest metrics per region/fold/model; 2024 forecasts with 80/95% intervals (TemporalForecasting).
* `subgroup_seasonality.csv`, `subgroup_clusters.csv` — seasonal measures and clusters per household group (DemandModelling 1).
* `household_group_features.csv`, `household_group_personas.csv` — persona features and assignments (DemandModelling 2).
* `gas_weather_bayes_summary.csv`, `ml_2023_test_results.csv`, `tariff_*.csv` — Bayesian summary, 2023 test metrics, tariff tables (TariffSimulation).
* `energy_poverty/` — HDBSCAN cells and groups, composition check, signals, asset access, SARIMA 2024 forecasts, 2024 bills and scenarios (EnergyPovertyTariffs).
* `repro/covariate_gradients_2023.csv`, `repro/temperature_response_2023.csv` — EDA tables; `out_semantic/` — bibliometric labels and validation.

The modelling input `data/Clean_Aggregated_data_2020_2023.csv` is the cleaned daily statistics file (previously named `forcasting.csv`).

---

## Tariff simulation notes

* The last section of `TariffSimulation.ipynb` prices SERL 2023 half-hourly profiles (scaled to monthly consumption) under **Octopus Agile** (half-hourly prices) and **Flexible Octopus** (flat, follows the price cap), using published 2023 rates for one GSP region (`REGION`, default `"C"`).
* It reports quarterly bills, a load-shifting scenario (moving 10–30% of 16:00–19:00 use to each day's cheapest half-hours) a comparison by PV status, heating fuel and IMD quintile, and a region-by-region comparison using each region's own prices. Tables are saved to `outputs/tariff_*.csv`.
* Prices come from the public Octopus API (no key needed) via `tariff_utils.py` and are cached in `outputs/artifacts/`. If a download fails with no cache, the code stops with an error; it never substitutes prices.
* July–December 2023 is the cleanest comparison: published flat rates for January–June 2023 do not consistently reflect the Energy Price Guarantee discount.

---

## Results at a glance

* **Demand fell by about a fifth, mostly in 2022:** electricity imports 10.9 → 8.5 kWh/day and gas 36.9 → 29.1 kWh/day per household (2020 → 2023), while the electricity peak stayed at **18:30** every year.
* **Forecasting:** on consistent regional series, ETS is most accurate (MASE 0.49, MAPE 7.8%); all models beat seasonal naive (Wilcoxon p ≤ 0.02 across 11 regions). Heating degree days do not improve forecasts when future weather must be estimated (p = 0.41).
* **Who is different:** electric-heated and PV homes form a distinct, strongly seasonal electricity cluster (winter ≈ 2.8× summer vs 1.5× for others). Electric-heated homes use 26.7 kWh/day of electricity on −5 to 0 °C days vs 7.0 on warm days. Gas seasonality is near-universal: +5.2 kWh/day per heating degree-day (Bayesian, R² 0.92).
* **Tariffs (Jul–Dec 2023):** Agile was 32% cheaper than the flat tariff for the average household in London (20–32% across regions). Every group benefited, but the most deprived quintile gained least (31.0% vs 32.0%) and has the highest share of use at 16:00–19:00. Moving 20% of that use to cheap hours saved about £11 more per half-year.
* **Crisis test (Apr–Dec 2022):** priced with the Agile product available at the height of the crisis, every group would have paid about **23–24% more** than on the flat tariff (August 2022 bills roughly doubled), and load shifting barely helped. Dynamic tariffs pass wholesale-price risk to households: timing differences between deprived and other households change bills by about one percentage point, whereas standing charges, access barriers and price spikes matter far more (`EnergyPovertyTariffs.ipynb`).

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
