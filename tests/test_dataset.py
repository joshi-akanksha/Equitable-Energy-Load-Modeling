"""Unit tests for serl_energy.dataset on small synthetic tables (no SERL data needed)."""
import numpy as np
import pandas as pd
import pytest

from serl_energy.dataset import _standardise, daily_profile, monthly_panel, monthly_series, select_slice


def make_monthly(months=3):
    """Mimic the SERL layout: overlapping groups and several units per month."""
    rows = []
    for d in pd.date_range("2023-01-01", periods=months, freq="MS"):
        for unit, scale in (("kWh/day", 1.0), ("kWh/m2/day", 0.01)):
            # whole sample, a PV split and a region split all share the same month
            rows.append(dict(date=d, unit=unit, has_PV="All", segmentation_variable_3=np.nan,
                             segment_3_value=np.nan, mean=10 * scale))
            rows.append(dict(date=d, unit=unit, has_PV="Yes", segmentation_variable_3=np.nan,
                             segment_3_value=np.nan, mean=8 * scale))
            for region, v in (("Wales", 9), ("Scotland", 12)):
                rows.append(dict(date=d, unit=unit, has_PV="All", segmentation_variable_3="region",
                                 segment_3_value=region, mean=v * scale))
    df = pd.DataFrame(rows)
    df["quantity"] = "Electricity net"
    df["weekday_weekend"] = "both"
    df["primary_space_heating_fuel"] = "All"
    return df


def test_select_slice_returns_one_row_per_month():
    out = select_slice(make_monthly(), "Electricity net", "kWh/day")
    assert len(out) == 3
    assert (out["mean"] == 10).all()


def test_select_slice_with_segment_returns_one_row_per_level():
    out = select_slice(make_monthly(), "Electricity net", "kWh/day", segment="region")
    assert len(out) == 6
    assert set(out["segment_3_value"]) == {"Wales", "Scotland"}


def test_duplicate_rows_raise():
    df = make_monthly()
    df = pd.concat([df, df.iloc[[0]]])  # same month and group twice
    with pytest.raises(ValueError, match="more than one row"):
        select_slice(df, "Electricity net", "kWh/day")


def test_unknown_value_lists_options():
    with pytest.raises(ValueError, match=r"unit='kWh'.*kWh/day"):
        select_slice(make_monthly(), "Electricity net", "kWh")
    with pytest.raises(ValueError, match="Options: .*Wales"):
        select_slice(make_monthly(), "Electricity net", "kWh/day", segment="region", segment_value="Kent")


def test_weekday_with_segment_explains_why_empty():
    df = make_monthly()
    extra = df.iloc[[0]].assign(weekday_weekend="weekday")  # weekday exists only for whole sample
    df = pd.concat([df, extra])
    with pytest.raises(ValueError, match="only splits weekday/weekend"):
        select_slice(df, "Electricity net", "kWh/day", weekday_weekend="weekday", segment="region")


def test_monthly_series_keeps_gaps_as_nan():
    df = make_monthly(months=4)
    df = df[df["date"] != "2023-02-01"]  # suppressed month
    s = monthly_series(df, "Electricity net", "kWh/day")
    assert len(s) == 4 and s.isna().sum() == 1
    assert isinstance(s.index, pd.DatetimeIndex) and s.index.freqstr == "MS"


def test_monthly_series_requires_segment_value():
    with pytest.raises(ValueError, match="monthly_panel"):
        monthly_series(make_monthly(), "Electricity net", "kWh/day", segment="region")


def test_monthly_panel_shape():
    panel = monthly_panel(make_monthly(), "Electricity net", "kWh/day", "region")
    assert panel.shape == (3, 2)
    assert panel.loc["2023-01-01", "Scotland"] == 12


def test_standardise_renames_raw_columns():
    raw = pd.DataFrame(columns=["segmentation_variable_1", "segment_1_value",
                                "segmentation_variable_2", "segment_2_value"])
    assert list(_standardise(raw).columns) == ["primary_space_heating_fuel", "has_PV"]


def test_daily_profile_converts_to_kwh():
    times = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]
    hh = pd.DataFrame(dict(summary_time=times, half_hour=range(48), year=2023, mean=500.0,
                           quantity="Electricity imports", unit="Wh", weekday_weekend="both",
                           primary_space_heating_fuel="All", has_PV="All",
                           segmentation_variable_3=np.nan, segment_3_value=np.nan))
    p = daily_profile(hh, 2023, "Electricity imports", "Wh", to_kwh=True)
    assert len(p) == 48 and p.iloc[0] == 0.5
    with pytest.raises(ValueError, match="Wh-based"):
        daily_profile(hh.assign(unit="kWh/day"), 2023, "Electricity imports", "kWh/day", to_kwh=True)
