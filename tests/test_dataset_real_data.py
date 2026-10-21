"""Checks against the real SERL files. Skipped when data/ is not present."""
import pandas as pd
import pytest

from serl_energy import dataset as serl

pytestmark = pytest.mark.skipif(not serl.DAILY_CSV.exists(), reason="SERL data not in data/raw/serl/")

QUANTITIES = ["Electricity imports", "Electricity exports", "Electricity net",
              "Gas", "Gas + electricity imports"]


@pytest.fixture(scope="module")
def monthly():
    return serl.load_monthly()


@pytest.fixture(scope="module")
def half_hourly():
    return serl.load_half_hourly()


def test_make_clean_daily_reproduces_interim_file():
    clean = pd.read_csv(serl.CLEAN_CSV)
    assert serl.make_clean_daily().equals(clean)


def test_clean_file_matches_raw_monthly(monthly):
    clean = serl.load_monthly(serl.CLEAN_CSV)
    assert len(clean) == len(monthly)
    a = serl.monthly_series(monthly, "Gas", "kWh/day")
    b = serl.monthly_series(clean, "Gas", "kWh/day")
    assert a.equals(b)


@pytest.mark.parametrize("quantity", QUANTITIES)
@pytest.mark.parametrize("unit", ["kWh/day", "kWh/m2/day", "kWh/person/day"])
def test_whole_sample_series_has_48_months(monthly, quantity, unit):
    s = serl.monthly_series(monthly, quantity, unit)
    assert len(s) == 48
    assert str(s.index.min().date()) == "2020-01-01"


def test_region_panel(monthly):
    panel = serl.monthly_panel(monthly, "Electricity net", "kWh/day", "region")
    assert panel.shape == (48, 11)
    # a mixed-unit slice would include per-m2 values around 0.1
    assert panel.min().min() > 1


def test_gas_peaks_in_winter(monthly):
    s = serl.monthly_series(monthly, "Gas", "kWh/day")
    assert isinstance(s.index, pd.DatetimeIndex)
    by_month = s.groupby(s.index.month).mean()
    assert by_month.idxmax() in (12, 1, 2)
    assert by_month.idxmin() in (6, 7, 8)


@pytest.mark.parametrize("year", serl.YEARS)
@pytest.mark.parametrize("day", ["both", "weekday", "weekend"])
def test_half_hourly_profile_has_48_slots(half_hourly, year, day):
    p = serl.daily_profile(half_hourly, year, "Electricity imports", "Wh",
                         to_kwh=True, weekday_weekend=day)
    assert len(p) == 48
    assert 5 < p.sum() < 20  # a typical GB home uses roughly 8-10 kWh of electricity a day


def test_yearly_rows():
    yearly = serl.load_yearly()
    assert sorted(yearly["year"].unique()) == list(serl.YEARS)
