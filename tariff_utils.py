"""Electricity bills for SERL consumption profiles under published Octopus tariffs.

Prices come from the public Octopus Energy API (no key needed) and are cached
in outputs/artifacts/ so later runs work offline. If a download fails and
nothing is cached, an error is raised; no prices are ever invented.

Consumption is built from SERL data (see serl_utils):
- the annual mean half-hourly profile gives the *shape* of a day
  (separately for weekdays and weekends where SERL provides it),
- the monthly mean daily consumption gives the *level* for each month.

Example
-------
>>> rates = half_hourly_rates(fetch_unit_rates(AGILE_PRODUCT, agile_code("C"), "2023-01-01", "2024-01-01"),
...                           "2023-01-01", "2024-01-01")
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Mapping, Optional

import numpy as np
import pandas as pd

OCTOPUS_API = "https://api.octopus.energy/v1/products"
ARTIFACTS_DIR = Path(__file__).resolve().parent / "outputs" / "artifacts"

# products that applied to 2023 (checked against the API's availability dates)
AGILE_PRODUCT = "AGILE-FLEX-22-11-25"   # Agile Octopus November 2022 v1
FLEX_PRODUCT = "VAR-22-11-01"           # Flexible Octopus (standard variable, follows the price cap)

UK_TZ = "Europe/London"


def agile_code(region: str) -> str:
    """Tariff code for Agile in a GSP region letter (A–P)."""
    return f"E-1R-{AGILE_PRODUCT}-{region}"


def flex_code(region: str) -> str:
    """Tariff code for Flexible Octopus in a GSP region letter (A–P)."""
    return f"E-1R-{FLEX_PRODUCT}-{region}"


# ── downloading (cached) ──────────────────────────────────────────────────────
def _get_all(url: str, timeout: int = 30) -> list[dict]:
    """Follow the API's `next` links and return all results."""
    results = []
    while url:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            page = json.load(resp)
        results.extend(page["results"])
        url = page.get("next")
    return results


def _fetch(kind: str, product: str, tariff_code: str, start: str, end: str,
           payment_method: Optional[str], cache_dir: Path) -> pd.DataFrame:
    cache = Path(cache_dir) / f"octopus_{tariff_code}_{kind}_{start}_{end}.csv"
    if cache.exists():
        df = pd.read_csv(cache)
    else:
        url = (f"{OCTOPUS_API}/{product}/electricity-tariffs/{tariff_code}/{kind}/"
               f"?period_from={start}T00:00Z&period_to={end}T00:00Z&page_size=1500")
        try:
            rows = _get_all(url)
        except Exception as exc:
            raise RuntimeError(f"Could not download {kind} for {tariff_code} and no cache at {cache}") from exc
        if not rows:
            raise RuntimeError(f"No {kind} returned for {tariff_code} {start}..{end}")
        df = pd.DataFrame(rows)
        cache.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache, index=False)

    if payment_method is not None and "payment_method" in df.columns:
        df = df[df["payment_method"].isna() | df["payment_method"].eq(payment_method)]
    out = pd.DataFrame({
        "valid_from": pd.to_datetime(df["valid_from"], utc=True),
        "valid_to": pd.to_datetime(df["valid_to"], utc=True),
        "p_inc_vat": df["value_inc_vat"].astype(float),
    })
    return out.sort_values("valid_from").reset_index(drop=True)


def fetch_unit_rates(product: str, tariff_code: str, start: str, end: str,
                     payment_method: Optional[str] = "DIRECT_DEBIT",
                     cache_dir: Path = ARTIFACTS_DIR) -> pd.DataFrame:
    """Unit rates (p/kWh inc. VAT) valid between `start` and `end` (YYYY-MM-DD)."""
    return _fetch("standard-unit-rates", product, tariff_code, start, end, payment_method, cache_dir)


def fetch_standing_charges(product: str, tariff_code: str, start: str, end: str,
                           payment_method: Optional[str] = "DIRECT_DEBIT",
                           cache_dir: Path = ARTIFACTS_DIR) -> pd.DataFrame:
    """Standing charges (p/day inc. VAT) valid between `start` and `end`."""
    return _fetch("standing-charges", product, tariff_code, start, end, payment_method, cache_dir)


# ── expanding prices to the half-hour grid ───────────────────────────────────
def half_hour_index(start: str, end: str) -> pd.DatetimeIndex:
    """UTC half-hour start times in [start, end)."""
    return pd.date_range(pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC"),
                         freq="30min", inclusive="left")


def _expand(rates: pd.DataFrame, index: pd.DatetimeIndex) -> pd.Series:
    """Value in force at each time in `index` (rates are [valid_from, valid_to) intervals)."""
    grid = pd.DataFrame({"t": index})
    merged = pd.merge_asof(grid, rates, left_on="t", right_on="valid_from", direction="backward")
    open_ended = merged["valid_to"].isna()
    in_force = open_ended | (merged["t"] < merged["valid_to"])
    values = merged["p_inc_vat"].where(in_force & merged["valid_from"].notna())
    if values.isna().any():
        missing = merged.loc[values.isna(), "t"]
        raise ValueError(f"No rate in force for {len(missing)} half-hours, e.g. {missing.iloc[0]}")
    return pd.Series(values.to_numpy(), index=index)


def half_hourly_rates(unit_rates: pd.DataFrame, start: str, end: str) -> pd.Series:
    """Unit rate (p/kWh) for every UTC half-hour in [start, end)."""
    return _expand(unit_rates, half_hour_index(start, end)).rename("p_per_kwh")


