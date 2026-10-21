"""Checks against the real SERL files. Skipped when data/ is not present."""
import pytest

import serl_utils as su

pytestmark = pytest.mark.skipif(not su.DAILY_CSV.exists(), reason="SERL data not in data/")

QUANTITIES = ["Electricity imports", "Electricity exports", "Electricity net",
              "Gas", "Gas + electricity imports"]


@pytest.fixture(scope="module")
def monthly():
    return su.load_monthly()


@pytest.fixture(scope="module")
def half_hourly():
    return su.load_half_hourly()


def test_clean_file_matches_raw_monthly(monthly):
    clean = su.load_monthly(su.CLEAN_CSV)
    assert len(clean) == len(monthly)
    a = su.monthly_series(monthly, "Gas", "kWh/day")
    b = su.monthly_series(clean, "Gas", "kWh/day")
    assert a.equals(b)


@pytest.mark.parametrize("quantity", QUANTITIES)
@pytest.mark.parametrize("unit", ["kWh/day", "kWh/m2/day", "kWh/person/day"])
def test_whole_sample_series_has_48_months(monthly, quantity, unit):
    s = su.monthly_series(monthly, quantity, unit)
    assert len(s) == 48
    assert str(s.index.min().date()) == "2020-01-01"


def test_region_panel(monthly):
    panel = su.monthly_panel(monthly, "Electricity net", "kWh/day", "region")
    assert panel.shape == (48, 11)
    # a mixed-unit slice would include per-m2 values around 0.1
    assert panel.min().min() > 1


def test_gas_peaks_in_winter(monthly):
    s = su.monthly_series(monthly, "Gas", "kWh/day")
    by_month = s.groupby(s.index.month).mean()
    assert by_month.idxmax() in (12, 1, 2)
    assert by_month.idxmin() in (6, 7, 8)


@pytest.mark.parametrize("year", su.YEARS)
@pytest.mark.parametrize("day", ["both", "weekday", "weekend"])
def test_half_hourly_profile_has_48_slots(half_hourly, year, day):
    p = su.daily_profile(half_hourly, year, "Electricity imports", "Wh",
                         to_kwh=True, weekday_weekend=day)
    assert len(p) == 48
    assert 5 < p.sum() < 20  # a typical GB home uses roughly 8-10 kWh of electricity a day


def test_yearly_rows():
    yearly = su.load_yearly()
    assert sorted(yearly["year"].unique()) == list(su.YEARS)
