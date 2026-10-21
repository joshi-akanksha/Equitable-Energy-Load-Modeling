"""Project paths in one place, so notebooks and scripts work from any folder.

Layout follows Cookiecutter Data Science:

    data/raw/serl/        SERL Study 8963 files as downloaded (never edited, never committed)
    data/raw/literature/  own literature table for the bibliometric notebook
    data/interim/         cleaned SERL daily file
    data/external/        third-party data cached from APIs (Octopus prices, appendix caches)
    reports/figures/<notebook>/   every saved figure (PNG + SVG)
    reports/tables/<notebook>/    every saved results table (CSV, snake_case columns)
    design/tokens.json    colours and fonts shared with the dashboard (design/fonts: Inter, OFL)
"""
from __future__ import annotations

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
SERL_DIR = RAW_DIR / "serl"
LITERATURE_DIR = RAW_DIR / "literature"
INTERIM_DIR = DATA_DIR / "interim"
EXTERNAL_DIR = DATA_DIR / "external"
OCTOPUS_CACHE_DIR = EXTERNAL_DIR / "octopus"
API_CACHE_DIR = EXTERNAL_DIR / "api_cache"

REPORTS_DIR = PROJECT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"

DESIGN_TOKENS = PROJECT_DIR / "design" / "tokens.json"
DESIGN_FONTS_DIR = PROJECT_DIR / "design" / "fonts"

SERL_DAILY_CSV = SERL_DIR / "serl_daily_energy_use_in_gb_domestic_buildings_2020_to_2023_aggregated_statistics.csv"
CLEAN_DAILY_CSV = INTERIM_DIR / "clean_aggregated_data_2020_2023.csv"
BIBLIOMETRIC_CSV = LITERATURE_DIR / "bibliometric_analysis.csv"


def serl_half_hourly_csv(year: int) -> Path:
    """Path of the SERL half-hourly aggregated statistics file for `year`."""
    return SERL_DIR / f"serl_half_hourly_energy_use_in_gb_domestic_buildings_{year}_aggregated_statistics.csv"
