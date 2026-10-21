"""Build data/interim/clean_aggregated_data_2020_2023.csv from the raw SERL daily file.

    python scripts/make_dataset.py

See `serl_energy.dataset.make_clean_daily` for what the cleaning does (column
names and row order only; no values are changed).
"""
from serl_energy import config
from serl_energy.dataset import make_clean_daily


def main() -> None:
    clean = make_clean_daily(config.SERL_DAILY_CSV)
    config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    clean.to_csv(config.CLEAN_DAILY_CSV, index=False)
    print(f"wrote {config.CLEAN_DAILY_CSV.relative_to(config.PROJECT_DIR)}: {clean.shape[0]:,} rows x {clean.shape[1]} columns")


if __name__ == "__main__":
    main()
