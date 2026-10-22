# data/

Inputs for the notebooks. Nothing here except this README and the empty folder
skeleton is committed: the SERL files are licensed (UK Data Service, Study 8963)
and too large for GitHub. All paths are defined once in `src/serl_energy/config.py`.

| Folder | File | Source |
|---|---|---|
| `raw/serl/` | `serl_daily_energy_use_in_gb_domestic_buildings_2020_to_2023_aggregated_statistics.csv` | UK Data Service, Study 8963 |
| `raw/serl/` | `serl_half_hourly_energy_use_in_gb_domestic_buildings_<year>_aggregated_statistics.csv` for 2020, 2021, 2022, 2023 | UK Data Service, Study 8963 |
| `raw/literature/` | `bibliometric_analysis.csv` | own literature table (5.1 notebook) |
| `interim/` | `clean_aggregated_data_2020_2023.csv` | built by `python scripts/make_dataset.py` from the raw daily file |
| `external/octopus/` | `octopus_<tariff>_<kind>_<start>_<end>.csv` | Octopus Energy public API, cached automatically on first use |
| `external/api_cache/` | geocoding and Google Trends caches | unused appendix clients in 2.1 |

The cleaned daily file is the raw daily file with the first two segment columns
renamed (`primary_space_heating_fuel`, `has_PV`), the generic segment names and the
empty `summary_time` column dropped, and rows ordered by period. No values are
changed; a test checks that the rebuild matches the file exactly.
