# Towards Equitable Energy: temporal load modelling for inclusive demand response

Code for the MSc dissertation *Towards Equitable Energy: Temporal Load Modelling for Inclusive Demand-Response* (University of Manchester, DATA72000, 2025). It analyses GB household electricity and gas use from SERL smart-meter statistics (2020–2023): demand patterns, regional forecasting, household groups and personas, and whether low-income households lose out under dynamic (half-hourly) tariffs, priced with real Octopus Energy rates for 2022, 2023 and 2024.

---

## Contents

* [Repository layout](#repository-layout)
* [Setup](#setup)
* [Data (SERL Study 8963)](#data-serl-study-8963)
* [Running the analysis](#running-the-analysis)
* [Notebooks](#notebooks)
* [Outputs and naming](#outputs-and-naming)
* [Figure theme](#figure-theme)
* [Results at a glance](#results-at-a-glance)
* [Data protection](#data-protection)
* [Citations and licensing](#citations-and-licensing)

---

## Repository layout

The layout follows [Cookiecutter Data Science](https://cookiecutter-data-science.drivendata.org/).

```
├── data/                      not committed (SERL licence); see data/README.md
│   ├── raw/serl/              SERL Study 8963 files as downloaded
│   ├── raw/literature/        hand-compiled literature table
│   ├── interim/               cleaned SERL daily file (scripts/make_dataset.py)
│   └── external/              cached third-party data (Octopus prices, API caches)
├── notebooks/                 <phase>.<step>-<initials>-<description>.ipynb
├── src/serl_energy/           installable project package
│   ├── config.py              every path in one place
│   ├── dataset.py             load and slice SERL statistics (one group, one unit at a time)
│   ├── labels.py              readable group names and energy-poverty proxies
│   ├── tariffs.py             Octopus prices (cached) and bill calculations
│   ├── plots.py               shared figure theme
│   └── reporting.py           save figures and tables with consistent names
├── design/                    tokens.json (colours, fonts) shared with the dashboard; fonts/ (Inter, OFL)
├── reports/                   generated, not committed
│   ├── figures/<notebook>/    every figure as 300-dpi PNG and SVG
│   └── tables/<notebook>/     every results table as CSV (snake_case columns)
├── docs/                      data-dictionary.md (generated), dissertation PDF
├── scripts/                   make_dataset.py, run_all.py, build_data_dictionary.py
├── tests/                     pytest suite
├── pyproject.toml             package metadata and pytest settings
└── requirements.txt           pinned environment
```

---

## Setup

Python 3.10 or later (tested on 3.12).

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # pinned libraries + the serl_energy package in editable mode
python -m pytest                   # 58 tests; the ones that need SERL data are skipped if data/ is empty
```

Notebooks import the project code as a package (`from serl_energy import dataset as serl, plots, tariffs`), so they run from any folder.

---

## Data (SERL Study 8963)

Analyses use the **Smart Energy Research Lab (SERL) Study 8963, 2020–2023** aggregated statistics (daily and half-hourly), available from the UK Data Service under its End User Licence.

1. Download the daily and the four half-hourly aggregated files.
2. Put them in `data/raw/serl/` with the names in [`data/README.md`](data/README.md).
3. Run `python scripts/make_dataset.py` to build the cleaned daily file in `data/interim/`.

Octopus prices are downloaded from the public API on first use and cached in `data/external/octopus/`; if a download fails and nothing is cached, the code stops with an error rather than invent prices.

---

## Running the analysis

```bash
python scripts/make_dataset.py          # once, after placing the SERL files
python scripts/run_all.py               # re-runs every notebook in order, then the data dictionary
python scripts/run_all.py 4.1 4.2       # only some notebooks
python scripts/run_all.py --skip 5.1    # skip the literature review (1.6 GB model download)
```

Seeds are fixed (`random_state=42` / `random_seed=42`); no GPU is needed.

**Selecting SERL data.** Each SERL file stacks overlapping household groups (whole sample, heating fuel, PV, region, EPC, tenure, …), each in three units. Averaging rows without choosing one group and one unit mixes them, so `serl_energy.dataset` raises an error when a filter is missing:

```python
from serl_energy import dataset as serl

monthly = serl.load_monthly(serl.CLEAN_CSV)
gas = serl.monthly_series(monthly, "Gas", "kWh/day")                                  # whole sample, 48 months
regions = serl.monthly_panel(monthly, "Electricity net", "kWh/day", "region")         # 48 months x 11 regions
profile = serl.daily_profile(serl.load_half_hourly([2023]), 2023, "Electricity imports", "Wh", to_kwh=True)
```

---

## Notebooks

| Notebook | Question |
|---|---|
| `1.1-aj-eda-univariate` | How much energy, when in the day and year, how unequal between households, and by household type? |
| `1.2-aj-eda-bivariate` | Electricity vs gas, solar PV, heating fuel, weekends, temperature and sunshine. |
| `1.3-aj-eda-distributions` | Spread, skewness and precision of use through the day. |
| `2.1-aj-forecasting-regional` | Regional monthly forecasts: rolling-origin backtest of naive, ETS, SARIMA, SARIMAX; 2024 forecasts. |
| `3.1-aj-household-seasonality` | Seasonal patterns of 75 household groups and k-means clusters of their shapes. |
| `3.2-aj-household-personas` | Demand personas from seven features per group. |
| `4.1-aj-tariffs-demand-models` | Bayesian gas–weather model, ML for monthly electricity, 2023 Agile vs flat by quarter, group and region. |
| `4.2-aj-energy-poverty-tariffs` | HDBSCAN groupings, energy-poverty signals, SARIMA 2024, tariff scenarios, 2022 crisis test. |
| `5.1-aj-literature-review` | Methods in the reviewed literature; zero-shot labels validated against hand coding. |

Every notebook follows the same structure: Question → Data → Method → numbered results (each figure introduced by what to look for) → Conclusions → Limitations.

---

## Outputs and naming

* **Figures:** `reports/figures/<notebook>/<name>.png` (300 dpi) and `.svg`; names are kebab-case (`daily-profile-by-year`).
* **Tables:** `reports/tables/<notebook>/<name>.csv`; table and column names are snake_case starting with a letter (`agile_saving_pct`, `flat_gbp`). The checks live in `serl_energy.reporting`, so names cannot drift.
* **Data dictionary:** [`docs/data-dictionary.md`](docs/data-dictionary.md) describes every table and column; it is regenerated by `scripts/run_all.py`.

---

## Figure theme

All figures share one theme defined in `design/tokens.json`, the same file the dashboard will read:

* **Fixed colour meanings:** electricity blue, gas orange, Agile aqua, solar export yellow, flat tariff grey, groups linked to energy poverty red, comparators violet; years 2020–2024 as one blue ramp (later = darker).
* **Palettes checked with a colour-vision-deficiency validator** in light and dark mode; sequential (one hue) and diverging (blue / grey / red) scales for heatmaps; status colours reserved for alerts.
* **One y-axis per chart**, Inter typeface (bundled under the SIL Open Font Licence), direct labels where they help.

---

## Results at a glance

* **Demand fell by about a fifth, mostly in 2022:** electricity imports 10.9 → 8.5 kWh/day and gas 36.8 → 29.1 kWh/day per household (2020 → 2023), while the electricity peak stayed at **18:30** every year.
* **Forecasting:** ETS is most accurate on consistent regional series (MASE 0.49, MAPE 7.8%); all models beat seasonal naive. Heating degree days do not improve forecasts when future weather must be estimated (p = 0.41).
* **Who is different:** heating fuel and size, not deprivation, define distinct demand patterns. Electric-heated homes use 26.7 kWh/day of electricity on −5 to 0 °C days vs 7.0 on warm days; gas rises by 5.2 kWh/day per heating degree-day (Bayesian, R² 0.92). Deprived groups use less energy but in the same pattern.
* **Energy-poverty signals:** lower use in deprived groups matches smaller homes, not under-heating per m²; deprived and rented homes have less solar PV (3.6% in IMD 1 vs 8.1% in IMD 5) and more electric heating.
* **Tariffs in calm years:** Agile was about 32% cheaper than the flat tariff in Jul–Dec 2023 (London) and 29–34% cheaper in 2024 for every group. The most deprived pay 4.7% more per kWh on the same tariff (standing charges), 11.6% more if they cannot shift, and 57% more if they cannot switch.
* **Crisis test (Apr–Dec 2022):** on the Agile product available at the height of the crisis, every group would have paid about **23–24% more** than on the flat tariff; August 2022 bills roughly doubled and load shifting barely helped. Dynamic tariffs pass wholesale-price risk to households; timing differences between deprived and other households change bills by only about one percentage point.

---

## Data protection

SERL data are licensed and are never committed: `data/` and `reports/` are git-ignored. Published outputs (figures, the future dashboard) contain **group-level aggregates only**, from groups of at least 50 households, rounded for display, with no combinations of characteristics that could narrow down small groups. Check the UK Data Service licence conditions before publishing results.

---

## Citations and licensing

* **Dissertation:** *Towards Equitable Energy: Temporal Load Modelling for Inclusive Demand-Response* (University of Manchester, 2025).
* **Data:** Smart Energy Research Lab (SERL), Study 8963: aggregated daily and half-hourly statistics, Great Britain, 2020–2023 (UK Data Service).
* **Prices:** Octopus Energy public API (Agile Octopus and Flexible Octopus tariffs).
* **Code:** Apache License 2.0 (see `LICENSE`). **Font:** Inter, SIL Open Font License 1.1 (`design/fonts/OFL.txt`). **SERL data** are not redistributed and remain under the UK Data Service End User Licence.
