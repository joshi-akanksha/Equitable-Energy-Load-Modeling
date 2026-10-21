# data/

Input files for the notebooks. Nothing in this folder except this README is
committed: the SERL files are licensed (UK Data Service, Study 8963) and too
large for GitHub.

After downloading Study 8963 from the UK Data Service, place these files here
with exactly these names:

| File | Used by |
|---|---|
| `serl_daily_energy_use_in_gb_domestic_buildings_2020_to_2023_aggregated_statistics.csv` | DemandModelling 1 & 2, TariffSimulation |
| `serl_half_hourly_energy_use_in_gb_domestic_buildings_2020_aggregated_statistics.csv` | EDA notebooks |
| `serl_half_hourly_energy_use_in_gb_domestic_buildings_2021_aggregated_statistics.csv` | EDA notebooks |
| `serl_half_hourly_energy_use_in_gb_domestic_buildings_2022_aggregated_statistics.csv` | EDA notebooks |
| `serl_half_hourly_energy_use_in_gb_domestic_buildings_2023_aggregated_statistics.csv` | EDA notebooks |
| `Clean_Aggregated_data_2020_2023.csv` | DemandModelling, TemporalForecasting, EDA - UnivariateYearly |
| `Bibliometric_Analysis.csv` | Bibliometric_Analyis (own literature table, not part of SERL) |

`Clean_Aggregated_data_2020_2023.csv` is the daily file after the cleaning in
the first cell of `DemandModelling 1.ipynb` (columns renamed, redundant columns
dropped). It was previously called `forcasting.csv`.

Notebooks use paths relative to the repository root, so run them from there.
