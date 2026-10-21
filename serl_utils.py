"""Load and slice SERL aggregated statistics (UK Data Service Study 8963).

Every SERL file stacks many *overlapping* groups of households in one table:
the whole sample, each heating fuel, PV / no PV, each region, EPC band,
tenure, ... and each quantity is repeated in three units (per household,
per m2, per person). Averaging or modelling across rows without first picking
exactly one group and one unit mixes these together and gives meaningless
numbers.

Use `select_slice` (or the wrappers built on it) before any statistic. It
raises an error when a filter is missing instead of silently mixing groups.

Example
-------
>>> from serl_utils import load_monthly, monthly_series, monthly_panel
>>> df = load_monthly()
>>> y = monthly_series(df, "Electricity net", "kWh/day")              # 48 months
>>> regions = monthly_panel(df, "Electricity net", "kWh/day", "region") # 48 x 11
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

# ── file locations (relative to this file, so they work from any cwd) ─────────
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
DAILY_CSV = DATA_DIR / "serl_daily_energy_use_in_gb_domestic_buildings_2020_to_2023_aggregated_statistics.csv"
CLEAN_CSV = DATA_DIR / "Clean_Aggregated_data_2020_2023.csv"
YEARS = (2020, 2021, 2022, 2023)


def half_hourly_csv(year: int) -> Path:
    """Path of the half-hourly aggregated statistics file for `year`."""
    return DATA_DIR / f"serl_half_hourly_energy_use_in_gb_domestic_buildings_{year}_aggregated_statistics.csv"


# raw SERL files name the first two segments generically; the clean file does not
_RENAMES = {"segment_1_value": "primary_space_heating_fuel", "segment_2_value": "has_PV"}
_DROP = ["segmentation_variable_1", "segmentation_variable_2"]


def _standardise(df: pd.DataFrame) -> pd.DataFrame:
    """Give raw and cleaned SERL files the same column names."""
    df = df.rename(columns=_RENAMES)
    return df.drop(columns=[c for c in _DROP if c in df.columns])


# ── loaders ───────────────────────────────────────────────────────────────────
def load_monthly(path: Path | str = DAILY_CSV) -> pd.DataFrame:
    """Monthly rows of the daily-statistics file, with a month-start `date` column.

    Values are average energy per day within the month (e.g. kWh/day).
    Works with the raw SERL daily file or Clean_Aggregated_data_2020_2023.csv.
    """
    df = _standardise(pd.read_csv(path))
    period = df["aggregation_period"].astype(str).str.strip()
    df = df[period.str.fullmatch(r"\d{4}-\d{2}")].copy()
    df["date"] = pd.to_datetime(df["aggregation_period"].astype(str), format="%Y-%m")
    return df.reset_index(drop=True)


def load_yearly(path: Path | str = DAILY_CSV) -> pd.DataFrame:
    """Yearly rows of the daily-statistics file, with an integer `year` column."""
    df = _standardise(pd.read_csv(path))
    period = df["aggregation_period"].astype(str).str.strip()
    df = df[period.str.fullmatch(r"\d{4}")].copy()
    df["year"] = df["aggregation_period"].astype(int)
    return df.reset_index(drop=True)


def load_half_hourly(years: Iterable[int] = YEARS) -> pd.DataFrame:
    """Half-hourly profiles (one row per half-hour slot), stacked across `years`.

    Adds `year` and `half_hour` (0 = 00:00, 47 = 23:30). Values are energy per
    half-hour in Wh (or Wh/m2, Wh/person).
    """
    frames = []
    for year in years:
        df = _standardise(pd.read_csv(half_hourly_csv(year)))
        df["year"] = int(year)
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    t = pd.to_datetime(df["summary_time"], format="%H:%M")
    df["half_hour"] = t.dt.hour * 2 + t.dt.minute // 30
    return df


# ── slicing ───────────────────────────────────────────────────────────────────
def _check_value(df: pd.DataFrame, column: str, value) -> None:
    """Raise a helpful error if `value` never occurs in `column`."""
    # segment levels can be numbers (e.g. IMD quintiles), so compare as text there
    values = df[column].astype(str) if column == "segment_3_value" else df[column]
    if not values.eq(str(value) if column == "segment_3_value" else value).any():
        options = sorted(df[column].dropna().astype(str).unique())
        raise ValueError(f"{column}={value!r} not found. Options: {options}")


def select_slice(
    df: pd.DataFrame,
    quantity: str,
    unit: str,
    weekday_weekend: str = "both",
    fuel: str = "All",
    pv: str = "All",
    segment: Optional[str] = None,
    segment_value: Optional[str] = None,
) -> pd.DataFrame:
    """Return exactly one group of households, in one unit.

    Args:
        quantity: e.g. "Electricity imports", "Gas", "Electricity net".
        unit: e.g. "kWh/day" (monthly/yearly files) or "Wh" (half-hourly files).
        weekday_weekend: "both", "weekday" or "weekend". The split exists only
            for the whole sample (segment=None).
        fuel: primary space-heating fuel: "All", "Gas" or "Electric".
        pv: "All", "Yes" or "No".
        segment: segmentation_variable_3, e.g. "region", "currentEnergyRating",
            "IMD_quintile". None means the whole sample (no third segment).
        segment_value: one level of `segment`, e.g. "Scotland". If None, all
            levels are returned (one row per level per time step).

    Raises:
        ValueError: if a filter value does not exist, the slice is empty, or
            the slice still has more than one row per time step (and segment
            level), which means rows from different groups would be mixed.
    """
    _check_value(df, "quantity", quantity)
    _check_value(df, "unit", unit)
    _check_value(df, "weekday_weekend", weekday_weekend)
    _check_value(df, "primary_space_heating_fuel", fuel)
    _check_value(df, "has_PV", pv)

    mask = (
        df["quantity"].eq(quantity)
        & df["unit"].eq(unit)
        & df["weekday_weekend"].eq(weekday_weekend)
        & df["primary_space_heating_fuel"].eq(fuel)
        & df["has_PV"].eq(pv)
    )
    if segment is None:
        mask &= df["segmentation_variable_3"].isna()
    else:
        _check_value(df, "segmentation_variable_3", segment)
        mask &= df["segmentation_variable_3"].eq(segment)
        if segment_value is not None:
            _check_value(df[df["segmentation_variable_3"].eq(segment)], "segment_3_value", segment_value)
            mask &= df["segment_3_value"].astype(str).eq(str(segment_value))

    out = df[mask].copy()
    if out.empty:
        hint = ""
        if weekday_weekend != "both" and segment is not None:
            hint = " SERL only splits weekday/weekend for the whole sample (segment=None)."
        raise ValueError(f"Slice is empty for these filters.{hint}")

    key = [c for c in ("date", "year", "half_hour") if c in out.columns]
    if segment is not None:
        key.append("segment_3_value")
    if out.duplicated(key).any():
        raise ValueError(f"Slice has more than one row per {key}; a filter is missing.")
    return out.sort_values(key).reset_index(drop=True)


# ── convenience wrappers ──────────────────────────────────────────────────────
def monthly_series(
    df: pd.DataFrame, quantity: str, unit: str, value: str = "mean", **filters
) -> pd.Series:
    """One monthly time series (month-start frequency) for a single group.

    Months that SERL suppressed (too few households) come back as NaN, so check
    `series.isna().sum()` before modelling.
    """
    if filters.get("segment") is not None and filters.get("segment_value") is None:
        raise ValueError("Give segment_value for one series, or use monthly_panel for all levels.")
    s = select_slice(df, quantity, unit, **filters).set_index("date")[value]
    return s.asfreq("MS").rename(f"{quantity} ({unit})")


def monthly_panel(
    df: pd.DataFrame, quantity: str, unit: str, segment: str, value: str = "mean", **filters
) -> pd.DataFrame:
    """Wide table of monthly series: one column per level of `segment`."""
    s = select_slice(df, quantity, unit, segment=segment, **filters)
    panel = s.pivot(index="date", columns="segment_3_value", values=value)
    return panel.asfreq("MS")


def daily_profile(
    hh: pd.DataFrame,
    year: int,
    quantity: str,
    unit: str,
    value: str = "mean",
    to_kwh: bool = False,
    **filters,
) -> pd.Series:
    """48 half-hourly values (00:00 ... 23:30) for one group in one year.

    Args:
        hh: output of `load_half_hourly`.
        to_kwh: convert Wh-based units to kWh (divide by 1000).
    """
    if filters.get("segment") is not None and filters.get("segment_value") is None:
        raise ValueError("Give segment_value to get a single profile.")
    s = select_slice(hh[hh["year"].eq(year)], quantity, unit, **filters)
    profile = s.set_index("summary_time")[value]
    if to_kwh:
        if not unit.startswith("Wh"):
            raise ValueError(f"to_kwh=True expects a Wh-based unit, got {unit!r}")
        profile = profile / 1000
    return profile.rename(f"{quantity} ({'k' + unit if to_kwh else unit}), {year}")