def daily_standing_charges(standing: pd.DataFrame, start: str, end: str) -> pd.Series:
    """Standing charge (p) for every UK calendar day in [start, end)."""
    days = pd.date_range(start, end, freq="D", inclusive="left", tz=UK_TZ)
    s = _expand(standing, days.tz_convert("UTC"))
    s.index = days.date
    return s.rename("p_per_day")


def _uk_times(s: pd.Series) -> pd.DatetimeIndex:
    """The series' half-hour start times in UK clock time.

    Raises TypeError unless `s` is indexed by timezone-aware timestamps
    (as produced by `half_hour_index` / `build_consumption`).
    """
    if not isinstance(s.index, pd.DatetimeIndex) or s.index.tz is None:
        raise TypeError("expected a series indexed by timezone-aware timestamps (see half_hour_index)")
    return s.index.tz_convert(UK_TZ)


# ── consumption ───────────────────────────────────────────────────────────────
def build_consumption(
    profiles: Mapping[str, pd.Series],
    monthly_kwh_per_day: pd.Series,
    index: pd.DatetimeIndex,
    profile_time_is_utc: bool = True,
) -> pd.Series:
    """kWh used in each half-hour of `index` (UTC).

    Args:
        profiles: 48-value half-hourly profiles indexed by "HH:MM". Keys
            "both", and optionally "weekday" and "weekend". When the split is
            given, each day uses its own shape, and weekday/weekend daily
            totals keep their ratio to the "both" profile.
        monthly_kwh_per_day: mean daily consumption per month (month-start index).
        profile_time_is_utc: whether SERL's half-hour labels are UTC (True) or
            UK clock time (False). Also decides which clock defines the day
            and month.
    """
    clock = index if profile_time_is_utc else index.tz_convert(UK_TZ)
    labels = clock.strftime("%H:%M")
    months = pd.DatetimeIndex(clock.tz_localize(None)).to_period("M").to_timestamp()
    is_weekend = clock.dayofweek >= 5

    both = profiles["both"]
    split = "weekday" in profiles and "weekend" in profiles

    level = monthly_kwh_per_day.reindex(months).to_numpy()
    if np.isnan(level).any():
        raise ValueError("monthly_kwh_per_day has no value for some months in the index")

    def share(p: pd.Series) -> np.ndarray:
        return (p / p.sum()).reindex(labels).to_numpy()

    if split:
        wd, we = profiles["weekday"], profiles["weekend"]
        frac = np.where(is_weekend, share(we), share(wd))
        factor = np.where(is_weekend, we.sum() / both.sum(), wd.sum() / both.sum())
    else:
        frac, factor = share(both), 1.0
    if np.isnan(frac).any():
        raise ValueError("profile is missing some half-hour labels")
    return pd.Series(frac * factor * level, index=index, name="kwh")


def shift_peak(
    kwh: pd.Series,
    p_per_kwh: pd.Series,
    fraction: float,
    peak: tuple[str, str] = ("16:00", "19:00"),
    n_cheapest: int = 8,
) -> pd.Series:
    """Move `fraction` of each day's peak-window use into that day's cheapest half-hours.

    The peak window is in UK clock time (Agile's 16:00–19:00 peak). Moved
    energy is spread evenly over the `n_cheapest` lowest-priced half-hours of
    the same UK day outside the peak window. Total daily energy is unchanged.
    """
    local = _uk_times(kwh)
    hhmm = local.strftime("%H:%M")
    in_peak = (hhmm >= peak[0]) & (hhmm < peak[1])
    df = pd.DataFrame({"kwh": kwh.to_numpy(), "p": p_per_kwh.reindex(kwh.index).to_numpy(),
                       "day": local.date, "peak": in_peak})
    moved = np.where(df["peak"], df["kwh"] * fraction, 0.0)
    df["kwh"] -= moved
    df["moved"] = moved
    # rank off-peak half-hours by price within each day (peak slots never receive load)
    df["p_rank"] = df["p"].where(~df["peak"]).groupby(df["day"]).rank(method="first")
    receives = df["p_rank"] <= n_cheapest
    per_day = df.groupby("day")["moved"].transform("sum")
    n_recv = receives.groupby(df["day"]).transform("sum")
    df.loc[receives, "kwh"] += per_day[receives] / n_recv[receives]
    return pd.Series(df["kwh"].to_numpy(), index=kwh.index, name="kwh")


# ── bills ─────────────────────────────────────────────────────────────────────
def bill(kwh: pd.Series, p_per_kwh: pd.Series, standing_p_per_day: pd.Series) -> dict:
    """Energy, standing and total cost (GBP) over the period covered by `kwh`."""
    p = p_per_kwh.reindex(kwh.index)
    if p.isna().any():
        raise ValueError("price series does not cover all half-hours")
    days = pd.Index(_uk_times(kwh).date).unique()
    energy = float((kwh * p).sum()) / 100
    standing = float(standing_p_per_day.reindex(days).sum()) / 100
    total_kwh = float(kwh.sum())
    return {"kwh": total_kwh, "energy_gbp": energy, "standing_gbp": standing,
            "total_gbp": energy + standing, "unit_p_per_kwh": 100 * energy / total_kwh}


def compare(kwh: pd.Series, tariffs: Mapping[str, tuple[pd.Series, pd.Series]], by: str = "Q") -> pd.DataFrame:
    """Bills per period (`by`: "Q" quarter, "M" month, "Y" year) for each tariff.

    `tariffs` maps a name to (half-hourly p/kWh, daily standing p/day).
    """
    period = _uk_times(kwh).tz_localize(None).to_period(by)
    rows = []
    for per in period.unique():
        part = kwh[period == per]
        for name, (rates, standing) in tariffs.items():
            rows.append({"period": str(per), "tariff": name, **bill(part, rates, standing)})
    return pd.DataFrame(rows)
